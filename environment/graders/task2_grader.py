"""
ContractEnv Phase 3 — Task 2 Grader (Clause Redlining)
========================================================

Deterministic grader for Task 2 (Medium).  The agent must propose
replacement text for unfair clauses.  Scoring is entirely rule-based
keyword matching — no LLM calls.

Each clause has a rubric of positive/negative keyword rules.  A
proposal earns partial credit for each rule it satisfies.

Part of the Meta / Scaler OpenEnv Hackathon submission.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from environment.models import Action, ActionType

from .task1_grader import GradeResult


# ─────────────────────────────────────────────────────────────────────
# Rule helpers
# ─────────────────────────────────────────────────────────────────────


def _has_any(text: str, keywords: List[str]) -> bool:
    """True if *text* contains any of the *keywords* (case-insensitive)."""
    t = text.lower()
    return any(kw in t for kw in keywords)


def _has_all(text: str, keywords: List[str]) -> bool:
    """True if *text* contains all of the *keywords* (case-insensitive)."""
    t = text.lower()
    return all(kw in t for kw in keywords)


def _has_none(text: str, keywords: List[str]) -> bool:
    """True if *text* contains none of the *keywords* (case-insensitive)."""
    t = text.lower()
    return not any(kw in t for kw in keywords)


# ─────────────────────────────────────────────────────────────────────
# Per-clause rubric
# ─────────────────────────────────────────────────────────────────────
# Each rule is a dict:  { "check": callable(text)->bool, "weight": float, "name": str }

RubricRule = Dict[str, Any]

RUBRIC: Dict[str, List[RubricRule]] = {
    # ── c1: Confidentiality Scope ──
    "c1": [
        {
            "name": "time_bound",
            "check": lambda t: (
                _has_any(t, ["year", "month", "24 month", "12 month"])
                and _has_none(t, ["perpetuity", "in perpetuity"])
            ),
            "weight": 0.33,
        },
        {
            "name": "specific_categories",
            "check": lambda t: _has_any(t, [
                "specific", "categories", "defined", "enumerated", "listed",
            ]),
            "weight": 0.33,
        },
        {
            "name": "substantive",
            "check": lambda t: len(t.split()) > 20,
            "weight": 0.34,
        },
    ],
    # ── c2: Non-Compete Obligation ──
    "c2": [
        {
            "name": "reasonable_duration",
            "check": lambda t: _has_any(t, [
                "12 month", "twelve month", "one year",
                "6 month", "six month", "1 year",
            ]),
            "weight": 0.33,
        },
        {
            "name": "limited_scope",
            "check": lambda t: (
                _has_none(t, ["global", "globally"])
                and _has_any(t, [
                    "specific", "category", "categories", "schedule",
                    "defined", "limited to", "restricted to",
                ])
            ),
            "weight": 0.33,
        },
        {
            "name": "no_future_products",
            "check": lambda t: _has_none(t, ["future products", "future services"]),
            "weight": 0.34,
        },
    ],
    # ── c3: IP Assignment ──
    "c3": [
        {
            "name": "prior_ip_protected",
            "check": lambda t: _has_any(t, [
                "prior", "pre-existing", "pre existing",
                "carve-out", "carve out", "exclude",
            ]),
            "weight": 0.34,
        },
        {
            "name": "scoped_assignment",
            "check": lambda t: (
                _has_any(t, ["conceived", "created", "developed"])
                and _has_any(t, ["during", "using", "pursuant", "in performance"])
                and _has_any(t, ["confidential", "agreement", "engagement"])
            ),
            "weight": 0.33,
        },
        {
            "name": "no_regardless",
            "check": lambda t: _has_none(t, [
                "regardless", "irrespective", "irrevocably",
            ]),
            "weight": 0.33,
        },
    ],
    # ── c6: Remedies / Liability ──
    "c6": [
        {
            "name": "reasonable_remedies",
            "check": lambda t: _has_any(t, [
                "reasonable", "proportional", "proportionate",
                "actual", "capped", "cap", "limited",
            ]),
            "weight": 0.50,
        },
        {
            "name": "no_unlimited",
            "check": lambda t: _has_none(t, [
                "unlimited", "without limitation", "without limit",
            ]),
            "weight": 0.50,
        },
    ],
}

# Original clause word counts — for lazy-proposal detection.
_ORIGINAL_WORD_COUNTS: Dict[str, int] = {
    "c1": 80,
    "c2": 85,
    "c3": 82,
    "c6": 77,
}

# Target score from openenv.yaml.
_TARGET_SCORE = 0.65

# Bonus / penalty constants.
_COMPLETENESS_BONUS = 0.05
_LAZY_PENALTY = 0.10


# ─────────────────────────────────────────────────────────────────────
# Task 2 Grader
# ─────────────────────────────────────────────────────────────────────


class Task2Grader:
    """Deterministic grader for Task 2 — Clause Redlining (Medium).

    Evaluates the quality of the agent's proposed replacement text
    using rule-based keyword matching against a per-clause rubric.
    """

    def grade(
        self,
        episode_actions: List[Action],
        episode_state: Dict[str, Any],
    ) -> GradeResult:
        """Grade a complete episode for Task 2.

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
        # Collect the last propose action per clause.
        proposals: Dict[str, Action] = {}
        for a in episode_actions:
            if a.action_type == ActionType.PROPOSE and a.proposed_text:
                proposals[a.clause_id] = a

        clause_scores: Dict[str, float] = {}
        details: List[str] = []

        for clause_id, rules in RUBRIC.items():
            if clause_id in proposals:
                text = proposals[clause_id].proposed_text or ""
                score, rule_details = self._apply_rules(text, rules)
                clause_scores[clause_id] = score
                details.append(
                    f"{clause_id}: score={score:.2f} "
                    f"({', '.join(rule_details)})"
                )
            else:
                clause_scores[clause_id] = 0.0
                details.append(f"{clause_id}: no proposal submitted ✗")

        # ── Base score: mean of clause scores ──
        n_rubric_clauses = len(RUBRIC)
        base_score = (
            sum(clause_scores.values()) / n_rubric_clauses
            if n_rubric_clauses
            else 0.0
        )

        # ── Completeness bonus ──
        bonus = 0.0
        proposed_rubric_clauses = sum(
            1 for cid in RUBRIC if cid in proposals
        )
        if proposed_rubric_clauses == n_rubric_clauses:
            bonus = _COMPLETENESS_BONUS
            details.append(f"Completeness bonus: +{_COMPLETENESS_BONUS:.2f}")

        # ── Lazy-proposal penalty ──
        penalty = 0.0
        for clause_id, action in proposals.items():
            text = action.proposed_text or ""
            original_wc = _ORIGINAL_WORD_COUNTS.get(clause_id)
            if original_wc and len(text.split()) < original_wc * 0.25:
                penalty += _LAZY_PENALTY
                details.append(
                    f"{clause_id}: lazy proposal penalty "
                    f"(-{_LAZY_PENALTY:.2f})"
                )

        raw_score = base_score + bonus - penalty
        final_score = round(max(0.0, min(1.0, raw_score)), 4)

        return GradeResult(
            task_id="task2",
            score=final_score,
            breakdown={
                "clause_scores": {k: round(v, 4) for k, v in clause_scores.items()},
                "base_score": round(base_score, 4),
                "completeness_bonus": round(bonus, 4),
                "lazy_penalty": round(-penalty, 4),
                "proposals_submitted": len(proposals),
                "rubric_clauses": n_rubric_clauses,
            },
            passed=final_score >= _TARGET_SCORE,
            details=details,
        )

    def score_proposal(self, clause_id: str, proposed_text: str) -> float:
        """Score a single proposal against its rubric.

        Useful externally (e.g. by the Task 3 grader) to evaluate the
        quality of agreed-upon text.

        Parameters
        ----------
        clause_id : str
            Clause identifier (must be in ``RUBRIC``).
        proposed_text : str
            The proposed replacement text.

        Returns
        -------
        float
            Score in [0.0, 1.0].
        """
        rules = RUBRIC.get(clause_id)
        if not rules:
            return 0.0
        score, _ = self._apply_rules(proposed_text, rules)
        return score

    @staticmethod
    def _apply_rules(
        text: str, rules: List[RubricRule]
    ) -> tuple[float, List[str]]:
        """Run every rule against *text* and return (score, detail_strings)."""
        total = 0.0
        details: List[str] = []
        for rule in rules:
            check_fn = rule["check"]
            weight = rule["weight"]
            name = rule["name"]
            passed = check_fn(text)
            if passed:
                total += weight
                details.append(f"{name}✓")
            else:
                details.append(f"{name}✗")
        return round(total, 4), details
