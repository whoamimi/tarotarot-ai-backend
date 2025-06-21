"""
src/utils.py
"""

import yaml
from pathlib import Path
from dataclasses import dataclass

from utils.woodpecker import UnavailableAction, setup_logger, InvalidModelInputs, LoadedProfileError

logger = setup_logger(__name__)

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

    def action_prompt(self, **kwargs):
        """
        Returns System Message with users inputs in chat formatted message to invoke LLM. Defaults to Llama 3.1 models' chatting template.
        """
        if user_input := self.input_template.format(**kwargs) if self.input_template else None:
            yield {"role": "system", "content": self.system_prompt}
            yield {"role": "user", "content": user_input}

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

    def get_jawa(self, label: str):
        """ Return an instance of the registered SandCrawler class by template label. """

        if jawa := self.templates.get(label):
            return jawa
        raise UnavailableAction(label)

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
