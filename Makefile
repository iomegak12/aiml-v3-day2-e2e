# NetCore TAC ETA (API + web UI) — common tasks.  Run `make` or `make help` to list targets.
# Recipes avoid shell-specific syntax so they work under cmd.exe, PowerShell and Git Bash.

-include .env                          # picks up WEB_PORT if you changed it in .env

WEB_PORT    ?= 80
WEB_URL     ?= http://127.0.0.1:$(WEB_PORT)
MODEL       := models/eta_model.joblib
SAMPLE      := data/sample_prediction_request.json
COMPOSE     := docker compose

.DEFAULT_GOAL := help
.PHONY: help train test test-web lock build build-api build-web start stop status logs predict

help:  ## List targets
	$(info Usage: make <target>   [WEB_PORT=80])
	$(info )
	$(info   build       Build both images - API and web; trains the model first if it is missing)
	$(info   build-api   Build only the API image)
	$(info   build-web   Build only the web - NGINX - image)
	$(info   start       Start API + web and wait until both are healthy - UI on $(WEB_URL))
	$(info   stop        Stop and remove the containers)
	$(info   status      Show container status and health)
	$(info   logs        Follow the logs of both services - Ctrl+C to quit)
	$(info   predict     Send $(SAMPLE) to $(WEB_URL)/api/v1/predictions through NGINX)
	$(info   train       Retrain the model - models/eta_model.joblib + .json)
	$(info   test        Run the Python unit tests - uv run pytest)
	$(info   test-web    Run the JavaScript unit tests - node --test)
	$(info   lock        Refresh requirements.lock for Docker after dependency changes)
	@exit 0

# Trains only when the model file is missing
$(MODEL):
	uv run python scripts/train_model.py

train:
	uv run python scripts/train_model.py

test:
	uv run pytest

test-web:
	node --test "tests/web/*.test.mjs"

lock:
	uv export --frozen --no-default-groups --no-emit-project -o requirements.lock

build: $(MODEL)
	$(COMPOSE) build

build-api: $(MODEL)
	$(COMPOSE) build eta-api

build-web:
	$(COMPOSE) build web

start: $(MODEL)
	$(COMPOSE) up -d --wait

stop:
	$(COMPOSE) down

status:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

predict:
	curl -sS --fail-with-body -X POST "$(WEB_URL)/api/v1/predictions" -H "Content-Type: application/json" -d @$(SAMPLE) -w "\n"
