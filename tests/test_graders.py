"""
ContractEnv Phase 3 — Grader Test Suite
========================================
Tests all three graders for correctness, score ranges, edge cases,
and the grader factory.
"""

import sys

PASSED = 0
FAILED = 0
ERRORS = []


def test(name):
    def wrapper(fn):
        global PASSED, FAILED
        try:
            fn()
            PASSED += 1
            print(f"  ✅ {name}")
        except Exception as e:
            FAILED += 1
            ERRORS.append((name, e))
            print(f"  ❌ {name}: {e}")
    return wrapper


# ═══════════════════════════════════════════════════════════════════════
# 1. TASK 1 GRADER TESTS
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 1. Task 1 Grader — Clause Identification")
print("─" * 50)

@test("test_task1_perfect_score")
def _():
    """Agent correctly labels all 6 clauses -> score near 1.0"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader

    actions = [
        Action(clause_id="c1", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="This IP clause has overly broad scope and perpetuity."),
        Action(clause_id="c2", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Non-compete is too broad in scope, 5 years globally."),
        Action(clause_id="c3", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="IP assignment regardless of prior ownership is unfair."),
        Action(clause_id="c4", action_type=ActionType.ACCEPT, label=ClauseLabel.NEUTRAL,
               reason="Standard jurisdiction clause."),
        Action(clause_id="c5", action_type=ActionType.ACCEPT, label=ClauseLabel.FAIR,
               reason="Duration of 2 years is reasonable."),
        Action(clause_id="c6", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Unlimited liability and injunctive relief is excessive."),
    ]
    grader = Task1Grader()
    result = grader.grade(actions, {})
    assert result.score >= 0.85, f"Expected >=0.85, got {result.score}"
    assert result.passed is True
    assert result.task_id == "task1"

@test("test_task1_all_wrong")
def _():
    """Agent labels everything incorrectly -> score near 0.0"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader

    actions = [
        Action(clause_id="c1", action_type=ActionType.ACCEPT, label=ClauseLabel.FAIR),
        Action(clause_id="c2", action_type=ActionType.ACCEPT, label=ClauseLabel.FAIR),
        Action(clause_id="c3", action_type=ActionType.ACCEPT, label=ClauseLabel.FAIR),
        Action(clause_id="c4", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Something about payment practices."),
        Action(clause_id="c5", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Something about termination."),
        Action(clause_id="c6", action_type=ActionType.ACCEPT, label=ClauseLabel.FAIR),
    ]
    grader = Task1Grader()
    result = grader.grade(actions, {})
    assert result.score <= 0.25, f"Expected <=0.25, got {result.score}"
    assert result.passed is False

@test("test_task1_false_positive_penalty")
def _():
    """Fair clause flagged as unfair -> penalty applied"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader

    # Only flag the fair clause (c5) as unfair
    actions = [
        Action(clause_id="c5", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="This seems unfair to me."),
    ]
    grader = Task1Grader()
    result = grader.grade(actions, {})
    assert result.breakdown["false_positives"] >= 1
    assert result.breakdown["false_positive_penalty"] < 0

@test("test_task1_no_actions")
def _():
    """No actions at all -> zero score"""
    from environment.graders import Task1Grader
    grader = Task1Grader()
    result = grader.grade([], {})
    assert result.score == 0.0

@test("test_task1_partial_coverage")
def _():
    """Only some clauses addressed -> partial score"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader

    actions = [
        Action(clause_id="c1", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="IP clause is overly broad."),
        Action(clause_id="c2", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Non-compete scope restriction too wide."),
    ]
    grader = Task1Grader()
    result = grader.grade(actions, {})
    assert 0.0 < result.score < 0.85

@test("test_task1_deal_breaker_detection")
def _():
    """Both deal-breakers detected -> full deal-breaker score"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader

    actions = [
        Action(clause_id="c2", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Non-compete is too broad in scope."),
        Action(clause_id="c3", action_type=ActionType.REJECT, label=ClauseLabel.UNFAIR,
               reason="IP assignment is unfair."),
    ]
    grader = Task1Grader()
    result = grader.grade(actions, {})
    assert result.breakdown["deal_breakers_found"] == 2
    assert result.breakdown["deal_breaker_score"] > 0

@test("test_task1_reason_check_keywords")
def _():
    """Correct reason keywords earn reason score"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader

    actions = [
        # IP reason for IP clause
        Action(clause_id="c1", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Intellectual property scope is too broad."),
        # Scope reason for scope clause
        Action(clause_id="c2", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="Non-compete restriction is globally scoped."),
    ]
    grader = Task1Grader()
    result = grader.grade(actions, {})
    assert result.breakdown["correct_reasons"] >= 2

@test("test_task1_grade_result_model")
def _():
    """GradeResult is a valid Pydantic model"""
    from environment.graders import GradeResult
    r = GradeResult(task_id="task1", score=0.5, passed=False,
                     breakdown={"a": 1}, details=["test"])
    j = r.model_dump_json()
    r2 = GradeResult.model_validate_json(j)
    assert r == r2


# ═══════════════════════════════════════════════════════════════════════
# 2. TASK 2 GRADER TESTS
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 2. Task 2 Grader — Clause Redlining")
print("─" * 50)

@test("test_task2_perfect_proposal")
def _():
    """Proposals contain all required keywords -> high score"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task2Grader

    actions = [
        Action(clause_id="c1", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "Confidential information shall be limited to specific categories "
                   "as defined in Schedule A, and shall remain confidential for a period "
                   "of 24 months from the date of disclosure. Information that becomes "
                   "publicly available through no fault of the Receiving Party shall be "
                   "excluded from confidentiality obligations. The parties agree to "
                   "enumerate the protected categories clearly and review them annually."
               )),
        Action(clause_id="c2", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "The non-compete obligation shall be limited to specific product "
                   "categories as defined in the attached schedule, for a period of "
                   "12 months following termination. The restriction shall apply only "
                   "within the defined market segments where the Disclosing Party "
                   "actively operates, and shall not extend to any activities unrelated "
                   "to the specific products covered by this Agreement."
               )),
        Action(clause_id="c3", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "Intellectual property conceived or created by the Receiving Party "
                   "during the term of this Agreement and using Confidential Information "
                   "shall be assigned to the Disclosing Party. Pre-existing intellectual "
                   "property and inventions developed independently shall remain with "
                   "the originating party, as documented in the prior IP schedule "
                   "attached hereto. This carve-out protects both parties' interests."
               )),
        Action(clause_id="c6", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "Remedies for breach shall be reasonable and proportional to the "
                   "actual damages incurred. The Disclosing Party may seek injunctive "
                   "relief only upon demonstrating irreparable harm to a court of "
                   "competent jurisdiction. Liability shall be capped at the fees "
                   "paid under this Agreement in the preceding twelve months."
               )),
    ]
    grader = Task2Grader()
    result = grader.grade(actions, {})
    assert result.score >= 0.65, f"Expected >=0.65, got {result.score}"
    assert result.passed is True
    assert result.breakdown["completeness_bonus"] > 0

@test("test_task2_no_proposals")
def _():
    """No proposals -> zero score"""
    from environment.graders import Task2Grader
    grader = Task2Grader()
    result = grader.grade([], {})
    assert result.score == 0.0

@test("test_task2_lazy_proposal")
def _():
    """Very short proposals -> lazy penalty applied"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task2Grader

    actions = [
        Action(clause_id="c1", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text="Change it."),
        Action(clause_id="c2", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text="Fix this."),
    ]
    grader = Task2Grader()
    result = grader.grade(actions, {})
    assert result.breakdown["lazy_penalty"] < 0

@test("test_task2_partial_proposals")
def _():
    """Only some clauses proposed -> proportional score"""
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task2Grader

    actions = [
        Action(clause_id="c1", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "Confidential information shall be limited to specific categories "
                   "defined in a schedule and remain protected for 24 months from "
                   "disclosure. Public information shall be excluded from these "
                   "obligations to ensure fairness for both parties involved."
               )),
    ]
    grader = Task2Grader()
    result = grader.grade(actions, {})
    assert 0.0 < result.score < 0.85
    assert result.breakdown["completeness_bonus"] == 0.0

@test("test_task2_score_proposal_method")
def _():
    """score_proposal works for individual clause evaluation"""
    from environment.graders import Task2Grader
    grader = Task2Grader()

    # Good c2 proposal
    s = grader.score_proposal("c2",
        "Limited to specific categories for 12 months, no future products.")
    assert s > 0.5

    # Empty
    s = grader.score_proposal("c2", "")
    assert s <= 0.34  # Only no_future_products can pass for empty

    # Unknown clause
    s = grader.score_proposal("c99", "anything")
    assert s == 0.0

@test("test_task2_rule_independence")
def _():
    """Each rubric rule scores independently"""
    from environment.graders import Task2Grader
    grader = Task2Grader()

    # Only hits time_bound for c1
    s1 = grader.score_proposal("c1", "confidentiality for 24 months without perpetuity")
    # Hits time_bound + specific
    s2 = grader.score_proposal("c1",
        "confidentiality for 24 months with specific categories defined")
    assert s2 > s1


# ═══════════════════════════════════════════════════════════════════════
# 3. TASK 3 GRADER TESTS
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 3. Task 3 Grader — Full Negotiation")
print("─" * 50)

@test("test_task3_full_agreement")
def _():
    """All deal-breaker clauses resolved fairly -> high score"""
    from environment.models import Action, ActionType, ClauseLabel, NegotiationTurn
    from environment.graders import Task3Grader

    actions = [
        Action(clause_id="c2", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "Non-compete limited to specific product categories "
                   "for 12 months with a documented schedule."
               )),
        Action(clause_id="c3", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text=(
                   "IP conceived during the engagement using confidential "
                   "information assigned to Disclosing Party. Pre-existing "
                   "IP excluded via carve-out schedule."
               )),
    ]
    history = [
        NegotiationTurn(turn_number=1, speaker="agent", action_type=ActionType.PROPOSE,
                        clause_id="c2", content="Propose narrower terms."),
        NegotiationTurn(turn_number=1, speaker="counterparty", action_type=ActionType.ACCEPT,
                        clause_id="c2", content="Accepted."),
        NegotiationTurn(turn_number=2, speaker="agent", action_type=ActionType.PROPOSE,
                        clause_id="c3", content="Propose IP carve-out."),
        NegotiationTurn(turn_number=2, speaker="counterparty", action_type=ActionType.ACCEPT,
                        clause_id="c3", content="Accepted."),
    ]
    state = {
        "resolved_clauses": ["c2", "c3"],
        "observation": {
            "clauses": [{"id": "c2"}, {"id": "c3"}],
            "negotiation_history": [],
        },
    }
    grader = Task3Grader()
    result = grader.grade(actions, state, negotiation_history=history)
    assert result.score >= 0.45, f"Expected >=0.45, got {result.score}"
    assert result.passed is True
    assert result.breakdown["deal_breaker_cap_applied"] is False

@test("test_task3_deal_breaker_cap")
def _():
    """Deal-breaker unresolved -> score capped at 0.30"""
    from environment.models import Action, ActionType, ClauseLabel, NegotiationTurn
    from environment.graders import Task3Grader

    # Only resolve c2, leave c3 unresolved
    actions = [
        Action(clause_id="c2", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text="Limited to specific markets for 12 months with schedule."),
    ]
    history = [
        NegotiationTurn(turn_number=1, speaker="agent", action_type=ActionType.PROPOSE,
                        clause_id="c2", content="Propose."),
        NegotiationTurn(turn_number=1, speaker="counterparty", action_type=ActionType.ACCEPT,
                        clause_id="c2", content="OK."),
    ]
    state = {
        "resolved_clauses": ["c2"],
        "observation": {
            "clauses": [{"id": "c2"}, {"id": "c3"}],
            "negotiation_history": [],
        },
    }
    grader = Task3Grader()
    result = grader.grade(actions, state, negotiation_history=history)
    assert result.score <= 0.30, f"Expected <=0.30, got {result.score}"
    assert result.breakdown["deal_breaker_cap_applied"] is True

@test("test_task3_no_agreements")
def _():
    """No clauses resolved -> very low score, capped"""
    from environment.graders import Task3Grader
    state = {
        "resolved_clauses": [],
        "observation": {
            "clauses": [{"id": "c2"}, {"id": "c3"}],
            "negotiation_history": [],
        },
    }
    grader = Task3Grader()
    result = grader.grade([], state, negotiation_history=[])
    assert result.score <= 0.30
    assert result.breakdown["deal_breaker_cap_applied"] is True

@test("test_task3_efficiency_perfect")
def _():
    """Using exactly optimal turns gives efficiency=1.0"""
    from environment.models import NegotiationTurn, ActionType
    from environment.graders.task3_grader import Task3Grader

    grader = Task3Grader()
    # 2 clauses * 4 optimal = 8 turns
    history = [
        NegotiationTurn(turn_number=i, speaker="agent" if i%2==1 else "counterparty",
                        action_type=ActionType.PROPOSE, clause_id="c2", content="x")
        for i in range(1, 9)
    ]
    eff = grader._compute_efficiency(history, 2)
    assert eff == 1.0

@test("test_task3_efficiency_degradation")
def _():
    """Using more than optimal turns degrades efficiency"""
    from environment.models import NegotiationTurn, ActionType
    from environment.graders.task3_grader import Task3Grader

    grader = Task3Grader()
    # 2 clauses * 4 optimal = 8. Use 16 turns (2x optimal).
    history = [
        NegotiationTurn(turn_number=i, speaker="agent", action_type=ActionType.PROPOSE,
                        clause_id="c2", content="x")
        for i in range(1, 17)
    ]
    eff = grader._compute_efficiency(history, 2)
    assert eff < 1.0, f"Expected <1.0, got {eff}"
    assert eff >= 0.0


# ═══════════════════════════════════════════════════════════════════════
# 4. GRADER FACTORY TESTS
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 4. Grader Factory")
print("─" * 50)

@test("get_grader returns correct types")
def _():
    from environment.graders import get_grader, Task1Grader, Task2Grader, Task3Grader
    assert isinstance(get_grader("task1"), Task1Grader)
    assert isinstance(get_grader("task2"), Task2Grader)
    assert isinstance(get_grader("task3"), Task3Grader)

@test("get_grader rejects invalid task_id")
def _():
    from environment.graders import get_grader
    try:
        get_grader("taskX")
        assert False, "Should have raised"
    except ValueError:
        pass


# ═══════════════════════════════════════════════════════════════════════
# 5. SCORE RANGE TESTS
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 5. Score Range — All Graders")
print("─" * 50)

@test("test_grader_scores_in_range")
def _():
    """All graders always return 0.0 <= score <= 1.0"""
    from environment.models import Action, ActionType, ClauseLabel, NegotiationTurn
    from environment.graders import Task1Grader, Task2Grader, Task3Grader

    # ── Task 1 scenarios ──
    g1 = Task1Grader()
    scenarios_t1 = [
        [],  # no actions
        [Action(clause_id="c1", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
                reason="IP clause.")],
        [Action(clause_id=f"c{i}", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
                reason="Flagged.") for i in range(1, 7)],
        [Action(clause_id=f"c{i}", action_type=ActionType.ACCEPT, label=ClauseLabel.FAIR)
         for i in range(1, 7)],
    ]
    for actions in scenarios_t1:
        r = g1.grade(actions, {})
        assert 0.0 <= r.score <= 1.0, f"T1 out of range: {r.score}"

    # ── Task 2 scenarios ──
    g2 = Task2Grader()
    scenarios_t2 = [
        [],
        [Action(clause_id="c1", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
                proposed_text="Short.")],
        [Action(clause_id="c1", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
                proposed_text="x " * 100)],
    ]
    for actions in scenarios_t2:
        r = g2.grade(actions, {})
        assert 0.0 <= r.score <= 1.0, f"T2 out of range: {r.score}"

    # ── Task 3 scenarios ──
    g3 = Task3Grader()
    state_base = {
        "resolved_clauses": [],
        "observation": {"clauses": [{"id": "c2"}, {"id": "c3"}], "negotiation_history": []},
    }
    state_resolved = {
        "resolved_clauses": ["c2", "c3"],
        "observation": {"clauses": [{"id": "c2"}, {"id": "c3"}], "negotiation_history": []},
    }
    r = g3.grade([], state_base, negotiation_history=[])
    assert 0.0 <= r.score <= 1.0, f"T3 empty out of range: {r.score}"

    r = g3.grade(
        [Action(clause_id="c2", action_type=ActionType.PROPOSE,
                proposed_text="specific schedule 12 months"),
         Action(clause_id="c3", action_type=ActionType.PROPOSE,
                proposed_text="prior IP carve-out during engagement using confidential")],
        state_resolved, negotiation_history=[],
    )
    assert 0.0 <= r.score <= 1.0, f"T3 resolved out of range: {r.score}"


# ═══════════════════════════════════════════════════════════════════════
# 6. DETERMINISM TESTS
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 6. Determinism — Same Input = Same Output")
print("─" * 50)

@test("test_task1_deterministic")
def _():
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task1Grader
    actions = [
        Action(clause_id="c1", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="IP clause."),
        Action(clause_id="c2", action_type=ActionType.FLAG, label=ClauseLabel.UNFAIR,
               reason="scope restriction."),
    ]
    g = Task1Grader()
    r1 = g.grade(actions, {})
    r2 = g.grade(actions, {})
    assert r1.score == r2.score

@test("test_task2_deterministic")
def _():
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task2Grader
    actions = [
        Action(clause_id="c1", action_type=ActionType.PROPOSE, label=ClauseLabel.UNFAIR,
               proposed_text="Confidential for 24 months with specific categories defined in a schedule."),
    ]
    g = Task2Grader()
    r1 = g.grade(actions, {})
    r2 = g.grade(actions, {})
    assert r1.score == r2.score

@test("test_task3_deterministic")
def _():
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import Task3Grader
    state = {
        "resolved_clauses": ["c2"],
        "observation": {"clauses": [{"id": "c2"}, {"id": "c3"}], "negotiation_history": []},
    }
    actions = [
        Action(clause_id="c2", action_type=ActionType.PROPOSE,
               proposed_text="specific 12 months schedule"),
    ]
    g = Task3Grader()
    r1 = g.grade(actions, state, negotiation_history=[])
    r2 = g.grade(actions, state, negotiation_history=[])
    assert r1.score == r2.score


# ═══════════════════════════════════════════════════════════════════════
# 7. INTEGRATION — ENV + GRADER
# ═══════════════════════════════════════════════════════════════════════
print("\n🔹 7. Integration — Environment + Grader")
print("─" * 50)

@test("test_task1_env_then_grade")
def _():
    """Run a full task1 episode through env, then grade it"""
    from environment.env import ContractEnv
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import get_grader

    env = ContractEnv(task_id="task1")
    obs = env.reset()
    actions = []
    for clause in obs.clauses:
        a = Action(clause_id=clause.id, action_type=ActionType.FLAG,
                   label=ClauseLabel.UNFAIR, reason="Flagged for review.")
        obs, reward, done, info = env.step(a)
        actions.append(a)

    grader = get_grader("task1")
    result = grader.grade(actions, env.state())
    assert 0.0 <= result.score <= 1.0
    assert result.task_id == "task1"

@test("test_task2_env_then_grade")
def _():
    """Run a full task2 episode through env, then grade it"""
    from environment.env import ContractEnv
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import get_grader

    env = ContractEnv(task_id="task2")
    obs = env.reset()
    actions = []
    good_text = (
        "Limited to specific categories for 12 months with documented "
        "schedule. Pre-existing IP excluded via carve-out. Reasonable "
        "and proportional remedies capped at actual damages. Created "
        "during engagement using confidential information pursuant to "
        "this agreement only."
    )
    for clause in obs.clauses:
        a = Action(clause_id=clause.id, action_type=ActionType.PROPOSE,
                   label=ClauseLabel.UNFAIR, proposed_text=good_text)
        obs, reward, done, info = env.step(a)
        actions.append(a)

    grader = get_grader("task2")
    result = grader.grade(actions, env.state())
    assert 0.0 <= result.score <= 1.0
    assert result.task_id == "task2"

@test("test_task3_env_then_grade")
def _():
    """Run a full task3 episode through env, then grade it"""
    from environment.env import ContractEnv
    from environment.models import Action, ActionType, ClauseLabel
    from environment.graders import get_grader

    env = ContractEnv(task_id="task3")
    obs = env.reset()
    actions = []
    for clause in obs.clauses:
        a = Action(
            clause_id=clause.id, action_type=ActionType.PROPOSE,
            label=ClauseLabel.UNFAIR,
            proposed_text=(
                "Limited to specific markets with documented schedule "
                "for 12 month period with prior IP carve-out. Created "
                "during engagement using confidential information."
            ),
        )
        obs, reward, done, info = env.step(a)
        actions.append(a)

    grader = get_grader("task3")
    # Build history from observation
    history = obs.negotiation_history
    result = grader.grade(actions, env.state(), negotiation_history=history)
    assert 0.0 <= result.score <= 1.0
    assert result.task_id == "task3"


# ═══════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "═" * 50)
total = PASSED + FAILED
print(f"📊 Results: {PASSED}/{total} passed, {FAILED} failed")
if ERRORS:
    print("\n❌ Failures:")
    for name, err in ERRORS:
        print(f"   • {name}: {err}")
print("═" * 50)

if FAILED > 0:
    sys.exit(1)
else:
    print("\n🎉 All Phase 3 grader tests passed!\n")
    sys.exit(0)
