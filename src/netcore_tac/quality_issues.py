"""Inject realistic data-quality issues into clean TAC tickets.

Each function returns a new DataFrame and leaves its input unchanged.
"""

import numpy as np
import pandas as pd

from netcore_tac import config


def pick_rows(index: pd.Index, fraction: float, rng: np.random.Generator) -> pd.Index:
    """Randomly pick ``round(fraction * len(index))`` labels from ``index``.

    Args:
        index: Candidate row labels.
        fraction: Share of candidates to pick (0-1).
        rng: NumPy random generator.

    Returns:
        Index of the picked row labels.
    """
    count = min(int(round(fraction * len(index))), len(index))
    return pd.Index(rng.choice(index.to_numpy(), size=count, replace=False))


def inject_outliers(df: pd.DataFrame, rng: np.random.Generator,
                    fraction: float = config.OUTLIER_FRACTION,
                    hours_range: tuple = config.OUTLIER_HOURS_RANGE) -> pd.DataFrame:
    """Turn a share of tickets into extreme long-running Hardware RMA cases.

    Args:
        df: Tickets.
        rng: NumPy random generator.
        fraction: Share of tickets to make outliers.
        hours_range: ``(low, high)`` resolution hours for outliers.

    Returns:
        Copy of ``df`` with outlier resolution hours and resolution code.
    """
    df = df.copy()
    rows = pick_rows(df.index, fraction, rng)
    df.loc[rows, "resolution_hours"] = np.round(rng.uniform(*hours_range, size=len(rows)), 1)
    df.loc[rows, "resolution_code"] = config.OUTLIER_RESOLUTION_CODE
    return df


def compute_sla_breached(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``sla_breached``: resolution hours above the SLA of the severity.

    Must run while ``severity`` is still clean (before missing values and
    inconsistent labels are injected). The column is placed just before
    ``resolution_hours``.

    Args:
        df: Tickets with clean ``severity`` and ``resolution_hours``.

    Returns:
        Copy of ``df`` with a boolean ``sla_breached`` column.
    """
    df = df.copy()
    sla = df["severity"].map(config.SLA_HOURS)
    breached = df["resolution_hours"] > sla
    df.insert(df.columns.get_loc("resolution_hours"), "sla_breached", breached)
    return df


def inject_negative_response(df: pd.DataFrame, rng: np.random.Generator,
                             count: int = config.NEGATIVE_RESPONSE_COUNT) -> pd.DataFrame:
    """Make ``first_response_minutes`` negative for ``count`` random tickets.

    Args:
        df: Tickets.
        rng: NumPy random generator.
        count: Number of tickets to corrupt.

    Returns:
        Copy of ``df`` with negative first-response values.
    """
    df = df.copy()
    count = min(count, len(df))
    rows = rng.choice(df.index.to_numpy(), size=count, replace=False)
    df.loc[rows, "first_response_minutes"] = -df.loc[rows, "first_response_minutes"].abs()
    return df


def inject_missing_values(df: pd.DataFrame, column: str, fraction: float,
                          rng: np.random.Generator,
                          exclude: pd.Series | None = None) -> pd.DataFrame:
    """Set a share of values in ``column`` to missing (NaN).

    Args:
        df: Tickets.
        column: Column to blank out.
        fraction: Share of eligible rows to blank out.
        rng: NumPy random generator.
        exclude: Optional boolean mask of rows that must stay untouched.

    Returns:
        Copy of ``df`` with missing values in ``column``.
    """
    df = df.copy()
    candidates = df.index if exclude is None else df.index[~exclude]
    rows = pick_rows(candidates, fraction * len(df) / max(len(candidates), 1), rng)
    df.loc[rows, column] = np.nan
    return df


def severity_variants(severity: str) -> list[str]:
    """Return inconsistent spellings of a clean severity, e.g. ``S2`` -> ``SEV2``.

    Args:
        severity: Clean severity label (``S1``-``S4``).

    Returns:
        List of variant spellings.
    """
    number = severity[1:]
    return [p.format(n=number) for p in config.SEVERITY_VARIANT_PATTERNS]


def region_variants(region: str) -> list[str]:
    """Return inconsistent spellings of a region, e.g. ``EMEA`` -> ``emea``.

    Args:
        region: Clean region label.

    Returns:
        List of variant spellings.
    """
    return [p.format(lower=region.lower(), upper=region.upper())
            for p in config.REGION_VARIANT_PATTERNS]


def inject_label_variants(df: pd.DataFrame, column: str, fraction: float, variants_fn,
                          rng: np.random.Generator) -> pd.DataFrame:
    """Replace a share of non-missing labels with inconsistent spellings.

    Args:
        df: Tickets.
        column: Categorical column to make inconsistent.
        fraction: Share of all rows to change.
        variants_fn: Function mapping a clean label to its variant spellings.
        rng: NumPy random generator.

    Returns:
        Copy of ``df`` with inconsistent labels in ``column``.
    """
    df = df.copy()
    candidates = df.index[df[column].notna()]
    rows = pick_rows(candidates, fraction * len(df) / max(len(candidates), 1), rng)
    df.loc[rows, column] = [rng.choice(variants_fn(value)) for value in df.loc[rows, column]]
    return df


def inject_severity_variants(df: pd.DataFrame, rng: np.random.Generator,
                             fraction: float = config.SEVERITY_VARIANT_FRACTION) -> pd.DataFrame:
    """Replace a share of severities with variants such as ``SEV1``, ``Sev 1``, ``Sev-1``.

    Rows whose severity is already missing are never chosen.

    Args:
        df: Tickets.
        rng: NumPy random generator.
        fraction: Share of rows to change.

    Returns:
        Copy of ``df`` with inconsistent severity labels.
    """
    return inject_label_variants(df, "severity", fraction, severity_variants, rng)


def inject_region_variants(df: pd.DataFrame, rng: np.random.Generator,
                           fraction: float = config.REGION_VARIANT_FRACTION) -> pd.DataFrame:
    """Replace a share of regions with variants such as ``emea``, ``amer ``, `` AMER ``.

    Args:
        df: Tickets.
        rng: NumPy random generator.
        fraction: Share of rows to change.

    Returns:
        Copy of ``df`` with inconsistent region labels.
    """
    return inject_label_variants(df, "region", fraction, region_variants, rng)


def add_near_duplicates(df: pd.DataFrame, count: int, rng: np.random.Generator,
                        minutes_range: tuple = config.NEAR_DUPLICATE_MINUTES_RANGE) -> pd.DataFrame:
    """Append near-duplicate copies of Email/Phone tickets.

    Each copy gets a new ticket ID (continuing the sequence), a ``created_at``
    a few minutes later, and its channel switched between Email and Phone.
    The result is sorted by ``created_at``.

    Args:
        df: Tickets with sequential ``ticket_id`` values.
        count: Number of near duplicates to add.
        rng: NumPy random generator.
        minutes_range: ``(low, high)`` minutes added to ``created_at``.

    Returns:
        New DataFrame with ``len(df) + count`` rows.
    """
    sources = df.index[df["channel"].isin(["Email", "Phone"])]
    rows = rng.choice(sources.to_numpy(), size=min(count, len(sources)), replace=False)
    copies = df.loc[rows].copy()

    copies["ticket_id"] = [f"TKT-{i:06d}" for i in range(len(df) + 1, len(df) + 1 + len(copies))]
    minutes = rng.integers(minutes_range[0], minutes_range[1] + 1, size=len(copies))
    copies["created_at"] = copies["created_at"] + pd.to_timedelta(minutes, unit="min")
    copies["channel"] = copies["channel"].map({"Email": "Phone", "Phone": "Email"})

    combined = pd.concat([df, copies], ignore_index=True)
    return combined.sort_values("created_at", kind="stable").reset_index(drop=True)
