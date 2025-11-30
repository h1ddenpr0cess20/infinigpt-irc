## Configuration

The bot reads a JSON configuration file (default `./config.json`). You can override with `--config` or environment variables. CLI flags and selected environment variables are merged on top of the file.

### Schema

- irc:
  - server (hostname or address)
  - nickname
  - password (optional NickServ password)
  - channels: list of channel names (e.g., `"#room"`)
  - admins: list of nicknames with admin privileges
- llm:
  - models: mapping of provider → list of model IDs (e.g., `"openai": ["gpt-4o-mini"]`, `"anthropic": ["claude-3-5-sonnet-20240620"]`, `"ollama": ["llama3.2"]`)
  - default_model: selected model (must match an entry from `models`)
  - api_keys: mapping of provider → API key (`openai`, `xai`, `anthropic`, `google`, `mistral`)
  - prompt: two strings `[prefix, suffix]` with optional third brevity clause `[prefix, suffix, brevity]`
  - personality: non‑empty default personality text
  - history_size: 1–1000 messages retained per user per channel
  - options: advanced generation options (e.g., `temperature`, `top_p`, `frequency_penalty`)
  - timeout: request timeout in seconds (default: 120)
  - ollama_url: base URL or host:port for an Ollama server
  - lmstudio_url: base URL or host:port for an LM Studio OpenAI-compatible server
  - mcp_servers: mapping of names to MCP server specs (optional)
    - Supports: URL string, shell string, argv list, or dict forms
    - Top‑level `mcp_servers` is also accepted and merged for backward compatibility

### Overrides

- CLI flags: `--ollama-url`, `--lmstudio-url`, `--model`, `--log-level`
- Environment variables:
  - `INFINIGPT_OLLAMA_URL`
  - `INFINIGPT_LMSTUDIO_URL`
  - `INFINIGPT_MODEL`
  - `INFINIGPT_IRC_SERVER`

### Validation

The app validates configuration on startup; on errors it prints messages and exits with code `2`.

Checks include:

- `irc.server`, `irc.nickname` non‑empty; `irc.channels` non‑empty list of `#channel`
- `llm.default_model` set and present by key or id
- `llm.prompt` is a list of 2 or 3 strings
- Bounds on `options` (temperature 0–2, top_p 0–1, repeat_penalty 0.5–2)
- `llm.mcp_servers` must be a mapping if provided

### Backwards Compatibility

- `irc.channel` (string) is accepted and normalized into `irc.channels`.
- Top‑level `mcp_servers` is merged into `llm.mcp_servers`.
