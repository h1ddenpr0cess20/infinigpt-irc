import infinibot
import openai

# Set up the OpenAI API client
openai.api_key = "API_KEY"

# create the bot and connect to the server
personality = "an AI that goes above and beyond, named InfiniBot" #you can put anything here.  A character, person, personality type, object, concept, use your imagination.
channel = "#CHANNEL"
nickname = "NICKNAME"
#password = "PASSWORD" #comment out if unregistered
server = "SERVER"

#check if there is a password
try:
    infinibot = infinibot.ircGPT(personality, channel, nickname, server, password)
except:
    infinibot = infinibot.ircGPT(personality, channel, nickname, server)
    
infinibot.start()
