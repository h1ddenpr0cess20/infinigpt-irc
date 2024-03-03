import infinigpt
import os

#put a key here and uncomment if not already set in environment
#os.environ['OPENAI_API_KEY'] = "api_key"

api_key = os.environ.get("OPENAI_API_KEY")
    

# create the bot and connect to the server
personality = "an AI that can assume any personality, named InfiniGPT"  #you can put anything here.  A character, person, personality type, object, concept, emoji, etc
channel = "CHANNEL"
nickname = "NICKNAME"
#password = "PASSWORD" #comment out if unregistered
server = "SERVER"

#check if there is a password
try:
    infinigpt = infinigpt.ircGPT(api_key, personality, channel, nickname, server, password)
except:
    infinigpt = infinigpt.ircGPT(api_key, personality, channel, nickname, server)
    
infinigpt.start()
