"""Build, train, evaluate, save and load the resolution-time model.

Notebook Part 4 (linear regression) + section 17 (Gamma GLM): the served model is a
Gamma GLM with a log link, whose predictions are always positive; plain linear regression
is still trained as a reference because it can predict negative hours for short S1 tickets.
"""

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
from sklearn.linear_model import LinearRegression, TweedieRegressor
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
MODEL_TYPE = "Gamma GLM: TweedieRegressor(power=2, link='log')"
# Per-severity minimum ETA = this quantile of the training hours for that severity
FLOOR_QUANTILE = 0.01


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


def build_preprocessor() -> ColumnTransformer:
    """Unfitted preprocessing, identical to the notebook (impute, scale, one-hot)."""
    numeric_pipe = Pipeline([("fill", SimpleImputer(strategy="median")),
                             ("scale", StandardScaler())])
    category_pipe = Pipeline([("fill", SimpleImputer(strategy="most_frequent")),
                              ("encode", OneHotEncoder(handle_unknown="ignore",
                                                       sparse_output=False))])
    return ColumnTransformer([("num", numeric_pipe, NUMERIC_FEATURES),
                              ("flags", "passthrough", FLAG_FEATURES),
                              ("cat", category_pipe, CATEGORICAL_FEATURES)],
                             verbose_feature_names_out=False)


def build_linear_pipeline() -> Pipeline:
    """Reference model from the notebook: preprocessing + LinearRegression (can go negative)."""
    return Pipeline([("prep", build_preprocessor()), ("model", LinearRegression())])


def build_pipeline() -> Pipeline:
    """Served model: preprocessing + Gamma GLM with a log link (predictions always > 0).

    Effects multiply instead of add ("each year of experience cuts time by x %"), which suits
    resolution hours: short S1 tickets and long S4 tickets are scaled, never pushed below zero.
    """
    # lbfgs copes with the collinear one-hot columns (no penalty, alpha=0); Newton needs alpha > 0
    glm = TweedieRegressor(power=2, link="log", alpha=0.0, solver="lbfgs", max_iter=1000)
    return Pipeline([("prep", build_preprocessor()), ("model", glm)])


def severity_floors(X_train: pd.DataFrame, y_train: pd.Series,
                    quantile: float = FLOOR_QUANTILE) -> dict[str, float]:
    """Minimum ETA per severity: the given quantile of training hours, 1 decimal."""
    floors = y_train.groupby(X_train["severity"]).quantile(quantile)
    return {str(sev): round(float(hours), 1) for sev, hours in floors.items()}


def input_ranges(X_train: pd.DataFrame) -> dict[str, list[float | int]]:
    """[min, max] of each numeric feature in the training split (blanks ignored)."""
    ranges: dict[str, list[float | int]] = {}
    for column in NUMERIC_FEATURES:
        values = X_train[column].dropna()
        cast = int if pd.api.types.is_integer_dtype(values) else float
        ranges[column] = [cast(values.min()), cast(values.max())]
    return ranges


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

    The returned pipeline (Gamma GLM) is fitted on the training split only (no refit on
    all data). The metadata adds the reference linear-regression metrics, the per-severity
    minimum ETA and the numeric input ranges seen in training (used by the API).

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
    linear = build_linear_pipeline().fit(X_train, y_train)
    pipeline = build_pipeline().fit(X_train, y_train)

    metadata = {
        "model_version": get_package_version(),
        "model_type": MODEL_TYPE,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scikit_learn_version": sklearn.__version__,
        "rows": {"total": len(df), "train": len(X_train), "test": len(X_test)},
        "features": {"numeric": NUMERIC_FEATURES, "flags": FLAG_FEATURES,
                     "categorical": CATEGORICAL_FEATURES},
        "target": TARGET,
        "metrics": {
            "baseline": regression_metrics(y_test, baseline.predict(X_test)),
            "linear_regression": regression_metrics(y_test, linear.predict(X_test)),
            "model": regression_metrics(y_test, pipeline.predict(X_test)),
        },
        "min_hours_by_severity": severity_floors(X_train, y_train),
        "input_ranges": input_ranges(X_train),
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
