"""Canonical revenue pipelines — the naive trap and the Navigator's defense.

These are the reference implementations the test suite runs against the seeded
database to prove the defensive pattern recovers the planted ground truth.
"""

# What every "chat with your database" agent writes: $sum silently skips
# non-numeric values, so 29% of revenue (string-typed prices) vanishes.
NAIVE_REVENUE = [
    {"$group": {"_id": None, "total": {"$sum": "$price"}}},
]

# TYPE_DRIFT defense: $convert with onError/onNull guards, $ifNull fallback.
DEFENSIVE_REVENUE = [
    {
        "$group": {
            "_id": None,
            "total": {
                "$sum": {
                    "$ifNull": [
                        {
                            "$convert": {
                                "input": "$price",
                                "to": "double",
                                "onError": None,
                                "onNull": None,
                            }
                        },
                        0,
                    ]
                }
            },
            "converted_strings": {
                "$sum": {"$cond": [{"$eq": [{"$type": "$price"}, "string"]}, 1, 0]}
            },
        }
    },
]

# ALIAS_FIELDS defense for customers.user_id / customers.userId.
ALIAS_COALESCE_CUSTOMER_KEY = {"$ifNull": ["$user_id", "$userId"]}
