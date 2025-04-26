from sqlalchemy import Column, Integer, String, DateTime, func
from demo_auth_svc.models.base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    google_id = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False)
    name = Column(String)
    profile_picture = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<User(id={self.id}, google_id='{self.google_id}', email='{self.email}')>"
