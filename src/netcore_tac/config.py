"""Constants that describe the NetCore TAC Desk ticket population."""

YEAR = 2025

PRODUCT_FAMILIES = {
    "Routers": 0.30,
    "Switches": 0.30,
    "Firewalls": 0.15,
    "Wireless": 0.13,
    "SD-WAN": 0.12,
}

SEVERITIES = {"S1": 0.05, "S2": 0.20, "S3": 0.45, "S4": 0.30}

CUSTOMER_TIERS = {"Platinum": 0.20, "Gold": 0.35, "Silver": 0.45}

REGIONS = {"AMER": 0.40, "EMEA": 0.35, "APJC": 0.25}

CHANNELS = {"Email": 0.35, "Phone": 0.30, "Portal": 0.35}

RESOLUTION_CODES = {
    "Config Fix": 0.40,
    "Customer Environment": 0.20,
    "Software Bug": 0.25,
    "Hardware RMA": 0.15,
}

# Contractual SLA (hours) per severity - same values as today's fixed-rule ETA.
SLA_HOURS = {"S1": 4.0, "S2": 24.0, "S3": 48.0, "S4": 72.0}

# Median resolution hours per severity before other effects are applied.
# S2 sits closest to its SLA, so it ends up with the highest breach rate.
BASE_RESOLUTION_HOURS = {"S1": 2.2, "S2": 19.0, "S3": 22.0, "S4": 30.0}

RESOLUTION_CODE_MULTIPLIER = {
    "Config Fix": 0.8,
    "Customer Environment": 1.0,
    "Software Bug": 2.0,
    "Hardware RMA": 2.5,
}

TIER_RESOLUTION_MULTIPLIER = {"Platinum": 0.85, "Gold": 0.95, "Silver": 1.0}

# Median first-response minutes per severity, and tier speed-up factors.
BASE_FIRST_RESPONSE_MINUTES = {"S1": 10.0, "S2": 30.0, "S3": 90.0, "S4": 180.0}
TIER_RESPONSE_MULTIPLIER = {"Platinum": 0.6, "Gold": 0.85, "Silver": 1.0}

COMMENT_TEMPLATES = [
    "BGP sessions on our {product} keep flapping since the last upgrade.",
    "Our {product} rebooted unexpectedly during business hours.",
    "High CPU on the {product} is causing packet drops across the site.",
    "After the firmware update the {product} lost its configuration.",
    "Users at the branch cannot connect through the {product}.",
    "Intermittent latency spikes observed on the {product}.",
    "The {product} shows hardware alarms and a failed power supply.",
    "License error on the {product} is blocking new features.",
    "Memory leak suspected on the {product}; utilisation grows daily.",
    "Need urgent help: {product} outage impacting multiple customers.",
]

# Data-quality injection settings.
OUTLIER_FRACTION = 0.01
OUTLIER_HOURS_RANGE = (1500.0, 3000.0)
OUTLIER_RESOLUTION_CODE = "Hardware RMA"
NEGATIVE_RESPONSE_COUNT = 10
MISSING_FRACTION_NUMERIC = 0.05
MISSING_FRACTION_SEVERITY = 0.01
SEVERITY_VARIANT_FRACTION = 0.03
REGION_VARIANT_FRACTION = 0.03
NEAR_DUPLICATE_FRACTION = 0.02
NEAR_DUPLICATE_MINUTES_RANGE = (1, 15)

# Patterns used to create inconsistent labels; {n} is the severity number.
SEVERITY_VARIANT_PATTERNS = ["SEV{n}", "Sev {n}", "Sev-{n}", "s{n}"]
# {lower} / {upper} are the region name in lower / upper case.
REGION_VARIANT_PATTERNS = ["{lower}", "{lower} ", " {upper} ", "{upper} "]
