import os
import logging
from typing import Optional

import httpx
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/auth/google/signup")
async def google_signup():
    try:
        client_id = os.getenv("CLIENT_ID")
        redirect_uri = os.getenv("REDIRECT_URI")
        state = "signup"
        if not client_id or not redirect_uri:
            raise HTTPException(status_code=500, detail="OAuth configuration is missing.")
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        query_params = {
            "response_type": "code",
            "scope": "openid email profile",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state
        }
        url = f"{google_auth_url}?{urlencode(query_params)}"
        return RedirectResponse(url, status_code=302)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate Google OAuth URL.")

@router.get("/auth/google/callback")
async def google_callback(code: Optional[str] = None, error: Optional[str] = None):
    if error:
        logging.error(f"Error during Google OAuth callback: {error}")
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided.")
    try:
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        redirect_uri = os.getenv("REDIRECT_URI")
        if not client_id or not client_secret or not redirect_uri:
            raise HTTPException(status_code=500, detail="OAuth configuration is missing.")
        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        token_response = httpx.post("https://oauth2.googleapis.com/token", data=payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        user_data = {
            "google_id": token_data.get("sub"),
            "email": token_data.get("email"),
            "name": token_data.get("name"),
            "profile_picture": token_data.get("picture")
        }
        return user_data
    except httpx.HTTPStatusError as http_err:
        logging.error(http_err, exc_info=True)
        raise HTTPException(status_code=http_err.response.status_code, detail="Token exchange failed with Google.")
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to exchange token.")
