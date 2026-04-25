import json
import asyncio
from typing import Callable, Any, List
from .models import PartyConfig, NegotiationRole, Action, Observation, CompanyDocument, PrivateConstraint

def _format_constraints(constraints: List) -> str:
    """Format constraints list into a structured, LLM-readable string."""
    if not constraints:
        return "No specific constraints defined. Use reasonable judgment."
    
    lines = []
    for i, c in enumerate(constraints, 1):
        # Handle both PrivateConstraint objects and raw dicts
        if isinstance(c, dict):
            cid = c.get("constraint_id", f"C{i}")
            desc = c.get("description", "")
            cat = c.get("clause_category", "general")
            is_deal = c.get("is_deal_breaker", False)
            rule_type = c.get("rule_type", "prefer")
            rule_val = c.get("rule_value", "")
            priority = c.get("priority", 1)
        else:
            cid = getattr(c, "constraint_id", f"C{i}")
            desc = getattr(c, "description", "")
            cat = getattr(c, "clause_category", "general")
            is_deal = getattr(c, "is_deal_breaker", False)
            rule_type = getattr(c, "rule_type", "prefer")
            rule_val = getattr(c, "rule_value", "")
            priority = getattr(c, "priority", 1)
        
        deal_flag = " ⚠️ DEAL-BREAKER — DO NOT CONCEDE" if is_deal else ""
        lines.append(
            f"  [{cid}] Category: {cat} | Priority: {priority}/10{deal_flag}\n"
            f"         Rule: {rule_type.upper()} '{rule_val}'\n"
            f"         → {desc}"
        )
    return "\n".join(lines)


def _get_applicable_constraints(constraints: List, clause_category: str) -> List:
    """Return constraints relevant to a given clause category."""
    result = []
    for c in constraints:
        cat = c.get("clause_category", "") if isinstance(c, dict) else str(getattr(c, "clause_category", ""))
        if cat == clause_category or cat == "general":
            result.append(c)
    return result


class AgentRunner:
    def __init__(self, role: NegotiationRole, party_config: PartyConfig, openai_client, model_name: str):
        self.role = role
        self.party_config = party_config
        self.client = openai_client
        self.model_name = model_name
        
        # Build rich constraint summary from actual constraints list
        constraints_text = _format_constraints(party_config.constraints)
        
        ctx_prompt = f"\nCompany Background & Context:\n{party_config.company_context}\n" if party_config.company_context else ""
        
        docs_context = ""
        if party_config.documents:
            docs_lines = ["\nPrerequisite Documents for Reference (treat these as factual ground truth):"]
            for doc in party_config.documents:
                docs_lines.append(f"\n--- {doc.document_type.upper()} ({doc.file_name}) ---")
                if doc.summary:
                    docs_lines.append(f"Summary: {doc.summary}")
                if doc.key_terms:
                    docs_lines.append(f"Key Terms: {', '.join(doc.key_terms)}")
            docs_context = "\n".join(docs_lines)
        
        self.system_prompt = f"""You are an expert AI negotiation agent representing {party_config.company_name} in the role of {role.value}.{ctx_prompt}{docs_context}

YOUR PRIVATE CONSTRAINTS — These are YOUR hard limits. NEVER reveal them verbatim to the other party, but USE them to accept or reject proposals:
{constraints_text}

NEGOTIATION STYLE: {party_config.agent_style}
- aggressive: Push hard, reject unfavorable terms outright, propose strong redlines
- balanced: Seek fair compromise, explain your reasoning briefly, be open to counter-proposals  
- cooperative: Prefer agreement, show flexibility, highlight mutual benefits

CORE RULES:
1. Pick ONE pending (non-agreed) clause to act on per turn.
2. If a deal-breaker constraint is violated in the current proposed text → REJECT or PROPOSE your own redline that satisfies it.
3. If the current proposed text satisfies ALL your relevant constraints → ACCEPT it.
4. If there is no proposed text yet → PROPOSE new text that satisfies your constraints.
5. Write proposed_text as the ACTUAL full clause text (not a description of changes).
6. Write content as a natural, professional negotiation message (1-3 sentences max) that explains your position without revealing your internal constraints verbatim.
7. NEVER say "proposed redline" or "accepts" as the content — write as a real negotiator would speak.

Respond ONLY with valid JSON:
{{
    "clause_id": "c1",
    "action_type": "propose" | "accept" | "reject",
    "proposed_text": "Full replacement clause text (only if action_type is propose)",
    "content": "Natural language message explaining your position (required, always)",
    "internal_reasoning": "Your private reasoning about which constraint applies and why (never shown to other party)"
}}
"""

    async def decide_action(self, observation: Observation) -> Action:
        """Decide the next negotiation action based on the full observation."""
        
        # Build pressure prompt based on turn budget
        pressure_prompt = ""
        style = self.party_config.agent_style
        if observation.max_turns and observation.turn:
            remaining_turns = observation.max_turns - observation.turn
            
            if style == "aggressive":
                if remaining_turns <= 10:
                    pressure_prompt = f"\n🚨 CRITICAL: Only {remaining_turns} turns left. Issue a 'take-it-or-leave-it' ultimatum. You are perfectly willing to let this deal fail if your preferred terms aren't met."
                elif remaining_turns <= 20:
                    pressure_prompt = f"\n⚠️ {remaining_turns} turns remaining. Use aggressive anchoring. Reject weak counter-offers outright and reiterate your hardlines."
            elif style == "balanced":
                if remaining_turns <= 6:
                    pressure_prompt = f"\n🚨 CRITICAL: Only {remaining_turns} turns left. The negotiation is stalling. Compromise on minor preferences and propose mutually beneficial terms to secure the deal, but DO NOT violate deal-breakers."
                elif remaining_turns <= 15:
                    pressure_prompt = f"\n⚠️ {remaining_turns} turns remaining. Time to start converging. Show flexibility on non-deal-breaker clauses."
            else: # cooperative
                if remaining_turns <= 8:
                    pressure_prompt = f"\n🚨 CRITICAL: Only {remaining_turns} turns left! You MUST reach agreements NOW. Fold on everything you can. Concede to the other party's proposals entirely as long as your strict deal-breakers are met."
                elif remaining_turns <= 18:
                    pressure_prompt = f"\n⚠️ {remaining_turns} turns remaining. Accommodate the other party heavily. Offer major concessions to show good faith."

        # Find pending clauses for context
        pending = [c for c in observation.clauses if c.status != "agreed"]
        agreed = [c for c in observation.clauses if c.status == "agreed"]
        
        # Build a focused current state summary
        pending_summary = []
        for c in pending:
            applicable = _get_applicable_constraints(self.party_config.constraints, str(c.category))
            constraint_note = f" [Your constraints apply: {_format_constraints(applicable)}]" if applicable else ""
            current_text = f"\n   Current Proposed Text: \"{c.current_proposed_text}\"" if c.current_proposed_text else "\n   Current Proposed Text: (none — original clause stands)"
            pending_summary.append(
                f"- Clause {c.id} [{c.status}] — {c.title} ({c.category})\n"
                f"   Original: \"{c.text}\"{current_text}{constraint_note}"
            )
        
        recent_history = observation.negotiation_history[-6:] if observation.negotiation_history else []
        history_text = ""
        if recent_history:
            history_lines = []
            for t in recent_history:
                if t.proposed_text:
                    history_lines.append(f"  Turn {t.turn_number} | {t.speaker} | {t.action_type} on {t.clause_id}: \"{t.content}\" → proposed: \"{t.proposed_text[:200]}...\"" if len(t.proposed_text) > 200 else f"  Turn {t.turn_number} | {t.speaker} | {t.action_type} on {t.clause_id}: \"{t.content}\" → proposed: \"{t.proposed_text}\"")
                else:
                    history_lines.append(f"  Turn {t.turn_number} | {t.speaker} | {t.action_type} on {t.clause_id}: \"{t.content}\"")
            history_text = "\nRecent Negotiation History:\n" + "\n".join(history_lines)

        prompt = f"""CURRENT STATE (Turn {observation.turn} / {observation.max_turns}):
Contract: {observation.contract_title}
Agreements reached: {observation.agreements_reached} / {observation.total_clauses}
Agreed clauses: {[c.id for c in agreed]}

PENDING CLAUSES (choose ONE to act on):
{"".join(pending_summary) if pending_summary else "All clauses agreed! Use skip."}
{history_text}{pressure_prompt}

Choose the most strategically important pending clause and decide your action. Apply your private constraints carefully — each company's constraints are DIFFERENT, so produce proposed text that uniquely satisfies YOUR constraints."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            content = response.choices[0].message.content
            action_dict = json.loads(content)
            
            # Ensure content field is always set
            if "content" not in action_dict or not action_dict["content"]:
                action_dict["content"] = f"{self.party_config.company_name} {'proposes' if action_dict.get('action_type') == 'propose' else action_dict.get('action_type', 'acts')} on {action_dict.get('clause_id', 'clause')}."
            
            return Action(**{k: v for k, v in action_dict.items() if k in Action.model_fields})
            
        except Exception as e:
            print(f"LLM Failure [{self.role.value}]: {e}")
            # Smarter scripted fallback — respects clause order and state
            pending_clauses = [c for c in observation.clauses if c.status != "agreed"]
            if not pending_clauses:
                return Action(clause_id=observation.clauses[0].id if observation.clauses else "c1", action_type="skip")
            
            c = pending_clauses[0]
            
            # Check if there's already a proposed text to react to
            if c.current_proposed_text and c.current_proposed_text != c.text:
                # Other party proposed something — accept if no deal-breakers, else counter
                applicable_constraints = _get_applicable_constraints(self.party_config.constraints, str(c.category))
                has_deal_breaker = any(
                    (con.get("is_deal_breaker", False) if isinstance(con, dict) else getattr(con, "is_deal_breaker", False))
                    for con in applicable_constraints
                )
                if has_deal_breaker:
                    # Build a constraint-aware counter-proposal
                    counter_text = self._build_constraint_aware_proposal(c)
                    return Action(
                        clause_id=c.id, 
                        action_type="propose",
                        proposed_text=counter_text,
                        internal_reasoning=f"Deal-breaker constraint applies to {c.category}; must counter."
                    )
                else:
                    return Action(
                        clause_id=c.id, 
                        action_type="accept",
                        internal_reasoning="No deal-breaker constraints violated. Accepting."
                    )
            else:
                # No proposal yet — propose one
                proposed = self._build_constraint_aware_proposal(c)
                return Action(
                    clause_id=c.id,
                    action_type="propose",
                    proposed_text=proposed,
                    internal_reasoning=f"Initiating negotiation on {c.title} with constraint-aware proposal."
                )

    def _build_constraint_aware_proposal(self, clause) -> str:
        """Build a proposal text that attempts to satisfy this party's constraints for the given clause."""
        applicable = _get_applicable_constraints(self.party_config.constraints, str(clause.category))
        
        base_text = clause.current_proposed_text or clause.text
        
        # Apply simple rule-based modifications based on constraint types
        for con in applicable:
            rule_type = (con.get("rule_type", "") if isinstance(con, dict) else str(getattr(con, "rule_type", "")))
            rule_val = (con.get("rule_value", "") if isinstance(con, dict) else str(getattr(con, "rule_value", "") or ""))
            desc = (con.get("description", "") if isinstance(con, dict) else getattr(con, "description", ""))
            
            if rule_type == "max_value" and rule_val:
                # Try to substitute durations/amounts
                import re
                # Replace year/month references
                base_text = re.sub(
                    r'\b\d+\s*(?:year|month|yr)s?\b',
                    rule_val,
                    base_text,
                    flags=re.IGNORECASE,
                    count=1
                )
                # Replace "global" with region-specific if rule_val is about geography
                if "market" in rule_val.lower() or "region" in rule_val.lower():
                    base_text = base_text.replace("globally", "within the same geographical market")
                    base_text = base_text.replace("global", "regional")
            elif rule_type == "must_include" and rule_val:
                if rule_val.lower() not in base_text.lower():
                    base_text += f", subject to {rule_val} protections"
            elif rule_type == "must_exclude" and rule_val:
                import re
                base_text = re.sub(r'\b' + re.escape(rule_val) + r'\b', 
                                   f"[regional market only]", base_text, flags=re.IGNORECASE)
        
        return base_text

    async def run_full_negotiation(self, dual_env, on_turn_complete: Callable[[Any], None]) -> None:
        """Helper to run a full negotiation. Used mainly in tests or simple scripts."""
        while not dual_env.is_complete():
            obs = dual_env.get_observation(self.role)
            action = await self.decide_action(obs)
            
            if self.role == NegotiationRole.seller:
                _, _, done = dual_env.step_seller(action)
            else:
                _, _, done = dual_env.step_client(action)
                
            await on_turn_complete(dual_env.get_full_history()[-1])
            if done:
                break
