"""
utils/handler.py


Data processors to augment and transform certain fields of the dataset before / after storing and retrieval.

BeforeValidator – Preprocessing input values: Use this when you want to clean or coerce the input before Pydantic validates or parses it.
AfterValidator – Post-processing or fixing values: when you want to modify or validate a value after its been parsed
"""


from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated

from geopy.geocoders import Nominatim
from pydantic.functional_validators import BeforeValidator
import yaml

from utils.woodpecker import (
    InvalidModelInputs,
    InvalidTarotMode,
    LoadedProfileError,
    setup_logger,
)

logger = setup_logger(__name__)

ACTION_PROMPT_V1 = """{action_prompt}

Please ensure that your response align with given response format below:

### Response Format
{response_format}

### Example User Input
{example_input}
### Example Response
{example_output}
"""

ACTION_PROMPT_V2 = """{action_prompt}

Please ensure that your response align with given response format below:

### Example User Input
{example_input}
### Example Response
{example_output}
"""

DEFAULT_DATE_FORMAT = "%d-%m-%Y"
DEFAULT_TIME_FORMAT = "%H:%M"

# [TODO] RECREATE THE TAROT READING MODE INFO CARDS
TAROT_READING_MODE = {
    'five_card': {
        'position': ['Past', 'Present', 'Future', 'Hidden Message or Problem', 'Near Future'],
        'num': 5,
    },
    'three_card': {
        'position': ['Past', 'Present', 'Future'],
        'num': 3
    },
    'one_card': {
        'position': ['Daily Card'],
        'num': 1
    },
    'celtic_cross': {
        'position': [
            'Present Situation',
            'Challenge',
            'Past Influences',
            'Future Influences',
            'Conscious Goal',
            'Unconscious Influence',
            'Your Attitude',
            'Environment',
            'Hopes and Fears',
            'Final Outcome'
        ],
        'num': 10
    },
    'relationship': {
        'position': ['You', 'Your Partner', 'Core Issue', 'Advice', 'Outcome'],
        'num': 5
    },
    'career': {
        'position': ['Current Job', 'Strengths', 'Weaknesses', 'Advice', 'Outcome'],
        'num': 5
    },
    'chakra_alignment': {
        'position': [
            'Root Chakra',
            'Sacral Chakra',
            'Solar Plexus',
            'Heart Chakra',
            'Throat Chakra',
            'Third Eye',
            'Crown Chakra'
        ],
        'num': 7
    },
    'horseshoe': {
        'position': ['Past', 'Present', 'Hidden Influences', 'Obstacles', 'External Influences', 'Advice', 'Outcome'],
        'num': 7
    },
    'seven_day_forecast': {
        'position': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'num': 7
    },
    'new_moon_intentions': {
        'position': ['What to Release', 'What to Embrace', 'Support Available', 'Lesson to Learn', 'Outcome'],
        'num': 5
    },
    'full_moon_insight': {
        'position': ['Current State', 'What is Illuminated', 'What to Let Go', 'What to Celebrate', 'Next Step'],
        'num': 5
    }
}

ReadingModeParser = namedtuple('ReadingModeParser', ['position', 'drawn_num'])

def parse_datetime(input_date: str | datetime) -> datetime | None:
    if isinstance(input_date, str):
        return datetime.strptime(input_date, DEFAULT_DATE_FORMAT)
    elif isinstance(input_date, datetime):
        return input_date


def parse_timestamp(input_time: str | datetime) -> datetime | None:
    if isinstance(input_time, str):
        return datetime.strptime(input_time, DEFAULT_TIME_FORMAT) # type: ignore
    elif isinstance(input_time, datetime):
        return input_time

def get_lat_lon(place: str):
    """ Gets Latitude and Longitude"""
    geolocator = Nominatim(user_agent="astro-app")
    location = geolocator.geocode(place)
    if location:
        return location.latitude, location.longitude # type: ignore
    else:
        raise ValueError(f"Could not geocode location: {place}")

def fetch_reading_mode(reading_mode: str) -> ReadingModeParser:
    reading_mode = reading_mode.strip().lower()
    if mode := TAROT_READING_MODE.get(reading_mode, None):
        return ReadingModeParser(position=mode.get('position', None), drawn_num=mode.get('num', None))
    else:
        raise InvalidTarotMode(reading_mode)

IncommingDate = Annotated[
    datetime | str,
    BeforeValidator(parse_datetime)
]
IncommingTimestamp = Annotated[
    datetime | str | None,
    BeforeValidator(parse_timestamp)
]
DisplayName = Annotated[
    str | None,
    BeforeValidator(lambda x: x.strip().title() if isinstance(x, str) else None)
]
ReadingMode = Annotated[
    ReadingModeParser,
    BeforeValidator(fetch_reading_mode)
]

@dataclass(slots=True)
class TaroAction:
    label: str
    prompt: str | None
    example: dict
    input_template: str
    response_format: str | None = None

    @property
    def system_prompt(self):
        """ Returns prompt for this Action in System prompt WITHOUT users input """
        if self.response_format:
            return ACTION_PROMPT_V1.format(
                action_prompt=self.prompt,
                response_format=self.response_format,
                example_input=self.example.get('user_input', None),
                example_output=self.example.get('response', None)
            )
        return ACTION_PROMPT_V2.format(
                action_prompt=self.prompt,
                example_input=self.example.get('user_input', None),
                example_output=self.example.get('response', None)
            )

    def prepare_prompt(self, **kwargs):
        """
        Returns System Message with users inputs in chat formatted message to invoke LLM. Defaults to Llama 3.1 models' chatting template.
        """
        if user_input := self.input_template.format(**kwargs) if self.input_template else None:
            yield {"role": "system", "content": self.system_prompt}
            yield {"role": "user", "content": user_input}
        else:
            logger.error(f"User posted too many args for this action. User's input: {kwargs}")
            raise InvalidModelInputs(kwargs)

@dataclass(slots=True)
class TaroProfile:
    name: str
    role: list[str]
    templates: dict[str, TaroAction] | dict[str, str]

    def __post_init__(self):
        """ Post-init transformations to the data. """
        if not isinstance(self.templates, dict):
            raise LoadedProfileError(self.templates)

        temp = self.templates
        self.templates = {
            key: TaroAction(
                label=key,
                prompt=val.get("prompt"),
                example=val.get("example"), # type: ignore
                response_format=val.get("response_format", None),
                input_template=val.get("input_template", None) # type: ignore
            )

            for key, val in temp.items()
            if isinstance(val, dict) and "prompt" in val and "example" in val
        }

    @staticmethod
    def load_agent():
        """ Loads agents config profile. """

        root_path = Path('.').resolve()
        profile_path = root_path / 'templates' / 'agent.yaml'

        if not profile_path.exists():
            raise FileNotFoundError(f"Taro profile YAML not found: {profile_path}")

        try:
            with open(profile_path, 'r') as file:
                data = yaml.safe_load(file)
                return TaroProfile(**data)

        except Exception as e:
            logger.error(e, exc_info=True)
            raise
