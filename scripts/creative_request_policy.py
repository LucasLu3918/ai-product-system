"""Prompt-scoped creative authorization; only admitted user prompts can grant mutations."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any

from turn_intent import classify_task

STOP = re.compile(r"取消|先停|停止|先不要|只規劃|只討論|不要(?:再)?(?:生成|產圖|繪製|畫)|\b(?:cancel|stop|pause|do not generate|don't generate|plan only)\b", re.IGNORECASE)
GENERATE = re.compile(r"生成|產圖|繪製|畫(?:一|兩|二|張|個|角色|圖)|(?:設計|製作).*(?:圖片|插畫|圖像)|\b(?:generate|render|draw|paint|create)\b.*\b(?:image|illustration|artwork|png|portrait)\b", re.IGNORECASE)
CONTINUE = re.compile(r"^(?:[ABC](?:$|\s)|選[ABC]|第[一二三]個|好(?:的)?|可以|繼續|用這個|照這個|依這個|改成|換成|調整|再生成|生成|請生成|ok\b|yes\b|continue\b|use this\b|generate\b|make it\b)", re.IGNORECASE)
CONFIGURE = re.compile(r"設定|配置|configure|configuration", re.IGNORECASE)
OTHER_TASK = re.compile(r"程式|網站|資料庫|寄信|\b(?:python|javascript|website|database|email)\b", re.IGNORECASE)
MAX_PROMPT_CHARS = 8000
ACTIONS = {"prepare", "configure", "execute", "preflight", "discover"}
OUTPUT_COUNT = re.compile(r"(?:生成|產圖|繪製|畫|create|generate|render|draw|paint)\s*(\d{1,2})\s*(?:張|個|幅|名|images?|illustrations?|characters?|items?)", re.IGNORECASE)
CJK_COUNTS = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
CJK_OUTPUT_COUNT = re.compile(r"([一兩二三四五六七八九十])(?:個|張|幅|名).{0,12}(?:角色|人物|圖片|插畫|圖)")
MAX_AUTHORIZED_OUTPUTS = 24


def output_budget(prompt: str) -> int:
    match = OUTPUT_COUNT.search(prompt)
    if match:
        return max(1, min(MAX_AUTHORIZED_OUTPUTS, int(match.group(1))))
    matches = list(CJK_OUTPUT_COUNT.finditer(prompt))
    if matches:
        return CJK_COUNTS[matches[-1].group(1)]
    return 1


class PolicyError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def _prompt_text(value: Any) -> str:
    if not isinstance(value, str) or len(value) > MAX_PROMPT_CHARS:
        raise PolicyError("creative_authorization_input_invalid")
    return value.strip()


def user_texts(messages: Any) -> list[str]:
    """Extract user text from legacy context input without a message-count cutoff."""
    if not isinstance(messages, list):
        raise PolicyError("creative_authorization_input_invalid")
    texts = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        info = message.get("info") or {}
        role = info.get("role") if isinstance(info, dict) else None
        if (role or message.get("role") or message.get("type")) != "user":
            continue
        parts = message.get("parts", message.get("content", message.get("text", [])))
        if isinstance(parts, str):
            text = parts
        elif isinstance(parts, list):
            text = "\n".join(p if isinstance(p, str) else str(p.get("text", "")) for p in parts if isinstance(p, (str, dict)))
        else:
            text = ""
        if len(text) > MAX_PROMPT_CHARS:
            raise PolicyError("creative_authorization_input_invalid")
        if text.strip():
            texts.append(text.strip())
    return texts


def _authorize_texts(texts: list[str], action: str) -> dict[str, Any]:
    if action not in ACTIONS:
        raise PolicyError("creative_authorization_action_invalid")
    if action in {"preflight", "discover"}:
        return {"allowed": True, "reason_code": "creative_readonly", "inherited": False}
    anchor = ""
    generation = False
    latest = ""
    active = False
    for text in texts:
        latest = text
        task = classify_task(text)
        if STOP.search(text):
            anchor, generation, active = "", False, False
        elif task["domain"] == "creative" and task["intent"] in {"create", "modify"}:
            if task["intent"] == "modify" and anchor:
                generation, active = generation or bool(GENERATE.search(text)), True
            else:
                anchor, generation, active = text, bool(GENERATE.search(text)), True
        elif task["intent"] in {"plan", "publish", "delete"} or OTHER_TASK.search(text):
            anchor, generation, active = "", False, False
        elif anchor and CONTINUE.search(text):
            active = True
            generation = generation or bool(GENERATE.search(text))
        elif anchor and CONFIGURE.search(text):
            active = action == "configure"
        else:
            anchor, generation, active = "", False, False
    allowed = active and bool(anchor) and (action != "execute" or generation)
    if action == "prepare" and anchor:
        allowed = allowed and classify_task(anchor)["intent"] == "create"
    return {
        "allowed": bool(allowed),
        "reason_code": "creative_request_authorized" if allowed else "creative_intent_required",
        "inherited": bool(allowed and anchor != latest),
        "basis_prompt": anchor if allowed else "",
    }


def authorize(messages: Any, action: str) -> dict[str, Any]:
    return _authorize_texts(user_texts(messages), action)


def admit_prompt(prompt: Any) -> dict[str, Any]:
    """Derive a short-lived action grant from one native prompt-admission event."""
    text = _prompt_text(prompt)
    texts = [text] if text else []
    grants = {action: _authorize_texts(texts, action) for action in ("prepare", "configure", "execute")}
    active = any(grant["allowed"] for grant in grants.values())
    # The native adapter stores only action decisions and a digest, never prompt text.
    for grant in grants.values():
        grant.pop("basis_prompt", None)
    return {
        "active": active,
        "grants": grants,
        "max_outputs": output_budget(text) if active else 0,
        "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise PolicyError("creative_authorization_input_invalid")
        request = json.loads(raw)
        result = admit_prompt(request.get("prompt")) if request.get("action") == "admit" else authorize(request["messages"], request["action"])
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except PolicyError as exc:
        print(json.dumps({"allowed": False, "reason_code": exc.reason_code}))
        return 2
    except (ValueError, KeyError, TypeError):
        print(json.dumps({"allowed": False, "reason_code": "creative_authorization_unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
