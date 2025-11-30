## Commands

All commands work in channels, private messages, or via `BotNick: <message>` mention routing. Admin-only commands require your nickname in `irc.admins`.

### User Commands
- `.ai <message>`: Send a prompt to the current model. Also triggered by `BotNick: <message>` and by typing directly in a DM.
  - Example: `.ai summarize the last 20 lines`
- `.x <target> <message>`: Ask on behalf of another nick in the same channel. The target must have an existing history.
  - Example: `.x alice what did you ask earlier?`
- `.persona <text>`: Set a persona for your conversation and introduce the bot to the channel (or DM).
  - Example: `.persona You are a concise systems engineer.`
- `.custom <system prompt>`: Replace the system prompt entirely for your conversation and introduce the bot.
  - Example: `.custom You only answer with JSON objects.`
- `.reset`: Reset your history (keep the default persona/prompt).
- `.stock`: Reset to a “stock” history without a system prompt.
- `.help [botnick]`: DM or mention the bot to get the help text via NOTICE (fallback to inline if necessary).

### Admin Commands
- `.model [name|reset]`: Show or set the active model for the channel context.
  - Examples: `.model`, `.model gpt-4o-mini`, `.model reset`
- `.clear`: Clear all histories (channel + DM) and reset defaults.
- `.verbose [on|off|toggle]`: Control whether the optional brevity clause is applied to prompts.
  - Example: `.verbose on` for long-form answers; `.verbose off` for concise.
- `.gpersona <text>`: Set the global default personality.
- `.join #channel`: Ask the bot to join a channel.
- `.part [#channel]`: Ask the bot to leave a channel (defaults to current).

### Notes & Tips
- Direct messages behave like `.ai` commands; no prefix is required.
- Rate limits: servers may throttle bursts. Replies are chunked with short pauses.
- Tools/MCP: when enabled, the model may call tools before responding. Tool calls and results are logged.
- Privacy: histories are kept per user per channel or DM; use `.stock` for minimal context.
