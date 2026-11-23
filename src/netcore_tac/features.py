"""Model feature lists and the triage feature flags (notebook Part 3)."""

import pandas as pd

NUMERIC_FEATURES = [
    "devices_affected",
    "software_version_months",
    "prior_tickets_90d",
    "engineer_experience_years",
    "first_response_minutes",
]
FLAG_FEATURES = ["is_weekend", "old_software"]
CATEGORICAL_FEATURES = ["product_family", "severity", "customer_tier", "region", "channel"]
ALL_FEATURES = NUMERIC_FEATURES + FLAG_FEATURES + CATEGORICAL_FEATURES
TARGET = "resolution_hours"

# Never model inputs: leak the outcome or are unknown at triage
EXCLUDED_COLUMNS = [
    "resolution_code",
    "escalation_count",
    "reopened",
    "sla_breached",
    "ticket_id",
    "customer_comments",
]

# Software older than this many months counts as "old"
OLD_SOFTWARE_MONTHS = 36


def add_tac_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the is_weekend and old_software flags (0/1); drop created_at.

    Args:
        df: Tickets with ``created_at`` (datetime) and ``software_version_months``.

    Returns:
        A new DataFrame; the caller's data is never changed.
    """
    df = df.copy()
    df["is_weekend"] = (df["created_at"].dt.day_of_week >= 5).astype(int)   # 5 = Sat, 6 = Sun
    df["old_software"] = (df["software_version_months"] > OLD_SOFTWARE_MONTHS).astype(int)
    return df.drop(columns="created_at")
