from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Literal
from enum import Enum

class ClauseCategory(str, Enum):
    scope="scope"; duration="duration"; ip="ip"; liability="liability"
    jurisdiction="jurisdiction"; payment="payment"; termination="termination"

class ClauseLabel(str, Enum):
    fair="fair"; unfair="unfair"; neutral="neutral"

class ActionType(str, Enum):
    flag="flag"; propose="propose"; accept="accept"
    reject="reject"; skip="skip"; counter="counter"

class NegotiationRole(str, Enum):
    seller="seller"; client="client"

class SessionStatus(str, Enum):
    waiting_seller="waiting_seller"; waiting_client="waiting_client"
    ready="ready"; negotiating="negotiating"; completed="completed"; failed="failed"
    paused="paused"

class PrivateConstraint(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "constraint_id": "s1",
                "description": "Non-compete must not exceed 1 year",
                "clause_category": "scope",
                "is_deal_breaker": True,
                "rule_type": "max_value",
                "rule_value": "1 year",
                "priority": 1
            }
        }
    )
    constraint_id: str = Field(description="Unique identifier for the constraint")
    description: str = Field(description="Human readable description")
    clause_category: ClauseCategory = Field(description="Category of clause this applies to")
    is_deal_breaker: bool = Field(default=False, description="If true, violation causes failure")
    rule_type: Literal["max_value","min_value","must_include","must_exclude","prefer"] = Field(description="Type of deterministic constraint")
    rule_value: Optional[str] = Field(default=None, description="Value for the rule")
    priority: int = Field(default=1, description="Priority weight 1-10")

class CompanyDocument(BaseModel):
    document_id: str = Field(description="Unique document ID")
    file_name: str = Field(description="Original file name")
    file_type: Literal["pdf", "docx", "txt", "xlsx"] = Field(description="File type")
    document_type: Literal["financials", "bylaws", "due_diligence", "cap_table", "employment", "ip_assignment", "other"] = Field(description="Category of document")
    summary: str = Field(default="", description="AI-generated summary of document contents")
    key_terms: List[str] = Field(default_factory=list, description="Extracted key terms relevant to negotiation")
    upload_date: str = Field(description="Timestamp of upload")

class PartyConfig(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "seller",
                "company_name": "Acme Corp",
                "constraints": [],
                "agent_style": "balanced",
                "constraint_summary": "Do not accept liability > 50k",
                "company_context": "",
                "documents": []
            }
        }
    )
    role: NegotiationRole = Field(description="Role of the party")
    company_name: str = Field(description="Name of the company")
    constraints: List[PrivateConstraint] = Field(description="List of private constraints")
    agent_style: Literal["aggressive","balanced","cooperative"] = Field(default="balanced", description="Negotiation style")
    constraint_summary: str = Field(default="", description="Summary of constraints for LLM")
    company_context: str = Field(default="", description="Optional background document context")
    documents: List[CompanyDocument] = Field(default_factory=list, description="Uploaded prerequisite documents")
class Clause(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "c1",
                "title": "Confidentiality Scope",
                "text": "All info is confidential",
                "category": "ip",
                "is_deal_breaker": False,
                "status": "pending"
            }
        }
    )
    id: str = Field(description="Clause ID, eg c1")
    title: str = Field(description="Clause Title")
    text: str = Field(description="Original clause text")
    category: ClauseCategory = Field(description="Clause Category")
    is_deal_breaker: bool = Field(default=False, description="Whether this clause contains a deal-breaker")
    ground_truth_label: Optional[ClauseLabel] = Field(default=None, description="Ground truth fairness label")
    current_proposed_text: Optional[str] = Field(default=None, description="Latest proposed redline")
    status: Literal["pending","agreed","rejected","in_negotiation"] = Field(default="pending", description="Current status")

class NegotiationTurn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "turn_number": 1,
                "speaker": "seller_agent",
                "action_type": "propose",
                "clause_id": "c1",
                "content": "I propose we limit to 1 yr.",
                "proposed_text": "Limited to 1 yr.",
                "is_visible_to_both": True
            }
        }
    )
    turn_number: int = Field(description="Sequential turn number")
    speaker: Literal["seller_agent","client_agent","system"] = Field(description="Who is making the turn")
    action_type: ActionType = Field(description="Type of action performed")
    clause_id: str = Field(description="Which clause this action targets")
    content: str = Field(description="Chat message content")
    proposed_text: Optional[str] = Field(default=None, description="Proposed redline text if any")
    reward_delta: float = Field(default=0.0, description="Change in reward based on action")
    internal_reasoning: Optional[str] = Field(default=None, description="Agent's internal chain of thought")
    is_visible_to_both: bool = Field(default=True, description="Whether this is public")

class Observation(BaseModel):
    contract_id: str = Field(description="Contract Identifier")
    contract_title: str = Field(description="Contract Title")
    contract_text: str = Field(description="Full text of the contract")
    clauses: List[Clause] = Field(description="List of clauses")
    negotiation_history: List[NegotiationTurn] = Field(description="Public history")
    current_clause_id: Optional[str] = Field(description="Clause currently under discussion")
    turn: int = Field(description="Current turn")
    max_turns: int = Field(description="Turn budget limit")
    task_id: str = Field(description="Current Task ID")
    agreements_reached: int = Field(description="Count of agreed clauses")
    total_clauses: int = Field(description="Total clauses")
    session_id: Optional[str] = Field(default=None, description="Session ID if dual-agent")
    role: Optional[NegotiationRole] = Field(default=None, description="Your role if dual-agent")

class Action(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "clause_id": "c1",
                "action_type": "propose",
                "proposed_text": "New text."
            }
        }
    )
    clause_id: str = Field(description="Clause to act on")
    action_type: ActionType = Field(description="Type of action")
    label: Optional[ClauseLabel] = Field(default=None, description="Task 1 fairness label")
    reason: Optional[str] = Field(default=None, description="Task 1 flag reason")
    proposed_text: Optional[str] = Field(default=None, description="Task 2/3 redlined text")
    internal_reasoning: Optional[str] = Field(default=None, description="Chain of thought for the action")

class RewardBreakdown(BaseModel):
    flag_correct: float = 0.0
    label_correct: float = 0.0
    proposal_quality: float = 0.0
    agreement_bonus: float = 0.0
    constraint_satisfaction: float = 0.0
    deal_breaker_penalty: float = 0.0
    false_positive_penalty: float = 0.0
    turn_efficiency_penalty: float = 0.0

class Reward(BaseModel):
    value: float = Field(description="Reward float [-1.0, 1.0]")
    breakdown: RewardBreakdown
    done: bool = Field(description="True if episode is complete")
    info: dict = Field(default_factory=dict, description="Extra info")

class TaskConfig(BaseModel):
    task_id: str
    name: str
    difficulty: Literal["easy","medium","hard"]
    description: str
    max_turns: int
    target_score: float

class NegotiationSession(BaseModel):
    session_id: str
    status: SessionStatus
    seller_config: Optional[PartyConfig] = None
    client_config: Optional[PartyConfig] = None
    contract_id: str
    contract_title: str
    clauses: List[Clause]
    negotiation_history: List[NegotiationTurn] = []
    final_agreed_clauses: Dict[str,str] = {}
    seller_signed: bool = False
    client_signed: bool = False
    created_at: str
    invite_token: str
    turn: int = 0
    max_turns: int = 100

class GradeResult(BaseModel):
    task_id: str
    score: float
    breakdown: dict
    passed: bool
    details: List[str]
