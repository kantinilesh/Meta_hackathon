from __future__ import annotations

from datetime import datetime

import mongomock_motor
import pytest
import pytest_asyncio
from beanie import init_beanie

from environment.database import (
    AnalyticsRepository,
    ClauseAnalyticsDocument,
    CompanyDocument,
    CompanyRepository,
    ContractDocument,
    ContractRepository,
    DemoRepository,
    DemoRunDocument,
    LeaderboardDocument,
    LeaderboardRepository,
    SessionDocument,
    SessionRepository,
)
from environment.database.connection import health_check_db
from environment.database.documents import PartyRecord


@pytest_asyncio.fixture(autouse=True)
async def beanie_test_db(monkeypatch):
    client = mongomock_motor.AsyncMongoMockClient()
    database = client["contractenv_test"]

    await init_beanie(
        database=database,
        document_models=[
            CompanyDocument,
            ContractDocument,
            SessionDocument,
            DemoRunDocument,
            ClauseAnalyticsDocument,
            LeaderboardDocument,
        ],
    )

    monkeypatch.setattr("environment.database.connection.client", client)
    monkeypatch.setattr("environment.database.connection.DATABASE_NAME", "contractenv_test")

    for model in [
        CompanyDocument,
        ContractDocument,
        SessionDocument,
        DemoRunDocument,
        ClauseAnalyticsDocument,
        LeaderboardDocument,
    ]:
        await model.get_motor_collection().delete_many({})

    yield

    client.close()


@pytest.mark.asyncio
async def test_company_upsert_creates_new():
    company = await CompanyRepository.upsert("Test_Acme", "seller")
    assert company.company_name == "Test_Acme"
    assert company.total_sessions == 1
    assert company.sessions_as_seller == 1


@pytest.mark.asyncio
async def test_company_upsert_returns_existing():
    first = await CompanyRepository.upsert("Test_Beta", "seller")
    second = await CompanyRepository.upsert("Test_Beta", "client")
    assert first.company_id == second.company_id
    assert second.total_sessions == 2
    assert second.sessions_as_client == 1


@pytest.mark.asyncio
async def test_contract_save_and_retrieve():
    owner = await CompanyRepository.upsert("Test_Contracts", "seller")
    saved = await ContractRepository.save(
        {
            "contract_id": "contract-123",
            "contract_title": "Test NDA",
            "contract_text": "Clause text",
            "uploaded_by": owner.company_id,
            "contract_type": "NDA",
            "clauses": [
                {
                    "clause_id": "c1",
                    "title": "Confidentiality",
                    "original_text": "Keep secrets.",
                    "category": "ip",
                    "is_deal_breaker": False,
                    "ground_truth_label": "fair",
                    "risk_level": "low",
                }
            ],
        }
    )
    fetched = await ContractRepository.find_by_id("contract-123")
    assert saved.contract_id == fetched.contract_id
    assert fetched.total_clauses == 1


@pytest.mark.asyncio
async def test_session_lifecycle():
    seller = await CompanyRepository.upsert("Test_Seller", "seller")
    client = await CompanyRepository.upsert("Test_Client", "client")
    contract = await ContractRepository.save(
        {
            "contract_id": "contract-session",
            "contract_title": "Lifecycle Contract",
            "contract_text": "One clause",
            "uploaded_by": seller.company_id,
            "contract_type": "NDA",
            "clauses": [
                {
                    "clause_id": "c1",
                    "title": "Payment",
                    "original_text": "Net 30",
                    "category": "payment",
                    "is_deal_breaker": False,
                    "ground_truth_label": "neutral",
                    "risk_level": "medium",
                }
            ],
        }
    )

    session = await SessionRepository.create(
        {
            "session_id": "session-lifecycle",
            "invite_token": "invite-lifecycle",
            "status": "waiting_client",
            "contract_id": contract.contract_id,
            "contract_title": contract.contract_title,
            "seller": {
                "company_id": seller.company_id,
                "company_name": seller.company_name,
                "agent_style": "balanced",
                "constraints": [],
            },
            "clause_outcomes": [
                {
                    "clause_id": "c1",
                    "clause_title": "Payment",
                    "original_text": "Net 30",
                    "status": "pending",
                    "turns_to_resolve": 0,
                }
            ],
        }
    )
    assert session.session_id == "session-lifecycle"

    session.client = PartyRecord(
        company_id=client.company_id,
        company_name=client.company_name,
        agent_style="cooperative",
        constraints=[],
    )
    await session.save()

    started = await SessionRepository.update_status("session-lifecycle", "negotiating")
    assert started.status == "negotiating"

    await SessionRepository.save_turn(
        "session-lifecycle",
        {
            "turn_number": 1,
            "speaker": "seller_agent",
            "action_type": "propose",
            "clause_id": "c1",
            "content": "Net 15",
            "proposed_text": "Net 15",
            "reward_delta": 0.15,
            "cumulative_reward": 0.15,
            "timestamp": datetime.utcnow(),
        },
    )
    await SessionRepository.save_clause_outcome(
        "session-lifecycle",
        "c1",
        {
            "clause_id": "c1",
            "clause_title": "Payment",
            "original_text": "Net 30",
            "final_agreed_text": "Net 15",
            "status": "agreed",
            "agreement_turn": 1,
            "seller_satisfied": True,
            "client_satisfied": True,
            "turns_to_resolve": 1,
        },
    )
    await SessionRepository.complete(
        "session-lifecycle",
        {
            "final_contract_text": "Net 15",
            "seller_total_reward": 0.15,
            "client_total_reward": 0.1,
        },
    )
    signed = await SessionRepository.mark_signed("session-lifecycle", "seller")
    signed = await SessionRepository.mark_signed("session-lifecycle", "client")

    assert signed.seller_signed is True
    assert signed.client_signed is True
    assert signed.both_signed_at is not None


@pytest.mark.asyncio
async def test_demo_run_save_and_leaderboard():
    run = await DemoRepository.save_run(
        {
            "session_id": "demo-session",
            "model_name": "gpt-4o-mini",
            "api_base_url": "https://api.example.com",
        }
    )
    for task_id, score in [("task1", 0.9), ("task2", 0.8), ("task3", 0.7)]:
        await DemoRepository.save_task_result(
            run.run_id,
            {
                "task_id": task_id,
                "task_name": task_id,
                "difficulty": "easy",
                "target_score": 0.5,
                "achieved_score": score,
                "passed": True,
                "steps_taken": 3,
                "max_turns": 10,
                "duration_seconds": 1.0,
                "reward_timeline": [score],
                "actions_taken": [],
                "grade_breakdown": {},
                "clause_results": [],
            },
        )
    completed = await DemoRepository.complete_run(
        run.run_id,
        {
            "completed_at": datetime.utcnow(),
            "passed_all_tasks": True,
            "openenv_validate_passed": True,
        },
    )
    entry = await LeaderboardRepository.add_entry(completed)
    assert entry.rank == 1
    assert entry.overall_score > 0


@pytest.mark.asyncio
async def test_clause_analytics_update():
    seller = await CompanyRepository.upsert("Test_Analytics_Seller", "seller")
    contract = await ContractRepository.save(
        {
            "contract_id": "contract-analytics",
            "contract_title": "Analytics Contract",
            "contract_text": "Clause text",
            "uploaded_by": seller.company_id,
            "contract_type": "NDA",
            "clauses": [],
        }
    )
    session = await SessionRepository.create(
        {
            "session_id": "session-analytics",
            "invite_token": "invite-analytics",
            "status": "completed",
            "contract_id": contract.contract_id,
            "contract_title": contract.contract_title,
            "seller": {
                "company_id": seller.company_id,
                "company_name": seller.company_name,
                "agent_style": "balanced",
                "constraints": [],
            },
            "clause_outcomes": [
                {
                    "clause_id": "c1",
                    "clause_title": "Liability",
                    "original_text": "Unlimited",
                    "final_agreed_text": "Limited to fees paid",
                    "status": "agreed",
                    "agreement_turn": 2,
                    "seller_satisfied": True,
                    "client_satisfied": True,
                    "turns_to_resolve": 2,
                }
            ],
        }
    )
    await SessionRepository.save_turn(
        session.session_id,
        {
            "turn_number": 1,
            "speaker": "seller_agent",
            "action_type": "propose",
            "clause_id": "c1",
            "content": "Limit liability",
            "proposed_text": "Limited to fees paid",
            "reward_delta": 0.2,
            "cumulative_reward": 0.2,
            "timestamp": datetime.utcnow(),
        },
    )
    refreshed = await SessionRepository.find_by_id(session.session_id)
    await AnalyticsRepository.update_clause_stats(refreshed)
    analytics = await AnalyticsRepository.get_clause_stats("c1")
    assert analytics is not None
    assert analytics.total_appearances == 1


@pytest.mark.asyncio
async def test_db_health_check():
    health = await health_check_db()
    assert health["status"] == "connected"
