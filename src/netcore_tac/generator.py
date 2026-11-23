"""Generate clean (defect-free) NetCore TAC Desk tickets.

Every function takes a ``numpy.random.Generator`` so results are reproducible
for a given seed.
"""

import numpy as np
import pandas as pd

from netcore_tac import config

COLUMNS = [
    "ticket_id",
    "created_at",
    "product_family",
    "severity",
    "customer_tier",
    "region",
    "channel",
    "devices_affected",
    "software_version_months",
    "prior_tickets_90d",
    "engineer_experience_years",
    "first_response_minutes",
    "customer_comments",
    "escalation_count",
    "reopened",
    "resolution_code",
    "resolution_hours",
]


def sample_categories(mapping: dict, n: int, rng: np.random.Generator) -> np.ndarray:
    """Draw ``n`` values from a ``{category: probability}`` mapping.

    Args:
        mapping: Category names mapped to probabilities that sum to 1.
        n: Number of values to draw.
        rng: NumPy random generator.

    Returns:
        Array of ``n`` category names.
    """
    return rng.choice(list(mapping.keys()), size=n, p=list(mapping.values()))


def format_ticket_ids(start: int, count: int) -> list[str]:
    """Build sequential ticket IDs such as ``TKT-000001``.

    Args:
        start: Number of the first ticket.
        count: How many IDs to build.

    Returns:
        List of ticket ID strings.
    """
    return [f"TKT-{i:06d}" for i in range(start, start + count)]


def generate_created_at(n: int, rng: np.random.Generator, weekday_share: float = 0.9,
                        business_hours_share: float = 0.9) -> pd.Series:
    """Generate ticket creation timestamps across the configured year.

    Most tickets fall on weekdays between 08:00 and 20:00.

    Args:
        n: Number of timestamps.
        rng: NumPy random generator.
        weekday_share: Fraction of tickets created on weekdays.
        business_hours_share: Fraction of tickets created between 08:00 and 20:00.

    Returns:
        Series of timestamps.
    """
    days = pd.date_range(f"{config.YEAR}-01-01", f"{config.YEAR}-12-31", freq="D")
    weekdays = days[days.day_of_week < 5]
    weekends = days[days.day_of_week >= 5]

    on_weekday = rng.random(n) < weekday_share
    day = np.where(
        on_weekday,
        rng.choice(weekdays.values, size=n),
        rng.choice(weekends.values, size=n),
    )

    in_business_hours = rng.random(n) < business_hours_share
    hour = np.where(in_business_hours, rng.integers(8, 20, size=n), rng.integers(0, 24, size=n))
    seconds = hour * 3600 + rng.integers(0, 3600, size=n)

    return pd.Series(pd.to_datetime(day) + pd.to_timedelta(seconds, unit="s"))


def generate_devices_affected(n: int, rng: np.random.Generator, max_devices: int = 60) -> np.ndarray:
    """Generate a right-skewed device count (mostly 1-3, a few around 50).

    Args:
        n: Number of values.
        rng: NumPy random generator.
        max_devices: Upper cap on devices affected.

    Returns:
        Integer array with values in ``[1, max_devices]``.
    """
    raw = np.ceil(rng.lognormal(mean=0.3, sigma=0.9, size=n))
    return np.clip(raw, 1, max_devices).astype(int)


def generate_software_version_months(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate the age of the running software version in months (0-60).

    Args:
        n: Number of values.
        rng: NumPy random generator.

    Returns:
        Integer array with values in ``[0, 60]``.
    """
    return rng.integers(0, 61, size=n)


def generate_prior_tickets(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate the number of prior tickets in the last 90 days (0 to ~15).

    Args:
        n: Number of values.
        rng: NumPy random generator.

    Returns:
        Integer array with values in ``[0, 15]``.
    """
    return np.clip(rng.poisson(2.0, size=n), 0, 15)


def generate_engineer_experience(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate engineer experience in years (0.5-20, one decimal).

    Args:
        n: Number of values.
        rng: NumPy random generator.

    Returns:
        Float array with values in ``[0.5, 20.0]``.
    """
    return np.round(np.clip(rng.gamma(shape=2.5, scale=2.8, size=n), 0.5, 20.0), 1)


def generate_first_response_minutes(severity: np.ndarray, tier: np.ndarray,
                                    rng: np.random.Generator) -> np.ndarray:
    """Generate first-response minutes; faster for S1/S2 and Platinum customers.

    Args:
        severity: Severity per ticket (``S1``-``S4``).
        tier: Customer tier per ticket.
        rng: NumPy random generator.

    Returns:
        Float array of minutes rounded to one decimal.
    """
    base = pd.Series(severity).map(config.BASE_FIRST_RESPONSE_MINUTES).to_numpy()
    factor = pd.Series(tier).map(config.TIER_RESPONSE_MULTIPLIER).to_numpy()
    noise = rng.lognormal(mean=0.0, sigma=0.4, size=len(severity))
    return np.round(np.maximum(base * factor * noise, 1.0), 1)


def generate_customer_comments(product: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Pick a realistic comment template and fill in the product family.

    Args:
        product: Product family per ticket.
        rng: NumPy random generator.

    Returns:
        Array of comment strings.
    """
    templates = rng.choice(config.COMMENT_TEMPLATES, size=len(product))
    return np.array([t.format(product=p) for t, p in zip(templates, product)])


def generate_resolution_hours(df: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """Generate resolution hours from the ticket's drivers.

    Drivers: severity, resolution code (Software Bug / Hardware RMA take much
    longer), customer tier, devices affected, engineer experience (more is
    faster), software version age, prior tickets and random noise.

    Args:
        df: Tickets with severity, resolution_code, customer_tier,
            devices_affected, engineer_experience_years,
            software_version_months and prior_tickets_90d.
        rng: NumPy random generator.

    Returns:
        Positive float array rounded to one decimal.
    """
    base = df["severity"].map(config.BASE_RESOLUTION_HOURS).to_numpy()
    code = df["resolution_code"].map(config.RESOLUTION_CODE_MULTIPLIER).to_numpy()
    tier = df["customer_tier"].map(config.TIER_RESOLUTION_MULTIPLIER).to_numpy()
    devices = 1 + 0.02 * (df["devices_affected"].to_numpy() - 1)
    experience = np.exp(-0.04 * (df["engineer_experience_years"].to_numpy() - 5))
    version = 1 + 0.004 * df["software_version_months"].to_numpy()
    prior = 1 + 0.03 * df["prior_tickets_90d"].to_numpy()
    noise = rng.lognormal(mean=0.0, sigma=0.35, size=len(df))

    hours = base * code * tier * devices * experience * version * prior * noise
    return np.round(np.maximum(hours, 0.1), 1)


def sla_ratio(hours: np.ndarray, severity: np.ndarray) -> np.ndarray:
    """Return resolution hours divided by the SLA hours for each severity.

    Args:
        hours: Resolution hours per ticket.
        severity: Clean severity per ticket.

    Returns:
        Float array of hours / SLA hours.
    """
    sla = pd.Series(severity).map(config.SLA_HOURS).to_numpy()
    return np.asarray(hours) / sla


def generate_escalation_count(hours: np.ndarray, severity: np.ndarray,
                              rng: np.random.Generator) -> np.ndarray:
    """Generate escalation counts (0-5) that rise as tickets run past SLA.

    Args:
        hours: Resolution hours per ticket.
        severity: Clean severity per ticket.
        rng: NumPy random generator.

    Returns:
        Integer array with values in ``[0, 5]``.
    """
    ratio = np.minimum(sla_ratio(hours, severity), 4.0)
    return np.clip(rng.poisson(0.2 + 0.6 * ratio), 0, 5)


def generate_reopened(hours: np.ndarray, severity: np.ndarray,
                      rng: np.random.Generator) -> np.ndarray:
    """Generate the reopened flag (~8% True, more likely for longer tickets).

    Args:
        hours: Resolution hours per ticket.
        severity: Clean severity per ticket.
        rng: NumPy random generator.

    Returns:
        Boolean array.
    """
    logit = -2.2 + 1.2 * np.log(sla_ratio(hours, severity))
    probability = 1 / (1 + np.exp(-logit))
    return rng.random(len(hours)) < probability


def generate_clean_tickets(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Generate ``n`` clean tickets sorted by creation time.

    The ``sla_breached`` column is not added here; see
    ``quality_issues.compute_sla_breached``.

    Args:
        n: Number of tickets.
        rng: NumPy random generator.

    Returns:
        DataFrame with the columns in ``COLUMNS``.
    """
    df = pd.DataFrame({"created_at": generate_created_at(n, rng)})
    df["product_family"] = sample_categories(config.PRODUCT_FAMILIES, n, rng)
    df["severity"] = sample_categories(config.SEVERITIES, n, rng)
    df["customer_tier"] = sample_categories(config.CUSTOMER_TIERS, n, rng)
    df["region"] = sample_categories(config.REGIONS, n, rng)
    df["channel"] = sample_categories(config.CHANNELS, n, rng)
    df["devices_affected"] = generate_devices_affected(n, rng)
    df["software_version_months"] = generate_software_version_months(n, rng)
    df["prior_tickets_90d"] = generate_prior_tickets(n, rng)
    df["engineer_experience_years"] = generate_engineer_experience(n, rng)
    df["first_response_minutes"] = generate_first_response_minutes(
        df["severity"].to_numpy(), df["customer_tier"].to_numpy(), rng
    )
    df["customer_comments"] = generate_customer_comments(df["product_family"].to_numpy(), rng)
    df["resolution_code"] = sample_categories(config.RESOLUTION_CODES, n, rng)
    df["resolution_hours"] = generate_resolution_hours(df, rng)
    df["escalation_count"] = generate_escalation_count(
        df["resolution_hours"].to_numpy(), df["severity"].to_numpy(), rng
    )
    df["reopened"] = generate_reopened(
        df["resolution_hours"].to_numpy(), df["severity"].to_numpy(), rng
    )

    df = df.sort_values("created_at", kind="stable").reset_index(drop=True)
    df["ticket_id"] = format_ticket_ids(1, n)
    return df[COLUMNS]
