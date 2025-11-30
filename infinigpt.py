"""Backward compatible launcher for the InfiniGPT IRC bot."""

from infinigpt_irc.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
