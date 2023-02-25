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
        if file is not None:
            df = read_file(file)
            with st.form(key='my_form_to_submit'):
                selected_authors = st.multiselect(
                    "Choose authors of the group",
                    df.author.unique().tolist())
                selected_lang = st.radio(
                    "What\'s your Whatsapp Language?",
                    ("English", 'Turkish'))

                submit_button = st.form_submit_button(label='Submit')
                if submit_button and len(selected_authors) < 2:
                    st.warning("You must select at least 2 authors!",
                               icon="⚠️")
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
                st.write("""
                ## Activity Stats by Author
                
                It shows the percent of an author who sent at least a message in a random 
                day with active conversation.
                """)
                o = activity(df=df)
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
                    st.info("It is an absolute plot which we can see who has "
                            "been more active in terms of total messsages."
                            " It is smoothed with gaussian "
                            "distribution since the data is likely to be "
                            "noisy.")
                smoothed_daily_activity_df = smoothed_daily_activity(df=df)
                st.area_chart(smoothed_daily_activity_df)

                # Relative activity timeseries - 100% stacked area plot
                st.write("""
                ## Relative Activity Area Plot
                """)
                with st.expander("More info"):
                    st.info("It is a relative plot which we can see who has "
                            "been more active."
                            "with respect to each other. It basically shows "
                            "the activity percentage of each author changes "
                            "over time. It is smoothed with gaussian "
                            "distribution since the data is likely to be "
                            "noisy.")
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
                ## Activity by time of day
                X-Axis labels have some problems. ToDo.
                """)
                b = activity_time_of_day_ts(df=df)
                st.line_chart(b)

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
                fig = response_matrix(df=df)
                st.pyplot(fig)

                st.write("""
                ## Response Time Distribution
                """)
                with st.expander("More info"):
                    st.info("Self consecutive messages "
                            "within 3 minutes are excluded."
                            "Median response time shows that author X "
                            "responded the messages at least y mins later, "
                            "half of the time."
                            "")

                # Response time
                prev_msg_lt_180_seconds = (df.timestamp - df.timestamp.shift(
                    1)).dt.seconds < 180
                same_prev_author = (df.author == df.author.shift(1))
                fig, ax = plt.subplots()
                plt.subplot(121)
                ((df.timestamp - df.timestamp.shift(1)).dt.seconds
                 .replace(0, np.nan)
                 .div(60)
                 .apply(np.log10)
                 [~(prev_msg_lt_180_seconds & same_prev_author)]
                 .groupby(df.author)
                 .apply(sns.kdeplot))
                plt.title('Response time distribution', fontsize=8)
                plt.ylabel('Relative frequency', fontsize=8)
                plt.xlabel('Response time (Mins)', fontsize=8)
                locs, ticks = plt.xticks()
                plt.xticks(locs, [f"$10^{{{int(loc)}}}$" for loc in locs])

                plt.subplot(122)
                ((df.timestamp - df.timestamp.shift(1)).dt.seconds
                 .replace(0, np.nan)
                 .div(60)
                 [~(prev_msg_lt_180_seconds & same_prev_author)]
                 .groupby(df.author)
                 .median()
                 .pipe(formatted_barh_plot))
                plt.title('Median response time', fontsize=8)
                plt.ylabel('')
                plt.xlabel('Response time (Mins)', fontsize=8)

                # plt.gcf().text(0, 0, "Excludes messages to self within 3 mins",
                #                va='bottom')
                plt.tight_layout()
                st.pyplot(fig)

                max_spammer, max_spam = spammer(df=df)
                st.write("""
                ## Who is the spammer?
                The most spam is from :red[%s] with %d consecutive 
                messages.""" % (
                    max_spammer, max_spam))

                st.write("""
                ## Year x Month Total Messages
                """)
                year_content = year_month(df=df)
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
                ## Radarchart: Message count per weekday
                # """)
                # fig = radar_chart(df=df)
                # st.pyplot(fig)

                st.write(""" ## Heatmap: Message count per day """)
                fig = heatmap(df=df)
                st.pyplot(fig)

                if locations.shape[0] > 0:
                    st.write(""" ## Map of Locations""")
                    with st.expander("More info"):
                        st.info("This map shows all the locations which are "
                                "sent by the authors via whatsapp. The "
                                "latitude and Longitude values are extracted "
                                "from google maps.")
                    st.map(locations)

                st.cache_data.clear()
                st.cache_resource.clear()


if __name__ == "__main__":
    app()
