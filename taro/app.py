"""
    app.py
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks

from taro.src.llm_model import send_prompt
from taro.src.schemas import TaroPostRequest, TaroRequest, TaroState, TaroResponse, NewUser, UserFeedback, User

load_dotenv()

logger = logging.getLogger('uvicorn.error')
SUPABASE_URL = os.getenv("SUPABASE_URL", None)
SUPABASE_KEY = os.getenv("SUPABASE_KEY", None)

### Helper functions
@asynccontextmanager
async def startup(app: FastAPI):
    try:
        if not hasattr(app.state, "agent"):
            app.state.agent = TaroState(SUPABASE_URL, SUPABASE_KEY)
            logger.info(f"Setting up apps state: {app.state.__dict__}")
        yield
        if app.state:
            app.state.__dict__.pop("agent", None)
            logger.info('Removed Agents state.')
    except Exception as e:
        if not isinstance(e, FileNotFoundError):
            logger.error(f"Unexpected error raised during startup: {e}")
        raise e

async def render_user_input(inputs: TaroRequest):
    """ Render users inputs. """
    if mode := app.state.agent.modes.get(inputs.reading_mode, None):
        print(mode)
        return TaroPostRequest(
            question=inputs.question,
            cards=inputs.cards,
            **mode.dict()
        )

    raise HTTPException(status_code=404, detail=f"Mode '{inputs.reading_mode}' not found.")

app = FastAPI(lifespan=startup)

### Endpoints
@app.get('/')
def root():
    return JSONResponse(content=f"Taro Active. Debug mode: {SUPABASE_URL}", status_code=200)

@app.post('/register_new_user/')
async def register_user(
    user: NewUser
):
    try:
        app.state.agent.add_user(user)
        return JSONResponse(
            content=f"Successfully added user {user.first_name}!",
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content=str(e),
            status_code=500
        )

@app.post('/prediction/')
async def tarot_reading(
    background_tasks: BackgroundTasks,
    user: User,
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
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True, log_level="trace")