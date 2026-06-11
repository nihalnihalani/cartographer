"""Schema Atlas document contract (docs/ARCHITECTURE.md §4) + validator."""

from __future__ import annotations

HAZARD_KINDS = {
    "TYPE_DRIFT",
    "ALIAS_FIELDS",
    "PARTIAL_COVERAGE",
    "SHAPE_DRIFT",
    "ENUM_DRIFT",
    "NULL_POLLUTION",
}
SEVERITIES = {"HIGH", "MEDIUM", "LOW"}

REQUIRED_TOP = {"atlas_version", "collection", "surveyed_at", "doc_count", "fields", "summary"}


def validate_atlas_doc(doc: dict) -> list[str]:
    """Return a list of violations (empty == valid)."""
    errors: list[str] = []
    missing = REQUIRED_TOP - doc.keys()
    if missing:
        errors.append(f"missing top-level keys: {sorted(missing)}")
    if not isinstance(doc.get("atlas_version"), int) or doc.get("atlas_version", 0) < 1:
        errors.append("atlas_version must be an int >= 1")
    if not isinstance(doc.get("fields"), dict):
        errors.append("fields must be a dict")
        return errors
    for fname, f in doc["fields"].items():
        if not isinstance(f, dict):
            errors.append(f"field {fname!r} must be a dict")
            continue
        cov = f.get("coverage")
        if not isinstance(cov, (int, float)) or not 0 <= cov <= 1:
            errors.append(f"field {fname!r}: coverage must be in [0,1]")
        types = f.get("types")
        if not isinstance(types, dict) or not types:
            errors.append(f"field {fname!r}: types must be a non-empty dict")
        for hz in f.get("hazards", []):
            if hz.get("kind") not in HAZARD_KINDS:
                errors.append(f"field {fname!r}: bad hazard kind {hz.get('kind')!r}")
            if hz.get("severity") not in SEVERITIES:
                errors.append(f"field {fname!r}: bad severity {hz.get('severity')!r}")
            if not hz.get("blast") or not hz.get("defense"):
                errors.append(f"field {fname!r}: hazard needs blast + defense")
    return errors
