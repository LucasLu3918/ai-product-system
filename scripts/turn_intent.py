"""Conservative, advisory task classification for Turn Context selection."""
from __future__ import annotations

import re

MUTATION_EN = re.compile(r"\b(?:modify|change|fix|implement|add|remove|refactor|update|create|delete|rename|repair|generate|draw|render|export|save|write|overwrite)\b", re.IGNORECASE)
MUTATION_ZH = re.compile(r"修改|調整|實作|新增|刪除|重構|修正|更新|修好|加入|移除|建立|完成|生成|產生|繪製|畫|製作|輸出|儲存|存檔|寫入|覆寫")
NEGATED_ZH = re.compile(r"(?:不要|不用|不需|無須|勿|禁止|不得|別)\s*(?:對[^，。；]*?)?(?:修改|調整|實作|新增|刪除|重構|修正|更新|建立|完成|生成|產生|繪製|畫|製作|輸出|儲存|存檔|寫入|覆寫)")
NEGATED_EN = re.compile(r"\b(?:do not|don't|never|without|no need to)\s+(?:\w+\s+){0,2}?(?:modify|change|fix|implement|add|remove|refactor|update|create|delete|rename|generate|draw|render|export|save|write|overwrite)\b", re.IGNORECASE)
EXPLANATION_EN = re.compile(r"\b(?:explain|describe|review|assess|analy[sz]e)\s+(?:the\s+)?(?:\w+\s+){0,2}?(?:update|change|implementation|build)\b", re.IGNORECASE)
EXPLANATION_ZH = re.compile(r"(?:建議|說明|解釋|評估|分析|檢視|查看)[^，。；]{0,15}(?:實作方式|實作建議|更新指令|修改方式|\bupdate\b\s*指令)", re.IGNORECASE)

TOPICS = (
    ("creative", re.compile(r"\b(?:svg|png|image|illustration|character|artwork|asset|icon|drawing)\b", re.IGNORECASE), re.compile(r"SVG|PNG|插畫|角色|圖像|圖片|素材|繪圖|圖檔|圖示"), ["conventions", "modules"]),
    ("visual", re.compile(r"\b(?:css|ui|ux|button|tag|layout|visual|style)\b", re.IGNORECASE), re.compile(r"樣式|風格|按鈕|版面"), ["conventions", "modules"]),
    ("data", re.compile(r"\b(?:database|schema|sql|migration|table|db)\b", re.IGNORECASE), re.compile(r"資料庫|欄位|遷移"), ["architecture", "data-flow", "modules"]),
    ("security", re.compile(r"\b(?:auth|authorization|security|permission|token)\b", re.IGNORECASE), re.compile(r"權限|驗證|資安"), ["architecture", "security", "modules"]),
    ("testing", re.compile(r"\b(?:test|spec|coverage|tests)\b", re.IGNORECASE), re.compile(r"測試"), ["testing", "modules", "conventions"]),
    ("api", re.compile(r"\b(?:api|endpoint|request|response|handler|route)\b", re.IGNORECASE), re.compile(r"接口|介面|請求|回應"), ["architecture", "data-flow", "modules", "conventions"]),
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
    "creative_asset": (
        ("creative_direction", "orchestration/CREATIVE_DIRECTION.md"),
        ("visual_polish", "orchestration/VISUAL_POLISH.md"),
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
    ("publish", re.compile(r"\b(?:pull request|\bpr\b|merge|publish|publication|release|deploy|git push|remote branch)\b", re.IGNORECASE), re.compile(r"PR|合併|發布|上線|推送|遠端分支|發版")),
    ("product_delivery", re.compile(r"\b(?:product delivery|end.to.end delivery|deliver (?:the )?(?:product|feature)|complete product)\b", re.IGNORECASE), re.compile(r"產品交付|端到端交付|完整交付|交付功能")),
    ("creative_asset", re.compile(r"\b(?:svg|png|illustration|character art|artwork|creative asset|image asset)\b", re.IGNORECASE), re.compile(r"SVG|PNG|插畫|角色|圖像|圖片|素材|繪圖|圖檔|圖示")),
    ("visual", re.compile(r"\b(?:css|ui|ux|visual|design|layout|style|button)\b", re.IGNORECASE), re.compile(r"視覺|介面|使用者體驗|版面|樣式|按鈕|品牌")),
    ("security", re.compile(r"\b(?:auth|authorization|security|permission|secret|credential|token)\b", re.IGNORECASE), re.compile(r"資安|安全|權限|憑證|密鑰|祕密|令牌")),
    ("testing", re.compile(r"\b(?:test|testing|spec|coverage|conformance|validation)\b", re.IGNORECASE), re.compile(r"測試|驗證|涵蓋率|符合性")),
    ("api_data", re.compile(r"\b(?:api|endpoint|request|response|handler|database|schema|sql|migration|table|data flow)\b", re.IGNORECASE), re.compile(r"API|端點|請求|回應|資料庫|資料流|資料|結構描述|遷移")),
    ("planning", re.compile(r"\b(?:plan|planning|roadmap|requirements|blueprint)\b", re.IGNORECASE), re.compile(r"規劃|計畫|藍圖|需求")),
    ("documentation", re.compile(r"\b(?:documentation|docs|readme|document)\b", re.IGNORECASE), re.compile(r"文件|文檔|說明文件|README")),
)


def route_system_protocols(prompt: str, mutation: bool, root: str | None = None) -> dict:
    """Resolve canonical protocol pointers without persisting the prompt."""
    from pathlib import Path

    matched_categories = []
    for candidate, english, chinese in ROUTE_PATTERNS:
        if candidate == "creative_asset" and not mutation and not (CREATIVE_EN.search(prompt) or CREATIVE_ZH.search(prompt)):
            continue
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


PLAN_EN = re.compile(r"\b(?:plan|planning|design|outline|propose|brainstorm)\b", re.IGNORECASE)
PLAN_ZH = re.compile(r"規劃|計畫|設計方向|構思|提案|先討論")
READ_EN = re.compile(r"\b(?:read|inspect|open|show|list|summari[sz]e|explain|describe|analy[sz]e|review)\b", re.IGNORECASE)
READ_ZH = re.compile(r"讀取|查看|檢視|列出|摘要|介紹|說明|解釋|分析|審查")
EXTERNAL_EN = re.compile(r"\b(?:publish|deploy|release|push|merge|send|upload|submit|purchase|transfer)\b", re.IGNORECASE)
EXTERNAL_ZH = re.compile(r"發布|部署|上線|推送|合併|寄送|上傳|提交|購買|轉帳")
CREATIVE_EN = re.compile(r"\b(?:image|illustration|character|artwork|asset|icon|drawing)\b", re.IGNORECASE)
CREATIVE_ZH = re.compile(r"圖片|圖像|插畫|角色|素材|圖檔|圖示|繪圖")
ASSET_FORMAT = re.compile(r"\b(?:svg|png|jpe?g|webp)\b", re.IGNORECASE)


def classify_task(prompt: str, intent: str = "auto") -> dict[str, object]:
    """Return independent task domain, intent, and likely side-effect dimensions."""
    if intent not in {"auto", "read", "write"}:
        raise ValueError("intent must be auto, read, or write")
    stripped = NEGATED_ZH.sub("", NEGATED_EN.sub("", prompt))
    stripped = EXPLANATION_ZH.sub("", EXPLANATION_EN.sub("", stripped))
    external = bool(EXTERNAL_EN.search(stripped) or EXTERNAL_ZH.search(stripped))
    mutation = intent == "write" or (intent == "auto" and bool(MUTATION_EN.search(stripped) or MUTATION_ZH.search(stripped)))
    asset = bool(CREATIVE_EN.search(prompt) or CREATIVE_ZH.search(prompt) or (ASSET_FORMAT.search(prompt) and mutation))
    if external:
        task_intent = "publish"
    elif PLAN_EN.search(stripped) or PLAN_ZH.search(stripped):
        task_intent = "plan"
    elif re.search(r"\b(?:delete|remove|erase)\b", stripped, re.IGNORECASE) or re.search(r"刪除|移除|刪掉", stripped):
        task_intent = "delete"
    elif re.search(r"\b(?:modify|edit|update|change|fix|repair|overwrite)\b", stripped, re.IGNORECASE) or re.search(r"修改|編輯|調整|修正|更新|覆寫", stripped):
        task_intent = "modify"
    elif mutation:
        task_intent = "create"
    elif READ_EN.search(prompt) or READ_ZH.search(prompt):
        task_intent = "read"
    else:
        task_intent = "discuss"
    effect = "external_action" if external else "filesystem_write" if mutation else "chat_only"
    if effect == "chat_only" and asset:
        effect = "chat_only"
    domain = (
        "creative" if asset else
        "data" if any(re.search(p, prompt, re.IGNORECASE) for p in (r"\b(?:database|schema|sql|migration|table|db)\b", r"資料庫|欄位|遷移")) else
        "document" if re.search(r"\b(?:document|documentation|docs|readme|report|memo)\b|文件|文檔|報告|備忘錄", prompt, re.IGNORECASE) else
        "software" if mutation else "general"
    )
    category = "creative" if asset else "general"
    for category, en, zh, topics in TOPICS:
        if category == "creative" and not asset:
            continue
        if en.search(prompt) or zh.search(prompt):
            selected_category, selected_topics = category, topics
            break
    else:
        selected_category = "mutation" if mutation else "general"
        selected_topics = ["architecture", "conventions", "modules"] if mutation else []
    if domain == "creative" and task_intent == "plan":
        effect = "chat_only"
    return {"category": selected_category, "mutation_likely": mutation, "topics": selected_topics,
            "domain": domain, "intent": task_intent, "effect": effect}


def classify_prompt(prompt: str, intent: str = "auto") -> tuple[str, bool, list[str]]:
    """Backward-compatible category/mutation/topics view of ``classify_task``."""
    result = classify_task(prompt, intent)
    return str(result["category"]), bool(result["mutation_likely"]), list(result["topics"])
