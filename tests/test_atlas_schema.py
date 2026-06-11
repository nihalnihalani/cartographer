"""Schema Atlas document contract."""

from cartographer.atlas_schema import validate_atlas_doc

GOOD = {
    "atlas_version": 1,
    "collection": "orders",
    "surveyed_at": "2026-06-11T18:30:00Z",
    "doc_count": 12483,
    "sample_size": 600,
    "fields": {
        "price": {
            "coverage": 1.0,
            "types": {"double": 0.71, "string": 0.29},
            "drift": {"from": "string", "to": "double", "boundary": "2024-03"},
            "hazards": [
                {
                    "id": "H-ORD-001",
                    "kind": "TYPE_DRIFT",
                    "severity": "HIGH",
                    "blast": "SUM/AVG over price silently ignores 29% of documents",
                    "defense": "$convert with onError:null + $ifNull guard",
                }
            ],
        }
    },
    "aliases": [],
    "summary": "Orders collection; price exhibits HIGH type drift from 2024-03.",
}


def test_architecture_example_validates():
    assert validate_atlas_doc(GOOD) == []


def test_missing_keys_rejected():
    assert any("missing top-level" in e for e in validate_atlas_doc({"fields": {}}))


def test_bad_hazard_kind_rejected():
    doc = {**GOOD, "fields": {"x": {"coverage": 1.0, "types": {"string": 1.0},
           "hazards": [{"kind": "BOGUS", "severity": "HIGH", "blast": "b", "defense": "d"}]}}}
    errs = validate_atlas_doc(doc)
    assert any("bad hazard kind" in e for e in errs)


def test_coverage_range_enforced():
    doc = {**GOOD, "fields": {"x": {"coverage": 1.5, "types": {"string": 1.0}}}}
    assert any("coverage" in e for e in validate_atlas_doc(doc))
