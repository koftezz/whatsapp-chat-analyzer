from helpers import *
import altair as alt
from responses import *

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
def show_github_sponsor():
    st.markdown("""
        <a href="https://github.com/sponsors/koftezz" style="text-decoration: none;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg height="16" viewBox="0 0 16 16" version="1.1" width="16" aria-hidden="true" fill="#db61a2">
                    <path fill-rule="evenodd" d="M4.25 2.5c-1.336 0-2.75 1.164-2.75 3 0 2.15 1.58 4.144 3.365 5.682A20.565 20.565 0 008 13.393a20.561 20.561 0 003.135-2.211C12.92 9.644 14.5 7.65 14.5 5.5c0-1.836-1.414-3-2.75-3-1.373 0-2.609.986-3.029 2.456a.75.75 0 01-1.442 0C6.859 3.486 5.623 2.5 4.25 2.5zM8 14.25l-.345.666-.002-.001-.006-.003-.018-.01a7.643 7.643 0 01-.31-.17 22.075 22.075 0 01-3.434-2.414C2.045 10.731 0 8.35 0 5.5 0 2.836 2.086 1 4.25 1 5.797 1 7.153 1.802 8 3.02 8.847 1.802 10.203 1 11.75 1 13.914 1 16 2.836 16 5.5c0 2.85-2.045 5.231-3.885 6.818a22.08 22.08 0 01-3.744 2.584l-.018.01-.006.003h-.002L8 14.25zm0 0l.345.666a.752.752 0 01-.69 0L8 14.25z"></path>
                </svg>
                <span style="color: #db61a2;">Sponsor on GitHub</span>
            </div>
        </a>
    """, unsafe_allow_html=True)

st.cache_data.clear()
st.cache_resource.clear()
st.write("""
         ## Whatsapp Group Chat Analyzer
         """)
show_github_sponsor()

with st.expander("🌟 Discover the Magic Behind This App"):
    st.markdown(
        """
    ### About This App

    - Your privacy is important: We don't store any of your chat data.

    - Languages: The app currently works with English, Turkish, and German chats. We're working on adding more languages.

    - Flexible analysis: You can analyze both group chats and direct messages.

    - Date format note: WhatsApp date formats can sometimes cause issues. If you get an error, please check that the dates in your file are consistent.

    - Processing time: It usually takes about 2 minutes to process a 20MB chat file.

    - Open source: You can view our source code on [GitHub](https://github.com/koftezz/whatsapp-chat-analyzer).

    - Acknowledgements: 
      - Thanks to [chat-miner](https://github.com/joweich/chat-miner) for their WhatsApp parsing tool.
      - Thanks to [Dinesh Vatvani](https://dvatvani.github.io/whatsapp-analysis.html) for inspiration.

    We hope you find some interesting insights in your chat data!
    """
    )

# usage instructions
with st.expander("📚 Usage Instructions"):
    st.markdown(
        """
    ### How to Use This App
    - For demo purposes, you can use the sample chat file provided. Download it and upload it.
    - For your own chat file, follow these steps:
    - **Upload Your Chat File:**
      - Click the "Upload" button and select your WhatsApp chat file.
      - Ensure the file is a .txt format.
      - Select the authors of the group.
      - Select the language of the chat.
      - Click "Submit".

    - **View the Analysis:**
      - The app will process your chat file and display various analyses and visualizations.
      - You can download the processed data as a CSV file.

    - **Explore the Data:**
      - Use the interactive charts and tables to explore the data.
      - Click on different authors to see their messaging patterns.
      """)

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
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            # first three entry is most likely is the group creation.
            df = df[3:]
            author_list = df["author"].drop_duplicates().tolist()
            with st.form(key='my_form_to_submit'):

                selected_authors = st.multiselect(
                    "Choose authors of the group",
                    author_list)
                selected_lang = st.radio(
                    "What\'s your Whatsapp Language?",
                    ("English", 'Turkish', "German"))
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

                # Calculate summary
                summary = calculate_chat_summary(df)

                # Create the summary message
                st.markdown("""
                ## 📊 Chat Snapshot: Your Digital Conversation at a Glance
                """)

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Messages", f"{summary['total_messages']:,}")
                    st.metric("Unique Participants", summary['unique_authors'])
                    st.metric("Average Messages/Day", f"{summary['avg_messages_per_day']:.1f}")

                with col2:
                    st.metric("Chat Duration", f"{summary['total_days']} days")
                    st.metric("Most Active Chatter", summary['most_active_author'])
                    st.metric("Their Message Count", f"{summary['most_active_author_messages']:,}")

                st.markdown(f"""
                📅 From {summary['start_date'].strftime('%B %d, %Y')} to {summary['end_date'].strftime('%B %d, %Y')}

                🏆 **{summary['most_active_author']}** leads the chat with **{summary['most_active_author_percentage']:.1f}%** of all messages!

                Ready to uncover more insights? Let's dive deeper into your chat data! 🕵️‍♂️📱
                """)

                # Basic summary of messages
                st.write("## Average Message Characteristics")
                with st.expander("Explanation of Metrics"):
                    st.write(
                        "This table shows the average values for various message characteristics per author. "
                        "Here's what each metric means:\n\n"
                        "- **Words**: Average number of words per message\n"
                        "- **Message Length**: Average number of characters per message\n"
                        "- **Link**: Percentage of messages containing a link\n"
                        "- **Conversation Starter**: Percentage of messages that started a new conversation "
                        "(defined as a message sent at least 7 hours after the previous message)\n"
                        "- **Image/Video/GIF/Audio/Sticker**: Percentage of messages containing each media type\n"
                        "- **Deleted**: Percentage of messages that were deleted\n"
                        "- **Emoji**: Percentage of messages containing at least one emoji\n"
                        "- **Location**: Percentage of messages sharing a location\n"
                    )
                print(df.columns)
                o = basic_stats(df=df)
                st.dataframe(o, use_container_width=True)

                # Basic summary of messages
                st.write("## Overall Chat Statistics (Aggregated)")
                with st.expander("More info"):
                    st.info(
                        "This section provides a summary of key statistics aggregated across all authors in the chat. "
                        "Unlike the 'Average Message Characteristics' table above, which shows per-author averages, "
                        "this table presents overall totals and averages for the entire conversation. "
                        "It gives you a bird's-eye view of the general chat activity and patterns, "
                        "helping you understand the overall dynamics of the conversation without breaking it down by individual authors."
                    )
                o = stats_overall(df=df)
                st.dataframe(o)

                st.write("## Talkativeness & Messaging Trends")
                with st.expander("More info"):
                    st.info(
                        "This section provides insights into each author's messaging patterns and trends. "
                        "It includes metrics such as the total number of messages, percentage of total messages, "
                        "and a qualitative 'Talkativeness' rating. Additionally, it shows messaging trends over "
                        "the last 3, 6, and 12 months, helping you understand how each author's participation "
                        "has changed over time."
                    )
                author_df = trend_stats(df=df)
                st.dataframe(author_df, use_container_width=True)

                # Total messages sent stats
                st.write("## Number of Messages Sent By Author")
                message_counts = get_message_count_by_author(df)
                most_active, total_msg = get_most_active_author(message_counts)
                
                chatter_response = get_random_chatter_response(most_active, total_msg)
                st.write(chatter_response)

                chart = create_message_count_chart(message_counts)
                st.altair_chart(chart)

                # Most used emoji
                st.write("## Most Used Emoji")
                emoji_counts = get_most_used_emoji(df)
                st.dataframe(emoji_counts)

                # Activity Stats by Author
                st.write("## Author Participation in Group Conversations")
                activity_stats = get_activity_stats(df)
                
                activity_response = get_random_activity_response(
                    activity_stats['most_active'],
                    activity_stats['most_active_perc']
                )
                st.write(activity_response)
                
                with st.expander("More info"):
                    st.info(
                        "This chart displays the percentage of days each author participated in group conversations. "
                        "An 'active day' is counted when an author sends at least one message. "
                        "The higher the percentage, the more consistently an author engages in the chat. "
                        "This metric helps identify the most regular participants, regardless of message volume."
                    )
                
                st.altair_chart(activity_stats['chart'])

                # Smoothed stacked activity area timeseries plot
                st.write("""## Message Volume Trends Over Time""")
                with st.expander("More info"):
                    min_year = df.year.max() - 3
                    st.info(
                        "This chart displays the smoothed daily message volume for each author over the last 3 years. "
                        "Key points:\n"
                        "- It shows absolute message counts, allowing you to compare activity levels between authors.\n"
                        "- The data is smoothed using a Gaussian distribution to reduce noise and highlight overall trends.\n"
                        f"- The chart covers the period from {min_year} to {df.year.max()}.\n"
                        "- Stacked areas represent each author's contribution to the total message volume."
                    )
                smoothed_daily_activity_df = smoothed_daily_activity(df=df, years=3)
                st.area_chart(smoothed_daily_activity_df)

                # Relative activity timeseries - 100% stacked area plot
                st.write("""
                    ## Relative Message Activity Over Time
                    """)
                with st.expander("More info"):
                    min_year = df.year.max() - 3
                    st.info(
                        "This chart shows the relative message activity of each author over the last 3 years.\n\n"
                        "Key points:\n"
                        "- The y-axis represents the percentage of total messages sent by each author on a given day.\n"
                        "- The areas are stacked to always total 100%, allowing you to see how each author's relative contribution changes over time.\n"
                        "- Data is smoothed using a Gaussian distribution to reduce daily fluctuations and highlight overall trends.\n"
                        f"- The chart covers the period from {min_year} to {df.year.max()}.\n"
                        "- This visualization helps identify shifts in group dynamics and individual participation patterns."
                    )
                o = relative_activity_ts(df=df, years=3)
                st.area_chart(o)

                # Timeseries: Activity by time of day
                st.write("""
                    ## Message Activity by Time of Day
                    """)
                time_of_day_data = activity_time_of_day_ts(df)
                st.altair_chart(time_of_day_data)
                
                # Timeseries: Activity by day of week
                st.write("""
                    ## Message Activity by Day of Week
                    """)
                # add info section
                with st.expander("More info"):
                    st.info(
                        "This chart displays the average message activity for each day of the week. "
                        "It shows the percentage of total messages sent on each day of the week, "
                        "with each author represented by a different color. "
                        "This visualization helps identify which days of the week are most active for messaging."
                    )
                day_of_week_data = activity_day_of_week_ts(df)
                st.altair_chart(day_of_week_data)
                
                # Response matrix
                st.write("""
                    ## Author Interaction: Response Matrix
                    """)
                with st.expander("More info"):
                    st.info("This matrix shows how often each author responds to messages from other authors. "
                            "The percentages indicate the proportion of an author's messages that are responses to each other author. "
                            "Note: This analysis excludes messages sent by an author to themselves within a 3-minute window.")

                response_chart = response_matrix(df)

                st.altair_chart(response_chart, use_container_width=True)

                st.write("""
                    ## Response Time Analysis
                    """)
                with st.expander("More info"):
                    st.info("Self consecutive messages within 3 minutes are excluded. "
                            "The distribution chart shows the frequency of response times for each author on a logarithmic scale. "
                            "The median response time chart shows the typical time an author takes to respond to messages.")

                response_time_analysis = analyze_response_time(df)

                #st.altair_chart(response_time_analysis['distribution_chart'], use_container_width=True)
                st.altair_chart(response_time_analysis['median_chart'], use_container_width=True)

                slowest_responder = response_time_analysis['slowest_responder']
                response_time_message = get_random_response_time_response(slowest_responder)
                st.write(response_time_message)

                st.write("## Consecutive Message Analysis")

                streak_info = find_longest_consecutive_streak(df)

                # Get a random response
                streak_response = get_random_streak_response(streak_info['author'], streak_info['streak_length'])
                st.write(streak_response)
                # Display the streak messages
                st.write("Streak Messages:")
                st.dataframe(streak_info['streak_messages'])

                st.write("## Monthly Message Volume Analysis")

                with st.expander("More Info"):
                    st.write("This chart shows the total number of messages sent each month over time. "
                             "The red line represents the average monthly message count. "
                             "Each bar is colored by year for easy year-over-year comparison.")
                monthly_analysis = analyze_monthly_messages(df)

                st.write(f"🏆 New monthly record! A total of {monthly_analysis['total_messages']} messages "
                         f"were sent in {monthly_analysis['peak_month']}. 💥")

                st.altair_chart(monthly_analysis['chart'], use_container_width=True)

                #st.write("""
                #    ## Sunburst: Message Distribution by Day and Hour
                #    """)

                #with st.expander("More info"):
                #    st.info("These sunburst charts show the distribution of messages by day of the week and hour of the day. "
                #            "The inner ring represents days of the week, and the outer ring represents hours of the day. "
                #            "The size and color of each segment indicate the number of messages.\n\n"
                #            "- Left chart: Highlights the most active times (larger segments are ordered first).\n"
                #            "- Right chart: Shows a more even distribution (smaller segments are ordered first).")

                # create the sunburst chart
                #chart1, chart2 = create_sunburst_charts(df)

                #col1, col2 = st.columns(2)
                #with col1:
                #    st.altair_chart(chart1)
                #with col2:
                #    st.altair_chart(chart2)

                st.write(""" ## Heatmap: Message count per day """)
                with st.expander("More Info"):
                    st.info("This heatmap shows the number of messages sent each day. "
                            "The x-axis represents weeks, the y-axis represents days of the week, "
                            "and the color intensity indicates the number of messages. "
                            "The chart is faceted by year for easy year-over-year comparison. "
                            "Hover over a cell to see the exact date and message count.")
                heatmap_chart = heatmap(df)
                st.altair_chart(heatmap_chart, use_container_width=True)
                

                st.write("## Word Cloud of Most Frequently Used Words")
                with st.expander("More Info"):
                    st.info("This word cloud displays the most frequently used words in the chat. "
                            "The size of each word is proportional to its frequency of occurrence. "
                            "This visualization helps identify the most common words used in the chat, "
                            "which can provide insights into the chat's topics and themes.")
                word_cloud = create_word_cloud(df)
                st.image(word_cloud)

                st.cache_data.clear()
                st.cache_resource.clear()


if __name__ == "__main__":
    app()
