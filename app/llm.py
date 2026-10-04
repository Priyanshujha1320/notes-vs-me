from __future__ import annotations
"""Model access — the only bridge between the app and any AI.

Two providers, one interface:

- ``ollama``  — everything runs on this machine. Open weights, offline, no keys.
- ``groq``    — fallback: an API key to a host serving *open-weight* models
                (Llama / Gemma), for laptops that can't run a model locally.

Selection: explicit via NVM_PROVIDER, else auto — Ollama if it answers,
hosted if a key is set. No closed models anywhere; when the app talks to a
host, it's still open weights, just borrowed compute.
"""
import json
import os
import re

import requests

OLLAMA_HOST = os.environ.get("NVM_OLLAMA_HOST", "http://localhost:11434")
# gemma3:1b is the safe default for 8GB laptops (~1GB resident); set
# NVM_CHAT_MODEL=gemma3:4b on machines with more headroom
CHAT_MODEL = os.environ.get("NVM_CHAT_MODEL", "gemma3:1b")
GROQ_BASE = "https://api.groq.com/openai/v1"
GROQ_CHAT_MODEL = os.environ.get("NVM_GROQ_MODEL", "llama-3.1-8b-instant")

TIMEOUT = 120


class ModelDown(Exception):
    pass


def _groq_key() -> str:
    return os.environ.get("NVM_GROQ_API_KEY", "")


def provider() -> str:
    """Which provider to use: 'ollama', 'groq', or 'none'."""
    explicit = os.environ.get("NVM_PROVIDER", "").strip().lower()
    if explicit in ("ollama", "groq"):
        return explicit
    try:
        requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2).raise_for_status()
        return "ollama"
    except requests.RequestException:
        return "groq" if _groq_key() else "none"


def chat(prompt: str, system: str = "", json_mode: bool = False) -> str:
    """One-shot completion, provider-agnostic. Returns the assistant text."""
    which = provider()
    if which == "ollama":
        return _chat_ollama(prompt, system, json_mode)
    if which == "groq":
        return _chat_groq(prompt, system, json_mode)
    raise ModelDown(
        "No model available: Ollama isn't running and no NVM_GROQ_API_KEY is set")


def _post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ModelDown(f"model request failed: {e}")
    return resp.json()


def _chat_ollama(prompt: str, system: str, json_mode: bool) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": prompt}]
    payload: dict = {"model": CHAT_MODEL, "messages": messages,
                     "stream": False,
                     # keep the KV cache small — this app targets 8GB laptops
                     "options": {"num_ctx": 2048}}
    if json_mode:
        payload["format"] = "json"
    return _post_json(f"{OLLAMA_HOST}/api/chat", payload)["message"]["content"]


def _chat_groq(prompt: str, system: str, json_mode: bool) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": prompt}]
    payload: dict = {"model": GROQ_CHAT_MODEL, "messages": messages,
                     "temperature": 0.7}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    data = _post_json(f"{GROQ_BASE}/chat/completions", payload,
                      headers={"Authorization": f"Bearer {_groq_key()}"})
    return data["choices"][0]["message"]["content"]


def extract_json(text: str) -> dict:
    """Pull a JSON object out of a model response, fences and all."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
    return json.loads(text)


def status() -> dict:
    """Health check for the frontend banner."""
    which = provider()
    if which == "none":
        return {"ok": False, "provider": "none",
                "reason": "No model: start Ollama, or set NVM_GROQ_API_KEY"}
    if which == "ollama":
        try:
            tags = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5).json()
        except requests.RequestException:
            return {"ok": False, "provider": "ollama",
                    "reason": "Ollama stopped responding"}
        names = [m["name"] for m in tags.get("models", [])]
        if not any(n.startswith(CHAT_MODEL) for n in names):
            return {"ok": False, "provider": "ollama",
                    "reason": f"Run: ollama pull {CHAT_MODEL}"}
        return {"ok": True, "provider": "ollama", "model": CHAT_MODEL}
    return {"ok": True, "provider": "groq", "model": GROQ_CHAT_MODEL}
