
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from taro.app import app

client = TestClient(app)

def test_app_exists():
    assert app is not None

def test_root():
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.text == '"Taro Active"'

def test_prediction_incorrect_reading_id():
    payload = {
        "question": "What should I focus on this week?",
        "cards": ["The Fool", "The Magician", "The Star"],
        "reading_id": "daily_spread"
    }
    response = client.post("/predictions/", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Mode 'daily_spread' not found."}

def test_prediction_incorrect_num_cards():
    response = client.post("/predictions/", json={
        "question": "What should I focus on this week?",
        "cards": ["The Fool", "The Magician", "The Star"],
        "reading_id": "one_card"
    })

    assert response.status_code == 500
    assert response.json() == {"detail":"Please draw the correct number of input cards 1. Only 3 cards received for reading one_card"}

def test_prediction():
    response = client.post("/predictions/", json={
        "question": "What should I focus on this week?",
        "cards": ["The Fool", "The Magician", "The Star"],
        "reading_id": "three_cards"
    })

    assert response.status_code == 404
    assert response.json() == {"detail":"Please draw the correct number of input cards 1. Only 3 cards received for reading one_card"}

