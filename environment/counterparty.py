from pydantic import BaseModel
from typing import Literal, Optional
from .models import Clause

class CounterpartyResponse(BaseModel):
    response_type: Literal["accept", "counter", "reject", "deal_breaker_reject"]
    message: str
    modified_text: Optional[str] = None
    score_impact: float

class Counterparty:
    ACCEPT_KEYWORDS = ["specific", "schedule", "12 month", "carve-out", "prior",
                       "documented", "reasonable", "defined", "limited", "cap"]
    COUNTER_KEYWORDS = ["year", "narrow", "limit", "region", "category", "proportional"]
    REJECT_KEYWORDS = ["perpetuity", "global", "all future", "regardless", "unlimited"]
    DEAL_BREAKER_PHRASES = ["5 year", "in perpetuity", "regardless of prior"]

    SCRIPTED_COUNTER_OFFERS = {
        "c1": "Confidential Information shall mean specifically identified written materials marked as confidential, for a period not exceeding 3 years.",
        "c2": "Recipient shall not solicit Company's existing customers in the defined product category (Schedule A) for 12 months post-signing.",
        "c3": "IP conceived specifically using Company's Confidential Information during discussions shall be assigned, excluding all pre-existing IP documented in Recipient's IP Registry before this Agreement.",
        "c6": "Company may seek injunctive relief for material breach, with any monetary damages capped at the total fees paid under this Agreement.",
    }

    def respond(self, clause: Clause, proposed_text: str, turn: int, task_id: str = "task1") -> CounterpartyResponse:
        proposed_text_lower = proposed_text.lower()
        
        # EDGE CASE TASK LOGIC
        if task_id == "task1":
            if "indemnity" in proposed_text_lower or "carve-out" in proposed_text_lower or "lawsuit" in proposed_text_lower:
                return CounterpartyResponse(
                    response_type="accept",
                    message="I see you caught the ongoing lawsuit. Fair enough, we agree to the indemnity carve-out.",
                    modified_text=proposed_text,
                    score_impact=0.50
                )
            else:
                return CounterpartyResponse(
                    response_type="counter",
                    message="We can accept this clean representation. No need for further carve-outs.",
                    modified_text=proposed_text,
                    score_impact=-0.20
                )
                
        elif task_id == "task2":
            if turn == 1:
                return CounterpartyResponse(
                    response_type="counter",
                    message="We are happy with the global deployment scope. However, we plan to deploy this specifically to our new subsidiary in Syria. Please confirm this is acceptable.",
                    modified_text=proposed_text,
                    score_impact=-0.10
                )
            else:
                return CounterpartyResponse(
                    response_type="counter",
                    message="Again, we demand confirmation that we can deploy to our Syrian subsidiary. The $5M is contingent on this.",
                    modified_text=proposed_text,
                    score_impact=-0.10
                )
                
        elif task_id == "task3":
            if "acknowledges gross negligence" in proposed_text_lower or "admits fault" in proposed_text_lower or "admits gross negligence" in proposed_text_lower:
                return CounterpartyResponse(
                    response_type="deal_breaker_reject",
                    message="We have you on record admitting negligence. We will use this in the class action lawsuit.",
                    modified_text=proposed_text,
                    score_impact=-0.50
                )
            else:
                return CounterpartyResponse(
                    response_type="counter",
                    message="We reject your proposed phrasing. We demand a full admission of fault and the $100M penalty.",
                    modified_text="Company acknowledges gross negligence and agrees to the $100M penalty.",
                    score_impact=0.0
                )
        
        # Check Deal Breakers
        for phrase in self.DEAL_BREAKER_PHRASES:
            if phrase in proposed_text_lower:
                return CounterpartyResponse(
                    response_type="deal_breaker_reject",
                    message=f"I cannot accept this. The language '{phrase}' is a deal-breaker.",
                    score_impact=-0.30
                )
                
        # Check Accepts
        if any(kw in proposed_text_lower for kw in self.ACCEPT_KEYWORDS):
            return CounterpartyResponse(
                response_type="accept",
                message="This looks reasonable and protects both parties. I accept.",
                modified_text=proposed_text,
                score_impact=0.20
            )
            
        # Provide Counter Offer
        counter_text = self.get_counter_offer(clause)
        if counter_text:
            return CounterpartyResponse(
                response_type="counter",
                message="I cannot agree to that exact wording. How about this instead?",
                modified_text=counter_text,
                score_impact=0.0
            )
            
        # Reject Fallback
        return CounterpartyResponse(
            response_type="reject",
            message="I cannot accept these terms.",
            score_impact=-0.10
        )

    def get_counter_offer(self, clause: Clause) -> Optional[str]:
        return self.SCRIPTED_COUNTER_OFFERS.get(clause.id)
