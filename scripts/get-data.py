"""Get data from the Strava API."""

import os
import time

import dotenv
from stravalib import Client

dotenv.load_dotenv(".env")

client = Client()

client_id = os.getenv("STRAVA_CLIENT_ID")
client_secret = os.getenv("STRAVA_CLIENT_SECRET")
access_token = os.getenv("STRAVA_TOKEN")
refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
expires_at = os.getenv("STRAVA_TOKEN_EXPIRES_AT")

# If we have an expired token and a refresh token, refresh and exit
if time.time() > float(expires_at):
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

client.access_token = access_token
assert client.access_token is not None
client.refresh_token = refresh_token
client.token_expired_at = expires_at

# TODO: Load activities table into memory and fetch only those newer than
# the latest

resp = client.get_activities(after="2025-01-01")  # TODO: Parameterize

for activity in resp:
    streams = client.get_activity_streams(activity_id=activity.id)
    data = {}
    for varname, stream in streams.items():
        data[varname] = streams.data

# TODO: Write out raw data somewhere
