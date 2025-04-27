import json
from datetime import datetime

import httpx
import pytest

from demo_auth_svc.google_calendar_integration import add_google_calendar_event

class DummyResponse:
    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            # Include the error message from the response to aid debugging
            raise httpx.HTTPStatusError(self.text, request=None, response=self)


def test_add_google_calendar_event_success(monkeypatch):
    # Setup dummy successful response
    def dummy_post(url, json, headers, timeout):
        return DummyResponse({"id": "event123", "status": "confirmed"}, 200)

    monkeypatch.setattr(httpx, 'post', dummy_post)
    meeting_time = datetime(2023, 10, 26, 15, 30)
    location = "Conference Room A"
    participants = ["user1@example.com", "user2@example.com"]
    oauth_token = "valid_token"
    
    result = add_google_calendar_event(meeting_time, location, participants, oauth_token)
    
    assert result["success"] is True
    assert "id" in result["response"]
    

def test_add_google_calendar_event_failure(monkeypatch):
    # Setup dummy failure response to simulate API error
    call_count = {'count': 0}

    def dummy_post_fail(url, json, headers, timeout):
        call_count['count'] += 1
        # simulate failure on each call
        return DummyResponse({"error": "Bad Request"}, 400)

    monkeypatch.setattr(httpx, 'post', dummy_post_fail)
    meeting_time = datetime(2023, 10, 26, 15, 30)
    location = "Conference Room B"
    participants = ["user3@example.com"]
    oauth_token = "invalid_token"
    
    result = add_google_calendar_event(meeting_time, location, participants, oauth_token)

    # Should have attempted retries (3 attempts)
    assert call_count['count'] == 3
    assert result["success"] is False
    assert "Bad Request" in result["message"]


def test_invalid_meeting_time(monkeypatch):
    # Test passing an invalid meeting_time to trigger conversion failure
    # We'll pass a string instead of a datetime
    meeting_time = "not a datetime"
    location = "Conference Room C"
    participants = ["user4@example.com"]
    oauth_token = "token"
    
    result = add_google_calendar_event(meeting_time, location, participants, oauth_token)
    
    assert result["success"] is False
    assert result["message"] == "Invalid meeting_time format."
