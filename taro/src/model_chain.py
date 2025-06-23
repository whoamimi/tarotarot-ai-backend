"""
src/model_chain.py

Defines the associated mini LLM agents / helpers for Taro.
"""

import re
from abc import abstractmethod, ABC

from src.schemas import TarotReading
from src.client import setup_client, LLM_MODEL_ID, OPTIONS

from utils.handler import TaroAction, TaroProfile
from utils.woodpecker import ErrorSettingUpModelChain, setup_logger

logger = setup_logger(__name__)

taro = TaroProfile.load_agent()

class SandCrawler(ABC):
    def __init__(self):
        self._decode_options = OPTIONS.copy()

    @abstractmethod
    def feature_augment(self, **kwargs) -> dict | None:
        """ Subclasses must implement this to preprocess or validate input. Must return dict type. """
        pass

    def run(self, **kwargs) -> str: # type: ignore
        """ Main entrypoint to run the data pipeline and return model output."""

        if 'inputs' not in kwargs:
            raise ValueError(f'Expected `inputs` to be one of the passing keys of kwargs but received: {kwargs}')

        if inputs := self.feature_augment(**kwargs):
            logger.info(f"Formating prompts before inserting to model: {inputs}")

            message = list(self.task.prepare_prompt(**inputs))
            logger.info(f"Done! Getting ready to invoke LLM with:\n {message}")

            # Fetch Client and validate connection / ollana active
            client = setup_client()

            # Client output
            output = client.chat(
                model=LLM_MODEL_ID,
                messages=message,
                stream=False,
                options=self._decode_options
            )

            logger.info(f"Ollama Output Returned: {output.message['content']}")

            return output.message.get('content', None)

    @property
    def decode_kwargs(self):
        """ Returns the decoder kwargs in LLM. """
        return self._decode_options

    @decode_kwargs.setter
    def decode_kwargs(self, kwargs: dict):
        """Update the decoder kwargs in the class instance."""
        if isinstance(kwargs, dict):
            for key, val in kwargs.items():
                if not hasattr(self._decode_options, key):
                    raise KeyError(f"Unknown decode option: {key!r}")
                setattr(self._decode_options, key, val)
            logger.info(f"Updated the decoder kwargs for current session: {self._decode_options}")
        else:
            raise TypeError("decode_kwargs must be set with a dictionary.")

    def __init_subclass__(cls, task: TaroAction | str | None, **kwargs):
        super().__init_subclass__(**kwargs)
        if isinstance(task, str) or not task:
            raise ErrorSettingUpModelChain(task)

        cls.task = task
        logger.info(f"Succesfully registered new Jawa member, {cls.__qualname__}(id: {cls.task.label if isinstance(cls.task, TaroAction) else ''})to our SandCrawler!", exc_info=True)

class CombinationAnalyst(SandCrawler, task=taro.templates.get('insight_combination', None)):
    def feature_augment(self, **kwargs):
        if inputs := kwargs.get('inputs', None):
            if isinstance(inputs, TarotReading):
                return {
                    'question': inputs.question,
                    'tarot_draw_input': inputs.pos_draw
                }
        else:
            raise ValueError

class NumerologyAnalyst(SandCrawler, task=taro.templates.get('insight_numerology', None)):
    def feature_augment(self, **kwargs):
        """ Reads the tarots inputs"""
        if inputs := kwargs.get('inputs', None):
            if isinstance(inputs, TarotReading):
                return {
                    'question': inputs.question,
                    'tarot_draw_input': inputs.pos_draw
                }
        else:
            raise ValueError

class StoryTell(SandCrawler, task=taro.templates.get('story_tell', None)):
    def feature_augment(self, **kwargs):

        if inputs := kwargs.get('inputs', None):
            if (
                (user := inputs.get('user')) and isinstance(user, User) and
                (tarot := inputs.get('tarot')) and isinstance(tarot, TarotReading)
            ):
                comb_model = CombinationAnalyst()
                numb_model = NumerologyAnalyst()

                comb_output = comb_model.run(inputs=tarot)
                numb_output = numb_model.run(inputs=tarot)

                txt = f"""**User Info**\nFull Name: {user.first_name.lower().title()} {user.last_name.lower().title()}\nBirth Date: {user.birth_date}""" # type: ignore

                comb_response = extract_combination_highlights(comb_output)
                print('\n\nInserting combination string response:\n', comb_response)
                self.decode_kwargs = {'num_predict': 500}
                return {
                    'current_timestamp': tarot.timestamp,
                    'question': tarot.question,
                    'tarot_draw_input': tarot.pos_draw,
                    'insight_combination': comb_response,
                    'insight_numerology': numb_output,
                    'user_info': txt
                }
        else:
            raise ValueError

def extract_combination_highlights(text: str) -> str:
    pattern = r"\*\*Combination Highlights\*\*(.*?)\*\*Possible insights"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "No combination highlights found."


if __name__ == "__main__":
    from src.schemas import User
    from datetime import datetime

    sample_user = User(
        id='12345',
        username='julie.lenova',
        first_name='Julie',
        last_name='Lenova',
        birth_date='21-03-1999',
    )

    sample_tarot = TarotReading(
        timestamp=str(datetime.now().date()),
        question='When will I see pookie?',
        reading_mode='three_card', # type: ignore
        drawn_cards=['two of cups', 'wheel of fortune', 'Death']
    )

    stry = StoryTell()
    output = stry.run(inputs={'user': sample_user, 'tarot': sample_tarot})
    print(output)
    # Example output
