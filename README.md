# Taro Tarot AI ML/AI Hub

Taro's development FastAPI + Ollama hub.

---

## Directory Overview

Top-level files:
- `docker-compose.yml` — App + Ollama stack definition
- `on_start.sh` / `on_stop.sh` — Start/stop helper scripts
- `requirements.txt` — Python dependencies
- `ollama_root/` — Ollama runner (`start_ollama.sh`)
- `taro/` — App source code

Important subpaths under `taro/`:
- `app.py` — FastAPI app (uvicorn entrypoint)
- `src/client.py` — Ollama client setup
- `src/model_chain.py` — Model pipeline and chat calls
- `src/schemas.py` — Pydantic models
- `utils/` — Logger and helpers (`woodpecker.py`, `handler.py`)
- `templates/` — Prompts and constants
- `tests/` — Pytests

---

## Running the Stack

There are **two ways** to start and stop the stack:

### 1. Run directly with Docker Compose
Run with docker-compose file:
```bash
docker compose -p tarohub up --build -d
```
Closing the session:

### 2. Alternatively, can run with the bash scripts:

```
# Start services (build + run in detached mode)
./on_start.sh

# Stop services (clean shutdown)
./on_stop.sh
```

# Data Processing Agents Notes

- The following are labels for the data processing tasks that utilizes the same prompt chain used in this project. 
- These tools are built as light-weight wrappers around databases like Supabase, Google BigQuery etc. to perform data cleaning / quality checks / EDA / Fine-tuning preparations. 


| **Category**                 | **Description**                                                                                  | **Example Questions**                                  |
|-------------------------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **Love & Relationships**      | Romantic interests, soulmates, breakups, dating.                                                | *"Will I meet someone soon?"*                         |
| **Career & Ambitions**        | Career moves, promotions, purpose.                                                              | *"Should I change jobs?"*                             |
| **Finance & Wealth**          | Money, savings, financial struggles.                                                            | *"Will I be financially stable?"*                     |
| **Health & Wellness**         | Physical, mental, and emotional well-being.                                                     | *"How can I improve my health?"*                      |
| **Family & Home**             | Family dynamics, children, and living situation.                                                | *"Will my home life become more peaceful?"*           |
| **Personal Growth**           | Healing, self-discovery, learning, emotional development.                                       | *"How can I grow emotionally?"*                       |
| **Friendships & Social Life** | Social circles, trust, and belonging.                                                           | *"Why do I feel so isolated from others?"*            |
| **Spirituality & Purpose**    | Soul path, meaning, karmic lessons, existential questions.                                      | *"What am I meant to learn in this lifetime?"*        |
| **Decisions & Dilemmas**      | Hard choices, forks in the road, evaluating options.                                            | *"Should I move or stay?"*                            |
| **Timing & Future**           | Questions about when events will occur or improve.                                              | *"When will things improve for me?"*                  |
| **Creativity & Expression**   | Creative projects, artistry, and self-expression.                                               | *"Will my art reach others?"*                         |