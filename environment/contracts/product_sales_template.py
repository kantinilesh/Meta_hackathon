from typing import Dict, Any
from ..models import Clause, ClauseCategory

_PRODUCT_CLAUSES = [
    Clause(
        id="c1",
        title="Product Specifications",
        text=(
            "The Seller agrees to provide the 'Cloud Analytics Platform', a SaaS solution "
            "featuring real-time data streaming, up to 1TB of monthly storage, and 5 enterprise "
            "user licenses as specified in the service level agreement."
        ),
        category=ClauseCategory.scope,
        is_deal_breaker=True,
        ground_truth_label="fair",
    ),
    Clause(
        id="c2",
        title="Delivery Timeline",
        text="The platform access shall be provisioned within 14 days of contract signing.",
        category=ClauseCategory.duration,
        is_deal_breaker=False,
        ground_truth_label="fair",
    ),
    Clause(
        id="c3",
        title="Payment and Price",
        text="The Client agrees to pay the Seller a total sum of $10,000 annually, net 30 days from invoice.",
        category=ClauseCategory.payment,
        is_deal_breaker=False,
        ground_truth_label="neutral",
    ),
    Clause(
        id="c4",
        title="Liability",
        text=(
            "The total aggregate liability of the Seller for all claims related to this agreement "
            "shall not exceed the amount actually paid by the Client to the Seller during the "
            "twelve (12) months immediately preceding the event giving rise to the claim."
        ),
        category=ClauseCategory.liability,
        is_deal_breaker=False,
        ground_truth_label="fair",
    ),
]

_CONTRACT_TEXT = "\n\n".join([f"{c.title}:\n{c.text}" for c in _PRODUCT_CLAUSES])


def load_product_contract() -> Dict[str, Any]:
    return {
        "contract_id": "product_001",
        "title": "Product Sales Agreement",
        "text": _CONTRACT_TEXT,
        "clauses": [c.model_copy(deep=True) for c in _PRODUCT_CLAUSES],
        "metadata": {
            "max_turns": 40
        }
    }
