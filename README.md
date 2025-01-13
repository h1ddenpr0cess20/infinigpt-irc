# infinigpt-irc
InfiniGPT is an asynchronous, multi-channel AI chatbot for IRC, with a great prompt which allows it to roleplay as almost anything you can think of.  It supports OpenAI, xAI, Google and Ollama models. You can set any default personality you would like.  It can be changed at any time, and each user has their own separate chat history with their chosen personality setting.  Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated.  

Also available for the Matrix chat protocol at [infinigpt-matrix](https://github.com/h1ddenpr0cess20/infinigpt-matrix/)

## Setup

```
pip3 install irc 

```  
Get an [OpenAI API](https://platform.openai.com/signup) key, an [xAI API](https://accounts.x.ai/) key, and a [Google API](https://aistudio.google.com/apikey) key.  Add those to config.json.  

Add desired Ollama models to model dictionary if you want to use them.  

Fill in the irc credentials in config.json.  
Password is optional, but registration is required for some channels.


## Use
```
python3 infinigpt.py
```  
**.ai** _message_ or **botname:** _message_  
    Basic usage.  You can also privately message the bot without using these commands.
    
**.x** _user_ _message_  
    This allows you to talk to another user's chat history.  
    _user_ is the display name of the user whose history you want to use
     
**.persona** _personality_  
    Changes the personality.  It can be a character, personality type, object, idea.  
    Don't use a custom system prompt here.

**.custom** _prompt_  
    Set a custom system prompt
        
**.reset**  
    Reset to preset personality
    
**.stock**  
    Remove personality and reset to standard GPT settings

**.model**  
    List available large language models

**.model _modelname_**  
    Change model

**.help**  
    Display the help menu
