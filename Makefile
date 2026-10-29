# Shortcuts: type `make <name>`.  Run `make help` to list them.
COMPOSE = docker compose -f docker/docker-compose.yml
VENV    = .venv

.PHONY: help setup lint test build up down demo-fail demo-fail-clean

help: ## Show this list
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ -/'

setup: ## Create the Python venv and install every dependency (Python + npm)
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements.txt -r requirements-dev.txt
	cd mobile && npm ci --no-audit --no-fund
	cd token-server && npm ci --no-audit --no-fund

lint: ## Check the Python code style with flake8
	$(VENV)/bin/flake8 .

test: ## Run pytest (with coverage) and the npm tests
	$(VENV)/bin/pytest --cov --cov-report=term
	cd token-server && npm test
	cd mobile && npm run test:ci

build: ## Build the Docker image
	docker build -t datastrap:local .

up: ## Start Jenkins + SonarQube (first run builds the Jenkins image: a few minutes)
	@test -f docker/.env || (cp docker/.env.example docker/.env && echo "Created docker/.env - change the password if you like")
	$(COMPOSE) up -d --build
	@echo "Jenkins:   http://localhost:8090"
	@echo "SonarQube: http://localhost:9000  (first login admin / admin)"

down: ## Stop Jenkins + SonarQube and the deployed app (data is kept in Docker volumes)
	-docker rm -f datastrap-staging datastrap-prod
	$(COMPOSE) down

demo-fail: ## Push a branch with a deliberately failing test, to show the pipeline stopping
	@git diff --quiet && git diff --cached --quiet || (echo "Commit or stash your changes first." && exit 1)
	git checkout -b demo-fail
	printf 'def test_deliberate_failure():\n    """Made by `make demo-fail`: this MUST fail so the pipeline stops before deploy."""\n    assert 1 + 1 == 3\n' > tests/test_demo_fail.py
	git add tests/test_demo_fail.py
	git commit -m "demo: add a deliberately failing test"
	git push -u origin demo-fail
	git checkout main
	@echo "Pushed branch demo-fail. Watch Jenkins: Test stage turns red and nothing is deployed."

demo-fail-clean: ## Remove the demo-fail branch locally and on GitHub
	-git checkout main
	-git branch -D demo-fail
	-git push origin --delete demo-fail
