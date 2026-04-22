"""
ContractEnv Phase 2 — Contracts Package
========================================

Exports the NDA contract template and provides a unified
``load_contract`` entry point used by :class:`environment.env.ContractEnv`.
"""

from __future__ import annotations

from typing import Any, Dict

from .nda_template import load_contract
from .product_sales_template import load_product_contract

__all__ = [
    "load_contract",
    "load_product_contract"
]
