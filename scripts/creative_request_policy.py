"""Bounded user-only creative authorization; classifications are not grants."""
from __future__ import annotations

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


def user_texts(messages: Any) -> list[str]:
    """Accept native context messages; ignore assistant/tool/system text entirely."""
    if not isinstance(messages, list) or len(messages) > 64:
        raise ValueError("creative_messages_invalid")
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
        if len(text) > 8000:
            raise ValueError("creative_messages_invalid")
        if text.strip():
            texts.append(text.strip())
    return texts


def authorize(messages: Any, action: str) -> dict[str, Any]:
    if action not in {"prepare", "configure", "execute", "preflight", "discover"}:
        raise ValueError("creative_action_invalid")
    texts = user_texts(messages)
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
            # A new discussion/read request does not authorize mutation. Do not
            # resurrect an unrelated or older grant on a later short reply.
            anchor, generation, active = "", False, False
    allowed = active and bool(anchor) and (action != "execute" or generation)
    if action == "prepare" and anchor:
        allowed = allowed and classify_task(anchor)["intent"] == "create"
    return {
        "allowed": bool(allowed),
        "reason_code": "creative_request_authorized" if allowed else "creative_intent_required",
        "inherited": bool(allowed and anchor != latest),
        # Returned transiently to the adapter for Context, never to trace storage.
        "basis_prompt": anchor if allowed else "",
    }


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise ValueError("creative_messages_invalid")
        request = json.loads(raw)
        result = authorize(request["messages"], request["action"])
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError):
        print(json.dumps({"allowed": False, "reason_code": "creative_authorization_unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
