from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .config import LLMConfig
from .exceptions import NetworkError, RuntimeFailure


class LLMClient:
    """Unified OpenAI-format client for multiple providers and Ollama."""

    def __init__(self, cfg: LLMConfig, *, session: Optional[httpx.Client] = None) -> None:
        self.cfg = cfg
        self.timeout = int(cfg.timeout or 120)
        self._session = session or httpx.Client(timeout=self.timeout)
        self._model_to_provider: Dict[str, str] = {}
        for provider, names in (cfg.models or {}).items():
            for name in names:
                self._model_to_provider[name] = provider
        self.available_models: List[str] = sorted(self._model_to_provider)
        self._ollama_openai_base, self._ollama_rest_base = self._normalize_ollama_url(cfg.ollama_url)
        self._lmstudio_openai_base = self._normalize_openai_url(cfg.lmstudio_url, default="http://localhost:1234")

    def _normalize_ollama_url(self, raw: str) -> tuple[str, str]:
        base = (raw or "").strip() or "http://localhost:11434"
        if not base.startswith("http"):
            base = f"http://{base}"
        base = base.rstrip("/")
        # Remove trailing /api or /v1 to get root
        if base.endswith("/api") or base.endswith("/v1"):
            root = base.rsplit("/", 1)[0]
        else:
            root = base
        return (f"{root}/v1", f"{root}/api")

    def _normalize_openai_url(self, raw: str, *, default: str) -> str:
        base = (raw or "").strip() or default
        if not base.startswith("http"):
            base = f"http://{base}"
        base = base.rstrip("/")
        if base.endswith("/v1"):
            return base
        return f"{base}/v1"

    def _provider_for_model(self, model: str) -> str:
        provider = self._model_to_provider.get(model)
        if not provider:
            raise RuntimeFailure(f"Unknown model '{model}'. Update llm.models to include it.")
        return provider

    def _headers_for_provider(self, provider: str) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if provider == "ollama":
            headers["Authorization"] = "Bearer hello_friend"
            return headers
        if provider == "lmstudio":
            return headers
        if provider == "anthropic":
            token = (self.cfg.api_keys or {}).get(provider)
            if not token:
                raise RuntimeFailure("Missing API key for provider 'anthropic'")
            headers["Authorization"] = f"Bearer {token}"
            headers["x-api-key"] = token
            headers["anthropic-version"] = "2023-06-01"
            return headers
        token = (self.cfg.api_keys or {}).get(provider)
        if not token:
            raise RuntimeFailure(f"Missing API key for provider '{provider}'")
        headers["Authorization"] = f"Bearer {token}"
        return headers

    def _base_for_provider(self, provider: str) -> str:
        if provider == "openai":
            return "https://api.openai.com/v1"
        if provider == "xai":
            return "https://api.x.ai/v1"
        if provider == "google":
            return "https://generativelanguage.googleapis.com/v1beta/openai"
        if provider == "mistral":
            return "https://api.mistral.ai/v1"
        if provider == "ollama":
            return self._ollama_openai_base
        if provider == "lmstudio":
            return self._lmstudio_openai_base
        if provider == "anthropic":
            return "https://api.anthropic.com/v1"
        return "https://api.openai.com/v1"

    def _prepare_payload(
        self,
        *,
        provider: str,
        model: str,
        messages: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._normalize_messages(model, messages),
        }
        if tools:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if provider != "google":
            payload.update(self._filtered_options(model, options or {}))
        return payload

    def _normalize_messages(self, model: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Adjust messages for provider quirks (e.g., GPT-5 uses 'developer')."""
        needs_developer = model.lower().startswith("gpt-5")
        if not needs_developer:
            return messages
        normalized: List[Dict[str, Any]] = []
        for msg in messages:
            entry = dict(msg)
            if entry.get("role") == "system":
                entry["role"] = "developer"
            normalized.append(entry)
        return normalized

    def _filtered_options(self, model: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Drop unsupported parameters for specific model families."""
        if not options:
            return {}
        if model.lower().startswith("gpt-5"):
            return {}
        return dict(options)

    def _post(self, url: str, payload: Dict[str, Any], timeout: Optional[int] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            resp = self._session.post(url, json=payload, timeout=timeout or self.timeout, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = e.response.text.strip()
            except Exception:
                detail = ""
            message = f"{e} :: {detail}" if detail else str(e)
            raise NetworkError(message)
        except httpx.HTTPError as e:
            raise NetworkError(str(e))
        try:
            return resp.json()
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from provider: {e}")

    def _convert_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if "message" in data and isinstance(data["message"], dict):
            message = data["message"]
        else:
            choices = data.get("choices")
            if not isinstance(choices, list) or not choices:
                raise RuntimeFailure("Provider response missing choices")
            message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            # OpenAI responses can include structured parts
            parts: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                elif isinstance(part, str):
                    parts.append(part)
            message["content"] = "".join(parts)
        elif content is None:
            message["content"] = ""
        return {"message": message}

    def chat(self, *, model: str, messages: List[Dict[str, Any]], options: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        provider = self._provider_for_model(model)
        headers = self._headers_for_provider(provider)
        base = self._base_for_provider(provider)
        payload = self._prepare_payload(provider=provider, model=model, messages=messages, options=options)
        result = self._post(f"{base}/chat/completions", payload, timeout=timeout, headers=headers)
        return self._convert_response(result)

    def chat_with_tools(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: str,
        options: Optional[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Optional[str] = "auto",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        provider = self._provider_for_model(model)
        headers = self._headers_for_provider(provider)
        base = self._base_for_provider(provider)
        payload = self._prepare_payload(
            provider=provider,
            model=model,
            messages=messages,
            options=options or {},
            tools=tools,
            tool_choice=tool_choice,
        )
        result = self._post(f"{base}/chat/completions", payload, timeout=timeout, headers=headers)
        return self._convert_response(result)

    def list_ollama_models(self) -> List[str]:
        url = f"{self._ollama_rest_base}/tags"
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(str(e))
        try:
            data = resp.json() or {}
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from Ollama: {e}")
        models = data.get("models")
        names: List[str] = []
        if isinstance(models, list):
            for item in models:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("model")
                    if isinstance(name, str):
                        names.append(name)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("model")
                    if isinstance(name, str):
                        names.append(name)
        return names

    def ollama_health(self) -> bool:
        try:
            self.list_ollama_models()
            return True
        except Exception:
            return False

    def list_lmstudio_models(self) -> List[str]:
        url = f"{self._lmstudio_openai_base}/models"
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise NetworkError(str(e))
        try:
            data = resp.json() or {}
        except ValueError as e:
            raise RuntimeFailure(f"Invalid JSON from LM Studio: {e}")
        entries = data.get("data")
        names: List[str] = []
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict):
                    ident = item.get("id") or item.get("name")
                    if isinstance(ident, str):
                        names.append(ident)
        return names

    def lmstudio_health(self) -> bool:
        try:
            self.list_lmstudio_models()
            return True
        except Exception:
            return False
