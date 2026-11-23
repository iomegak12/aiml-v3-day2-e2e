"""Unit tests for netcore_tac.api.schemas."""

import pytest
from pydantic import ValidationError

from netcore_tac.api.schemas import TICKET_EXAMPLE, PredictionOut, TicketIn


def ticket(**changes) -> dict:
    return {**TICKET_EXAMPLE, **changes}


def test_valid_example_passes():
    parsed = TicketIn(**TICKET_EXAMPLE)
    assert parsed.severity == "S2" and type(parsed.severity) is str   # plain string values
    assert parsed.created_at.year == 2026


def test_nulls_allowed_for_optional_numbers():
    parsed = TicketIn(**ticket(engineer_experience_years=None, first_response_minutes=None))
    assert parsed.engineer_experience_years is None and parsed.first_response_minutes is None


def test_unseen_product_family_allowed():
    assert TicketIn(**ticket(product_family="Optical Transport")).product_family == "Optical Transport"


@pytest.mark.parametrize("field,value", [
    ("severity", "S5"), ("severity", "Sev-2"), ("customer_tier", "Bronze"),
    ("region", "LATAM"), ("channel", "Fax"),
])
def test_bad_enum_fails(field, value):
    with pytest.raises(ValidationError):
        TicketIn(**ticket(**{field: value}))


@pytest.mark.parametrize("field,value", [
    ("devices_affected", 0), ("devices_affected", 1001), ("software_version_months", -1),
    ("software_version_months", 241), ("prior_tickets_90d", 101),
    ("engineer_experience_years", 51), ("first_response_minutes", -0.1),
    ("first_response_minutes", 10081), ("product_family", ""), ("product_family", "x" * 51),
])
def test_out_of_range_fails(field, value):
    with pytest.raises(ValidationError):
        TicketIn(**ticket(**{field: value}))


def test_extra_field_fails():
    with pytest.raises(ValidationError, match="Extra inputs"):
        TicketIn(**ticket(escalation_count=2))


def test_missing_required_field_fails():
    data = ticket()
    del data["severity"]
    with pytest.raises(ValidationError):
        TicketIn(**data)


def test_prediction_out_adjusted_inputs_default_and_shape():
    out = PredictionOut(predicted_hours=2.3, model_version="0.5.0", request_id="x")
    assert out.adjusted_inputs == []
    out = PredictionOut(predicted_hours=2.3, model_version="0.5.0", request_id="x",
                        adjusted_inputs=[{"field": "engineer_experience_years", "original": 35, "used": 20}])
    assert out.model_dump()["adjusted_inputs"] == [
        {"field": "engineer_experience_years", "original": 35.0, "used": 20.0}]


def test_prediction_out_rejects_negative_hours():
    with pytest.raises(ValidationError):
        PredictionOut(predicted_hours=-1, model_version="0.3.0", request_id="x")
