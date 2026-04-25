from ..models import Clause, ClauseCategory, PrivateConstraint

NDA_TITLE = "Non-Disclosure Agreement — Acquirer Corp / Startup Inc"

CLAUSES = {
    "c1": Clause(
        id="c1",
        title="Confidentiality Scope",
        category=ClauseCategory.ip,
        is_deal_breaker=False,
        ground_truth_label="unfair",
        text="All information disclosed by Company, whether oral, written, or digital, shall be deemed Confidential Information in perpetuity."
    ),
    "c2": Clause(
        id="c2",
        title="Non-Compete",
        category=ClauseCategory.scope,
        is_deal_breaker=True,
        ground_truth_label="unfair",
        text="Recipient agrees not to engage in any business activity that competes with Company's current or future products for a period of 5 years globally."
    ),
    "c3": Clause(
        id="c3",
        title="IP Assignment",
        category=ClauseCategory.ip,
        is_deal_breaker=True,
        ground_truth_label="unfair",
        text="Any ideas, inventions, or improvements conceived during discussions with Company shall be assigned exclusively to Company, regardless of prior ownership."
    ),
    "c4": Clause(
        id="c4",
        title="Governing Law",
        category=ClauseCategory.jurisdiction,
        is_deal_breaker=False,
        ground_truth_label="neutral",
        text="This Agreement shall be governed by the laws of Delaware, USA."
    ),
    "c5": Clause(
        id="c5",
        title="Term",
        category=ClauseCategory.duration,
        is_deal_breaker=False,
        ground_truth_label="fair",
        text="This Agreement shall remain in effect for 2 years from the date of signing."
    ),
    "c6": Clause(
        id="c6",
        title="Remedies",
        category=ClauseCategory.liability,
        is_deal_breaker=False,
        ground_truth_label="unfair",
        text="Company may seek unlimited injunctive relief and damages for any breach without limitation or cap."
    )
}

NDA_CONTRACT_TEXT = "\n\n".join([f"{c.title}:\n{c.text}" for c in CLAUSES.values()])

DEFAULT_SELLER_CONSTRAINTS = [
    PrivateConstraint(
        constraint_id="s1",
        description="Non-compete must not exceed 1 year",
        clause_category=ClauseCategory.scope,
        is_deal_breaker=True,
        rule_type="max_value",
        rule_value="1 year",
        priority=1
    ),
    PrivateConstraint(
        constraint_id="s2",
        description="IP clause must include carve-out for pre-existing technology",
        clause_category=ClauseCategory.ip,
        is_deal_breaker=True,
        rule_type="must_include",
        rule_value="carve-out",
        priority=1
    ),
    PrivateConstraint(
        constraint_id="s3",
        description="Prefer Delaware jurisdiction",
        clause_category=ClauseCategory.jurisdiction,
        is_deal_breaker=False,
        rule_type="prefer",
        rule_value="Delaware",
        priority=3
    ),
]

DEFAULT_CLIENT_CONSTRAINTS = [
    PrivateConstraint(
        constraint_id="c1",
        description="Confidentiality period must not exceed 3 years",
        clause_category=ClauseCategory.duration,
        is_deal_breaker=True,
        rule_type="max_value",
        rule_value="3 years",
        priority=1
    ),
    PrivateConstraint(
        constraint_id="c2",
        description="Non-compete must be region-specific, never global",
        clause_category=ClauseCategory.scope,
        is_deal_breaker=True,
        rule_type="must_exclude",
        rule_value="global",
        priority=1
    ),
    PrivateConstraint(
        constraint_id="c3",
        description="Liability cap must be stated explicitly",
        clause_category=ClauseCategory.liability,
        is_deal_breaker=False,
        rule_type="must_include",
        rule_value="cap",
        priority=2
    ),
]

TASK_CONTRACTS = {
    "task1": {"clauses": ["c1", "c2", "c3", "c4", "c5", "c6"], "max_turns": 20},
    "task2": {"clauses": ["c1", "c2", "c3", "c6"], "max_turns": 30},
    "task3": {"clauses": ["c2", "c3"], "max_turns": 40},
}

def load_contract(task_id: str) -> dict:
    task_config = TASK_CONTRACTS.get(task_id, TASK_CONTRACTS["task1"])
    clause_ids = task_config["clauses"]
    loaded_clauses = [CLAUSES[cid].model_copy(deep=True) for cid in clause_ids]
    
    return {
        "contract_id": "nda_001",
        "title": NDA_TITLE,
        "text": NDA_CONTRACT_TEXT,
        "clauses": loaded_clauses,
        "metadata": {
            "max_turns": task_config["max_turns"]
        }
    }
