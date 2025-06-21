"""
src/schemas.py

Contains data models for GET/POST requests of FastAPI events and between data source routings.

"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, field_validator, model_validator, Field

from utils.woodpecker import MismatchedDrawnCards, setup_logger

logger = setup_logger(__name__)

DEFAULT_DATETIME_FORMAT = "%d-%m-%Y %H:%M"

# Dataclasses for API / Endpoints handling
class TaroRequest(BaseModel):
    reading_mode: str
    question: str
    cards: list[str]
    timestamp: str = Field(default=datetime.now().strftime(DEFAULT_DATETIME_FORMAT))

class TaroPostRequest(TaroRequest):
    position: list[str]
    num: int

    @model_validator(mode='after')
    def validate_user_input(self):
        if len(self.cards) != self.num:
            raise MismatchedDrawnCards(self.reading_mode, len(self.cards), self.num)
        return self

    @property
    def pos_draw(self) -> str:
        return "\n".join(
            f"{pos}:\t{card}" for pos, card in zip(self.position, self.cards)
        )

class UserFeedback(BaseModel):
    more_creative: bool = False
    less_creative: bool = False
    upvote: bool = False
    downvote: bool = False
    favorite: bool = False

class TaroResponse(TaroPostRequest):
    feedback: UserFeedback
    response: object
    inputs: TaroPostRequest


class StatsRequest(BaseModel):
    reading_mode: str
    drawn_cards: List[str]

    @field_validator("reading_mode", mode="before")
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator("reading_mode", mode="after")
    def lowercase(cls, v: str) -> str:
        return v.lower()

    @field_validator("drawn_cards", mode="before")
    def normalize_cards(cls, v: List[str]) -> List[str]:
        # strip & title-case each entry
        return [card.strip().title() for card in v]

    @model_validator(mode="after")
    def ensure_non_empty(cls, model):
        if not model.drawn_cards:
            # FastAPI will translate this into a 422 response
            raise ValueError("drawn_cards must have at least one card")
        return model
