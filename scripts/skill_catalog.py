"""Generate a self-contained Skill Explorer from the canonical AIPS registry."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "skills/INDEX.yaml"
SOURCE = ROOT / "skills/integrations/matt-pocock-skills.json"
OUTPUT = ROOT / "docs/human/public/skill-catalog.html"

DISPOSITION = {
    "merged": ("已合併至 AIPS", "integrated"),
    "adopted": ("已新增為 AIPS Skill", "adopted"),
    "adopted_optional": ("選用 Skill", "optional"),
    "workflow": ("整合至既有流程", "workflow"),
    "deferred": ("延後評估", "deferred"),
    "excluded_beta": ("依決策排除 Beta", "excluded"),
    "reference_only": ("僅保留來源參考", "reference"),
    "not_adopted": ("不導入", "not-adopted"),
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def title(identifier: str) -> str:
    return identifier.replace("-", " ").title()


def prompt_for_active(identifier: str, triggers: list[str]) -> str:
    trigger = triggers[0].replace("_", " ") if triggers else identifier.replace("-", " ")
    return (
        f"請使用 AIPS 的「{identifier}」Skill，協助我處理「{trigger}」的需求。"
        "請依照技能指引完成，並列出結果與限制。"
    )


def build_cards(registry: dict[str, Any], source: dict[str, Any]) -> tuple[str, list[str]]:
    cards: list[str] = []
    categories: set[str] = set()
    active = registry.get("skills")
    if not isinstance(active, dict):
        raise TypeError("skills/INDEX.yaml must contain a skills mapping")

    for identifier, skill in sorted(active.items()):
        category = str(skill.get("capability", "other"))
        categories.add(category)
        prompt = prompt_for_active(identifier, skill.get("triggers") or [])
        search = " ".join(
            [identifier, skill.get("description", ""), category, prompt, "AIPS 啟用"]
        )
        cards.append(
            '<article class="card" data-category="{category}" data-status="enabled" data-search="{search}">'
            '<div class="badges"><span class="badge">{category}</span><span class="badge status-enabled">AIPS 啟用</span></div>'
            '<h2>{name}</h2><code>{identifier}</code><p>{description}</p>'
            '<p class="detail"><strong>用途</strong> {description}</p>'
            '<p class="detail"><strong>來源</strong> AIPS canonical Skill · {path}</p>'
            '<details><summary>使用範例</summary><p>{prompt}</p>'
            '<button class="copy" type="button" data-prompt="{prompt}" aria-label="複製 {identifier} 使用範例">複製範例</button></details>'
            "</article>".format(
                category=esc(category),
                search=esc(search),
                name=esc(title(identifier)),
                identifier=esc(identifier),
                description=esc(skill.get("description", "")),
                path=esc(skill.get("path", "")),
                prompt=esc(prompt),
            )
        )

    records = source.get("skills")
    if not isinstance(records, list):
        raise TypeError("source disposition must contain a skills list")
    for record in records:
        disposition = record.get("disposition")
        if disposition not in DISPOSITION:
            raise ValueError(f"unsupported disposition for {record.get('id')}: {disposition}")
        label, status = DISPOSITION[disposition]
        category = str(record.get("category", "other"))
        categories.add(category)
        targets = record.get("aips_targets") or []
        prompt = (
            f"請參考上游 {record['id']} 的方法，使用 AIPS 已整合的 "
            f"{'、'.join(targets)} 來處理「{record['description']}」；"
            "完成後說明採用範圍與任何限制。"
            if disposition in {"merged", "adopted", "adopted_optional", "workflow"} and targets
            else f"請檢視上游 {record['id']} 的用途與 AIPS 處置，說明差異；不要把未採用項目當成可用的 AIPS Skill。"
        )
        target_text = "、".join(targets) if targets else "無；目前沒有啟用對應 AIPS Skill"
        search = " ".join(
            [record.get("id", ""), record.get("description", ""), category, label, target_text, record.get("reason", ""), prompt]
        )
        cards.append(
            '<article class="card upstream" data-category="{category}" data-status="{status}" data-search="{search}">'
            '<div class="badges"><span class="badge">{category}</span><span class="badge status-{status}">{label}</span></div>'
            '<h2>{name}</h2><code>{identifier}</code><p>{description}</p>'
            '<p class="detail"><strong>AIPS 處置</strong> {reason}</p>'
            '<p class="detail"><strong>對應</strong> {targets}</p>'
            '<p class="detail"><strong>上游路徑</strong> {path}</p>'
            '<details><summary>使用範例 / 查看方式</summary><p>{prompt}</p>'
            '<button class="copy" type="button" data-prompt="{prompt}" aria-label="複製 {identifier} 範例">複製範例</button></details>'
            "</article>".format(
                category=esc(category),
                status=esc(status),
                search=esc(search),
                label=esc(label),
                name=esc(title(record.get("id", ""))),
                identifier=esc(record.get("id", "")),
                description=esc(record.get("description", "")),
                reason=esc(record.get("reason", "")),
                targets=esc(target_text),
                path=esc(record.get("path", "")),
                prompt=esc(prompt),
            )
        )
    return "\n".join(cards), sorted(categories)


def render() -> str:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    expected_categories = {"engineering": 20, "productivity": 7, "in-progress": 7, "misc": 4}
    if source.get("source", {}).get("commit") != "49dd158d1076134a641b33efb035946536778336":
        raise ValueError("upstream source commit is not pinned to the reviewed SHA")
    records = source.get("skills")
    if not isinstance(records, list) or len(records) != 38:
        raise ValueError("the upstream inventory must classify exactly 38 Skills")
    counts: dict[str, int] = {}
    for record in records:
        category = record.get("category")
        counts[category] = counts.get(category, 0) + 1
    if counts != expected_categories:
        raise ValueError(f"upstream category counts mismatch: {counts}")

    cards, categories = build_cards(registry, source)
    active_count = len(registry["skills"])
    category_options = "\n".join(
        f'<option value="{esc(category)}">{esc(category)}</option>' for category in categories
    )
    source_sha = source["source"]["commit"]
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="搜尋 AIPS Skills，查看用途、狀態與可複製的使用範例。">
<title>AIPS Skill Explorer</title>
<style>
:root{{color-scheme:light dark;--bg:#f5f7fb;--panel:#fff;--ink:#172033;--muted:#526078;--line:#d8deea;--accent:#245fe8;--chip:#eaf0ff}}
@media(prefers-color-scheme:dark){{:root{{--bg:#111722;--panel:#1b2534;--ink:#edf2fb;--muted:#afbdd0;--line:#34445a;--accent:#8db0ff;--chip:#26385a}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header,main,footer{{max-width:1180px;margin:auto;padding:24px}}header{{padding-top:44px}}h1{{font-size:clamp(2rem,5vw,3.2rem);line-height:1.1;margin:.2em 0}}h2{{font-size:1.15rem;margin:.65em 0 .2em}}p{{margin:.65em 0}}.lede,.muted{{color:var(--muted)}}.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0}}.stat,.control,.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px}}.stat{{padding:10px 15px}}.stat strong{{font-size:1.2rem;margin-right:6px}}.controls{{display:grid;grid-template-columns:minmax(220px,2fr) 1fr 1fr;gap:12px;margin:20px 0}}input,select{{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);font:inherit}}#results{{color:var(--muted);margin:10px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,330px),1fr));gap:14px}}.card{{padding:17px;min-width:0}}.card[hidden]{{display:none}}.card code{{font-size:.84rem;color:var(--muted);overflow-wrap:anywhere}}.badges{{display:flex;gap:7px;flex-wrap:wrap}}.badge{{font-size:.76rem;padding:3px 9px;border-radius:999px;background:var(--chip);color:var(--accent)}}.badge[class*="status-"]{{background:#e8f5ed;color:#176a37}}@media(prefers-color-scheme:dark){{.badge[class*="status-"]{{background:#193b2a;color:#9ce0b1}}}}.badge.status-deferred,.badge.status-reference,.badge.status-excluded,.badge.status-not-adopted{{background:#fff2d8;color:#815200}}@media(prefers-color-scheme:dark){{.badge.status-deferred,.badge.status-reference,.badge.status-excluded,.badge.status-not-adopted{{background:#493719;color:#f2c774}}}}.detail{{font-size:.92rem;color:var(--muted)}}strong{{color:var(--ink)}}details{{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}}summary{{cursor:pointer;color:var(--accent);font-weight:650}}button{{border:0;border-radius:8px;padding:8px 12px;background:var(--accent);color:white;font:inherit;cursor:pointer}}button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{{outline:3px solid var(--accent);outline-offset:2px}}footer{{color:var(--muted);font-size:.86rem}}@media(max-width:700px){{.controls{{grid-template-columns:1fr}}header,main,footer{{padding-left:16px;padding-right:16px}}}}
</style>
</head>
<body>
<header>
<p class="muted">AI Product System · 技能圖鑑</p>
<h1>找到適合這項工作的 Skill</h1>
<p class="lede">搜尋 AIPS 現有 Skills 與 Matt Pocock 上游 38 項處置紀錄。卡片會標示哪些已整合、選用、流程化、延後或不導入；上游項目不會因此自動成為 AIPS 可用 Skill。</p>
<div class="stats"><div class="stat"><strong>{active_count}</strong>AIPS 可用 Skills</div><div class="stat"><strong>38</strong>上游 Skills 全數有處置</div><div class="stat"><strong>{active_count + 38}</strong>可搜尋卡片</div></div>
<div class="controls">
<label><span class="muted">搜尋名稱、用途、情境</span><input id="search" type="search" placeholder="例如：debug、測試、writing" autocomplete="off"></label>
<label><span class="muted">分類</span><select id="category"><option value="">全部分類</option>{category_options}</select></label>
<label><span class="muted">狀態</span><select id="status"><option value="">全部狀態</option><option value="enabled">AIPS 可用</option><option value="integrated">已合併</option><option value="adopted">已採納</option><option value="optional">選用</option><option value="workflow">流程整合</option><option value="deferred">延後</option><option value="reference">來源參考</option><option value="excluded">Beta 排除</option><option value="not-adopted">不導入</option></select></label>
</div><p id="results" aria-live="polite"></p>
</header>
<main><div class="grid" id="cards">
{cards}
</div></main>
<footer>
<p>此頁由 scripts/skill_catalog.py 從 skills/INDEX.yaml 與來源處置清單產生。AIPS Skill 的路由資料以 canonical SKILL.md / Registry 為準。</p>
<p>上游來源：mattpocock/skills · commit {source_sha} · MIT License。Writing Fragments → Beats → Shape 僅依明確要求使用。</p>
</footer>
<script>
const search=document.getElementById("search"), category=document.getElementById("category"), status=document.getElementById("status");
const cards=[...document.querySelectorAll(".card")], results=document.getElementById("results");
function filterCards(){{
 const q=search.value.trim().toLocaleLowerCase();
 let shown=0;
 for(const card of cards){{
  const matchText=!q||card.dataset.search.toLocaleLowerCase().includes(q);
  const matchCategory=!category.value||card.dataset.category===category.value;
  const matchStatus=!status.value||card.dataset.status===status.value;
  card.hidden=!(matchText&&matchCategory&&matchStatus);
  if(!card.hidden)shown++;
 }}
 results.textContent="顯示 "+shown+" / "+cards.length+" 個 Skills";
}}
for(const control of [search,category,status])control.addEventListener("input",filterCards);
for(const control of [category,status])control.addEventListener("change",filterCards);
document.addEventListener("click",async event=>{{
 const button=event.target.closest(".copy");
 if(!button)return;
 try{{await navigator.clipboard.writeText(button.dataset.prompt);button.textContent="已複製";setTimeout(()=>button.textContent="複製範例",1200);}}
 catch{{window.prompt("複製以下範例",button.dataset.prompt);}}
}});
filterCards();
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated HTML without writing")
    args = parser.parse_args()
    try:
        expected = render()
        if args.check:
            if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
                raise ValueError("Skill Explorer drift; run python scripts/skill_catalog.py")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_text(expected, encoding="utf-8")
    except (OSError, ValueError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print("Skill catalog PASS" if args.check else f"Skill catalog generated: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
