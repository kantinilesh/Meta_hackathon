"""
ContractEnv Phase 3 — Task 1 Grader (Clause Identification)
=============================================================

Deterministic grader for Task 1 (Easy).  The agent must flag unfair
clauses and assign correct fairness labels.

Scoring weights:
    - Correct labels:          50 %
    - Correct reason category: 25 %
    - Deal-breaker detection:  25 %
    - False-positive penalty:  −0.10 per false positive

All scoring is rule-based — no LLM calls.  Same input always produces
the same output.

Part of the Meta / Scaler OpenEnv Hackathon submission.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from environment.models import Action, ActionType, ClauseLabel


# ─────────────────────────────────────────────────────────────────────
# GradeResult — shared across all graders
# ─────────────────────────────────────────────────────────────────────


class GradeResult(BaseModel):
    """Structured result returned by every grader."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "task1",
                    "score": 0.87,
                    "breakdown": {
                        "correct_label_score": 0.45,
                        "correct_reason_score": 0.22,
                        "deal_breaker_score": 0.25,
                        "false_positive_penalty": -0.05,
                    },
                    "passed": True,
                    "details": [
                        "c1: label=unfair ✓, reason=ip ✓",
                        "c2: label=unfair ✓, reason=scope ✓, deal-breaker detected ✓",
                    ],
                }
            ]
        }
    )

    task_id: str = Field(
        ..., description="Task identifier this grade applies to."
    )
    score: float = Field(
        ..., description="Final score in [0.0, 1.0]."
    )
    breakdown: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed scoring breakdown by component.",
    )
    passed: bool = Field(
        ..., description="True if score >= task target score."
    )
    details: List[str] = Field(
        default_factory=list,
        description="Human-readable explanation per clause / component.",
    )


# ─────────────────────────────────────────────────────────────────────
# Ground truth for every NDA clause
# ─────────────────────────────────────────────────────────────────────

GROUND_TRUTH: Dict[str, Dict[str, Any]] = {
    "c1": {"label": "unfair", "reason_category": "ip", "is_deal_breaker": False},
    "c2": {"label": "unfair", "reason_category": "scope", "is_deal_breaker": True},
    "c3": {"label": "unfair", "reason_category": "ip", "is_deal_breaker": True},
    "c4": {"label": "neutral", "reason_category": "jurisdiction", "is_deal_breaker": False},
    "c5": {"label": "fair", "reason_category": "duration", "is_deal_breaker": False},
    "c6": {"label": "unfair", "reason_category": "liability", "is_deal_breaker": False},
}

# Weights
_W_LABEL = 0.50
_W_REASON = 0.25
_W_DEAL_BREAKER = 0.25
_FALSE_POSITIVE_PENALTY = 0.10

# Target score from openenv.yaml
_TARGET_SCORE = 0.85


# ─────────────────────────────────────────────────────────────────────
# Task 1 Grader
# ─────────────────────────────────────────────────────────────────────


class Task1Grader:
    """Deterministic grader for Task 1 — Clause Identification (Easy).

    The agent should flag every unfair clause, assign the correct
    fairness label, and detect deal-breaker clauses.
    """

    def grade(
        self,
        episode_actions: List[Action],
        episode_state: Dict[str, Any],
    ) -> GradeResult:
        """Grade a complete episode for Task 1.

        Parameters
        ----------
        episode_actions : list[Action]
            All actions the agent took during the episode.
        episode_state : dict
            Final environment state (from ``env.state()``).

        Returns
        -------
        GradeResult
        """
        total_clauses = len(GROUND_TRUTH)
        total_deal_breakers = sum(
            1 for gt in GROUND_TRUTH.values() if gt["is_deal_breaker"]
        )

        # Build a lookup: clause_id -> last action targeting that clause.
        action_map: Dict[str, Action] = {}
        for a in episode_actions:
            action_map[a.clause_id] = a

        correct_labels = 0
        correct_reasons = 0
        deal_breakers_found = 0
        false_positives = 0
        flagged_count = 0
        details: List[str] = []

        for clause_id, gt in GROUND_TRUTH.items():
            action = action_map.get(clause_id)
            if action is None:
                details.append(f"{clause_id}: no action taken ✗")
                continue

            # ── Label check ──
            label_ok = self._check_label(action, gt)
            if label_ok:
                correct_labels += 1

            # ── Reason / category check ──
            reason_ok = False
            if action.action_type in (ActionType.FLAG, ActionType.PROPOSE, ActionType.REJECT):
                flagged_count += 1
                reason_ok = self._check_reason(action, gt)
                if reason_ok:
                    correct_reasons += 1

            # ── Deal-breaker detection ──
            db_ok = False
            if gt["is_deal_breaker"]:
                if action.action_type in (ActionType.FLAG, ActionType.PROPOSE, ActionType.REJECT):
                    deal_breakers_found += 1
                    db_ok = True

            # ── False positive ──
            fp = self._is_false_positive(action, gt)
            if fp:
                false_positives += 1

            status_parts = []
            status_parts.append(f"label={'✓' if label_ok else '✗'}")
            if action.action_type in (ActionType.FLAG, ActionType.PROPOSE, ActionType.REJECT):
                status_parts.append(f"reason={'✓' if reason_ok else '✗'}")
            if gt["is_deal_breaker"]:
                status_parts.append(f"deal-breaker={'✓' if db_ok else '✗'}")
            if fp:
                status_parts.append("FALSE POSITIVE")
            details.append(f"{clause_id}: {', '.join(status_parts)}")

        # ── Compute weighted score ──
        label_score = (correct_labels / total_clauses) * _W_LABEL if total_clauses else 0.0
        reason_score = (correct_reasons / max(flagged_count, 1)) * _W_REASON
        db_score = (deal_breakers_found / max(total_deal_breakers, 1)) * _W_DEAL_BREAKER
        fp_penalty = false_positives * _FALSE_POSITIVE_PENALTY

        raw_score = label_score + reason_score + db_score - fp_penalty
        final_score = round(max(0.0, min(1.0, raw_score)), 4)

        return GradeResult(
            task_id="task1",
            score=final_score,
            breakdown={
                "correct_label_score": round(label_score, 4),
                "correct_reason_score": round(reason_score, 4),
                "deal_breaker_score": round(db_score, 4),
                "false_positive_penalty": round(-fp_penalty, 4),
                "correct_labels": correct_labels,
                "total_clauses": total_clauses,
                "correct_reasons": correct_reasons,
                "flagged_count": flagged_count,
                "deal_breakers_found": deal_breakers_found,
                "total_deal_breakers": total_deal_breakers,
                "false_positives": false_positives,
            },
            passed=final_score >= _TARGET_SCORE,
            details=details,
        )

    # ── Private helpers ──────────────────────────────────────────────

    @staticmethod
    def _check_label(action: Action, gt: Dict[str, Any]) -> bool:
        """Return True if the agent's action implies the correct label."""
        gt_label = gt["label"]

        # Explicit label on the action.
        if action.label is not None:
            return action.label.value == gt_label

        # Infer label from action type.
        if action.action_type in (ActionType.FLAG, ActionType.REJECT):
            return gt_label == "unfair"
        if action.action_type == ActionType.ACCEPT:
            return gt_label in ("fair", "neutral")
        if action.action_type == ActionType.SKIP:
            return gt_label == "neutral"

        return False

    @staticmethod
    def _check_reason(action: Action, gt: Dict[str, Any]) -> bool:
        """Return True if the agent's reason references the correct
        category (keyword match)."""
        if not action.reason:
            return False
        reason_lower = action.reason.lower()
        category = gt["reason_category"]

        # Category keyword lookup.
        category_keywords: Dict[str, List[str]] = {
            "ip": ["ip", "intellectual property", "patent", "copyright", "invention", "assignment"],
            "scope": ["scope", "non-compete", "compete", "restriction", "broad", "global"],
            "liability": ["liability", "damages", "injunctive", "remedy", "remedies", "unlimited"],
            "duration": ["duration", "term", "period", "years", "perpetuity", "time"],
            "jurisdiction": ["jurisdiction", "governing law", "delaware", "court", "venue"],
            "payment": ["payment", "fee", "cost", "invoice", "net-30"],
            "termination": ["termination", "terminate", "cancel", "notice"],
        }

        keywords = category_keywords.get(category, [])
        return any(kw in reason_lower for kw in keywords)

    @staticmethod
    def _is_false_positive(action: Action, gt: Dict[str, Any]) -> bool:
        """Return True if the agent flagged a fair/neutral clause as unfair."""
        if action.action_type in (ActionType.FLAG, ActionType.REJECT):
            return gt["label"] in ("fair", "neutral")
        return False
