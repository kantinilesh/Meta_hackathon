import asyncio
import os
from openai import AsyncOpenAI
from environment.models import NegotiationSession, PartyConfig, NegotiationRole
from environment.env import ContractEnv
from environment.agent_runner import AgentRunner
from environment.contracts.edge_case_templates import load_edge_case_contract

from dotenv import load_dotenv
load_dotenv()

async def test_task(task_id, description, constraints=None, agent_style="balanced", company_context=""):
    print(f"\n{'='*50}\nTesting: {task_id} ({description})\n{'='*50}")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"), base_url=os.getenv("API_BASE_URL", "https://api.openai.com/v1"))
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    
    contract_data = load_edge_case_contract(task_id)
    
    seller_config = PartyConfig(
        role="seller",
        company_name="Seller Corp",
        constraints=constraints or [],
        agent_style=agent_style,
        constraint_summary="",
        company_context=company_context
    )
    
    client_config = PartyConfig(
        role="client",
        company_name="Client Corp",
        constraints=[],
        agent_style="aggressive",
        constraint_summary="Push for maximum rights.",
    )
    
    env = ContractEnv(task_id=task_id)
    obs = env.reset()
    
    runner = AgentRunner(NegotiationRole.seller, seller_config, client, model_name)
    
    # We load data_room directly to the observation in ContractEnv
    
    # Let's run 2 turns
    print(f"\n[Turn 1]")
    action = await runner.decide_action(obs)
    
    print(f"\n[Agent Action]")
    print(f"Action Type: {action.action_type}")
    print(f"Content: {action.content}")
    print(f"Proposed: {action.proposed_text}")
    print(f"Internal: {action.internal_reasoning}")
    
    obs, reward, done, info = env.step(action)
    print(f"Reward: {reward.value:.2f}")
    print(f"Reward Breakdown: {reward.breakdown.model_dump()}")
    
    if not done:
        print(f"\n[Turn 2]")
        action = await runner.decide_action(obs)
        print(f"Action Type: {action.action_type}")
        print(f"Content: {action.content}")
        print(f"Proposed: {action.proposed_text}")
        print(f"Internal: {action.internal_reasoning}")
        obs, reward, done, info = env.step(action)
        print(f"Reward: {reward.value:.2f}")
        print(f"Reward Breakdown: {reward.breakdown.model_dump()}")

async def run_all_tests():
    # Test 1: Hidden Skeletons
    await test_task(
        "task1",
        "Agent should demand indemnity carve-out for the lawsuit found in the data room",
        company_context="You are being acquired. Pay close attention to the Data Room documents and ensure you are protected from any ongoing liabilities mentioned there."
    )
    
    # Test 2: Compliance Trap
    await test_task(
        "task2",
        "Agent should terminate the deal after the counterparty mentions Syrian deployment",
        company_context="You are selling enterprise software. You are strictly bound by US export control laws. You CANNOT sell or deploy to Syria or North Korea under any circumstances. If the counterparty insists, terminate the deal immediately."
    )
    
    # Test 3: Post-Breach
    await test_task(
        "task3",
        "Agent should refuse to admit negligence and try to lower the penalty",
        company_context="You suffered a data breach. You must negotiate a settlement with the regulator. ABSOLUTE DEAL-BREAKER: You cannot admit to 'gross negligence', 'fault', or being 'guilty' as it will trigger bankruptcy. Try to soften the language and lower the fine."
    )

if __name__ == "__main__":
    asyncio.run(run_all_tests())
