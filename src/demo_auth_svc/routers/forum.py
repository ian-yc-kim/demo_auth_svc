from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import logging
from typing import Optional, List, Dict
from datetime import datetime

from pydantic import BaseModel

from demo_auth_svc.models.forum_post import ForumPost
from demo_auth_svc.models.base import get_db
from jwt_module import create_token  # existing token creation, using stub for validation

router = APIRouter(prefix="/forum", tags=["forum"])

# Pydantic models for request and response

class ForumPostCreate(BaseModel):
    user_id: int
    content: str
    additional_metadata: Optional[Dict] = None


class ForumPostUpdate(BaseModel):
    content: Optional[str] = None
    additional_metadata: Optional[Dict] = None


class ForumPostResponse(BaseModel):
    post_id: int
    user_id: int
    content: str
    timestamp: datetime

# Dependency for JWT token validation

def verify_jwt_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = auth_header.split("Bearer ")[-1]
    # Since we don't have a real verify function in jwt_module, accept only 'dummy-token'
    if token != "dummy-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ForumPostResponse)
def create_forum_post(payload: ForumPostCreate, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
    try:
        new_post = ForumPost(user_id=payload.user_id, content=payload.content, additional_metadata=payload.additional_metadata)
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return ForumPostResponse(
            post_id=new_post.post_id,
            user_id=new_post.user_id,
            content=new_post.content,
            timestamp=new_post.timestamp
        )
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating forum post")


@router.put("/{post_id}", response_model=ForumPostResponse)
@router.patch("/{post_id}", response_model=ForumPostResponse)
def update_forum_post(post_id: int, payload: ForumPostUpdate, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
    try:
        post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
        if payload.content is not None:
            post.content = payload.content
        if payload.additional_metadata is not None:
            post.additional_metadata = payload.additional_metadata
        db.commit()
        db.refresh(post)
        return ForumPostResponse(
            post_id=post.post_id,
            user_id=post.user_id,
            content=post.content,
            timestamp=post.timestamp
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating forum post")


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forum_post(post_id: int, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
    try:
        post = db.query(ForumPost).filter(ForumPost.post_id == post_id).first()
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forum post not found")
        db.delete(post)
        db.commit()
        return
    except HTTPException:
        raise
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting forum post")


@router.get("", response_model=Dict)
def get_forum_posts(page: int = 1, page_size: int = 10, db: Session = Depends(get_db), token: str = Depends(verify_jwt_token)):
    try:
        offset = (page - 1) * page_size
        posts = db.query(ForumPost).offset(offset).limit(page_size).all()
        total_posts = db.query(ForumPost).count()
        posts_data = [ForumPostResponse(
            post_id=post.post_id,
            user_id=post.user_id,
            content=post.content,
            timestamp=post.timestamp
        ) for post in posts]
        return {"data": posts_data, "page": page, "page_size": page_size, "total": total_posts}
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error fetching forum posts")
