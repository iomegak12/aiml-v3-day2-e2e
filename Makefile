# NetCore TAC ETA API — common tasks.  Run `make` or `make help` to list targets.
# Recipes avoid shell-specific syntax so they work under cmd.exe, PowerShell and Git Bash.

-include .env                          # picks up PORT if you changed it in .env

PORT        ?= 8000
API_URL     ?= http://127.0.0.1:$(PORT)
MODEL       := models/eta_model.joblib
SAMPLE      := data/sample_prediction_request.json
COMPOSE     := docker compose

.DEFAULT_GOAL := help
.PHONY: help train test lock build start stop status logs predict

help:  ## List targets
	$(info Usage: make <target>   [PORT=8000])
	$(info )
	$(info   build     Build the Docker image; trains the model first if it is missing)
	$(info   start     Start the eta-api container and wait until it is healthy)
	$(info   stop      Stop and remove the container)
	$(info   predict   Send $(SAMPLE) to $(API_URL)/api/v1/predictions)
	$(info   status    Show container status and health)
	$(info   logs      Follow the container logs - Ctrl+C to quit)
	$(info   train     Retrain the model - models/eta_model.joblib + .json)
	$(info   test      Run the unit tests - uv run pytest)
	$(info   lock      Refresh requirements.lock for Docker after dependency changes)
	@exit 0

# Trains only when the model file is missing
$(MODEL):
	uv run python scripts/train_model.py

train:
	uv run python scripts/train_model.py

test:
	uv run pytest

lock:
	uv export --frozen --no-default-groups --no-emit-project -o requirements.lock

build: $(MODEL)
	$(COMPOSE) build

start: $(MODEL)
	$(COMPOSE) up -d --wait

stop:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f eta-api

predict:
	curl -sS --fail-with-body -X POST "$(API_URL)/api/v1/predictions" -H "Content-Type: application/json" -d @$(SAMPLE) -w "\n"
