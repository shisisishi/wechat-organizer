"""群聊消息摘要生成器：活跃成员、关键词/话题、链接、@我、高信息量句子。"""
import re, json, collections, datetime
from pathlib import Path
import jieba

STOPWORDS = set("""的 了 是 我 你 他 她 它 们 这 那 就 也 都 和 与 或 但 而 在 有 不 没 很 还 把 被 让 给 对 从 到 跟 嘛 吧 呢 啊 呀 哦 哈 嗯 啥 么 这 样 一 个 中 上 下 为 于 之 其 并 且 等 又 再 怎么 什么 为什么 哪个 哪里 谁 大家 大神 大佬 请问 一下 好的 收到 嗯嗯 哈哈 哈哈哈 谢谢 谢了 牛逼 牛 666 可以 行 ok OK 😂 emmm""".split())

URL_RE = re.compile(r"https?://\S+")
NUM_RE = re.compile(r"\d+(\.\d+)?")
AT_RE = re.compile(r"[@＠](\S{1,20})")

def tokenize(text):
    words = []
    for w in jieba.cut(text):
        w = w.strip()
        if not w: continue
        if len(w) == 1 and not w.isalnum(): continue
        if w.lower() in STOPWORDS: continue
        if w in STOPWORDS: continue
        words.append(w)
    return words

def summarize(messages, group_name="", top_k=15):
    """messages: list of {sender,body,ts,captured_at}"""
    bodies = [m.get("body") or "" for m in messages]
    senders = [m.get("sender") or "未知" for m in messages]

    # 活跃成员
    sender_count = collections.Counter(senders)
    top_members = sender_count.most_common(top_k)

    # 关键词
    wc = collections.Counter()
    for b in bodies:
        for w in tokenize(b):
            wc[w] += 1
    # 过滤纯数字串过长的噪音
    kw = [(w, c) for w, c in wc.most_common(60) if not (w.isdigit() and len(w) > 4)]
    top_kw = kw[:top_k]

    # 链接
    links = []
    for b in bodies:
        links += URL_RE.findall(b)
    # @我 / @提及
    ats = []
    for b in bodies:
        ats += AT_RE.findall(b)

    # 高信息量消息 (含链接 / 数字 / 较长)
    info = []
    for m in messages:
        b = m.get("body") or ""
        if not b: continue
        score = 0
        if URL_RE.search(b): score += 3
        if NUM_RE.search(b): score += 1
        if len(b) >= 20: score += 2
        if score >= 2:
            info.append({"sender": m.get("sender"), "body": b, "ts": m.get("ts")})
    info.sort(key=lambda x: -(len(x["body"])))
    info = info[:15]

    total = len(messages)
    return {
        "group": group_name,
        "total_messages": total,
        "active_members": top_members,
        "top_keywords": top_kw,
        "links": list(dict.fromkeys(links))[:20],
        "mentions": list(dict.fromkeys(ats))[:20],
        "highlights": info,
    }

def render_markdown(summary, capture_time=""):
    g = summary["group"]
    lines = []
    lines.append(f"# 群聊整理：{g or '未知群'}  ")
    if capture_time:
        lines.append(f"> 抓取时间：{capture_time}  ")
    lines.append("")
    lines.append(f"**消息数**：{summary['total_messages']}  ")
    lines.append("")
    lines.append("## 活跃成员 TOP  ")
    for name, cnt in summary["active_members"]:
        lines.append(f"- **{name}** ：{cnt} 条")
    lines.append("")
    lines.append("## 关键词 / 话题  ")
    if summary["top_keywords"]:
        lines.append("、".join([f"{w}({c})" for w, c in summary["top_keywords"]]))
        lines.append("")
    lines.append("## 链接  ")
    if summary["links"]:
        for l in summary["links"]:
            lines.append(f"- {l}")
    else:
        lines.append("- （无）")
    lines.append("")
    lines.append("## @提及  ")
    if summary["mentions"]:
        lines.append("、" .join(summary["mentions"]))
    else:
        lines.append("- （无）")
    lines.append("")
    lines.append("## 高信息量消息  ")
    if summary["highlights"]:
        for it in summary["highlights"]:
            lines.append(f"- **{it['sender']}**：{it['body']}")
    else:
        lines.append("- （无）")
    lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    msgs = json.load(open("data/_msgs.json", encoding="utf-8")) if Path("data/_msgs.json").exists() else []
    if msgs:
        s = summarize(msgs, "测试群")
        print(render_markdown(s))
    else:
        print("no _msgs.json")
