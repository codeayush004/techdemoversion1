import os
import requests
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth")

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

@router.get("/github/login")
def github_login():
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID not configured")
    
    # We request 'repo' scope to access private repositories
    # We also request 'read:user' to get basic profile info if needed
    scope = "repo read:user"
    github_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope={scope}"
    return RedirectResponse(github_url)

@router.get("/github/callback")
def github_callback(code: str):
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OAuth credentials not configured")

    # Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }

    resp = requests.post(token_url, headers=headers, data=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    token_data = resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        error_desc = token_data.get("error_description", "Unknown error")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {error_desc}")

    # Instead of a simple redirect, we return a script that sends the token back to the opener window
    # This is a common pattern for "Login with..." popups
    html_content = f"""
    <html>
        <body>
            <script>
                window.opener.postMessage({{ type: 'GITHUB_AUTH_SUCCESS', token: '{access_token}' }}, "*");
                window.close();
            </script>
            <p>Authentication successful! Closing window...</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
