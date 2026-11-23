"""FastAPI application factory; the lifespan loads the model once at startup.

Run:  uv run uvicorn netcore_tac.api.main:app
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from netcore_tac.api.predictor import Predictor
from netcore_tac.api.problems import register_exception_handlers, use_problem_media_type
from netcore_tac.api.rate_limit import RateLimiter, RateLimitMiddleware
from netcore_tac.api.request_id import RequestIdMiddleware
from netcore_tac.api.routes import router
from netcore_tac.api.settings import Settings, load_settings
from netcore_tac.model import get_package_version, load_model

logger = logging.getLogger("netcore_tac.api")

PROBE_PATHS = ("/health", "/ready")
OPENAPI_TAGS = [
    {"name": "predictions", "description": "Resolution-time (ETA) predictions"},
    {"name": "operations", "description": "Liveness and readiness probes"},
]


def configure_logging(level: str) -> None:
    """Log netcore_tac messages to stderr at ``level``."""
    package_logger = logging.getLogger("netcore_tac")
    if not package_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        package_logger.addHandler(handler)
        package_logger.propagate = False
    package_logger.setLevel("DEBUG" if level == "trace" else level.upper())


def build_description(metadata: dict[str, Any] | None) -> str:
    """OpenAPI description: what the model does, its inputs and its test MAE."""
    text = (
        "Predicts how many hours a NetCore TAC ticket will take to resolve, at triage time, "
        "replacing the fixed per-severity ETA (S1 4 h, S2 24 h, S3 48 h, S4 72 h).\n\n"
        "**Model:** scikit-learn Gamma GLM (TweedieRegressor, log link) with median / "
        "most-frequent imputation, scaling and one-hot encoding. Predictions are always "
        "positive and never below the minimum ETA for the severity; numeric inputs outside "
        "the training range are clamped and reported in `adjusted_inputs`.\n\n"
        "**Inputs:** product family, severity, customer tier, region, channel, devices "
        "affected, software age, prior tickets (90 days), engineer experience, first-response "
        "time and created time (weekend flag).\n\n"
    )
    if metadata:
        model, base = metadata["metrics"]["model"], metadata["metrics"]["baseline"]
        text += (f"**Test MAE:** {model['mae']:.1f} h (baseline {base['mae']:.1f} h), "
                 f"RMSE {model['rmse']:.1f} h, R² {model['r2']:.2f}; "
                 f"model version {metadata.get('model_version')}.")
    else:
        text += "**Model:** not loaded."
    return text


def try_load_predictor(settings: Settings) -> Predictor | None:
    """Load the model; on failure log it and return None (the app stays not-ready)."""
    try:
        result = load_model(settings.model_path, settings.model_metadata_path)
    except FileNotFoundError as exc:
        logger.warning("%s - run: uv run python scripts/train_model.py", exc)
        return None
    except Exception:
        logger.exception("Could not load the model from %s", settings.model_path)
        return None
    logger.info("Loaded model version %s", result.metadata.get("model_version"))
    return Predictor.from_training_result(result)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app from ``settings`` (default: environment / .env)."""
    settings = settings or load_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.predictor = try_load_predictor(settings)
        yield
        app.state.predictor = None

    docs = settings.docs_enabled
    app = FastAPI(
        title=settings.app_name,
        version=get_package_version(),
        description=build_description(None),
        openapi_tags=OPENAPI_TAGS,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.predictor = None
    app.include_router(router)
    register_exception_handlers(app)

    limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds,
                          settings.rate_limit_block_seconds)
    app.state.rate_limiter = limiter
    app.add_middleware(RateLimitMiddleware, limiter=limiter, exempt_paths=PROBE_PATHS,
                       trust_proxy_headers=settings.trust_proxy_headers)
    app.add_middleware(RequestIdMiddleware)   # added last = outermost: every response gets an ID

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            predictor = app.state.predictor
            schema = get_openapi(
                title=app.title, version=app.version, routes=app.routes, tags=OPENAPI_TAGS,
                description=build_description(predictor.metadata if predictor else None),
            )
            app.openapi_schema = use_problem_media_type(schema)
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_app()
