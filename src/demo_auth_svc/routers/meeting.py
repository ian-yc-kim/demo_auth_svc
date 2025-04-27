import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, validator

from demo_auth_svc.models.base import get_db
from demo_auth_svc.models.meeting import Meeting
import demo_auth_svc.google_calendar_integration as gc_integration

router = APIRouter()

class MeetingRequest(BaseModel):
    meeting_time: datetime
    location: str
    participants: List[str]
    oauth_token: str

    @validator('meeting_time', pre=True)
    def validate_meeting_time_format(cls, v):
        # Accept either ISO format or 'yyyy-mm-dd HH:MM AM/PM'
        if isinstance(v, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(v)
            except Exception:
                try:
                    return datetime.strptime(v, "%Y-%m-%d %I:%M %p")
                except Exception:
                    raise ValueError("meeting_time must be in ISO format or 'yyyy-mm-dd HH:MM AM/PM'")
        return v

    @validator('location')
    def location_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Location must not be empty')
        return v

    class Config:
        schema_extra = {
            "example": {
                "meeting_time": "2023-10-26T15:30:00",
                "location": "Conference Room A",
                "participants": ["user1@example.com", "user2@example.com"],
                "oauth_token": "your_oauth_token_here"
            }
        }

class MeetingUpdateRequest(BaseModel):
    meeting_time: Optional[datetime] = None
    location: Optional[str] = None
    participants: Optional[List[str]] = None

    @validator('meeting_time', pre=True, always=True)
    def validate_meeting_time_format(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except Exception:
                try:
                    return datetime.strptime(v, "%Y-%m-%d %I:%M %p")
                except Exception:
                    raise ValueError("meeting_time must be in ISO format or 'yyyy-mm-dd HH:MM AM/PM'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "meeting_time": "2023-10-26T11:00:00",
                "location": "Conference Room B",
                "participants": ["user1@example.com", "user3@example.com"]
            }
        }

class MeetingResponse(BaseModel):
    meeting_id: int
    user_id: int
    time: datetime
    location: str
    participants: str

    class Config:
        orm_mode = True
        from_attributes = True

@router.post("/meetings")

def create_meeting(meeting: MeetingRequest, db=Depends(get_db)):
    """
    Create a meeting and integrate with Google Calendar.
    Validates meeting_time format, non-empty location, and participant emails.
    On successful Google Calendar integration, stores the meeting in the database and returns the event details.
    Note: The user_id is hardcoded as 1 for demonstration purposes.
    """
    try:
        # Validate participant emails using email-validator
        try:
            from email_validator import validate_email
        except ImportError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email validator not installed")
        valid_emails = []
        for email in meeting.participants:
            try:
                valid = validate_email(email, check_deliverability=False)
                valid_emails.append(valid.email)
            except Exception as ve:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid email: {email}")

        # Convert meeting to dict and update participants with validated emails
        meeting_data = meeting.dict()
        meeting_data["participants"] = valid_emails

        # Call Google Calendar integration
        result = gc_integration.add_google_calendar_event(
            meeting_time=meeting.meeting_time,
            location=meeting.location,
            participants=valid_emails,
            oauth_token=meeting.oauth_token
        )
        if result.get("success"):
            # After successful integration, store meeting in DB
            new_meeting = Meeting(
                user_id=1,  # Hardcoded; in production, use actual user id from auth context.
                time=meeting.meeting_time,
                location=meeting.location,
                participants=",".join(valid_emails)
            )
            db.add(new_meeting)
            db.commit()
            db.refresh(new_meeting)
            # Return only the Google Calendar response to match expected API response
            return result.get("response")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message"))
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/meetings/{meeting_id}")

def update_meeting(meeting_id: int, meeting_update: MeetingUpdateRequest, db=Depends(get_db)):
    """
    Update meeting details for the given meeting_id.
    Validates updated fields: meeting_time format, non-empty location, and participant emails.
    Returns the updated meeting record on success.
    """
    try:
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        if meeting_update.meeting_time is not None:
            meeting.time = meeting_update.meeting_time
        if meeting_update.location is not None:
            if not meeting_update.location.strip():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location must not be empty")
            meeting.location = meeting_update.location
        if meeting_update.participants is not None:
            try:
                from email_validator import validate_email
            except ImportError:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email validator not installed")
            valid_emails = []
            for email in meeting_update.participants:
                try:
                    valid = validate_email(email, check_deliverability=False)
                    valid_emails.append(valid.email)
                except Exception as ve:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid email: {email}")
            meeting.participants = ",".join(valid_emails)
        db.commit()
        db.refresh(meeting)
        return MeetingResponse.from_orm(meeting)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/meetings/{meeting_id}")

def delete_meeting(meeting_id: int, db=Depends(get_db)):
    """
    Delete the meeting with the specified meeting_id.
    Returns a success message upon deletion.
    """
    try:
        meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        db.delete(meeting)
        db.commit()
        return {"detail": "Meeting deleted"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/meetings/user/{user_id}")

def get_meetings_by_user(user_id: int, db=Depends(get_db)):
    """
    Retrieve all meetings associated with the provided user_id.
    Returns a list of meeting records.
    """
    try:
        meetings = db.query(Meeting).filter(Meeting.user_id == user_id).all()
        return [MeetingResponse.from_orm(m) for m in meetings]
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
