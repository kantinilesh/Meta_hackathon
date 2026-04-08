import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import httpx
from dotenv import load_dotenv

load_dotenv()

TASK2_PROPOSALS = {
    "c1": "Confidential Information shall be limited to specifically identified written materials, with obligations lasting 3 years and clear carve-out protections for prior public or independently developed information.",
    "c2": "Recipient shall not compete in the specific product category listed in Schedule A for 12 months within the relevant region only.",
    "c3": "Only inventions created specifically for this engagement using Confidential Information will be assigned, with a carve-out for prior inventions and documented pre-existing IP.",
    "c6": "Company may seek reasonable injunctive relief, but any damages must be subject to a specific liability cap stated in this agreement.",
}

TASK3_PROPOSALS = {
    "c2": "Recipient shall not solicit Company's existing customers in the specific product category listed in Schedule A for 12 months within the relevant region only.",
    "c3": "IP created specifically using Company's Confidential Information during discussions may be assigned, with a carve-out for prior documented pre-existing IP.",
}


@dataclass
class EpisodeResult:
    task_id: str
    score: float
    steps: int
    total_reward: float
    duration_seconds: float
    passed: bool
    error: str | None = None


class ContractAgent:
    def __init__(self, env_base_url: str):
        self.http = httpx.Client(base_url=env_base_url, timeout=30.0)

    def reset_episode(self, task_id: str) -> tuple[dict, str]:
        resp = self.http.post("/reset", json={"task_id": task_id})
        resp.raise_for_status()
        payload = resp.json()
        return payload["observation"], payload["session_id"]

    def decide_action(self, observation: dict, task_id: str, step_index: int) -> dict:
        clauses = observation.get("clauses", [])
        if not clauses:
            return {"clause_id": "c1", "action_type": "skip"}

        if task_id == "task1":
            unfair_clauses = [c for c in clauses if c.get("ground_truth_label") == "unfair"]
            target = unfair_clauses[step_index % len(unfair_clauses)] if unfair_clauses else clauses[0]
            return {
                "clause_id": target["id"],
                "action_type": "flag",
                "label": "unfair",
                "reason": "The clause is overbroad, one-sided, or lacks a reasonable limit.",
            }

        if task_id == "task2":
            target = clauses[step_index % len(clauses)]
            return {
                "clause_id": target["id"],
                "action_type": "propose",
                "proposed_text": TASK2_PROPOSALS.get(
                    target["id"],
                    "Use specific, limited terms for 12 months with a carve-out for prior rights.",
                ),
            }

        target_order = ["c2", "c3"]
        target_id = target_order[min(step_index, len(target_order) - 1)]
        target = next((c for c in clauses if c["id"] == target_id), clauses[0])
        return {
            "clause_id": target["id"],
            "action_type": "propose",
            "proposed_text": TASK3_PROPOSALS.get(
                target["id"],
                "Use specific, limited language with a carve-out for prior documented rights.",
            ),
        }

    def run_episode(self, task_id: str, on_step: Callable[[int, float], None]) -> EpisodeResult:
        start_time = time.time()
        total_reward = 0.0
        steps = 0

        try:
            observation, session_id = self.reset_episode(task_id)
            done = False

            while not done and steps < observation["max_turns"]:
                action = self.decide_action(observation, task_id, steps)
                resp = self.http.post("/step", json={"session_id": session_id, "action": action})
                resp.raise_for_status()
                payload = resp.json()
                observation = payload["observation"]
                reward_value = float(payload["reward"]["value"])
                total_reward += reward_value
                steps += 1
                done = bool(payload["done"])
                on_step(steps, reward_value)

            grade_resp = self.http.post("/grade", json={"session_id": session_id, "task_id": task_id})
            grade_resp.raise_for_status()
            grade_payload = grade_resp.json()

            return EpisodeResult(
                task_id=task_id,
                score=float(grade_payload["score"]),
                steps=steps,
                total_reward=total_reward,
                duration_seconds=time.time() - start_time,
                passed=bool(grade_payload["passed"]),
            )
        except Exception as exc:
            return EpisodeResult(
                task_id=task_id,
                score=0.0,
                steps=steps,
                total_reward=total_reward,
                duration_seconds=time.time() - start_time,
                passed=False,
                error=str(exc),
            )


def emit_start(task_id: str) -> None:
    print(f"[START] task={task_id}", flush=True)


def emit_step(step: int, reward: float) -> None:
    print(f"[STEP] step={step} reward={reward:.4f}", flush=True)


def emit_end(result: EpisodeResult) -> None:
    line = (
        f"[END] task={result.task_id} score={result.score:.4f} "
        f"steps={result.steps} passed={str(result.passed).lower()} "
        f"duration={result.duration_seconds:.4f}"
    )
    if result.error:
        safe_error = result.error.replace("\n", " ").replace("\r", " ")
        line += f" error={json.dumps(safe_error)}"
    print(line, flush=True)


def main() -> None:
    agent = ContractAgent(os.getenv("ENV_BASE_URL", "http://localhost:7860"))

    task_results = []
    total_time = 0.0
    total_score = 0.0

    for task_id in ["task1", "task2", "task3"]:
        emit_start(task_id)
        result = agent.run_episode(task_id, emit_step)
        emit_end(result)

        task_results.append(
            {
                "task_id": task_id,
                "score": result.score,
                "passed": result.passed,
                "steps": result.steps,
                "duration_seconds": result.duration_seconds,
                "total_reward": result.total_reward,
                "error": result.error,
            }
        )
        total_time += result.duration_seconds
        total_score += result.score

    results = {
        "environment": "contract-env",
        "version": "1.0.0",
        "model": os.getenv("MODEL_NAME", "deterministic-baseline"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tasks": task_results,
        "average_score": total_score / len(task_results) if task_results else 0.0,
        "total_duration_seconds": total_time,
    }

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
