import pytest
from demo_auth_svc.models.forum_post import ForumPost


def test_create_forum_post(db_session):
    # Test creation of a forum post
    post = ForumPost(user_id=1, content='Test post', additional_metadata={"key": "value"})
    db_session.add(post)
    db_session.commit()
    assert post.post_id is not None


def test_read_forum_post(db_session):
    # Test reading the forum post
    post = ForumPost(user_id=2, content='Another post')
    db_session.add(post)
    db_session.commit()
    post_id = post.post_id
    retrieved = db_session.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    assert retrieved is not None
    assert retrieved.content == 'Another post'


def test_update_forum_post(db_session):
    # Test updating a forum post
    post = ForumPost(user_id=3, content='Update post')
    db_session.add(post)
    db_session.commit()
    post.content = 'Updated content'
    db_session.commit()
    updated = db_session.query(ForumPost).filter(ForumPost.post_id == post.post_id).first()
    assert updated.content == 'Updated content'


def test_delete_forum_post(db_session):
    # Test deletion of a forum post
    post = ForumPost(user_id=4, content='Delete post')
    db_session.add(post)
    db_session.commit()
    post_id = post.post_id
    db_session.delete(post)
    db_session.commit()
    deleted = db_session.query(ForumPost).filter(ForumPost.post_id == post_id).first()
    assert deleted is None


def test_non_null_constraints(db_session):
    # Test that non-null constraints are enforced
    with pytest.raises(Exception):
        post = ForumPost(user_id=1, content=None)
        db_session.add(post)
        db_session.commit()
