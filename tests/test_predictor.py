"""Unit tests for netcore_tac.api.predictor."""

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from netcore_tac.api.predictor import Predictor, clip_and_round, ticket_to_frame
from netcore_tac.api.schemas import TICKET_EXAMPLE, TicketIn


@pytest.fixture(scope="module")
def predictor(trained) -> Predictor:
    return Predictor.from_training_result(trained)


def make(**changes) -> TicketIn:
    return TicketIn(**{**TICKET_EXAMPLE, **changes})


def test_predicts_rounded_non_negative(predictor):
    hours = predictor.predict(make())
    assert hours >= 0
    assert hours == round(hours, 1)


def test_unseen_product_and_null_experience_still_predict(predictor):
    hours = predictor.predict(make(product_family="Quantum Widgets",
                                   engineer_experience_years=None, first_response_minutes=None))
    assert np.isfinite(hours) and hours >= 0


def test_matches_pipeline_on_same_row(predictor):
    from netcore_tac.features import ALL_FEATURES, add_tac_features
    raw = predictor.pipeline.predict(add_tac_features(ticket_to_frame(make()))[ALL_FEATURES])[0]
    assert predictor.predict(make()) == clip_and_round(raw)


def test_ticket_to_frame_layout():
    df = ticket_to_frame(make(engineer_experience_years=None,
                              created_at=datetime(2026, 11, 21, 10, tzinfo=timezone(timedelta(hours=5)))))
    assert len(df) == 1
    assert np.isnan(df.loc[0, "engineer_experience_years"])
    assert df.loc[0, "created_at"].tzinfo is None and df.loc[0, "created_at"].hour == 10


@pytest.mark.parametrize("raw,expected", [(-3.7, 0.0), (0.04, 0.0), (12.345, 12.3), (7.96, 8.0)])
def test_clip_and_round(raw, expected):
    assert clip_and_round(raw) == expected


def test_metadata_properties(predictor, trained):
    assert predictor.model_version == trained.metadata["model_version"]
    assert predictor.trained_at == trained.metadata["trained_at"]
    assert Predictor(predictor.pipeline, {}).model_version == "unknown"
