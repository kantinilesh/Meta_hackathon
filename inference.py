import os
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AGENT_SYSTEM_PROMPT = """You are a legal contract negotiation expert AI agent.
Read each contract clause carefully and decide the best action.
For Task 1: flag each clause as fair, unfair, or neutral with a reason.
For Task 2: propose improved replacement text for unfair clauses.
For Task 3: negotiate multi-turn to reach agreement with the counterparty.
Always respond with valid JSON matching the Action schema exactly."""

@dataclass
class EpisodeResult:
    task_id: str
    score: float
    steps: int
    total_reward: float
    duration_seconds: float
    passed: bool

class ContractAgent:
    def __init__(self, env_base_url, openai_client):
        self.env_base_url = env_base_url
        self.client = openai_client
        self.model = os.getenv("MODEL_NAME", "gpt-4o-mini")
        import httpx
        self.http = httpx.Client(base_url=self.env_base_url, timeout=30.0)

    def reset_episode(self, task_id) -> tuple[dict, str]:
        resp = self.http.post("/reset", json={"task_id": task_id}).json()
        return resp["observation"], resp["session_id"]

    def decide_action(self, observation, task_id) -> dict:
        clause = observation["clauses"][0]
        if task_id == "task1":
            prompt = f"Flag this clause: {clause}. Return {{\"clause_id\": \"{clause['id']}\", \"action_type\":\"flag\", \"label\": \"fair\", \"reason\": \"none\"}}"
        elif task_id == "task2":
            prompt = f"Rewrite this clause to be fair: {clause}. Return {{\"clause_id\": \"{clause['id']}\", \"action_type\":\"propose\", \"proposed_text\": \"fairer text\"}}"
        else:
            prompt = f"Negotiate: {clause}. Return {{\"clause_id\": \"{clause['id']}\", \"action_type\": \"accept\"}}"

        try:
            res = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
        except:
            return {"clause_id": clause['id'], "action_type": "skip"}

    def run_episode(self, task_id) -> EpisodeResult:
        start_time = time.time()
        obs, session_id = self.reset_episode(task_id)
        
        total_reward = 0.0
        steps = 0
        done = False
        
        while not done and steps < obs["max_turns"]:
            action = self.decide_action(obs, task_id)
            resp = self.http.post("/step", json={"session_id": session_id, "action": action}).json()
            obs = resp["observation"]
            total_reward += resp["reward"]["value"]
            done = resp["done"]
            steps += 1
            
        grade_resp = self.http.post("/grade", json={"session_id": session_id, "task_id": task_id}).json()
        
        return EpisodeResult(
            task_id=task_id,
            score=grade_resp["score"],
            steps=steps,
            total_reward=total_reward,
            duration_seconds=time.time() - start_time,
            passed=grade_resp["passed"]
        )

def main():
    if not os.getenv("API_BASE_URL") or not os.getenv("MODEL_NAME"):
        print("Missing required env vars: API_BASE_URL, MODEL_NAME")
        return

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"), base_url=os.getenv("API_BASE_URL"))
    agent = ContractAgent("http://localhost:7860", openai_client)
    
    task_results = []
    total_time = 0.0
    total_score = 0.0
    for task_id in ["task1", "task2", "task3"]:
        print(f"[START] task={task_id}", flush=True)
        res = agent.run_episode(task_id)
        task_results.append({
            "task_id": task_id,
            "score": res.score,
            "passed": res.passed,
            "steps": res.steps,
            "duration_seconds": res.duration_seconds,
        })
        total_time += res.duration_seconds
        total_score += res.score
        print(
            f"[STEP] step={res.steps} reward={res.total_reward:.4f}",
            flush=True,
        )
        print(
            f"[END] task={task_id} score={res.score:.4f} steps={res.steps} passed={str(res.passed).lower()} duration={res.duration_seconds:.4f}",
            flush=True,
        )

    results = {
        "environment": "contract-env",
        "version": "1.0.0",
        "model": os.getenv("MODEL_NAME"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tasks": task_results,
        "average_score": total_score / len(task_results) if task_results else 0.0,
        "total_duration_seconds": total_time,
    }

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"Total Inference Time: {total_time:.2f}s (< 1200s required)", flush=True)

if __name__ == "__main__":
    main()
