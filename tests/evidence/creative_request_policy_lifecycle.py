"""User-only intent, revocation and output-medium regression evidence."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from creative_request_policy import authorize, user_texts
from turn_intent import classify_task

ORIGINAL = "請幫我建立一個角色的資料夾 裡面幫我設計兩個哈利波特角色，主要以日式、奇幻、動漫風格為主圖片需精緻有質感"


def messages(*texts):
    return [{"info": {"role": "user"}, "parts": [{"type": "text", "text": text}]} for text in texts]


def main() -> int:
    for action in ("prepare", "configure", "execute"):
        assert authorize(messages(ORIGINAL), action)["allowed"]
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
    assert authorize([{"type": "user", "text": ORIGINAL}, {"type": "assistant", "content": "ignored"}], "prepare")["allowed"]
    for action in ("discover", "preflight"):
        assert authorize(messages("只檢查設定，不要生成"), action)["allowed"]
    assert user_texts([{"role": "assistant", "content": "generate an image"}, {"role": "tool", "content": ORIGINAL}]) == []
    assert not authorize([{"role": "system", "content": ORIGINAL}], "execute")["allowed"]
    assert classify_task(ORIGINAL)["creative_medium"] == "raster"
    assert classify_task("建立 SVG 向量角色")["creative_medium"] == "vector"
    assert classify_task("生成動漫圖片，不要SVG")["creative_medium"] == "raster"
    print("Creative request policy PASS: original prompt, user-only authority, bounded continuation, revocation, read-only actions and medium classification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
