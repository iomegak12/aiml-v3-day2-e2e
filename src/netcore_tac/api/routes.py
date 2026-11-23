"""HTTP routes: prediction, liveness and readiness."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from netcore_tac.api.predictor import Predictor
from netcore_tac.api.problems import (
    ModelNotReadyError,
    get_request_id,
    problem_responses,
)
from netcore_tac.api.schemas import TICKET_EXAMPLE, HealthOut, PredictionOut, ReadyOut, TicketIn

router = APIRouter()

TICKET_EXAMPLES = {
    "s2_router_ticket": {
        "summary": "S2 router ticket (Gold, EMEA, phone)",
        "description": "A realistic Severity 2 ticket at triage time.",
        "value": TICKET_EXAMPLE,
    }
}


def get_predictor(request: Request) -> Predictor:
    """The loaded Predictor; raises ModelNotReadyError (503) when there is none."""
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise ModelNotReadyError()
    return predictor


@router.post(
    "/api/v1/predictions",
    tags=["predictions"],
    response_model=PredictionOut,
    summary="Predict resolution hours for one ticket",
    description=(
        "Returns the predicted hours to resolve a ticket, using only fields known at "
        "triage. Replaces the fixed per-severity ETA (S1 4 h, S2 24 h, S3 48 h, S4 72 h). "
        "Unknown product families are accepted; null experience or first-response "
        "times are filled with training medians."
    ),
    responses=problem_responses(422, 429, 503, 500),
)
def create_prediction(
    request: Request,
    ticket: Annotated[TicketIn, Body(openapi_examples=TICKET_EXAMPLES)],
    predictor: Annotated[Predictor, Depends(get_predictor)],
) -> PredictionOut:
    return PredictionOut(predicted_hours=predictor.predict(ticket),
                         model_version=predictor.model_version,
                         request_id=get_request_id(request) or "")


@router.get(
    "/health",
    tags=["operations"],
    response_model=HealthOut,
    summary="Liveness probe",
    description="200 while the process is running. Never touches the model; not rate limited.",
    responses=problem_responses(500),
)
def health() -> HealthOut:
    return HealthOut(status="ok")


@router.get(
    "/ready",
    tags=["operations"],
    response_model=ReadyOut,
    summary="Readiness probe",
    description="200 once the model and its metadata are loaded, otherwise 503. Not rate limited.",
    responses=problem_responses(503, 500),
)
def ready(request: Request) -> ReadyOut:
    predictor = get_predictor(request)
    return ReadyOut(status="ready", model_version=predictor.model_version,
                    trained_at=predictor.trained_at)
