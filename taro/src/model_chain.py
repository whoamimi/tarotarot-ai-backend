"""
src/model_chain.py

Defines the associated mini LLM agents / helpers for Taro.
"""

from abc import abstractmethod, ABC

from src.schemas import TarotReading
from src.client import setup_client, LLM_MODEL_ID, OPTIONS

from utils.handler import TaroAction, TaroProfile
from utils.woodpecker import ErrorSettingUpModelChain, setup_logger

logger = setup_logger(__name__)

taro = TaroProfile.load_agent()

class SandCrawler(ABC):
    registry: dict[str, type["SandCrawler"]] = {}

    def __init__(self):
        self._decode_options = OPTIONS.copy()

    @abstractmethod
    def feature_augment(self, **kwargs) -> dict | None:
        """Subclasses must implement this to preprocess or validate input. Must return dict type. """
        pass

    def run(self, **kwargs) -> str: # type: ignore
        """Main entrypoint to run the data pipeline and return model output."""

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
        SandCrawler.registry[cls.__qualname__] = cls
        logger.info(f"Succesfully registered new Jawa member, {cls.__qualname__}(id: {cls.task.label if isinstance(cls.task, TaroAction) else ''})to our SandCrawler!", exc_info=True)

class CombinationAnalyst(SandCrawler, task=taro.templates.get('insight_combination', None)):
    def feature_augment(self, **kwargs):
        if inputs := kwargs.get('inputs', None):
            if isinstance(inputs, TarotReading):
                return {
                    'question': inputs.question,
                    'tarot_draw_input': inputs.drawn_cards
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
                    'tarot_draw_input': inputs.drawn_cards
                }
        else:
            raise ValueError

class StoryTell(SandCrawler, task=taro.templates.get('story_tell', None)):
    def feature_augment(self, **kwargs):
        return kwargs

if __name__ == "__main__":
    from datetime import datetime

    sample_tarot = TarotReading(
        timestamp=str(datetime.now().date()),
        question='When will I see pookie?',
        reading_mode='three_card', # type: ignore
        drawn_cards=['Ace of Wands', 'Wheel of fortune', 'Death (Reversed)']
    )

    comb = CombinationAnalyst()
    output = comb.run(inputs=sample_tarot)
    print(output)