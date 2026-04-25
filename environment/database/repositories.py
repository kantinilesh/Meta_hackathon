from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pymongo import DESCENDING

from .documents import (
    ActionRecord,
    ClauseAnalyticsDocument,
    ClauseDoc,
    ClauseGradeDetail,
    ClauseOutcome,
    CompanyDocument,
    ConstraintRecord,
    ContractDocument,
    DemoRunDocument,
    GradeBreakdownDoc,
    LeaderboardDocument,
    PartyRecord,
    PrerequisiteDocRef,
    SessionDocument,
    TaskResult,
    TurnRecord,
)


class CompanyRepository:
    @staticmethod
    async def upsert(company_name: str, role: str) -> CompanyDocument:
        return await CompanyDocument.get_or_create(company_name, role)

    @staticmethod
    async def find_by_id(company_id: str) -> Optional[CompanyDocument]:
        return await CompanyDocument.find_one({"company_id": company_id})

    @staticmethod
    async def find_by_name(name: str) -> Optional[CompanyDocument]:
        return await CompanyDocument.find_one({"company_name": name.strip()})

    @staticmethod
    async def update_post_session(
        company_id: str,
        won: bool,
        score: float,
        constraints_honored: int,
        deal_breakers_violated: int = 0,
        agreements_reached: int = 0,
        preferred_agent_style: Optional[str] = None,
        constraint_templates: Optional[List[dict]] = None,
    ) -> Optional[CompanyDocument]:
        return await CompanyDocument.update_stats_after_session(
            company_id,
            {
                "won": won,
                "score": score,
                "agreements_reached": agreements_reached,
                "deal_breakers_honored": constraints_honored,
                "deal_breakers_violated": deal_breakers_violated,
                "preferred_agent_style": preferred_agent_style,
                "constraint_templates": constraint_templates or [],
            },
        )

    @staticmethod
    async def get_stats(company_id: str) -> dict:
        company = await CompanyRepository.find_by_id(company_id)
        if not company:
            return {}
        sessions = await SessionDocument.get_by_company(company_id)
        agreement_rates = [session.agreement_rate for session in sessions]
        return {
            "company": company,
            "agreement_rate": sum(agreement_rates) / len(agreement_rates) if agreement_rates else 0.0,
            "sessions": sessions,
        }

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 20) -> List[CompanyDocument]:
        return await CompanyDocument.find_all().sort([("last_active", DESCENDING)]).skip(skip).limit(limit).to_list()


class ContractRepository:
    @staticmethod
    async def save(contract_data: dict) -> ContractDocument:
        existing = None
        if contract_data.get("contract_id"):
            existing = await ContractDocument.get_by_id(contract_data["contract_id"])
        if existing:
            for key, value in contract_data.items():
                if key == "clauses":
                    setattr(existing, key, [ClauseDoc(**item) if isinstance(item, dict) else item for item in value])
                elif key == "prerequisite_docs":
                    setattr(
                        existing,
                        key,
                        [PrerequisiteDocRef(**item) if isinstance(item, dict) else item for item in value],
                    )
                else:
                    setattr(existing, key, value)
            await existing.save()
            return existing

        doc = ContractDocument(
            contract_id=contract_data.get("contract_id"),
            contract_title=contract_data["contract_title"],
            contract_text=contract_data["contract_text"],
            uploaded_by=contract_data["uploaded_by"],
            contract_type=contract_data.get("contract_type", "Other"),
            clauses=[ClauseDoc(**item) if isinstance(item, dict) else item for item in contract_data.get("clauses", [])],
            prerequisite_docs=[
                PrerequisiteDocRef(**item) if isinstance(item, dict) else item
                for item in contract_data.get("prerequisite_docs", [])
            ],
            times_used=contract_data.get("times_used", 0),
        )
        await doc.insert()
        return doc

    @staticmethod
    async def find_by_id(contract_id: str) -> Optional[ContractDocument]:
        return await ContractDocument.get_by_id(contract_id)

    @staticmethod
    async def find_by_company(company_id: str) -> List[ContractDocument]:
        return await ContractDocument.get_by_company(company_id)

    @staticmethod
    async def increment_usage(contract_id: str) -> None:
        await ContractDocument.increment_usage(contract_id)

    @staticmethod
    async def get_recent(limit: int = 10) -> List[ContractDocument]:
        return await ContractDocument.find_all().sort([("created_at", DESCENDING)]).limit(limit).to_list()


class SessionRepository:
    @staticmethod
    async def create(session_data: dict) -> SessionDocument:
        doc = SessionDocument(
            session_id=session_data.get("session_id"),
            invite_token=session_data["invite_token"],
            status=session_data.get("status", "waiting_client"),
            contract_id=session_data["contract_id"],
            contract_title=session_data["contract_title"],
            seller=PartyRecord(**session_data["seller"]),
            client=PartyRecord(**session_data["client"]) if session_data.get("client") else None,
            clause_outcomes=[
                ClauseOutcome(**item) if isinstance(item, dict) else item
                for item in session_data.get("clause_outcomes", [])
            ],
            total_clauses=session_data.get("total_clauses", len(session_data.get("clause_outcomes", []))),
            created_at=session_data.get("created_at", datetime.utcnow()),
            started_at=session_data.get("started_at"),
        )
        await doc.insert()
        return doc

    @staticmethod
    async def find_by_id(session_id: str) -> Optional[SessionDocument]:
        return await SessionDocument.find_one({"session_id": session_id})

    @staticmethod
    async def find_by_token(invite_token: str) -> Optional[SessionDocument]:
        return await SessionDocument.get_by_token(invite_token)

    @staticmethod
    async def update_status(session_id: str, status: str) -> Optional[SessionDocument]:
        doc = await SessionRepository.find_by_id(session_id)
        if not doc:
            return None
        doc.status = status
        if status == "negotiating" and not doc.started_at:
            doc.started_at = datetime.utcnow()
        await doc.save()
        return doc

    @staticmethod
    async def save_turn(session_id: str, turn: dict) -> Optional[SessionDocument]:
        doc = await SessionRepository.find_by_id(session_id)
        if not doc:
            return None
        await doc.add_turn(TurnRecord(**turn))
        return doc

    @staticmethod
    async def save_clause_outcome(session_id: str, clause_id: str, outcome: dict) -> Optional[SessionDocument]:
        doc = await SessionRepository.find_by_id(session_id)
        if not doc:
            return None
        await doc.update_clause_outcome(clause_id, ClauseOutcome(**outcome))
        return doc

    @staticmethod
    async def save_final_contract(session_id: str, contract_text: str, agreed_clauses: dict) -> Optional[SessionDocument]:
        doc = await SessionRepository.find_by_id(session_id)
        if not doc:
            return None
        doc.final_contract_text = contract_text
        doc.total_agreements = len(agreed_clauses)
        await doc.save()
        return doc

    @staticmethod
    async def mark_signed(session_id: str, role: str) -> Optional[SessionDocument]:
        doc = await SessionRepository.find_by_id(session_id)
        if not doc:
            return None
        await doc.mark_signed(role)
        refreshed = await SessionRepository.find_by_id(session_id)
        return refreshed or doc

    @staticmethod
    async def complete(session_id: str, summary: dict) -> Optional[SessionDocument]:
        doc = await SessionRepository.find_by_id(session_id)
        if not doc:
            return None
        for key, value in summary.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        await doc.complete_session()
        refreshed = await SessionRepository.find_by_id(session_id)
        return refreshed or doc

    @staticmethod
    async def get_by_company(company_id: str, limit: int = 10) -> List[SessionDocument]:
        sessions = await SessionDocument.get_by_company(company_id)
        return sessions[:limit]

    @staticmethod
    async def get_recent_completed(limit: int = 20) -> List[SessionDocument]:
        return await SessionDocument.get_completed_sessions(limit=limit)


class DemoRepository:
    @staticmethod
    async def save_run(run_data: dict) -> DemoRunDocument:
        if run_data.get("run_id"):
            existing = await DemoRunDocument.find_one({"run_id": run_data["run_id"]})
            if existing:
                for key, value in run_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                await existing.save()
                return existing
        return await DemoRunDocument.create_from_inference(run_data)

    @staticmethod
    async def find_by_id(run_id: str) -> Optional[DemoRunDocument]:
        return await DemoRunDocument.find_one({"run_id": run_id})

    @staticmethod
    async def save_task_result(run_id: str, task_result: dict) -> Optional[DemoRunDocument]:
        doc = await DemoRepository.find_by_id(run_id)
        if not doc:
            return None

        normalized = TaskResult(
            **{
                **task_result,
                "actions_taken": [
                    ActionRecord(**item) if isinstance(item, dict) else item
                    for item in task_result.get("actions_taken", [])
                ],
                "grade_breakdown": GradeBreakdownDoc(**task_result.get("grade_breakdown", {})),
                "clause_results": [
                    ClauseGradeDetail(**item) if isinstance(item, dict) else item
                    for item in task_result.get("clause_results", [])
                ],
            }
        )

        doc.task_results = [item for item in doc.task_results if item.task_id != normalized.task_id]
        doc.task_results.append(normalized)
        doc.overall_average_score = sum(item.achieved_score for item in doc.task_results) / len(doc.task_results)
        doc.passed_all_tasks = all(item.passed for item in doc.task_results) and len(doc.task_results) >= 3
        await doc.save()
        return doc

    @staticmethod
    async def complete_run(run_id: str, summary: dict) -> Optional[DemoRunDocument]:
        doc = await DemoRepository.find_by_id(run_id)
        if not doc:
            return None
        doc.completed_at = summary.get("completed_at", datetime.utcnow())
        doc.total_duration_seconds = summary.get(
            "total_duration_seconds",
            (doc.completed_at - doc.started_at).total_seconds(),
        )
        doc.passed_all_tasks = summary.get("passed_all_tasks", doc.passed_all_tasks)
        doc.openenv_validate_passed = summary.get("openenv_validate_passed", doc.openenv_validate_passed)
        await doc.save()
        return doc

    @staticmethod
    async def get_recent(limit: int = 10) -> List[DemoRunDocument]:
        return await DemoRunDocument.get_recent_runs(limit)

    @staticmethod
    async def get_best_per_model() -> List[dict]:
        runs = await DemoRunDocument.find_all().sort([("model_name", 1), ("overall_average_score", DESCENDING)]).to_list()
        best_by_model: Dict[str, dict] = {}
        for run in runs:
            if run.model_name not in best_by_model:
                best_by_model[run.model_name] = {
                    "model_name": run.model_name,
                    "run_id": run.run_id,
                    "overall_average_score": run.overall_average_score,
                    "passed_all_tasks": run.passed_all_tasks,
                }
        return list(best_by_model.values())


class AnalyticsRepository:
    @staticmethod
    async def update_clause_stats(session: SessionDocument) -> None:
        await ClauseAnalyticsDocument.update_after_session(session)

    @staticmethod
    async def get_clause_stats(clause_id: str) -> Optional[ClauseAnalyticsDocument]:
        return await ClauseAnalyticsDocument.find_one({"clause_id": clause_id})

    @staticmethod
    async def get_most_contested_clauses(limit: int = 5) -> List[dict]:
        docs = await ClauseAnalyticsDocument.get_most_contested(limit)
        return [doc.model_dump() for doc in docs]

    @staticmethod
    async def get_platform_summary() -> dict:
        sessions = await SessionDocument.find_all().to_list()
        companies = await CompanyDocument.find_all().to_list()
        leaderboard = await LeaderboardDocument.get_leaderboard(limit=1)
        analytics = await ClauseAnalyticsDocument.get_most_contested(limit=1)

        total_agreements = sum(session.total_agreements for session in sessions)
        avg_agreement_rate = (
            sum(session.agreement_rate for session in sessions) / len(sessions)
            if sessions
            else 0.0
        )
        return {
            "total_sessions": len(sessions),
            "total_companies": len(companies),
            "total_agreements": total_agreements,
            "avg_agreement_rate": avg_agreement_rate,
            "most_contested_clause": analytics[0].model_dump() if analytics else None,
            "top_model": leaderboard[0].model_dump() if leaderboard else None,
        }


class LeaderboardRepository:
    @staticmethod
    async def add_entry(run: DemoRunDocument) -> LeaderboardDocument:
        return await LeaderboardDocument.add_entry(run)

    @staticmethod
    async def get_top(limit: int = 20) -> List[LeaderboardDocument]:
        return await LeaderboardDocument.get_leaderboard(limit)

    @staticmethod
    async def get_rank(run_id: str) -> Optional[int]:
        entry = await LeaderboardDocument.find_one({"run_id": run_id})
        return entry.rank if entry else None
