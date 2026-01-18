"""
Activity analysis for WhatsApp chat data.
"""

import numpy as np
import pandas as pd
import altair as alt
from scipy.ndimage import gaussian_filter


def activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate activity percentage for each author.

    Activity is defined as the percentage of days (since first message)
    on which the author sent at least one message.

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with author and Activity % columns
    """
    distinct_dates = df[["date"]].drop_duplicates()
    distinct_authors = df[["author"]].drop_duplicates()
    distinct_authors['key'] = 1
    distinct_dates['key'] = 1
    distinct_dates = pd.merge(
        distinct_dates, distinct_authors,
        on="key",
        how="left"
    ).drop("key", axis=1)

    activity_df = pd.DataFrame(
        df.groupby(["author", "date"])["words"].nunique()
    ).reset_index()
    activity_df["start_date"] = activity_df.groupby(["author"])["date"].transform("min")
    activity_df["is_active"] = np.where(activity_df['words'] > 0, 1, 0)

    distinct_dates = pd.merge(
        distinct_dates, activity_df,
        on=["date", "author"],
        how="left"
    )
    distinct_dates["max_date"] = df.date.max()
    distinct_dates[['max_date', 'start_date']] = distinct_dates[
        ['max_date', 'start_date']
    ].apply(pd.to_datetime)
    distinct_dates["date_diff"] = (
        distinct_dates['max_date'] - distinct_dates['start_date']
    ).dt.days

    o = distinct_dates.groupby("author", as_index=False).agg({
        "is_active": "sum",
        "date_diff": "max"
    })
    o["is_active_percent"] = 100 * (o["is_active"] / o["date_diff"])

    return o.reset_index().drop(["is_active", "date_diff"], axis=1).rename(
        columns={"is_active_percent": "Activity %"}
    )


def smoothed_daily_activity(df: pd.DataFrame, years: int = 3) -> pd.DataFrame:
    """
    Calculate Gaussian-smoothed daily activity.

    Args:
        df: Preprocessed DataFrame
        years: Number of years to include (default 3)

    Returns:
        Smoothed daily activity DataFrame
    """
    df = df.copy()
    df["year"] = df["timestamp"].dt.year
    min_year = df.year.max() - years

    daily_activity_df = df.loc[df["year"] > min_year].groupby(
        ['author', 'timestamp']
    ).first().unstack(level=0).resample('D').sum().msg_length.fillna(0)

    smoothed_daily_activity_df = pd.DataFrame(
        gaussian_filter(daily_activity_df, (6, 0)),
        index=daily_activity_df.index,
        columns=daily_activity_df.columns
    )

    return smoothed_daily_activity_df


def relative_activity_ts(df: pd.DataFrame, years: int = 3) -> pd.DataFrame:
    """
    Calculate relative activity time series (normalized by total daily activity).

    Args:
        df: Preprocessed DataFrame
        years: Number of years to include (default 3)

    Returns:
        Relative activity DataFrame (each row sums to 1)
    """
    min_year = df.year.max() - years

    daily_activity_df = df.loc[df["year"] > min_year].groupby(
        ['author', 'timestamp']
    ).first().unstack(level=0).resample('D').sum().msg_length.fillna(0)

    smoothed_daily_activity_df = pd.DataFrame(
        gaussian_filter(daily_activity_df, (6, 0)),
        index=daily_activity_df.index,
        columns=daily_activity_df.columns
    )

    o = smoothed_daily_activity_df.div(
        smoothed_daily_activity_df.sum(axis=1),
        axis=0
    )
    return o


def get_activity_stats(df: pd.DataFrame) -> dict:
    """
    Get activity statistics and chart.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with:
        - most_active: Most active author name
        - most_active_perc: Activity percentage
        - data: Activity DataFrame
        - chart: Altair chart
    """
    o = activity(df)
    most_active = o.sort_values("Activity %", ascending=False).iloc[0]['author']
    most_active_perc = o.sort_values("Activity %", ascending=False).iloc[0]['Activity %']

    c = alt.Chart(o).mark_bar().encode(
        x=alt.X("author:N", sort="-y"),
        y=alt.Y('Activity %:Q'),
        color='author',
    )
    rule = alt.Chart(o).mark_rule(color='red').encode(
        y='mean(Activity %):Q'
    )
    chart = (c + rule).properties(
        width=600,
        height=600,
        title='Activity % by author'
    )

    return {
        'most_active': most_active,
        'most_active_perc': most_active_perc,
        'data': o,
        'chart': chart
    }
