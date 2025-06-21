
import pytest
from pydantic import ValidationError
from src.data_models import TarotInsights, UserProfile, TarotReading
from utils.woodpecker import InvalidTarotInsightsCalculation

def test_user_profile_incorrect_datetime_format():
    """ Test create new user with incorrect datetime format. """
    with pytest.raises(ValueError) as excinfo:
        User(
            id='12345',
            username='whoamimi',
            first_name='mimi',
            last_name='phan',
            birth_date='1994-12-21',
            birth_time='03:15',
            birth_place='Australia/Sydney'
        )
    assert "does not match format '%d-%m-%Y'" in str(excinfo.value)

def test_user_profile_success():
    """ Test successful creation of user with correct datetime format. """
    user = User(
        id='abcde-12345',
        username='astrofan',
        first_name='mimi',
        last_name='phan',
        birth_date='21-12-1994',
        birth_time='03:15',
        birth_place='Australia/Sydney'
    )

    assert user.username == 'astrofan'
    assert user.first_name == 'Mimi'  # assuming DisplayName validator applies title-case
    assert user.birth_place == 'Australia/Sydney'
    assert user.sun_sign is not None

    user._get_astrology()

def test_tarot_insights():
    insights = TarotInsights(
        num_cards=4,
        king_count=1,
        queen_count=1,
        wand_count=2,
        coin_count=1,
        sword_count=1
    )

    assert insights.stats["king"] == 0.25 and insights.stats["wand"] == 0.5 and insights.stats["cup"] == 0.0 and insights.stats["coin"] == 0.25
    assert insights.stats["card_count"] == 4 and insights.stats["card_count"] == 4

def test_model_dump_includes_stats():
    insights = TarotInsights(num_cards=1, wand_count=1)
    dumped = insights.model_dump()

    assert "stats" in dumped
    assert dumped["stats"]["wand"] == 1.0
    assert dumped["stats"]["king"] == 0.0 and dumped["stats"]["queen"] == dumped["stats"]["court_prob"]

def test_zero_num_cards_raises():
    insights = TarotInsights(num_cards=0)
    with pytest.raises(ZeroDivisionError):
        insights.get_stats()

