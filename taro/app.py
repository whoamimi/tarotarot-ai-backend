"""
    app.py
"""

import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import Body, FastAPI, BackgroundTasks

from src.client import setup_client
from src.schemas import StatsRequest, TarotInsights, TarotReading, User
from src.model_chain import CombinationAnalyst, NumerologyAnalyst, StoryTell
from utils.woodpecker import DBConnectionError, StartUpCrash, setup_logger

load_dotenv()
logger = setup_logger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", None)
SUPABASE_KEY = os.getenv("SUPABASE_KEY", None)

DEBUG_MODE = os.getenv("DEBUG_MODE", False)
DB_USERS = "users"
DB_SESSION = "session"
DB_MODEL_DUMP = "raw_model_data"

logger.info("Environment labels loaded")

### Helper functions
@asynccontextmanager
async def startup(app: FastAPI):
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise DBConnectionError

        if not hasattr(app.state, "agent"):
            app.state.db_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            client = setup_client()
            logger.info("App state initialized; Ollama client ready: %s", bool(client))
        yield
        #if app.state:
        #    app.state.__dict__.pop("agent", None)
        #    logger.info('Removed Agents state.')
    except Exception as e:
        logger.exception("Startup failure")
        raise StartUpCrash(e)
    finally:
        if app.state:
            app.state.__dict__.pop("agent", None)
            logger.debug('Removed Agents state.')

app = FastAPI(
    title="Taro's API",
    lifespan=startup,
    description=(
        """FastAPI Server Endpoints + Ollama to serve Tarot reading / fortune telling LLM. """
    ),
    version="1.0.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

@app.get('/')
def root():
    return JSONResponse(content=f"Taro Active. Debug mode: {DEBUG_MODE}", status_code=200)

@app.post(
    '/user_astrology/',
    response_class=JSONResponse,
    response_model_exclude_none=True,
    response_model=User,  # if you want automatic output validation
)
async def user_astrology(
    user: User = Body(
        ...,
        example={
            "id": "12345",
            "username": "whoamimi",
            "first_name": "john",
            "last_name": "snow",
            "birth_date": "20-02-1994",
            "birth_time": "03:15",
            "birth_place": "Australia/Sydney",
            "gender": "male"
        }
    )
):
    # Redact PII; log minimal metadata
    logger.info('User astrology requested (user_id=%s)', user.id)
    user.get_astrology()
    return JSONResponse(content=user.model_dump(), status_code=200)

@app.post(
    '/insight_combination/',
    response_class=JSONResponse,
    response_model_exclude_none=True,
)
async def tarot_insight_combination(
    background_tasks: BackgroundTasks,
    inputs: TarotReading = Body(
        ...,
        example={
            "timestamp": "2025-06-22T02:30:00",
            "question": "What does my reading reveal about my life path?",
            "reading_mode": {"position": "present", "draw_num": 3},
            "drawn_cards": [
                "Ace of Cups",
                "Three of Wands",
                "Ten of Swords"
            ]
        }
    )
):
    try:
        comb = CombinationAnalyst()
        response = comb.run(inputs=inputs)
        return JSONResponse(content=response, status_code=200)
    except Exception:
        logger.exception("Error in combination insight")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post(
    '/insight_numerology/',
    response_class=JSONResponse,
    response_model_exclude_none=True,
)
async def tarot_insight_numerology(
    inputs: TarotReading = Body(
        ...,
        example={
            "timestamp": "2025-06-22T02:30:00",
            "question": "What does my reading reveal about my life path?",
            "reading_mode": {"position": "present", "draw_num": 3},
            "drawn_cards": [
                "Ace of Cups",
                "Three of Wands",
                "Ten of Swords"
            ]
        }
    )
):
    try:
        num = NumerologyAnalyst()
        response = num.run(inputs=inputs)
        return JSONResponse(content=response, status_code=200)
    except Exception:
        logger.exception("Error in numerology insight")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post(
    "/story_tell/",
    response_class=JSONResponse,
    response_model_exclude_none=True
)
async def tarot_story_tell(
    inputs: StatsRequest = Body(
        ...,
        example={
            'user': {
                'id': '12345',
                'username': 'julie.lenova',
                'first_name': 'Julie',
                'last_name': 'Lenova',
                'birth_date': '21-03-1999'
            },
            'tarot': {
                'timestamp': "2025-06-22T02:30:00",
                'question': 'When will I see Pookie?',
                'reading_mode': 'three_card',
                'drawn_cards': ['two of cups', 'wheel of fortune', 'Death']
            }
        }
    )
):
    try:
        story = StoryTell()
        response = story.run(inputs=inputs)
        return JSONResponse(content=response, status_code=200)
    except Exception:
        logger.exception("Error while summarising prediction")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post(
    "/insight_stats/",
    response_class=JSONResponse,
    response_model_exclude_none=True,
    response_model=TarotInsights,  # if you want automatic output validation
)
async def tarot_insight_stats(
    inputs: StatsRequest = Body(
        ...,
        example={
            "reading_mode": "three_card",
            "drawn_cards": ["ace of wands", " nine of cups ", "two of swords"]
        }
    )
):
    logger.info("Tarot insights requested for mode=%s", inputs.reading_mode)
    insights = TarotInsights.insight(inputs.reading_mode.drawn_num, inputs.drawn_cards) # type: ignore
    return JSONResponse(content=insights.model_dump(), status_code=200)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",              # module:app_instance
        host="0.0.0.0",       
        port=8005,
        reload=True,            # auto-reload on file change (dev only)
        log_level="debug",      # very verbose logs (dev only)
    )