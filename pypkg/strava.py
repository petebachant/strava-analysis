"""Strava client module.

If we don't have a token and refresh token saved in the .env file,
we will go through the OAuth flow to get one.
"""

import http.server
import os
import socketserver
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

import dotenv
from stravalib.client import Client
from stravalib.exc import AccessUnauthorized

dotenv.load_dotenv()


def get_client() -> Client:
    """Check authentication and re-authenticate if necessary."""
    client = Client()
    port = 8080
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    token = os.getenv("STRAVA_TOKEN")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    expires_at = os.getenv("STRAVA_TOKEN_EXPIRES_AT")
    client.access_token = token
    client.refresh_token = refresh_token
    client.token_expires_at = expires_at
    # If we have an expired token and a refresh token, refresh and exit
    if (token is None and refresh_token is not None) or (
        expires_at is not None
        and refresh_token is not None
        and time.time() > float(expires_at)
    ):
        refresh_response = client.refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )
        access_token = refresh_response["access_token"]
        refresh_token = refresh_response["refresh_token"]
        expires_at = refresh_response["expires_at"]
        dotenv.set_key(".env", "STRAVA_TOKEN", access_token)
        dotenv.set_key(".env", "STRAVA_REFRESH_TOKEN", refresh_token)
        dotenv.set_key(".env", "STRAVA_TOKEN_EXPIRES_AT", str(expires_at))
        print("Refreshed token")
        # Check that we can get activities or if we raise AccessUnauthorized
        client.access_token = access_token
        client.refresh_token = refresh_token
        client.token_expires_at = expires_at
        try:
            resp = client.get_activities(limit=1)
            for act in resp:
                print("Fetched activity ID", act.id)
            return client
        except AccessUnauthorized:
            print("Token is invalid; reauthorizing")
    elif (
        token is not None
        and expires_at is not None
        and time.time() < float(expires_at)
    ):
        print("Token is still valid")
        return client
    authorize_url = client.authorization_url(
        client_id=client_id,
        redirect_uri=f"http://127.0.0.1:{port}/",
        scope="activity:read",
    )
    webbrowser.open(authorize_url)
    code = None

    # Spin up a temporary server to get one request
    class MyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            global code
            parsed = urlparse(self.path)
            code = parse_qs(parsed.query)["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Success! You can close this tab now.")

    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        while code is None:
            time.sleep(0.5)
            httpd.handle_request()
    # Extract the code from your webapp response
    token_response = client.exchange_code_for_token(
        client_id=client_id, client_secret=client_secret, code=code
    )
    access_token = token_response["access_token"]
    refresh_token = token_response["refresh_token"]
    expires_at = token_response["expires_at"]
    client.access_token = access_token
    client.refresh_token = refresh_token
    client.token_expires_at = expires_at
    athlete = client.get_athlete()
    print(f"Successfully authenticated athlete ID {athlete.id}")
    # Write out tokens to .env file
    dotenv.set_key(".env", "STRAVA_TOKEN", access_token)
    dotenv.set_key(".env", "STRAVA_REFRESH_TOKEN", refresh_token)
    dotenv.set_key(".env", "STRAVA_TOKEN_EXPIRES_AT", str(expires_at))
    return client
