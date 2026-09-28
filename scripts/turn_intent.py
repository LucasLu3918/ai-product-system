"""Conservative, advisory task classification for Turn Context selection."""
from __future__ import annotations

import re

MUTATION_EN = re.compile(r"\b(?:modify|change|fix|implement|add|remove|refactor|update|create|delete|rename|repair)\b", re.I)
MUTATION_ZH = re.compile(r"修改|調整|實作|新增|刪除|重構|修正|更新|修好|加入|移除|建立|完成")
NEGATED_ZH = re.compile(r"(?:不要|不用|不需|無須|勿|禁止|不得|別)\s*(?:對[^，。；]*?)?(?:修改|調整|實作|新增|刪除|重構|修正|更新|建立)")
NEGATED_EN = re.compile(r"\b(?:do not|don't|never|without|no need to)\s+(?:\w+\s+){0,2}?(?:modify|change|fix|implement|add|remove|refactor|update|create|delete|rename)\b", re.I)
EXPLANATION_EN = re.compile(r"\b(?:explain|describe|review|assess|analy[sz]e)\s+(?:the\s+)?(?:\w+\s+){0,2}?(?:update|change|implementation|build)\b", re.I)
EXPLANATION_ZH = re.compile(r"(?:建議|說明|解釋|評估|分析|檢視|查看)[^，。；]{0,15}(?:實作方式|實作建議|更新指令|修改方式|\bupdate\b\s*指令)", re.I)

TOPICS = (
    ("visual", re.compile(r"\b(?:css|ui|ux|button|tag|layout|visual|style)\b", re.I), re.compile(r"樣式|風格|按鈕|版面"), ["conventions", "modules"]),
    ("data", re.compile(r"\b(?:database|schema|sql|migration|table|db)\b", re.I), re.compile(r"資料庫|欄位|遷移"), ["architecture", "data-flow", "modules"]),
    ("security", re.compile(r"\b(?:auth|authorization|security|permission|token)\b", re.I), re.compile(r"權限|驗證|資安"), ["architecture", "security", "modules"]),
    ("testing", re.compile(r"\b(?:test|spec|coverage|tests)\b", re.I), re.compile(r"測試"), ["testing", "modules", "conventions"]),
    ("api", re.compile(r"\b(?:api|endpoint|request|response|handler|route)\b", re.I), re.compile(r"接口|介面|請求|回應"), ["architecture", "data-flow", "modules", "conventions"]),
)


def classify_prompt(prompt: str, intent: str = "auto") -> tuple[str, bool, list[str]]:
    if intent not in {"auto", "read", "write"}:
        raise ValueError("intent must be auto, read, or write")
    stripped = NEGATED_ZH.sub("", NEGATED_EN.sub("", prompt))
    stripped = EXPLANATION_ZH.sub("", EXPLANATION_EN.sub("", stripped))
    mutation = intent == "write" or (intent == "auto" and bool(MUTATION_EN.search(stripped) or MUTATION_ZH.search(stripped)))
    for category, en, zh, topics in TOPICS:
        if en.search(prompt) or zh.search(prompt):
            return category, mutation, topics
    return ("mutation" if mutation else "general"), mutation, (["architecture", "conventions", "modules"] if mutation else [])
