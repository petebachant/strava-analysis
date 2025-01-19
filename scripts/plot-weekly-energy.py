"""Plot weekly energy consumption."""

import duckdb

duckdb.sql(
    """
        select
            date_trunc('week', start_date) as week_start,
            sum(kilojoules)
        from 'data/activities/*.json'
        group by week_start
        order by week_start
    """
).df().set_index("week_start").plot(backend="plotly").update_layout(
    showlegend=False,
    yaxis_title="Energy expenditure (kJ)",
    xaxis_title="Week start date",
).write_json("figures/weekly-energy.json")
