from sqlalchemy import Column, Integer, DateTime, String, Text, CheckConstraint
from demo_auth_svc.models.base import Base

class Meeting(Base):
    __tablename__ = 'meetings'

    meeting_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    participants = Column(Text, nullable=False)
    __table_args__ = (
        CheckConstraint("location <> ''", name="check_location_non_empty"),
    )

    def __repr__(self):
        return (f"<Meeting(meeting_id={self.meeting_id}, user_id={self.user_id}, "
                f"time={self.time}, location='{self.location}', "
                f"participants='{self.participants}')>")
