# src/schemas/tarot.py
from typing import List
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_serializer, ConfigDict

from utils.handler import ReadingMode
from utils.woodpecker import InvalidTarotInsightsCalculation, MismatchedDrawnCards

DEFAULT_DATETIME_FORMAT = "%d-%m-%Y %H:%M"

class StatsRequest(BaseModel):
    reading_mode: ReadingMode
    drawn_cards: List[str]

    @model_validator(mode="after")
    def ensure_non_empty(cls, model):
        if not model.drawn_cards:
            raise ValueError("drawn_cards must have at least one card")
        return model


class DecodeMeter(BaseModel):
    num_keep: int = 5
    seed: int = 42
    num_predict: int = 300
    temperature: float = 0.8
    top_k: int = 50
    top_p: float = 0.9
    repeat_last_n: int = 33
    repeat_penalty: float = 1.1
    presence_penalty: float = 1.5
    frequency_penalty: float = 0.5
    num_ctx: int = 2048


class TarotInsights(BaseModel):
    """
    Tarot Spread general insights.
    Used to input LLMs or return JSON response data (after mapping to the appropriate information).
    """
    num_cards: int  # total cards drawn
    # Courts Ratio of drawn spread
    king_count: int = 0
    queen_count: int = 0
    knight_count: int = 0
    page_count: int = 0
    total_courts: int = 0
    # Elements Ratio of drawn spread
    wand_count: int = 0
    coin_count: int = 0
    sword_count: int = 0
    cup_count: int = 0

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    @model_validator(mode='after')
    def validate_statistics(self):
        self.total_courts = self.king_count + self.queen_count + self.knight_count + self.page_count
        if self.total_courts > self.num_cards:
            raise InvalidTarotInsightsCalculation(self.num_cards, 'Court', self.total_courts)
        return self

    def get_stats(self):
        if self.num_cards == 0:
            raise ZeroDivisionError("Cannot compute stats with zero cards.")
        return {
            'card_count': self.num_cards,
            'king': self.king_count / self.num_cards,
            'queen': self.queen_count / self.num_cards,
            'knight': self.knight_count / self.num_cards,
            'pages': self.page_count / self.num_cards,
            'court_prob': self.total_courts / self.num_cards,
            'wand': self.wand_count / self.num_cards,
            'coin': self.coin_count / self.num_cards,
            'sword': self.sword_count / self.num_cards,
            'cup': self.cup_count / self.num_cards,
        }

    @property
    def stats(self) -> dict[str, float]:
        return self.get_stats()

    def model_dump(self, *args, **kwargs) -> dict:
        base = super().model_dump(*args, **kwargs)
        base["stats"] = self.get_stats()
        return base

    @staticmethod
    def insight(num_cards: int, drawn_cards: List[str]):
        element = ('wand', 'sword', 'coin', 'cup')
        court = ('king', 'queen', 'page', 'knight')

        insight = TarotInsights(num_cards=num_cards)

        for input_card in drawn_cards:
            card = input_card.strip().lower()
            for el, co in zip(element, court):
                if el in card:
                    setattr(insight, f"{el}_count", getattr(insight, f"{el}_count") + 1)
                if co in card:
                    setattr(insight, f"{co}_count", getattr(insight, f"{co}_count") + 1)

        insight.total_courts = insight.king_count + insight.knight_count + insight.queen_count + insight.page_count
        return insight


class TarotPrediction(BaseModel):
    combination: str | None = None
    numerology: str | None = None
    story_tell: str | None = None


class TarotReading(BaseModel):
    timestamp: str = Field(default=datetime.now().isoformat())
    question: str
    reading_mode: ReadingMode
    drawn_cards: list

    def get_tarot_insights(self):
        return TarotInsights.insight(self.reading_mode.drawn_num, self.drawn_cards)  # type: ignore

    @model_validator(mode='after')
    def validate_user_input(self):
        if len(self.drawn_cards) != self.reading_mode.drawn_num:
            raise MismatchedDrawnCards(self.reading_mode.drawn_num, len(self.drawn_cards), self.reading_mode.drawn_num)
        return self

    @property
    def pos_draw(self) -> str:
        return "\n".join(
            f"{pos}:\t{card}" for pos, card in zip(self.reading_mode.position, self.drawn_cards)
        )


def save_session(
    reading: TarotReading,
    insights: TarotInsights,
    prediction: TarotPrediction,
    id: str = uuid4().hex,
    _id: str = uuid4().hex
):
    """End-of-session dict schema ready for DB insertion."""
    session = dict(
        reading=reading.model_dump(),
        insights=insights.model_dump(),
        prediction=prediction.model_dump(),
        id=id,
        _id=_id
    )
    # implement DB write logic where appropriate
    return session