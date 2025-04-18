# infinigpt-irc
InfiniGPT is an asynchronous, multi-channel AI chatbot for IRC, with a great prompt which allows it to roleplay as almost anything you can think of.  It supports OpenAI, xAI, Google and Ollama models. You can set any default personality you would like.  It can be changed at any time, and each user has their own separate chat history with their chosen personality setting.  Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated.  

Also available for the Matrix chat protocol at [infinigpt-matrix](https://github.com/h1ddenpr0cess20/infinigpt-matrix/)

## Setup

```
pip install -r requirements.txt 
```  
Get an [OpenAI API](https://platform.openai.com/signup) key, an [xAI API](https://accounts.x.ai/) key, a [Google API](https://aistudio.google.com/apikey) key, and a [Mistral API](https://mistral.ai/) key, if you would like to use those services.  Add those to config.json.  Add/remove the models you would like to be available from the model lists.  

Familiarize yourself with [Ollama](http://ollama.com/), make sure you can run local LLMs.  Install the models you want to use and replace the example Ollama models in config.json.  If you would like to use with Ollama only, you can leave the lists of models for the other services empty.  

Fill in the irc credentials in config.json.  
Password is optional, but it is recommended because registration is required for some channels, and some users may not be able to privately message the bot unless it has identified to the server.

You can add your own tools to the tools.py file and add them to the schema.json file.  I have included a crypto price tool as an example.

## Use
```
python infinigpt.py
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

**.model** _modelname_  
    Change model

**.join** _channel_   
    Join a channel

**.part** _channel_   
    Leave a channel.  You can omit channel to part channel command was issued in.

**.gpersona** _personality_  
    Set a new default personality.

**.help** _botname_  
    Display the help menu
