"""
src/model_chain.py

Defines the associated mini LLM agents / helpers for Taro.
"""

from abc import abstractmethod, ABC

from src.model_client import setup_client, LLM_MODEL_ID, OPTIONS
from utils.handler import TaroAction, TaroProfile
from utils.woodpecker import ErrorSettingUpModelChain, setup_logger

logger = setup_logger(__name__)

taro = TaroProfile.load_agent()

class SandCrawler(ABC):
    registry: dict[str, type["SandCrawler"]] = {}

    def __init__(self):
        self._decode_options = OPTIONS.copy()

    @abstractmethod
    def feature_augment(self, *args, **kwargs) -> dict:
        """Subclasses must implement this to preprocess or validate input. Must return dict type. """
        pass

    def process(self, **kwargs) -> list[dict[str, str]]:
        """To run / invoke this mini helping agent."""

        inputs = self.feature_augment(**kwargs)
        message = list(self.task.action_prompt(**inputs))
        return message

    def run(self, **kwargs) -> str:
        """Main entrypoint to run the data pipeline and return model output."""
        message = self.process(**kwargs)
        client = setup_client()
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

    def __init_subclass__(cls, task: TaroAction | str, **kwargs):
        super().__init_subclass__(**kwargs)
        if isinstance(task, str):
            raise ErrorSettingUpModelChain(task)

        cls.task = task
        SandCrawler.registry[cls.__qualname__] = cls
        logger.info(f"Succesfully registered new Jawa member, {cls.__qualname__}(id: {cls.task.label if isinstance(cls.task, TaroAction) else ''})to our SandCrawler!", exc_info=True)

class CombinationAnalyst(SandCrawler, task=taro.get_jawa('insight_combination')):
    def feature_augment(self, *args, **kwargs):
        return kwargs

class NumerologyAnalyst(SandCrawler, task=taro.get_jawa('insight_numerology')):
    def feature_augment(self, *args, **kwargs):
        return kwargs

class InsightHistory(SandCrawler, task=taro.get_jawa('story_tell')):
    def feature_augment(self, *args, **kwargs):
        return kwargs
