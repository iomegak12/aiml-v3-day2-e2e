"""Unit tests for netcore_tac.api.predictor."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from netcore_tac.api.predictor import (
    Prediction,
    Predictor,
    clamp_inputs,
    clip_and_round,
    ticket_to_frame,
)
from netcore_tac.api.schemas import TICKET_EXAMPLE, TicketIn
from netcore_tac.features import ALL_FEATURES, add_tac_features

RANGES = {"devices_affected": [1, 54], "software_version_months": [0, 60], "prior_tickets_90d": [0, 9],
          "engineer_experience_years": [0.5, 20.0], "first_response_minutes": [2.2, 800.4]}
FLOORS = {"S1": 0.9, "S2": 6.9, "S3": 8.3, "S4": 11.6}


class ConstantPipeline:
    """Stub model: always predicts ``value``; records the features it was given."""

    def __init__(self, value: float) -> None:
        self.value = value
        self.seen: pd.DataFrame | None = None

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        self.seen = X.copy()
        return np.array([self.value])


@pytest.fixture(scope="module")
def predictor(trained) -> Predictor:
    return Predictor.from_training_result(trained)


def make(**changes) -> TicketIn:
    return TicketIn(**{**TICKET_EXAMPLE, **changes})


def stub(value: float, **metadata) -> Predictor:
    return Predictor(ConstantPipeline(value), {"min_hours_by_severity": FLOORS, "input_ranges": RANGES, **metadata})


# ---------- real (small) model ----------
def test_predicts_rounded_positive(predictor):
    result = predictor.predict(make())
    assert isinstance(result, Prediction)
    assert result.hours > 0
    assert result.hours == round(result.hours, 1)


def test_unseen_product_and_null_experience_still_predict(predictor):
    result = predictor.predict(make(product_family="Quantum Widgets",
                                    engineer_experience_years=None, first_response_minutes=None))
    assert np.isfinite(result.hours) and result.hours > 0


def test_s1_with_long_experience_is_never_zero(predictor):
    """The UI case that showed 0 h with linear regression."""
    result = predictor.predict(make(severity="S1", product_family="Firewalls", engineer_experience_years=15))
    assert result.hours >= predictor.min_hours_by_severity["S1"] > 0


def test_matches_pipeline_when_inputs_in_range(trained):
    p = Predictor(trained.pipeline, {**trained.metadata, "input_ranges": RANGES})
    raw = p.pipeline.predict(add_tac_features(ticket_to_frame(make()))[ALL_FEATURES])[0]
    floor = p.min_hours_by_severity.get("S2", 0.0)
    result = p.predict(make())
    assert result.hours == clip_and_round(raw, floor)
    assert result.adjusted_inputs == []


# ---------- floor ----------
@pytest.mark.parametrize("severity,expected", [("S1", 0.9), ("S2", 6.9), ("S3", 8.3), ("S4", 11.6)])
def test_floor_applied_per_severity(severity, expected):
    assert stub(0.2).predict(make(severity=severity)).hours == expected


def test_prediction_above_floor_unchanged():
    assert stub(31.46).predict(make(severity="S2")).hours == 31.5


def test_old_metadata_without_floors_or_ranges_still_predicts():
    result = Predictor(ConstantPipeline(-2.0), {}).predict(make(devices_affected=999))
    assert result == Prediction(hours=0.0, adjusted_inputs=[])


@pytest.mark.parametrize("raw,minimum,expected", [(-3.7, 0.0, 0.0), (0.04, 0.0, 0.0), (12.345, 0.0, 12.3),
                                                  (7.96, 0.0, 8.0), (0.3, 0.9, 0.9), (-5, 6.9, 6.9)])
def test_clip_and_round(raw, minimum, expected):
    assert clip_and_round(raw, minimum) == expected


# ---------- clamping ----------
def test_clamp_reports_field_original_used():
    df, adjustments = clamp_inputs(ticket_to_frame(make(engineer_experience_years=35, devices_affected=200,
                                                        first_response_minutes=0)), RANGES)
    assert adjustments == [
        {"field": "devices_affected", "original": 200, "used": 54},
        {"field": "engineer_experience_years", "original": 35, "used": 20},
        {"field": "first_response_minutes", "original": 0, "used": 2.2},
    ]
    assert df.loc[0, "engineer_experience_years"] == 20.0
    assert df.loc[0, "devices_affected"] == 54.0


def test_in_range_and_null_values_not_clamped():
    original = ticket_to_frame(make(engineer_experience_years=None))
    df, adjustments = clamp_inputs(original, RANGES)
    assert adjustments == []
    assert np.isnan(df.loc[0, "engineer_experience_years"])
    pd.testing.assert_frame_equal(df, original)


def test_clamped_values_reach_the_model():
    p = stub(30.0)
    result = p.predict(make(engineer_experience_years=35))
    assert p.pipeline.seen.loc[0, "engineer_experience_years"] == 20.0
    assert result.adjusted_inputs == [{"field": "engineer_experience_years", "original": 35, "used": 20}]


# ---------- frame + metadata ----------
def test_ticket_to_frame_layout():
    df = ticket_to_frame(make(engineer_experience_years=None,
                              created_at=datetime(2026, 11, 21, 10, tzinfo=timezone(timedelta(hours=5)))))
    assert len(df) == 1
    assert np.isnan(df.loc[0, "engineer_experience_years"])
    assert df.loc[0, "created_at"].tzinfo is None and df.loc[0, "created_at"].hour == 10


def test_metadata_properties(predictor, trained):
    assert predictor.model_version == trained.metadata["model_version"]
    assert predictor.trained_at == trained.metadata["trained_at"]
    assert predictor.min_hours_by_severity == trained.metadata["min_hours_by_severity"]
    assert predictor.input_ranges == trained.metadata["input_ranges"]
    empty = Predictor(predictor.pipeline, {})
    assert empty.model_version == "unknown"
    assert empty.min_hours_by_severity == {} and empty.input_ranges == {}
