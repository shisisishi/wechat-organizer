# 群聊整理原型

这是一个**群聊截图 OCR 结果 → 结构化转写 + 摘要**的本地原型，不是完整微信机器人。

## 能做什么

- 读取示例 OCR JSON（`data/demo.json`）
- 解析发送者 / 正文
- 写入本地 SQLite（去重）
- 生成转写 Markdown 与群聊摘要 Markdown

## 不能做什么

- **没有连接真实微信**
- **没有自动回复**
- OCR 模块（`app/vision/ocr.py`）可对图片做识别，但**没有独立启动工作流**；本仓库公开副本以现成 OCR JSON 演示整理链路为主
- 不应把它当成可上线的微信助手

## 目录说明

```
app/
  organizer.py          # 入口：OCR JSON → 入库 + 转写 + 摘要
  vision/
    parse_chat.py       # OCR 文本块 → 消息结构
    ocr.py              # 可选：图片 OCR（需额外依赖，非演示必跑）
  store/
    db.py               # SQLite 存储与去重
  summary/
    summarize.py        # 活跃成员 / 关键词 / 链接 / 高信息量句
data/
  demo.json             # 虚构示例 OCR
  demo_transcript.md    # 示例转写结果
  demo_summary.md       # 示例摘要结果
```

## 依赖

- Python 3
- `jieba`（摘要分词）
- 可选：`rapidocr_onnxruntime`（仅在直接调用 `ocr.py` 识图时需要）

```bash
pip install jieba
```

## 用示例数据跑通整理流程

在项目根目录执行（`--pattern` 必须指向示例文件名；默认值是 `ocr_live.json`，本副本没有该文件）：

```bash
python app/organizer.py --dir data --pattern demo.json
```

预期控制台会打印：找到 1 份 OCR、解析消息数、入库新增数，以及转写 / 摘要路径；并在 `data/` 下生成带时间戳的 `*_transcript.md` 与 `*_summary.md`。本地还会生成 `data/wechat.db`（已在 `.gitignore` 中排除，请勿提交）。

可选参数：

- `--out 路径前缀`：指定输出文件名前缀（不含扩展名）

仅初始化 / 查看数据库（会打印库路径与已有群名）：

```bash
python app/store/db.py
```

## 示例数据说明

`data/demo.json` 等为**虚构**群名与发言（如「示例群」「示例甲」「示例乙」），用于演示解析与摘要，不是真实聊天记录。
