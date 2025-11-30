# infinigpt-irc

InfiniGPT IRC is an asynchronous, multi-provider AI chatbot for IRC.  
It keeps per-user histories, supports roleplay personas, can call tools via MCP servers, and speaks OpenAI-compatible APIs including OpenAI, xAI, Google Gemini (OpenAI compatibility layer), Mistral, LM Studio, and local Ollama.

## Features

- **Multiple providers** – use OpenAI, xAI, Anthropic (OpenAI-compatible endpoint), Google Gemini, Mistral, LM Studio, or Ollama by listing models per provider in `config.json`.
- **Personas & prompts** – each user has an independent personality and conversation history with `.persona`, `.custom`, `.reset`, `.stock`, `.gpersona`.
- **Collaborative chats** – `.x user message` talks to another user's history while replying back to the sender.
- **Tool calling** – built-in tools plus `fastmcp` support for Model Context Protocol servers; custom tools come from `tools.py` + `schema.json`.
- **Admin controls** – change models, clear history, toggle verbosity, and manage channels from IRC.
- **Modular package** – run via `python -m infinigpt_irc` or installable package ready for Docker/packaging workflows.

## Setup

1. **Clone / download** this repository.
2. **Create a virtual environment** and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Edit `config.json`** with your IRC credentials and model providers.
4. **Add API keys** for the providers you plan to use (`llm.api_keys`).
5. **(Optional) Install Ollama and/or LM Studio** if you want to run local models. Make sure you can `ollama pull llama3` or start an LM Studio local server (`lmstudio --server`) before using their models.  
6. **(Optional) Configure MCP servers** under `llm.mcp_servers` or add more builtin tools via `tools.py` and `schema.json`.

## Usage

Start the bot with either command:

```bash
python -m infinigpt_irc -c config.json
# or legacy entry point
python infinigpt.py
```

