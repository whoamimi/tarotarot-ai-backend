"""
schemas.py
"""
import yaml
import logging

from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime
from dataclasses import dataclass
from fastapi import HTTPException
from supabase import create_client

from taro.src.llm_model import setup_client

logger = logging.getLogger('uvicorn.error')

# Prompts / Configs
ACTION_PROMPT = """{action_prompt}

Please ensure that your response align with given response format below:

### Response Format
{response_format}

### Example User Input
{example_input}
### Example Response
{example_output}
"""

TAROT_READING_MODE = {
    'five_cards': {
        'position': ['Past', 'Present', 'Future', 'Hidden Message', 'Near Future'],
        'num': 5,
    },
    'three_card': {
        'position': ['Past', 'Present', 'Future'],
        'num': 3
    },
    'one_card': {
        'position': ['Daily Card'],
        'num': 1
    }
}

# DB Data Managers / Classes
# Dataclasses for API / Endpoints handling
class User(BaseModel):
    username: str
    first_name: str
    last_name: str
    birth_date: datetime
    birth_time: datetime
    birth_country: str | None
    birth_state: str | None
    gender: str | None = "Unknown"

class NewUser(User):
    created: str = datetime.now().isoformat()
    user_id: str = str(uuid4())

class TaroBase(BaseModel):
    user_id: str
    reading_mode: str

class TaroRequest(TaroBase):
    question: str
    cards: list[str]
    id: str = str(uuid4())
    timestamp: str = datetime.now().isoformat()

class TaroPostRequest(TaroRequest):
    position: list[str]
    num: int

    def model_post_init(self, __context):
        if len(self.cards) != self.num:
            raise HTTPException(status_code=500, detail=f"Please draw the correct number of input cards {self.num}. Only {len(self.cards)} cards received for reading {self.reading_mode}" )

    @property
    def pos_draw(self) -> str:
        return "\n".join(
            f"{pos}:\t{card}" for pos, card in zip(self.position, self.cards)
        )

class ModelOutput(BaseModel):
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

# State Management
class TaroState:
    """ Taro State Manager Class. """

    def __init__(self, supabase_url, supabase_key):

        try:
            self.root_path = Path(__file__).resolve().parents[1]
            print(f"Loaded Root path: {self.root_path}")
            self._load_profile("templates/agent.yaml")
            self.modes = TAROT_READING_MODE
            self.client = setup_client() # Ollama set up
            self.supa = create_client(supabase_url, supabase_key)

            self.DB_DECODER_STATES = "model_decoder_states"
            self.DB_USERS = "users"
            self.DB_MAIN = "readings"

        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error initializing TaroState: {str(e)}")

    def add_session(self, inputs: TaroPostRequest, data: TaroResponse):
        payload = data.model_dump(mode="json")
        payload.update(inputs.model_dump(mode="json"))
        self.supa.table(self.DB_MAIN).insert(payload)

    def get_last_decoder_states(self, username: str, first_name: str, last_name: str):
        return (
            self.supa.table(self.DB_DECODER_STATES)
            .select("*")
            .eq("username", username)
            .eq("first_name",first_name)
            .eq("last_name", last_name)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

    def get_last_decoder_states_with_update(self, feedback: UserFeedback, username: str, first_name: str, last_name: str):
        last_decoder_states = self.get_last_decoder_states(username, first_name, last_name)

        meter = {
            'temperature': 0.5,
            'top_k': 10,
            'top_p': 0.2,
            'repeat_last_n': 2,
            'presence_penalty': 0.0000001,
            'frequency_penalty': 0.0000001
        }

        decoder_states = last_decoder_states.model_dump(mode='json')
        for d, addon in meter.items():
            d_prev = decoder_states.get(d)

            if feedback.more_creative:
                decoder_states[d] = d_prev + addon
            elif feedback.less_creative:
                decoder_states[d] = d_prev - addon

        self.supa.table(self.DB_DECODER_STATES).update(decoder_states)
        return decoder_states

    def add_user(self, user: NewUser):
        # registers new user to supabase as internal ID for data processing. Irrelevant to account id in firebase

        user_json = user.model_dump(mode="json")
        self.supa.table(self.DB_USERS).insert(user_json)

    def _load_profile(self, relative_path: str):
        """ Loads agents config profile. """

        profile_path = self.root_path / relative_path

        if not profile_path.exists():
            raise FileNotFoundError(f"Taro profile YAML not found: {profile_path}")

        try:
            with open(profile_path, 'r') as file:
                data = yaml.safe_load(file)
                self.profile = TaroProfile(**data)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML profile: {e}")

    def action(self, action_id, **kwargs):
        """ Triggers agent's task. """

        if action := self.profile.templates.get(action_id, None) if isinstance(self.profile.templates, dict) else None:
            yield from action.action_prompt(**kwargs)
        else:
            raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")


# Dataclasses Utilities to load the Taro Profile and Actions Template
@dataclass(slots=True)
class TaroAction:
    label: str
    prompt: str
    example: dict
    response_format: str | None = None
    input_template: str | None = None

    @property
    def system_prompt(self):
        """ Returns prompt for this Action / Task. """

        return ACTION_PROMPT.format(
            action_prompt=self.prompt,
            response_format=self.response_format,
            example_input=self.example.get('user_input', None),
            example_output=self.example.get('response', None)
        )

    def action_prompt(self, **kwargs):
        """Constructs final instruction prompt with user's input."""

        if user_input := self.input_template.format(**kwargs) if self.input_template else None:
            yield {"role": "system", "content": self.system_prompt}
            yield {"role": "user", "content": user_input}
        else:
            raise HTTPException(status_code=500, detail="No User input template detected. Returning chat format.")

@dataclass(slots=True)
class TaroProfile:
    name: str
    role: list[str]
    templates: list[dict] | dict[str, TaroAction]

    def __post_init__(self):
        if isinstance(self.templates, list):
            temp = self.templates
            self.templates = {item["label"]: TaroAction(**item) for item in temp if isinstance(item, dict) and item.get("label") is not None}

