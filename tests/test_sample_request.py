"""Unit test: data/sample_prediction_request.json (used by `make predict`) is a valid ticket."""

import json
from pathlib import Path

from netcore_tac.api.schemas import TICKET_EXAMPLE, TicketIn

SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_prediction_request.json"


def test_sample_request_is_valid_ticket():
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    TicketIn(**payload)   # raises ValidationError if the file drifts from the schema


def test_sample_request_matches_openapi_example():
    assert json.loads(SAMPLE.read_text(encoding="utf-8")) == TICKET_EXAMPLE
