# bank_slim/llm_utils.py
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Default audit log path (relative to project). Ensure directory exists before writing.
DEFAULT_AUDIT_DIR = Path(__file__).resolve().parent / "logs"
DEFAULT_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_AUDIT_FILE = DEFAULT_AUDIT_DIR / "llm_audit.log"


async def _call_llm_and_log(
    sk,
    prompt: str,
    attempt: int,
    agent: Optional[str],
    audit_file: Path,
    timeout_seconds: Optional[float],
    gen_kwargs: Dict[str, Any],
) -> str:
    """
    Helper: call sk.generate_text(prompt, **gen_kwargs) with optional timeout and write
    an audit entry (prompt + response) to audit_file. Returns raw text (may be empty on timeout).
    """
    ts = datetime.now().isoformat() + "Z"
    raw_text = ""
    error = None

    try:
        if timeout_seconds is None:
            raw_text = await sk.generate_text(prompt, **gen_kwargs)
        else:
            raw_text = await asyncio.wait_for(sk.generate_text(prompt, **gen_kwargs), timeout=timeout_seconds)
    except asyncio.TimeoutError as e:
        error = f"timeout after {timeout_seconds}s"
        raw_text = ""
    except Exception as e:
        error = str(e)
        raw_text = ""

    # Build audit record
    record = {
        "timestamp": ts,
        "agent": agent or "unknown",
        "attempt": attempt,
        "prompt": prompt,
        "response": raw_text,
        "error": error,
        "gen_kwargs": gen_kwargs,
    }

    # Append JSON line to audit file
    try:
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error in appending Audit file, {e}")

    return raw_text


async def parse_json_with_retry(
    sk,
    prompt: str,
    example_shape: Optional[Dict[str, Any]] = None,
    max_retries: int = 2,
    retry_suffix: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    agent: Optional[str] = None,
    audit_file: Optional[str] = None,
    **gen_kwargs,
) -> Dict[str, Any]:
    """
    Ask the SK wrapper (sk.generate_text) to produce JSON, try to parse it,
    and if parsing fails, ask the model (up to max_retries times) to reformat
    its previous output into valid JSON.

    Parameters:
      - sk: SKWrapper-like object with async generate_text(prompt, **gen_kwargs)
      - prompt: initial prompt instructing the LLM to return JSON
      - example_shape: helpful example JSON shape to include in reformat instructions
      - max_retries: number of reformat attempts when parsing fails (default 2)
      - timeout_seconds: optional per-call timeout (seconds)
      - agent: optional string (e.g. "coordinator", "fraud") used in audit log
      - audit_file: optional path to JSONL audit file (defaults to bank_slim/logs/llm_audit.log)
      - **gen_kwargs: forwarded to sk.generate_text (temperature, max_tokens, etc)

    Returns:
      - parsed dict on success
      - on persistent failure returns {"__parse_error__": True, "raw_text": "<last llm text>"}
    """

    audit_path = Path(audit_file) if audit_file else DEFAULT_AUDIT_FILE

    # Build a canonical reformat instruction using example_shape for clarity
    try:
        example_text = json.dumps(example_shape, indent=2, ensure_ascii=False) if example_shape is not None else ""
    except Exception:
        example_text = str(example_shape or "")

    if retry_suffix is None:
        retry_suffix = (
            "Return ONLY valid JSON and nothing else. If you cannot produce valid JSON, "
            "return a single JSON object with an 'error' key describing why."
        )

    attempt = 0
    last_text = ""
    current_prompt = prompt

    while attempt <= max_retries:
        attempt += 1

        # call LLM and log the call/response
        last_text = await _call_llm_and_log(
            sk=sk,
            prompt=current_prompt,
            attempt=attempt,
            agent=agent,
            audit_file=audit_path,
            timeout_seconds=timeout_seconds,
            gen_kwargs=gen_kwargs or {},
        )

        # try parse
        try:
            parsed = json.loads(last_text)
            if isinstance(parsed, dict):
                # Successful parse -> log success marker (append small success record)
                try:
                    with open(audit_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"timestamp": datetime.utcnow().isoformat() + "Z", "agent": agent or "unknown", "parse_success": True, "attempt": attempt}, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                return parsed
            # if parsed is list/other wrap it
            return {"result": parsed}
        except Exception:
            # try to extract braces block
            start = last_text.find("{")
            end = last_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = last_text[start:end+1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                    return {"result": parsed}
                except Exception:
                    pass

        # If reached here, parse failed. If attempts remain, ask LLM to reformat.
        if attempt <= max_retries:
            # Compose reformat prompt that includes the previous output verbatim.
            reformat_prompt = (
                "The output you provided is not valid JSON. Here is your previous output (exactly):\n\n"
                "<<<BEGIN OUTPUT>>>\n"
                f"{last_text}\n"
                "<<<END OUTPUT>>>\n\n"
                "Please reformat the above output into VALID JSON ONLY (no surrounding text), "
                "matching this example shape:\n\n"
                f"{example_text}\n\n"
                f"{retry_suffix}\n"
                "Return only valid JSON."
            )
            current_prompt = reformat_prompt
            # small backoff to avoid rate issues
            await asyncio.sleep(0.2)
            continue

        # all retries exhausted -> return parse error structure and keep raw_text for debugging
        try:
            with open(audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"timestamp": datetime.utcnow().isoformat() + "Z", "agent": agent or "unknown", "parse_success": False, "attempts": attempt, "final_raw": last_text[:2000]}, ensure_ascii=False) + "\n")
        except Exception:
            pass

        return {"__parse_error__": True, "raw_text": last_text}
