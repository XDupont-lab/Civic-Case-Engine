"""Eén deur naar de modelhuizen.

Gratis instap met 1 Gmail-account (agy / Gemini Flash) + 1 gratis NVIDIA-registratie
(meerdere onafhankelijke modelfamilies op integrate.api.nvidia.com: Nemotron 120B,
OpenAI GPT-OSS 20B, MiniMax M3.1 Flash), plus optioneel DeepSeek, Mistral, Qwen en Grok.
De sleutel blijft in de omgeving. Elke tekst wordt lokaal gemaskeerd via pii_mask.py.
"""

import json
import os
import re
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
    "nvidia": {
        "env": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
        "style": "openai",
    },
    "nvidia_gpt": {
        "env": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "openai/gpt-oss-20b",
        "style": "openai",
    },
    "nvidia_minimax": {
        "env": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "minimaxai/minimax-m3.1-flash",
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
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg_key:
                for env_name in (
                    "DEEPSEEK_API_KEY",
                    "MISTRAL_API_KEY",
                    "GROQ_API_KEY",
                    "NVIDIA_API_KEY",
                    "OPENROUTER_API_KEY",
                    "GOOGLE_API_KEY",
                ):
                    if env_name not in os.environ:
                        try:
                            val, _ = winreg.QueryValueEx(reg_key, env_name)
                            if val and str(val).strip() and str(val).strip() != "vul_hier_in":
                                os.environ[env_name] = str(val).strip()
                        except FileNotFoundError:
                            pass
        except Exception:
            pass
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent / "Shared_Tools" / ".env",
        Path(__file__).resolve().parent.parent.parent / "Shared_Tools" / ".env",
        Path(os.environ.get("CIVIC_WORKSPACE", "")) / ".env" if os.environ.get("CIVIC_WORKSPACE") else None,
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


def available():
    """Geeft per modelhuis terug of er een sleutel in de omgeving staat (zonder de sleutel zelf te tonen)."""
    _load_env()
    status = {}
    nv_ok = bool(os.environ.get("NVIDIA_API_KEY", "") and os.environ.get("NVIDIA_API_KEY") != "vul_hier_in")
    for name, spec in _HOUSES.items():
        val = os.environ.get(spec["env"], "")
        if name in ("mistral", "deepseek", "grok") and (not val or val == "vul_hier_in") and nv_ok:
            status[name] = True
        else:
            status[name] = bool(val and val != "vul_hier_in")
    return status


def _scrub_tokens(text: str, *known_keys) -> str:
    if not text:
        return text
    cleaned = str(text)
    for k in known_keys:
        if k and isinstance(k, str) and len(k) > 6:
            cleaned = cleaned.replace(k, "[VERBORGEN_SLEUTEL]")
    cleaned = re.sub(r"(\?key=)[^&\s\"\']+", r"\1[VERBORGEN_SLEUTEL]", cleaned)
    cleaned = re.sub(r'(Bearer\s+)[A-Za-z0-9_\-\.]{8,}', r'\1[VERBORGEN_SLEUTEL]', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'nvapi-[A-Za-z0-9_\-]{8,}', '[VERBORGEN_SLEUTEL]', cleaned)
    cleaned = re.sub(r'AIza[0-9A-Za-z-_]{20,}', '[VERBORGEN_SLEUTEL]', cleaned)
    cleaned = re.sub(r'sk-[A-Za-z0-9_\-]{20,}', '[VERBORGEN_SLEUTEL]', cleaned)
    return cleaned

def complete(house, system, user, model=None, temperature=0.2, max_tokens=2048):
    """Stuur system en user naar één huis. Antwoord is lokaal hersteld."""
    name = (house or "").strip().lower()
    if name not in _HOUSES:
        return f"[FOUT]: onbekend modelhuis '{house}'"
    spec = _HOUSES[name]
    _load_env()
    key = os.environ.get(spec["env"], "")
    url = spec["url"]
    chosen = model or spec["model"]

    nv_key = os.environ.get("NVIDIA_API_KEY", "")
    if (not key or key == "vul_hier_in") and nv_key and nv_key != "vul_hier_in":
        if name in ("mistral", "deepseek"):
            key = nv_key
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            chosen = "nvidia/nemotron-3.5-super-vl-120b-a12b"
        elif name == "grok":
            key = nv_key
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            chosen = "openai/gpt-oss-20b"

    if not key or key == "vul_hier_in":
        return f"[FOUT]: geen {spec['env']}"

    vault_holder = {}
    system_m, vault = mask(system or "")
    user_m, vault = mask(user or "", vault)
    vault_holder["v"] = vault

    try:
        if spec["style"] == "gemini" and url.startswith("https://generativelanguage"):
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
            if any(tag in chosen for tag in ("nemotron", "gpt-oss", "minimax")):
                payload["chat_template_kwargs"] = {"enable_thinking": False}
            raw = _post(url, payload, key)
            msg = raw["choices"][0]["message"]
            text = msg.get("content") or msg.get("reasoning_content") or ""
    except Exception as exc:
        if name == "gemini" and ("402" in str(exc) or "429" in str(exc)) and nv_key and nv_key != "vul_hier_in":
            try:
                nv_payload = {
                    "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
                    "messages": [
                        {"role": "system", "content": system_m},
                        {"role": "user", "content": user_m},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "chat_template_kwargs": {"enable_thinking": False},
                }
                raw = _post("https://integrate.api.nvidia.com/v1/chat/completions", nv_payload, nv_key)
                msg = raw["choices"][0]["message"]
                text = msg.get("content") or msg.get("reasoning_content") or ""
                return restore(text, vault_holder["v"])
            except Exception:
                pass
        return f"[FOUT {name}]: {_scrub_tokens(str(exc), key, nv_key)}"
    return restore(text, vault_holder["v"])


def _post(url, payload, bearer):
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Antigravity-ModelBus/1.0",
    }
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        clean_body = _scrub_tokens(body, bearer)
        raise RuntimeError(f"HTTP {exc.code}: {clean_body}") from None
