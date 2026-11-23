"""Unit tests for netcore_tac.model."""

import json

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from netcore_tac.features import ALL_FEATURES, EXCLUDED_COLUMNS, TARGET, add_tac_features
from netcore_tac.model import (
    build_pipeline,
    get_package_version,
    load_model,
    regression_metrics,
    save_model,
)


def test_build_pipeline_steps():
    pipeline = build_pipeline()
    assert list(pipeline.named_steps) == ["prep", "model"]
    assert isinstance(pipeline.named_steps["model"], LinearRegression)
    names = [name for name, _, _ in pipeline.named_steps["prep"].transformers]
    assert names == ["num", "flags", "cat"]


def test_split_sizes(trained, small_clean_df):
    rows = trained.metadata["rows"]
    assert rows["total"] == len(small_clean_df)
    assert rows["train"] + rows["test"] == rows["total"]
    assert rows["test"] == pytest.approx(0.2 * rows["total"], abs=1)


def test_metadata_fields(trained):
    meta = trained.metadata
    for key in ["model_version", "trained_at", "scikit_learn_version", "rows", "features",
                "metrics"]:
        assert key in meta
    assert meta["model_version"] == get_package_version()
    for name in ["baseline", "model"]:
        assert set(meta["metrics"][name]) == {"mae", "rmse", "r2"}
    json.dumps(meta)   # must be JSON-serialisable


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
