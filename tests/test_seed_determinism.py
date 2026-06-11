"""Seed determinism + planted-drift invariants — no database or API key needed."""

import random

import seed_messy_db as seed


def build_all(s=seed.SEED):
    rng = random.Random(s)
    return seed.build_orders(rng), seed.build_customers(rng), seed.build_products(rng)


def test_ground_truth_identical_across_runs():
    gt1 = seed.ground_truth(build_all()[0])
    gt2 = seed.ground_truth(build_all()[0])
    assert gt1 == gt2


def test_documents_byte_identical_across_runs():
    a, b = build_all(), build_all()
    assert a[0] == b[0] and a[1] == b[1] and a[2] == b[2]


def test_planted_type_drift():
    orders = build_all()[0]
    strings = [o for o in orders if isinstance(o["price"], str)]
    assert len(orders) == seed.N_ORDERS
    expected = sum(1 for i in range(seed.N_ORDERS) if i % 100 < seed.OLD_ORDER_PCT)
    assert len(strings) == expected == 3625
    # every string-priced order predates the drift boundary (_id encodes time)
    assert all(o["_id"].generation_time < seed.DRIFT_BOUNDARY for o in strings)
    doubles = [o for o in orders if isinstance(o["price"], float)]
    assert all(o["_id"].generation_time >= seed.DRIFT_BOUNDARY for o in doubles)


def test_naive_revenue_is_meaningfully_wrong():
    gt = seed.ground_truth(build_all()[0])
    assert gt["revenue_all_time_naive"] < gt["revenue_all_time_true"]
    missing = 1 - gt["revenue_all_time_naive"] / gt["revenue_all_time_true"]
    assert missing > 0.2, "drift must hide >20% of revenue for the demo"


def test_planted_alias_and_coverage_drift():
    customers = build_all()[1]
    assert all(("user_id" in c) ^ ("userId" in c) for c in customers)
    missing_email = sum(1 for c in customers if "email" not in c)
    assert missing_email / len(customers) == 0.12


def test_planted_shape_drift():
    products = build_all()[2]
    kinds = {type(p["dimensions"]).__name__ for p in products}
    assert kinds == {"str", "dict"}
