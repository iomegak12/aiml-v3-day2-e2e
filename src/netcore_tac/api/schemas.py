"""Pydantic v2 request / response models with OpenAPI examples."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"


class CustomerTier(StrEnum):
    PLATINUM = "Platinum"
    GOLD = "Gold"
    SILVER = "Silver"


class Region(StrEnum):
    AMER = "AMER"
    EMEA = "EMEA"
    APJC = "APJC"


class Channel(StrEnum):
    EMAIL = "Email"
    PHONE = "Phone"
    PORTAL = "Portal"


TICKET_EXAMPLE = {
    "created_at": "2026-11-23T10:15:00",
    "product_family": "Routers",
    "severity": "S2",
    "customer_tier": "Gold",
    "region": "EMEA",
    "channel": "Phone",
    "devices_affected": 4,
    "software_version_months": 40,
    "prior_tickets_90d": 1,
    "engineer_experience_years": 6.5,
    "first_response_minutes": 20.0,
}


class TicketIn(BaseModel):
    """Fields known at triage time for one ticket."""

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,   # plain strings reach the model's encoder
        json_schema_extra={"examples": [TICKET_EXAMPLE]},
    )

    created_at: datetime = Field(description="When the ticket was opened (ISO-8601); "
                                             "used for the weekend flag as given")
    product_family: str = Field(min_length=1, max_length=50,
                                description="Product line; unseen products are allowed")
    severity: Severity
    customer_tier: CustomerTier
    region: Region
    channel: Channel
    devices_affected: int = Field(ge=1, le=1000)
    software_version_months: int = Field(ge=0, le=240,
                                         description="Age of the running software release")
    prior_tickets_90d: int = Field(ge=0, le=100,
                                   description="Tickets from this customer in the last 90 days")
    engineer_experience_years: float | None = Field(
        default=None, ge=0, le=50, allow_inf_nan=False,
        description="Null if unknown; filled with the training median")
    first_response_minutes: float | None = Field(
        default=None, ge=0, le=10080, allow_inf_nan=False,
        description="Null if unknown; filled with the training median")


class PredictionOut(BaseModel):
    """Predicted resolution time for one ticket."""

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "predicted_hours": 31.4,
        "model_version": "0.3.0",
        "request_id": "3f2b8c1e-6f1d-4c55-9a43-2f0c1f8f6b7a",
    }]})

    predicted_hours: float = Field(ge=0, description="Rounded to 1 decimal, never below 0")
    model_version: str
    request_id: str = Field(description="UUID4; also sent as the X-Request-ID header")


class HealthOut(BaseModel):
    status: str = Field(examples=["ok"])


class ReadyOut(BaseModel):
    status: str = Field(examples=["ready"])
    model_version: str = Field(examples=["0.3.0"])
    trained_at: str = Field(examples=["2026-11-23T10:49:42+00:00"])


class FieldError(BaseModel):
    field: str = Field(examples=["severity"])
    message: str = Field(examples=["Input should be 'S1', 'S2', 'S3' or 'S4'"])


class ProblemDetails(BaseModel):
    """RFC 9457 problem details (media type application/problem+json)."""

    type: str = Field(examples=["https://netcore.example/problems/validation-error"])
    title: str = Field(examples=["Request validation failed"])
    status: int = Field(examples=[422])
    detail: str = Field(examples=["1 field(s) failed validation."])
    instance: str = Field(examples=["/api/v1/predictions"])
    request_id: str | None = Field(default=None,
                                   examples=["3f2b8c1e-6f1d-4c55-9a43-2f0c1f8f6b7a"])
    errors: list[FieldError] | None = None
