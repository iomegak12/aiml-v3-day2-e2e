"""Unit tests for netcore_tac.api.problems."""

import json

from netcore_tac.api.problems import (
    MODEL_NOT_READY,
    PROBLEM_MEDIA_TYPE,
    RATE_LIMITED,
    VALIDATION_ERROR,
    format_validation_errors,
    http_problem,
    internal_error_problem,
    model_not_ready_problem,
    problem_body,
    problem_response,
    problem_responses,
    rate_limited_problem,
    use_problem_media_type,
    validation_problem,
)

RFC_MEMBERS = {"type", "title", "status", "detail", "instance"}


def test_problem_body_has_rfc_9457_members_and_extensions():
    body = problem_body(418, "Teapot", "Short and stout.", "/pot", "rid-1", extra="x")
    assert RFC_MEMBERS <= body.keys()
    assert body["type"] == "about:blank" and body["request_id"] == "rid-1" and body["extra"] == "x"


def test_problem_response_media_type_and_status():
    response = problem_response(model_not_ready_problem("/ready", "rid"), headers={"X-A": "1"})
    assert response.status_code == 503
    assert response.media_type == PROBLEM_MEDIA_TYPE
    assert response.headers["content-type"].startswith(PROBLEM_MEDIA_TYPE)
    assert response.headers["x-a"] == "1"
    assert json.loads(response.body)["instance"] == "/ready"


def test_validation_problem_lists_errors():
    errors = [{"field": "severity", "message": "bad"}]
    body = validation_problem(errors, "/api/v1/predictions", "rid")
    assert body["status"] == 422 and body["type"] == VALIDATION_ERROR and body["errors"] == errors


def test_specific_builders():
    assert rate_limited_problem(30, "/x")["status"] == 429
    assert rate_limited_problem(30, "/x")["type"] == RATE_LIMITED
    assert "30" in rate_limited_problem(30, "/x")["detail"]
    assert model_not_ready_problem("/x")["type"] == MODEL_NOT_READY
    assert internal_error_problem("/x")["status"] == 500


def test_internal_error_detail_is_generic():
    detail = internal_error_problem("/x")["detail"]
    assert "Traceback" not in detail and "\\" not in detail and "/" not in detail


def test_http_problem_uses_status_phrase():
    body = http_problem(404, "/nope")
    assert body["title"] == "Not Found" and body["type"] == "about:blank"
    assert http_problem(405, "/x")["title"] == "Method Not Allowed"


def test_format_validation_errors():
    raw = [{"loc": ("body", "severity"), "msg": "bad enum", "type": "enum"},
           {"loc": ("body", "items", 0), "msg": "bad", "type": "x"},
           {"loc": ("body", 1), "msg": "JSON decode error", "type": "json_invalid"}]
    assert format_validation_errors(raw) == [
        {"field": "severity", "message": "bad enum"},
        {"field": "items.0", "message": "bad"},
        {"field": "body", "message": "JSON decode error"},
    ]


def test_problem_responses_entries():
    responses = problem_responses(422, 429)
    assert set(responses) == {422, 429}
    assert PROBLEM_MEDIA_TYPE in responses[422]["content"]
    assert "Retry-After" in responses[429]["headers"]


def test_use_problem_media_type_moves_error_schemas_only():
    schema = {"paths": {"/x": {"post": {"responses": {
        "200": {"content": {"application/json": {"schema": {"a": 1}}}},
        "422": {"content": {"application/json": {"schema": {"b": 2}},
                            PROBLEM_MEDIA_TYPE: {"example": {}}}},
    }}}}}
    responses = use_problem_media_type(schema)["paths"]["/x"]["post"]["responses"]
    assert "application/json" in responses["200"]["content"]
    assert list(responses["422"]["content"]) == [PROBLEM_MEDIA_TYPE]
    assert responses["422"]["content"][PROBLEM_MEDIA_TYPE] == {"example": {}, "schema": {"b": 2}}
