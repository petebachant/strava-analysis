# Strava analysis

[![DOI](https://zenodo.org/badge/DOI/10.5072/zenodo.165874.svg)](https://handle.stage.datacite.org/10.5072/zenodo.165874)

Collecting and analyzing data from Strava.
The pipeline is designed to be run approximately daily,
and will continuously accumulate data from new Strava activities.

## Setup

If you look at the `dependencies` in `calkit.yaml` you'll see you need to
define two environmental variables,
`STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`.
These can be obtained when you 
[create your own Strava app to interact with the API](https://www.strava.com/settings/api).
They can then be placed in a `.env` file in this directory,
or you can call:

```sh
calkit set-env-var STRAVA_CLIENT_ID ...
calkit set-env-var STRAVA_CLIENT_SECRET ...
```
