import asyncio
import os
import signal
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import (
    RedirectResponse, HTMLResponse
)
from fastapi_mcp import FastApiMCP
from tweepy import Client, OAuth2UserHandler

load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class TwitterHandler:
    def __init__(self):
        self.refresh_token: Optional[str] = None
        self.access_token: Optional[str] = None
        self.client: Optional[Client] = None
        self.limited = False
        scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]
        client_id = os.getenv("X_CLIENT_ID")
        client_secret = os.getenv("X_CLIENT_SECRET")
        redirect_uri = f'{os.getenv("SERVER_DOMAIN")}/callback'
        if not client_id or not client_secret:
            raise ValueError("Environment variables X_CLIENT_ID and X_CLIENT_SECRET must be set")
        self.origin = OAuth2UserHandler(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scopes
        )

    def set_client(self, access_token: str):
        self.access_token = access_token
        self.client = Client(
            bearer_token=access_token,
            wait_on_rate_limit=True
        )

    def send_tweet(self, text: str) -> (bool, str):
        if self.limited:
            return False, ""
        res = self.client.create_tweet(text=text)
        if res.status_code == 429 and res.headers["x-user-limit-24hour-remaining"] == 0:
            self.limited = True
            return False, ""
        if res.status_code == 200:
            tweet_id = res.data.get("id")
            return True, tweet_id
        else:
            return False, ""


    def refresh(self):
        token = self.origin.refresh_token(token_url="https://api.twitter.com/2/oauth2/token", refresh_token=self.refresh_token)
        self.access_token = token["access_token"]
        self.refresh_token = token.get("refresh_token", "")
        self.set_client(self.access_token)
        self.limited = False


app = FastAPI()
twitter_handle = TwitterHandler()

# 显式 operation_id（工具将被命名为 "get_user_info"）
@app.get("/users/{user_id}", operation_id="get_user_info")
async def read_user(user_id: int):
    return {"user_id": user_id}

@app.get("/auth", operation_id="auth_twitter")
async def auth_twitter():
    authorization_url = twitter_handle.origin.get_authorization_url()
    return RedirectResponse(url=authorization_url)

@app.get("/callback", operation_id="callback_twitter")
async def callback_twitter(request: Request):
    try:
        authorization_response = str(request.url)
        token = twitter_handle.origin.fetch_token(authorization_response=authorization_response)
        access_token = token["access_token"]
        refresh_token = token.get("refresh_token", "")
        twitter_handle.set_client(access_token)
        twitter_handle.refresh_token = refresh_token
        # Notice user auth should set to False, to avoid use oauth1.0
        user = twitter_handle.client.get_me(user_auth=False).data
        return HTMLResponse(
        f"Authentication successful! User ID: {user.id}, Username: {user.username}, access token: {access_token}, refresh_token: {refresh_token}"
    )
    except Exception as e:
        print(f"Error during callback: {e}")
        return HTMLResponse(f"Authentication failed: {e}", status_code=500)

@app.get("/refresh", operation_id="refresh_x_access_token")
async def refresh_twitter_access_token():
    try:
        twitter_handle.refresh()
        return HTMLResponse(f"refresh token: {twitter_handle.refresh_token}, access token {twitter_handle.access_token}")
    except Exception as e:
        return HTMLResponse(f"Refresh access token failed: {e}", status_code=500)


if __name__ == '__main__':

    mcp = FastApiMCP(app, exclude_operations=['auth_twitter', 'callback_twitter'])

    mcp.mount()
    loop = asyncio.get_event_loop()

    # Add signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: ())

    try:
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT")))
    except Exception as e:
        print(f"Error during server run: {e}")
    finally:
        loop.close()
        print("Event loop closed.")
