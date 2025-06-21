"""
    app.py
"""

import os
from typing import Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, BackgroundTasks

from src.data_models import TarotInsights, User
from src.schemas import TaroPostRequest, TaroRequest, TaroResponse, UserFeedback, StatsRequest
from src.agent_state import TaroState
from src.helper import DisplayName, IncommingDate, IncommingTimestamp
from utils.woodpecker import DBConnectionError, InactiveTaro, StartUpCrash, InvalidTarotMode, setup_logger

load_dotenv()
logger = setup_logger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", None)
SUPABASE_KEY = os.getenv("SUPABASE_KEY", None)
DEBUG_MODE = os.getenv("DEBUG_MODE", False)

logger.info("Complete loading environment labels")

### Helper functions
@asynccontextmanager
async def startup(app: FastAPI):
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise DBConnectionError
        if not hasattr(app.state, "agent"):
            app.state.agent = TaroState(SUPABASE_URL, SUPABASE_KEY)
            logger.info(f"Setting up apps state: {app.state.__dict__}")
        yield
        #if app.state:
        #    app.state.__dict__.pop("agent", None)
        #    logger.info('Removed Agents state.')
    except Exception as e:
        logger.error(f"🚨 {type(e).__name__} during startup: {e}", exc_info=True)
        raise StartUpCrash(e)
    finally:
        if app.state:
            app.state.__dict__.pop("agent", None)
            logger.info('Removed Agents state.')

app = FastAPI(
    title="Taro's API",
    lifespan=startup,
    description=(
        """Taro's ML/AI dockers container to serve main all of Taro's functionality e.g. Tarot reading, data workflows and ML/AI invokes."""
    ),
    version="1.0.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

async def render_user_input(
    inputs: TaroRequest
):
    """ Entry point for users inputs for invoking Taro's actions or prompts. """
    # Checks if state has been loaded
    if not app.state.agent:
        logger.error(f"{type(InactiveTaro).__name__}: {InactiveTaro().message}", exc_info=True)
        raise InactiveTaro

    # Checks if the Tarot reading mode requested is available.
    if mode := app.state.agent.modes.get(inputs.reading_mode, None):
        logger.info(f"User input request for reading mode: {mode}")
        return TaroPostRequest(
            question=inputs.question,
            cards=inputs.cards,
            **mode.dict()
        )

    logger.error(f"{type(InvalidTarotMode).__name__}: {InvalidTarotMode(inputs.reading_mode)}", exc_info=True)
    raise InvalidTarotMode(inputs.reading_mode)

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
    user: User
):
    logger.info(f'User posted: \n{user.first_name}\nInfo:\n{user.birth_date}\n{user.birth_time}\n{user.birth_place}')
    user.get_astrology()
    return JSONResponse(content=user.model_dump(), status_code=200)

@app.post('/insight_combination/')
async def tarot_insight_combination(
    timestamp: str,
    reading_mode: str,
    question: str,
    drawn_cards: list[str]
):
    return JSONResponse(content="This is currently trialing and in Beta Mode. Try again later :)", status_code=200)


@app.post('/insight_numerology/')
async def tarot_insight_numerology(
    timestamp: str,
    reading_mode: str,
    question: str,
    drawn_cards: list[str]
):
    return JSONResponse(content="This is currently trialing and in Beta Mode. Try again later :)", status_code=200)


@app.post(
    "/insight_stats/",
    response_class=JSONResponse,
    response_model_exclude_none=True,
    response_model=TarotInsights,  # if you want automatic output validation
)
async def tarot_insight_stats(
    req: StatsRequest = Body(
        ...,
        example={
            "reading_mode": " Celtic Cross ",
            "drawn_cards": ["ace of wands", " nine of cups ", "two of swords"]
        }
    )
):
    n = len(req.drawn_cards)
    insights = TarotInsights.insight(n, req.drawn_cards)
    return JSONResponse(content=insights.model_dump(), status_code=200)

@app.post('/insight_history/')
async def tarot_insight_history(
    timestamp: str | None,
    reading_mode: str | None,
    question: str | None,
    drawn_cards: list[str] | None
):
    return JSONResponse(content="This is currently trialing and in Beta Mode. Try again later :)", status_code=200)

@app.post('/prediction/')
async def tarot_reading(
    background_tasks: BackgroundTasks,
    user: UserProfile,
    inputs: TaroPostRequest = Depends(render_user_input),
    feedback: Optional[UserFeedback] = None
):

    logger.info(f"Taros Prediction Function received: {inputs}")

    try:
        user_input = {
            "question": inputs.question,
            "tarot_draw_input": inputs.pos_draw
        }

        messages = app.state.agent.action("pred_combination", **user_input)

        logger.info(f"Inserted Messages: {messages}")

        if feedback and any([
            feedback.more_creative,
            feedback.upvote,
            feedback.downvote,
            feedback.favorite
        ]):
            last_decoder_states = app.state.agent.get_last_decoder_states_with_update(feedback, user.username, user.first_name, user.last_name)
        else:
            last_decoder_states = app.state.agent.get_last_decoder_states(user.username, user.first_name, user.last_name)

        response = send_prompt(app.state.agent.client, messages, last_decoder_states)

        output = TaroResponse(
            feedback=feedback,
            response=response,
            inputs=inputs
        ) # type: ignore

        background_tasks.add_task(app.state.agent.add_session, output)

        return JSONResponse(content=response.model_dump(mode="json"), status_code=200)

    except Exception as e:
        return JSONResponse(content=str(e.__traceback__), status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "taro.app:app",              # module:app_instance
        host="127.0.0.1",       # only accessible locally
        port=8005,
        reload=True,            # auto-reload on file change (dev only)
        log_level="trace",      # very verbose logs (dev only)
    )