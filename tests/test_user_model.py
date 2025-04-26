import pytest
from datetime import datetime
from sqlalchemy import select

from demo_auth_svc.models.user import User


def test_create_read_update_delete_user(db_session):
    session = db_session

    # Create a new user
    new_user = User(
        google_id='google123', 
        email='test@example.com', 
        name='Test User', 
        profile_picture='http://example.com/pic.jpg'
    )
    session.add(new_user)
    session.commit()

    # Read the user
    stmt = select(User).where(User.google_id == 'google123')
    result = session.execute(stmt).scalar_one_or_none()
    assert result is not None
    assert result.email == 'test@example.com'

    # Update the user's name
    result.name = 'Updated User'
    session.commit()

    stmt = select(User).where(User.google_id == 'google123')
    updated_user = session.execute(stmt).scalar_one()
    assert updated_user.name == 'Updated User'

    # Delete the user
    session.delete(updated_user)
    session.commit()

    stmt = select(User).where(User.google_id == 'google123')
    deleted_user = session.execute(stmt).scalar_one_or_none()
    assert deleted_user is None
