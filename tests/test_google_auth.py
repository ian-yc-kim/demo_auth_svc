import os
import json
import httpx
import pytest
from fastapi import HTTPException


def test_signup_redirect(client, monkeypatch):
    # Setup environment variables
    monkeypatch.setenv("CLIENT_ID", "test_client_id")
    monkeypatch.setenv("REDIRECT_URI", "http://localhost/callback")
    
    # Using 'follow_redirects' instead of 'allow_redirects' because TestClient does not accept 'allow_redirects'
    response = client.get("/auth/google/signup", follow_redirects=False)
    
    # Verify redirection status code
    assert response.status_code == 302
    
    # Verify redirection url
    location = response.headers.get("location")
    assert location is not None
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    
    # Check that necessary query parameters exist in the URL
    from urllib.parse import urlparse, parse_qs
    url_parts = urlparse(location)
    query_params = parse_qs(url_parts.query)
    assert query_params.get("response_type") == ["code"]
    assert query_params.get("scope") == ["openid email profile"]
    assert query_params.get("client_id") == ["test_client_id"]
    assert query_params.get("redirect_uri") == ["http://localhost/callback"]
    assert query_params.get("state") == ["signup"]


def fake_httpx_post_success(url, data):
    class FakeResponse:
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "sub": "google123",
                "email": "user@example.com",
                "name": "Test User",
                "picture": "http://example.com/pic.jpg"
            }
    return FakeResponse()


def fake_httpx_post_failure(url, data):
    from httpx import HTTPStatusError, Response
    fake_response = Response(400, content=b'Bad Request')
    raise HTTPStatusError(message="Error", request=None, response=fake_response)


def test_callback_success(client, monkeypatch):
    # Setup environment variables
    monkeypatch.setenv("CLIENT_ID", "test_client_id")
    monkeypatch.setenv("CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("REDIRECT_URI", "http://localhost/callback")

    # Monkey patch httpx.post to simulate successful token exchange
    monkeypatch.setattr(httpx, "post", fake_httpx_post_success)

    response = client.get("/auth/google/callback", params={"code": "valid_code"})
    assert response.status_code == 200
    data = response.json()
    assert data["google_id"] == "google123"
    assert data["email"] == "user@example.com"
    assert data["name"] == "Test User"
    assert data["profile_picture"] == "http://example.com/pic.jpg"


def test_callback_error(client):
    response = client.get("/auth/google/callback", params={"error": "access_denied"})
    assert response.status_code == 400
    data = response.json()
    assert "Google OAuth error" in data["detail"]
