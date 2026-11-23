"""Unit tests for netcore_tac.api.routes (route functions called directly)."""

from types import SimpleNamespace

import pytest

from netcore_tac.api.predictor import Predictor
from netcore_tac.api.problems import ModelNotReadyError
from netcore_tac.api.routes import create_prediction, get_predictor, health, ready, router
from netcore_tac.api.schemas import TICKET_EXAMPLE, TicketIn


def fake_request(predictor=None, request_id="rid-1"):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(predictor=predictor)),
                           state=SimpleNamespace(request_id=request_id))


@pytest.fixture(scope="module")
def predictor(trained) -> Predictor:
    return Predictor.from_training_result(trained)


def test_health_never_needs_model():
    assert health().status == "ok"


def test_ready_with_model(predictor):
    out = ready(fake_request(predictor))
    assert out.status == "ready"
    assert out.model_version == predictor.model_version
    assert out.trained_at == predictor.trained_at


def test_ready_and_predictor_without_model_raise():
    with pytest.raises(ModelNotReadyError):
        ready(fake_request(None))
    with pytest.raises(ModelNotReadyError):
        get_predictor(fake_request(None))


def test_create_prediction_returns_request_id(predictor):
    out = create_prediction(fake_request(predictor), TicketIn(**TICKET_EXAMPLE), predictor)
    assert out.request_id == "rid-1"
    assert out.model_version == predictor.model_version
    assert out.predicted_hours >= 0


def test_routes_registered_with_tags():
    routes = {(r.path, tuple(sorted(r.methods))): r.tags for r in router.routes}
    assert routes[("/api/v1/predictions", ("POST",))] == ["predictions"]
    assert routes[("/health", ("GET",))] == ["operations"]
    assert routes[("/ready", ("GET",))] == ["operations"]
