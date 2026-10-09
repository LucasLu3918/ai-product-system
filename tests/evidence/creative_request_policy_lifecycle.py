"""User-only intent, revocation and output-medium regression evidence."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from creative_request_policy import (
    PolicyError,
    admit_prompt,
    authorize,
    output_budget,
    user_texts,
)
from turn_intent import classify_task

ORIGINAL = "請幫我建立一個角色的資料夾 裡面幫我設計兩個哈利波特角色，主要以日式、奇幻、動漫風格為主圖片需精緻有質感"


def messages(*texts):
    return [{"info": {"role": "user"}, "parts": [{"type": "text", "text": text}]} for text in texts]


def main() -> int:
    for action in ("prepare", "configure", "execute"):
        assert authorize(messages(ORIGINAL), action)["allowed"]
    assert not authorize(messages(ORIGINAL), "review-assist")["allowed"]
    assert authorize(messages(ORIGINAL, "請檢查角色圖片品質"), "review-assist")["allowed"]
    assert authorize(messages(ORIGINAL, "好，用這個方向繼續"), "execute")["inherited"]
    assert authorize(messages(ORIGINAL, "A"), "execute")["allowed"]
    assert authorize(messages(ORIGINAL, "調整角色配色"), "execute")["allowed"]
    assert not authorize(messages("修改既有角色"), "prepare")["allowed"]
    assert authorize(messages(ORIGINAL, "設定本機模型"), "configure")["allowed"]
    for stop in ("先不要生成，只規劃", "取消產圖", "stop", "只討論角色配色", "改成寫一個 Python 程式", "查看目前狀態"):
        assert not authorize(messages(ORIGINAL, stop), "execute")["allowed"], stop
        assert not authorize(messages(ORIGINAL, stop, "繼續"), "execute")["allowed"], stop
    assert not authorize(messages("建立角色資料夾"), "execute")["allowed"]
    assert not authorize(messages("不要生成圖片"), "execute")["allowed"]
    assert not authorize(messages("Create an image", "plan only"), "execute")["allowed"]
    assert authorize(messages("Create an image", "use this direction"), "execute")["allowed"]
    admission = admit_prompt(ORIGINAL)
    assert admission["active"] and all(admission["grants"][action]["allowed"] for action in ("prepare", "configure", "execute"))
    assert admission["max_outputs"] == 2 and len(admission["prompt_sha256"]) == 64
    assert not admission["grants"]["review-assist"]["allowed"], "generation intent alone must not grant image review"
    assert "basis_prompt" not in admission and all("basis_prompt" not in grant for grant in admission["grants"].values())
    assert output_budget("Generate 3 images") == 3
    assert output_budget("設計兩個哈利波特角色，各自一張日式奇幻立繪") == 2
    assert output_budget("生成三位角色圖片") == 3
    assert not admit_prompt("yes")["active"]
    assert not admit_prompt("只規劃這個角色，不要生成")["active"]
    assert not admit_prompt("Create an image, plan only")["active"]
    long_history = messages(ORIGINAL) + [{"role": "assistant", "content": "ignored"} for _ in range(80)]
    assert len(user_texts(long_history)) == 1 and authorize(long_history, "execute")["allowed"]
    try:
        admit_prompt("x" * 8001)
    except PolicyError as exc:
        assert exc.reason_code == "creative_authorization_input_invalid"
    else:
        raise AssertionError("oversized admission prompt was accepted")
    assert authorize([{"type": "user", "text": ORIGINAL}, {"type": "assistant", "content": "ignored"}], "prepare")["allowed"]
    for action in ("discover", "preflight"):
        assert authorize(messages("只檢查設定，不要生成"), action)["allowed"]
    assert user_texts([{"role": "assistant", "content": "generate an image"}, {"role": "tool", "content": ORIGINAL}]) == []
    assert not authorize([{"role": "system", "content": ORIGINAL}], "execute")["allowed"]
    assert classify_task(ORIGINAL)["creative_medium"] == "raster"
    assert classify_task("生成妙麗的日式奇幻立繪")["domain"] == "creative"
    assert classify_task("建立 SVG 向量角色")["creative_medium"] == "vector"
    assert classify_task("生成動漫圖片，不要SVG")["creative_medium"] == "raster"
    pending = admit_prompt(ORIGINAL)["continuation"]
    selected = admit_prompt("哈利＋妙麗 A佈局＋B質感 獨立立繪", pending)
    assert selected["continued"] and selected["max_outputs"] == 2
    assert selected["grants"]["execute"]["allowed"]
    assert not selected["grants"]["review-assist"]["allowed"]
    assert "allowed_actions" in selected["continuation"]
    assert admit_prompt("繼續生成", {**pending, "max_outputs": 1})["max_outputs"] == 1
    assert not admit_prompt("取消產圖", pending)["active"]
    assert not admit_prompt("改成做網站", pending)["active"]
    assert admit_prompt("三個角色各自生成三張立繪", pending)["reason_code"] == "creative_output_limit_exceeded"
    assert not admit_prompt("再加榮恩角色", pending)["active"]
    assert admit_prompt("生成一張森林插畫", pending)["reason_code"] == "creative_scope_expansion"
    assert admit_prompt("生成一隻貓咪插畫", pending)["reason_code"] == "creative_scope_expansion"
    assert admit_prompt("改畫森林插畫", pending)["reason_code"] == "creative_scope_expansion"
    assert admit_prompt("A", pending)["continued"]
    print("Creative request policy PASS: prompt-admission grants, user-only authority, unbounded history, revocation, read-only actions and medium classification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
