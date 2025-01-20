"""Plot weekly power and heart rate distributions."""

import pypkg.plot

pypkg.plot.plot_weekly_dists(lookback_weeks=24, save=True)
pypkg.plot.plot_latest_week_dists(save=True)
