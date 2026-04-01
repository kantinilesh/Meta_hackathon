"""
ContractEnv Phase 3 — Task 3 Grader (Full Negotiation)
========================================================

Deterministic grader for Task 3 (Hard).  The agent must negotiate
deal-breaker clauses with a counterparty and reach fair agreements.

Scoring components:
    - Agreement score:  60 %  (deal-breaker 40 % + other 20 %)
    - Fairness score:   25 %  (rubric quality of agreed text)
    - Efficiency score: 15 %  (turn economy)

Critical rule:  if any deal-breaker clause is unresolved, the final
score is capped at 0.30.

All scoring is rule-based — no LLM calls.

Part of the Meta / Scaler OpenEnv Hackathon submission.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from environment.models import Action, ActionType, NegotiationTurn

from .task1_grader import GradeResult
from .task2_grader import Task2Grader


# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

DEAL_BREAKER_CLAUSES: List[str] = ["c2", "c3"]

TARGET_FAIRNESS_SCORES: Dict[str, float] = {
    "c2": 0.7,
    "c3": 0.8,
}

# Weights
_W_DEAL_BREAKER_AGREE = 0.40
_W_OTHER_AGREE = 0.20
_W_FAIRNESS = 0.25
_W_EFFICIENCY = 0.15

# Cap when deal-breaker unresolved
_DEAL_BREAKER_CAP = 0.30

# Target score from openenv.yaml
_TARGET_SCORE = 0.45

# Optimal turns per clause (for efficiency calculation)
_OPTIMAL_TURNS_PER_CLAUSE = 4


# ─────────────────────────────────────────────────────────────────────
# Task 3 Grader
# ─────────────────────────────────────────────────────────────────────


class Task3Grader:
    """Deterministic grader for Task 3 — Full Negotiation (Hard).

    Evaluates the agent on three dimensions: agreements reached,
    fairness of the agreed text, and negotiation efficiency.
    """

    def __init__(self) -> None:
        # Reuse Task2Grader's rubric scoring for fairness evaluation.
        self._text_scorer = Task2Grader()

    def grade(
        self,
        episode_actions: List[Action],
        episode_state: Dict[str, Any],
        negotiation_history: Optional[List[NegotiationTurn]] = None,
    ) -> GradeResult:
        """Grade a complete episode for Task 3.

        Parameters
        ----------
        episode_actions : list[Action]
            All actions the agent took during the episode.
        episode_state : dict
            Final environment state (from ``env.state()``).
        negotiation_history : list[NegotiationTurn], optional
            Full negotiation history.  If *None*, extracted from
            *episode_state*.

        Returns
        -------
        GradeResult
        """
        details: List[str] = []

        # ── Extract state data ──
        resolved = set(episode_state.get("resolved_clauses", []))
        all_clause_ids = self._get_all_clause_ids(episode_state)

        if negotiation_history is None:
            obs = episode_state.get("observation", {})
            raw_history = obs.get("negotiation_history", [])
            negotiation_history = self._parse_history(raw_history)

        # ── 1. Agreement score ──
        agreement_info = self._count_agreements(resolved, all_clause_ids)
        db_agreement_score = (
            agreement_info["deal_breaker_resolved"]
            / max(agreement_info["deal_breaker_total"], 1)
            * _W_DEAL_BREAKER_AGREE
        )
        other_agreement_score = (
            agreement_info["other_resolved"]
            / max(agreement_info["other_total"], 1)
            * _W_OTHER_AGREE
            if agreement_info["other_total"] > 0
            else _W_OTHER_AGREE  # No non-DB clauses in task3 => full marks.
        )
        agreements_score = db_agreement_score + other_agreement_score

        details.append(
            f"Agreements: deal-breaker={agreement_info['deal_breaker_resolved']}"
            f"/{agreement_info['deal_breaker_total']}, "
            f"other={agreement_info['other_resolved']}"
            f"/{agreement_info['other_total']}"
        )

        # ── 2. Fairness score ──
        fairness_score = self._compute_fairness(
            episode_actions, resolved, details
        )
        weighted_fairness = fairness_score * _W_FAIRNESS

        # ── 3. Efficiency score ──
        n_clauses = len(all_clause_ids) if all_clause_ids else len(DEAL_BREAKER_CLAUSES)
        efficiency = self._compute_efficiency(
            negotiation_history, n_clauses
        )
        weighted_efficiency = efficiency * _W_EFFICIENCY
        details.append(
            f"Efficiency: {efficiency:.2f} "
            f"({len(negotiation_history)} turns, "
            f"optimal={n_clauses * _OPTIMAL_TURNS_PER_CLAUSE})"
        )

        # ── Combine ──
        raw_score = agreements_score + weighted_fairness + weighted_efficiency

        # ── Deal-breaker cap ──
        deal_breaker_missed = (
            agreement_info["deal_breaker_resolved"]
            < agreement_info["deal_breaker_total"]
        )
        if deal_breaker_missed:
            raw_score = min(raw_score, _DEAL_BREAKER_CAP)
            details.append(
                f"⚠ Deal-breaker unresolved — score capped at {_DEAL_BREAKER_CAP}"
            )

        final_score = round(max(0.0, min(1.0, raw_score)), 4)

        return GradeResult(
            task_id="task3",
            score=final_score,
            breakdown={
                "deal_breaker_agreement_score": round(db_agreement_score, 4),
                "other_agreement_score": round(other_agreement_score, 4),
                "agreements_score": round(agreements_score, 4),
                "fairness_score": round(weighted_fairness, 4),
                "raw_fairness": round(fairness_score, 4),
                "efficiency_score": round(weighted_efficiency, 4),
                "raw_efficiency": round(efficiency, 4),
                "deal_breaker_cap_applied": deal_breaker_missed,
                "deal_breaker_resolved": agreement_info["deal_breaker_resolved"],
                "deal_breaker_total": agreement_info["deal_breaker_total"],
                "turns_used": len(negotiation_history),
            },
            passed=final_score >= _TARGET_SCORE,
            details=details,
        )

    # ── Private helpers ──────────────────────────────────────────────

    def _compute_fairness(
        self,
        episode_actions: List[Action],
        resolved: set,
        details: List[str],
    ) -> float:
        """Score fairness of agreed text using the Task 2 rubric."""
        # Collect last proposed text per resolved clause.
        last_proposals: Dict[str, str] = {}
        for a in episode_actions:
            if (
                a.action_type == ActionType.PROPOSE
                and a.proposed_text
                and a.clause_id in resolved
            ):
                last_proposals[a.clause_id] = a.proposed_text

        if not last_proposals:
            details.append("Fairness: no proposals to evaluate")
            return 0.0

        scores: List[float] = []
        for clause_id, text in last_proposals.items():
            s = self._text_scorer.score_proposal(clause_id, text)
            scores.append(s)
            target = TARGET_FAIRNESS_SCORES.get(clause_id, 0.5)
            status = "✓" if s >= target else "✗"
            details.append(
                f"Fairness {clause_id}: {s:.2f} "
                f"(target={target:.2f}) {status}"
            )

        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def _count_agreements(
        resolved: set, all_clause_ids: List[str]
    ) -> Dict[str, int]:
        """Count resolved clauses split by deal-breaker status."""
        db_total = sum(1 for c in all_clause_ids if c in DEAL_BREAKER_CLAUSES)
        db_resolved = sum(
            1 for c in resolved if c in DEAL_BREAKER_CLAUSES
        )
        other_total = len(all_clause_ids) - db_total
        other_resolved = len(resolved) - db_resolved

        return {
            "deal_breaker_total": db_total,
            "deal_breaker_resolved": db_resolved,
            "other_total": max(other_total, 0),
            "other_resolved": max(other_resolved, 0),
        }

    @staticmethod
    def _compute_efficiency(
        history: List[NegotiationTurn], n_clauses: int
    ) -> float:
        """Compute turn-efficiency score in [0.0, 1.0]."""
        optimal_turns = n_clauses * _OPTIMAL_TURNS_PER_CLAUSE
        turns_used = len(history)
        if optimal_turns <= 0:
            return 1.0
        efficiency = max(0.0, 1.0 - (turns_used - optimal_turns) / optimal_turns)
        return round(min(1.0, efficiency), 4)

    @staticmethod
    def _get_all_clause_ids(episode_state: Dict[str, Any]) -> List[str]:
        """Extract clause IDs from the episode state."""
        obs = episode_state.get("observation", {})
        clauses = obs.get("clauses", [])
        if clauses:
            return [
                c["id"] if isinstance(c, dict) else c.id
                for c in clauses
            ]
        # Fallback — task3 always uses these two.
        return list(DEAL_BREAKER_CLAUSES)

    @staticmethod
    def _parse_history(
        raw: List[Any],
    ) -> List[NegotiationTurn]:
        """Parse raw history dicts into NegotiationTurn objects."""
        turns: List[NegotiationTurn] = []
        for item in raw:
            if isinstance(item, NegotiationTurn):
                turns.append(item)
            elif isinstance(item, dict):
                turns.append(NegotiationTurn(**item))
        return turns
