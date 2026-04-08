import math
from typing import Tuple, Dict, Any
from .models import Action, Observation, Reward, RewardBreakdown, NegotiationTurn
from .contracts.nda_template import load_contract
from .counterparty import Counterparty

class ContractEnv:
    def __init__(self, task_id="task1", party_config=None):
        self.task_id = task_id
        contract_data = load_contract(task_id)
        self.contract_id = contract_data["contract_id"]
        self.contract_title = contract_data["title"]
        self.contract_text = contract_data["text"]
        self.clauses = {c.id: c for c in contract_data["clauses"]}
        self.max_turns = contract_data["metadata"]["max_turns"]
        self.turn = 0
        self.history = []
        self.counterparty = Counterparty()
        self.party_config = party_config

    def reset(self) -> Observation:
        self.turn = 0
        self.history = []
        contract_data = load_contract(self.task_id)
        self.clauses = {c.id: c for c in contract_data["clauses"]}
        
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
            total_clauses=len(self.clauses)
        )

    def state(self) -> Dict[str, Any]:
        return {"observation": self._get_observation().model_dump()}

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self.turn += 1
        done = False
        info = {}
        reward_breakdown = RewardBreakdown()
        
        clause = self.clauses.get(action.clause_id)
        if not clause:
            return self._get_observation(), Reward(value=-0.1, breakdown=reward_breakdown, done=done, info={"error": "Invalid clause id"}), done, info
            
        reward_val = 0.0
        
        # TASK 1 Logic
        if self.task_id == "task1" and action.action_type == "flag":
            if action.label == clause.ground_truth_label and clause.ground_truth_label == "unfair":
                reward_breakdown.flag_correct += 0.10
                if action.reason:
                    reward_breakdown.label_correct += 0.05
            elif action.label == "unfair" and clause.ground_truth_label != "unfair":
                reward_breakdown.false_positive_penalty -= 0.15
                
            self.history.append(NegotiationTurn(
                turn_number=self.turn,
                speaker="system",
                action_type=action.action_type,
                clause_id=action.clause_id,
                content=f"Evaluated label: {action.label}",
                reward_delta=sum(reward_breakdown.model_dump().values())
            ))
            
        # TASK 2 Logic
        elif self.task_id == "task2" and action.action_type == "propose":
            if not action.proposed_text:
                reward_val -= 0.1
            else:
                clause.current_proposed_text = action.proposed_text
                clause.status = "in_negotiation"
                
                pt_lower = action.proposed_text.lower()
                if "year" in pt_lower or "month" in pt_lower:
                    reward_breakdown.proposal_quality += 0.10
                if "region" in pt_lower or "specific" in pt_lower:
                    reward_breakdown.proposal_quality += 0.10
                if "carve-out" in pt_lower or "prior" in pt_lower:
                    reward_breakdown.proposal_quality += 0.08
                
                self.history.append(NegotiationTurn(
                    turn_number=self.turn,
                    speaker="system",
                    action_type=action.action_type,
                    clause_id=action.clause_id,
                    content="Proposed redline.",
                    proposed_text=action.proposed_text,
                    reward_delta=sum(reward_breakdown.model_dump().values())
                ))

        # TASK 3 Logic 
        elif self.task_id == "task3":
            if action.action_type == "propose":
                cp_resp = self.counterparty.respond(clause, action.proposed_text or "", self.turn)
                reward_breakdown.proposal_quality += cp_resp.score_impact
                
                if cp_resp.response_type == "accept":
                    clause.status = "agreed"
                    clause.current_proposed_text = cp_resp.modified_text or action.proposed_text
                    reward_breakdown.agreement_bonus += 0.20
                elif cp_resp.response_type == "deal_breaker_reject":
                    reward_breakdown.break_counterparty_deal_breaker = -0.30

                # Persist the proposal outcome so grading can recover task progress later.
                self.history.append(NegotiationTurn(
                    turn_number=self.turn,
                    speaker="system",
                    action_type=action.action_type,
                    clause_id=action.clause_id,
                    content="Negotiation proposal evaluated.",
                    proposed_text=action.proposed_text,
                    reward_delta=sum(reward_breakdown.model_dump().values())
                ))

                # Counterparty turn
                self.history.append(NegotiationTurn(
                    turn_number=self.turn,
                    speaker="client_agent",
                    action_type=action.action_type,
                    clause_id=action.clause_id,
                    content=cp_resp.message,
                    proposed_text=cp_resp.modified_text,
                ))

            # check if all clauses agreed or max turns reached
            agreed = sum(1 for c in self.clauses.values() if c.status == "agreed")
            if agreed == len(self.clauses):
                reward_breakdown.agreement_bonus += 0.25
                done = True
        
        # turn budget penalty
        if self.turn > self.max_turns:
            done = True
            reward_breakdown.turn_efficiency_penalty -= 0.10
            
        reward_val = sum(reward_breakdown.model_dump().values())
        reward_val = max(-1.0, min(1.0, reward_val))
        
        obs = self._get_observation(current_clause_id=action.clause_id)
        reward = Reward(value=reward_val, breakdown=reward_breakdown, done=done, info=info)
        return obs, reward, done, info
