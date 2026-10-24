"""Eén deur naar de modelhuizen.

DeepSeek, Gemini, Mistral, Qwen en Grok. De sleutel blijft in de omgeving.
Elke tekst wordt gemaskeerd voordat zij het huis bereikt, en lokaal hersteld
in het antwoord.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

try:
    from .pii_mask import mask, restore
except ImportError:
    from pii_mask import mask, restore

_HOUSES = {
    "deepseek": {
        "env": "DEEPSEEK_API_KEY",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
        "style": "openai",
    },
    "mistral": {
        "env": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-large-latest",
        "style": "openai",
    },
    "qwen": {
        "env": "GROQ_API_KEY",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "qwen/qwen3.8-27b",
        "style": "openai",
    },
    "grok": {
        "env": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "x-ai/grok-4.5",
        "style": "openai",
    },
    "gemini": {
        "env": "GOOGLE_API_KEY",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "model": "gemini-pro-latest",
        "style": "gemini",
    },
}


def _load_env():
    # Zoekt naar .env in huidige map, bovenliggende map, of workspace
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(os.environ.get("CIVIC_WORKSPACE", "")) / ".env" if os.environ.get("CIVIC_WORKSPACE") else None,
        Path(r"E:\LLM_Workspace\.env") if Path(r"E:\LLM_Workspace\.env").exists() else None,
    ]
    for env_path in candidates:
        if env_path and env_path.exists():
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key and value and value != "vul_hier_in" and key not in os.environ:
                    os.environ[key] = value


def complete(house, system, user, model=None, temperature=0.2, max_tokens=2048):
    """Stuur system en user naar één huis. Antwoord is lokaal hersteld."""
    name = (house or "").strip().lower()
    if name not in _HOUSES:
        return f"[FOUT]: onbekend modelhuis '{house}'"
    spec = _HOUSES[name]
    _load_env()
    key = os.environ.get(spec["env"], "")
    if not key or key == "vul_hier_in":
        return f"[FOUT]: geen {spec['env']}"

    vault_holder = {}
    system_m, vault = mask(system or "")
    user_m, vault = mask(user or "", vault)
    vault_holder["v"] = vault
    chosen = model or spec["model"]

    try:
        if spec["style"] == "gemini":
            url = spec["url"].format(model=chosen) + f"?key={key}"
            payload = {
                "system_instruction": {"parts": [{"text": system_m}]},
                "contents": [{"parts": [{"text": user_m}]}],
                "generationConfig": {"temperature": temperature},
            }
            raw = _post(url, payload, None)
            text = raw["candidates"][0]["content"]["parts"][0]["text"]
        else:
            payload = {
                "model": chosen,
                "messages": [
                    {"role": "system", "content": system_m},
                    {"role": "user", "content": user_m},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            raw = _post(spec["url"], payload, key)
            text = raw["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"[FOUT {name}]: {exc}"
    return restore(text, vault_holder["v"])


def _post(url, payload, bearer):
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code}: {body}") from None
