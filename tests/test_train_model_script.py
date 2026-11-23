"""Unit tests for scripts/train_model.py."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "train_model.py"


@pytest.fixture(scope="module")
def train_script():
    spec = importlib.util.spec_from_file_location("train_model", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_defaults(train_script):
    args = train_script.parse_args([])
    assert args.data.name == "netcore_tickets.csv" and args.data.parent.name == "data"
    assert args.output_dir.name == "models"


def test_main_writes_model_and_metadata(train_script, small_raw_df, tmp_path, capsys):
    csv = tmp_path / "tickets.csv"
    small_raw_df.to_csv(csv, index=False)
    out_dir = tmp_path / "models"

    result = train_script.main(["--data", str(csv), "--output-dir", str(out_dir)])

    assert (out_dir / "eta_model.joblib").is_file()
    meta = json.loads((out_dir / "eta_model.json").read_text(encoding="utf-8"))
    assert meta["rows"] == result.metadata["rows"]
    printed = capsys.readouterr().out
    assert "Baseline MAE" in printed and "Model MAE" in printed
