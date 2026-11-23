"""RFC 9457 problem details: builders, exception handlers and OpenAPI helpers."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from netcore_tac.api.request_id import REQUEST_ID_HEADER
from netcore_tac.api.schemas import ProblemDetails

logger = logging.getLogger("netcore_tac.api")

PROBLEM_MEDIA_TYPE = "application/problem+json"
PROBLEM_BASE_URI = "https://netcore.example/problems/"

VALIDATION_ERROR = PROBLEM_BASE_URI + "validation-error"
RATE_LIMITED = PROBLEM_BASE_URI + "rate-limited"
MODEL_NOT_READY = PROBLEM_BASE_URI + "model-not-ready"
INTERNAL_ERROR = PROBLEM_BASE_URI + "internal-error"


class ModelNotReadyError(Exception):
    """The model is not loaded, so predictions cannot be served."""


def problem_body(status: int, title: str, detail: str, instance: str,
                 request_id: str | None = None, type_: str = "about:blank",
                 **extensions: Any) -> dict[str, Any]:
    """RFC 9457 members plus extensions (``request_id`` and any keyword given)."""
    body = {"type": type_, "title": title, "status": status, "detail": detail,
            "instance": instance, "request_id": request_id}
    body.update(extensions)
    return body


def problem_response(body: dict[str, Any], headers: dict[str, str] | None = None) -> JSONResponse:
    """JSONResponse with the application/problem+json media type."""
    return JSONResponse(body, status_code=body["status"], media_type=PROBLEM_MEDIA_TYPE,
                        headers=headers)


def validation_problem(errors: list[dict[str, str]], instance: str,
                       request_id: str | None = None) -> dict[str, Any]:
    """422 body with an ``errors`` list of ``{field, message}``."""
    return problem_body(422, "Request validation failed",
                        f"{len(errors)} field(s) failed validation.", instance, request_id,
                        VALIDATION_ERROR, errors=errors)


def rate_limited_problem(retry_after: int, instance: str,
                         request_id: str | None = None) -> dict[str, Any]:
    """429 body; send it with a ``Retry-After`` header."""
    return problem_body(429, "Too many requests",
                        f"Rate limit exceeded. Retry after {retry_after} seconds.",
                        instance, request_id, RATE_LIMITED)


def model_not_ready_problem(instance: str, request_id: str | None = None) -> dict[str, Any]:
    """503 body when the model is not loaded."""
    return problem_body(503, "Model not ready",
                        "The prediction model is not loaded. Try again later.",
                        instance, request_id, MODEL_NOT_READY)


def internal_error_problem(instance: str, request_id: str | None = None) -> dict[str, Any]:
    """500 body with a generic detail (no internals)."""
    return problem_body(500, "Internal server error",
                        "An unexpected error occurred. Quote the request_id when reporting it.",
                        instance, request_id, INTERNAL_ERROR)


def http_problem(status: int, instance: str, request_id: str | None = None) -> dict[str, Any]:
    """Generic ``about:blank`` body for HTTP errors such as 404 and 405."""
    phrase = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else "Error"
    return problem_body(status, phrase, f"{phrase}.", instance, request_id)


def format_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Pydantic errors -> ``[{field, message}]`` (dotted path, without the "body" prefix)."""
    formatted = []
    for error in errors:
        if error.get("type") == "json_invalid":   # loc holds a character position, not a field
            loc = []
        else:
            loc = [str(part) for part in error.get("loc", ()) if part != "body"]
        formatted.append({"field": ".".join(loc) or "body", "message": error.get("msg", "")})
    return formatted


def get_request_id(request: Request) -> str | None:
    """Request ID set by RequestIdMiddleware, if any."""
    return getattr(request.state, "request_id", None)


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = validation_problem(format_validation_errors(exc.errors()), request.url.path,
                              get_request_id(request))
    return problem_response(body)


async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    body = http_problem(exc.status_code, request.url.path, get_request_id(request))
    return problem_response(body, headers=getattr(exc, "headers", None))


async def _model_not_ready_handler(request: Request, exc: ModelNotReadyError) -> JSONResponse:
    return problem_response(model_not_ready_problem(request.url.path, get_request_id(request)))


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    logger.error("Unhandled error request_id=%s path=%s", request_id, request.url.path,
                 exc_info=exc)
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return problem_response(internal_error_problem(request.url.path, request_id), headers)


def register_exception_handlers(app: FastAPI) -> None:
    """Route every error through an RFC 9457 problem response."""
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_handler)
    app.add_exception_handler(ModelNotReadyError, _model_not_ready_handler)
    app.add_exception_handler(Exception, _unhandled_handler)


_EXAMPLES = {
    422: validation_problem([{"field": "severity",
                              "message": "Input should be 'S1', 'S2', 'S3' or 'S4'"}],
                            "/api/v1/predictions", "3f2b8c1e-6f1d-4c55-9a43-2f0c1f8f6b7a"),
    429: rate_limited_problem(30, "/api/v1/predictions", "3f2b8c1e-6f1d-4c55-9a43-2f0c1f8f6b7a"),
    503: model_not_ready_problem("/api/v1/predictions", "3f2b8c1e-6f1d-4c55-9a43-2f0c1f8f6b7a"),
    500: internal_error_problem("/api/v1/predictions", "3f2b8c1e-6f1d-4c55-9a43-2f0c1f8f6b7a"),
}
_DESCRIPTIONS = {
    422: "Validation error (problem details with an `errors` list)",
    429: "Rate limit exceeded; see the `Retry-After` header",
    503: "Model not loaded",
    500: "Unexpected server error (no internals exposed)",
}


def problem_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI ``responses`` entries for the given error statuses."""
    responses: dict[int | str, dict[str, Any]] = {}
    for status in statuses:
        entry: dict[str, Any] = {
            "model": ProblemDetails,
            "description": _DESCRIPTIONS[status],
            "content": {PROBLEM_MEDIA_TYPE: {"example": _EXAMPLES[status]}},
        }
        if status == 429:
            entry["headers"] = {"Retry-After": {"description": "Seconds until the block ends",
                                                "schema": {"type": "integer"}}}
        responses[status] = entry
    return responses


def use_problem_media_type(openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """Move 4xx/5xx response schemas from application/json to application/problem+json.

    FastAPI places a response ``model`` under application/json; errors are
    actually sent as application/problem+json.
    """
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            for status, response in operation.get("responses", {}).items():
                content = response.get("content", {})
                if not str(status).startswith(("4", "5")) or "application/json" not in content:
                    continue
                json_entry = content.pop("application/json")
                problem_entry = content.setdefault(PROBLEM_MEDIA_TYPE, {})
                problem_entry.setdefault("schema", json_entry.get("schema",
                    {"$ref": "#/components/schemas/ProblemDetails"}))
    return openapi_schema
