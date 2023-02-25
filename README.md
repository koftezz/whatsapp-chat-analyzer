# whatsapp-chat-analyzer
A Streamlit application for analyzing Whatsapp Group Chat. See [here](https://whats-chat-detective.streamlit.app/)

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
