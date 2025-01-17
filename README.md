# Strava analysis

Collecting and analyzing data from Strava.

## How it works

If you look at the `dependencies` in `calkit.yaml` you'll see you need to
define two environmental variables,
`STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`.
These can be obtained when you create your own Strava app to interact with
the API.
They can then be placed in a `.env` file in this directory,
or you can call:

```sh
calkit set-env-var STRAVA_CLIENT_ID ...
calkit set-env-var STRAVA_CLIENT_SECRET ...
```

## Pipeline

Raw time series, or "stream" data is downloaded for every Strava
activity,
and these are aggregated and stored in a Hive-partitioned dataset
using the parquet file format.

In order to not duplicate work,
activities that have already been processed are kept in an on-disk queue.

This dataset is then used for further analysis.
