from sqlalchemy import Column, Integer, Text, DateTime, func, Index, ForeignKey, JSON
from demo_auth_svc.models.base import Base


class ForumPost(Base):
    __tablename__ = 'forum_posts'

    post_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    additional_metadata = Column(JSON, nullable=True)

    __table_args__ = (
        Index('ix_forum_posts_user_id', 'user_id'),
        Index('ix_forum_posts_timestamp', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<ForumPost(post_id={self.post_id}, user_id={self.user_id})>"
