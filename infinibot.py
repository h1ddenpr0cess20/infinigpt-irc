import irc.bot
import openai
import time
import textwrap
import threading

  
class ircGPT(irc.bot.SingleServerIRCBot):
    def __init__(self, personality, channel, nickname, server, password=None, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        
        self.personality = personality
        self.channel = channel
        self.server = server
        self.nickname = nickname
        self.password = password

        self.messages = {} #Holds chat history
        self.users = [] #List of users in the channel
        
        self.symbols = {"@", "+", "%", "&", "~"} #symbols for ops and voiced, need to strip them from nicks

        self.prompt = ("assume the personality of ", ".  roleplay and always stay in character unless instructed otherwise.  keep your first response short.")

    #resets bot to preset personality per user    
    def reset(self, sender):
        self.messages[sender].clear()
        self.persona(self.personality, sender)

    #sets the bot personality 
    def persona(self, persona, sender):
        #clear existing history
        if sender in self.messages:
            self.messages[sender].clear()
        #my personally engineered prompt
        personality = self.prompt[0] + persona + self.prompt[1]
        self.add_history("system", sender, personality)

    #adds messages to self.messages    
    def add_history(self, role, sender, message):
        if sender in self.messages:
            self.messages[sender].append({"role": role, "content": message})
        else:
            if role == "system":
                self.messages[sender] = [{"role": role, "content": message}]
            else:
                self.messages[sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]

    #respond with gpt-3.5-turbo           
    def respond(self, c, sender, message, sender2=None):
        try:
            response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=self.messages[sender])
        except openai.error.InvalidRequestError:
            c.privmsg(self.channel, "Token size too large, try .reset")
        except openai.error.APIError:
            c.privmsg(self.channel, "Error")
        except Exception as x:
            print(x)
        try:
            response_text = response['choices'][0]['message']['content']
        except:
            c.privmsg(self.channel, "Something went wrong, try again.")
        self.add_history("assistant", sender, response_text)
        #if .x function used
        if sender2:
            c.privmsg(self.channel, sender2 + ":")
        #normal .ai usage
        else:
            c.privmsg(self.channel, sender + ":")
        time.sleep(1)
        #split up the response to fit irc length limit
        lines = response_text.splitlines()
        
        for line in lines:
            if len(line) > 420:
                    newlines = textwrap.wrap(line, width=420, drop_whitespace=False, replace_whitespace=False, fix_sentence_endings=True, break_long_words=False)
                    for line in newlines:
                        c.privmsg(self.channel, line)
            else: 
                c.privmsg(self.channel, line)    
            time.sleep(2)
            
        #trim history for token size management
        if len(self.messages) > 14:
            del self.messages[1:3]
        
    #run message through moderation endpoint for ToS check        
    def moderate(self, message):
        flagged = False
        if not flagged:
            moderate = openai.Moderation.create(input=message,) #run through the moderation endpoint
            flagged = moderate["results"][0]["flagged"] #true or false
        return flagged

              
    #when bot joins network, identify and wait, then join channel   
    def on_welcome(self, c, e):
        #if nick has a password
        if self.password != None:
          c.privmsg(f"NickServ", "IDENTIFY {self.password}")
          #wait for identify to finish
          time.sleep(5)
        
        c.join(self.channel)
        #optional join message
        c.privmsg(self.channel, f"I'm an OpenAI chatbot.  Type .help {self.nickname} for more info")
        
    def on_nicknameinuse(self, c, e):
        #add an underscore if nickname is in use
        c.nick(c.get_nickname() + "_")

    # actions to take when a user joins 
    # comment this function out if you find it annoying
    def on_join(self, c, e):
        sender = e.source
        sender = sender.split("!")
        sender = sender[0]
        greet = f"come up with a unique greeting for the user {sender}"
        if sender != self.nickname:
            try:
                response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                                                                                         {"role": "user", "content": greet}])
                response_text = response['choices'][0]['message']['content']
            except Exception as x:
                print(x)
            time.sleep(3)
            c.privmsg(self.channel, response_text)

    #gets the userlist
    def on_namreply(self, c, e):
        userlist = e.arguments[2].split()
        for name in userlist:
            for symbol in self.symbols:
                if name.startswith(symbol):
                    name = name.lstrip(symbol)
            if name not in self.users:
                self.users.append(name)

    #process chat messages
    def on_pubmsg(self, c, e):
        #get the users in channel each time a message is sent
        c.send_raw("NAMES " + self.channel)

        #message parts
        message = e.arguments[0]
        sender = e.source
        sender = sender.split("!")
        sender = sender[0]

        #if the bot didn't send the message
        if sender != self.nickname:
            #basic use
            if message.startswith(".ai") or message.startswith(self.nickname):
                if message.startswith(".ai"):
                    message = message.lstrip(".ai")
                    message = message.strip()
                else:
                    message = message.lstrip(self.nickname)
                    #allows both botname: <message> and botname <message> to work
                    if message.startswith(":"):
                        message.lstrip(":")
                    message = message.strip()

                #moderation   
                flagged = self.moderate(message)
                if flagged:
                    c.privmsg(self.channel, f"{sender}: This message violates OpenAI terms of use and was not sent")
                else:
                    #add to history and start responder thread
                    self.add_history("user", sender, message)
                    thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                    thread.start()
                    thread.join(timeout=30)
                    time.sleep(2) #help prevent mixing user output

            #collborative use
            if message.startswith(".x "):
                message = message.lstrip(".x")
                message = message.strip()
                for name in self.users:
                    if type(name) == str and message.startswith(name):
                        user = name
                        message = message.lstrip(user)
                        if user in self.messages:
                            self.add_history("user", user, message)
                            thread = threading.Thread(target=self.respond, args=(c, user, self.messages[user],), kwargs={'sender2': sender})
                            thread.start()
                            thread.join(timeout=30)
                            time.sleep(2)
                            
            #change personality    
            if message.startswith(".persona "):
                message = message.lstrip(".persona")
                message = message.strip()
                #check if it violates ToS
                flagged = self.moderate(message)
                if flagged:
                    c.privmsg(self.channel, f"{sender}: This persona violates OpenAI terms of use and was not set.")
                else:
                    self.persona(message, sender)
                    thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                    thread.start()
                    thread.join(timeout=30)
                    time.sleep(2)
                    
            #reset to default personality    
            if message.startswith(".reset"):
                self.reset(sender)
                c.privmsg(self.channel, f"{self.nickname} reset to default for {sender}.")

            #stock GPT settings    
            if message.startswith(".stock"):
                if sender in self.messages:
                    self.messages[sender].clear()
                else:
                    self.messages[sender] = []                    
                c.privmsg(self.channel, f"Stock settings applied for {sender}")

            #help menu    
            if message.startswith(".help {}".format(self.nickname)):
                help = [
                    "I am an OpenAI chatbot.  I can have any personality you want me to have.  Each user has their own chat history and personality setting.",
                    f".ai <message> or {self.nickname}: <message> to talk to me.", ".x <user> <message> to talk to another user's history for collaboration.",
                    ".persona <personality> to change my personality. I can be any personality type, character, inanimate object, place, concept.",
                    f".reset to reset to my default personality, {self.personality}.", ".stock to set to stock GPT settings.", 
                    "Available at https://github.com/h1ddenpr0cess20/infinibot-irc"

                ]
                for line in help:
                    c.privmsg(self.channel, line)
                    time.sleep(1)
                
if __name__ == "__main__":

    # Set up the OpenAI API client
    openai.api_key = "API_KEY"

    # create the bot and connect to the server
    
    personality = "an AI that goes above and beyond, named InfiniBot" #you can put anything here.  A character, person, personality type, object, concept, use your imagination.
    channel = "#CHANNEL"
    nickname = "NICKNAME"
    password = "PASSWORD"
    server = "SERVER"
    
    #checks if password variable exists (comment it out if unregistered)
    try:
      infinibot = ircGPT(personality, channel, nickname, server, password)
    except:
      infinibot = ircGPT(personality, channel, nickname, server)
      
    infinibot.start()

