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

### Configuration Overview

`config.json` has two sections:

- `irc`: `server`, `port`, `nickname`, optional `password`, list of `channels`, and admin nicknames.
- `llm`:
  - `models`: mapping of provider → list of model IDs (`"openai": ["gpt-4o-mini"]`, `"anthropic": ["claude-3-5-sonnet-20240620"]`, `"ollama": ["llama3.2"]`, etc.)
  - `api_keys`: provider → API key (OpenAI/xAI/Anthropic/Google/Mistral). Providers without keys are skipped.
  - `default_model`: the model name to start with (must exist in `models`).
  - `personality` & `prompt`: default persona template array `[prefix, suffix, optional_extra]`.
  - `options`: OpenAI-style generation parameters (temperature, top_p, frequency_penalty, etc.) applied to all non-Google providers.
  - `history_size`: number of messages to keep per user/channel.
  - `ollama_url`: base URL or host:port for local Ollama (`localhost:11434` works).
  - `lmstudio_url`: OpenAI-compatible base URL (host:port) for LM Studio's local server (`localhost:1234` by default).
  - `timeout`: request timeout seconds (optional, defaults to 120).
  - `mcp_servers`: optional mapping of MCP server names to commands/URLs for tool discovery.
  - `verbose`: when true, disables the short prompt suffix for extra detail.

Environment overrides:

- `INFINIGPT_MODEL`: override `llm.default_model`.
- `INFINIGPT_IRC_SERVER`: override `irc.server`.
- `INFINIGPT_OLLAMA_URL`: override `llm.ollama_url`.
- `INFINIGPT_LMSTUDIO_URL`: override `llm.lmstudio_url`.
- `INFINIGPT_LOG_FORMAT`: choose `auto|rich|plain|json`.

## Usage

Start the bot with either command:

```bash
python -m infinigpt_irc -c config.json
# or legacy entry point
python infinigpt.py
```

Helpful CLI flags:

- `--ollama-url http://host:11434` – override Ollama endpoint for this run.
- `--lmstudio-url http://host:1234` – override the LM Studio OpenAI-compatible endpoint.
- `--model <name>` – set the default model (use `.model` later to switch).
- `--verbose` – start with verbose prompts (extra suffix disabled).
- `--server-models` – list models reported by the configured local servers (Ollama and/or LM Studio) and exit.
- `--log-format rich|plain|json` – control log output (defaults to smart auto-detection).

If installed as a package (`pip install .`), the entry command is `infinigpt-irc`.

## Commands

| Command | Description |
|---------|-------------|
| `.ai message` or `botname: message` | Talk to the bot in the channel. |
| `.x user message` | Borrow another user's conversation while replying to you. |
| `.persona personality` | Change your persona (characters, ideas, anything). |
| `.custom prompt` | Set a custom system message instead of persona template. |
| `.reset` | Reset to the default persona. |
| `.stock` | Remove persona and use provider stock instructions. |
| `.help <bot>` | Receive the help text via NOTICE (admins also get admin commands). |
| `.model` | Show the current model and available provider:model entries. *(admin)* |
| `.model <name>` | Switch to a model (supports `provider:model`). *(admin)* |
| `.clear` | Wipe all histories and reset defaults. *(admin)* |
| `.verbose [on|off|toggle]` | Control whether the optional suffix is used. *(admin)* |
| `.gpersona personality` | Set a new global default persona. *(admin)* |
| `.join #chan` / `.part #chan` | Join or leave IRC channels. *(admin)* |

Private messages support the same persona commands and simple chatting, mirroring the `.ai` behavior.

## Tools & MCP

- Builtin tools live in `infinigpt_irc/tools/` with a default `schema.json`.
- Custom tools can be added by editing the top-level `tools.py` and `schema.json`. The package automatically merges your schema and imports your functions.
- Model Context Protocol servers can be defined under `llm.mcp_servers`. The bot will load tools once at startup via [`fastmcp`](https://github.com/modelcontextprotocol/fastmcp) and expose them to tool-capable models.
