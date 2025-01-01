'''
InfiniGPT-IRC
    An OpenAI GPT-3.5-Turbo chatbot for internet relay chat with infinite personalities
    written by Dustin Whyte
    April 2023

'''

import irc.bot
from openai import OpenAI
import time
import textwrap
import threading
import os
import json

class infiniGPT(irc.bot.SingleServerIRCBot):
    def __init__(self, port=6667):
        with open("config.json", "r") as f:
            self.config = json.load(f)
            f.close()

        self.server, self.nickname, self.password, self.channel, self.admin = self.config["irc"].values()
        self.models, self.api_keys, self.default_model, self.default_personality, self.prompt, self.options = self.config["llm"].values()
        self.openai_key, self.xai_key = self.api_keys.values()
        self.personality = self.default_personality

        irc.bot.SingleServerIRCBot.__init__(self, [(self.server, port)], self.nickname, self.nickname)
        self.openai = OpenAI()
        
        self.messages = {}
        self.users = [] 

        self.change_model(self.default_model) 

    #chop up response for irc length limit
    def chop(self, message):
        lines = message.splitlines()
        newlines = []  

        for line in lines:
            if len(line) > 420:
                wrapped_lines = textwrap.wrap(
                    line,
                    width=420,
                    drop_whitespace=False,
                    replace_whitespace=False,
                    fix_sentence_endings=True,
                    break_long_words=False)
                newlines.extend(wrapped_lines) 
            else:
                newlines.append(line) 
        return newlines  
    
    #change between different LLMs
    def change_model(self, model):
        if model in self.models:
            if model.startswith("gpt"):
                self.openai.base_url = 'https://api.openai.com/v1'
                self.openai.api_key = self.openai_key
            elif model.startswith("grok"):
                self.openai.base_url = 'https://api.x.ai/v1/'
                self.openai.api_key = self.xai_key
            else:
                self.openai.base_url = 'http://localhost:11434/v1'

        self.model = self.models[self.models.index(model)]
    
    #resets bot to preset personality per user    
    def reset(self, sender):
        if sender in self.messages:
            self.messages[sender].clear()
            self.persona(self.default_personality, sender)

    def set_prompt(self, c, sender, persona=None, custom=None, respond=True):
        if sender in self.messages:
            self.messages[sender].clear()
        if persona != None and persona != "":
            prompt = self.prompt[0] + persona + self.prompt[1]
        if custom != None  and custom != "":
            prompt = custom
        self.add_history("system", sender, prompt)
        if respond:
            self.add_history("user", sender, "introduce yourself")
            thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
            thread.start()
            thread.join(timeout=30)
            time.sleep(2)

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

    #respond with an AI model           
    def respond(self, c, sender, message, sender2=None):
        try:
            response = self.openai.chat.completions.create(
                model=self.model, 
                messages=self.messages[sender])
            
            response_text = response.choices[0].message.content
            
            #removes any unwanted quotation marks from responses
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')  

            #add the response text to the history before breaking it up
            self.add_history("assistant", sender, response_text)

            #add username before response
            #if .x function used
            if sender2:
                c.privmsg(self.channel, sender2 + ":")
            #normal .ai usage
            else:
                c.privmsg(self.channel, sender + ":")
            time.sleep(1)

            #split up the response to fit irc length limit
            lines = self.chop(response_text)
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)

        except Exception as x: #improve this later with specific errors (token error, invalid request error etc)
            c.privmsg(self.channel, "Something went wrong, try again.")
            print(x)

        #trim history for token size management
        if len(self.messages[sender]) > 20:
            del self.messages[sender][1:3]
        
    def moderate(self, message):
        flagged = False 
        if not flagged:
            try:
                moderate = self.openai.moderations.create(input=message,) 
                flagged = moderate.results[0].flagged #true or false
            except:
                pass
        return flagged

    #when bot joins network, identify and wait, then join channel   
    def on_welcome(self, c, e):
        #if nick has a password
        if self.password != None:
            c.privmsg("NickServ", f"IDENTIFY {self.password}")
            #wait for identify to finish
            time.sleep(5)
        
        #join channel
        c.join(self.channel)

        # get users in channel
        c.send_raw("NAMES " + self.channel)

        #optional join message
        greet = "introduce yourself"
        try:
            response = self.openai.chat.completions.create(model=self.model, 
                    messages=[{"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": "user", "content": greet}])
            response_text = response.choices[0].message.content
            lines = self.chop(response_text + f"  Type .help {self.nickname} to learn how to use me.")
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except:
            pass
            
    def on_nicknameinuse(self, c, e):
        #add an underscore if nickname is in use
        try:
            c.nick(c.get_nickname() + "1")
        except:
            c.nick(c.get_nickname() + "2")

    # actions to take when a user joins 
    def on_join(self, c, e):
        user = e.source
        user = user.split("!")
        user = user[0]
        if user not in self.users:
            self.users.append(user)

    # Optional greeting for when a user joins        
        # greet = f"come up with a unique greeting for the user {user}"
        # if user != self.nickname:
        #     try:
        #         response = self.openai.chat.completions.create(model=self.model, 
        #                 messages=[{"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}, {"role": "user", "content": greet}])
        #         response_text = response.choices[0].message.content
        #         time.sleep(5)
        #         lines = self.chop(response_text)
        #         for line in lines:
        #             c.privmsg(self.channel, line)
        #             time.sleep(2)
        #     except:
        #         pass
            
    # Get the users in the channel
    def on_namreply(self, c, e):
        symbols = {"@", "+", "%", "&", "~"} #symbols for ops and voiced
        userlist = e.arguments[2].split()
        for name in userlist:
            for symbol in symbols:
                if name.startswith(symbol):
                    name = name.lstrip(symbol)
            if name not in self.users:
                self.users.append(name)       

    #process chat messages
    def on_pubmsg(self, c, e):
        #message parts
        message = e.arguments[0]
        sender = e.source
        sender = sender.split("!")
        sender = sender[0]

        #if the bot didn't send the message
        if sender != self.nickname:
            #basic use
            if message.startswith(".ai") or message.startswith(self.nickname):
                msg = message.split(" ", 1)
                msg = msg[1]

                #moderation   
                flagged = self.moderate(msg)  #set to False if you want to bypass moderation
                if flagged:
                    c.privmsg(self.channel, f"{sender}: This message violates OpenAI terms of use and was not sent")
                    
                    #add way to ignore user after a certain number of violations 
                    #maybe like 3 flagged messages gets you ignored for a while

                else:
                    #add to history and start respond thread
                    self.add_history("user", sender, msg)
                    thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                    thread.start()
                    thread.join(timeout=30)
                    time.sleep(2) #help prevent mixing different users' output

            #collborative use
            if message.startswith(".x "):
                msg = message.split(" ", 2)
                msg.pop(0)
                if len(msg) > 1:
                    #get users in channel
                    c.send_raw("NAMES " + self.channel)

                    #check if the message starts with a name in the history
                    for name in self.users:
                        if type(name) == str and msg[0] == name:
                            user = msg[0]
                            msg = msg[1]
                            
                            #if so, respond, otherwise ignore
                            if user in self.messages:
                                flagged = self.moderate(msg)  #set to False if you want to bypass moderation
                                if flagged:
                                    c.privmsg(self.channel, f"{sender}: This message violates OpenAI terms of use and was not sent")
                                    #add way to ignore user after a certain number of violations

                                else:
                                    self.add_history("user", user, msg)
                                    thread = threading.Thread(target=self.respond, args=(c, user, self.messages[user],), kwargs={'sender2': sender})
                                    thread.start()
                                    thread.join(timeout=30)
                                    time.sleep(2)
                            
            #change personality    
            if message.startswith(".persona "):
                msg = message.split(" ", 1)
                msg = msg[1]
                #check if it violates ToS
                flagged = self.moderate(msg) #set to False if you want to bypass moderation
                if flagged:
                    c.privmsg(self.channel, f"{sender}: This persona violates OpenAI terms of use and was not set.")
                    #add way to ignore user after a certain number of violations
                else:
                    self.set_prompt(c, sender, persona=msg)
            #use custom prompts 
            if message.startswith(".custom "):
                msg = message.split(" ", 1)
                msg = msg[1]
                #check if it violates ToS
                flagged = self.moderate(msg) #set to False if you want to bypass moderation
                if flagged:
                    c.privmsg(self.channel, f"{sender}: This custom prompt violates OpenAI terms of use and was not set.")
                    #add way to ignore user after a certain number of violations
                else:
                    self.set_prompt(c, sender, custom=msg)
                    
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
            
            #list models
            if message == ".model":
                c.privmsg(self.channel, f"Current model: {self.model}")
                c.privmsg(self.channel, "Available models:")
                for line in self.chop(", ".join(self.models)):
                    c.privmsg(self.channel, line)
                    time.sleep(.5)
            #change model if admin
            if message.startswith(".model ") and sender == self.admin:
                model = message.split(" ", 1)[1]
                if model in self.models:
                    self.change_model(model)
                    c.privmsg(self.channel, f"Model set to {self.model}")
                elif model == "reset":
                    self.change_model(self.default_model)
                    c.privmsg(self.channel, f"Model set to {self.model}")
                else:
                    c.privmsg(self.channel, "Try again")

            #help menu    
            if message.startswith(f".help {self.nickname}"):
                with open("help.txt", "r") as f:
                    help_text = f.readlines()
                for line in help_text:
                    c.notice(sender, line.strip())
                    time.sleep(1)
                
if __name__ == "__main__":
    infiniGPT = infiniGPT()
    infiniGPT.start()

