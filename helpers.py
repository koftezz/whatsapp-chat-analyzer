import streamlit as st
import pandas as pd
import numpy as np
from chatminer.chatparsers import WhatsAppParser
import seaborn as sns
import datetime
import altair as alt
import tempfile
import chatminer.visualizations as vis
from matplotlib import ticker, pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter


def set_custom_matplotlib_style():
    plt.style.use('seaborn-dark')
    plt.rcParams['figure.figsize'] = [10, 6.5]
    plt.rcParams['axes.titlesize'] = 13.0
    plt.rcParams['axes.titleweight'] = 500
    plt.rcParams['figure.titlesize'] = 13.0
    plt.rcParams['figure.titleweight'] = 500
    plt.rcParams['text.color'] = '#242121'
    plt.rcParams['xtick.color'] = '#242121'
    plt.rcParams['ytick.color'] = '#242121'
    plt.rcParams['axes.labelcolor'] = '#242121'
    plt.rcParams['font.family'] = ['Source Sans Pro', 'Verdana', 'sans-serif']
    return (None)


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


def preprocess_data(df: pd.DataFrame,
                    selected_lang: str,
                    selected_authors: list):
    # language settings
    lang = {"English": {"picture": "image omitted",
                        "video": "video omitted",
                        "gif": "GIF omitted",
                        "audio": "audio omitted",
                        "sticker": "sticker omitted"
                        },
            "Turkish": {"picture": "görüntü dahil edilmedi",
                        "video": "video dahil edilmedi",
                        "gif": "GIF dahil edilmedi",
                        "audio": "ses dahil edilmedi",
                        "sticker": "Çıkartma dahil edilmedi"}}

    df["timestamp"] = pd.to_datetime(df["timestamp"],
                                     errors='coerce')
    df["date"] = df["timestamp"].dt.strftime('%Y-%m-%d')
    df = df.loc[df["author"].isin(selected_authors)]
    df = df.sort_values(["timestamp"])

    # Deal with links (URLS) as messages
    df['is_link'] = ~df.message.str.extract('(https?:\S*)',
                                            expand=False).isnull() * 1

    # Extract message length
    df['msg_length'] = df.message.str.len()
    df.loc[df.is_link == 1, 'msg_length'] = 0

    # Deal with multimedia messages to flag them and
    # set the text to null
    df['is_image'] = (df.message == lang[selected_lang][
        "picture"]) * 1
    df.loc[df.is_image == 1, 'message'] = np.nan
    df['is_video'] = (df.message == lang[selected_lang][
        "video"]) * 1
    df.loc[df.is_video == 1, 'message'] = np.nan

    df['is_gif'] = (df.message == lang[selected_lang][
        "gif"]) * 1
    df.loc[df.is_video == 1, 'message'] = np.nan

    df['is_sticker'] = (df.message == lang[selected_lang][
        "sticker"]) * 1
    df.loc[df.is_video == 1, 'message'] = np.nan

    df['is_audio'] = (df.message == lang[selected_lang][
        "audio"]) * 1
    df.loc[df.is_video == 1, 'message'] = np.nan

    # Filter out rows with no known author
    # or phone numbers as authors
    df = df[~(~df.author.str.extract('(\+)',
                                     expand=False).isnull() |
              df.author.isnull())]

    # Add field to flag the start of a new conversation
    # Conversation starter defined as a message sent at least
    # 7 hours after the previous message on the thread
    df['is_conversation_starter'] = ((
                                             df.timestamp - df.timestamp.shift(
                                         1)) > pd.Timedelta(
        '7 hours')) * 1
    return df


def basic_stats(df: pd.DataFrame):
    df = df.drop("hour", axis=1).groupby(
        'author').mean().rename(
        columns={
            "words": "Avg. Words",
            "msg_length": "Avg. Message Length",
            "letters": "Avg. Letters",
            "is_link": "Avg. Link",
            "is_conversation_starter": "Avg. Is Conversation Starter",
            "is_image": "Avg. Image",
            "is_video": "Avg. Video",
            "is_gif": "Avg. GIF",
            "is_audio": "Avg. Audio",
            "is_sticker": "Avg. Sticker"
        }
    ).style.format({
        'Avg. Words': '{:.2f}',
        'Avg. Message Length': '{:.1f}',
        'Avg. Letters': '{:.1f}',
        'Avg. Link': '{:.2%}',
        'Avg. Is Conversation Starter': '{:.2%}',
        'Avg. Image': '{:.2%}',
        'Avg. Video': '{:.2%}',
        'Avg. GIF': '{:.2%}',
        'Avg. Audio': '{:.2%}',
        'Avg. Sticker': '{:.2%}'
    }).background_gradient(axis=0)
    return df


def stats_overall(df: pd.DataFrame):
    temp = df.loc[df["is_image"] == 1]
    o1 = pd.DataFrame(
        temp.groupby("author")["is_image"].sum() / temp[
            "is_image"].sum()).reset_index()

    temp = df.loc[df["is_video"] == 1]
    o2 = pd.DataFrame(temp.groupby("author")["is_video"].sum() / temp[
        "is_video"].sum()).reset_index()

    temp = df.loc[df["is_link"] == 1]
    o3 = pd.DataFrame(temp.groupby("author")["is_link"].sum() / temp[
        "is_link"].sum()).reset_index()

    temp = df.loc[df["is_conversation_starter"] == 1]
    o4 = pd.DataFrame(
        temp.groupby("author")["is_conversation_starter"].sum() / temp[
            "is_conversation_starter"].sum()).reset_index()

    temp = df.loc[df["is_gif"] == 1]
    o5 = pd.DataFrame(
        temp.groupby("author")["is_gif"].sum() / temp[
            "is_gif"].sum()).reset_index()

    temp = df.loc[df["is_audio"] == 1]
    o6 = pd.DataFrame(
        temp.groupby("author")["is_audio"].sum() / temp[
            "is_audio"].sum()).reset_index()

    temp = df.loc[df["is_sticker"] == 1]
    o7 = pd.DataFrame(
        temp.groupby("author")["is_sticker"].sum() / temp[
            "is_sticker"].sum()).reset_index()
    o1 = pd.merge(o1, o2, on=["author"], how="left")
    o1 = pd.merge(o1, o3, on=["author"], how="left")
    o1 = pd.merge(o1, o4, on=["author"], how="left")
    o1 = pd.merge(o1, o5, on=["author"], how="left")
    o1 = pd.merge(o1, o6, on=["author"], how="left")
    o1 = pd.merge(o1, o7, on=["author"], how="left").fillna(
        {"is_sticker": 0,
         "is_gif": 0,
         "is_audio": 0,
         "is_video": 0,
         "is_conversation_starter": 0})
    return o1.rename(columns={
        "is_link": "Avg. Link",
        "is_conversation_starter": "Avg. Is Conversation Starter",
        "is_image": "Avg. Image",
        "is_video": "Avg. Video",
        "is_gif": "Avg. GIF",
        "is_audio": "Avg. Audio",
        "is_sticker": "Avg. Sticker"
    }
    ).style.format({
        'Avg. Link': '{:.2%}',
        'Avg. Is Conversation Starter': '{:.2%}',
        'Avg. Image': '{:.2%}',
        'Avg. Video': '{:.2%}',
        'Avg. GIF': '{:.2%}',
        'Avg. Audio': '{:.2%}',
        'Avg. Sticker': '{:.2%}'
    }).background_gradient(axis=0)


def smoothed_daily_activity(df: pd.DataFrame):
    df["year"] = df["timestamp"].dt.year
    daily_activity_df = df.loc[df["year"] > 2018].groupby(
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
                              on="key").drop(
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
    o = distinct_dates.groupby("author").agg(
        {"is_active": "sum", "date_diff": "max"})
    o["is_active_percent"] = 100 * (o["is_active"] / o["date_diff"])
    return o.drop(["is_active", "date_diff"], 1).rename(columns={
        "is_active_percent": "Activity %"
    }
    ).style.format(
        {"Activity %": '{:.2f}'}).background_gradient(axis=0)


def create_colormap(colors=['w', 'g'], n_bins=256):
    """
     Function to create bespoke linear segmented color map.
    Will be useful to create colormaps for each user
    consistent with their colour scheme
    :param colors:
    :param n_bins:
    :return:
    """
    n_bins = 256  # Discretizes the interpolation into bins
    cmap_name = 'temp_cmap'

    # Create the colormap
    cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)
    return (cm)


def relative_activity_ts(df: pd.DataFrame):
    daily_activity_df = df.loc[df["year"] > 2021].groupby(
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
    o = df.groupby(
        [df.timestamp.dt.dayofweek, df.author]).msg_length.sum(

    ).unstack().fillna(0)
    # o = o.reindex(["Monday", "Tuesday", "Wednesday",
    #               "Thursday", "Friday", "Saturday",
    #               "Sunday"])
    return o


def activity_time_of_day_ts(df: pd.DataFrame):
    a = df.groupby(
        [df.timestamp.dt.time,
         df.author]).msg_length.sum().unstack().fillna(0)
    a = a.reindex(
        [datetime.time(i, j) for i in range(24) for j in
         range(60)]).fillna(0)

    # Temporarily add the tail at the start and head and the end of the
    # data frame for the gaussian smoothing
    # to be continuous around midnight
    a = pd.concat([a.tail(120), a, a.head(120)])

    # Apply gaussian convolution
    b = pd.DataFrame(gaussian_filter(a.values, (60, 0)),
                     index=a.index,
                     columns=a.columns)

    # Remove the points temporarily added from the ends
    b = b.iloc[120:-120]

    # o = b.reset_index()
    # o["hour"] = o["timestamp"].apply(lambda x: x.hour)
    # # o["hour"] = o["hour"].astype(str) + ":00"
    # o = o.sort_values("timestamp")
    # b = o.set_index(["hour", "timestamp"])

    # # Plot the smoothed data
    # o = b.plot(ax=plt.gca())
    # plt.xticks(range(0,24*60*60+1, 3*60*60))
    # plt.xlabel('Time of day')
    # plt.ylabel('Relative activity')
    # plt.ylim(0, plt.ylim()[1])
    # plt.title('Activity by time of day')
    # plt.gca().legend(title=None)
    # plt.tight_layout()
    # st.pyplot(o)
    return b


def response_matrix(df: pd.DataFrame):
    prev_msg_lt_180_seconds = (df.timestamp - df.timestamp.shift(
        1)).dt.seconds < 180
    same_prev_author = (df.author == df.author.shift(1))
    fig, ax = plt.subplots()
    ax = (df
          [~(prev_msg_lt_180_seconds & same_prev_author)]
          .groupby([df.author.rename('Message author'),
                    df.author.shift(1).rename('Responding to...')])
          .size()
          .unstack()
          .pipe(lambda x: x.div(x.sum(axis=1), axis=0))
          .pipe(sns.heatmap, vmin=0, annot=True, fmt='.0%',
                cmap='viridis',
                cbar=False))

    plt.title('Reponse Martix\n ')
    plt.gca().text(.5, 1.04,
                   "Author of previous message when a message is sent*",
                   ha='center', va='center', size=12,
                   transform=plt.gca().transAxes);
    plt.gca().set_yticklabels(plt.gca().get_yticklabels(),
                              va='center',
                              minor=False)
    plt.gcf().text(0, 0,
                   "*Excludes messages to self within 3 mins",
                   va='bottom')
    plt.tight_layout()
    return fig


def spammer(df: pd.DataFrame):
    prev_sender = []
    max_spam = 0
    tmp_spam = 0

    for jj in range(len(df)):
        current_sender = df['author'].iloc[jj]
        if current_sender == prev_sender:
            tmp_spam += 1
            if tmp_spam > max_spam:
                max_spam = tmp_spam
                max_spammer = current_sender
        else:
            tmp_spam = 0

        prev_sender = current_sender
    return max_spammer, max_spam


def year_month(df: pd.DataFrame):
    df[
        'YearMonth'] = df.timestamp.dt.year * 100 + df.timestamp.dt.month
    year_content = df.groupby('YearMonth', as_index=False).count()[
        ['YearMonth', 'message']]
    year_content = year_content.sort_values('YearMonth')
    year_content = year_content.set_index("YearMonth")
    return year_content


def radar_chart(df: pd.DataFrame):
    if not vis.is_radar_registered():
        vis.radar_factory(7, frame="polygon")
    fig, ax = plt.subplots(1, 1, figsize=(7, 3),
                           subplot_kw={'projection': 'radar'})
    ax = vis.radar(df, ax=ax)
    fig.tight_layout()
    return fig


def heatmap(df: pd.DataFrame):
    current_year = df.year.max()
    last_year = current_year - 1
    if df.loc[df["year"] == last_year].shape[0] > 0:
        fig, ax = plt.subplots(2, 1, figsize=(9, 3))
        ax[0] = vis.calendar_heatmap(df, year=last_year,
                                     monthly_border=True,
                                     cmap='Oranges',
                                     ax=ax[0])
        ax[1] = vis.calendar_heatmap(df, year=current_year,
                                     linewidth=0,
                                     monthly_border=True, ax=ax[1])
        ax[0].set_title(last_year)
        ax[1].set_title(current_year)
    else:
        fig, ax = plt.subplots(1, 1, figsize=(9, 3))
        ax[0] = vis.calendar_heatmap(df, year=current_year,
                                     linewidth=0,
                                     monthly_border=True, ax=ax[1])
    return fig


def sunburst(df: pd.DataFrame):
    fig, ax = plt.subplots(1, 2, figsize=(7, 3),
                           subplot_kw={'projection': 'polar'})
    ax[0] = vis.sunburst(df, highlight_max=True,
                         isolines=[2500, 5000],
                         isolines_relative=False, ax=ax[0])
    ax[1] = vis.sunburst(df, highlight_max=False,
                         isolines=[0.5, 1],
                         color='C1', ax=ax[1])
    return fig
