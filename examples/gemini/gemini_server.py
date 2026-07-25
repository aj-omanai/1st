#!/usr/bin/env python3
"""
Gemini MCP Server - Lets Claude call Google Gemini models as tools.
"""
import os
import sys
import logging
import json
import urllib.request
import urllib.error

from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
)
logger = logging.getLogger("gemini-server")

mcp = FastMCP("gemini")

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = os.environ.get("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash")


def _get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it as a Docker MCP secret or "
            "pass it as an environment variable."
        )
    return key


def _call_gemini(model: str, contents: list, generation_config: dict | None = None) -> dict:
    api_key = _get_api_key()
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent"
    payload: dict = {"contents": contents}
    if generation_config:
        payload["generationConfig"] = generation_config

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error {e.code}: {body}") from None


def _extract_text(response: dict) -> str:
    candidates = response.get("candidates") or []
    if not candidates:
        feedback = response.get("promptFeedback")
        if feedback:
            return f"(no candidates returned; promptFeedback: {json.dumps(feedback)})"
        return "(empty response from Gemini)"
    parts = candidates[0].get("content", {}).get("parts", []) or []
    return "".join(p.get("text", "") for p in parts).strip() or "(empty text)"


@mcp.tool()
async def gemini_ask(prompt: str, model: str = "", temperature: str = "") -> str:
    """Ask a Google Gemini model a question and return the text response.

    prompt: the user prompt to send to Gemini.
    model: Gemini model id (e.g. gemini-2.5-flash, gemini-2.5-pro). Defaults to gemini-2.5-flash.
    temperature: optional float 0.0-2.0 to control randomness.
    """
    if not prompt.strip():
        return "Error: prompt is required."
    model_id = model.strip() or DEFAULT_MODEL
    gen_config: dict = {}
    if temperature.strip():
        try:
            gen_config["temperature"] = float(temperature)
        except ValueError:
            return f"Error: invalid temperature '{temperature}'."

    logger.info("gemini_ask model=%s temp=%s", model_id, gen_config.get("temperature"))
    try:
        response = _call_gemini(
            model_id,
            [{"role": "user", "parts": [{"text": prompt}]}],
            gen_config or None,
        )
        return _extract_text(response)
    except Exception as e:
        logger.error("gemini_ask failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def gemini_chat(messages_json: str, model: str = "", system: str = "") -> str:
    """Multi-turn chat with Gemini.

    messages_json: JSON array like [{"role":"user","text":"hi"},{"role":"model","text":"hello"}].
    model: Gemini model id. Defaults to gemini-2.5-flash.
    system: optional system instruction prepended as a user turn.
    """
    try:
        raw = json.loads(messages_json)
        if not isinstance(raw, list) or not raw:
            return "Error: messages_json must be a non-empty JSON array."
    except json.JSONDecodeError as e:
        return f"Error: messages_json is not valid JSON: {e}"

    contents = []
    if system.strip():
        contents.append({"role": "user", "parts": [{"text": f"[system]\n{system.strip()}"}]})
    for m in raw:
        role = m.get("role", "user")
        if role not in ("user", "model"):
            return f"Error: role must be 'user' or 'model', got '{role}'."
        text = m.get("text", "")
        contents.append({"role": role, "parts": [{"text": text}]})

    model_id = model.strip() or DEFAULT_MODEL
    logger.info("gemini_chat model=%s turns=%d", model_id, len(contents))
    try:
        response = _call_gemini(model_id, contents)
        return _extract_text(response)
    except Exception as e:
        logger.error("gemini_chat failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def gemini_list_models() -> str:
    """List Gemini models available to your API key."""
    try:
        api_key = _get_api_key()
        req = urllib.request.Request(
            f"{GEMINI_API_BASE}/models",
            headers={"x-goog-api-key": api_key},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return f"Error {e.code}: {e.read().decode('utf-8', errors='replace')}"
    except Exception as e:
        return f"Error: {e}"

    names = [m.get("name", "").removeprefix("models/") for m in data.get("models", [])]
    names = [n for n in names if n]
    if not names:
        return "(no models returned)"
    return "Available Gemini models:\n" + "\n".join(f"- {n}" for n in sorted(names))


if __name__ == "__main__":
    logger.info("Starting Gemini MCP server (default model: %s)...", DEFAULT_MODEL)
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        sys.exit(1)
