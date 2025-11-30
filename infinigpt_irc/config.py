from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os
import logging


log = logging.getLogger("infinigpt_irc")


@dataclass
class IrcConfig:
    server: str
    nickname: str
    password: Optional[str] = None
    channels: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)


@dataclass
class LLMConfig:
    models: Dict[str, List[str]] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    personality: str = "a helpful assistant"
    prompt: List[str] = field(default_factory=lambda: ["You are ", "."])
    options: Dict[str, Any] = field(default_factory=dict)
    history_size: int = 24
    timeout: int = 120
    ollama_url: str = "http://localhost:11434"
    lmstudio_url: str = "http://localhost:1234"
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False


@dataclass
class AppConfig:
    irc: IrcConfig
    llm: LLMConfig


def _normalize_channels(raw: Dict[str, Any]) -> List[str]:
    """Normalize channel configuration to a list of names.

    Accepts legacy ``irc.channel`` (single string) or modern ``irc.channels``
    (list of strings) and returns a clean list.

    Args:
        raw: Raw ``irc`` section mapping from the config.

    Returns:
        A list of channel names to join.
    """
    # Back-compat: support legacy single "channel" string
    channels = []
    if "channels" in raw and isinstance(raw["channels"], list):
        channels = [c for c in raw["channels"] if c]
    elif "channel" in raw and isinstance(raw["channel"], str):
        if raw["channel"]:
            channels = [raw["channel"]]
    return channels


def _deep_update(base: dict, updates: dict) -> dict:
    """Recursively update mapping ``base`` with values from ``updates``.

    Args:
        base: Destination mapping to update in place.
        updates: Mapping of changes to apply; nested dicts are merged.

    Returns:
        The updated ``base`` mapping.
    """
    for k, v in (updates or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _deep_update(dict(base[k]), v)
        else:
            base[k] = v
    return base


def load_config(path: Path | str, *, env: Optional[Dict[str, str]] = None, overrides: Optional[Dict[str, Any]] = None) -> AppConfig:
    """Load and normalize configuration from a JSON file.

    Applies selected environment variable overrides and optional caller
    overrides for convenience.

    Args:
        path: Path to the ``config.json`` file.
        env: Optional environment mapping to read overrides from.
        overrides: Optional mapping to deep-merge onto the config.

    Returns:
        A validated ``AppConfig`` object.

    Raises:
        ValueError: If required sections are missing or essential fields empty.
    """
    p = Path(path)
    data = json.loads(p.read_text())

    # Validate sections exist
    if "irc" not in data or ("llm" not in data and "ollama" not in data):
        raise ValueError("Config must contain 'irc' and 'llm' sections")
    if "llm" not in data and "ollama" in data:
        log.warning("Config key 'ollama' is deprecated; rename to 'llm'")
        data["llm"] = data["ollama"]

    env = env or os.environ
    # Apply selected ENV overrides
    env_over: Dict[str, Any] = {}
    if env.get("INFINIGPT_MODEL"):
        env_over.setdefault("llm", {})["default_model"] = env["INFINIGPT_MODEL"]
    if env.get("INFINIGPT_IRC_SERVER"):
        env_over.setdefault("irc", {})["server"] = env["INFINIGPT_IRC_SERVER"]
    if env.get("INFINIGPT_OLLAMA_URL"):
        env_over.setdefault("llm", {})["ollama_url"] = env["INFINIGPT_OLLAMA_URL"]
    if env.get("INFINIGPT_LMSTUDIO_URL"):
        env_over.setdefault("llm", {})["lmstudio_url"] = env["INFINIGPT_LMSTUDIO_URL"]
    if env_over:
        data = _deep_update(data, env_over)
    if overrides:
        data = _deep_update(data, overrides)

    irc_raw = data["irc"]
    llm_raw = data["llm"]
    # Back-compat: allow top-level mcp_servers to merge into llm section
    try:
        top_mcp = data.get("mcp_servers")
        if isinstance(top_mcp, dict):
            existing = llm_raw.get("mcp_servers")
            if not isinstance(existing, dict):
                llm_raw["mcp_servers"] = dict(top_mcp)
            else:
                merged = dict(existing)
                merged.update(top_mcp)
                llm_raw["mcp_servers"] = merged
    except Exception:
        pass

    # Deprecation warning for legacy key
    try:
        if isinstance(data.get("irc"), dict) and "channel" in data["irc"] and "channels" not in data["irc"]:
            log.warning("Config key 'irc.channel' is deprecated; use 'irc.channels' instead (will be normalized).")
    except Exception:
        pass

    irc_cfg = IrcConfig(
        server=str(irc_raw.get("server", "")),
        nickname=str(irc_raw.get("nickname", "InfiniGPT")),
        password=irc_raw.get("password"),
        channels=_normalize_channels(irc_raw),
        admins=list(irc_raw.get("admins", [])),
    )

    if not irc_cfg.server:
        raise ValueError("IRC server is required in config.irc.server")
    if not irc_cfg.channels:
        raise ValueError("At least one IRC channel is required (irc.channels or legacy irc.channel)")

    prompt_list = list(llm_raw.get("prompt", ["You are ", "."]))
    if not (2 <= len(prompt_list) <= 3):
        prompt_list = ["You are ", "."]

    llm_cfg = LLMConfig(
        models={k: list(v) for k, v in dict(llm_raw.get("models", {})).items()},
        api_keys=dict(llm_raw.get("api_keys", {})),
        default_model=str(llm_raw.get("default_model", "")),
        personality=str(llm_raw.get("personality", "a helpful assistant")),
        prompt=prompt_list[:3],
        options=dict(llm_raw.get("options", {})),
        history_size=int(llm_raw.get("history_size", 24)),
        timeout=int(llm_raw.get("timeout", 120)),
        ollama_url=str(llm_raw.get("ollama_url", "http://localhost:11434")),
        lmstudio_url=str(llm_raw.get("lmstudio_url", "http://localhost:1234")),
        mcp_servers=dict(llm_raw.get("mcp_servers", {})),
        verbose=bool(llm_raw.get("verbose", False)),
    )

    if not llm_cfg.default_model:
        flattened = [m for group in llm_cfg.models.values() for m in group]
        if flattened:
            llm_cfg.default_model = flattened[0]

    return AppConfig(irc=irc_cfg, llm=llm_cfg)


def validate_config(cfg: AppConfig) -> Tuple[bool, List[str]]:
    """Validate an ``AppConfig`` instance and collect errors.

    Args:
        cfg: The configuration to validate.

    Returns:
        Tuple of ``(ok, errors)`` where ``ok`` is ``True`` when validation
        passes, otherwise ``False`` with human-readable error messages.
    """
    errors: List[str] = []
    # IRC validation
    if not isinstance(cfg.irc.server, str) or not cfg.irc.server.strip():
        errors.append("irc.server must be a non-empty string (hostname or address)")
    if not isinstance(cfg.irc.nickname, str) or not cfg.irc.nickname.strip():
        errors.append("irc.nickname must be a non-empty string")
    if not isinstance(cfg.irc.channels, list) or not cfg.irc.channels:
        errors.append("irc.channels must be a non-empty list (or provide legacy irc.channel)")
    else:
        bad = [c for c in cfg.irc.channels if not isinstance(c, str) or not c.startswith("#")]
        if bad:
            errors.append(f"irc.channels entries must start with '#': {bad}")
    if not isinstance(cfg.irc.admins, list):
        errors.append("irc.admins must be a list of nicknames")

    # LLM validation
    if not isinstance(cfg.llm.models, dict):
        errors.append("llm.models must be a mapping of provider→[models]")
    if not isinstance(cfg.llm.default_model, str) or not cfg.llm.default_model:
        errors.append("llm.default_model must be a non-empty string")
    else:
        flat = {m for models in (cfg.llm.models or {}).values() for m in models}
        if flat and cfg.llm.default_model not in flat:
            errors.append("llm.default_model must be present in llm.models")
    if not isinstance(cfg.llm.api_keys, dict):
        errors.append("llm.api_keys must be a mapping of provider→key")
    if not isinstance(cfg.llm.prompt, list) or len(cfg.llm.prompt) not in (2, 3) or not all(isinstance(p, str) for p in cfg.llm.prompt):
        errors.append("llm.prompt must be a list of 2 or 3 strings [prefix, suffix, (optional clause)]")
    if not isinstance(cfg.llm.personality, str) or not cfg.llm.personality:
        errors.append("llm.personality must be a non-empty string")
    if not (1 <= int(cfg.llm.history_size) <= 1000):
        errors.append("llm.history_size must be between 1 and 1000")
    if not isinstance(cfg.llm.mcp_servers, dict):
        errors.append("llm.mcp_servers must be a mapping if provided")
    if not isinstance(cfg.llm.ollama_url, str) or not cfg.llm.ollama_url:
        errors.append("llm.ollama_url must be a non-empty string (http URL or host:port)")
    if not isinstance(cfg.llm.lmstudio_url, str) or not cfg.llm.lmstudio_url:
        errors.append("llm.lmstudio_url must be a non-empty string (http URL or host:port)")
    # Options ranges
    opts = cfg.llm.options or {}
    temp = opts.get("temperature")
    if temp is not None:
        try:
            if not (0 <= float(temp) <= 2):
                errors.append("llm.options.temperature must be between 0 and 2")
        except Exception:
            errors.append("llm.options.temperature must be numeric")
    top_p = opts.get("top_p")
    if top_p is not None:
        try:
            if not (0 < float(top_p) <= 1):
                errors.append("llm.options.top_p must be >0 and ≤1")
        except Exception:
            errors.append("llm.options.top_p must be numeric")
    freq = opts.get("frequency_penalty")
    if freq is not None:
        try:
            float(freq)
        except Exception:
            errors.append("llm.options.frequency_penalty must be numeric")

    return (len(errors) == 0, errors)
