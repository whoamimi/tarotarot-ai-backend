PYTHON ?= python3
PIP ?= pip

.PHONY: install test lint run up down

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Run tests locally without Docker
# Make sure SUPABASE_* envs are set or mocked if tests require them

test:
	pytest -q

# Optional lints (add tools if desired)
lint:
	@echo "No linters configured. Add ruff/flake8 if needed."

# Run FastAPI locally (without Docker)
run:
	uvicorn taro.app:app --host 0.0.0.0 --port $${PORT:-8005} --reload

# Docker helpers
up:
	docker compose -p tarohub up --build -d

down:
	echo "[!] Stopping services..." && docker compose -p tarohub down
