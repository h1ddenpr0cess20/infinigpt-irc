'''
InfiniGPT-IRC
    An AI chatbot for IRC with infinite personalities
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
    """
    An IRC bot that integrates with the OpenAI API, allowing interaction 
    with customizable personalities and models.
    Supports OpenAI, xAI, Google, and Ollama models.

    Attributes:
        config_file (str): Path to the configuration file.
        server (str): The IRC server address.
        nickname (str): The bot's nickname.
        password (str): Password for NickServ identification.
        channel (str): The IRC channel the bot will join.
        admin (str): Admin username.
        models (list): Available models for the chatbot.
        api_keys (dict): API keys for OpenAI, xAI, and Google.
        default_model (str): Default model to use.
        default_personality (str): Default personality for the chatbot.
        prompt (list): Default system prompt structure.
        options (dict): Options for the API requests.
        openai_key (str): OpenAI API key.
        xai_key (str): xAI API key.
        google_key (str): Google API key.
        personality (str): Current personality in use.
        openai: OpenAI client instance.
        messages (dict): History of conversations per user.
    """
    def __init__(self, port=6667):
        """
        Initialize the bot with configuration and setup.

        Args:
            port (int): Port to connect to the IRC server. Defaults to 6667.
        """
        with open("config.json", "r") as f:
            self.config = json.load(f)
            f.close()

        self.server, self.nickname, self.password, self.channel, self.admin = self.config["irc"].values()
        self.models, self.api_keys, self.default_model, self.default_personality, self.prompt, self.options = self.config["llm"].values()
        self.openai_key, self.xai_key, self.google_key = self.api_keys.values()
        self.personality = self.default_personality

        irc.bot.SingleServerIRCBot.__init__(self, [(self.server, port)], self.nickname, self.nickname)
        self.openai = OpenAI()
        
        self.messages = {}

    def chop(self, message):
        """
        Break a message into lines of at most 420 characters, preserving whitespace.

        Args:
            message (str): The message to be chopped.

        Returns:
            newlines (list): A list of strings, each within the 420-character limit.
        """
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
        """
        Change the large language model or list available models.

        Args:
            c: IRC connection object.
            channel (bool): Whether to send messages to the channel. Defaults to False.
            model (str): The model to switch to. Defaults to False.
        """
        if model:
            try:
                if model in self.models:
                    if model.startswith("gpt"):
                        self.openai.base_url = 'https://api.openai.com/v1'
                        self.openai.api_key = self.openai_key
                        self.params = self.options
                    elif model.startswith("grok"):
                        self.openai.base_url = 'https://api.x.ai/v1/'
                        self.openai.api_key = self.xai_key
                        self.params = self.options
                    elif model.startswith("gemini"):
                        self.openai.base_url = 'https://generativelanguage.googleapis.com/v1beta/openai/'
                        self.openai.api_key = self.google_key
                        self.params = {key: value for key, value in self.options.items() if key != 'frequency_penalty'} #unsupported with gemini
                    else:
                        self.openai.base_url = 'http://localhost:11434/v1'
                        self.params = self.options

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
        """
        Reset the chat history for a user and optionally apply default settings.

        Args:
            c: IRC connection object.
            sender (str): The user initiating the reset.
            stock (bool): Whether to apply stock settings. Defaults to False.
        """
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
        """
        Set a custom or personality-based prompt for a user.

        Args:
            c: IRC connection object.
            sender (str): The user for whom the prompt is being set.
            persona (str): Predefined personality. Defaults to None.
            custom (str): Custom prompt. Defaults to None.
            respond (bool): Whether to initiate a response. Defaults to True.
        """
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
        """
        Append a message to the user's conversation history.

        Args:
            role (str): The role of the message sender (e.g., 'user', 'assistant', 'system').
            sender (str): The user for whom the message is being added.
            message (str): The message content.
        """
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
        """
        Generate and send a response to a user.

        Args:
            c: IRC connection object.
            sender (str): The user to respond to.
            message (list): The conversation history.
            sender2 (str): Recipient for the response if the .x function was used.  Defaults to None.
        """
        try:
            response = self.openai.chat.completions.create(
                model=self.model, 
                messages=message,
                **self.params)
            
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
        """
        Check if message violates OpenAI terms of service if OpenAI used.

        Args:
            message (str): The message content.

        Returns:
            flagged (bool): Whether or not the message violates OpenAI terms of service.
        """
        flagged = False 
        if not flagged:
            try:
                moderate = self.openai.moderations.create(model="omni-moderation-latest", input=message) 
                flagged = moderate.results[0].flagged
            except:
                pass
        return flagged

    def on_welcome(self, c, e):
        """
        Handle the welcome event and join the configured channel.

        Args:
            c: IRC connection object.
            e: IRC event object.
        """
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
        """
        Handle the nickname-in-use event by appending an underscore to the nickname.

        Args:
            c: IRC connection object.
            e: IRC event object.
        """
        c.nick(c.get_nickname() + "_")

    def on_join(self, c, e):
        """
        Handle the join event to extract and optionally use the username to generate a greeting.

        Args:
            c: IRC connection object.
            e: IRC event object.
        """
        user = e.source.split("!")[0]

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
        """
        Process AI-related commands for generating responses.

        Args:
            c: IRC connection object.
            e: IRC event object.
            sender (str): The user initiating the command.
            message (list): The command and arguments.
            x (bool): Whether to address the command to another user. Defaults to False.
        """
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
        """
        Display the help menu by sending lines to the user.

        Args:
            c: IRC connection object.
            sender (str): The user requesting help.
        """
        with open("help.txt", "r") as f:
            help_text = f.readlines()
        for line in help_text:
            c.notice(sender, line.strip())
            time.sleep(1)

    def handle_message(self, c, e, sender, message):
        """
        Handle user and admin commands by executing the corresponding actions.

        Args:
            c: IRC connection object.
            e: IRC event object.
            sender (str): The user issuing the command.
            message (list): The command and its arguments.
        """
        user_commands = {
            ".ai": lambda: self.ai(c, e, sender, message),
            f"{self.nickname}:": lambda: self.ai(c, e, sender, message),
            ".x": lambda: self.ai(c, e, sender, message, x=True),
            ".persona": lambda: self.set_prompt(c, sender, persona=' '.join(message[1:])),
            ".custom": lambda: self.set_prompt(c, sender, custom=' '.join(message[1:])),
            ".reset": lambda: self.reset(c, sender),
            ".stock": lambda: self.reset(c, sender, stock=True),
            ".help": lambda: self.help_menu(c, sender)
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
        """
        Handles public messages sent in the channel.
        Parses the message to identify commands or content directed at the bot
        and delegates to the appropriate handler.

        Args:
            c: IRC connection object.
            e: IRC event object.
        """
        message = e.arguments[0].split(" ")
        sender = e.source.split("!")[0]

        if sender != self.nickname:
            self.handle_message(c, e, sender, message)

if __name__ == "__main__":
    infiniGPT = infiniGPT()
    infiniGPT.start()

