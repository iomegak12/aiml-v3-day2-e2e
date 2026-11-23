"""Shared fixtures: a small trained model built from synthetic tickets."""

import pandas as pd
import pytest

from netcore_tac.cleaning import clean_tickets
from netcore_tac.dataset import build_dataset
from netcore_tac.model import TrainingResult, train_model


@pytest.fixture(scope="session")
def small_raw_df() -> pd.DataFrame:
    return build_dataset(n=400, seed=1)


@pytest.fixture(scope="session")
def small_clean_df(small_raw_df) -> pd.DataFrame:
    return clean_tickets(small_raw_df)


@pytest.fixture(scope="session")
def trained(small_clean_df) -> TrainingResult:
    return train_model(small_clean_df)
