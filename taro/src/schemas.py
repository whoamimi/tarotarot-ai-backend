"""
src/data_models.py

Defines the data models structure currently in place in my datastore.

"""

from typing import List
from uuid import uuid4
from datetime import datetime, time
from pydantic import BaseModel, field_serializer, field_validator, model_validator, Field, ConfigDict

from immanuel import charts
from zoneinfo import ZoneInfo
from immanuel.const import chart
from utils.handler import IncommingDate, IncommingTimestamp, DisplayName, ReadingMode, get_lat_lon
from utils.woodpecker import InvalidTarotInsightsCalculation, MismatchedDrawnCards

DEFAULT_DATETIME_FORMAT = "%d-%m-%Y %H:%M"

class StatsRequest(BaseModel):
    reading_mode: ReadingMode
    drawn_cards: List[str]

    @model_validator(mode="after")
    def ensure_non_empty(cls, model):
        if not model.drawn_cards:
            # FastAPI will translate this into a 422 response
            raise ValueError("drawn_cards must have at least one card")

        return model

class UserInsights(BaseModel):
    """ Astrology & Natal House Placements of the user. """
    sun_sign: str = 'UNKNOWN'
    moon_sign: str = 'UNKNOWN'
    rising_sign: str = 'UNKNOWN'
    house_placements: dict[str, str | None] | str = {}
    elemental_distribution: dict[str, int] = {}
    modality_distribution: dict[str, int] = {}
    dominant_planets: dict[str, int] = {}

    @field_validator('sun_sign', 'moon_sign', 'rising_sign', mode='before')
    @classmethod
    def normalize_sign(cls, v):
        return v.strip().title()

class User(UserInsights):
    """ Gets users astrology & Natal house placements. """
    id: str
    username: str
    first_name: DisplayName
    last_name: DisplayName
    birth_date: IncommingDate  # 1994-12-21
    birth_time: IncommingTimestamp = None # 03:15:00+11:00
    birth_place: str | None = 'Australia/Sydney'
    gender: str | None = 'UNKNOWN'
    model_config = ConfigDict(
        json_encoders={ datetime: lambda dt: dt.isoformat() }
    )

    @field_serializer('birth_date', mode='plain')
    def _ser_birth_date(self, v: datetime, _info) -> str:
        # e.g. 1998-07-27
        return v.strftime('%Y-%m-%d')

    @field_serializer('birth_time', mode='plain')
    def _ser_birth_time(self, v: datetime | None, _info) -> str | None:
        if not v:
            return None
        # e.g. 03:15:00+11:00
        # ensure it’s timezone‐aware before this, or .isoformat()
        return v.isoformat()

    @model_validator(mode='after')
    def validate_user_profile(self):
        if not self.birth_date or not self.birth_place:
            raise ValueError(f"Expected 'birth_date' to always be non-null but received ambigous inputs: {self.birth_date}")
        if isinstance(self.birth_date, str):
            raise ValueError(f"Processing birth date failed. Expected datetime formatted attribute for `self.birth_date` after processing but received: {self.birth_date} with data type: {type(self.birth_date)} ")

        # If birth_time was provided and is already a datetime, extract its time.
        if self.birth_time and isinstance(self.birth_time, datetime):
            # attach the correct tzinfo to the incoming datetime
            tz = ZoneInfo(self.birth_place)
            bt = self.birth_time.replace(tzinfo=tz).time()
        else:
            # no birth_time → default to midnight (or whatever makes sense)
            tz = ZoneInfo(self.birth_place)
            bt = time(0, 0)

        # Now we can safely combine date + time into dt
        dt = datetime.combine(self.birth_date, bt).replace(tzinfo=tz)

        # Overwrite both fields so they're fully tz-aware datetimes
        self.birth_time = dt
        self.birth_date = dt

        # Finally, kick off your astrology logic
        self.get_astrology()
        return self

    @property
    def birth(self):
        if isinstance(self.birth_time, datetime):
            timestamp = self.birth_date.time()# type: ignore
        else:
            timestamp = datetime.now().time()

        return datetime.combine(self.birth_date.date(), timestamp).replace(tzinfo=ZoneInfo(self.birth_place)) # type: ignore

    #BETA MODE
    def get_astrology(self):
        """ Astrology & Natal house associations with the user's birth date. """
        # Combine date and time with timezone
        dt = self.birth
        birth_place = self.birth_place if self.birth_place is not None else "Australia/Sydney"

        latitude, longitude = get_lat_lon(place=birth_place)
        native = charts.Subject(date_time=dt, latitude=latitude, longitude=longitude)
        natal = charts.Natal(native)

        self.sun_sign = natal.objects[chart.SUN].sign.name
        self.moon_sign = natal.objects[chart.MOON].sign.name
        self.rising_sign = natal.objects[chart.ASC].sign.name
        self.house_placements = {
            f"{i}th House": natal.houses.get(str(i)).sign.name
            if natal.houses.get(str(i)) and getattr(natal.houses.get(str(i)), "sign", None) is not None
            else None
            for i in range(1, 13)
        }

        elements = {}
        modalities = {}
        dominant_planets = {}

        for obj in natal.objects.values():
            if obj.type.name == 'Planet':
                # sign = obj.sign['name']
                element = obj.sign.element
                modality = obj.sign.modality
                planet = obj.name

                elements[element] = elements.get(element, 0) + 1
                modalities[modality] = modalities.get(modality, 0) + 1
                dominant_planets[planet] = dominant_planets.get(planet, 0) + 1

        self.elemental_distribution = elements
        self.modality_distribution = modalities
        self.dominant_planets = dominant_planets

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
    num_cards: int # total cards drawn
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

    # Astrology
    @model_validator(mode='after')
    def validate_statistics(self):
        """ Validates the users' inputs. """
        self.total_courts = self.king_count + self.queen_count + self.knight_count + self.page_count

        if self.total_courts > self.num_cards:
            raise InvalidTarotInsightsCalculation(self.num_cards, 'Court', self.total_courts)

        return self

    def get_stats(self):
        """ Fetch probas for the tarot spread readings. """
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
        """Expose stats as a model field for dumping."""
        return self.get_stats()

    def model_dump(self, *args, **kwargs) -> dict:
        """Override to include stats in the dumped output."""
        base = super().model_dump(*args, **kwargs)
        base["stats"] = self.get_stats()
        return base

    @staticmethod
    def insight(num_cards: int, drawn_cards: list[str]):
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
    """ Beta mode. Still in progress. """
    combination: str | None = None
    numerology: str | None = None
    story_tell: str | None = None

class TarotReading(BaseModel):
    """ User Inputs in the current reading session. """
    timestamp: str = Field(default=datetime.now().isoformat())
    question: str
    reading_mode: ReadingMode
    drawn_cards: list

    def get_tarot_insights(self):
        """ Returns drawn cards' insights. """
        return TarotInsights.insight(self.reading_mode.drawn_num, self.drawn_cards) # type: ignore

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
    id: str = uuid4().hex, # duplicated so that I dont ever have to look back at this app and worry about the duplicated data etc.
    _id: str = uuid4().hex
):
    """ End of session Data Model Schema to store in the database for the tarot reading session. """

    session = dict(
        reading=reading.model_dump(),
        insights=insights.model_dump(),
        prediction=prediction.model_dump(),
        id=id,
        _id=_id
    )

    # connect to db client
    # store in db
    # logger.info success else error
    return session

if __name__ == "__main__":
    insights = User(
        id=uuid4().hex,
        username='whoamimi',
        first_name='mimi',
        last_name='phan',
        birth_date='1994-12-21',
        birth_time='03:15',
        birth_place='Australia/Sydney'
    )
