from __future__ import annotations

from typing import Awaitable, Callable


def make_join_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.join`` admin handler."""

    async def join_cmd(channel: str, sender: str, tokens: list) -> None:
        target = tokens[1] if len(tokens) > 1 else None
        if not target or not target.startswith("#"):
            return
        ctx.log.info("Joining channel %s at %s request", target, sender)
        ctx.irc.join_channel(target)
        if target not in ctx.cfg.irc.channels:
            ctx.cfg.irc.channels.append(target)
        await ctx._send_welcome(target)

    return join_cmd


def make_part_handler(ctx) -> Callable[[str, str, list], Awaitable[None]]:
    """Create the ``.part`` admin handler."""

    async def part_cmd(channel: str, sender: str, tokens: list) -> None:
        target = tokens[1] if len(tokens) > 1 else channel
        if not target or not target.startswith("#"):
            return
        ctx.log.info("Parting channel %s at %s request", target, sender)
        await ctx._send_goodbye(target)
        ctx.irc.part_channel(target, "https://github.com/h1ddenpr0cess20/infinigpt-irc")
        ctx.history.store.pop(target, None)
        if target in ctx.cfg.irc.channels:
            ctx.cfg.irc.channels.remove(target)

    return part_cmd
