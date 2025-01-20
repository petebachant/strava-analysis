"""Plotting."""

import duckdb
import plotly.graph_objects as go
import polars as pl
from plotly.subplots import make_subplots
import calkit
import os

POWER_BINS = [-1, 138, 188, 225, 263, 300, 375, 1000]
HR_BINS = [0, 106, 140, 157, 174, 210]
FIGS_DIR = "figures"


def check_figs_dir():
    os.makedirs(FIGS_DIR, exist_ok=True)


def get_ts_data(lookback_weeks=52) -> pl.DataFrame:
    return (
        duckdb.sql(
            f"""
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
            where activities.start_date >= (
                date_trunc('week', current_timestamp)
                - INTERVAL {lookback_weeks * 7} DAYS
            )
            order by ts asc
        """,
        )
        .pl()
        .with_columns(
            power_zone=pl.col("watts").cut(breaks=POWER_BINS),
            hr_zone=pl.col("heartrate").cut(breaks=HR_BINS),
        )
    )


def plot_weekly_dists(lookback_weeks=12, save=True) -> go.Figure:
    lookback_days = 7 * lookback_weeks
    df = get_ts_data(lookback_weeks=lookback_weeks)
    # Get weekly energy expenditure
    dfe = duckdb.sql(
        f"""
            select
                date_trunc('week', start_date) as week_start,
                sum(kilojoules) as energy
            from 'data/activities/*.json'
            where start_date >= (
                date_trunc('week', current_timestamp)
                - INTERVAL {lookback_days} DAYS
            )
            group by week_start
            order by week_start
        """
    ).pl()
    dfg_power = (
        df.drop_nulls(subset=["ts", "power_zone"])
        .group_by_dynamic(
            index_column="ts",
            every="1w",
            group_by="power_zone",
        )
        .agg(pl.len())
        .sort(["ts", "power_zone"])
        .with_columns(hours=pl.col("len") / 3600)
        .rename(dict(ts="week_start", len="seconds"))
    )
    power_bin = (
        dfg_power["power_zone"]
        .cast(str)
        .str.split(",")
        .list.get(0)
        .str.replace("(", "", literal=True)
        .str.strip_chars()
        .cast(float)
    )
    dfg_hr = (
        df.drop_nulls(subset=["ts", "hr_zone"])
        .group_by_dynamic(
            index_column="ts",
            every="1w",
            group_by="hr_zone",
        )
        .agg(pl.len())
        .sort(["ts", "hr_zone"])
        .with_columns(hours=pl.col("len") / 3600)
        .rename(dict(ts="week_start", len="seconds"))
    )
    hr_bin = (
        dfg_hr["hr_zone"]
        .cast(str)
        .str.split(",")
        .list.get(0)
        .str.replace("(", "", literal=True)
        .str.strip_chars()
        .cast(float)
    )
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
    fig.add_trace(go.Bar(x=dfe["week_start"], y=dfe["energy"], name="Energy"))
    fig.add_trace(
        go.Bar(
            x=dfg_power["week_start"],
            y=dfg_power["hours"],
            marker=dict(color=power_bin, colorscale="YlOrRd"),
            name="Power",
            hovertext=dfg_power["power_zone"],
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=dfg_hr["week_start"],
            y=dfg_hr["hours"],
            marker=dict(color=hr_bin, colorscale="YlOrRd"),
            name="HR",
            hovertext=dfg_hr["hr_zone"],
        ),
        row=3,
        col=1,
    )
    # Update x-axis titles
    fig.update_xaxes(title_text="Week start date", row=3, col=1)
    # Update y-axis titles
    fig.update_yaxes(title_text="Energy (kJ)", row=1, col=1)
    fig.update_yaxes(title_text="Hours in PZ", row=2, col=1)
    fig.update_yaxes(title_text="Hours in HRZ", row=3, col=1)
    fig.update_layout(showlegend=False, margin=dict(t=30, b=35, r=30))
    if save:
        fpath = f"{FIGS_DIR}/weekly-dists-{lookback_weeks}-weeks.json"
        check_figs_dir()
        fig.write_json(fpath)
    return fig


def plot_latest_week_dists(save=True) -> go.Figure:
    df = get_ts_data(lookback_weeks=1)
    dfg_power = (
        df.drop_nulls(subset=["ts", "power_zone"])
        .group_by_dynamic(
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
        df.drop_nulls(subset=["ts", "hr_zone"])
        .group_by_dynamic(
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
    week_start = latest_week
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
    if save:
        outpath = f"{FIGS_DIR}/dists-latest-week.json"
        check_figs_dir()
        fig.write_json(outpath)
        # Update the first figure in calkit.yaml to have this path
        ck_info = calkit.load_calkit_info()
        ck_info["figures"][0]["title"] = (
            "Power and heart rate distributions for the latest week "
            f"(starting {latest_week.date()})"
        )
        with open("calkit.yaml", "w") as f:
            calkit.ryaml.dump(ck_info, f)
    return fig
