from geopy.geocoders import Nominatim
from helpers import *
import altair as alt

st.set_page_config(
    page_title="Whatsapp Group Chat Analyzer",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "https://github.com/koftezz/whatsapp-chat-analyzer/issues",
        'About': "# This is an Whatsapp Group Chat Analyzer!"
    }
)
st.cache_data.clear()
st.cache_resource.clear()
st.write("""
         ## Whatsapp Group Chat Analyzer
         """)

with st.expander("About this app"):
    st.markdown(
        """
    V1.0 2023-02-25:
    ### What's New?
    - GIF, Sticker, Audio, Deleted, Location Message Statistics.
    - Maps for shared location
    - Talkativeness & Messaging Trends
    - General Formatting & Chart Redesign
    
    ### Info
     - This does not save your chat file.
     - Note that it only supports English and Turkish right now.
     - Most of the charts are based on group chats but it works for dms too, 
     some of the charts will be pointless but give it a shot.
     - Sometimes whatsapp can have problems while exporting with date formats. 
     If there is an error after uploading, check your file date format, 
     there might be some inconsistency in date formatting. 
     - It may take a while for around 2 minutes for 20mb of chat file on the 
     server.
     - Possible to-dos:
        - Aggregate multiple people into one. Sometimes a user can have multi 
        numbers and we should give a chance to see them as one single user.
        - Charts can be change by year via dropdown.
        - Add emoji support
        - Exportable pdf
        - More prescriptive
        - Demo chat
     - Last but not least - Thanks to [chat-miner](
     https://github.com/joweich/chat-miner) for easy whatsapp parsing tool and 
     their awesome charts. Thanks to [Dinesh Vatvani](https://dvatvani.github.io/whatsapp-analysis.html) 
     for his great analysis.
     - source: [koftezz](https://github.com/koftezz/whatsapp-chat-analyzer)
    """
    )

def app():
    session_state = st.session_state
    if "df" not in session_state:
        file = st.file_uploader("Upload WhatsApp chat file without media. "
                                "The file should be .txt", type="txt")

        @st.cache_data
        def read_sample_data():
            df = pd.read_csv(
                "https://raw.githubusercontent.com/koftezz/whatsapp-chat-analyzer/0aee084ffb8b8ec4869da540dc95401b8e16b7dd/data/sample_file.txt", header=None)
            return df.to_csv(index=False).encode('utf-8')

        csv = read_sample_data()

        st.download_button(
            label="Download sample chat file.",
            data=csv,
            file_name='data/sample_file.txt',
        )
        if file is not None:
            df = read_file(file)
            df = df.sort_values("timestamp")
            # first three entry is most likely is the group creation.
            df = df[3:]
            edited_df = df[["author"]].drop_duplicates()
            edited_df["combined authors"] = edited_df["author"]
            edited_df = st.data_editor(edited_df)
            author_list = edited_df["combined authors"].drop_duplicates().tolist()
            with st.form(key='my_form_to_submit'):

                selected_authors = st.multiselect(
                    "Choose authors of the group",
                    author_list)
                selected_lang = st.radio(
                    "What\'s your Whatsapp Language?",
                    ("English", 'Turkish'))
                submit_button = st.form_submit_button(label='Submit')
                if submit_button and len(selected_authors) < 2:
                    st.warning("Proceeding with all of the authors. Please "
                               "check that there might be some problematic "
                               "authors.",
                               icon="⚠️")
                    selected_authors = df["author"].drop_duplicates().tolist()
            if submit_button:
                df, locations = preprocess_data(df=df,
                                                selected_lang=selected_lang,
                                                selected_authors=selected_authors)

                with st.expander("Show the `Chat` dataframe"):
                    st.dataframe(df)

                # Set up colors to use for each author to
                # keep them consistent across the analysis
                author_list = df.groupby('author').size().index.tolist()
                author_color_lookup = {author: f'C{n}' for n, author in
                                       enumerate(author_list)}
                author_color_lookup['Group total'] = 'k'

                def formatted_barh_plot(s,
                                        pct_axis=False,
                                        thousands_separator=False,
                                        color_labels=True,
                                        sort_values=True,
                                        width=0.8,
                                        **kwargs):
                    if sort_values:
                        s = s.sort_values()
                    s.plot(kind='barh',
                           color=s.index.to_series().map(
                               author_color_lookup).fillna(
                               'grey'),
                           width=width,
                           **kwargs)
                    if color_labels:
                        for color, tick in zip(
                                s.index.to_series().map(
                                    author_color_lookup).fillna(
                                    'grey'),
                                plt.gca().yaxis.get_major_ticks()):
                            tick.label1.set_color(
                                color)  # set the color property
                    if pct_axis:
                        if type(pct_axis) == int:
                            decimals = pct_axis
                        else:
                            decimals = 0
                        plt.gca().xaxis.set_major_formatter(
                            ticker.PercentFormatter(1, decimals=decimals))
                    elif thousands_separator:
                        plt.gca().xaxis.set_major_formatter(
                            ticker.FuncFormatter(
                                lambda x, p: format(int(x), ',')))

                    return plt.gca()

                msg = f"## Overall Summary\n" \
                      f"{len(df)} total messages from" \
                      f" {len(df.author.unique())}  " \
                      f"people " \
                      f"from {df.date.min()} to {df.date.max()}."
                st.write(msg)

                # Basic summary of messages
                st.write(
                    "## Basic summary of messages")
                with st.expander("More info"):
                    st.write("All the "
                             "statistics are average of the respective "
                             "columns. For Ex: Link means average of "
                             "messages sent with link.\n- Conversation starter \n"
                             "defined as a message sent at least 7 hours after the"
                             " previous message on the thread\n")
                o = basic_stats(df=df)
                st.dataframe(o, use_container_width=True)

                # Basic summary of messages
                st.write("## Summary across authors")
                o = stats_overall(df=df)
                st.dataframe(o)

                st.write("## Talkativeness & Messaging Trends")
                author_df = trend_stats(df=df)
                st.dataframe(author_df, use_container_width=True)

                # Total messages sent stats
                st.write("## Number of Messages Sent By Author")
                o = pd.DataFrame(
                    df.groupby('author')["message"].count()).reset_index()
                most_active = \
                    o.sort_values("message", ascending=False).iloc[0][
                        'author']
                total_msg = o.sort_values("message",
                                          ascending=False).iloc[0][
                    'message']
                st.write(f"Here is the chatter of the group :red"
                         f"[{most_active}], by sending total of"
                         f" {total_msg} messages. Only by him/herself. 🤯")

                c = alt.Chart(o).mark_bar().encode(
                    x=alt.X("author", sort="-y"),
                    y=alt.Y('message:Q'),
                    color='author',
                )
                rule = alt.Chart(o).mark_rule(color='red').encode(
                    y='mean(message):Q'
                )
                c = (c + rule).properties(width=600, height=600,
                                          title='Number of messages sent'
                                          )
                st.altair_chart(c)
                # Average message length by use
                o = activity(df=df)
                most_active = \
                    o.sort_values("Activity %", ascending=False).iloc[0][
                        'author']
                most_active_perc = o.sort_values("Activity %",
                                                 ascending=False).iloc[0][
                    'Activity %']
                st.write(f"""## Activity Stats by Author""")
                st.write(f":red[{most_active}] is online "
                         f"{round(most_active_perc, 2)}% of the conversations. "
                         f"Go get a job!")
                with st.expander("More info"):
                    st.info(
                        "It shows the percent of an author who sent at least a"
                        " message in a random"
                        " day with active conversation.")
                c = alt.Chart(o).mark_bar().encode(
                    x=alt.X("author:N", sort="-y"),
                    y=alt.Y('Activity %:Q'),
                    color='author',
                )
                rule = alt.Chart(o).mark_rule(color='red').encode(
                    y='mean(Activity %):Q'
                )
                c = (c + rule).properties(width=600, height=600,
                                          title='Activity % by author'
                                          )
                st.altair_chart(c)

                # Smoothed stacked activity area timeseries plot
                st.write("""## Activity Area Plot """)
                with st.expander("More info"):
                    min_year = df.year.max() - 5
                    st.info("It is an absolute plot which we can see who has "
                            "been more active in terms of total messsages."
                            " It is smoothed with gaussian "
                            "distribution since the data is likely to be "
                            f"noisy.\nChart starts from year {min_year + 1}")
                smoothed_daily_activity_df = smoothed_daily_activity(df=df)
                st.area_chart(smoothed_daily_activity_df)

                # Relative activity timeseries - 100% stacked area plot
                st.write("""
                    ## Relative Activity Area Plot
                    """)
                with st.expander("More info"):
                    min_year = df.year.max() - 3
                    st.info("It is a relative plot which we can see who has "
                            "been more active."
                            "with respect to each other. It basically shows "
                            "the activity percentage of each author changes "
                            "over time. It is smoothed with gaussian "
                            "distribution since the data is likely to be "
                            f"noisy.\nChart starts from year {min_year + 1}")
                o = relative_activity_ts(df=df)
                st.area_chart(o)

                # Timeseries: Activity by day of week
                st.write("""
                    ## Activity by day of week
                    0 - Monday
                    6 - Sunday
                    """)
                o = activity_day_of_week_ts(df=df)
                st.line_chart(o)

                # Timeseries: Activity by time of day
                st.write("""
                    ## Activity by time of day (UTC)
                    """)
                b = activity_time_of_day_ts(df=df)

                c = alt.Chart(b).transform_fold(
                    selected_authors,
                    as_=['author', "message"]
                ).mark_line().encode(
                    x=alt.X('utchoursminutes(timestamp):T', axis=alt.Axis(
                        format='%H:00'),
                            scale=alt.Scale(type='utc')),
                    y='message:Q',
                    color='author:N'
                ).properties(width=1000, height=600)
                st.altair_chart(c)

                # Response matrix
                st.write("""
                    ## Response Matrix
                    """)
                with st.expander("More info"):
                    st.info("This does not consider the content of the "
                            "message. It is based on who is the previous "
                            "sender of the message. Self sonsecutive messages "
                            "within 3 minutes are excluded."
                            "")
                with st.container():
                    fig = response_matrix(df=df)
                    st.pyplot(fig)

                st.write("""
                    ## Response Time Distribution
                    """)
                with st.expander("More info"):
                    st.info("Self consecutive messages "
                            "within 3 minutes are excluded."
                            " Median response time shows that author X "
                            "responded the messages at least y mins later, "
                            "half of the time."
                            "")

                # Response time
                prev_msg_lt_180_seconds = (df.timestamp - df.timestamp.shift(
                    1)).dt.seconds < 180
                same_prev_author = (df.author == df.author.shift(1))
                fig, ax = plt.subplots()
                plt.subplot(121)
                o = df[~(prev_msg_lt_180_seconds & same_prev_author)]
                o["response_time"] = (
                    (o.timestamp - o.timestamp.shift(1)).dt.seconds
                        .replace(0, np.nan)
                        .div(60)
                        .apply(np.log10))
                o = o[["author", "response_time"]]

                o.groupby("author")["response_time"].apply(
                    sns.kdeplot)
                plt.title('Response time distribution', fontsize=8)
                plt.ylabel('Relative frequency', fontsize=8)
                plt.xlabel('Response time (Mins)', fontsize=8)
                locs, ticks = plt.xticks()
                plt.xticks(locs, [f"$10^{{{int(loc)}}}$" for loc in locs])

                plt.subplot(122)
                o = df[~(prev_msg_lt_180_seconds & same_prev_author)]
                o["response_time"] = (
                    (o.timestamp - o.timestamp.shift(1)).dt.seconds
                        .replace(0, np.nan)
                        .div(60))
                response = o[["author", "response_time", "letters"]]
                response.groupby("author").median()["response_time"].pipe(
                    formatted_barh_plot)
                plt.title('Median response time', fontsize=8)
                plt.ylabel('')
                plt.xlabel('Response time (Mins)', fontsize=8)

                plt.tight_layout()
                with st.container():
                    slow_typer = response.groupby("author").median()[
                                     "response_time"]. \
                                     sort_values()[-1:].index[0]
                    st.write(f"Looks like :red[{slow_typer}] has much to do, "
                             f"except responding to you guys on time.👨‍💻👩‍💻")
                    st.pyplot(fig)
                std = response.response_time.std()
                mean = response.response_time.mean()

                response = response.loc[response["response_time"] <= mean + 3
                                        * std]
                c = alt.Chart(response).mark_point(size=60).encode(
                    x='letters',
                    y='response_time',
                    color='author',
                    tooltip=["author", "response_time", "letters"]
                )
                c = (c + c.transform_regression("letters",
                                                'response_time').mark_line()). \
                    properties(width=1000, height=600,
                               title='Response Time vs Number of letters in '
                                     'a message'
                               ).interactive()
                st.write("## Is number of letters correlated with the "
                         "response time?")
                with st.container():
                    st.altair_chart(c)

                max_spammer, max_spam = spammer(df=df)
                st.write("""
                    ## Who is the spammer?
                    The most spam is from :red[%s] with %d consecutive 
                    messages. ☠️""" % (
                    max_spammer, max_spam))

                st.write("""
                    ## Year x Month Total Messages
                    """)
                year_content = year_month(df=df)
                total_messages = year_content.sort_values("message",
                                                          ascending=False).iloc[
                    0].message
                year = int(year_content.sort_values("message",
                                                    ascending=False).iloc[
                               0].YearMonth / 100)
                month = \
                    year_content.sort_values("message", ascending=False).iloc[
                        0].YearMonth % 100
                st.write(f"You break the monthly record! Total of"
                         f" {total_messages} messages"
                         f" in {year}-{str(month).rjust(2, '0')}.💥 ")
                c = alt.Chart(year_content).mark_bar().encode(
                    x=alt.X("YearMonth:O", ),
                    y=alt.Y('message:Q'),
                    color='year:O',
                )
                rule = alt.Chart(year_content).mark_rule(color='red').encode(
                    y='mean(message):Q'
                )
                c = (c + rule).properties(width=1000, height=600,
                                          title='Total Number of messages '
                                                'sent over years'
                                          )
                st.altair_chart(c)

                st.write("""
                            ## Sunburst: Message count per daytime
                            """)
                with st.expander("More info"):
                    st.info("- Left chart shows the realized values."
                            "\n- Right chart shows the adjusted values based "
                            "on "
                            "max message count.")
                fig = sunburst(df=df)
                st.pyplot(fig)

                # st.write("""
                # Radarchart: Message count per weekday
                # """)
                # fig = radar_chart(df=df)
                # st.pyplot(fig)

                st.write(""" ## Heatmap: Message count per day """)
                fig = heatmap(df=df)
                st.pyplot(fig)

                if locations.shape[0] > 0:
                    st.write(""" ## Map of Locations""")

                    #   geolocator = Nominatim(user_agent="loc_finder")
                    #   with st.expander("More info"):
                    #       st.info("This map shows all the locations which are "
                    #               "sent by the authors via whatsapp. The "
                    #               "latitude and Longitude values are extracted "
                    #               "from google maps.")
                    #   with st.spinner('This may take a while. Wait for it...'):
                    #       for i, row in locations.iterrows():
                    #           location = geolocator.reverse((row.lat, row.lon)).raw
                    #           locations.loc[i, "country"] = location["address"]["country"]
                    #           locations.loc[i, "town"] = location["address"]["town"]
                    #       st.write("### Top shared locations")
                    #       st.dataframe(pd.DataFrame(locations.groupby(["country", "town"])["lat"]
                    #                    .count()).rename(columns={"lat":
                    #                                  "count"}).sort_values(
                    #           "count", ascending=False))

                    st.map(locations)

                st.cache_data.clear()
                st.cache_resource.clear()


if __name__ == "__main__":
    app()
