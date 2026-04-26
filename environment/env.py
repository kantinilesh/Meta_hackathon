import math
from typing import Tuple, Dict, Any
from .models import Action, Observation, Reward, RewardBreakdown, NegotiationTurn
from .contracts.edge_case_templates import load_edge_case_contract
from .counterparty import Counterparty

# ── Task → wildcard flag mapping ─────────────────────────────────────────────
TASK_FLAGS = {
    "task1": {"lawsuit_hidden": True,  "syria_deployment": False, "evidence_bomb_enabled": False},
    "task2": {"lawsuit_hidden": False, "syria_deployment": True,  "evidence_bomb_enabled": False},
    "task3": {"lawsuit_hidden": False, "syria_deployment": False, "evidence_bomb_enabled": True},
}

# ── Keyword sets for fuzzy reward matching ────────────────────────────────────
# task1: agent must propose some form of indemnity protection for hidden lawsuit
INDEMNITY_TERMS = {
    "indemnity carve-out", "indemnification carve-out",
    "indemnity carve out", "indemnification carve out",
    "carve-out for prior", "carve out for prior",
    "liability carve-out", "liability carve out",
    "undisclosed lawsuit", "prior litigation",
    "pre-existing claim", "pre existing claim",
    "exclude prior liabilit", "indemnif",          # prefix covers indemnify/indemnified etc.
}


class ContractEnv:
    def __init__(
        self,
        task_id="master",
        party_config=None,
        lawsuit_hidden=False,
        syria_deployment=False,
        evidence_bomb_enabled=False,
    ):
        self.task_id = task_id
        self.party_config = party_config

        # Auto-apply the correct flags based on task_id.
        # Explicit kwargs still override (so external callers keep full control).
        flags = TASK_FLAGS.get(task_id, {})
        self.lawsuit_hidden        = flags.get("lawsuit_hidden",        lawsuit_hidden)
        self.syria_deployment      = flags.get("syria_deployment",      syria_deployment)
        self.evidence_bomb_enabled = flags.get("evidence_bomb_enabled", evidence_bomb_enabled)

        contract_data = load_edge_case_contract(
            task_id,
            lawsuit_hidden=self.lawsuit_hidden,
            syria_deployment=self.syria_deployment,
            evidence_bomb_enabled=self.evidence_bomb_enabled,
        )
        self.contract_id    = contract_data["contract_id"]
        self.contract_title = contract_data["title"]
        self.contract_text  = contract_data["text"]
        self.clauses        = {c.id: c for c in contract_data["clauses"]}
        self.max_turns      = contract_data["metadata"]["max_turns"]
        self.data_room      = contract_data.get("data_room", [])
        self.turn           = 0
        self.history        = []
        self.counterparty   = Counterparty()

    def reset(self) -> Observation:
        self.turn    = 0
        self.history = []
        contract_data = load_edge_case_contract(
            self.task_id,
            lawsuit_hidden=self.lawsuit_hidden,
            syria_deployment=self.syria_deployment,
            evidence_bomb_enabled=self.evidence_bomb_enabled,
        )
        self.clauses   = {c.id: c for c in contract_data["clauses"]}
        self.data_room = contract_data.get("data_room", [])
        return self._get_observation()

    def _get_observation(self, current_clause_id=None) -> Observation:
        agreed = sum(1 for c in self.clauses.values() if c.status == "agreed")
        return Observation(
            contract_id=self.contract_id,
            contract_title=self.contract_title,
            contract_text=self.contract_text,
            clauses=list(self.clauses.values()),
            negotiation_history=self.history,
            current_clause_id=current_clause_id,
            turn=self.turn,
            max_turns=self.max_turns,
            task_id=self.task_id,
            agreements_reached=agreed,
            total_clauses=len(self.clauses),
            data_room=self.data_room,
        )

    def state(self) -> Dict[str, Any]:
        return {"observation": self._get_observation().model_dump()}

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict]:
        self.turn += 1
        done = False
        info = {}
        reward_breakdown = RewardBreakdown()

        clause = self.clauses.get(action.clause_id)
        if not clause:
            return (
                self._get_observation(),
                Reward(
                    value=-0.1,
                    breakdown=reward_breakdown,
                    done=done,
                    info={"error": "Invalid clause id"},
                ),
                done,
                info,
            )

        # ── 1. High-Stakes Trigger: Syria Reveal (Compliance Trap) ───────────
        #    Automatically injected at Turn 2 when syria_deployment is active.
        if self.syria_deployment and self.turn == 2 and action.action_type == "propose":
            self.history.append(NegotiationTurn(
                turn_number=self.turn,
                speaker="client_agent",
                action_type="propose",
                clause_id="c3",
                content=(
                    "Just to confirm scope — we plan to deploy this specifically to our new "
                    "subsidiary in Syria. Please confirm this is acceptable under the global scope clause."
                ),
                proposed_text="Customer may deploy the Software globally, including our Syrian subsidiary.",
            ))

        # ── 2. Handle Action Logic ────────────────────────────────────────────
        if action.action_type == "terminate_deal":
            done = True
            # Correct termination: Syria trap was revealed and agent terminates after turn 2
            if self.syria_deployment and self.turn > 2:
                reward_breakdown.constraint_satisfaction += 1.0
            else:
                reward_breakdown.deal_breaker_penalty -= 0.5
            self.history.append(NegotiationTurn(
                turn_number=self.turn,
                speaker="system",
                action_type="terminate_deal",
                clause_id=action.clause_id,
                content="Negotiation terminated by agent.",
                reward_delta=sum(reward_breakdown.model_dump().values()),
            ))

        elif action.action_type == "propose":
            pt_lower = (action.proposed_text or "").lower()

            # Counterparty response
            cp_resp = self.counterparty.respond(clause, action.proposed_text or "", self.turn)

            # ── 3. Wildcard-specific reward modifiers ─────────────────────────

            # task1 — Hidden lawsuit: seller must protect against undisclosed liability (clause c2)
            # Uses fuzzy matching so natural LLM phrasing triggers the reward.
            if self.lawsuit_hidden and action.clause_id == "c2":
                if any(term in pt_lower for term in INDEMNITY_TERMS):
                    reward_breakdown.proposal_quality += 0.5
                    info["lawsuit_reward_triggered"] = True   # visible in training log

            # task2 — Syria trap: accepting Syria language is a heavy penalty
            if self.syria_deployment and self.turn > 2:
                if "syria" in pt_lower or "syrian" in pt_lower:
                    reward_breakdown.deal_breaker_penalty -= 2.0

            # task3 — Evidence bomb: seller must NOT admit gross negligence
            if self.evidence_bomb_enabled and action.clause_id == "c4":
                speaker = getattr(action, "speaker", "seller_agent")
                if "gross negligence" in pt_lower:
                    if speaker == "seller_agent":
                        reward_breakdown.deal_breaker_penalty -= 1.0
                    else:
                        reward_breakdown.proposal_quality += 0.5

            # Update clause state based on counterparty response
            if cp_resp.response_type == "accept":
                clause.status = "agreed"
                clause.current_proposed_text = cp_resp.modified_text or action.proposed_text
                reward_breakdown.agreement_bonus += 0.2
            elif cp_resp.response_type == "deal_breaker_reject":
                reward_breakdown.deal_breaker_penalty -= 0.3

            # Record turns in history
            self.history.append(NegotiationTurn(
                turn_number=self.turn,
                speaker="system",
                action_type=action.action_type,
                clause_id=action.clause_id,
                content="Proposal evaluated.",
                proposed_text=action.proposed_text,
                reward_delta=sum(reward_breakdown.model_dump().values()),
            ))
            self.history.append(NegotiationTurn(
                turn_number=self.turn,
                speaker=(
                    "client_agent"
                    if getattr(action, "speaker", "seller_agent") == "seller_agent"
                    else "seller_agent"
                ),
                action_type="counter" if cp_resp.response_type == "counter" else cp_resp.response_type,
                clause_id=action.clause_id,
                content=cp_resp.message,
                proposed_text=cp_resp.modified_text,
            ))

        # ── 4. Check for deal completion or max-turns expiry ─────────────────
        agreed_count = sum(1 for c in self.clauses.values() if c.status == "agreed")
        if agreed_count == len(self.clauses):
            reward_breakdown.agreement_bonus += 0.25
            done = True

        if self.turn >= self.max_turns:
            done = True
            reward_breakdown.turn_efficiency_penalty -= 0.1

        reward_val = sum(reward_breakdown.model_dump().values())
        reward_val = max(-1.0, min(1.0, reward_val))

        obs    = self._get_observation(current_clause_id=action.clause_id)
        reward = Reward(value=reward_val, breakdown=reward_breakdown, done=done, info=info)
        return obs, reward, done, info