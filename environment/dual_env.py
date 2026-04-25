from typing import List, Tuple, Dict
from copy import deepcopy
from .models import NegotiationSession, NegotiationRole, Observation, Action, NegotiationTurn

class DualAgentEnv:
    def __init__(self, session: NegotiationSession):
        self.session = session
        self.clauses = {c.id: c for c in session.clauses}
        
    def get_observation(self, role: NegotiationRole) -> Observation:
        obs = Observation(
            contract_id=self.session.contract_id,
            contract_title=self.session.contract_title,
            contract_text="",
            clauses=list(self.clauses.values()),
            negotiation_history=self.get_private_history(role),
            current_clause_id=None,
            turn=self.session.turn,
            max_turns=self.session.max_turns,
            task_id="dual",
            agreements_reached=sum(1 for c in self.clauses.values() if c.status == "agreed"),
            total_clauses=len(self.clauses),
            session_id=self.session.session_id,
            role=role
        )
        return obs
        
    def step_seller(self, action: Action) -> Tuple[Observation, float, bool]:
        return self._step(NegotiationRole.seller, action)
        
    def step_client(self, action: Action) -> Tuple[Observation, float, bool]:
        return self._step(NegotiationRole.client, action)
        
    def _step(self, role: NegotiationRole, action: Action) -> Tuple[Observation, float, bool]:
        self.session.turn += 1
        clause = self.clauses.get(action.clause_id)
        
        # Use the LLM-generated content field if available, otherwise build a natural default
        if hasattr(action, 'content') and action.content:
            message_content = action.content
        elif action.action_type == "propose" and action.proposed_text:
            message_content = f"{role.value.capitalize()} Agent proposes a revision to the {clause.title if clause else action.clause_id} clause."
        elif action.action_type == "accept":
            message_content = f"{role.value.capitalize()} Agent accepts the current terms for {clause.title if clause else action.clause_id}."
        elif action.action_type == "reject":
            message_content = f"{role.value.capitalize()} Agent rejects the current terms for {clause.title if clause else action.clause_id}."
        else:
            message_content = f"{role.value.capitalize()} Agent acts on {action.clause_id}."
        
        turn = NegotiationTurn(
            turn_number=self.session.turn,
            speaker=f"{role.value}_agent",
            action_type=action.action_type,
            clause_id=action.clause_id,
            content=message_content,
            proposed_text=action.proposed_text,
            internal_reasoning=action.internal_reasoning,
            is_visible_to_both=True
        )
        self.session.negotiation_history.append(turn)
        
        if action.action_type == "propose" and action.proposed_text:
            clause.current_proposed_text = action.proposed_text
            clause.status = "in_negotiation"
        elif action.action_type == "accept":
            clause.status = "agreed"
            # Store the agreed text: prefer current_proposed_text, fallback to original
            agreed_text = clause.current_proposed_text if clause.current_proposed_text else clause.text
            self.session.final_agreed_clauses[action.clause_id] = agreed_text
            self.session.negotiation_history.append(NegotiationTurn(
                turn_number=self.session.turn,
                speaker="system",
                action_type="accept",
                clause_id=action.clause_id,
                content=f"✅ Agreement reached on '{clause.title if clause else action.clause_id}'",
            ))
            
        done = self.is_complete()
        if done:
            self.session.status = "completed"
            
        return self.get_observation(role), 0.0, done
        
    def get_full_history(self) -> List[NegotiationTurn]:
        return self.session.negotiation_history
        
    def get_private_history(self, role: NegotiationRole) -> List[NegotiationTurn]:
        # Filter internal reasoning of the opponent
        history = deepcopy(self.session.negotiation_history)
        for t in history:
            if t.speaker != f"{role.value}_agent" and t.speaker != "system":
                t.internal_reasoning = None
        return history
        
    def is_complete(self) -> bool:
        agreed = sum(1 for c in self.clauses.values() if c.status == "agreed")
        if agreed == len(self.clauses) or self.session.turn >= self.session.max_turns:
            return True
        return False
        
    def get_final_contract(self) -> str:
        text_parts = []
        for c in self.clauses.values():
            text_parts.append(f"{c.title}:")
            if c.status == "agreed" and c.id in self.session.final_agreed_clauses:
                text_parts.append(self.session.final_agreed_clauses[c.id])
            else:
                text_parts.append(c.text)
        return "\n\n".join(text_parts)
