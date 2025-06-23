"""
utils/woodpecker.py
"""

import logging
import traceback
from typing import Callable

def setup_logger(name: str = __name__) -> logging.Logger:
    """ sets the custom logger. """
    base_logger = logging.getLogger("uvicorn.error")
    logger = logging.getLogger(name)
    logger.setLevel(base_logger.level)

    if base_logger.handlers:
        for handler in base_logger.handlers:
            logger.addHandler(handler)

    #logger.propagate = True  # allow upward logging

    return logger

class WoodPecker(Exception):
    def __init__(self, message: str, status_code: int = 400): # type: ignore
        self.message = message
        self.status_code = status_code
        super().__init__(message)

# UNEXPECTED
class UncapturedError(WoodPecker):
    """ For unknown error / exceptions that could be raised from app deployment. """
    def __init__(self, error: Exception | str, func: Callable):
        func_name = getattr(func, "__name__", str(func))
        trace = traceback.format_exc()
        message = (
            f"⚠️ An unexpected error occurred in `{func_name}`.\n"
            f"🔍 Error Type: {type(error).__name__}\n"
            f"📝 Message: {error}\n"
            f"📄 Traceback:\n{trace}"
        )

        super().__init__(message, status_code=500)  # 🔴 500 Internal Server Error

# INVALID USER REQUESTS
class InvalidModelInputs(WoodPecker):
    def __init__(self, action, **user_input):
        super().__init__(message=(
            f"Insufficient inputs provided for action '{action}'. "
            f"Expected more complete data, but got: {user_input}"
        ), status_code=422)  # 🟠 422 Unprocessable Entity

class InvalidTarotMode(WoodPecker):
    def __init__(self, reading_mode: str):
        super().__init__(message=f"❌ Mode '{reading_mode}' is unavailable. Please try again.", status_code=404)  # 🟡 404 Not Found

class InvalidTarotAction(WoodPecker):
    def __init__(self, action_id: str):
        super().__init__(message=f"❌ Received user's requested action from Taro, however the action, {action_id} is unavailable at the moment. Please try again with another action ID or come back later ^^", status_code=404)  # 🟡 404 Not Found

# TAROT READING ERRORS
class MismatchedDrawnCards(WoodPecker):
    def __init__(self, reading_mode: str, num_drawn: int, num_cards: int):
        super().__init__(
            message=f"❌ Expected {num_cards} to be drawn but received {num_drawn} cards by user for reading mode: {reading_mode}",
            status_code=404
        )  # 🟡 404 Not Found

# INACTIVITY ERRORS
class InactiveTaro(WoodPecker):
    def __init__(self):
        super().__init__(
            message="❌ Taro's state is missing or failed to initialize. Please restart container.",
            status_code=503  # 🔵 503 Service Unavailable
        )
class ErrorSettingUpModelChain(WoodPecker):
    def __init__(self, action):
        super().__init__(
            message=f"❌ Action failing to load into Model Chains due to input type error for initialising the subclasses: {action}",
            status_code=503  # 🔵 503 Service Unavailable
        )

# SYSTEM ERRORS
class StartUpCrash(WoodPecker):
    """ Error failed at setting up app's state and check ups. """
    def __init__(self, error: Exception):
        message = f"❌ Failed to start application with error returned:\n\t{error}"
        super().__init__(message=message, status_code=500)  # Internal Server Error

class BadOllamaSetup(WoodPecker):
    def __init__(self):
        super().__init__('Ollama client connected but expected bartwoski\'s model pulled. Please Restart container or check backend :(', status_code=500)

class DataModelException(WoodPecker):
    def __init__(self, error):
        super().__init__(f'Unexpected Error Captured within Data Schema Models:\n\t{error}', status_code=500)

class DataValidatorException(WoodPecker):
    def __init__(self, error):
        super().__init__(f'Error Captured while parsing data in Data Schema Models:\n\t{error}', status_code=500)

class DBConnectionError(WoodPecker):
    def __init__(self):
        super().__init__('Unable to proceed in setting up FastAPI due to Supabase DB connection error. Either the SUPABASE_URL or SUPABASE_KEY could not be loaded...')

class LoadedProfileError(WoodPecker):
    def __init__(self, loaded_template):
        super().__init__(f'Unable to proceed in loading agent\'s profile. Expected agent\'s actions in `templates` to be loaded as dict but received: {type(loaded_template)}')

class UnavailableAction(WoodPecker):
    def __init__(self, action_label):
        super().__init__(f'Unable to locate Taro\'s action, {action_label}.', status_code=500)

class InvalidTarotInsightsCalculation(WoodPecker):
    def __init__(self, expected_count: int, insight_type: str, count: int):
        message = (
            f"Invalid tarot insight calculation for '{insight_type}'. "
            f"Num cards provided: {count} which doesn't match with the total drawn cards: {expected_count}. This may indicate a misconfigured or logically impossible card count."
        )
        super().__init__(message, status_code=422)