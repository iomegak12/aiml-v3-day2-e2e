"""Turn one validated ticket into a resolution-hours prediction."""

from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from netcore_tac.api.schemas import TicketIn
from netcore_tac.features import ALL_FEATURES, NUMERIC_FEATURES, add_tac_features
from netcore_tac.model import TrainingResult


def clip_and_round(hours: float) -> float:
    """Never below 0 h; rounded to 1 decimal."""
    return round(max(float(hours), 0.0), 1)


def ticket_to_frame(ticket: TicketIn) -> pd.DataFrame:
    """One-row DataFrame in the training layout (before add_tac_features)."""
    row = ticket.model_dump()
    row["created_at"] = row["created_at"].replace(tzinfo=None)   # wall-clock time as sent
    df = pd.DataFrame([row])
    df["created_at"] = pd.to_datetime(df["created_at"])
    df[NUMERIC_FEATURES] = df[NUMERIC_FEATURES].astype(float)    # None -> NaN for the imputer
    return df


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

    def predict(self, ticket: TicketIn) -> float:
        """Predicted resolution hours for one ticket (>= 0, 1 decimal)."""
        features = add_tac_features(ticket_to_frame(ticket))[ALL_FEATURES]
        return clip_and_round(self.pipeline.predict(features)[0])
