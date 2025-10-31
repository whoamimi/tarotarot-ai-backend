"""
src/agent/base.py

Base Class builders for Tarot Reading Agent.
"""

import re
from abc import abstractmethod, ABC

from utils.woodpecker import ErrorSettingUpModelChain
from src.agent.client import setup_client, LLM_MODEL_ID, OPTIONS

class SandCrawler(ABC):
    @abstractmethod
    def feature_augment(self, **kwargs) -> dict | None:
        """ Subclasses must implement this to preprocess or validate input. Must return dict type. """
        pass

    def run(self, **kwargs) -> str: # type: ignore
        """ Main entrypoint to run the data pipeline and return model output."""

        if 'inputs' not in kwargs:
            raise ValueError(f'Expected `inputs` to be one of the passing keys of kwargs but received: {kwargs}')

        if inputs := self.feature_augment(**kwargs):
            # Avoid logging full user inputs to prevent PII leakage
            message = list(self.task.prepare_prompt(**inputs))
            # Fetch Client and validate connection / ollana active
            client = setup_client()

            # Client output
            output = client.chat(
                model=LLM_MODEL_ID,
                messages=message,
                stream=False,
                options=self._decode_options
            )
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
        else:
            raise TypeError("decode_kwargs must be set with a dictionary.")

    def __init_subclass__(cls, task: TaroAction | str | None, **kwargs):
        super().__init_subclass__(**kwargs)
        if isinstance(task, str) or not task:
            raise ErrorSettingUpModelChain(task)

        cls.task = task
        cls._decode_options = OPTIONS.copy()
        print(f"Succesfully registered new Jawa member, {cls.__qualname__}(id: {cls.task.label if isinstance(cls.task, TaroAction) else ''})to our SandCrawler!", exc_info=True)
