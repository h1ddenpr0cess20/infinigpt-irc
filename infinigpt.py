'''
InfiniGPT-IRC
    An AI chatbot for internet relay chat with infinite personalities
    Supports OpenAI, xAI, and Ollama models

    written by Dustin Whyte

'''

import irc.bot
from openai import OpenAI
import time
import textwrap
import threading
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
    
    def change_model(self, c, channel=False, model=False):
        if model:
            try:
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
                    if channel:
                        c.privmsg(self.channel, f"Model set to {self.model}")
            except:
                pass
        else:
            if channel:
                current_model = [f"Current model: {self.model}", f"Available models: {', '.join(sorted(list(self.models)))}"]
                for line in current_model:
                    c.privmsg(self.channel, line)
                
    def reset(self, c, sender, stock=False):
        if sender in self.messages:
            self.messages[sender].clear()
        else:
            self.messages[sender] = []
        if not stock:
            self.set_prompt(c, sender, persona=self.default_personality, respond=False)
            c.privmsg(self.channel, f"{self.nickname} reset to default for {sender}")
        else:
            c.privmsg(self.channel, f"Stock settings applied for {sender}")

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
        if len(self.messages[sender]) > 24:
            if self.messages[sender][0]["role"] == "system":
                del self.messages[sender][1:3]
            else:
                del self.messages[sender][0:2]

    def respond(self, c, sender, message, sender2=None):
        try:
            response = self.openai.chat.completions.create(
                model=self.model, 
                messages=message)
            
            response_text = response.choices[0].message.content
            
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')  

            self.add_history("assistant", sender, response_text)

            if sender2:
                c.privmsg(self.channel, sender2 + ":")
            else:
                c.privmsg(self.channel, sender + ":")
            time.sleep(1)

            lines = self.chop(response_text)
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)

        except Exception as x: 
            c.privmsg(self.channel, "Something went wrong, try again.")
            print(x)
        
    def moderate(self, message):
        flagged = False 
        if not flagged:
            try:
                moderate = self.openai.moderations.create(model="omni-moderation-latest", input=message) 
                flagged = moderate.results[0].flagged
            except:
                pass
        return flagged

    def on_welcome(self, c, e):
        self.change_model(c, model=self.default_model)
        if self.password != None:
            c.privmsg("NickServ", f"IDENTIFY {self.password}")
            time.sleep(5)
        
        c.join(self.channel)

        greet = "introduce yourself"
        try:
            response = self.openai.chat.completions.create(model=self.model, 
                    messages=[{"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": "user", "content": greet}])
            response_text = response.choices[0].message.content
            lines = self.chop(response_text + f"  Type .help to learn how to use me.")
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except:
            pass
            
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_join(self, c, e):
        user = e.source
        user = user.split("!")
        user = user[0]

    # # Optional greeting for when a user joins        
    #     greet = f"come up with a unique greeting for the user {user}"
    #     if user != self.nickname:
    #         try:
    #             response = self.openai.chat.completions.create(
    #                 model=self.model, 
    #                 messages=[
    #                     {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}, 
    #                     {"role": "user", "content": greet}
    #                 ]
    #             )
    #             response_text = response.choices[0].message.content
    #             time.sleep(5)
    #             lines = self.chop(response_text)
    #             for line in lines:
    #                 c.privmsg(self.channel, line)
    #                 time.sleep(2)
    #         except:
    #             pass
            
    def ai(self, c, e, sender, message, x=False):
        if x and message[2]:
            name = message[1]
            message = ' '.join(message[2:])
            if not self.moderate(message):
                if name in self.messages:
                    self.add_history("user", name, message)
                    thread = threading.Thread(target=self.respond, args=(c, name, self.messages[name],), kwargs={'sender2': sender})
                    thread.start()
                    thread.join(timeout=30)
                else:
                    pass
            else:
                c.privmsg(self.channel, f"{sender}: This message violates OpenAI terms of use and was not sent")
                
        else:
            message = ' '.join(message[1:])
            if not self.moderate(message):        
                self.add_history("user", sender, message)
                thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                thread.start()
                thread.join(timeout=30)
            else:
                c.privmsg(self.channel, f"{sender}: This message violates OpenAI terms of use and was not sent")
        time.sleep(2)

    def help_menu(self, c, sender):
        with open("help.txt", "r") as f:
            help_text = f.readlines()
        for line in help_text:
            c.notice(sender, line.strip())
            time.sleep(1)

    def handle_message(self, c, e, sender, message):
        user_commands = {
            ".ai": lambda: self.ai(c, e, sender, message),
            f"{self.nickname}:": lambda: self.ai(c, e, sender, message),
            ".x": lambda: self.ai(c, e, sender, message, x=True),
            ".persona": lambda: self.set_prompt(c, sender, persona=' '.join(message[1:])),
            ".custom": lambda: self.set_prompt(c, sender, custom=' '.join(message[1:])),
            ".reset": lambda: self.reset(c, sender),
            ".stock": lambda: self.reset(c, sender, stock=True),
            f".help": lambda: self.help_menu(c, sender),
        }
        admin_commands = {
            ".model": lambda: self.change_model(c, channel=True, model=message[1] if len(message) > 1 else False)
        }

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
            action()
        if sender == self.admin and command in admin_commands:
            action = admin_commands[command]
            action()

    def on_pubmsg(self, c, e):
        message = e.arguments[0].split(" ")
        sender = e.source
        sender = sender.split("!")
        sender = sender[0]

        if sender != self.nickname:
            self.handle_message(c, e, sender, message)

if __name__ == "__main__":
    infiniGPT = infiniGPT()
    infiniGPT.start()

