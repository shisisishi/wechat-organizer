"""组织器：处理截图OCR JSON -> 入库 + 逐条转写 + 群聊摘要。"""
import sys, os, json, re, glob, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.vision.parse_chat import parse_ocr_items
from app.store import db
from app.summary.summarize import summarize, render_markdown

HDR_RE = re.compile(r"(.+?)[（(]\d+[)）]\s*$")
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.json"

def load_config():
    try:
        return json.load(open(CONFIG_PATH, encoding="utf-8"))
    except Exception:
        return {}

def guess_group(items):
    for it in items:
        if it.get("cy", 999) < 80 and it.get("cx", 0) >= 200:
            t = (it.get("text") or "").strip()
            m = HDR_RE.match(t)
            if m: return m.group(1).strip()
            if t and len(t) < 20: return t
    return "未知群"

def process_ocr_file(path, cfg):
    raw = json.load(open(path, encoding="utf-8"))
    items = raw.get("items", [])
    group = guess_group(items)
    gmap = cfg.get("group_name_map", {})
    group = gmap.get(group, group)  # 别名纠错
    msgs = parse_ocr_items(items)
    for m in msgs: m["group"] = group
    return group, msgs, raw

def render_transcript(messages):
    lines = ["# 群聊转写", ""]
    for m in messages:
        ts = m.get("ts") or ""
        lines.append(f"- {ts}  **{m.get('sender') or '未知'}**：{m.get('body')}")
    lines.append("")
    return "\n".join(lines)

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data")
    ap.add_argument("--pattern", default="ocr_live.json")
    ap.add_argument("--out", default=None, help="摘要输出路径(不含扩展名)")
    args = ap.parse_args()
    cfg = load_config()
    files = sorted(glob.glob(os.path.join(args.dir, args.pattern)))
    print(f"[organizer] 找到 {len(files)} 张截图OCR")
    all_msgs = []; groups = []
    for f in files:
        g, msgs, raw = process_ocr_file(f, cfg)
        groups.append(g); all_msgs.extend(msgs)
        db.add_capture(g, f, json.dumps(raw, ensure_ascii=False))
    seen = set(); merged = []
    for m in all_msgs:
        key = (m.get("sender"), m.get("body"), m.get("ts"))
        if key in seen: continue
        seen.add(key); merged.append(m)
    primary_group = groups[0] if groups else "未知群"
    captured_at = datetime.datetime.now().isoformat(timespec="seconds")
    added = db.add_messages([{"sender":m.get("sender"),"body":m.get("body"),"ts":m.get("ts")} for m in merged],
                            primary_group, captured_at, os.path.basename(files[0]) if files else "")
    print(f"[organizer] 群={primary_group} 解析消息={len(merged)} 新增入库={added} 累计={len(db.query_messages(primary_group))}")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = args.out or os.path.join("data", f"group_{primary_group}_{ts}")
    base = str(stem).replace(".md", "")
    trans_path = base + "_transcript.md"
    summ_path  = base + "_summary.md"
    Path(trans_path).write_text(render_transcript(merged), encoding="utf-8")
    s = summarize(merged, primary_group)
    Path(summ_path).write_text(render_markdown(s, captured_at), encoding="utf-8")
    print("[organizer] 转写:", trans_path)
    print("[organizer] 摘要:", summ_path)
    print("===== 摘要预览 =====")
    print(render_markdown(s, captured_at))

if __name__ == "__main__":
    main()
