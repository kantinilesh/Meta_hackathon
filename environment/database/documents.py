from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional
import re
import uuid

from beanie import Document, Insert, Replace, before_event
from pydantic import BaseModel, Field, field_validator
from pymongo import DESCENDING, TEXT, IndexModel


ALLOWED_AGENT_STYLES = {"aggressive", "balanced", "cooperative"}
ALLOWED_SESSION_STATUSES = {
    "waiting_seller",
    "waiting_client",
    "ready",
    "negotiating",
    "completed",
    "failed",
}
ALLOWED_CLAUSE_STATUSES = {"agreed", "rejected", "abandoned", "pending"}
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "shall",
    "must",
    "will",
    "your",
    "their",
    "have",
    "has",
    "been",
    "were",
    "about",
    "not",
    "any",
    "all",
    "per",
    "our",
    "out",
    "but",
}


def utcnow() -> datetime:
    return datetime.utcnow()


class PrivateConstraintDoc(BaseModel):
    constraint_id: str
    description: str
    clause_category: str
    is_deal_breaker: bool = False
    rule_type: str
    rule_value: Optional[str] = None
    priority: int = 1

    @field_validator("description", "clause_category", "rule_type")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        return max(1, value)


class ClauseDoc(BaseModel):
    clause_id: str
    title: str
    original_text: str
    category: str
    is_deal_breaker: bool = False
    ground_truth_label: Optional[str] = None
    risk_level: str = "medium"
    ai_analysis: Optional[str] = None

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"high", "medium", "low"}:
            raise ValueError("risk_level must be high, medium, or low")
        return normalized


class PrerequisiteDocRef(BaseModel):
    doc_type: str
    filename: str
    uploaded_at: datetime = Field(default_factory=utcnow)
    summary: str = ""


class ConstraintRecord(PrivateConstraintDoc):
    was_satisfied: Optional[bool] = None
    satisfaction_turn: Optional[int] = None


class PartyRecord(BaseModel):
    company_id: str
    company_name: str
    agent_style: str = "balanced"
    constraints: List[ConstraintRecord] = Field(default_factory=list)

    @field_validator("agent_style")
    @classmethod
    def validate_agent_style(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in ALLOWED_AGENT_STYLES:
            raise ValueError("invalid agent style")
        return normalized


class TurnRecord(BaseModel):
    turn_number: int
    speaker: str
    action_type: str
    clause_id: str
    content: str
    proposed_text: Optional[str] = None
    reward_delta: float = 0.0
    cumulative_reward: float = 0.0
    timestamp: datetime = Field(default_factory=utcnow)


class ClauseOutcome(BaseModel):
    clause_id: str
    clause_title: str
    original_text: str
    final_agreed_text: Optional[str] = None
    status: str = "pending"
    agreement_turn: Optional[int] = None
    seller_satisfied: Optional[bool] = None
    client_satisfied: Optional[bool] = None
    turns_to_resolve: int = 0

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in ALLOWED_CLAUSE_STATUSES:
            raise ValueError("invalid clause outcome status")
        return normalized


class ActionRecord(BaseModel):
    turn: int
    clause_id: str
    action_type: str
    label: Optional[str] = None
    proposed_text: Optional[str] = None
    reward_delta: float = 0.0


class GradeBreakdownDoc(BaseModel):
    flag_correct: float = 0.0
    label_correct: float = 0.0
    proposal_quality: float = 0.0
    agreement_bonus: float = 0.0
    constraint_satisfaction: float = 0.0
    deal_breaker_penalty: float = 0.0
    false_positive_penalty: float = 0.0
    turn_efficiency_penalty: float = 0.0


class ClauseGradeDetail(BaseModel):
    clause_id: str
    title: str
    agent_label: Optional[str] = None
    correct_label: Optional[str] = None
    correct: bool = False
    proposed_text: Optional[str] = None
    rubric_score: float = 0.0


class TaskResult(BaseModel):
    task_id: str
    task_name: str
    difficulty: str
    target_score: float
    achieved_score: float
    passed: bool
    steps_taken: int
    max_turns: int
    duration_seconds: float
    reward_timeline: List[float] = Field(default_factory=list)
    actions_taken: List[ActionRecord] = Field(default_factory=list)
    grade_breakdown: GradeBreakdownDoc = Field(default_factory=GradeBreakdownDoc)
    clause_results: List[ClauseGradeDetail] = Field(default_factory=list)


class CompanyDocument(Document):
    company_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    role_history: List[str] = Field(default_factory=list)
    total_sessions: int = 0
    sessions_as_seller: int = 0
    sessions_as_client: int = 0
    total_agreements_reached: int = 0
    total_deal_breakers_honored: int = 0
    total_deal_breakers_violated: int = 0
    avg_negotiation_score: float = 0.0
    created_at: datetime = Field(default_factory=utcnow)
    last_active: datetime = Field(default_factory=utcnow)
    preferred_agent_style: str = "balanced"
    constraint_templates: List[PrivateConstraintDoc] = Field(default_factory=list)

    class Settings:
        name = "companies"
        indexes = [
            IndexModel([("company_id", 1)], unique=True),
            IndexModel([("company_name", TEXT)]),
            IndexModel([("last_active", DESCENDING)]),
        ]

    @field_validator("company_name")
    @classmethod
    def normalize_company_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("company_name cannot be empty")
        return cleaned

    @field_validator("preferred_agent_style")
    @classmethod
    def normalize_agent_style(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in ALLOWED_AGENT_STYLES:
            raise ValueError("invalid preferred_agent_style")
        return normalized

    @before_event(Insert)
    def set_insert_timestamps(self) -> None:
        now = utcnow()
        self.created_at = self.created_at or now
        self.last_active = now

    @before_event(Replace)
    def refresh_last_active(self) -> None:
        self.last_active = utcnow()

    @classmethod
    async def get_or_create(cls, company_name: str, role: str) -> "CompanyDocument":
        normalized_role = role.strip().lower()
        doc = await cls.find_one({"company_name": company_name.strip()})
        if doc:
            doc.last_active = utcnow()
            if normalized_role in {"seller", "client"}:
                doc.role_history.append(normalized_role)
                if normalized_role == "seller":
                    doc.sessions_as_seller += 1
                else:
                    doc.sessions_as_client += 1
                doc.total_sessions += 1
            await doc.save()
            return doc

        doc = cls(
            company_name=company_name,
            role_history=[normalized_role] if normalized_role else [],
            total_sessions=1 if normalized_role else 0,
            sessions_as_seller=1 if normalized_role == "seller" else 0,
            sessions_as_client=1 if normalized_role == "client" else 0,
        )
        await doc.insert()
        return doc

    @classmethod
    async def update_stats_after_session(cls, company_id: str, session_result: Dict[str, Any]) -> Optional["CompanyDocument"]:
        doc = await cls.find_one({"company_id": company_id})
        if not doc:
            return None

        previous_sessions = max(doc.total_sessions, 1)
        score = float(session_result.get("score", 0.0))
        doc.avg_negotiation_score = (
            ((doc.avg_negotiation_score * max(previous_sessions - 1, 0)) + score) / previous_sessions
        )
        doc.total_agreements_reached += int(session_result.get("agreements_reached", 0))
        doc.total_deal_breakers_honored += int(session_result.get("deal_breakers_honored", 0))
        doc.total_deal_breakers_violated += int(session_result.get("deal_breakers_violated", 0))
        doc.last_active = utcnow()

        constraints = session_result.get("constraint_templates") or []
        if constraints:
            doc.constraint_templates = [PrivateConstraintDoc(**item) for item in constraints]
        if session_result.get("preferred_agent_style"):
            doc.preferred_agent_style = session_result["preferred_agent_style"]

        await doc.save()
        return doc

    @classmethod
    async def get_top_companies(cls, limit: int = 10) -> List["CompanyDocument"]:
        return await cls.find_all().sort([("avg_negotiation_score", DESCENDING)]).limit(limit).to_list()


class ContractDocument(Document):
    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_title: str
    contract_text: str
    uploaded_by: str
    contract_type: str = "Other"
    clauses: List[ClauseDoc] = Field(default_factory=list)
    total_clauses: int = 0
    unfair_clause_count: int = 0
    deal_breaker_count: int = 0
    prerequisite_docs: List[PrerequisiteDocRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    times_used: int = 0

    class Settings:
        name = "contracts"
        indexes = [
            IndexModel([("contract_id", 1)], unique=True),
            IndexModel([("uploaded_by", 1)]),
            IndexModel([("contract_type", 1)]),
            IndexModel([("created_at", DESCENDING)]),
        ]

    @before_event(Insert)
    def initialize_counts(self) -> None:
        self.total_clauses = len(self.clauses)
        self.unfair_clause_count = sum(1 for clause in self.clauses if clause.ground_truth_label == "unfair")
        self.deal_breaker_count = sum(1 for clause in self.clauses if clause.is_deal_breaker)
        self.created_at = self.created_at or utcnow()

    @before_event(Replace)
    def refresh_counts(self) -> None:
        self.total_clauses = len(self.clauses)
        self.unfair_clause_count = sum(1 for clause in self.clauses if clause.ground_truth_label == "unfair")
        self.deal_breaker_count = sum(1 for clause in self.clauses if clause.is_deal_breaker)

    @classmethod
    async def get_by_id(cls, contract_id: str) -> Optional["ContractDocument"]:
        return await cls.find_one({"contract_id": contract_id})

    @classmethod
    async def increment_usage(cls, contract_id: str) -> None:
        doc = await cls.find_one({"contract_id": contract_id})
        if doc:
            await doc.update({"$inc": {"times_used": 1}})

    @classmethod
    async def get_by_company(cls, company_id: str) -> List["ContractDocument"]:
        return await cls.find({"uploaded_by": company_id}).sort([("created_at", DESCENDING)]).to_list()


class SessionDocument(Document):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invite_token: str
    status: str = "waiting_client"
    contract_id: str
    contract_title: str
    seller: PartyRecord
    client: Optional[PartyRecord] = None
    negotiation_turns: List[TurnRecord] = Field(default_factory=list)
    clause_outcomes: List[ClauseOutcome] = Field(default_factory=list)
    final_contract_text: Optional[str] = None
    total_turns: int = 0
    total_agreements: int = 0
    total_clauses: int = 0
    agreement_rate: float = 0.0
    seller_total_reward: float = 0.0
    client_total_reward: float = 0.0
    seller_constraints_satisfied: int = 0
    client_constraints_satisfied: int = 0
    seller_deal_breakers_honored: int = 0
    client_deal_breakers_honored: int = 0
    seller_signed: bool = False
    client_signed: bool = False
    seller_signed_at: Optional[datetime] = None
    client_signed_at: Optional[datetime] = None
    both_signed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime = Field(default_factory=utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Settings:
        name = "sessions"
        indexes = [
            IndexModel([("session_id", 1)], unique=True),
            IndexModel([("invite_token", 1)], unique=True),
            IndexModel([("seller.company_id", 1)]),
            IndexModel([("client.company_id", 1)]),
            IndexModel([("status", 1)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("status", 1), ("created_at", DESCENDING)]),
        ]

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in ALLOWED_SESSION_STATUSES:
            raise ValueError("invalid session status")
        return normalized

    @before_event(Insert)
    def initialize_session_metrics(self) -> None:
        self.created_at = self.created_at or utcnow()
        self.total_clauses = self.total_clauses or len(self.clause_outcomes)
        self.agreement_rate = (
            float(self.total_agreements) / float(self.total_clauses)
            if self.total_clauses
            else 0.0
        )

    @before_event(Replace)
    def update_session_metrics(self) -> None:
        self.total_turns = len(self.negotiation_turns)
        self.total_agreements = sum(1 for outcome in self.clause_outcomes if outcome.status == "agreed")
        self.total_clauses = self.total_clauses or len(self.clause_outcomes)
        self.agreement_rate = (
            float(self.total_agreements) / float(self.total_clauses)
            if self.total_clauses
            else 0.0
        )

    @classmethod
    async def get_by_token(cls, invite_token: str) -> Optional["SessionDocument"]:
        return await cls.find_one({"invite_token": invite_token})

    @classmethod
    async def get_by_company(cls, company_id: str) -> List["SessionDocument"]:
        return await cls.find(
            {
                "$or": [
                    {"seller.company_id": company_id},
                    {"client.company_id": company_id},
                ]
            }
        ).sort([("created_at", DESCENDING)]).to_list()

    @classmethod
    async def get_active_sessions(cls) -> List["SessionDocument"]:
        return await cls.find({"status": {"$in": ["ready", "negotiating"]}}).sort(
            [("created_at", DESCENDING)]
        ).to_list()

    @classmethod
    async def get_completed_sessions(cls, limit: int = 20) -> List["SessionDocument"]:
        return await cls.find({"status": "completed"}).sort([("completed_at", DESCENDING)]).limit(limit).to_list()

    async def add_turn(self, turn: TurnRecord) -> None:
        await self.get_motor_collection().update_one(
            {"session_id": self.session_id},
            {
                "$push": {"negotiation_turns": turn.model_dump()},
                "$set": {
                    "total_turns": turn.turn_number,
                    "seller_total_reward": turn.cumulative_reward if turn.speaker == "seller_agent" else self.seller_total_reward,
                    "client_total_reward": turn.cumulative_reward if turn.speaker == "client_agent" else self.client_total_reward,
                },
            },
        )
        self.negotiation_turns.append(turn)
        self.total_turns = turn.turn_number
        if turn.speaker == "seller_agent":
            self.seller_total_reward = turn.cumulative_reward
        elif turn.speaker == "client_agent":
            self.client_total_reward = turn.cumulative_reward

    async def update_clause_outcome(self, clause_id: str, outcome: ClauseOutcome) -> None:
        outcomes = [item for item in self.clause_outcomes if item.clause_id != clause_id]
        outcomes.append(outcome)
        self.clause_outcomes = outcomes
        self.total_agreements = sum(1 for item in self.clause_outcomes if item.status == "agreed")
        self.total_clauses = len(self.clause_outcomes)
        self.agreement_rate = self.total_agreements / self.total_clauses if self.total_clauses else 0.0
        await self.get_motor_collection().update_one(
            {"session_id": self.session_id},
            {
                "$set": {
                    "clause_outcomes": [item.model_dump() for item in self.clause_outcomes],
                    "total_agreements": self.total_agreements,
                    "total_clauses": self.total_clauses,
                    "agreement_rate": self.agreement_rate,
                }
            },
        )

    async def mark_signed(self, role: str) -> None:
        now = utcnow()
        update_fields: Dict[str, Any] = {}
        if role == "seller":
            self.seller_signed = True
            self.seller_signed_at = now
            update_fields.update({"seller_signed": True, "seller_signed_at": now})
        elif role == "client":
            self.client_signed = True
            self.client_signed_at = now
            update_fields.update({"client_signed": True, "client_signed_at": now})

        if self.seller_signed and self.client_signed:
            self.both_signed_at = now
            update_fields["both_signed_at"] = now

        await self.get_motor_collection().update_one({"session_id": self.session_id}, {"$set": update_fields})

    async def complete_session(self) -> None:
        completed_at = utcnow()
        self.completed_at = completed_at
        self.status = "completed"
        self.duration_seconds = (
            int((completed_at - self.started_at).total_seconds())
            if self.started_at
            else None
        )
        self.total_turns = len(self.negotiation_turns)
        self.total_agreements = sum(1 for outcome in self.clause_outcomes if outcome.status == "agreed")
        self.total_clauses = len(self.clause_outcomes)
        self.agreement_rate = self.total_agreements / self.total_clauses if self.total_clauses else 0.0
        await self.save()


class DemoRunDocument(Document):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    model_name: str
    api_base_url: str
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    passed_all_tasks: bool = False
    task_results: List[TaskResult] = Field(default_factory=list)
    overall_average_score: float = 0.0
    openenv_validate_passed: bool = False

    class Settings:
        name = "demo_runs"
        indexes = [
            IndexModel([("run_id", 1)], unique=True),
            IndexModel([("model_name", 1)]),
            IndexModel([("completed_at", DESCENDING)]),
            IndexModel([("overall_average_score", DESCENDING)]),
            IndexModel([("model_name", 1), ("completed_at", DESCENDING)]),
        ]

    @before_event(Insert)
    def set_started_at(self) -> None:
        self.started_at = self.started_at or utcnow()

    @before_event(Replace)
    def recalc_scores(self) -> None:
        if self.task_results:
            self.overall_average_score = sum(item.achieved_score for item in self.task_results) / len(self.task_results)
            self.passed_all_tasks = all(item.passed for item in self.task_results) and len(self.task_results) >= 3
        if self.completed_at:
            self.total_duration_seconds = max(
                self.total_duration_seconds,
                (self.completed_at - self.started_at).total_seconds(),
            )

    @classmethod
    async def create_from_inference(cls, results: Dict[str, Any]) -> "DemoRunDocument":
        doc = cls(
            session_id=results.get("session_id"),
            model_name=results.get("model_name", "unknown"),
            api_base_url=results.get("api_base_url", ""),
            started_at=results.get("started_at", utcnow()),
        )
        await doc.insert()
        return doc

    @classmethod
    async def get_recent_runs(cls, limit: int = 10) -> List["DemoRunDocument"]:
        return await cls.find_all().sort([("started_at", DESCENDING)]).limit(limit).to_list()

    @classmethod
    async def get_best_score(cls) -> Optional[float]:
        best = await cls.find_all().sort([("overall_average_score", DESCENDING)]).limit(1).to_list()
        return best[0].overall_average_score if best else None


class ClauseAnalyticsDocument(Document):
    clause_id: str
    clause_title: str
    clause_category: str
    contract_id: str
    total_appearances: int = 0
    total_agreed: int = 0
    total_rejected: int = 0
    total_abandoned: int = 0
    agreement_rate: float = 0.0
    avg_turns_to_resolve: float = 0.0
    min_turns_to_resolve: int = 0
    max_turns_to_resolve: int = 0
    most_common_proposals: List[str] = Field(default_factory=list)
    most_effective_keywords: List[str] = Field(default_factory=list)
    most_common_rejection_reasons: List[str] = Field(default_factory=list)
    seller_win_rate: float = 0.0
    client_win_rate: float = 0.0
    last_updated: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "clause_analytics"
        indexes = [
            IndexModel([("clause_id", 1)]),
            IndexModel([("agreement_rate", DESCENDING)]),
            IndexModel([("clause_category", 1)]),
        ]

    @before_event(Insert)
    def set_last_updated(self) -> None:
        self.last_updated = utcnow()

    @before_event(Replace)
    def refresh_last_updated(self) -> None:
        self.last_updated = utcnow()

    @classmethod
    async def update_after_session(cls, session: SessionDocument) -> None:
        for outcome in session.clause_outcomes:
            analytics = await cls.find_one(
                {
                    "clause_id": outcome.clause_id,
                    "contract_id": session.contract_id,
                }
            )
            if not analytics:
                category = "unknown"
                for constraint in session.seller.constraints:
                    if constraint.clause_category and constraint.clause_category != "unknown":
                        category = constraint.clause_category
                        break
                analytics = cls(
                    clause_id=outcome.clause_id,
                    clause_title=outcome.clause_title,
                    clause_category=category,
                    contract_id=session.contract_id,
                )

            clause_turns = [turn for turn in session.negotiation_turns if turn.clause_id == outcome.clause_id]
            proposal_texts = [turn.proposed_text for turn in clause_turns if turn.proposed_text]
            rejection_reasons = [
                turn.content
                for turn in clause_turns
                if turn.action_type == "reject" and turn.content
            ]
            agreed_texts = [
                turn.proposed_text
                for turn in clause_turns
                if outcome.status == "agreed" and turn.proposed_text
            ]

            analytics.total_appearances += 1
            analytics.total_agreed += 1 if outcome.status == "agreed" else 0
            analytics.total_rejected += 1 if outcome.status == "rejected" else 0
            analytics.total_abandoned += 1 if outcome.status == "abandoned" else 0
            analytics.agreement_rate = (
                analytics.total_agreed / analytics.total_appearances
                if analytics.total_appearances
                else 0.0
            )

            historical_turns = []
            if analytics.avg_turns_to_resolve:
                historical_turns.append(analytics.avg_turns_to_resolve)
            historical_turns.append(float(outcome.turns_to_resolve))
            analytics.avg_turns_to_resolve = sum(historical_turns) / len(historical_turns)
            analytics.min_turns_to_resolve = (
                outcome.turns_to_resolve
                if analytics.min_turns_to_resolve == 0
                else min(analytics.min_turns_to_resolve, outcome.turns_to_resolve)
            )
            analytics.max_turns_to_resolve = max(analytics.max_turns_to_resolve, outcome.turns_to_resolve)

            proposal_counter = Counter(analytics.most_common_proposals)
            proposal_counter.update(proposal_texts)
            analytics.most_common_proposals = [item for item, _ in proposal_counter.most_common(5)]

            keyword_counter = Counter(analytics.most_effective_keywords)
            for text in agreed_texts:
                keyword_counter.update(
                    word
                    for word in re.findall(r"[a-zA-Z]{4,}", text.lower())
                    if word not in STOP_WORDS
                )
            analytics.most_effective_keywords = [item for item, _ in keyword_counter.most_common(5)]

            rejection_counter = Counter(analytics.most_common_rejection_reasons)
            rejection_counter.update(rejection_reasons)
            analytics.most_common_rejection_reasons = [item for item, _ in rejection_counter.most_common(5)]

            seller_texts = {turn.proposed_text for turn in clause_turns if turn.speaker == "seller_agent" and turn.proposed_text}
            client_texts = {turn.proposed_text for turn in clause_turns if turn.speaker == "client_agent" and turn.proposed_text}
            final_text = outcome.final_agreed_text or ""
            if final_text and seller_texts:
                analytics.seller_win_rate = min(
                    1.0,
                    analytics.seller_win_rate + (1.0 / analytics.total_appearances if final_text in seller_texts else 0.0),
                )
            if final_text and client_texts:
                analytics.client_win_rate = min(
                    1.0,
                    analytics.client_win_rate + (1.0 / analytics.total_appearances if final_text in client_texts else 0.0),
                )

            analytics.last_updated = utcnow()
            if analytics.id:
                await analytics.save()
            else:
                await analytics.insert()

    @classmethod
    async def get_most_contested(cls, limit: int = 5) -> List["ClauseAnalyticsDocument"]:
        return await cls.find_all().sort([("agreement_rate", 1), ("total_appearances", DESCENDING)]).limit(limit).to_list()


class LeaderboardDocument(Document):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    model_name: str
    rank: int = 0
    overall_score: float
    task1_score: float = 0.0
    task2_score: float = 0.0
    task3_score: float = 0.0
    all_passed: bool = False
    total_steps: int = 0
    total_duration_s: float = 0.0
    submitted_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "leaderboard"
        indexes = [
            IndexModel([("overall_score", DESCENDING)]),
            IndexModel([("model_name", 1)]),
            IndexModel([("submitted_at", DESCENDING)]),
            IndexModel([("all_passed", 1), ("overall_score", DESCENDING)]),
        ]

    @before_event(Insert)
    def set_submitted_at(self) -> None:
        self.submitted_at = self.submitted_at or utcnow()

    @classmethod
    async def add_entry(cls, run: DemoRunDocument) -> "LeaderboardDocument":
        task_scores = {task.task_id: task.achieved_score for task in run.task_results}
        entry = cls(
            run_id=run.run_id,
            model_name=run.model_name,
            overall_score=run.overall_average_score,
            task1_score=task_scores.get("task1", 0.0),
            task2_score=task_scores.get("task2", 0.0),
            task3_score=task_scores.get("task3", 0.0),
            all_passed=run.passed_all_tasks,
            total_steps=sum(task.steps_taken for task in run.task_results),
            total_duration_s=run.total_duration_seconds,
        )
        await entry.insert()
        await cls.recalculate_ranks()
        refreshed = await cls.find_one({"entry_id": entry.entry_id})
        return refreshed or entry

    @classmethod
    async def get_leaderboard(cls, limit: int = 20) -> List["LeaderboardDocument"]:
        return await cls.find_all().sort(
            [("all_passed", DESCENDING), ("overall_score", DESCENDING), ("submitted_at", DESCENDING)]
        ).limit(limit).to_list()

    @classmethod
    async def recalculate_ranks(cls) -> None:
        entries = await cls.find_all().sort(
            [("all_passed", DESCENDING), ("overall_score", DESCENDING), ("submitted_at", DESCENDING)]
        ).to_list()
        for idx, entry in enumerate(entries, start=1):
            if entry.rank != idx:
                entry.rank = idx
                await entry.save()
