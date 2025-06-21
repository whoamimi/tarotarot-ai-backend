"""
src/agent_state.py
"""

from supabase import create_client
from schemas import TaroPostRequest, TaroResponse

from src.schemas import UserFeedback
from src.model_client import setup_client
from utils.handler import TaroProfile, TAROT_READING_MODE
from utils.woodpecker import setup_logger, InvalidTarotAction

logger = setup_logger(__name__)

# State Management
class TaroState:
    """ Taro State Manager Class. """

    def __init__(self, supabase_url: str, supabase_key: str):
        self.DB_DECODER_STATES = "model_decoder_states"
        self.DB_USERS = "users"
        self.DB_MAIN = "readings"

        self.profile = TaroProfile.load_agent()
        logger.info(f"Loaded Agent profile: {self.profile}")
        self.modes = TAROT_READING_MODE
        self.client = 'mock_client' # setup_client() # Ollama set up
        self.supa = create_client(supabase_url, supabase_key)
        logger.info(f"Loaded Agent profile: {self.profile}")

    def add_session(self, inputs: TaroPostRequest, data: TaroResponse):
        """ Adds readings to sessions. """
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

    def action(self, action_id, **kwargs):
        """ Triggers agent's task.

        if action := self.profile.templates.get(action_id, None) if isinstance(self.profile.templates, dict) else None:
            yield from action.action_prompt(**kwargs)
        else:
            raise InvalidTarotAction(action_id)

        """
        pass