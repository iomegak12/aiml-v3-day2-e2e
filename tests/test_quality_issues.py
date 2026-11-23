"""Unit tests for netcore_tac.quality_issues (data-quality injection)."""

import numpy as np
import pandas as pd
import pytest

from netcore_tac import config
from netcore_tac.generator import generate_clean_tickets
from netcore_tac.quality_issues import (
    add_near_duplicates,
    compute_sla_breached,
    inject_missing_values,
    inject_negative_response,
    inject_outliers,
    inject_region_variants,
    inject_severity_variants,
    region_variants,
    severity_variants,
)

N = 2000


@pytest.fixture()
def clean() -> pd.DataFrame:
    return generate_clean_tickets(N, np.random.default_rng(0))


def rng():
    return np.random.default_rng(99)


def test_outliers(clean):
    out = inject_outliers(clean, rng())
    mask = out["resolution_hours"] >= config.OUTLIER_HOURS_RANGE[0]
    assert mask.sum() == round(config.OUTLIER_FRACTION * N)
    assert out.loc[mask, "resolution_hours"].le(config.OUTLIER_HOURS_RANGE[1]).all()
    assert (out.loc[mask, "resolution_code"] == "Hardware RMA").all()


def test_input_not_modified(clean):
    before = clean.copy()
    inject_outliers(clean, rng())
    pd.testing.assert_frame_equal(clean, before)


def test_sla_breached_rule_and_position(clean):
    out = compute_sla_breached(clean)
    expected = out["resolution_hours"] > out["severity"].map(config.SLA_HOURS)
    assert (out["sla_breached"] == expected).all()
    cols = list(out.columns)
    assert cols.index("sla_breached") == cols.index("resolution_hours") - 1


def test_s2_has_highest_breach_rate(clean):
    rates = compute_sla_breached(clean).groupby("severity")["sla_breached"].mean()
    assert rates.idxmax() == "S2"


def test_negative_response_count(clean):
    out = inject_negative_response(clean, rng())
    assert (out["first_response_minutes"] < 0).sum() == config.NEGATIVE_RESPONSE_COUNT


def test_missing_values_fraction(clean):
    out = inject_missing_values(clean, "engineer_experience_years", 0.05, rng())
    assert out["engineer_experience_years"].isna().sum() == round(0.05 * N)


def test_missing_values_respect_exclude(clean):
    negative = inject_negative_response(clean, rng())
    exclude = negative["first_response_minutes"] < 0
    out = inject_missing_values(negative, "first_response_minutes", 0.05, rng(), exclude=exclude)
    assert out["first_response_minutes"].isna().sum() == round(0.05 * N)
    assert (out["first_response_minutes"] < 0).sum() == config.NEGATIVE_RESPONSE_COUNT


def test_variant_helpers():
    assert severity_variants("S1") == ["SEV1", "Sev 1", "Sev-1", "s1"]
    assert set(region_variants("AMER")) == {"amer", "amer ", " AMER ", "AMER "}


def test_severity_variants_skip_missing_rows(clean):
    with_nan = inject_missing_values(clean, "severity", 0.01, rng())
    nan_rows = with_nan["severity"].isna()
    out = inject_severity_variants(with_nan, np.random.default_rng(5))
    changed = out["severity"].notna() & ~out["severity"].isin(config.SEVERITIES)
    assert changed.sum() == round(0.03 * N)
    assert not (changed & nan_rows).any()
    assert out["severity"].isna().sum() == nan_rows.sum()
    allowed = {v for s in config.SEVERITIES for v in severity_variants(s)}
    assert set(out.loc[changed, "severity"]) <= allowed
    # every variant keeps its original severity number
    assert (out.loc[changed, "severity"].str[-1] == clean.loc[changed, "severity"].str[-1]).all()


def test_region_variants(clean):
    out = inject_region_variants(clean, rng())
    changed = ~out["region"].isin(config.REGIONS)
    assert changed.sum() == round(0.03 * N)
    assert (out.loc[changed, "region"].str.strip().str.upper() == clean.loc[changed, "region"]).all()


def test_near_duplicates(clean):
    count = 40
    out = add_near_duplicates(clean, count, rng())
    assert len(out) == N + count
    assert out["ticket_id"].is_unique
    assert out["created_at"].is_monotonic_increasing

    new_ids = [f"TKT-{i:06d}" for i in range(N + 1, N + count + 1)]
    dup_rows = out[out["ticket_id"].isin(new_ids)]
    assert len(dup_rows) == count

    for _, row in dup_rows.iterrows():
        match = clean[
            (clean["customer_comments"] == row["customer_comments"])
            & (clean["resolution_hours"] == row["resolution_hours"])
            & (clean["devices_affected"] == row["devices_affected"])
            & (clean["severity"] == row["severity"])
        ]
        assert len(match) >= 1
        src = match.iloc[0]
        assert {src["channel"], row["channel"]} == {"Email", "Phone"}
        delta = (row["created_at"] - src["created_at"]).total_seconds() / 60
        assert config.NEAR_DUPLICATE_MINUTES_RANGE[0] <= delta <= config.NEAR_DUPLICATE_MINUTES_RANGE[1]
