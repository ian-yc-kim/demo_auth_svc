import pytest
from fastapi import status


def auth_header(valid: bool = True):
    token = "dummy-token" if valid else "invalid-token"
    return {"Authorization": f"Bearer {token}"}


def test_create_forum_post_success(client):
    payload = {
        "user_id": 1,
        "content": "This is a test forum post",
        "additional_metadata": {"key": "value"}
    }
    response = client.post("/forum", json=payload, headers=auth_header())
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == payload["user_id"]
    assert data["content"] == payload["content"]
    assert "post_id" in data
    assert "timestamp" in data


def test_create_forum_post_invalid_token(client):
    payload = {"user_id": 1, "content": "This is a test forum post"}
    response = client.post("/forum", json=payload, headers=auth_header(valid=False))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_forum_post_success(client):
    # First create a forum post
    payload = {"user_id": 2, "content": "Original content"}
    post_resp = client.post("/forum", json=payload, headers=auth_header())
    assert post_resp.status_code == status.HTTP_201_CREATED
    post_id = post_resp.json()["post_id"]

    # Now update the post
    update_payload = {"content": "Updated content"}
    update_resp = client.put(f"/forum/{post_id}", json=update_payload, headers=auth_header())
    assert update_resp.status_code == status.HTTP_200_OK
    updated_data = update_resp.json()
    assert updated_data["content"] == "Updated content"


def test_update_forum_post_not_found(client):
    update_payload = {"content": "Updated content"}
    response = client.put("/forum/9999", json=update_payload, headers=auth_header())
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_forum_post_success(client):
    # Create a forum post
    payload = {"user_id": 3, "content": "Content to delete"}
    post_resp = client.post("/forum", json=payload, headers=auth_header())
    post_id = post_resp.json()["post_id"]

    # Delete the post
    del_resp = client.delete(f"/forum/{post_id}", headers=auth_header())
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion by attempting to delete again
    del_resp_again = client.delete(f"/forum/{post_id}", headers=auth_header())
    assert del_resp_again.status_code == status.HTTP_404_NOT_FOUND


def test_get_forum_posts(client):
    # Ensure at least one forum post exists
    payload = {"user_id": 4, "content": "Content for get test"}
    client.post("/forum", json=payload, headers=auth_header())
    response = client.get("/forum?page=1&page_size=10", headers=auth_header())
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
