"""Get data from the Strava API."""

import os
import warnings

import duckdb
import polars as pl
from stravalib import Client

client = Client(access_token=os.getenv("STRAVA_TOKEN"))
start_date = "2024-01-01"

outdir_act = "data/activities"
os.makedirs(outdir_act, exist_ok=True)

# Read the latest activity and set start date after that
try:
    start_date = duckdb.sql(
        "select max(start_date) from data/activities/*.json"
    ).fetchall()[0]
except Exception as e:
    warnings.warn(f"Could not detect latest activity date: {e}")

resp = client.get_activities(after=start_date)
i = 0

for activity in resp:
    i += 1
    print(f"[{i}] Working on activity ID: {activity.id}")
    # Write the time series data first
    streams = client.get_activity_streams(activity_id=activity.id)
    data = {}
    for varname, stream in streams.items():
        data[varname] = stream.data
    fpath = f"data/timeseries/activity_id={activity.id}/data.parquet"
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    df = pl.DataFrame(data)
    df.write_parquet(fpath)
    # Now write the activity as JSON
    fpath = f"{outdir_act}/{activity.id}.json"
    with open(fpath, "w") as f:
        f.write(activity.model_dump_json())
