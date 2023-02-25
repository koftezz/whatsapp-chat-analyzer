import streamlit as st
import pandas as pd
import numpy as np
from chatminer.chatparsers import WhatsAppParser
import seaborn as sns
import datetime
import tempfile
import chatminer.visualizations as vis
from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
import math
import emoji
from collections import Counter


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
                        "sticker": "sticker omitted",
                        "deleted": ["This message was deleted.",
                                    "You deleted this message."],
                        "location": "Location https://"
                        },
            "Turkish": {"picture": "görüntü dahil edilmedi",
                        "video": "video dahil edilmedi",
                        "gif": "GIF dahil edilmedi",
                        "audio": "ses dahil edilmedi",
                        "sticker": "Çıkartma dahil edilmedi",
                        "deleted": ["Bu mesaj silindi.",
                                    "Bu mesajı sildiniz."],
                        "location": "Konum https://"}}

    df["timestamp"] = pd.to_datetime(df["timestamp"],
                                     errors='coerce')
    df["date"] = df["timestamp"].dt.strftime('%Y-%m-%d')
    df = df.loc[df["author"].isin(selected_authors)]
    df = df.sort_values(["timestamp"])

    df["is_location"] = (df.message.str.contains('maps.google') == True) * 1
    locations = df.loc[df["is_location"] == 1]
    df.loc[df.is_location == 1, 'message'] = np.nan

    if locations.shape[0] > 0:
        locs = locations["message"].str.split(" ", expand=True)
        locs[1] = locs[1].str[27:]
        locs = locs[1].str.split(",", expand=True)
        locs = locs.rename(columns={0: "lat", 1: "lon"})
        locs = locs.loc[(locs["lat"] != "") & (locs["lon"] != "") \
                        & (~locs["lat"].isna()) & (~locs["lon"].isna())]
        locations = locs[["lat", "lon"]].astype(float).drop_duplicates()

    # Deal with links (URLS) as messages
    df['is_link'] = ~df.message.str.extract('(https?:\S*)',
                                            expand=False).isnull() * 1

    # Extract message length
    df['msg_length'] = df.message.str.len()
    df.loc[df.is_link == 1, 'msg_length'] = np.nan

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

    df['is_deleted'] = (df.message.isin(lang[selected_lang]["deleted"])) * 1
    df.loc[df.is_deleted == 1, 'message'] = np.nan

    # df["emoji_count"] = df["message"].apply(lambda word_list:
    #                                         collections.Counter([match[
    #                                                                  "message"]
    #                                                              for word in
    #                                                              word_list for
    #                                                              match in
    #                                                              emoji.emoji_list(
    #                                                                  word)]))

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
    return df, locations


def basic_stats(df: pd.DataFrame):
    df = df.drop("hour", axis=1).groupby(
        'author').mean().rename(
        columns={
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
            "is_location": "Location"
        }
    ).style.format({
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
        'Location': '{:.2%}'
    }).background_gradient(axis=0)
    return df


def stats_overall(df: pd.DataFrame):
    authors = df[["author"]].drop_duplicates()

    temp = df.loc[df["is_image"] == 1]
    images = pd.DataFrame(
        temp.groupby("author")["is_image"].sum() / temp[
            "is_image"].sum()).reset_index()

    temp = df.loc[df["is_video"] == 1]
    videos = pd.DataFrame(temp.groupby("author")["is_video"].sum() / temp[
        "is_video"].sum()).reset_index()

    temp = df.loc[df["is_link"] == 1]
    links = pd.DataFrame(temp.groupby("author")["is_link"].sum() / temp[
        "is_link"].sum()).reset_index()

    temp = df.loc[df["is_conversation_starter"] == 1]
    con_starters = pd.DataFrame(
        temp.groupby("author")["is_conversation_starter"].sum() / temp[
            "is_conversation_starter"].sum()).reset_index()

    temp = df.loc[df["is_gif"] == 1]
    gifs = pd.DataFrame(
        temp.groupby("author")["is_gif"].sum() / temp[
            "is_gif"].sum()).reset_index()

    temp = df.loc[df["is_audio"] == 1]
    audios = pd.DataFrame(
        temp.groupby("author")["is_audio"].sum() / temp[
            "is_audio"].sum()).reset_index()

    temp = df.loc[df["is_sticker"] == 1]
    stickers = pd.DataFrame(
        temp.groupby("author")["is_sticker"].sum() / temp[
            "is_sticker"].sum()).reset_index()

    temp = df.loc[df["is_deleted"] == 1]
    delete = pd.DataFrame(
        temp.groupby("author")["is_deleted"].sum() / temp[
            "is_deleted"].sum()).reset_index()

    temp = df.loc[df["is_location"] == 1]
    locs = pd.DataFrame(
        temp.groupby("author")["is_location"].sum() / temp[
            "is_location"].sum()).reset_index()

    authors = pd.merge(authors, images, on=["author"], how="left")
    authors = pd.merge(authors, videos, on=["author"], how="left")
    authors = pd.merge(authors, audios, on=["author"], how="left")
    authors = pd.merge(authors, con_starters, on=["author"], how="left")
    authors = pd.merge(authors, links, on=["author"], how="left")
    authors = pd.merge(authors, gifs, on=["author"], how="left")
    authors = pd.merge(authors, stickers, on=["author"], how="left")
    authors = pd.merge(authors, delete, on=["author"], how="left")
    authors = pd.merge(authors, locs, on=["author"], how="left")
    authors = authors.fillna(
        {"is_sticker": 0,
         "is_gif": 0,
         "is_audio": 0,
         "is_video": 0,
         "is_conversation_starter": 0,
         "is_deleted": 0,
         "is_location": 0}).rename(
        columns={
            "is_link": "Link",
            "is_conversation_starter": "Is Conversation Starter",
            "is_image": "Image",
            "is_video": "Video",
            "is_gif": "GIF",
            "is_audio": "Audio",
            "is_sticker": "Sticker",
            "is_deleted": "Deleted",
            "is_location": "Location"
        }
    ).style.format({
        'Link': '{:.2%}',
        'Is Conversation Starter': '{:.2%}',
        'Image': '{:.2%}',
        'Video': '{:.2%}',
        'GIF': '{:.2%}',
        'Audio': '{:.2%}',
        'Sticker': '{:.2%}',
        'Deleted': '{:.2%}',
        'Location': '{:.2%}'
    }).background_gradient(axis=0)
    return authors


def smoothed_daily_activity(df: pd.DataFrame):
    df["year"] = df["timestamp"].dt.year
    min_year = df.year.max() - 5
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
    return o.reset_index().drop(["is_active", "date_diff"], 1) \
        .rename(columns={
        "is_active_percent": "Activity %"
    }
    )


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
    min_year = df.year.max() - 3
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

    b = b.reset_index()
    b = b.rename_axis(None, axis=1)
    b['timestamp'] = pd.to_datetime(b['timestamp'].astype(str))

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
                   ha='center', va='center', size=8,
                   transform=plt.gca().transAxes);
    plt.gca().set_yticklabels(plt.gca().get_yticklabels(),
                              va='center',
                              minor=False,
                              fontsize=8)
    # plt.gcf().text(0, 0,
    #                "*Excludes messages to self within 3 mins",
    #                va='bottom')
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
    year_content = df.groupby(["year", 'YearMonth'], as_index=False).count()[
        ["year", 'YearMonth', 'message']]
    year_content = year_content.sort_values('YearMonth')
    return year_content


def radar_chart(df: pd.DataFrame):
    fig, ax = plt.subplots(1, 2, figsize=(7, 3),
                           subplot_kw={'projection': 'radar'})
    current_year = df.year.max()
    last_year = current_year - 1
    ax[0] = vis.radar(df.loc[df["year"] == last_year], ax=ax[0])
    ax[1] = vis.radar(df.loc[df["year"] == current_year], ax=ax[1], color='C1',
                      alpha=0)
    ax[0].set_title(last_year)
    ax[1].set_title(current_year)
    plt.tight_layout()

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


def trend_stats(df: pd.DataFrame):
    author_df = df["author"].value_counts().reset_index()
    author_df.rename(columns={"index": "Author",
                              "author": "Number of messages"},
                     inplace=True)
    author_df["Total %"] = round(
        author_df["Number of messages"] * 100 / df.shape[0], 2)
    author_df["Talkativeness"] = author_df["Total %"].apply(
        lambda x: talkativeness(x, df["author"].nunique()))

    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month
    max_year = df.year.max()
    max_month = df.loc[
        df.year == max_year].month.max()

    df["yearmonth"] = df["year"] * 100 + \
                      df["month"]
    df.loc[
        df["yearmonth"] <= max_year * 100 + max_month]
    temp_df = df.pivot_table(
        index=["yearmonth"], columns=["author"],
        values=["message"], aggfunc="count", fill_value=0)
    temp_df.columns = [col_[1] for col_ in
                       temp_df.columns]
    temp_df = temp_df.reset_index().sort_values(
        ["yearmonth"])

    temp_df.set_index('yearmonth', inplace=True)
    author_df["Messaging Trend Last 12 Months"] = author_df[
        "Author"].apply(
        lambda x: trendline(temp_df.tail(12)[x]))
    author_df["Messaging Trend Last 6 Months"] = author_df[
        "Author"].apply(
        lambda x: trendline(temp_df.tail(6)[x]))
    author_df["Messaging Trend Last 3 Months"] = author_df[
        "Author"].apply(
        lambda x: trendline(temp_df.tail(3)[x]))
    return author_df


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


def extract_emojis(s):
    return ''.join(c for c in s if c in emoji.UNICODE_EMOJI)


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
