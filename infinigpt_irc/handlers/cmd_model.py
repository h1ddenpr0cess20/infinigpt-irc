from __future__ import annotations

from typing import Callable, Awaitable


def make_model_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.model`` admin handler.

    Without arguments it shows the current model and available keys.
    With an argument it sets the model to a known key or raw name.

    Args:
        ctx: Application context.

    Returns:
        An async handler with signature ``(channel, sender, tokens)``.
    """
    async def model_cmd(channel: str, sender: str, tokens: list) -> None:
        """Handle ``.model [reset|<name>]`` commands.

        Args:
            channel: IRC channel.
            sender: Nickname issuing the command.
            tokens: Tokenized input starting with ``.model``.
        """
        arg = tokens[1] if len(tokens) > 1 else None
        flattened: list[str] = []
        model_lookup = {}
        try:
            for provider, names in (ctx.models or {}).items():
                for name in names:
                    flattened.append(name)
                    model_lookup[name] = name
                    label = f"{provider}:{name}"
                    model_lookup[label] = name
        except Exception:
            pass
        if not arg:
            ctx.irc.send_message(channel, f"Current model: {ctx.model}")
            unique = sorted(dict.fromkeys(flattened))
            ctx.irc.send_message(channel, f"Available models: {', '.join(unique) if unique else 'none configured'}")
            return
        if arg == "reset":
            ctx.model = ctx.default_model
        else:
            target = model_lookup.get(arg)
            if not target and ":" in arg:
                _, value = arg.split(":", 1)
                target = model_lookup.get(value) or (value if value in flattened else None)
            if not target:
                ctx.irc.send_message(channel, f"Unknown model '{arg}'. Use .model to list available options.")
                return
            ctx.model = target
        ctx.log.info("Model set to %s", ctx.model)
        ctx.irc.send_message(channel, f"Model set to {ctx.model}")

    return model_cmd
