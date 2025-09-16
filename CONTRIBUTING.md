# Contributing

## Quick start
1. Clone repo
2. Create a virtualenv and install dependencies:
   - python3 -m venv .venv && source .venv/bin/activate
   - pip install -r requirements.txt
3. Copy .env.example to .env and fill required values
4. Run tests: make test

## Running locally
- make run (uvicorn)
- make up / make down (Docker compose)

## Code style
- Keep logs parameterized and avoid PII in logs.
- Prefer small, focused PRs.
