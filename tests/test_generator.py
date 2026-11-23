"""Unit tests for netcore_tac.generator (clean ticket generation)."""

import numpy as np
import pandas as pd
import pytest

from netcore_tac import config
from netcore_tac.generator import (
    COLUMNS,
    format_ticket_ids,
    generate_clean_tickets,
    generate_created_at,
    generate_devices_affected,
    generate_engineer_experience,
    sample_categories,
)

N = 5000


@pytest.fixture(scope="module")
def clean() -> pd.DataFrame:
    return generate_clean_tickets(N, np.random.default_rng(0))


def test_columns_and_row_count(clean):
    assert list(clean.columns) == COLUMNS
    assert len(clean) == N


def test_same_seed_same_output():
    a = generate_clean_tickets(300, np.random.default_rng(7))
    b = generate_clean_tickets(300, np.random.default_rng(7))
    pd.testing.assert_frame_equal(a, b)


def test_format_ticket_ids():
    assert format_ticket_ids(1, 3) == ["TKT-000001", "TKT-000002", "TKT-000003"]


def test_ticket_ids_unique_and_sorted_by_time(clean):
    assert clean["ticket_id"].is_unique
    assert clean["created_at"].is_monotonic_increasing


def test_sample_categories_respects_probabilities():
    values = sample_categories(config.SEVERITIES, 20000, np.random.default_rng(1))
    shares = pd.Series(values).value_counts(normalize=True)
    for level, p in config.SEVERITIES.items():
        assert shares[level] == pytest.approx(p, abs=0.02)


def test_created_at_mostly_weekday_business_hours():
    ts = generate_created_at(N, np.random.default_rng(2))
    assert (ts.dt.year == config.YEAR).all()
    assert (ts.dt.day_of_week < 5).mean() > 0.85
    assert ts.dt.hour.between(8, 19).mean() > 0.85


def test_devices_affected_right_skewed():
    devices = generate_devices_affected(N, np.random.default_rng(3))
    assert devices.min() >= 1
    assert (devices <= 3).mean() > 0.7
    assert devices.max() > 20


def test_engineer_experience_range():
    years = generate_engineer_experience(N, np.random.default_rng(4))
    assert years.min() >= 0.5 and years.max() <= 20.0
    assert np.allclose(years, np.round(years, 1))


def test_first_response_faster_for_high_severity_and_platinum(clean):
    by_sev = clean.groupby("severity")["first_response_minutes"].median()
    assert by_sev["S1"] < by_sev["S2"] < by_sev["S3"] < by_sev["S4"]
    by_tier = clean.groupby("customer_tier")["first_response_minutes"].median()
    assert by_tier["Platinum"] < by_tier["Silver"]


def test_comments_mention_product_family(clean):
    assert all(p in c for p, c in zip(clean["product_family"], clean["customer_comments"]))


def test_rma_and_bug_take_longer(clean):
    med = clean.groupby("resolution_code")["resolution_hours"].median()
    assert med["Hardware RMA"] > med["Config Fix"]
    assert med["Software Bug"] > med["Config Fix"]


def test_resolution_hours_positive_one_decimal(clean):
    hours = clean["resolution_hours"]
    assert (hours > 0).all()
    assert np.allclose(hours, hours.round(1))


def test_escalation_count_range(clean):
    assert clean["escalation_count"].between(0, 5).all()


def test_reopened_rate_and_link_to_long_tickets(clean):
    assert clean["reopened"].mean() == pytest.approx(0.08, abs=0.03)
    by_flag = clean.groupby("reopened")["resolution_hours"].median()
    assert by_flag[True] > by_flag[False]
