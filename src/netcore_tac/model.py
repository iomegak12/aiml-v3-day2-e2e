"""Build, train, evaluate, save and load the resolution-time model (notebook Part 4)."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from netcore_tac.features import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    FLAG_FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    add_tac_features,
)

PACKAGE_NAME = "day2"
TEST_SIZE = 0.2
RANDOM_STATE = 42


@dataclass
class TrainingResult:
    """A fitted pipeline plus its metadata (versions, row counts, test metrics)."""

    pipeline: Pipeline
    metadata: dict[str, Any]


def get_package_version() -> str:
    """Return the project version from pyproject.toml (via installed metadata)."""
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return "0.0.0+unknown"


def build_pipeline() -> Pipeline:
    """Unfitted preprocessing + LinearRegression pipeline, identical to the notebook."""
    numeric_pipe = Pipeline([("fill", SimpleImputer(strategy="median")),
                             ("scale", StandardScaler())])
    category_pipe = Pipeline([("fill", SimpleImputer(strategy="most_frequent")),
                              ("encode", OneHotEncoder(handle_unknown="ignore",
                                                       sparse_output=False))])
    preprocessor = ColumnTransformer([("num", numeric_pipe, NUMERIC_FEATURES),
                                      ("flags", "passthrough", FLAG_FEATURES),
                                      ("cat", category_pipe, CATEGORICAL_FEATURES)],
                                     verbose_feature_names_out=False)
    return Pipeline([("prep", preprocessor), ("model", LinearRegression())])


def regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    """MAE, RMSE and R² rounded to 4 decimals."""
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 4),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
    }


def train_model(df: pd.DataFrame, test_size: float = TEST_SIZE,
                random_state: int = RANDOM_STATE) -> TrainingResult:
    """Fit the pipeline on an 80/20 split of cleaned tickets and evaluate it.

    The returned pipeline is the one fitted on the training split only
    (no refit on all data), exactly as in the notebook.

    Args:
        df: Cleaned tickets (output of ``clean_tickets``) with ``created_at``.
        test_size: Fraction held out for testing.
        random_state: Seed for ``train_test_split``.

    Returns:
        TrainingResult with the fitted pipeline and metadata.
    """
    X = add_tac_features(df)[ALL_FEATURES]
    y = df[TARGET].copy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state)

    baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
    pipeline = build_pipeline().fit(X_train, y_train)

    metadata = {
        "model_version": get_package_version(),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scikit_learn_version": sklearn.__version__,
        "rows": {"total": len(df), "train": len(X_train), "test": len(X_test)},
        "features": {"numeric": NUMERIC_FEATURES, "flags": FLAG_FEATURES,
                     "categorical": CATEGORICAL_FEATURES},
        "target": TARGET,
        "metrics": {
            "baseline": regression_metrics(y_test, baseline.predict(X_test)),
            "model": regression_metrics(y_test, pipeline.predict(X_test)),
        },
    }
    return TrainingResult(pipeline=pipeline, metadata=metadata)


def save_model(result: TrainingResult, model_path: Path, metadata_path: Path) -> None:
    """Write the pipeline (joblib) and its metadata (JSON); create folders as needed."""
    model_path, metadata_path = Path(model_path), Path(metadata_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(result.pipeline, model_path)
    metadata_path.write_text(json.dumps(result.metadata, indent=2), encoding="utf-8")


def load_model(model_path: Path, metadata_path: Path) -> TrainingResult:
    """Load a pipeline and its metadata saved by ``save_model``.

    Only load files you trained yourself: joblib files can run code when loaded.

    Raises:
        FileNotFoundError: If either file is missing.
    """
    model_path, metadata_path = Path(model_path), Path(metadata_path)
    for path in (model_path, metadata_path):
        if not path.is_file():
            raise FileNotFoundError(f"Model file not found: {path}")
    pipeline = joblib.load(model_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return TrainingResult(pipeline=pipeline, metadata=metadata)
