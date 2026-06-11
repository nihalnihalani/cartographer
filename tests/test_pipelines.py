"""Defensive-pipeline correctness against the actually-seeded database.

Skips cleanly when MongoDB is unreachable; runs keyless (pure pymongo, no LLM).
"""

import os
import random

import pytest
from pymongo import MongoClient
from pymongo.errors import PyMongoError

import seed_messy_db as seed
from cartographer.pipelines import (
    ALIAS_COALESCE_CUSTOMER_KEY,
    DEFENSIVE_REVENUE,
    NAIVE_REVENUE,
)

URI = os.environ.get("MDB_MCP_CONNECTION_STRING", "mongodb://localhost:27017")


@pytest.fixture(scope="module")
def db():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
    except PyMongoError:
        pytest.skip(f"MongoDB unreachable at {URI}")
    database = client[seed.DB_NAME]
    if database.orders.estimated_document_count() == 0:
        pytest.skip("carto_demo not seeded — run seed/seed_messy_db.py")
    return database


@pytest.fixture(scope="module")
def gt():
    return seed.ground_truth(seed.build_orders(random.Random(seed.SEED)))


def test_naive_pipeline_reproduces_the_wrong_number(db, gt):
    total = next(iter(db.orders.aggregate(NAIVE_REVENUE)))["total"]
    assert round(total, 2) == gt["revenue_all_time_naive"]


def test_defensive_pipeline_recovers_ground_truth(db, gt):
    row = next(iter(db.orders.aggregate(DEFENSIVE_REVENUE)))
    assert round(row["total"], 2) == gt["revenue_all_time_true"]
    assert row["converted_strings"] == gt["string_priced_orders"]


def test_damage_is_the_planted_29_percent(db, gt):
    naive = next(iter(db.orders.aggregate(NAIVE_REVENUE)))["total"]
    true = next(iter(db.orders.aggregate(DEFENSIVE_REVENUE)))["total"]
    assert (true - naive) / true == pytest.approx(0.289, abs=0.02)


def test_alias_coalesce_covers_every_customer(db):
    rows = list(
        db.customers.aggregate(
            [
                {"$project": {"key": ALIAS_COALESCE_CUSTOMER_KEY}},
                {"$match": {"key": None}},
                {"$count": "missing"},
            ]
        )
    )
    assert rows == [], "every customer must have user_id or userId"
