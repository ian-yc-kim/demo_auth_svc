import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from demo_auth_svc.app import app
from demo_auth_svc.models.meeting import Meeting


# Helper function to create a meeting directly in the database
def create_meeting_in_db(db, user_id=1, meeting_time_str='2023-10-26T10:00:00', location='Conference Room A', participants='user1@example.com,user2@example.com'):
    meeting_time = datetime.fromisoformat(meeting_time_str)
    meeting = Meeting(
        user_id=user_id,
        time=meeting_time,
        location=location,
        participants=participants
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@pytest.fixture
def client_instance(client):
    return client


# Test updating a meeting with valid data
def test_update_meeting_success(client_instance, db_session):
    # Insert a meeting into the DB
    meeting = create_meeting_in_db(db_session, location='Conference Room A')
    
    update_payload = {
        "meeting_time": "2023-10-26T11:00:00",
        "location": "Conference Room B",
        "participants": ["user1@example.com", "user3@example.com"]
    }
    response = client_instance.put(f"/meetings/{meeting.meeting_id}", json=update_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    # Validate updated fields
    assert data.get('location') == "Conference Room B"
    # Check that meeting_time is updated (returned in ISO format)
    assert "2023-10-26T11:00:00" in data.get('time')
    # Participants stored as comma separated string
    assert "user1@example.com,user3@example.com" in data.get('participants')


# Test updating a meeting with empty location, expected to fail
def test_update_meeting_empty_location(client_instance, db_session):
    meeting = create_meeting_in_db(db_session, location='Initial Location')
    update_payload = {
        "location": "   "  
    }
    response = client_instance.put(f"/meetings/{meeting.meeting_id}", json=update_payload)
    assert response.status_code == 400, response.text
    data = response.json()
    assert "Location must not be empty" in data.get('detail')


# Test updating a meeting with invalid email in participants
def test_update_meeting_invalid_email(client_instance, db_session):
    meeting = create_meeting_in_db(db_session)
    update_payload = {
        "participants": ["invalid-email", "user2@example.com"]
    }
    response = client_instance.put(f"/meetings/{meeting.meeting_id}", json=update_payload)
    assert response.status_code == 400, response.text
    data = response.json()
    assert "Invalid email: invalid-email" in data.get('detail')


# Test deleting a meeting successfully
def test_delete_meeting_success(client_instance, db_session):
    meeting = create_meeting_in_db(db_session)
    response = client_instance.delete(f"/meetings/{meeting.meeting_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "Meeting deleted" in data.get('detail')
    
    # Try to get the meeting by user to ensure it's deleted
    response_get = client_instance.get(f"/meetings/user/{meeting.user_id}")
    assert response_get.status_code == 200
    meetings = response_get.json()
    # Ensure meeting_id is not in the list
    meeting_ids = [m.get('meeting_id') for m in meetings]
    assert meeting.meeting_id not in meeting_ids


# Test retrieving meetings by user id
def test_get_meetings_by_user(client_instance, db_session):
    # Insert two meetings for user_id 1
    meeting1 = create_meeting_in_db(db_session, user_id=1, location='Room 1')
    meeting2 = create_meeting_in_db(db_session, user_id=1, location='Room 2')
    # Insert one meeting for different user
    create_meeting_in_db(db_session, user_id=2, location='Room 3')
    
    response = client_instance.get(f"/meetings/user/1")
    assert response.status_code == 200, response.text
    meetings = response.json()
    # Expect at least two meetings
    assert isinstance(meetings, list)
    meeting_locations = [m.get('location') for m in meetings]
    assert 'Room 1' in meeting_locations
    assert 'Room 2' in meeting_locations

