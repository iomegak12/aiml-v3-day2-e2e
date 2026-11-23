"""Unit tests for netcore_tac.model."""

import json

import numpy as np
import pytest
import pandas as pd
from sklearn.linear_model import LinearRegression, TweedieRegressor

from netcore_tac.features import (
    ALL_FEATURES,
    EXCLUDED_COLUMNS,
    NUMERIC_FEATURES,
    TARGET,
    add_tac_features,
)
from netcore_tac.model import (
    build_linear_pipeline,
    build_pipeline,
    input_ranges,
    get_package_version,
    load_model,
    regression_metrics,
    save_model,
    severity_floors,
)


def test_build_pipeline_steps():
    pipeline = build_pipeline()
    assert list(pipeline.named_steps) == ["prep", "model"]
    glm = pipeline.named_steps["model"]
    assert isinstance(glm, TweedieRegressor)
    assert (glm.power, glm.link) == (2, "log")
    names = [name for name, _, _ in pipeline.named_steps["prep"].transformers]
    assert names == ["num", "flags", "cat"]


def test_linear_reference_pipeline():
    assert isinstance(build_linear_pipeline().named_steps["model"], LinearRegression)


def test_predictions_always_positive_even_for_extreme_inputs(trained):
    extremes = pd.DataFrame([{
        "created_at": pd.Timestamp("2026-11-21 10:30"), "product_family": "Firewalls", "severity": sev,
        "customer_tier": "Platinum", "region": "EMEA", "channel": "Phone", "devices_affected": devices,
        "software_version_months": 0, "prior_tickets_90d": 0, "engineer_experience_years": exp,
        "first_response_minutes": 0.0,
    } for sev in ["S1", "S2", "S3", "S4"] for exp in [0.0, 15.0, 50.0] for devices in [1, 1000]])
    predictions = trained.pipeline.predict(add_tac_features(extremes)[ALL_FEATURES])
    assert (predictions > 0).all()


def test_split_sizes(trained, small_clean_df):
    rows = trained.metadata["rows"]
    assert rows["total"] == len(small_clean_df)
    assert rows["train"] + rows["test"] == rows["total"]
    assert rows["test"] == pytest.approx(0.2 * rows["total"], abs=1)


def test_metadata_fields(trained):
    meta = trained.metadata
    for key in ["model_version", "model_type", "trained_at", "scikit_learn_version", "rows",
                "features", "metrics", "min_hours_by_severity", "input_ranges"]:
        assert key in meta
    assert meta["model_version"] == get_package_version()
    assert "Gamma GLM" in meta["model_type"]
    for name in ["baseline", "linear_regression", "model"]:
        assert set(meta["metrics"][name]) == {"mae", "rmse", "r2"}
    assert set(meta["min_hours_by_severity"]) == {"S1", "S2", "S3", "S4"}
    assert all(hours > 0 for hours in meta["min_hours_by_severity"].values())
    assert set(meta["input_ranges"]) == set(NUMERIC_FEATURES)
    for low, high in meta["input_ranges"].values():
        assert low <= high
    json.dumps(meta)   # must be JSON-serialisable


def test_severity_floors_use_the_quantile_per_severity():
    X = pd.DataFrame({"severity": ["S1"] * 3 + ["S4"] * 3})
    y = pd.Series([1.0, 2.0, 3.0, 10.0, 20.0, 30.0])
    assert severity_floors(X, y, quantile=0.0) == {"S1": 1.0, "S4": 10.0}
    assert severity_floors(X, y, quantile=0.5) == {"S1": 2.0, "S4": 20.0}


def test_input_ranges_ignore_blanks_and_keep_int_types(small_clean_df):
    X = add_tac_features(small_clean_df)[ALL_FEATURES]
    ranges = input_ranges(X)
    assert ranges["devices_affected"] == [int(X["devices_affected"].min()), int(X["devices_affected"].max())]
    assert isinstance(ranges["devices_affected"][0], int)
    low, high = ranges["engineer_experience_years"]
    assert low == X["engineer_experience_years"].min() and high == X["engineer_experience_years"].max()


def test_no_leakage_column_in_inputs(trained):
    inputs = set(trained.pipeline.feature_names_in_)
    assert inputs == set(ALL_FEATURES)
    assert not inputs & set(EXCLUDED_COLUMNS + [TARGET, "created_at"])


def test_save_load_round_trip(trained, small_clean_df, tmp_path):
    model_path, meta_path = tmp_path / "m" / "eta.joblib", tmp_path / "m" / "eta.json"
    save_model(trained, model_path, meta_path)
    loaded = load_model(model_path, meta_path)

    X = add_tac_features(small_clean_df)[ALL_FEATURES]
    np.testing.assert_array_equal(loaded.pipeline.predict(X), trained.pipeline.predict(X))
    assert loaded.metadata == trained.metadata


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_model(tmp_path / "missing.joblib", tmp_path / "missing.json")


def test_regression_metrics_perfect_fit():
    y = np.array([1.0, 2.0, 3.0])
    assert regression_metrics(y, y) == {"mae": 0.0, "rmse": 0.0, "r2": 1.0}
