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

PROTOCOL_ROUTES = {
    "general_read": (
        ("orchestrator", "orchestration/ORCHESTRATOR.md"),
    ),
    "general_mutation": (
        ("orchestrator", "orchestration/ORCHESTRATOR.md"),
        ("change_impact", "orchestration/CHANGE_IMPACT.md"),
        ("quality_planning", "orchestration/QUALITY_PLANNING.md"),
    ),
    "publish": (
        ("orchestrator", "orchestration/ORCHESTRATOR.md"),
        ("release_readiness", "orchestration/RELEASE_READINESS.md"),
        ("branch_hygiene", "orchestration/BRANCH_HYGIENE.md"),
    ),
    "product_delivery": (
        ("product_delivery", "orchestration/PRODUCT_DELIVERY.md"),
        ("requirement_clarification", "orchestration/REQUIREMENT_CLARIFICATION.md"),
        ("quality_planning", "orchestration/QUALITY_PLANNING.md"),
    ),
    "visual": (
        ("visual_polish", "orchestration/VISUAL_POLISH.md"),
        ("creative_direction", "orchestration/CREATIVE_DIRECTION.md"),
        ("brand_system", "orchestration/BRAND_SYSTEM.md"),
    ),
    "security": (
        ("secret_handling", "orchestration/SECRET_HANDLING.md"),
        ("security_assurance", "docs/human/SECURITY_ASSURANCE.md"),
        ("content_safety", "orchestration/CONTENT_SAFETY_BOUNDARY.md"),
    ),
    "testing": (
        ("quality_planning", "orchestration/QUALITY_PLANNING.md"),
        ("conformance", "orchestration/CONFORMANCE.md"),
        ("core_change_testing", "orchestration/CORE_CHANGE_TESTING.md"),
    ),
    "api_data": (
        ("change_impact", "orchestration/CHANGE_IMPACT.md"),
        ("project_intelligence", "orchestration/PROJECT_INTELLIGENCE.md"),
        ("quality_planning", "orchestration/QUALITY_PLANNING.md"),
    ),
    "planning": (
        ("planning_package", "orchestration/PLANNING_PACKAGE.md"),
        ("requirement_clarification", "orchestration/REQUIREMENT_CLARIFICATION.md"),
        ("project_identity", "orchestration/PROJECT_IDENTITY.md"),
    ),
    "documentation": (
        ("documentation_sync", "orchestration/DOCUMENTATION_SYNC.md"),
        ("conformance", "orchestration/CONFORMANCE.md"),
        ("maintenance", "docs/human/MAINTENANCE.md"),
    ),
}

ROUTE_PATTERNS = (
    ("publish", re.compile(r"\b(?:pull request|\bpr\b|merge|publish|publication|release|deploy|git push|remote branch)\b", re.I), re.compile(r"PR|合併|發布|上線|推送|遠端分支|發版")),
    ("product_delivery", re.compile(r"\b(?:product delivery|end.to.end delivery|deliver (?:the )?(?:product|feature)|complete product)\b", re.I), re.compile(r"產品交付|端到端交付|完整交付|交付功能")),
    ("visual", re.compile(r"\b(?:css|ui|ux|visual|design|layout|style|button)\b", re.I), re.compile(r"視覺|介面|使用者體驗|版面|樣式|按鈕|品牌")),
    ("security", re.compile(r"\b(?:auth|authorization|security|permission|secret|credential|token)\b", re.I), re.compile(r"資安|安全|權限|憑證|密鑰|祕密|令牌")),
    ("testing", re.compile(r"\b(?:test|testing|spec|coverage|conformance|validation)\b", re.I), re.compile(r"測試|驗證|涵蓋率|符合性")),
    ("api_data", re.compile(r"\b(?:api|endpoint|request|response|handler|database|schema|sql|migration|table|data flow)\b", re.I), re.compile(r"API|端點|請求|回應|資料庫|資料流|資料|結構描述|遷移")),
    ("planning", re.compile(r"\b(?:plan|planning|roadmap|requirements|blueprint)\b", re.I), re.compile(r"規劃|計畫|藍圖|需求")),
    ("documentation", re.compile(r"\b(?:documentation|docs|readme|document)\b", re.I), re.compile(r"文件|文檔|說明文件|README")),
)


def route_system_protocols(prompt: str, mutation: bool, root: str | None = None) -> dict:
    """Resolve canonical protocol pointers without persisting the prompt."""
    from pathlib import Path

    matched_categories = []
    for candidate, english, chinese in ROUTE_PATTERNS:
        if english.search(prompt) or chinese.search(prompt):
            matched_categories.append(candidate)
    category = (matched_categories or ["general_mutation" if mutation else "general_read"])[0]
    selected_categories = matched_categories or [category]

    base = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    core = base / "SYSTEM_CORE.md"
    selected = list(dict.fromkeys(
        protocol for selected_category in selected_categories for protocol in PROTOCOL_ROUTES[selected_category]
    ))
    missing = []
    protocols = []
    for protocol_id, relative_path in selected:
        path = base / relative_path
        if not path.is_file():
            missing.append(relative_path)
        protocols.append({"id": protocol_id, "path": str(path)})
    if not core.is_file():
        missing.append("SYSTEM_CORE.md")
    return {
        "category": category,
        "matched_categories": selected_categories,
        "status": "UNAVAILABLE" if missing else "READY",
        "system_core": {"path": str(core), "bytes": core.stat().st_size if core.is_file() else None},
        "protocols": protocols,
        "missing": missing,
    }


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
