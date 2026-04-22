import json
from typing import Dict, Any

PRODUCT_SALES_CONTRACT = {
    "title": "Product Sales Agreement",
    "clauses": [
        {
            "id": "c1",
            "title": "Product Specifications",
            "text": "The Seller agrees to provide the 'Cloud Analytics Platform', a SaaS solution featuring real-time data streaming, up to 1TB of monthly storage, and 5 enterprise user licenses as specified in the service level agreement.",
            "category": "scope"
        },
        {
            "id": "c2",
            "title": "Delivery Timeline",
            "text": "The platform access shall be provisioned within 14 days of contract signing.",
            "category": "duration"
        },
        {
            "id": "c3",
            "title": "Payment and Price",
            "text": "The Client agrees to pay the Seller a total sum of $10,000 annually, net 30 days from invoice.",
            "category": "payment"
        },
        {
            "id": "c4",
            "title": "Liability",
            "text": "The total aggregate liability of the Seller for all claims related to this agreement shall not exceed the amount actually paid by the Client to the Seller during the twelve (12) months immediately preceding the event giving rise to the claim.",
            "category": "liability"
        }
    ]
}

def load_product_contract() -> Dict[str, Any]:
    return PRODUCT_SALES_CONTRACT
