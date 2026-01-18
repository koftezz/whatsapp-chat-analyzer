"""
Basic statistics calculations for WhatsApp chat data.
"""

import pandas as pd


def basic_stats(df: pd.DataFrame):
    """
    Calculate mean statistics per author for various message attributes.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Styled DataFrame with formatted percentages and gradient colors
    """
    # Remove 'hour' column if it exists
    if 'hour' in df.columns:
        df = df.drop("hour", axis=1)

    # Calculate mean values for each author
    df_mean = df.groupby('author').mean(numeric_only=True)

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
        "is_media": "Media",
        "is_sticker": "Sticker",
        "is_deleted": "Deleted",
        "is_edited": "Edited",
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
        'Media': '{:.2%}',
        'Sticker': '{:.2%}',
        'Deleted': '{:.2%}',
        'Edited': '{:.2%}',
        'Location': '{:.2%}',
        'Emoji': '{:.2%}'
    }

    # Only format columns that exist in the DataFrame
    format_dict = {k: v for k, v in format_dict.items() if k in df_renamed.columns}

    # Apply styling
    styled_df = df_renamed.style.format(format_dict).background_gradient(axis=0)

    return styled_df


def stats_overall(df: pd.DataFrame):
    """
    Calculate overall distribution of message types across authors.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Styled DataFrame showing percentage distribution per author
    """
    authors = df[["author"]].drop_duplicates()

    # List of columns to process
    columns = [
        "is_image", "is_video", "is_link", "is_conversation_starter",
        "is_gif", "is_audio", "is_media", "is_sticker", "is_deleted",
        "is_edited", "is_location", "is_emoji"
    ]

    # Filter to only columns that exist
    columns = [col for col in columns if col in df.columns]

    # Function to process each column
    def process_column(col):
        temp = df.loc[df[col] == 1]
        if temp[col].sum() == 0:
            return pd.DataFrame({'author': df['author'].unique(), col: 0})
        return pd.DataFrame(temp.groupby("author")[col].sum() / temp[col].sum()).reset_index()

    # Process all columns
    processed_dfs = {col: process_column(col) for col in columns}

    # Merge all processed dataframes with authors
    for col, processed_df in processed_dfs.items():
        authors = pd.merge(authors, processed_df, on=["author"], how="left")

    # Fill NaN values
    authors = authors.fillna({col: 0 for col in columns})

    column_rename = {
        "is_link": "Link",
        "is_conversation_starter": "Is Conversation Starter",
        "is_image": "Image",
        "is_video": "Video",
        "is_gif": "GIF",
        "is_audio": "Audio",
        "is_media": "Media",
        "is_sticker": "Sticker",
        "is_deleted": "Deleted",
        "is_edited": "Edited",
        "is_location": "Location",
        "is_emoji": "Emoji"
    }

    # Only rename columns that exist
    column_rename = {k: v for k, v in column_rename.items() if k in authors.columns}
    authors = authors.rename(columns=column_rename)

    # Apply styling
    format_cols = {col: '{:.2%}' for col in column_rename.values() if col in authors.columns}
    authors = authors.style.format(format_cols).background_gradient(axis=0)

    return authors
