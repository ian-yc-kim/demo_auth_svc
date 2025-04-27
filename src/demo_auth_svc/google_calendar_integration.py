import logging
import time
from datetime import datetime
from typing import Any, Dict, List

import httpx

def add_google_calendar_event(meeting_time: datetime, location: str, participants: List[str], oauth_token: str) -> Dict[str, Any]:
    """
    Add an event to Google Calendar using provided meeting details.

    Parameters:
        meeting_time (datetime): The meeting time to be converted to ISO 8601 format.
        location (str): The meeting location.
        participants (List[str]): List of participant emails.
        oauth_token (str): OAuth token for authentication.

    Returns:
        Dict[str, Any]: A dictionary with the success flag and response data or error message.
    """
    # Convert meeting_time to ISO 8601 format
    try:
        iso_meeting_time = meeting_time.isoformat()
    except Exception as e:
        logging.error(e, exc_info=True)
        return {"success": False, "message": "Invalid meeting_time format."}

    # Prepare the event data according to Google Calendar API schema
    event_data = {
        "start": {"dateTime": iso_meeting_time},
        "location": location,
        "attendees": [{"email": email} for email in participants]
    }

    # Set up headers with the OAuth token
    headers = {"Authorization": f"Bearer {oauth_token}"}
    # Google Calendar API endpoint for inserting events
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    retries = 3
    wait_seconds = 1

    for attempt in range(retries):
        try:
            response = httpx.post(url, json=event_data, headers=headers, timeout=10.0)
            response.raise_for_status()  # Raises an exception for 4xx/5xx responses
            return {"success": True, "response": response.json()}
        except Exception as e:
            logging.error(e, exc_info=True)
            if attempt < retries - 1:
                time.sleep(wait_seconds)
            else:
                return {"success": False, "message": str(e)}
