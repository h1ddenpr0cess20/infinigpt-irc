from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

import importlib
import json
import pkgutil
from pathlib import Path
import logging


_TOOL_REGISTRY: Dict[str, Callable[..., str]] | None = None
logger = logging.getLogger(__name__)


def _schema_path() -> Path:
    """Return the filesystem path of the builtin ``schema.json`` file."""
    return Path(__file__).resolve().parent / "schema.json"


def _load_schema_file(path: Path) -> List[Dict[str, Any]]:
    logger.debug("Loading tools schema from %s", path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array of tool definitions")
    return data


def load_schema(path: str | None = None) -> List[Dict[str, Any]]:
    """Load the builtin tool schema definitions.

    Args:
        path: Optional path to a schema file. When omitted, the package's
            default ``schema.json`` is used.

    Returns:
        A list of tool definition dictionaries.

    Raises:
        ValueError: If the schema file does not contain a JSON array.
    """
    # Aggregate builtins with optional user schema
    entries: List[Dict[str, Any]] = []
    if path:
        entries.extend(_load_schema_file(Path(path)))
        return entries
    builtin_path = _schema_path()
    try:
        entries.extend(_load_schema_file(builtin_path))
    except Exception:
        logger.exception("Failed to load builtin tools schema")
    user_path = Path("schema.json")
    if user_path.exists():
        try:
            user_entries = _load_schema_file(user_path)
            # Merge by function name to avoid duplicates
            existing = {(tool.get("function") or {}).get("name") for tool in entries}
            for tool in user_entries:
                fn = (tool.get("function") or {}).get("name")
                if fn and fn in existing:
                    # Replace existing entry
                    entries = [t for t in entries if (t.get("function") or {}).get("name") != fn]
                entries.append(tool)
        except Exception:
            logger.exception("Failed to load user schema.json")
    logger.debug("Loaded %d tool definition(s)", len(entries))
    return entries


def _discover_functions(names: Iterable[str]) -> Dict[str, Callable[..., str]]:
    """Import tool modules and resolve named functions.

    Args:
        names: Iterable of function names to locate across the tools package.

    Returns:
        Mapping of function name to callable implementing that tool.
    """
    names = list(dict.fromkeys(names))
    remaining = set(names)
    found: Dict[str, Callable[..., str]] = {}

    pkg_path = Path(__file__).resolve().parent
    package_name = __name__

    modules = []
    for modinfo in pkgutil.iter_modules([str(pkg_path)]):
        mod_name = modinfo.name
        if mod_name.startswith("_") or mod_name == "__init__":
            continue
        modules.append(importlib.import_module(f"{package_name}.{mod_name}"))
    try:
        user_module = importlib.import_module("tools")
        modules.append(user_module)
    except Exception:
        pass

    for module in modules:
        for fname in list(remaining):
            func = getattr(module, fname, None)
            if callable(func):
                found[fname] = func  # type: ignore[assignment]
                remaining.discard(fname)
        if not remaining:
            break

    return found


def _build_registry_from_schema(schema: List[Dict[str, Any]]) -> Dict[str, Callable[..., str]]:
    """Construct a function registry from a schema list.

    Args:
        schema: Tool schema entries as loaded from JSON.

    Returns:
        Mapping of tool name to the corresponding callable.
    """
    names: List[str] = []
    for tool in schema:
        fn = (tool.get("function") or {}).get("name")
        if isinstance(fn, str) and fn:
            names.append(fn)
    return _discover_functions(names)


def _get_registry() -> Dict[str, Callable[..., str]]:
    """Get or build the cached builtin tools registry."""
    global _TOOL_REGISTRY
    if _TOOL_REGISTRY is None:
        schema = load_schema()
        _TOOL_REGISTRY = _build_registry_from_schema(schema)
    return _TOOL_REGISTRY


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Execute a builtin tool by name and return a JSON string.

    Args:
        name: Tool function name to execute.
        arguments: Keyword arguments to pass to the function.

    Returns:
        A JSON string representing the function's result, or an error object
        if the tool is unknown or raises.
    """
    registry = _get_registry()
    func = registry.get(name)
    if func is None:
        logger.warning("Unknown builtin tool '%s'", name)
        return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
    try:
        try:
            _args_str = json.dumps(arguments or {}, ensure_ascii=False, default=str)
        except Exception:
            _args_str = str(arguments)
        if len(_args_str) > 800:
            _args_str = _args_str[:800] + "…"
        # AppContext logs tool calls centrally; keep this at DEBUG to avoid duplicates
        logger.debug("Tool (builtin): %s args=%s", name, _args_str)
        result = func(**(arguments or {}))
        if isinstance(result, (dict, list, int, float, bool)) or result is None:
            return json.dumps(result, ensure_ascii=False)
        if isinstance(result, str):
            try:
                json.loads(result)
                return result
            except Exception:
                return json.dumps({"result": result}, ensure_ascii=False)
        return json.dumps({"result": str(result)}, ensure_ascii=False)
    except TypeError as e:
        logger.exception("Invalid arguments for builtin tool '%s'", name)
        return json.dumps({"error": f"Invalid arguments for {name}: {e}"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("Tool execution error for builtin tool '%s'", name)
        return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)


__all__ = ["execute_tool", "load_schema"]
