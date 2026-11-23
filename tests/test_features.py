"""Unit tests for netcore_tac.features."""

import pandas as pd

from netcore_tac.features import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    EXCLUDED_COLUMNS,
    FLAG_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    add_tac_features,
)


def frame() -> pd.DataFrame:
    return pd.DataFrame({
        # Fri, Sat, Sun, Mon (2026-11-20 .. 2026-11-23)
        "created_at": pd.to_datetime(["2026-11-20 23:59", "2026-11-21 10:00",
                                      "2026-11-22 08:00", "2026-11-23 00:00"]),
        "software_version_months": [36, 37, 0, 120],
    })


def test_weekend_flag_on_known_dates():
    assert add_tac_features(frame())["is_weekend"].tolist() == [0, 1, 1, 0]


def test_old_software_flag_boundary():
    assert add_tac_features(frame())["old_software"].tolist() == [0, 1, 0, 1]


def test_flags_are_ints_and_created_at_dropped():
    out = add_tac_features(frame())
    assert "created_at" not in out.columns
    assert out["is_weekend"].dtype.kind == "i" and out["old_software"].dtype.kind == "i"


def test_input_not_modified():
    df = frame()
    add_tac_features(df)
    assert list(df.columns) == ["created_at", "software_version_months"]


def test_feature_lists_have_no_leakage():
    assert ALL_FEATURES == NUMERIC_FEATURES + FLAG_FEATURES + CATEGORICAL_FEATURES
    assert not set(ALL_FEATURES) & set(EXCLUDED_COLUMNS)
    assert TARGET not in ALL_FEATURES
