"""Build the full NetCore TAC Desk dataset: clean tickets plus data-quality issues."""

import numpy as np
import pandas as pd

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
)


def build_dataset(n: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generate ``n`` tickets with outliers, missing values, inconsistent labels
    and near duplicates.

    Order: clean tickets -> outliers -> SLA breached (clean severity) ->
    negative first response -> missing values -> severity / region variants ->
    near duplicates. Near duplicates are included within ``n``.

    Args:
        n: Total number of rows, near duplicates included.
        seed: Seed for ``numpy.random.default_rng``; same seed, same output.

    Returns:
        DataFrame with ``n`` rows.
    """
    rng = np.random.default_rng(seed)
    n_duplicates = int(round(config.NEAR_DUPLICATE_FRACTION * n))

    df = generate_clean_tickets(n - n_duplicates, rng)
    df = inject_outliers(df, rng)
    df = compute_sla_breached(df)
    df = inject_negative_response(df, rng)

    df = inject_missing_values(df, "engineer_experience_years", config.MISSING_FRACTION_NUMERIC, rng)
    df = inject_missing_values(
        df, "first_response_minutes", config.MISSING_FRACTION_NUMERIC, rng,
        exclude=df["first_response_minutes"] < 0,
    )
    df = inject_missing_values(df, "severity", config.MISSING_FRACTION_SEVERITY, rng)

    df = inject_severity_variants(df, rng)
    df = inject_region_variants(df, rng)
    return add_near_duplicates(df, n_duplicates, rng)
