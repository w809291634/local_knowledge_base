#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""log_entry.py —— 把『新问题』与『提示词』一致地写进本工具箱。

为什么要有它：本技能要求「任何 AI 工具」都能把开发中遇到的新问题、以及用户与 AI 的
提示词，追加进工具箱以便日后追查。固定格式靠手写容易漂移，所以提供一个只用**标准库**
的 CLI：能跑命令的 AI/人直接调用；不能跑的，按 `INTAKE.md` 里的手写格式追加即可。

用法:
  python tools/log_entry.py prompt  "用户的原始提示词" [--tool WorkBuddy] [--ask 诉求] [--out 产出] [--link P-0001] [--time "2026-09-23 14:16"]
  python tools/log_entry.py problem --title "标题" [--project 工程] [--tool 工具] [--tags a,b] [--status open|fixed|wontfix]
                                    [--symptom ..] [--repro ..] [--root ..] [--fix ..] [--evidence ..] [--sink ..] [--link PR-0001]
  python tools/log_entry.py list [problem|prompt]
  python tools/log_entry.py next-id [problem|prompt]

产出（均在本工具箱内，与具体工程解耦）:
  intake/P-####_<slug>.md   每个新问题一个文件
  intake/index.md           问题总表（自动追加一行）
  prompts/PROMPT_LOG.md     提示词日志（只追加）
"""
import argparse
import datetime
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
INTAKE = os.path.join(KIT, "intake")
PROMPTS = os.path.join(KIT, "prompts")
PLOG = os.path.join(PROMPTS, "PROMPT_LOG.md")
PINDEX = os.path.join(INTAKE, "index.md")

PLOG_HEAD = (
    "# 提示词日志（PROMPT_LOG）\n\n"
    "> 追加式：**只往后加，不改历史**。每条对应「用户 → AI」的一次输入，\n"
    "> 用于日后追查「当时为什么要改这个」。写入方式见 `../INTAKE.md`。\n"
    "> 格式由 `tools/log_entry.py prompt` 生成；手写请照抄同一格式。\n\n---\n\n")

PINDEX_HEAD = (
    "# 问题登记索引\n\n"
    "> 每遇到一个新问题，追加一行 + 一个 `P-####_*.md`。写入方式见 `../INTAKE.md`。\n\n"
    "| 编号 | 日期 | 标题 | 标签 | 状态 |\n"
    "|---|---|---|---|---|\n")

PROBLEM_TMPL = """# {pid} · {title}

- **工程**：{project}
- **日期**：{date}
- **工具**：{tool}
- **状态**：{status}
- **标签**：{tags}
- **关联提示词**：{link}

## 现象（看到什么）

{symptom}

## 复现（怎么稳定重现）

{repro}

## 根因（真正的原因）

{root}

## 修复（做了什么）

{fix}

## 证据（数字 / 命令输出）

{evidence}

## 沉淀（新增断言 / 案例 / 文档）

{sink}
"""


def _ensure_dirs():
    for d in (INTAKE, PROMPTS):
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)


def _read(path):
    return io.open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _today():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def next_problem_id():
    mx = 0
    for n in (os.listdir(INTAKE) if os.path.isdir(INTAKE) else []):
        m = re.match(r"P-(\d{4})", n)
        if m:
            mx = max(mx, int(m.group(1)))
    return "P-%04d" % (mx + 1)


def next_prompt_id():
    mx = 0
    for m in re.finditer(r"PR-(\d{4})", _read(PLOG)):
        mx = max(mx, int(m.group(1)))
    return "PR-%04d" % (mx + 1)


def _slug(title):
    s = re.sub(r"[\\/:*?\"<>|\s]+", "_", (title or "entry").strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "entry")[:48]


def _field(label, text, indent="  "):
    """多行文本做成一段：首行接标签，后续行同缩进对齐。空值给占位提示。"""
    text = (text or "").strip()
    if not text:
        return "%s- %s：（待补）" % (indent, label)
    lines = [ln.rstrip() for ln in text.splitlines()]
    out = ["%s- %s：%s" % (indent, label, lines[0].strip())]
    for ln in lines[1:]:
        out.append("%s  %s" % (indent, ln))
    return "\n".join(out)


def _section(text):
    """问题文件里的正文段：空值给占位提示。"""
    text = (text or "").strip()
    return text if text else "（待补）"


def append_prompt(text, tool=None, ask=None, out=None, link=None, when=None):
    _ensure_dirs()
    if not os.path.isfile(PLOG):
        io.open(PLOG, "w", encoding="utf-8").write(PLOG_HEAD)
    pid = next_prompt_id()
    block = [
        "### %s · %s · %s" % (pid, when or _now(), tool or "未知工具"),
        _field("提示词", text),
        _field("诉求", ask),
        _field("产出/结论", out),
        _field("关联", link),
        "",
    ]
    with io.open(PLOG, "a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")
    return pid


def create_problem(title, project=None, tool=None, tags=None, status="open",
                   symptom=None, repro=None, root=None, fix=None,
                   evidence=None, sink=None, link=None):
    _ensure_dirs()
    pid = next_problem_id()
    date = _today()
    tags = tags or ""
    body = PROBLEM_TMPL.format(
        pid=pid, title=title, project=project or "（待补）", date=date,
        tool=tool or "未知工具", status=status, tags=tags or "（无）",
        link=link or "（无）", symptom=_section(symptom), repro=_section(repro),
        root=_section(root), fix=_section(fix), evidence=_section(evidence),
        sink=_section(sink))
    path = os.path.join(INTAKE, "%s_%s.md" % (pid, _slug(title)))
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(body)
    if not os.path.isfile(PINDEX):
        io.open(PINDEX, "w", encoding="utf-8").write(PINDEX_HEAD)
    with io.open(PINDEX, "a", encoding="utf-8") as f:
        f.write("| %s | %s | %s | %s | %s |\n" % (pid, date, title, tags or "-", status))
    return pid, path


def do_list(what):
    _ensure_dirs()
    if what in ("problem", "all", None):
        print("== 问题（intake/）==")
        print(_read(PINDEX).strip() or "（暂无）")
    if what in ("prompt", "all", None):
        txt = _read(PLOG)
        ids = re.findall(r"^### (PR-\d{4}) · (.+?) · (.+)$", txt, re.M)
        print("\n== 提示词（prompts/）%d 条 ==" % len(ids))
        for pid, when, tool in ids:
            print("  %s  %s  %s" % (pid, when, tool))


def main():
    ap = argparse.ArgumentParser(description="把新问题 / 提示词写进 ui_debug_kit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("prompt", help="追加一条提示词")
    pp.add_argument("text", help="用户原始提示词（逐字抄，不要改写）")
    pp.add_argument("--tool", default=None, help="AI 工具名，如 WorkBuddy / Cursor / ChatGPT")
    pp.add_argument("--ask", default=None, help="用户想达成什么")
    pp.add_argument("--out", default=None, help="本轮产出/结论")
    pp.add_argument("--link", default=None, help="关联问题编号，如 P-0002")
    pp.add_argument("--time", default=None, help="时间，默认当前（补录用 '2026-09-23（补录）'）")

    pr = sub.add_parser("problem", help="登记一个新问题")
    pr.add_argument("--title", required=True)
    pr.add_argument("--project", default=None)
    pr.add_argument("--tool", default=None)
    pr.add_argument("--tags", default=None, help="逗号分隔")
    pr.add_argument("--status", default="open", choices=["open", "fixed", "wontfix"])
    pr.add_argument("--symptom", default=None)
    pr.add_argument("--repro", default=None)
    pr.add_argument("--root", default=None, help="根因")
    pr.add_argument("--fix", default=None)
    pr.add_argument("--evidence", default=None)
    pr.add_argument("--sink", default=None, help="沉淀：新增断言/案例/文档")
    pr.add_argument("--link", default=None, help="关联提示词，如 PR-0007")

    ls = sub.add_parser("list", help="列出已有登记")
    ls.add_argument("what", nargs="?", choices=["problem", "prompt", "all"], default="all")

    ni = sub.add_parser("next-id", help="打印下一个编号")
    ni.add_argument("what", nargs="?", choices=["problem", "prompt"], default="problem")

    args = ap.parse_args()

    if args.cmd == "prompt":
        pid = append_prompt(args.text, args.tool, args.ask, args.out, args.link, args.time)
        print("%s 已追加到 prompts/PROMPT_LOG.md" % pid)
    elif args.cmd == "problem":
        pid, path = create_problem(args.title, args.project, args.tool, args.tags,
                                   args.status, args.symptom, args.repro, args.root,
                                   args.fix, args.evidence, args.sink, args.link)
        print("%s 已创建 intake/%s" % (pid, os.path.basename(path)))
    elif args.cmd == "list":
        do_list(args.what)
    elif args.cmd == "next-id":
        print(next_problem_id() if args.what == "problem" else next_prompt_id())
    return 0


if __name__ == "__main__":
    sys.exit(main())
