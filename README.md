# Taro: Tarot & Fortune Telling LLM Backend

FastAPI Server Endpoints + Ollama integration to serve Tarot reading, astrology insights, numerology, and storytelling with a Large Language Model (LLM). This project handles both AI/ML workflows, Database Creation and API endpoints.

## Features

- Tarot reading insights (combinations, numerology, storytelling) - insights selected based on real-life tarot readers.
- Astrology charting (sun, moon, rising signs, houses, planets, etc.)
- Numerology analysis
- Tarot stats & spread summaries relative to the user's life journey and current spread.
- REST API with OpenAPI/Swagger (/docs) and ReDoc (/redoc)

## Directory Overview

Root Directory path:
- `docker-compose.yml` — App + Ollama stack definition
- `on_start.sh` / `on_stop.sh` — Start/stop helper scripts
- `requirements.txt` — Python dependencies
- `ollama_root/` — Ollama runner (`start_ollama.sh`) and mounts over ollama container volume - where all chat logs are stored.
- `taro/` — App source code

App's sub-directory paths `taro/`:
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

# Example of API Endpoints

1. Quick summary of user's astrology: POST /user_astrology/
Generate astrological insights for a given user.
Example Input:
```json
{
  "id": "12345",
  "username": "whoamimi",
  "first_name": "john",
  "last_name": "snow",
  "birth_date": "20-02-1994",
  "birth_time": "03:15",
  "birth_place": "Australia/Sydney",
  "gender": "male"
}
```
Example Output: 
```json
{
  "sun_sign": "UNKNOWN",
  "moon_sign": "UNKNOWN",
  "rising_sign": "UNKNOWN",
  "house_placements": {},
  "elemental_distribution": {},
  "modality_distribution": {},
  "dominant_planets": {},
  "id": "12345",
  "username": "whoamimi",
  "first_name": "john",
  "last_name": "snow",
  "birth_date": "20-02-1994",
  "birth_time": "03:15",
  "birth_place": "Australia/Sydney",
  "gender": "male"
}
```

2. Tarot Reading Prediction: POST /story_tell/
Returns a narrative/storytelling interpretation of the reading.
Example Input:
```json
{
  "user": {
    "id": "12345",
    "username": "julie.lenova",
    "first_name": "Julie",
    "last_name": "Lenova",
    "birth_date": "21-03-1999"
  },
  "tarot": {
    "timestamp": "2025-06-22T02:30:00",
    "question": "When will I see Pookie?",
    "reading_mode": "three_card",
    "drawn_cards": [
      "two of cups",
      "wheel of fortune",
      "Death"
    ]
  }
}
```
Example Output:
```json
{
  "detail": [
    {
      "msg": "Pookie is dead. Move on.",
      "type": "string"
    }
  ]
}
```
3. Tarot Insight Stats: POST /insight_stats/
Returns statistical summaries of a Tarot spread reading. 
Schema:
	•	num_cards (int)
	•	king_count, queen_count, knight_count, page_count (court counts)
	•	wand_count, coin_count, sword_count, cup_count (suit counts)
	•	total_courts (int)
Example Input:
```json
{
  "reading_mode": "three_card",
  "drawn_cards": [
    "ace of wands",
    " nine of cups ",
    "two of swords"
  ]
}
```
Example Output: 
```json
{
  "num_cards": 0,
  "king_count": 0,
  "queen_count": 0,
  "knight_count": 0,
  "page_count": 0,
  "total_courts": 0,
  "wand_count": 0,
  "coin_count": 0,
  "sword_count": 0,
  "cup_count": 0
}
```

# AI/ML/LLM Life Cycle

- The Tarot reading insights and statistcal insights are used to fine-tune Llama 3.1 every 2 months of collected datasets.
- The cloud server supporting the LLM is Ollama and Hugging Face.  

Note: The tarot reading insights were simplified for the sake of the mobile app's simplicity.

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