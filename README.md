# whatsapp-chat-analyzer
A Streamlit application for analyzing Whatsapp Group Chat. See [here](https://koftezz-whatsapp-chat-analyzer-streamlit-app-96gt93.streamlit.app/)

V0.1 2023-02-21:
### What's New?
- GIF, Sticker, Audio Message Statistics.

### About
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
    - Is conversation starter with a slider
    - Add emoji support
    - Exportable pdf
 - Last but not least - Thanks to [chat-miner](
 https://github.com/joweich/chat-miner) for easy whatsapp parsing tool and 
 their awesome charts. Thanks to [Dinesh Vatvani](https://dvatvani.github.io/whatsapp-analysis.html) 
 for his great analysis.
