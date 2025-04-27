import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

import demo_auth_svc.google_calendar_integration as gc_integration

router = APIRouter()


class MeetingRequest(BaseModel):
    meeting_time: datetime
    location: str
    participants: List[str]
    oauth_token: str


@router.post("/meetings")
def create_meeting(meeting: MeetingRequest):
    try:
        result = gc_integration.add_google_calendar_event(
            meeting_time=meeting.meeting_time,
            location=meeting.location,
            participants=meeting.participants,
            oauth_token=meeting.oauth_token
        )
        if result.get("success"):
            return result.get("response")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message"))
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
