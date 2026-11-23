"""Turn one validated ticket into a resolution-hours prediction.

Steps: ticket -> one-row DataFrame -> clamp numeric inputs to the training range ->
add_tac_features -> model -> per-severity minimum ETA -> round to 1 decimal.
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from netcore_tac.api.schemas import TicketIn
from netcore_tac.features import ALL_FEATURES, NUMERIC_FEATURES, add_tac_features
from netcore_tac.model import TrainingResult


@dataclass(frozen=True)
class Prediction:
    """Predicted hours plus the inputs that were clamped to the training range."""

    hours: float
    adjusted_inputs: list[dict[str, Any]] = field(default_factory=list)


def clip_and_round(hours: float, minimum: float = 0.0) -> float:
    """Never below ``minimum`` (and never below 0 h); rounded to 1 decimal."""
    return round(max(float(hours), float(minimum), 0.0), 1)


def _plain_number(value: float) -> int | float:
    value = float(value)
    return int(value) if value.is_integer() else value


def ticket_to_frame(ticket: TicketIn) -> pd.DataFrame:
    """One-row DataFrame in the training layout (before add_tac_features)."""
    row = ticket.model_dump()
    row["created_at"] = row["created_at"].replace(tzinfo=None)   # wall-clock time as sent
    df = pd.DataFrame([row])
    df["created_at"] = pd.to_datetime(df["created_at"])
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].astype(float)    # None -> NaN for the imputer
    return df


def clamp_inputs(df: pd.DataFrame,
                 input_ranges: dict[str, list[float]]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Clamp each numeric input of a one-row frame to its training [min, max].

    Blank (NaN) values are left for the imputer. Returns a new frame and the
    adjustments as ``[{field, original, used}]``.
    """
    df = df.copy()
    adjustments: list[dict[str, Any]] = []
    for column, (low, high) in input_ranges.items():
        if column not in df.columns:
            continue
        value = df.at[0, column]
        if pd.isna(value):
            continue
        used = min(max(float(value), float(low)), float(high))
        if used != float(value):
            df.at[0, column] = used
            adjustments.append({"field": column, "original": _plain_number(value),
                                "used": _plain_number(used)})
    return df, adjustments


class Predictor:
    """Wraps the loaded pipeline and its metadata."""

    def __init__(self, pipeline: Pipeline, metadata: dict[str, Any]) -> None:
        self.pipeline = pipeline
        self.metadata = metadata

    @classmethod
    def from_training_result(cls, result: TrainingResult) -> "Predictor":
        return cls(result.pipeline, result.metadata)

    @property
    def model_version(self) -> str:
        return str(self.metadata.get("model_version", "unknown"))

    @property
    def trained_at(self) -> str:
        return str(self.metadata.get("trained_at", "unknown"))

    @property
    def min_hours_by_severity(self) -> dict[str, float]:
        """Per-severity minimum ETA (empty for models trained before 0.5.0)."""
        return dict(self.metadata.get("min_hours_by_severity") or {})

    @property
    def input_ranges(self) -> dict[str, list[float]]:
        """Training [min, max] per numeric feature (empty for models trained before 0.5.0)."""
        return dict(self.metadata.get("input_ranges") or {})

    def predict(self, ticket: TicketIn) -> Prediction:
        """Predicted resolution hours (>= the severity minimum, 1 decimal) and clamped inputs."""
        frame, adjustments = clamp_inputs(ticket_to_frame(ticket), self.input_ranges)
        raw = self.pipeline.predict(add_tac_features(frame)[ALL_FEATURES])[0]
        floor = self.min_hours_by_severity.get(ticket.severity, 0.0)
        return Prediction(hours=clip_and_round(raw, floor), adjusted_inputs=adjustments)
