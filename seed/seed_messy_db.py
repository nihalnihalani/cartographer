"""Seed `carto_demo` with an e-commerce dataset containing planted, dated schema drift.

Every value is deterministic (seeded RNG, ObjectIds built from fixed timestamps),
so the printed ground-truth numbers are identical on every run.

Planted drift (see docs/ARCHITECTURE.md §6):
  orders    — price stored as *string* before 2024-03-01, double after (TYPE_DRIFT)
              status case drift: "SHIPPED" (old) vs "shipped" (new) (ENUM_DRIFT)
  customers — user_id (old) vs userId (new) alias pair (ALIAS_FIELDS)
              email missing in 12% of docs (PARTIAL_COVERAGE)
              phone explicitly null in some old docs (NULL_POLLUTION)
  products  — dimensions "LxWxH" string (old) vs object (new) (SHAPE_DRIFT)

Usage:
  MDB_MCP_CONNECTION_STRING=mongodb://localhost:27017 python seed/seed_messy_db.py
"""

from __future__ import annotations

import json
import logging
import os
import random
import struct
import sys
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("seed")

DB_NAME = "carto_demo"
SEED = 20260611

N_ORDERS = 12_483
N_CUSTOMERS = 5_000
N_PRODUCTS = 1_000

DRIFT_BOUNDARY = datetime(2024, 3, 1, tzinfo=timezone.utc)
OLD_START = datetime(2023, 1, 1, tzinfo=timezone.utc)
OLD_END = datetime(2024, 2, 28, 23, 59, 59, tzinfo=timezone.utc)
NEW_START = DRIFT_BOUNDARY
NEW_END = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

# 29 of every 100 orders are "old era" => exactly 29% string-typed prices.
OLD_ORDER_PCT = 29
EMAIL_MISSING_PCT = 12  # of customers
OLD_CUSTOMER_PCT = 40   # have user_id instead of userId
OLD_PRODUCT_PCT = 35    # have string dimensions


def det_object_id(ts: datetime, n: int) -> ObjectId:
    """ObjectId whose 4-byte timestamp is `ts` and remaining 8 bytes encode `n`.

    Keeps _id-based time bucketing (Historian's evidence) truthful while staying
    fully deterministic across runs.
    """
    return ObjectId(struct.pack(">I", int(ts.timestamp())) + n.to_bytes(8, "big"))


def spread(rng: random.Random, start: datetime, end: datetime) -> datetime:
    t = rng.uniform(start.timestamp(), end.timestamp())
    return datetime.fromtimestamp(int(t), tz=timezone.utc)


def build_orders(rng: random.Random) -> list[dict]:
    orders = []
    for i in range(N_ORDERS):
        is_old = (i % 100) < OLD_ORDER_PCT
        created = (
            spread(rng, OLD_START, OLD_END) if is_old else spread(rng, NEW_START, NEW_END)
        )
        price = round(rng.uniform(8.0, 240.0), 2)
        status_pool = ["SHIPPED", "PENDING", "CANCELLED"] if is_old else ["shipped", "pending", "cancelled", "Shipped"]
        doc = {
            "_id": det_object_id(created, i),
            "order_date": created,
            "customer_id": rng.randrange(N_CUSTOMERS),
            "price": f"{price:.2f}" if is_old else price,
            "status": rng.choice(status_pool),
            "items": rng.randint(1, 5),
        }
        orders.append(doc)
    return orders


def build_customers(rng: random.Random) -> list[dict]:
    customers = []
    for i in range(N_CUSTOMERS):
        is_old = (i % 100) < OLD_CUSTOMER_PCT
        created = (
            spread(rng, OLD_START, OLD_END) if is_old else spread(rng, NEW_START, NEW_END)
        )
        doc = {
            "_id": det_object_id(created, 10_000_000 + i),
            "name": f"Customer {i:05d}",
            "signup_date": created,
        }
        # ALIAS_FIELDS: same logical key under two names, value space overlaps 100%
        if is_old:
            doc["user_id"] = i
        else:
            doc["userId"] = i
        # PARTIAL_COVERAGE on email
        if (i % 100) >= EMAIL_MISSING_PCT:
            doc["email"] = f"customer{i:05d}@example.com"
        # NULL_POLLUTION: old docs carry explicit null phone, new docs omit it
        if is_old and i % 3 == 0:
            doc["phone"] = None
        customers.append(doc)
    return customers


def build_products(rng: random.Random) -> list[dict]:
    products = []
    for i in range(N_PRODUCTS):
        is_old = (i % 100) < OLD_PRODUCT_PCT
        created = (
            spread(rng, OLD_START, OLD_END) if is_old else spread(rng, NEW_START, NEW_END)
        )
        l, w, h = rng.randint(2, 40), rng.randint(2, 40), rng.randint(1, 20)
        doc = {
            "_id": det_object_id(created, 20_000_000 + i),
            "sku": f"SKU-{i:04d}",
            "name": f"Product {i:04d}",
            "dimensions": f"{l}x{w}x{h}" if is_old else {"l": l, "w": w, "h": h},
            "list_price": round(rng.uniform(5.0, 500.0), 2),
        }
        products.append(doc)
    return products


def ground_truth(orders: list[dict]) -> dict:
    def fval(o):
        return float(o["price"])

    def is_double(o):
        return isinstance(o["price"], float)

    def in_2024(o):
        return o["order_date"].year == 2024

    all_true = sum(fval(o) for o in orders)
    all_naive = sum(fval(o) for o in orders if is_double(o))
    y_true = sum(fval(o) for o in orders if in_2024(o))
    y_naive = sum(fval(o) for o in orders if in_2024(o) and is_double(o))
    return {
        "orders": len(orders),
        "string_priced_orders": sum(1 for o in orders if not is_double(o)),
        "revenue_all_time_true": round(all_true, 2),
        "revenue_all_time_naive": round(all_naive, 2),
        "revenue_2024_true": round(y_true, 2),
        "revenue_2024_naive": round(y_naive, 2),
        "string_priced_2024": sum(1 for o in orders if in_2024(o) and not is_double(o)),
    }


def main() -> int:
    uri = os.environ.get("MDB_MCP_CONNECTION_STRING", "mongodb://localhost:27017")
    rng = random.Random(SEED)
    orders = build_orders(rng)
    customers = build_customers(rng)
    products = build_products(rng)
    gt = ground_truth(orders)

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[DB_NAME]
        client.drop_database(DB_NAME)
        db.orders.insert_many(orders)
        db.customers.insert_many(customers)
        db.products.insert_many(products)
        log.info(
            "seeded db=%s orders=%d customers=%d products=%d",
            DB_NAME, N_ORDERS, N_CUSTOMERS, N_PRODUCTS,
        )
    except PyMongoError as exc:
        log.error("MongoDB unavailable at %s: %s", uri, exc)
        return 1

    print("=" * 64)
    print("GROUND TRUTH (deterministic — identical on every run)")
    print("=" * 64)
    print(json.dumps(gt, indent=2))
    print("-" * 64)
    print(f"Demo question: 'What was total revenue in 2024?'")
    print(f"  naive agent (ignores string prices): ${gt['revenue_2024_naive']:,.2f}")
    print(f"  correct (defensive pipeline):        ${gt['revenue_2024_true']:,.2f}")
    print(f"  string-typed prices in 2024:         {gt['string_priced_2024']}")
    print(f"All-time:  naive ${gt['revenue_all_time_naive']:,.2f}  vs  true ${gt['revenue_all_time_true']:,.2f}")
    print(f"  string-typed prices overall:         {gt['string_priced_orders']} "
          f"({100 * gt['string_priced_orders'] / gt['orders']:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
