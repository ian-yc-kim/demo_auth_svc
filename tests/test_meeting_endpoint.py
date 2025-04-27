import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from demo_auth_svc.app import app


# Use the existing client fixture from conftest.py

@pytest.fixture
def client_instance(client):
    return client


# Fixture to simulate successful Google Calendar integration
@pytest.fixture
def dummy_success(monkeypatch):
    def dummy_add_google_calendar_event(meeting_time, location, participants, oauth_token):
        return {"success": True, "response": {"id": "dummy_event_id", "status": "confirmed"}}
    monkeypatch.setattr(
        "demo_auth_svc.google_calendar_integration.add_google_calendar_event",
        dummy_add_google_calendar_event
    )


# Fixture to simulate failure in Google Calendar integration
@pytest.fixture
def dummy_failure(monkeypatch):
    def dummy_add_google_calendar_event(meeting_time, location, participants, oauth_token):
        return {"success": False, "message": "Failed to create event"}
    monkeypatch.setattr(
        "demo_auth_svc.google_calendar_integration.add_google_calendar_event",
        dummy_add_google_calendar_event
    )


def test_create_meeting_success(client_instance, dummy_success):
    payload = {
        "meeting_time": "2023-10-26T15:30:00",
        "location": "Conference Room A",
        "participants": ["user1@example.com", "user2@example.com"],
        "oauth_token": "valid_token"
    }
    response = client_instance.post("/meetings", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data.get("id") == "dummy_event_id"
    assert data.get("status") == "confirmed"


def test_create_meeting_failure(client_instance, dummy_failure):
    payload = {
        "meeting_time": "2023-10-26T16:00:00",
        "location": "Conference Room B",
        "participants": ["user3@example.com"],
        "oauth_token": "invalid_token"
    }
    response = client_instance.post("/meetings", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Failed to create event" in data.get("detail")


def test_create_meeting_invalid_input(client_instance):
    # Missing required field 'oauth_token'
    payload = {
        "meeting_time": "2023-10-26T17:00:00",
        "location": "Conference Room C",
        "participants": ["user4@example.com"]
    }
    response = client_instance.post("/meetings", json=payload)
    assert response.status_code == 422  # Unprocessable Entity due to validation error
