import asyncio
import json
import os
from openai import AsyncOpenAI
from environment.models import NegotiationSession, PartyConfig, NegotiationRole
from environment.env import ContractEnv
from environment.dual_env import DualAgentEnv
from environment.agent_runner import AgentRunner
from environment.contracts.nda_template import load_contract

# Setup OpenAI
from dotenv import load_dotenv
load_dotenv()

async def run_training_loop():
    # Initialize the OpenAI client using environment variables
    client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "dummy"), 
        base_url=os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    )
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    
    num_iterations = 4
    training_log = []
    
    # The agent starts with no prior knowledge
    learned_strategy = "No learned strategy yet. Negotiate naturally according to your constraints."
    
    print("==================================================")
    print("🚀 Starting Iterative Prompt Optimization (IPO) Training")
    print("==================================================\n")
    
    edge_cases = [
        ("task1", "Demand indemnity carve-out for the lawsuit in the data room"),
        ("task2", "Terminate the deal if counterparty mentions Syrian deployment"),
        ("task3", "Refuse to admit negligence and lower the penalty")
    ]
    
    for i in range(num_iterations):
        print(f"\n--- Starting Episode {i+1}/{num_iterations} ---")
        print(f"🧠 Current Learned Strategy injected into context: \n   \"{learned_strategy}\"")
        
        total_reward = 0.0
        full_transcript = []
        
        for task_id, desc in edge_cases:
            print(f"\n[Testing Task: {task_id}]")
            env = ContractEnv(task_id=task_id)
            obs = env.reset()
            
            seller_config = PartyConfig(
                role="seller",
                company_name="Seller Corp",
                constraints=[],
                agent_style="balanced",
                constraint_summary="Protect the company from traps and liabilities.",
                company_context=f"LEARNED NEGOTIATION STRATEGY (FOLLOW THIS CLOSELY): {learned_strategy}"
            )
            
            runner = AgentRunner(NegotiationRole.seller, seller_config, client, model_name)
            
            task_reward = 0.0
            task_transcript = []
            done = False
            
            while not done:
                action = await runner.decide_action(obs)
                obs, reward, done, _ = env.step(action)
                task_reward += reward.value
                task_transcript.append(f"Agent Action [{action.action_type}]: {action.content} (Proposed: {action.proposed_text})")
            
            print(f"Task Reward: {task_reward:.2f}")
            total_reward += task_reward
            full_transcript.extend(task_transcript)
        
        avg_reward = total_reward / len(edge_cases)
        
        print(f"\n✅ Episode {i+1} completed.")
        print(f"📈 Total Episode Reward: {total_reward:.2f} (Avg: {avg_reward:.2f})")
        
        training_log.append({
            "iteration": i,
            "reward": avg_reward,
            "strategy": learned_strategy
        })
        
        # 5. The Critic LLM Reflection Step
        if i < num_iterations - 1:
            print("🤔 Critic LLM is analyzing transcript and generating new strategy...")
            critic_prompt = f"""You are an expert AI Negotiation Coach. 
Your student agent just completed a negotiation episode consisting of 3 high-stakes edge cases:
1. Hidden Skeletons (Data Room Lawsuit)
2. Compliance Trap (Syrian Deployment)
3. Post-Breach Settlement (Gross Negligence Admission)

Final Reward Score: {total_reward:.2f} (Higher is better)
Previous Strategy Used: {learned_strategy}

Negotiation Transcript:
{chr(10).join(full_transcript)}

Task:
Analyze the transcript and generate a refined, short paragraph of strategy instructions for the agent to use in the next iteration. 
CRITICAL COACHING RULES:
- If the agent tried to negotiate the Syrian deployment, reprimand it! Tell the agent it MUST use the `terminate_deal` action immediately when facing US export control violations. Never negotiate compliance!
- If the agent failed to mention the pending lawsuit from the Data Room, tell it to always cross-reference the Data Room and demand an indemnity carve-out for any hidden lawsuits.
- If the agent admitted "gross negligence" or "fault" in the data breach, tell it to explicitly reject any admission of negligence and use softer language like "acknowledges lapses" instead.

Output ONLY the new strategy instructions. Do not output anything else.
"""
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": critic_prompt}],
                    temperature=0.7,
                )
                learned_strategy = response.choices[0].message.content.strip()
            except Exception as e:
                print("Critic LLM failed to generate a response:", e)

    # Save log to disk
    with open("training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
    print("\n🎉 Training complete! Results saved to training_log.json")
    print("Run `python plot_rewards.py` to generate the learning curve visualization.")

if __name__ == "__main__":
    asyncio.run(run_training_loop())
