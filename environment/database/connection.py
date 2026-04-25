from __future__ import annotations

import logging
import os
from typing import Optional

import motor.motor_asyncio
from beanie import init_beanie

from .documents import (
    ClauseAnalyticsDocument,
    CompanyDocument,
    ContractDocument,
    DemoRunDocument,
    LeaderboardDocument,
    SessionDocument,
)


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "contractenv")

client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None


async def connect_db() -> None:
    global client
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
        minPoolSize=2,
    )
    await init_beanie(
        database=client[DATABASE_NAME],
        document_models=[
            CompanyDocument,
            ContractDocument,
            SessionDocument,
            DemoRunDocument,
            ClauseAnalyticsDocument,
            LeaderboardDocument,
        ],
    )
    logging.info("Connected to MongoDB: %s", DATABASE_NAME)


async def disconnect_db() -> None:
    global client
    if client:
        client.close()
        client = None
        logging.info("Disconnected from MongoDB")


async def health_check_db() -> dict:
    if not client:
        return {"status": "disconnected", "error": "client not initialized"}
    try:
        await client.admin.command("ping")
        return {"status": "connected", "database": DATABASE_NAME}
    except Exception as exc:
        return {"status": "disconnected", "error": str(exc)}
