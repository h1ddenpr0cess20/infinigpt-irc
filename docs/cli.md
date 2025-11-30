## CLI

Preferred: `infinigpt-irc [options]`

Or run as a module: `python -m infinigpt_irc [options]`

### Options
- `-c, --config <path>`: Path to JSON config (default `./config.json`).
- `--ollama-url <url>`: Override the Ollama chat API URL.
- `--lmstudio-url <url>`: Override the LM Studio OpenAI-compatible URL.
- `--model <name|id>`: Override default model (key or id).
- `--verbose`: Start with verbose mode ON (omit brevity clause).
- `--server-models`: List models from configured local servers (Ollama / LM Studio) and exit.
- `--log-level <level>`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `--log-format <auto|rich|plain|json>`: Log formatting. `auto` selects Rich in TTY, plain otherwise.

### Environment Variables
- `INFINIGPT_OLLAMA_URL`
- `INFINIGPT_LMSTUDIO_URL`
- `INFINIGPT_MODEL`
- `INFINIGPT_IRC_SERVER`
- `INFINIGPT_LOG_FORMAT` (`auto|rich|plain|json`)
  - In containers or CI, set to `plain` for clean logs without ANSI codes.

### Examples
- Use a different config: `infinigpt-irc -c ./myconfig.json`
- Point to remote Ollama: `infinigpt-irc --ollama-url http://host:11434`
- Point to remote LM Studio: `infinigpt-irc --lmstudio-url http://host:1234`
- Start with a model: `infinigpt-irc --model qwen3`
- List server models: `infinigpt-irc --server-models`

### Exit Codes
- `0`: success
- `2`: invalid configuration or CLI arguments
