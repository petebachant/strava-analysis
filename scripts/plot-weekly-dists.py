"""Plot weekly power and heart rate distributions."""

import os

import duckdb
import plotly.graph_objects as go
import polars as pl
from plotly.subplots import make_subplots
from tqdm import tqdm

power_bins = [-1, 138, 188, 225, 263, 300, 375, 1000]
hr_bins = [0, 106, 140, 157, 174, 210]

fig_dir = "figures/weekly-dists"
os.makedirs(fig_dir, exist_ok=True)

df = duckdb.sql(
    """
        select
            start_date + INTERVAL (time) SECONDS AS ts,
            timeseries.*
        from read_parquet(
            'data/timeseries/**/*.parquet', union_by_name = true
        ) timeseries
        left join (
            select * from 'data/activities/*.json'
        ) activities
        on activities.id = timeseries.activity_id
        where sport_type = 'Ride'
        and watts is not null
        -- and ts > '2024-06-01'
        order by ts asc
    """,
).pl()

df = df.with_columns(
    power_zone=pl.col("watts").cut(breaks=power_bins),
    hr_zone=pl.col("heartrate").cut(breaks=hr_bins),
)

dfg_power = (
    df.group_by_dynamic(
        index_column="ts",
        every="1w",
        group_by="power_zone",
    )
    .agg(pl.len())
    .sort(["ts", "power_zone"])
    .with_columns(hours=pl.col("len") / 3600)
    .rename(dict(ts="week_start", len="seconds"))
)

dfg_hr = (
    df.group_by_dynamic(
        index_column="ts",
        every="1w",
        group_by="hr_zone",
    )
    .agg(pl.len())
    .sort(["ts", "hr_zone"])
    .with_columns(hours=pl.col("len") / 3600)
    .rename(dict(ts="week_start", len="seconds"))
)

latest_week = dfg_power["week_start"].max()

for week_start in tqdm(dfg_power["week_start"].unique()):
    df1_p = dfg_power.filter(pl.col("week_start") == week_start)
    df1_hr = dfg_hr.filter(pl.col("week_start") == week_start)
    fig = make_subplots(rows=1, cols=2)
    fig.add_trace(
        go.Bar(x=df1_p["power_zone"], y=df1_p["hours"], name="Power"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(x=df1_hr["hr_zone"], y=df1_hr["hours"], name="HR"),
        row=1,
        col=2,
    )
    # Update x-axis titles
    fig.update_xaxes(title_text="Power (W)", row=1, col=1)
    fig.update_xaxes(title_text="Heart rate (BPM)", row=1, col=2)
    # Update y-axis titles
    fig.update_yaxes(title_text="Hours", row=1, col=1)
    fig.update_yaxes(title_text=None, row=1, col=2)
    fig.update_layout(showlegend=False, margin=dict(t=40))
    if week_start == latest_week:
        outpath = f"{fig_dir}/latest.json"
    else:
        outpath = f"{fig_dir}/{week_start.date()}.json"
    fig.write_json(outpath)
