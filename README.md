# infinibot-irc
Infinibot is an OpenAI chatbot for IRC (Internet Relay Chat).  It has a great prompt which allows it to roleplay as almost anything you can think of.  You can set any default personality you would like.  It can be changed at any time, and each user has their own separate chat history with their chosen personality setting.  Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated.

Also available for the Matrix chat protocol at [infinibot-matrix](https://github.com/h1ddenpr0cess20/infinibot-matrix/)

## Setup

```
pip3 install openai irc
```
Get an [OpenAI API](https://platform.openai.com/signup) key 

Fill in the variables for channel, nickname, password and server in launcher.py.  
Password is optional, but registration is required for some channels.

## Use
```
python3 ircBotLauncher.py
```
**.ai _message_ or botname: _message_**
    Basic usage.
    Personality is preset by bot operator.
    
**.x _user message_**
    This allows you to talk to another user's chat history.
    _user_ is the display name of the user whose history you want to use
     
**.persona _personality_**
    Changes the personality.  It can be a character, personality type, object, idea.
    Don't use a custom prompt here.
    If you want to use a custom prompt, use .stock then use .ai _custom prompt_
        
**.reset**
    Reset to preset personality
    
**.stock**
    Remove personality and reset to standard GPT settings

**.help _botname_**
    Display the help menu
