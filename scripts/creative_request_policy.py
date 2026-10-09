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
STYLE_SELECTION = re.compile(r"(?:[ABC]\s*(?:佈局|質感|配色|風格|構圖|色調|比例).{0,80}[ABC]\s*(?:佈局|質感|配色|風格|構圖|色調|比例)|[ABC]\s*(?:佈局|質感|配色|風格|構圖|色調|比例))", re.IGNORECASE)
CREATIVE_TARGET = re.compile(r"角色|人物|立繪|肖像|人像|character|portrait", re.IGNORECASE)
CONFIGURE = re.compile(r"設定|配置|configure|configuration", re.IGNORECASE)
VISUAL_REVIEW = re.compile(r"檢查|審查|評論|review|inspect|critique|quality", re.IGNORECASE)
OTHER_TASK = re.compile(r"程式|網站|資料庫|寄信|\b(?:python|javascript|website|database|email)\b", re.IGNORECASE)
MAX_PROMPT_CHARS = 8000
ACTIONS = {"prepare", "configure", "execute", "preflight", "discover", "review-assist"}
OUTPUT_COUNT = re.compile(r"(?:生成|產圖|繪製|畫|create|generate|render|draw|paint)\s*(\d{1,2})\s*(?:張|個|幅|名|images?|illustrations?|characters?|items?)", re.IGNORECASE)
CJK_COUNTS = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
CJK_OUTPUT_COUNT = re.compile(r"([一兩二三四五六七八九十])\s*(?:個|張|幅|名|位).{0,16}(?:角色|人物|圖片|插畫|圖|立繪|肖像|人像)")
ROLE_COUNT = re.compile(r"([一兩二三四五六七八九十])\s*(?:個|名|位)\s*(?:[^\s，,。；;]{0,8})?(?:角色|人物)")
ENGLISH_ROLE_COUNT = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:[a-z-]+\s+){0,2}(?:characters?|people|portraits?)\b", re.IGNORECASE)
MAX_AUTHORIZED_OUTPUTS = 24
MAX_CONTINUATION_TURNS = 3
CONTINUATION_VERSION = 1
SCOPE_EXPANSION = re.compile(r"再加|另外(?:再)?(?:加|新增)|增加(?:一位|一個|一名)?(?:角色|人物)|(?:改畫|改做|換成|改成).{0,20}(?:新|另一|其他|不同|場景|插畫|圖片|角色|人物)|(?:生成|產圖|繪製|畫|製作).{0,20}(?:森林|風景|場景|海報|背景|新角色|新人物|logo|banner)|\b(?:add another|one more character|expand the cast)\b", re.IGNORECASE)


def explicit_output_budget(prompt: str) -> int | None:
    match = OUTPUT_COUNT.search(prompt)
    if match:
        return max(1, min(MAX_AUTHORIZED_OUTPUTS, int(match.group(1))))
    matches = list(CJK_OUTPUT_COUNT.finditer(prompt))
    if matches:
        return CJK_COUNTS[matches[-1].group(1)]
    role_match = ROLE_COUNT.search(prompt)
    if role_match:
        return CJK_COUNTS[role_match.group(1)]
    english_match = ENGLISH_ROLE_COUNT.search(prompt)
    if english_match:
        return {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}[english_match.group(1).lower()]
    return None


def output_budget(prompt: str) -> int:
    return explicit_output_budget(prompt) or 1


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
    if action == "review-assist":
        review_task = classify_task(latest)
        allowed = bool(latest) and review_task["domain"] == "creative" and bool(VISUAL_REVIEW.search(latest)) and not STOP.search(latest) and not OTHER_TASK.search(latest)
        anchor = latest if allowed else ""
        active = allowed
    return {
        "allowed": bool(allowed),
        "reason_code": "creative_request_authorized" if allowed else "creative_intent_required",
        "inherited": bool(allowed and anchor != latest),
        "basis_prompt": anchor if allowed else "",
    }


def authorize(messages: Any, action: str) -> dict[str, Any]:
    return _authorize_texts(user_texts(messages), action)


def _valid_continuation(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("version") == CONTINUATION_VERSION
        and isinstance(value.get("max_outputs"), int)
        and 1 <= value["max_outputs"] <= MAX_AUTHORIZED_OUTPUTS
        and isinstance(value.get("turns_remaining"), int)
        and 1 <= value["turns_remaining"] <= MAX_CONTINUATION_TURNS
        and isinstance(value.get("allowed_actions"), list)
        and bool(value["allowed_actions"])
        and all(action in {"prepare", "configure", "execute", "review-assist"} for action in value["allowed_actions"])
    )


def _continuation_result(text: str, pending: Any) -> dict[str, Any] | None:
    """Issue a fresh bounded grant from a current response to an active creative task."""
    if not _valid_continuation(pending) or not text:
        return None
    task = classify_task(text)
    if SCOPE_EXPANSION.search(text):
        return {
            "active": False,
            "continued": False,
            "max_outputs": 0,
            "grants": {action: {"allowed": False, "reason_code": "creative_scope_expansion", "inherited": False}
                       for action in ("prepare", "configure", "execute", "review-assist")},
            "continuation": None,
            "reason_code": "creative_scope_expansion",
        }
    if (STOP.search(text) or OTHER_TASK.search(text)
            or task["intent"] in {"plan", "publish", "delete"}):
        return None
    requested = explicit_output_budget(text)
    if requested is not None and requested > pending["max_outputs"]:
        return {
            "active": False,
            "continued": False,
            "max_outputs": 0,
            "grants": {action: {"allowed": False, "reason_code": "creative_output_limit_exceeded", "inherited": False}
                       for action in ("prepare", "configure", "execute", "review-assist")},
            "continuation": None,
            "reason_code": "creative_output_limit_exceeded",
        }
    if (GENERATE.search(text) and not CREATIVE_TARGET.search(text)
            and not re.fullmatch(r"(?:繼續|繼續生成|再生成|請生成|生成|continue|generate)", text.strip(), re.IGNORECASE)):
        return {
            "active": False,
            "continued": False,
            "max_outputs": 0,
            "grants": {action: {"allowed": False, "reason_code": "creative_scope_expansion", "inherited": False}
                       for action in ("prepare", "configure", "execute", "review-assist")},
            "continuation": None,
            "reason_code": "creative_scope_expansion",
        }
    if not CONTINUE.search(text) and not (task["domain"] == "creative" and STYLE_SELECTION.search(text)):
        return None
    max_outputs = min(pending["max_outputs"], requested) if requested is not None else pending["max_outputs"]
    allowed_actions = set(pending["allowed_actions"])
    grants = {
        action: {
            "allowed": action in allowed_actions,
            "reason_code": "creative_request_continued" if action in allowed_actions else "creative_intent_required",
            "inherited": action in allowed_actions,
        }
        for action in ("prepare", "configure", "execute", "review-assist")
    }
    turns_remaining = pending["turns_remaining"] - 1
    continuation = ({
        "version": CONTINUATION_VERSION,
        "max_outputs": max_outputs,
        "turns_remaining": turns_remaining,
        "allowed_actions": sorted(allowed_actions),
    } if turns_remaining > 0 else None)
    return {
        "active": any(grant["allowed"] for grant in grants.values()),
        "continued": True,
        "grants": grants,
        "max_outputs": max_outputs,
        "continuation": continuation,
        "reason_code": "creative_request_continued",
    }


def admit_prompt(prompt: Any, pending: Any = None) -> dict[str, Any]:
    """Derive a fresh grant; optionally continue only a bounded in-memory task state."""
    text = _prompt_text(prompt)
    if _valid_continuation(pending):
        continued = _continuation_result(text, pending)
        if continued is not None:
            continued["prompt_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            return continued
    texts = [text] if text else []
    grants = {action: _authorize_texts(texts, action) for action in ("prepare", "configure", "execute", "review-assist")}
    active = any(grant["allowed"] for grant in grants.values())
    # The native adapter stores only action decisions and a digest, never prompt text.
    for grant in grants.values():
        grant.pop("basis_prompt", None)
    max_outputs = output_budget(text) if active else 0
    actions = [action for action, grant in grants.items() if grant["allowed"]]
    continuation = ({
        "version": CONTINUATION_VERSION,
        "max_outputs": max_outputs,
        "turns_remaining": MAX_CONTINUATION_TURNS,
        "allowed_actions": actions,
    } if active and actions else None)
    return {
        "active": active,
        "grants": grants,
        "max_outputs": max_outputs,
        "continued": False,
        "continuation": continuation,
        "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def main() -> int:
    try:
        raw = sys.stdin.buffer.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise PolicyError("creative_authorization_input_invalid")
        request = json.loads(raw)
        result = admit_prompt(request.get("prompt"), request.get("pending")) if request.get("action") == "admit" else authorize(request["messages"], request["action"])
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
