## Getting Started (IRC)

Follow these steps to run the bot locally against OpenAI-compatible APIs and optional local servers (Ollama, LM Studio).

### 1) Prerequisites
- Python 3.10+
- Provider APIs (OpenAI/xAI/Google/Mistral) with valid API keys
- Optional local servers:
  - Ollama installed and serving (see [ollama.md](./ollama.md))
  - LM Studio running with its OpenAI-compatible server enabled

Install Ollama and pull at least one model (example):

```
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```
Start LM Studio’s local server (`lmstudio --server`) and note the host/port.

### 2) Install
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure
Create or edit `config.json` and set the basics:
- `irc.server`: e.g., `irc.libera.chat`
- `irc.nickname`: your bot nickname
- `irc.password`: optional NickServ password
- `irc.channels`: list of channels like `["#yourchannel"]`
- `irc.admins`: list of nicknames allowed to use admin commands
- `llm.models`: provider → list of model IDs (`openai`, `xai`, `anthropic`, `google`, `mistral`, `lmstudio`, `ollama`)
- `llm.default_model`: starting model (must exist in the lists above)
- `llm.api_keys`: keys for OpenAI/xAI/Anthropic/Google/Mistral (if you plan to use them)
- `llm.ollama_url`: e.g., `http://localhost:11434`
- `llm.lmstudio_url`: e.g., `http://localhost:1234`
- `llm.mcp_servers`: optional mapping of MCP server names to commands/URLs

See [Configuration](configuration.md) for full schema and validation rules.

### 4) Run
```
python -m infinigpt_irc -c config.json
```

If installed as a package:
```
infinigpt-irc -c config.json
```

Join the same channel(s) and try:
- `.ai hello there`
- `.model` to list available models, or `.model reset` to revert
- `.help <botnick>` in a channel or DM to get the help text

Private messages work out of the box. DM the bot directly and say “hello” (no prefix needed) to start a private conversation.

### Next Steps
- Learn commands: [commands.md](./commands.md)
- Tune configuration: [configuration.md](./configuration.md)
- Enable tools/MCP: [tools-and-mcp.md](./tools-and-mcp.md)
