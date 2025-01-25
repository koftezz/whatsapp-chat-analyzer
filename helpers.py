import streamlit as st
import pandas as pd
import numpy as np
from chatminer.chatparsers import WhatsAppParser
import tempfile
import chatminer.visualizations as vis
from scipy.ndimage import gaussian_filter
import math
from collections import Counter
from scipy import stats
import altair as alt
import emoji
from wordcloud import WordCloud
import re


@st.cache_data(show_spinner=False)
def read_file(file):
    with tempfile.NamedTemporaryFile(mode="wb") as temp:
        with st.spinner('This may take a while. Wait for it...'):
            bytes_data = file.getvalue()
            temp.write(bytes_data)
            parser = WhatsAppParser(temp.name)
            parser.parse_file()
            df = parser.parsed_messages.get_df()
    return df

def get_most_active_author(df: pd.DataFrame):
    author_message_counts = df.groupby('author', as_index=False)["message"].count().reset_index()
    most_active_author = author_message_counts.sort_values("message", ascending=False).iloc[0]
    return most_active_author['author'], most_active_author['message']

def preprocess_data(df: pd.DataFrame, selected_lang: str, selected_authors: list):
    lang = get_language_settings(selected_lang)
    df = preprocess_timestamps(df, selected_authors)
    df = process_links(df)
    df = process_message_length(df)
    df = process_multimedia(df, lang)
    df = process_emojis(df)
    df = filter_authors(df)
    df = add_conversation_starter_flag(df)
    df, locations = process_locations(df)
    df = add_year_week(df)
    return df, locations

def add_year_week(df: pd.DataFrame):
    df['year'] = df['timestamp'].dt.year
    df['week'] = df['timestamp'].dt.isocalendar().week
    return df

def process_emojis(df: pd.DataFrame):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    def search_emoji(x):
        if isinstance(x, str):
            return bool(emoji_pattern.search(x))
        return False
    
    df['is_emoji'] = df['message'].apply(search_emoji).astype(int)
    #df.loc[df['is_emoji'] == 1, 'message'] = np.nan
    return df

def get_language_settings(selected_lang: str):
    lang = {
        "English": {
            "image": "image omitted",
            "video": "video omitted",
            "gif": "GIF omitted",
            "audio": "audio omitted",
            "sticker": "sticker omitted",
            "deleted": ["This message was deleted.", "You deleted this message."],
            "location": "Location https://"
        },
        "Turkish": {
            "image": "görüntü dahil edilmedi",
            "video": "video dahil edilmedi",
            "gif": "GIF dahil edilmedi",
            "audio": "ses dahil edilmedi",
            "sticker": "Çıkartma dahil edilmedi",
            "deleted": ["Bu mesaj silindi.", "Bu mesajı sildiniz."],
            "location": "Konum https://"
        },
        "German": {
            "image": "Bild weggelassen",
            "video": "Video weggelassen",
            "gif": "GIF weggelassen",
            "audio": "Audio weggelassen",
            "sticker": "Sticker weggelassen",
            "deleted": ["Diese Nachricht wurde gelöscht.", "Du hast diese Nachricht gelöscht."],
            "location": "Standort https://"
        }
    }
    return lang[selected_lang]

def preprocess_timestamps(df: pd.DataFrame, selected_authors: list):
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
    df["date"] = df["timestamp"].dt.strftime('%Y-%m-%d')
    df = df.loc[df["author"].isin(selected_authors)]
    return df.sort_values(["timestamp"])

def process_locations(df: pd.DataFrame):
    df["is_location"] = (df.message.str.contains('maps.google') == True) * 1
    locations = df.loc[df["is_location"] == 1]
    df.loc[df.is_location == 1, 'message'] = np.nan

    if locations.shape[0] > 0:
        locs = locations["message"].str.split(" ", expand=True)
        locs[1] = locs[1].str[27:]
        locs = locs[1].str.split(",", expand=True)
        locs = locs.rename(columns={0: "lat", 1: "lon"})
        locs = locs.loc[(locs["lat"] != "") & (locs["lon"] != "") & (~locs["lat"].isna()) & (~locs["lon"].isna())]
        locations = locs[["lat", "lon"]].astype(float).drop_duplicates()
    
    return df, locations

def process_links(df: pd.DataFrame):
    df['is_link'] = ~df.message.str.extract('(https?:\S*)', expand=False).isnull() * 1
    return df

def process_message_length(df: pd.DataFrame):
    df['msg_length'] = df.message.str.len()
    df.loc[df.is_link == 1, 'msg_length'] = np.nan
    return df

def process_multimedia(df: pd.DataFrame, lang: dict):
    multimedia_types = ['image', 'video', 'gif', 'sticker', 'audio']
    for media_type in multimedia_types:
        column_name = f'is_{media_type}'
        df[column_name] = (df.message == lang[media_type]) * 1
        df.loc[df[column_name] == 1, 'message'] = np.nan

    df['is_deleted'] = (df.message.isin(lang["deleted"])) * 1
    df.loc[df.is_deleted == 1, 'message'] = np.nan
    return df

def filter_authors(df: pd.DataFrame):
    return df[~(~df.author.str.extract('(\+)', expand=False).isnull() | df.author.isnull())]

def add_conversation_starter_flag(df: pd.DataFrame):
    df['is_conversation_starter'] = ((df.timestamp - df.timestamp.shift(1)) > pd.Timedelta('7 hours')) * 1
    return df


def basic_stats(df: pd.DataFrame):
    # Remove 'hour' column if it exists
    if 'hour' in df.columns:
        df = df.drop("hour", axis=1)
    
    # Calculate mean values for each author
    df_mean = df.groupby('author').mean()

    # Define column renaming dictionary
    rename_dict = {
        "words": "Words",
        "msg_length": "Message Length",
        "letters": "Letters",
        "is_link": "Link",
        "is_conversation_starter": "Is Conversation Starter",
        "is_image": "Image",
        "is_video": "Video",
        "is_gif": "GIF",
        "is_audio": "Audio",
        "is_sticker": "Sticker",
        "is_deleted": "Deleted",
        "is_emoji": "Emoji",
        "is_location": "Location",
    }
    
    # Only rename columns that exist in the DataFrame
    rename_dict = {k: v for k, v in rename_dict.items() if k in df_mean.columns}
    
    # Select only columns that are in the rename_dict
    df_renamed = df_mean[list(rename_dict.keys())].rename(columns=rename_dict)
    # Define formatting dictionary
    format_dict = {
        'Words': '{:.2f}',
        'Message Length': '{:.1f}',
        'Letters': '{:.1f}',
        'Link': '{:.2%}',
        'Is Conversation Starter': '{:.2%}',
        'Image': '{:.2%}',
        'Video': '{:.2%}',
        'GIF': '{:.2%}',
        'Audio': '{:.2%}',
        'Sticker': '{:.2%}',
        'Deleted': '{:.2%}',
        'Location': '{:.2%}',
        'Emoji': '{:.2%}'
    }
    
    # Only format columns that exist in the DataFrame
    format_dict = {k: v for k, v in format_dict.items() if k in df_renamed.columns}
    
    # Apply styling
    styled_df = df_renamed.style.format(format_dict).background_gradient(axis=0)
    
    return styled_df


def stats_overall(df: pd.DataFrame):
    authors = df[["author"]].drop_duplicates()
    
    # List of columns to process
    columns = [
        "is_image", "is_video", "is_link", "is_conversation_starter",
        "is_gif", "is_audio", "is_sticker", "is_deleted", "is_location", "is_emoji"
    ]
    
    # Function to process each column
    def process_column(col):
        temp = df.loc[df[col] == 1]
        return pd.DataFrame(temp.groupby("author")[col].sum() / temp[col].sum()).reset_index()
    
    # Process all columns
    processed_dfs = {col: process_column(col) for col in columns}
    
    # Merge all processed dataframes with authors
    for col, processed_df in processed_dfs.items():
        authors = pd.merge(authors, processed_df, on=["author"], how="left")
    
    # Fill NaN values and rename columns
    authors = authors.fillna({col: 0 for col in columns})
    
    column_rename = {
        "is_link": "Link",
        "is_conversation_starter": "Is Conversation Starter",
        "is_image": "Image",
        "is_video": "Video",
        "is_gif": "GIF",
        "is_audio": "Audio",
        "is_sticker": "Sticker",
        "is_deleted": "Deleted",
        "is_location": "Location",
        "is_emoji": "Emoji"
    }
    
    authors = authors.rename(columns=column_rename)
    
    # Apply styling
    authors = authors.style.format({
        col: '{:.2%}' for col in column_rename.values()
    }).background_gradient(axis=0)
    
    return authors


def smoothed_daily_activity(df: pd.DataFrame, years: int = 3):
    df["year"] = df["timestamp"].dt.year
    min_year = df.year.max() - years
    daily_activity_df = df.loc[df["year"] > min_year].groupby(
        ['author',
         'timestamp']).first().unstack(
        level=0).resample('D').sum().msg_length.fillna(0)

    smoothed_daily_activity_df = pd.DataFrame(
        gaussian_filter(daily_activity_df,
                        (6, 0)),
        index=daily_activity_df.index,
        columns=daily_activity_df.columns)
    # fig, ax = plt.subplots()
    # subplots = daily_activity_df.plot(figsize=[8,2*len(df.author.unique())],
    #                         subplots=True, sharey=True, lw=0.3, label=None)
    # ax = smoothed_daily_activity_df.plot(figsize=[8, 2*len(
    #     df.author.unique())], subplots=True, ax=ax)
    # [ax.set_title(auth) for auth, ax in zip(df.groupby('author').size().index, subplots)]
    # [ax.set_ylabel('Activity (characters per day)') for auth, ax in zip(df.groupby('author').size().index, subplots)]
    # plt.xlabel('')
    # [ax.legend(['Daily activity', 'Gaussian-smoothed']) for ax in subplots]
    # [ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ','))) for ax in subplots]
    # plt.tight_layout()
    # plt.subplots_adjust(wspace=10, hspace=10)
    # st.pyplot(fig)
    return smoothed_daily_activity_df


def activity(df: pd.DataFrame):
    distinct_dates = df[["date"]].drop_duplicates()
    distinct_authors = df[["author"]].drop_duplicates()
    distinct_authors['key'] = 1
    distinct_dates['key'] = 1
    distinct_dates = pd.merge(distinct_dates, distinct_authors,
                              on="key",
                              how="left").drop(
        "key", 1)
    activity = pd.DataFrame(
        df.groupby(["author", "date"])[
            "words"].nunique()).reset_index()
    activity["start_date"] = activity.groupby(["author"])[
        "date"].transform(
        "min")
    activity["is_active"] = np.where(activity['words'] > 0, 1, 0)
    distinct_dates = pd.merge(distinct_dates, activity,
                              on=["date", "author"],
                              how="left")
    distinct_dates["max_date"] = df.date.max()
    distinct_dates[['max_date', 'start_date']] = distinct_dates[
        ['max_date', 'start_date']].apply(pd.to_datetime)
    distinct_dates["date_diff"] = (
            distinct_dates['max_date'] - distinct_dates[
        'start_date']).dt.days
    o = distinct_dates.groupby("author", as_index=False).agg(
        {"is_active": "sum", "date_diff": "max"})
    o["is_active_percent"] = 100 * (o["is_active"] / o["date_diff"])
    return o.reset_index().drop(["is_active", "date_diff"], 1) \
        .rename(columns={
        "is_active_percent": "Activity %"
    }
    )

def relative_activity_ts(df: pd.DataFrame, years: int = 3):
    min_year = df.year.max() - years
    daily_activity_df = df.loc[df["year"] > min_year].groupby(
        ['author', 'timestamp']).first().unstack(level=0).resample(
        'D').sum().msg_length.fillna(0)
    smoothed_daily_activity_df = pd.DataFrame(
        gaussian_filter(daily_activity_df, (6, 0)),
        index=daily_activity_df.index,
        columns=daily_activity_df.columns)
    o = smoothed_daily_activity_df.div(
        smoothed_daily_activity_df.sum(axis=1),
        axis=0)
    return o


def activity_day_of_week_ts(df: pd.DataFrame):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    o = df.groupby([df.timestamp.dt.dayofweek, df.author])['msg_length'].sum().unstack(fill_value=0)
    o.index = pd.CategoricalIndex(o.index.map(lambda x: days[x]), categories=days, ordered=True)
    o = o.sort_index()
    
    # Normalize the data for each author
    o_normalized = o.div(o.sum(axis=0), axis=1)
    
    # Explicitly name the index
    o_normalized.index.name = 'day_of_week'
    
    # Convert the DataFrame to a format suitable for Altair
    o_melted = o_normalized.reset_index().melt(id_vars='day_of_week', var_name='author', value_name='activity')
    
    # Create Altair chart
    chart = alt.Chart(o_melted).mark_rect().encode(
        x=alt.X('day_of_week:N', sort=days, title='Day of Week'),
        y=alt.Y('author:N', title='Author'),
        color=alt.Color('activity:Q', scale=alt.Scale(scheme='viridis'), title='Activity'),
        tooltip=[
            alt.Tooltip('day_of_week:N', title='Day'),
            alt.Tooltip('author:N', title='Author'),
            alt.Tooltip('activity:Q', title='Activity', format='.1%')
        ]
    ).properties(
        width=600,
        height=400,
        title='Activity Distribution by Day of Week'
    )
    
    # Add text labels
    text = chart.mark_text(baseline='middle').encode(
        text=alt.Text('activity:Q', format='.1%'),
        color=alt.condition(
            alt.datum.activity > 0.15,
            alt.value('white'),
            alt.value('black')
        )
    )
    
    return chart + text


def activity_time_of_day_ts(df: pd.DataFrame):
    # Group by hour and minute, sum message lengths
    a = df.groupby([df.timestamp.dt.hour, df.timestamp.dt.minute, 'author'])['msg_length'].sum().unstack(fill_value=0)
    
    # Create a complete time index
    time_index = pd.date_range("2000-01-01", "2000-01-02", freq="1min")[:-1]
    
    # Reindex to fill missing times with 0
    a = a.reindex(pd.MultiIndex.from_product([range(24), range(60)], names=['hour', 'minute']), fill_value=0)
    
    # Temporarily add the tail at the start and head at the end for continuous smoothing
    a = pd.concat([a.tail(120), a, a.head(120)])
    
    # Apply gaussian convolution
    smoothed = pd.DataFrame(gaussian_filter(a.values, (60, 0)), index=a.index, columns=a.columns)
    
    # Remove the temporarily added points
    smoothed = smoothed.iloc[120:-120]
    
    # Reset index and prepare for plotting
    smoothed = smoothed.reset_index()
    smoothed['time'] = pd.to_datetime(smoothed['hour'].astype(str) + ':' + smoothed['minute'].astype(str).str.zfill(2))
    
    # Melt the dataframe for Altair
    melted = smoothed.melt(id_vars=['hour', 'minute', 'time'], var_name='author', value_name='activity')
    
    # Create Altair chart
    chart = alt.Chart(melted).mark_line().encode(
        x=alt.X('time:T', title='Time of Day', axis=alt.Axis(format='%H:%M')),
        y=alt.Y('activity:Q', title='Activity'),
        color=alt.Color('author:N', title='Author')
    ).properties(
        width=800,
        height=400,
        title='Activity by Time of Day'
    )
    
    return chart

def response_matrix(df: pd.DataFrame):
    # Calculate time difference and same author flag
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    df['same_author'] = df['author'] == df['author'].shift()

    # Filter out self-responses within 3 minutes
    response_data = df[~((df['time_diff'] < 180) & df['same_author'])]

    # Create response matrix
    response_matrix = pd.crosstab(
        response_data['author'],
        response_data['author'].shift(),
        normalize='index'
    )

    # Prepare data for Altair
    matrix_melted = response_matrix.reset_index().melt(
        id_vars='author',
        var_name='responding_to',
        value_name='response_rate'
    )

    # Create Altair heatmap
    heatmap = alt.Chart(matrix_melted).mark_rect().encode(
        x=alt.X('responding_to:N', title='Responding to', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('author:N', title='Message author'),
        color=alt.Color('response_rate:Q', scale=alt.Scale(scheme='viridis')),
        tooltip=[
            alt.Tooltip('author:N', title='Message author'),
            alt.Tooltip('responding_to:N', title='Responding to'),
            alt.Tooltip('response_rate:Q', title='Response rate', format='.1%')
        ]
    ).properties(
        title='Response Matrix'
    )

    # Add text labels
    text = heatmap.mark_text(baseline='middle').encode(
        text=alt.Text('response_rate:Q', format='.0%'),
        color=alt.condition(
            alt.datum.response_rate > 0.5,
            alt.value('white'),
            alt.value('black')
        )
    )

    return (heatmap + text).configure_view(
        strokeWidth=0
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    )

def find_longest_consecutive_streak(df: pd.DataFrame):
    # Ensure the dataframe is sorted by timestamp
    df = df.sort_values('timestamp')
    
    # Create a new column to identify changes in author
    df['author_change'] = (df['author'] != df['author'].shift()).cumsum()
    
    # Group by the author and the change indicator
    grouped = df.groupby(['author', 'author_change'])
    
    # Find the group with the maximum count
    streak_info = grouped.size().reset_index(name='streak_length')
    longest_streak = streak_info.loc[streak_info['streak_length'].idxmax()]
    
    max_spammer = longest_streak['author']
    max_spam = longest_streak['streak_length']
    
    # Get the start and end times of the longest streak
    streak_data = grouped.get_group((max_spammer, longest_streak['author_change']))
    start_time = streak_data['timestamp'].min()
    end_time = streak_data['timestamp'].max()
    
    # Select relevant columns for display
    streak_messages = streak_data[['timestamp', 'author', 'message']]
    
    return {
        'author': max_spammer,
        'streak_length': max_spam,
        'start_time': start_time,
        'end_time': end_time,
        'streak_messages': streak_messages
    }


def year_month(df: pd.DataFrame):
    df[
        'YearMonth'] = df.timestamp.dt.year * 100 + df.timestamp.dt.month
    year_content = df.groupby(["year", 'YearMonth'], as_index=False).count()[
        ["year", 'YearMonth', 'message']]
    year_content = year_content.sort_values('YearMonth')
    return year_content


def heatmap(df: pd.DataFrame):
    # Prepare data for heatmap
    df['date'] = df['timestamp'].dt.date
    df['weekday'] = df['timestamp'].dt.weekday
    df['week'] = df['timestamp'].dt.isocalendar().week
    df['year'] = df['timestamp'].dt.year

    # Filter for last two years
    last_two_years = df['year'].max() - 1
    df_filtered = df[df['year'] >= last_two_years]

    # Count messages per day
    heatmap_data = df_filtered.groupby(['date', 'weekday', 'week', 'year'])['message'].count().reset_index()

    # Calculate the maximum message count
    max_message_count = heatmap_data['message'].max()

    # Create weekday labels
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    heatmap_data['weekday_label'] = heatmap_data['weekday'].map(dict(enumerate(weekday_labels)))

    # Create Altair chart
    chart = alt.Chart(heatmap_data).mark_rect().encode(
        x=alt.X('week:O', title='Week', axis=alt.Axis(labelAngle=0, tickCount=53)),
        y=alt.Y('weekday_label:O', 
                title='Day', 
                sort=weekday_labels,
                axis=alt.Axis(labelAngle=0)),
        color=alt.Color('message:Q', 
                        scale=alt.Scale(scheme='viridis', domain=[0, max_message_count]),
                        legend=alt.Legend(title='Message Count')),
        tooltip=[
            alt.Tooltip('year:O', title='Year'),
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('message:Q', title='Message Count')
        ]
    ).properties(
        width=1000,
        height=300
    ).facet(
        row=alt.Row('year:O', title='Year', header=alt.Header(labelAngle=0))
    ).properties(
        title='Message Count Heatmap (Last Two Years)'
    )

    return chart

def create_sunburst_charts(df: pd.DataFrame):
    # Create a DataFrame with hour of day
    df['hour_of_day'] = df['timestamp'].dt.hour

    # Count messages per hour of day
    hour_counts = df.groupby('hour_of_day').size().reset_index(name='count')

    # Create hour labels and radians
    hour_counts['hour_label'] = hour_counts['hour_of_day'].apply(lambda x: f"{x:02d}:00")
    hour_counts['rad'] = hour_counts['hour_of_day'] * 2 * np.pi / 24 + np.pi / 24

    # Calculate max count for scaling
    max_count = hour_counts['count'].max()

    # Create base chart
    base = alt.Chart(hour_counts).encode(
        theta=alt.Theta('rad:Q', scale=alt.Scale(domain=[0, 2*np.pi])),
        radius=alt.Radius('count:Q', scale=alt.Scale(type='sqrt', zero=True, rangeMin=20, rangeMax=180)),
        color=alt.Color('count:Q', scale=alt.Scale(scheme='viridis')),
        tooltip=['hour_label:O', 'count:Q']
    )

    # Create arc chart
    arc = base.mark_arc(innerRadius=20, stroke="black", strokeWidth=0.5)

    # Create hour labels
    hour_labels = alt.Chart(hour_counts).mark_text(radiusOffset=10, align='center').encode(
        theta=alt.Theta('rad:Q'),
        text='hour_label:N',
        angle=alt.Angle('rad:Q', offset=-90)
    )

    # Create background for full circle
    background = alt.Chart(hour_counts).mark_arc(innerRadius=20, stroke="black", strokeWidth=0.5, opacity=0.1).encode(
        theta=alt.Theta('rad:Q'),
        radius=alt.value(180)
    )

    # Create the first sunburst chart (all data)
    chart1 = (background + arc + hour_labels).properties(
        width=400,
        height=400,
        title='Message Distribution by Hour (All Times)'
    )

    # Create the second sunburst chart (highlight max)
    max_hour = hour_counts.loc[hour_counts['count'].idxmax()]
    highlight = alt.Chart(pd.DataFrame([max_hour])).mark_arc(innerRadius=20, stroke="black", strokeWidth=0.5).encode(
        theta=alt.Theta('rad:Q', scale=alt.Scale(domain=[0, 2*np.pi])),
        radius=alt.Radius('count:Q', scale=alt.Scale(type='sqrt', zero=True, rangeMin=20, rangeMax=180)),
        color=alt.Color('count:Q', scale=alt.Scale(scheme='viridis')),
        opacity=alt.value(1)
    )

    chart2 = (background + arc.encode(opacity=alt.value(0.6)) + highlight + hour_labels).properties(
        width=400,
        height=400,
        title='Message Distribution by Hour (Highlight Max)'
    )

    return chart1, chart2



def calculate_chat_summary(df):
    total_messages = len(df)
    unique_authors = len(df.author.unique())
    
    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    
    start_date = df.date.min()
    end_date = df.date.max()
    total_days = (end_date - start_date).days + 1  # Add 1 to include both start and end dates
    avg_messages_per_day = total_messages / total_days
    
    author_counts = df['author'].value_counts()
    most_active_author = author_counts.index[0]
    most_active_author_messages = author_counts.iloc[0]
    most_active_author_percentage = (most_active_author_messages / total_messages) * 100

    return {
        "total_messages": total_messages,
        "unique_authors": unique_authors,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days,
        "avg_messages_per_day": avg_messages_per_day,
        "most_active_author": most_active_author,
        "most_active_author_messages": most_active_author_messages,
        "most_active_author_percentage": most_active_author_percentage
    }

def trend_stats(df: pd.DataFrame):
    author_stats = calculate_author_stats(df)
    time_data = prepare_time_data(df)
    author_stats = calculate_messaging_trends(author_stats, time_data)
    return author_stats

def calculate_author_stats(df: pd.DataFrame):
    author_stats = df["author"].value_counts().reset_index()
    author_stats.columns = ["Author", "Number of messages"]
    total_messages = df.shape[0]
    author_stats["Total %"] = round(author_stats["Number of messages"] * 100 / total_messages, 2)
    author_stats["Talkativeness"] = author_stats["Total %"].apply(
        lambda x: talkativeness(x, df["author"].nunique()))
    
    # Add average messages per day
    date_range = (df['timestamp'].max() - df['timestamp'].min()).days + 1
    author_stats["Avg Messages/Day"] = round(author_stats["Number of messages"] / date_range, 2)
    
    return author_stats

def prepare_time_data(df: pd.DataFrame):
    df["yearmonth"] = df["timestamp"].dt.to_period('M')
    time_data = df.groupby(["yearmonth", "author"]).size().unstack(fill_value=0)
    return time_data.sort_index()

def calculate_messaging_trends(author_stats: pd.DataFrame, time_data: pd.DataFrame):
    for period in [12, 6, 3]:
        column_name = f"Trend Last {period} Months"
        author_stats[column_name] = author_stats["Author"].apply(
            lambda x: analyze_trend(time_data.tail(period)[x]))
    return author_stats

def analyze_trend(series: pd.Series):
    if len(series) < 2:
        return "Insufficient data"
    
    x = np.arange(len(series))
    y = series.values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Calculate percentage change
    start_value = series.iloc[0]
    end_value = series.iloc[-1]
    pct_change = ((end_value - start_value) / start_value) * 100 if start_value != 0 else np.inf
    
    # Interpret trend
    if p_value < 0.1:  # Lowered from 0.05 to 0.1
        if slope > 0:
            trend = "Increase"
        else:
            trend = "Decrease"
    else:
        trend = "No trend"
    
    # Determine trend strength
    if abs(pct_change) > 50:
        strength = "Strong"
    elif abs(pct_change) > 25:
        strength = "Moderate"
    else:
        strength = "Slight"
    
    return f"{strength} {trend}"

def talkativeness(percentage: float, num_authors: int) -> str:
    average = 100 / num_authors
    ratio = percentage / average
    
    if ratio > 2:
        return "Very talkative"
    elif ratio > 1.5:
        return "Talkative"
    elif ratio > 0.75:
        return "Average"
    elif ratio > 0.5:
        return "Quiet"
    else:
        return "Very quiet"


def word_stats(df: pd.DataFrame):
    words_lst = (
        ''.join(df["message"].values.astype(str))).split(' ')
    words_lst = [i for i in words_lst if len(i) > 3]
    df = pd.DataFrame.from_dict(Counter(words_lst),
                                orient='index',
                                columns=[
                                    "count"]).reset_index().rename(
        columns={'index': 'word'})
    df.sort_values('count', ascending=False,
                   inplace=True, ignore_index=True)
    df[""] = df["count"].apply(
        lambda x: percent_helper(x / df.shape[0]))
    return df


def trendline(df: pd.DataFrame, order=1):
    index = range(0, len(df))
    coeffs = np.polyfit(index, list(df), order)
    slope = coeffs[-2]

    if slope > 0:
        return "Increasing (" + str(round(slope, 2)) + ")"
    else:
        return "Decreasing (" + str(round(slope, 2)) + ")"


def talkativeness(percent_message, total_authors):
    mean = 100 / total_authors
    threshold = mean * .25

    if percent_message > (mean + threshold):
        return "Very talkative"
    elif percent_message < (mean - threshold):
        return "Quiet, untalkative"
    else:
        return "Moderately talkative"

# Returns smallest integer k such that k
# * str becomes natural. str is an input floating point number #
def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)


def findnum(str):
    # Find size of string representing a
    # floating point number.
    n = len(str)
    # Below is used to find denominator in
    # fraction form.
    count_after_dot = 0

    # Used to find value of count_after_dot
    dot_seen = 0

    # To find numerator in fraction form of
    # given number. For example, for 30.25,
    # numerator would be 3025.
    num = 0
    for i in range(n):
        if str[i] != '.':
            num = num * 10 + int(str[i])
            if dot_seen == 1:
                count_after_dot += 1
        else:
            dot_seen = 1

    # If there was no dot, then number
    # is already a natural.
    if dot_seen == 0:
        return 1

    # Find denominator in fraction form. For example,
    # for 30.25, denominator is 100
    dem = int(math.pow(10, count_after_dot))

    # Result is denominator divided by
    # GCD-of-numerator-and-denominator. For example, for
    # 30.25, result is 100 / GCD(3025,100) = 100/25 = 4
    return dem / gcd(num, dem)


def percent_helper(percent):
    percent = math.floor(percent * 100) / 100

    if percent > 0.01:
        ans = findnum(str(percent))
        return "{} out of {} messages".format(int(percent * ans), int(1 * ans))
    else:
        return "<1 out of 100 messages"


def get_message_count_by_author(df: pd.DataFrame):
    return df.groupby('author')["message"].count().sort_values(ascending=False).reset_index()

def get_most_active_author(message_counts: pd.DataFrame):
    most_active = message_counts.sort_values("message", ascending=False).iloc[0]
    return most_active['author'], most_active['message']

def create_message_count_chart(message_counts: pd.DataFrame):
    
    base = alt.Chart(message_counts).encode(
        x=alt.X("author", sort="-y"),
        y=alt.Y('message:Q'),
        color='author'
    )
    
    bars = base.mark_bar()
    
    # Calculate the mean
    mean_value = message_counts['message'].mean()
    
    # Create a rule for the mean line
    mean_line = alt.Chart(pd.DataFrame({'mean': [mean_value]})).mark_rule(color='red').encode(
        y='mean:Q'
    )
    
    # Add text annotation for the mean
    mean_text = alt.Chart(pd.DataFrame({'mean': [mean_value]})).mark_text(
        align='left',
        baseline='bottom',
        dx=5,
        dy=-5,
        color='red'
    ).encode(
        y='mean:Q',
        text=alt.Text('mean:Q', format='.2f')
    )
    
    chart = (bars + mean_line + mean_text).properties(
        width=600,
        height=600,
        title='Number of messages sent'
    )
    
    return chart

def get_activity_stats(df: pd.DataFrame):
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
    chart = (c + rule).properties(width=600, height=600, title='Activity % by author')
    
    return {
        'most_active': most_active,
        'most_active_perc': most_active_perc,
        'data': o,
        'chart': chart
    }

def analyze_response_time(df: pd.DataFrame):
    # Calculate time difference and same author flag
    df = df.sort_values(["timestamp", "author"])
    df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
    df['same_author'] = df['author'] == df['author'].shift()

    # Filter out self-responses within 3 minutes
    response_data = df[~((df['time_diff'] < 180) & df['same_author'])]

    # Calculate response time in minutes
    response_data['response_time'] = response_data['time_diff'] / 60

    # Calculate log response time for distribution plot
    response_data['log_response_time'] = np.log10(response_data['response_time'])

    # Calculate median response time for each author
    median_response_time = response_data.groupby('author')['response_time'].median().reset_index()

    # Prepare data for distribution plot
    distribution_data = response_data[['author', 'log_response_time']].dropna()

    # Create median response time chart
    median_chart = alt.Chart(median_response_time).mark_bar().encode(
        y=alt.Y('author:N', sort='-x'),
        x=alt.X('response_time:Q', title='Median Response Time (minutes)'),
        color='author:N'
    ).properties(
        title='Median Response Time by Author'
    )

    return {
        'median_chart': median_chart,
        'slowest_responder': median_response_time.loc[median_response_time['response_time'].idxmax(), 'author']
    }

def analyze_monthly_messages(df: pd.DataFrame):
    # Extract year and month from timestamp
    df['YearMonth'] = df['timestamp'].dt.to_period('M')
    df['year'] = df['timestamp'].dt.year

    # Group by YearMonth and count messages
    year_content = df.groupby('YearMonth').agg({
        'message': 'count',
        'year': 'first'
    }).reset_index()

    # Find the month with the most messages
    peak_month = year_content.loc[year_content['message'].idxmax()]
    total_messages = peak_month['message']
    year = peak_month['YearMonth'].year
    month = peak_month['YearMonth'].month

    # Convert YearMonth to string for proper sorting
    year_content['YearMonth'] = year_content['YearMonth'].astype(str)

    # Create Altair chart
    base = alt.Chart(year_content).encode(
        x=alt.X("YearMonth:O", axis=alt.Axis(title="Year-Month", labelAngle=-45)),
        y=alt.Y('message:Q', axis=alt.Axis(title="Number of Messages"))
    )

    bar_chart = base.mark_bar().encode(
        color='year:O'
    )

    rule = base.mark_rule(color='red').encode(
        y='mean(message):Q'
    )

    chart = (bar_chart + rule).properties(
        width=1000,
        height=600,
        title='Monthly Message Volume Over Time'
    )

    return {
        'chart': chart,
        'peak_month': f"{year}-{str(month).zfill(2)}",
        'total_messages': total_messages
    }

def extract_emojis(s):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return ''.join(emoji_pattern.findall(s))

def create_word_cloud(df: pd.DataFrame):
    # Combine all messages and split into words
    all_words = ' '.join(df['message'].astype(str)).split()
    
    # Count word frequencies
    word_freq = pd.Series(all_words).value_counts().reset_index()
    word_freq.columns = ['word', 'frequency']
    
    # Take top 100 words for better performance
    word_freq = word_freq.head(100)
    
    # Create a word cloud object
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(dict(zip(word_freq['word'], word_freq['frequency'])))
    
    # Convert the word cloud to an image
    img = wordcloud.to_image()

    return img


def get_most_used_emoji(df: pd.DataFrame):
    try:
        # Combine all messages and extract emojis
        all_emojis = ' '.join(df['message'].astype(str).apply(extract_emojis))
        emoji_counts = Counter(all_emojis)
        
        # Convert to DataFrame for sorting
        emoji_df = pd.DataFrame(emoji_counts.items(), columns=['Emoji', 'Count'])
        # remove any length of whitespace from emoji column
        emoji_df['Emoji'] = emoji_df['Emoji'].str.replace(' ', '')
        # remove any length of whitespace from emoji column
        emoji_df['Emoji'] = emoji_df['Emoji'].str.replace('  ', '')
        emoji_df = emoji_df[emoji_df['Emoji'] != '']  # Remove non-emoji entries

        # remove nulls
        emoji_df = emoji_df[emoji_df['Emoji'].notna()]
        # Sort by count in descending order
        emoji_df = emoji_df.sort_values('Count', ascending=False)
        emoji_df['Count'] = emoji_df['Count'].astype(int)
        
        if len(emoji_df) >= 3:
            print(emoji_df.iloc[2].values)
        
        return emoji_df.head(10)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return pd.DataFrame(columns=['Emoji', 'Count'])
