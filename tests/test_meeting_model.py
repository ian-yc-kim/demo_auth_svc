import logging
from datetime import datetime

import sqlalchemy

from demo_auth_svc.models.meeting import Meeting


def test_create_read_update_delete_meeting(db_session):
    try:
        # Create a new Meeting instance
        meeting = Meeting(
            user_id=1,
            time=datetime(2023, 10, 1, 10, 0, 0),
            location='Conference Room A',
            participants='user1@example.com,user2@example.com'
        )
        db_session.add(meeting)
        db_session.commit()
        
        # Read the meeting
        created_meeting = db_session.query(Meeting).filter(Meeting.meeting_id == meeting.meeting_id).first()
        assert created_meeting is not None
        assert created_meeting.location == 'Conference Room A'

        # Update the meeting
        created_meeting.location = 'Conference Room B'
        db_session.commit()

        updated_meeting = db_session.query(Meeting).filter(Meeting.meeting_id == meeting.meeting_id).first()
        assert updated_meeting.location == 'Conference Room B'

        # Delete the meeting
        db_session.delete(updated_meeting)
        db_session.commit()

        deleted_meeting = db_session.query(Meeting).filter(Meeting.meeting_id == meeting.meeting_id).first()
        assert deleted_meeting is None
    except Exception as e:
        logging.error(e, exc_info=True)
        assert False, f"Test failed due to exception: {e}"
