"""Unit tests for netcore_tac.cleaning."""

import numpy as np
import pandas as pd

from netcore_tac.cleaning import (
    clean_tickets,
    drop_duplicate_tickets,
    normalize_region,
    normalize_severity,
)


def make_tickets(rows: list[dict]) -> pd.DataFrame:
    """Minimal ticket frame; each row overrides the defaults."""
    defaults = {"ticket_id": "T", "created_at": pd.Timestamp("2025-01-01 09:00"),
                "product_family": "Routers", "severity": "S2", "region": "EMEA",
                "channel": "Email", "devices_affected": 1, "first_response_minutes": 10.0,
                "resolution_hours": 20.0}
    return pd.DataFrame([{**defaults, "ticket_id": f"T{i}", **row} for i, row in enumerate(rows)])


def test_normalize_severity_variants():
    raw = pd.Series(["Sev-1", "SEV1", "s1", "Sev 2", "S3", None])
    result = normalize_severity(raw)
    assert result[:5].tolist() == ["S1", "S1", "S1", "S2", "S3"]
    assert pd.isna(result[5])


def test_normalize_region():
    assert normalize_region(pd.Series([" emea ", "amer ", "APJC"])).tolist() == ["EMEA", "AMER", "APJC"]


def test_clean_fixes_labels():
    df = make_tickets([{"severity": "Sev-1", "region": " apjc "}, {"severity": np.nan}])
    out = clean_tickets(df)
    assert out.loc[0, "severity"] == "S1"
    assert out.loc[0, "region"] == "APJC"
    assert pd.isna(out.loc[1, "severity"])


def test_negative_first_response_becomes_nan():
    out = clean_tickets(make_tickets([{"first_response_minutes": -5.0},
                                      {"first_response_minutes": 0.0}]))
    assert pd.isna(out.loc[0, "first_response_minutes"])
    assert out.loc[1, "first_response_minutes"] == 0.0


def test_duplicates_keep_earliest_and_original_order():
    df = make_tickets([
        {"created_at": pd.Timestamp("2025-01-03"), "devices_affected": 2},
        {"created_at": pd.Timestamp("2025-01-05"), "devices_affected": 7, "channel": "Phone"},
        {"created_at": pd.Timestamp("2025-01-02"), "devices_affected": 7, "channel": "Email"},
    ])
    out = drop_duplicate_tickets(df)
    # row 1 repeats the earlier row 2 (only ticket_id, channel, created_at differ)
    assert out["ticket_id"].tolist() == ["T0", "T2"]


def test_rows_differing_on_other_columns_are_kept():
    df = make_tickets([{"devices_affected": 1}, {"devices_affected": 2}])
    assert len(drop_duplicate_tickets(df)) == 2


def test_tickets_above_1000_hours_removed():
    out = clean_tickets(make_tickets([{"resolution_hours": 1000.0}, {"resolution_hours": 1000.1},
                                      {"resolution_hours": 2500.0}]))
    assert out["resolution_hours"].tolist() == [1000.0]


def test_input_not_modified():
    df = make_tickets([{"severity": "sev-2", "region": " emea", "first_response_minutes": -1.0},
                       {"resolution_hours": 2000.0}])
    before = df.copy()
    clean_tickets(df)
    pd.testing.assert_frame_equal(df, before)


def test_clean_synthetic_dataset_only_valid_labels(small_raw_df):
    out = clean_tickets(small_raw_df)
    assert set(out["severity"].dropna()) <= {"S1", "S2", "S3", "S4"}
    assert set(out["region"]) <= {"AMER", "EMEA", "APJC"}
    assert (out["first_response_minutes"].dropna() >= 0).all()
    assert (out["resolution_hours"] <= 1000).all()
