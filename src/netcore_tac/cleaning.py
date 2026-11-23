"""Clean raw TAC ticket exports (reproduces notebook Part 1 — Data Quality)."""

import numpy as np
import pandas as pd

# Columns ignored when deciding whether two tickets are duplicates
DUPLICATE_IGNORE_COLUMNS = ["ticket_id", "channel", "created_at"]

# Tickets above this many hours are parked Hardware RMA cases, not real work time
MAX_RESOLUTION_HOURS = 1000


def normalize_severity(severity: pd.Series) -> pd.Series:
    """Map label variants to S1–S4: "Sev-1", "SEV1", "s1" -> "S1"; blanks stay blank."""
    return (severity.str.upper()
            .str.replace("EV", "").str.replace(" ", "").str.replace("-", ""))


def normalize_region(region: pd.Series) -> pd.Series:
    """Strip whitespace and upper-case: " emea " -> "EMEA"."""
    return region.str.strip().str.upper()


def drop_duplicate_tickets(df: pd.DataFrame) -> pd.DataFrame:
    """Drop tickets that repeat an earlier ticket on every column except
    ticket_id, channel and created_at.

    "Earlier" is by ``created_at``; the original row order is kept.
    """
    match_cols = [c for c in df.columns if c not in DUPLICATE_IGNORE_COLUMNS]
    is_duplicate = df.sort_values("created_at").duplicated(subset=match_cols, keep="first")
    return df.drop(index=is_duplicate[is_duplicate].index)


def clean_tickets(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all notebook Part 1 cleaning rules; the input is never modified.

    Rules: severity and region labels, negative first-response times -> NaN,
    duplicates removed, tickets above 1,000 h removed.

    Args:
        df: Raw ticket export with ``created_at`` parsed as datetime.

    Returns:
        A cleaned copy.
    """
    df = df.copy()
    df["severity"] = normalize_severity(df["severity"])
    df["region"] = normalize_region(df["region"])
    df.loc[df["first_response_minutes"] < 0, "first_response_minutes"] = np.nan
    df = drop_duplicate_tickets(df)
    return df[~(df["resolution_hours"] > MAX_RESOLUTION_HOURS)].copy()
