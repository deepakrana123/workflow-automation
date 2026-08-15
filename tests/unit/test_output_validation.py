"""Unit tests for the (non-fatal) output-schema validation core."""

from app.execution.runtime.output_validation import validate_outputs


def test_no_schema_is_always_valid():
    assert validate_outputs({"anything": 1}, None)["validated"] is True
    assert validate_outputs({}, {})["validated"] is True


def test_json_schema_required_keys_present():
    schema = {"properties": {"score": {}, "risk": {}}, "required": ["score"]}
    result = validate_outputs({"score": 720, "risk": "LOW"}, schema)
    assert result["validated"] is True
    assert result["checked"] == ["score"]


def test_json_schema_missing_required_key():
    schema = {"properties": {"score": {}, "risk": {}}, "required": ["score", "risk"]}
    result = validate_outputs({"score": 720}, schema)
    assert result["validated"] is False
    assert result["missing"] == ["risk"]


def test_json_schema_without_required_checks_all_properties():
    schema = {"properties": {"score": {}, "risk": {}}}
    result = validate_outputs({"score": 720}, schema)
    assert result["validated"] is False
    assert result["missing"] == ["risk"]


def test_simple_map_schema_checks_all_keys():
    schema = {"score": "number", "risk": "string"}
    assert validate_outputs({"score": 1, "risk": "LOW"}, schema)["validated"] is True
    assert validate_outputs({"score": 1}, schema)["missing"] == ["risk"]


def test_empty_outputs_against_schema_flags_all():
    schema = {"properties": {"a": {}, "b": {}}, "required": ["a", "b"]}
    result = validate_outputs({}, schema)
    assert set(result["missing"]) == {"a", "b"}
