from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from .documents import (
    ClauseAnalyticsDocument,
    ClauseOutcome,
    CompanyDocument,
    ConstraintRecord,
    ContractDocument,
    DemoRunDocument,
    LeaderboardDocument,
    PartyRecord,
    SessionDocument,
    TurnRecord,
)


async def seed_demo_data() -> None:
    now = datetime.utcnow()

    seller_one = await CompanyDocument.get_or_create("TechVentures", "seller")
    client_one = await CompanyDocument.get_or_create("Acme Corp", "client")
    seller_two = await CompanyDocument.get_or_create("StartupXYZ", "seller")
    client_two = await CompanyDocument.get_or_create("BigCorp Ltd", "client")
    seller_three = await CompanyDocument.get_or_create("AlphaVentures", "seller")
    client_three = await CompanyDocument.get_or_create("Beta Inc", "client")

    contract = await ContractDocument.find_one({"contract_title": "Seeded NDA"})
    if not contract:
        contract = ContractDocument(
            contract_id="seed-contract-001",
            contract_title="Seeded NDA",
            contract_text="Confidentiality\n\nLiability\n\nTerm",
            uploaded_by=seller_one.company_id,
            contract_type="NDA",
            clauses=[],
        )
        await contract.insert()

    session_payloads = [
        SessionDocument(
            session_id=f"seed-{uuid.uuid4()}",
            invite_token=f"invite-{uuid.uuid4()}",
            status="completed",
            contract_id=contract.contract_id,
            contract_title=contract.contract_title,
            seller=PartyRecord(
                company_id=seller_one.company_id,
                company_name=seller_one.company_name,
                agent_style="balanced",
                constraints=[
                    ConstraintRecord(
                        constraint_id="seed-s1",
                        description="Cap liability at $50k",
                        clause_category="liability",
                        is_deal_breaker=True,
                        rule_type="max_value",
                        rule_value="$50k",
                        priority=1,
                        was_satisfied=True,
                        satisfaction_turn=2,
                    )
                ],
            ),
            client=PartyRecord(
                company_id=client_one.company_id,
                company_name=client_one.company_name,
                agent_style="cooperative",
                constraints=[],
            ),
            clause_outcomes=[
                ClauseOutcome(
                    clause_id="c1",
                    clause_title="Liability",
                    original_text="Unlimited liability",
                    final_agreed_text="Liability capped at $50,000.",
                    status="agreed",
                    agreement_turn=2,
                    seller_satisfied=True,
                    client_satisfied=True,
                    turns_to_resolve=2,
                )
            ],
            negotiation_turns=[
                TurnRecord(
                    turn_number=1,
                    speaker="seller_agent",
                    action_type="propose",
                    clause_id="c1",
                    content="We propose a mutual liability cap.",
                    proposed_text="Liability capped at $50,000.",
                    reward_delta=0.2,
                    cumulative_reward=0.2,
                    timestamp=now - timedelta(minutes=20),
                ),
                TurnRecord(
                    turn_number=2,
                    speaker="client_agent",
                    action_type="accept",
                    clause_id="c1",
                    content="Accepted.",
                    proposed_text="Liability capped at $50,000.",
                    reward_delta=0.25,
                    cumulative_reward=0.25,
                    timestamp=now - timedelta(minutes=19),
                ),
            ],
            total_turns=2,
            total_agreements=1,
            total_clauses=1,
            agreement_rate=1.0,
            seller_signed=True,
            client_signed=True,
            seller_signed_at=now - timedelta(minutes=18),
            client_signed_at=now - timedelta(minutes=17),
            both_signed_at=now - timedelta(minutes=17),
            created_at=now - timedelta(minutes=30),
            started_at=now - timedelta(minutes=21),
            completed_at=now - timedelta(minutes=19),
            duration_seconds=120,
            final_contract_text="Liability capped at $50,000.",
        ),
        SessionDocument(
            session_id=f"seed-{uuid.uuid4()}",
            invite_token=f"invite-{uuid.uuid4()}",
            status="negotiating",
            contract_id=contract.contract_id,
            contract_title=contract.contract_title,
            seller=PartyRecord(
                company_id=seller_two.company_id,
                company_name=seller_two.company_name,
                agent_style="aggressive",
                constraints=[],
            ),
            client=PartyRecord(
                company_id=client_two.company_id,
                company_name=client_two.company_name,
                agent_style="balanced",
                constraints=[],
            ),
            clause_outcomes=[
                ClauseOutcome(
                    clause_id="c1",
                    clause_title="Payment Terms",
                    original_text="Net 15",
                    status="pending",
                    turns_to_resolve=3,
                )
            ],
            negotiation_turns=[
                TurnRecord(
                    turn_number=1,
                    speaker="seller_agent",
                    action_type="propose",
                    clause_id="c1",
                    content="Move to net 10.",
                    proposed_text="Net 10",
                    reward_delta=0.1,
                    cumulative_reward=0.1,
                    timestamp=now - timedelta(minutes=10),
                )
            ],
            total_turns=1,
            total_clauses=1,
            created_at=now - timedelta(minutes=12),
            started_at=now - timedelta(minutes=11),
        ),
        SessionDocument(
            session_id=f"seed-{uuid.uuid4()}",
            invite_token=f"invite-{uuid.uuid4()}",
            status="completed",
            contract_id=contract.contract_id,
            contract_title=contract.contract_title,
            seller=PartyRecord(
                company_id=seller_three.company_id,
                company_name=seller_three.company_name,
                agent_style="balanced",
                constraints=[],
            ),
            client=PartyRecord(
                company_id=client_three.company_id,
                company_name=client_three.company_name,
                agent_style="cooperative",
                constraints=[],
            ),
            clause_outcomes=[
                ClauseOutcome(
                    clause_id="c2",
                    clause_title="Term",
                    original_text="5 years",
                    final_agreed_text="3 years",
                    status="agreed",
                    agreement_turn=4,
                    seller_satisfied=True,
                    client_satisfied=False,
                    turns_to_resolve=4,
                )
            ],
            total_turns=4,
            total_agreements=1,
            total_clauses=1,
            agreement_rate=1.0,
            seller_signed=True,
            client_signed=False,
            seller_signed_at=now - timedelta(days=1, minutes=10),
            created_at=now - timedelta(days=1, minutes=30),
            started_at=now - timedelta(days=1, minutes=20),
            completed_at=now - timedelta(days=1, minutes=15),
            duration_seconds=300,
            final_contract_text="3 year term.",
        ),
    ]

    for session in session_payloads:
        exists = await SessionDocument.find_one({"session_id": session.session_id})
        if not exists:
            await session.insert()


async def create_indexes() -> None:
    for document in [
        CompanyDocument,
        ContractDocument,
        SessionDocument,
        DemoRunDocument,
        ClauseAnalyticsDocument,
        LeaderboardDocument,
    ]:
        collection = document.get_motor_collection()
        for index in getattr(document.Settings, "indexes", []):
            await collection.create_indexes([index])


async def clear_test_data() -> None:
    await CompanyDocument.find({"company_name": {"$regex": r"^Test_"}}).delete()
