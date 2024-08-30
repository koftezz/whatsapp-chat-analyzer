import random

chatter_responses = [
    "Oh joy, :red[{name}] has graced us with {count} messages. Because we were all dying to hear more from them, right? 🙄",
    "Congratulations, :red[{name}]! You've won the 'Most Likely to Wear Out a Keyboard' award with {count} messages. What an achievement. 🏆🙃",
    "Breaking news: :red[{name}] has discovered the 'send' button and used it {count} times. Revolutionary. 👏😒",
    "Alert! :red[{name}] has flooded the chat with {count} messages. I'm sure they're all absolutely riveting. 🙄💤",
    "Well, well, well. :red[{name}] clearly thinks quantity beats quality with their {count} messages. How enlightening. 🤦‍♂️"
]

activity_responses = [
    ":red[{name}] is in {percent}% of conversations. I'm sure we'd all be lost without their constant presence. How ever did we manage before? 🙄",
    "Wow, :red[{name}] is active {percent}% of the time. I guess some people really don't have anything better to do. 🏆🛋️",
    "Look everyone, :red[{name}] has graced {percent}% of our chats with their presence. Whatever would we do without them? 🎭👑",
    "Oh goody, :red[{name}] is here for {percent}% of conversations. Because that's exactly what we all wanted. 🙃📱",
    "Surprise, surprise. :red[{name}] has nothing better to do than be in {percent}% of chats. Living the dream, aren't they? 💤🏅"
]

response_time_responses = [
    "Ah, :red[{name}], our resident sloth when it comes to replying. Your speedy responses are truly awe-inspiring. 🦥⏳",
    "Oh look, :red[{name}] has finally decided to grace us with a response. I'm sure it was worth the wait. 🙄⌛",
    "Breaking news: :red[{name}] responds to messages! ...Eventually. Don't hold your breath, folks. 💀⏰",
    "Congratulations, :red[{name}]! You've won the 'Slowest Fingers in the West' award. Your parents must be so proud. 🐌🏆",
    "Attention: :red[{name}] operates in their own time zone. It's always 'I'll get back to you later o'clock' there. 🌍⏱️"
]

streak_responses = [
    "Wow, :red[{name}] blessed us with {count} consecutive messages. I'm sure they were all absolutely necessary. 🙄📚",
    "Alert: :red[{name}] just discovered the 'send' button and hit it {count} times in a row. Revolutionary. 👏😒",
    "Breaking: :red[{name}] sets new record for most consecutive messages at {count}. Because one just wasn't annoying enough. 🏆🔇",
    "Hold the presses! :red[{name}] just dropped {count} messages in a row. I'm sure we were all on the edge of our seats. 🛋️💤",
    "Attention! :red[{name}] has gone on a {count}-message rampage. I'm sure it's not just the sound of one hand clapping. 👏🦗"
]

def get_random_chatter_response(name, count):
    response = random.choice(chatter_responses)
    return response.format(name=name, count=count)

def get_random_activity_response(name, percent):
    response = random.choice(activity_responses)
    return response.format(name=name, percent=round(percent, 2))

def get_random_response_time_response(name):
    response = random.choice(response_time_responses)
    return response.format(name=name)

def get_random_streak_response(name, count):
    response = random.choice(streak_responses)
    return response.format(name=name, count=count)