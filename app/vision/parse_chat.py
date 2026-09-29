"""将 OCR 文本块解析为结构化聊天消息(发送者/正文/时间)。"""
import re
TIME_RE = re.compile(r"^\s*(\d{1,2}:\d{2})\s*$")
SENT_PUNCT = set("。，！？、；：“”（）【】《》.,!?;:()[]\"'")
def looks_like_name(text, max_len=14):
    t = text.strip()
    if not t: return False
    if len(t) > max_len: return False
    if any(ch in SENT_PUNCT for ch in t): return False
    if len(t) >= 10 and not re.search(r"\s", t): return False
    return True

def parse_ocr_items(items, panel_x0=260, header_bottom=78, input_top=560,
                    sticker_x0=700, GAP=42):
    panel = [it for it in items if it["cx"] >= panel_x0 and header_bottom <= it["cy"] <= input_top]
    panel.sort(key=lambda it: (it["cy"], it["cx"]))
    lines = []
    for it in panel:
        txt = (it.get("text") or "").strip()
        if not txt: continue
        m = TIME_RE.match(txt)
        if m:
            lines.append({"kind": "ts", "text": m.group(1), "cy": it["cy"], "cx": it["cx"]})
        elif it["cx"] >= sticker_x0:
            lines.append({"kind": "sticker", "text": "[贴纸/表情]", "cy": it["cy"], "cx": it["cx"]})
        else:
            lines.append({"kind": "text", "text": txt, "cy": it["cy"], "cx": it["cx"]})

    messages = []
    cur = None
    for ln in lines:
        if ln["kind"] == "ts":
            if cur is not None and not cur.get("ts"):
                cur["ts"] = ln["text"]
            continue
        if ln["kind"] == "sticker":
            if cur is not None:
                cur["body"] = (cur.get("body","") + " " + ln["text"]).strip()
            continue
        if cur is None:
            cur = {"sender": None, "body": "", "ts": None, "cy": ln["cy"]}
            if looks_like_name(ln["text"]):
                cur["sender"] = ln["text"]
            else:
                cur["body"] = ln["text"]
        else:
            dist = ln["cy"] - cur["cy"]
            if dist > GAP:
                messages.append(cur)
                cur = {"sender": None, "body": "", "ts": None, "cy": ln["cy"]}
                if looks_like_name(ln["text"]):
                    cur["sender"] = ln["text"]
                else:
                    cur["body"] = ln["text"]
            else:
                if not cur.get("sender") and looks_like_name(ln["text"]):
                    cur["sender"] = ln["text"]
                else:
                    cur["body"] = (cur.get("body","") + " " + ln["text"]).strip()
    if cur is not None:
        messages.append(cur)
    messages = [m for m in messages if (m.get("sender") or m.get("body"))]
    return messages

if __name__ == "__main__":
    import json
    raw = json.load(open("data/_ocr.json", encoding="utf-8"))
    msgs = parse_ocr_items(raw["items"])
    for m in msgs:
        print(f"{m.get('ts') or '':6} [{m.get('sender') or '?'}] {m.get('body')}")
