"""
src/agent/agents.py

Contains the Helper Agent for the Tarot Reading Agent.
"""

from .base import SandCrawler

from src.schemas import TarotReading
from utils.handler import TaroAction, TaroProfile
from utils.woodpecker import ErrorSettingUpModelChain

taro = TaroProfile.load_agent()

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
                logger.debug("Extracted combination highlights. Length: %d", len(comb_response or ""))
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
    logger = setup_logger(__name__)
    logger.info("StoryTell sample output length: %d", len(output or ""))
    # Example output
