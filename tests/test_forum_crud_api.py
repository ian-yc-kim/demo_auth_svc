import time
import pytest
from fastapi import status


def auth_header(valid: bool = True):
    token = "dummy-token" if valid else "invalid-token"
    return {"Authorization": f"Bearer {token}"}


def test_post_forum_valid(client):
    payload = {
        "user_id": 1,
        "content": "Valid forum post",
        "additional_metadata": {"info": "test"}
    }
    response = client.post("/forum", json=payload, headers=auth_header())
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data.get("user_id") == payload["user_id"]
    assert data.get("content") == payload["content"]
    assert "post_id" in data
    assert "timestamp" in data


def test_post_forum_missing_fields(client):
    # Missing required field 'content'
    payload = {"user_id": 1}
    response = client.post("/forum", json=payload, headers=auth_header())
    # FastAPI/Pydantic returns 422 for validation errors
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_post_forum_invalid_types(client):
    # user_id should be integer; providing string to simulate invalid type
    payload = {"user_id": "not_an_int", "content": "Invalid type test", "additional_metadata": {}}
    response = client.post("/forum", json=payload, headers=auth_header())
    # Expecting validation error
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_post_forum_invalid_jwt(client):
    payload = {"user_id": 1, "content": "Test invalid JWT"}
    response = client.post("/forum", json=payload, headers=auth_header(valid=False))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_forum_post_valid(client):
    # Create a forum post first
    payload = {"user_id": 2, "content": "Original content"}
    create_response = client.post("/forum", json=payload, headers=auth_header())
    assert create_response.status_code == status.HTTP_201_CREATED
    post_id = create_response.json()["post_id"]

    # Update the post
    update_payload = {"content": "Updated content", "additional_metadata": {"edited": True}}
    update_response = client.put(f"/forum/{post_id}", json=update_payload, headers=auth_header())
    assert update_response.status_code == status.HTTP_200_OK
    updated_data = update_response.json()
    assert updated_data.get("content") == "Updated content"


def test_update_forum_post_empty_payload(client):
    # Create forum post
    payload = {"user_id": 3, "content": "Initial content"}
    create_response = client.post("/forum", json=payload, headers=auth_header())
    assert create_response.status_code == status.HTTP_201_CREATED
    post_id = create_response.json()["post_id"]

    # Send an empty payload; expect no changes
    update_payload = {}
    update_response = client.put(f"/forum/{post_id}", json=update_payload, headers=auth_header())
    assert update_response.status_code == status.HTTP_200_OK
    data = update_response.json()
    # Since no fields provided, content remains unchanged
    assert data.get("content") == "Initial content"


def test_update_forum_post_not_found(client):
    update_payload = {"content": "Attempt to update non-existent post"}
    response = client.put("/forum/9999", json=update_payload, headers=auth_header())
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_forum_post_invalid_jwt(client):
    # Create a forum post
    payload = {"user_id": 4, "content": "Content before invalid JWT update"}
    create_response = client.post("/forum", json=payload, headers=auth_header())
    assert create_response.status_code == status.HTTP_201_CREATED
    post_id = create_response.json()["post_id"]

    # Attempt update with invalid JWT
    update_payload = {"content": "Should not update"}
    response = client.put(f"/forum/{post_id}", json=update_payload, headers=auth_header(valid=False))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_forum_post_valid(client):
    # Create a forum post for deletion
    payload = {"user_id": 5, "content": "Post to be deleted"}
    create_response = client.post("/forum", json=payload, headers=auth_header())
    assert create_response.status_code == status.HTTP_201_CREATED
    post_id = create_response.json()["post_id"]

    # Delete the post
    delete_response = client.delete(f"/forum/{post_id}", headers=auth_header())
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_forum_post_not_found(client):
    # Attempt to delete a post that does not exist
    response = client.delete("/forum/8888", headers=auth_header())
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_forum_post_invalid_jwt(client):
    # Create a forum post
    payload = {"user_id": 6, "content": "Post for JWT deletion test"}
    create_response = client.post("/forum", json=payload, headers=auth_header())
    assert create_response.status_code == status.HTTP_201_CREATED
    post_id = create_response.json()["post_id"]

    # Attempt deletion with an invalid JWT
    response = client.delete(f"/forum/{post_id}", headers=auth_header(valid=False))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_forum_posts(client):
    # Ensure multiple posts exist for retrieval
    for i in range(3):
        payload = {"user_id": 7, "content": f"Post {i}"}
        client.post("/forum", json=payload, headers=auth_header())

    # Measure response time for performance check
    start_time = time.time()
    response = client.get("/forum?page=1&page_size=10", headers=auth_header())
    elapsed = (time.time() - start_time) * 1000  # elapsed time in milliseconds
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    # Ensure response time is less than 300ms as an indirect performance check
    assert elapsed < 300, f"Response took too long: {elapsed}ms"
