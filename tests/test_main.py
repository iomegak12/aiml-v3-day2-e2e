"""Unit tests for netcore_tac.api.main (app factory, lifespan, OpenAPI; no server)."""

import asyncio

import pytest
from fastapi.middleware.cors import CORSMiddleware

from netcore_tac.api.main import build_description, create_app
from netcore_tac.api.problems import PROBLEM_MEDIA_TYPE
from netcore_tac.api.settings import Settings
from netcore_tac.model import save_model


def make_settings(tmp_path, **changes) -> Settings:
    return Settings(_env_file=None, model_path=tmp_path / "eta.joblib",
                    model_metadata_path=tmp_path / "eta.json", **changes)


def run_lifespan(app):
    """Enter the lifespan, return what it loaded, then shut down."""
    async def go():
        async with app.router.lifespan_context(app):
            return app.state.predictor
    return asyncio.run(go())


def test_missing_model_app_starts_but_not_ready(tmp_path):
    app = create_app(make_settings(tmp_path))
    assert run_lifespan(app) is None


def test_model_loaded_at_startup(tmp_path, trained):
    settings = make_settings(tmp_path)
    save_model(trained, settings.model_path, settings.model_metadata_path)
    predictor = run_lifespan(create_app(settings))
    assert predictor is not None
    assert predictor.model_version == trained.metadata["model_version"]


def test_corrupt_model_stays_not_ready(tmp_path):
    settings = make_settings(tmp_path)
    settings.model_path.write_text("not a model")
    settings.model_metadata_path.write_text("{}")
    assert run_lifespan(create_app(settings)) is None


def test_docs_enabled_by_default(tmp_path):
    app = create_app(make_settings(tmp_path))
    assert (app.docs_url, app.redoc_url, app.openapi_url) == ("/docs", "/redoc", "/openapi.json")


def test_docs_disabled(tmp_path):
    app = create_app(make_settings(tmp_path, docs_enabled=False))
    assert (app.docs_url, app.redoc_url, app.openapi_url) == (None, None, None)
    paths = {getattr(r, "path", None) for r in app.routes}
    assert not paths & {"/docs", "/redoc", "/openapi.json"}


def test_no_cors_middleware(tmp_path):
    app = create_app(make_settings(tmp_path))
    assert all(m.cls is not CORSMiddleware for m in app.user_middleware)


def test_openapi_metadata_tags_and_problem_responses(tmp_path):
    app = create_app(make_settings(tmp_path, app_name="Test API"))
    schema = app.openapi()
    assert schema["info"]["title"] == "Test API"
    assert [t["name"] for t in schema["tags"]] == ["predictions", "operations"]
    post = schema["paths"]["/api/v1/predictions"]["post"]
    assert post["summary"] and post["description"]
    assert "examples" in post["requestBody"]["content"]["application/json"]
    for status in ("422", "429", "503", "500"):
        assert list(post["responses"][status]["content"]) == [PROBLEM_MEDIA_TYPE]
    assert "503" in schema["paths"]["/ready"]["get"]["responses"]


@pytest.mark.parametrize("metadata,expected", [
    (None, "not loaded"),
    ({"model_version": "0.3.0", "metrics": {"model": {"mae": 18.47, "rmse": 25.04, "r2": 0.1985},
                                            "baseline": {"mae": 20.46}}}, "18.5 h"),
])
def test_build_description(metadata, expected):
    assert expected in build_description(metadata)
