"""Unit tests for netcore_tac.dataset.build_dataset and the CLI script."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from netcore_tac import config
from netcore_tac.dataset import build_dataset

N = 2000


@pytest.fixture(scope="module")
def dataset() -> pd.DataFrame:
    return build_dataset(n=N, seed=42)


def test_row_count_includes_duplicates(dataset):
    assert len(dataset) == N
    assert dataset["ticket_id"].is_unique


def test_same_seed_identical_output(dataset):
    pd.testing.assert_frame_equal(dataset, build_dataset(n=N, seed=42))


def test_different_seed_different_output(dataset):
    assert not dataset.equals(build_dataset(n=N, seed=7))


def test_expected_columns(dataset):
    assert "sla_breached" in dataset.columns
    assert all(c == c.lower() and " " not in c for c in dataset.columns)


def test_all_issues_present(dataset):
    assert (dataset["resolution_hours"] >= 1500).sum() >= round(0.01 * (N - 40))
    assert (dataset["first_response_minutes"] < 0).sum() >= config.NEGATIVE_RESPONSE_COUNT
    assert dataset["engineer_experience_years"].isna().mean() == pytest.approx(0.05, abs=0.01)
    assert dataset["first_response_minutes"].isna().mean() == pytest.approx(0.05, abs=0.01)
    assert dataset["severity"].isna().mean() == pytest.approx(0.01, abs=0.005)
    sev = dataset["severity"].dropna()
    assert (~sev.isin(config.SEVERITIES)).mean() == pytest.approx(0.03, abs=0.01)
    assert (~dataset["region"].isin(config.REGIONS)).mean() == pytest.approx(0.03, abs=0.01)


def test_outliers_are_breached(dataset):
    assert dataset.loc[dataset["resolution_hours"] >= 1500, "sla_breached"].all()


def load_script():
    path = Path(__file__).resolve().parent.parent / "scripts" / "generate_tickets.py"
    spec = importlib.util.spec_from_file_location("generate_tickets", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_defaults():
    args = load_script().parse_args([])
    assert args.n == 2000
    assert args.seed == 42
    assert args.output.parts[-2:] == ("data", "netcore_tickets.csv")


def test_script_writes_csv(tmp_path):
    output = tmp_path / "out" / "tickets.csv"
    load_script().main(["--n", "300", "--seed", "1", "--output", str(output)])
    written = pd.read_csv(output)
    assert len(written) == 300
