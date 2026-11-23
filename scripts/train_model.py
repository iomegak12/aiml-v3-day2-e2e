"""Train the resolution-time model and save it with its metadata.

Usage:
    uv run python scripts/train_model.py
    uv run python scripts/train_model.py --data data/netcore_tickets.csv --output-dir models/
"""

import argparse
from pathlib import Path

import pandas as pd

from netcore_tac.cleaning import clean_tickets
from netcore_tac.model import TrainingResult, save_model, train_model

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "netcore_tickets.csv"
DEFAULT_OUTPUT_DIR = ROOT / "models"
MODEL_FILE = "eta_model.joblib"
METADATA_FILE = "eta_model.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse ``--data`` and ``--output-dir``."""
    parser = argparse.ArgumentParser(description="Train the NetCore TAC ETA model.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA,
                        help="input CSV (default: data/netcore_tickets.csv)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="folder for the model and metadata (default: models/)")
    return parser.parse_args(argv)


def format_summary(result: TrainingResult, raw_rows: int) -> str:
    """One short, human-readable training summary."""
    rows, metrics = result.metadata["rows"], result.metadata["metrics"]
    base, model = metrics["baseline"], metrics["model"]
    return (f"Tickets: {raw_rows:,} raw -> {rows['total']:,} clean | "
            f"train {rows['train']:,} | test {rows['test']:,}\n"
            f"Baseline MAE {base['mae']:.1f} h | Model MAE {model['mae']:.1f} h, "
            f"RMSE {model['rmse']:.1f} h, R² {model['r2']:.2f}")


def main(argv: list[str] | None = None) -> TrainingResult:
    """Load -> clean -> train/evaluate -> save; print a short summary."""
    args = parse_args(argv)
    raw_df = pd.read_csv(args.data, parse_dates=["created_at"])
    result = train_model(clean_tickets(raw_df))

    model_path = args.output_dir / MODEL_FILE
    metadata_path = args.output_dir / METADATA_FILE
    save_model(result, model_path, metadata_path)
    print(format_summary(result, len(raw_df)))
    print(f"Saved {model_path} and {metadata_path}")
    return result


if __name__ == "__main__":
    main()
