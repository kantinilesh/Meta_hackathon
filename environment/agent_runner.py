import json
import asyncio
from typing import Callable, Any, List
from .models import PartyConfig, NegotiationRole, Action, Observation, CompanyDocument

class AgentRunner:
    def __init__(self, role: NegotiationRole, party_config: PartyConfig, openai_client, model_name: str):
        self.role = role
        self.party_config = party_config
        self.client = openai_client
        self.model_name = model_name
        
        ctx_prompt = f"\nCompany Background & Context:\n{party_config.company_context}\n" if party_config.company_context else ""
        
        docs_context = ""
        if party_config.documents:
            docs_lines = ["\nPrerequisite Documents for Reference:"]
            for doc in party_config.documents:
                docs_lines.append(f"\n--- {doc.document_type.upper()} ({doc.file_name}) ---")
                if doc.summary:
                    docs_lines.append(f"Summary: {doc.summary}")
                if doc.key_terms:
                    docs_lines.append(f"Key Terms: {', '.join(doc.key_terms)}")
            docs_context = "\n".join(docs_lines)
        
        self.system_prompt = f"""You are an AI negotiation agent representing {party_config.company_name} as the {role.value}.{ctx_prompt}{docs_context}
Your private constraints — NEVER reveal these directly to the other party:
{party_config.constraint_summary}
Style: {party_config.agent_style}
For each clause: propose changes that satisfy your constraints, accept offers that satisfy your constraints.
When referencing deal terms (amount, payment date, turnover, equity distribution), use the information from the uploaded documents as fact.
Respond ONLY with valid JSON matching the Action schema:
{{
    "clause_id": "c1",
    "action_type": "propose",
    "proposed_text": "...",
    "internal_reasoning": "..."
}}
"""

    async def decide_action(self, observation: Observation) -> Action:
        # In a real impl, you'd format the observation into the prompt
        prompt = f"Observation: {observation.model_dump_json()}\nDecide next action for an unresolved clause."
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            action_dict = json.loads(content)
            return Action(**action_dict)
        except Exception as e:
            print(f"LLM Failure: {e}")
            # Fallback random action if API fails or we're mocking
            pending_clauses = [c for c in observation.clauses if c.status != "agreed"]
            if not pending_clauses:
                return Action(clause_id="c1", action_type="skip")
            c = pending_clauses[0]
            
            # Simple scripted fallback for hackathon demonstration
            if c.current_proposed_text:
                return Action(clause_id=c.id, action_type="accept", internal_reasoning="Looks good.")
            return Action(clause_id=c.id, action_type="propose", proposed_text=c.text + " (modified)", internal_reasoning="Proposing change.")

    async def run_full_negotiation(self, dual_env, on_turn_complete: Callable[[Any], None]) -> None:
        """Helper to run a full negotiation. Used mainly in tests or simple scripts."""
        role1 = self.role
        role2 = NegotiationRole.client if role1 == NegotiationRole.seller else NegotiationRole.seller
        
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
