# infinigpt-irc

InfiniGPT IRC is a modular IRC chatbot that talks to multiple OpenAI-compatible providers (OpenAI, xAI, Anthropic, Google, Mistral, LM Studio, Ollama) while tracking per-user histories and personas.

## Why InfiniGPT?

- Multi-provider routing with model lists per vendor and hot-swappable defaults.
- Per-user personalities, shared histories, and cross-user replies via `.x` and persona commands.
- Built-in and custom tools, including Model Context Protocol (MCP) servers for function calling.
- Admin/ops controls for model changes, resets, verbosity, and channel permissions from IRC.
- Ships as a Python package, Docker image, or bare script for flexible deployment.

## Quick Start

1. Clone the repo and create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `config.json` (or tailor it) with your IRC server, channels, and provider credentials.
3. Export API keys for the providers you plan to call (see `llm.api_keys` in the config schema).
4. Start the bot:
   ```bash
   python -m infinigpt_irc -c config.json
   # legacy entry point
   python infinigpt.py
   ```

## Documentation

Everything lives in `docs/`. Start with [`docs/index.md`](docs/index.md) and dive deeper:

- [`docs/getting-started.md`](docs/getting-started.md) for end-to-end setup
- [`docs/configuration.md`](docs/configuration.md) for every config option
- [`docs/commands.md`](docs/commands.md) for the IRC command surface
- [`docs/tools-and-mcp.md`](docs/tools-and-mcp.md) for tool and MCP wiring
- [`docs/ollama.md`](docs/ollama.md) + [`docs/docker.md`](docs/docker.md) for deployment extras
- [`docs/operations.md`](docs/operations.md) & [`docs/security.md`](docs/security.md) for running in production
- [`docs/architecture.md`](docs/architecture.md) & [`docs/development.md`](docs/development.md) for contributors

See `docs/not-a-companion.md` if you're deploying in shared or sensitive communities.

## License

GNU AGPL-3.0 — see [`LICENSE`](LICENSE).
