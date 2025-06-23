import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from taro.app import app
from src.schemas import TarotReading
from src.model_chain import CombinationAnalyst
from utils.woodpecker import InvalidTarotMode

client = TestClient(app)

BASE_URL = "http://localhost:11434"

@pytest.mark.asyncio
async def test_root():
    """ Tests the Apps root connection. """
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Taro Active" in response.text

@pytest.mark.asyncio
async def test_combination_analyst_raises_invalid_tarot_mode():
    inputs = {
        "timestamp": "2025-06-22T02:30:00",
        "question": "What should I focus on this week?",
        "reading_mode": "daily_spread",  # invalid
        "drawn_cards": ["The Fool", "The Magician", "The Star"]
    }

    analyst = CombinationAnalyst()

    with pytest.raises(InvalidTarotMode) as excinfo:
        analyst.run(inputs=TarotReading(**inputs))

    exc = excinfo.value
    assert "daily_spread" in exc.message
    assert exc.status_code == 404

@pytest.mark.asyncio
async def test_prediction_incorrect_num_cards():
    payload = {
        "question": "What should I focus on this week?",
        "cards": ["The Fool", "The Magician", "The Star"],
        "reading_mode": "one_card"
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/predictions/", json=payload)

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Please draw the correct number of input cards 1. Only 3 cards received for reading one_card"
    }

@pytest.mark.asyncio
async def test_tarot_insight_stats_case_sensitive():
    payload = {
        "reading_mode": "THREE_CARD",
        "drawn_cards": ["ace of wandS", "NINE OF WANDS", "twO OF SWORDS"]
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/insight_stats/", json=payload)
        output = response.json()
    assert output and set(output.keys()) == {"stat"}, f"Unexpected output: {output}"


@pytest.mark.asyncio
async def test_user_astrology():
    payload = {
        "id": "12345",
        "username": "whoamimi",
        "first_name": "john",
        "last_name": "snow",
        "birth_date": "20-02-1994",
        "birth_time": "03:15",
        "birth_place": "Australia/Sydney",
        "gender": "male"
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/user_astrology/", json=payload)
    assert response.status_code == 200
    assert response.json()["first_name"] == "john"

@pytest.mark.asyncio
async def test_insight_combination():
    payload = {
        "timestamp": "2025-06-22T02:30:00",
        "question": "What does my reading reveal about my life path?",
        "reading_mode": {"position": "present", "draw_num": 3},
        "drawn_cards": ["Ace of Cups", "Three of Wands", "Ten of Swords"]
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/insight_combination/", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

@pytest.mark.asyncio
async def test_insight_numerology():
    payload = {
        "timestamp": "2025-06-22T02:30:00",
        "question": "What does my reading reveal about my life path?",
        "reading_mode": {"position": "present", "draw_num": 3},
        "drawn_cards": ["Ace of Cups", "Three of Wands", "Ten of Swords"]
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/insight_numerology/", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), dict)


@pytest.mark.asyncio
async def test_insight_stats():
    payload = {
        "reading_mode": "three_card",
        "drawn_cards": ["ace of wands", " nine of cups ", "two of swords"]
    }
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        response = await ac.post("/insight_stats/", json=payload)
    assert response.status_code == 200
    assert "wand_count" in response.json()