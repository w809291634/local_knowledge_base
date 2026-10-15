# -*- coding: utf-8 -*-
"""
gen_clicks.py —— 从设计源自动生成 L2 真点击用例

为什么不手写 clicks.txt：手写只能覆盖记得住的几条，改一次 UI 就失效。
这个脚本从设计源直接推导，**每个可达按钮都被点到**：

  1. 每个可达页面的每个跳转按钮（含导航路径：先走回该页再点）
  2. 底栏「点当前项」回归项（修复前会切到自己，表现为闪屏）
  3. 不可达页面会明确列出，提示「这些屏还没配入口」

底栏识别规则来自配置 checks.tab_bar；
底栏各项对应的页名**自动推导**（扫全量页，收集各页底栏同索引按钮的 goto），
推导不出来时才提示去补 checks.tab_pages。

输出格式（供仿真器消费）：
    x  y  期望点击后所在页面

用法：
    python gen_clicks.py                        # 输出到 stdout
    python gen_clicks.py -o clicks.txt          # 写文件
    python gen_clicks.py --only Main,Settings   # 只生成指定页
"""
import argparse
import io
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
from audit_ui import sch, walk, num, tabbar_rule  # noqa: E402


def collect_buttons(root, page, s, out):
    """收集页面内所有可跳转控件，坐标换算成绝对坐标 + 中心点。"""
    nav_types = s["nav_types"]
    for ax, ay, n, _d in walk(root, s):
        if n.get(s["type"]) in nav_types and n.get(s["goto"]):
            out.append({"page": page,
                        "cx": ax + num(n, s["w"]) // 2,
                        "cy": ay + num(n, s["h"]) // 2,
                        "goto": n[s["goto"]],
                        "label": _label(n, s)})


def _label(n, s):
    """控件的可读标识：取子树里第一个文字。"""
    def first_text(node):
        if not isinstance(node, dict):
            return None
        if node.get(s["text"]):
            return node[s["text"]]
        for c in (node.get(s["children"]) or []):
            r = first_text(c)
            if r:
                return r
        return None
    return first_text(n) or n.get(s["goto"]) or ""


def find_tabbar(root, s, rule):
    """找到底栏容器，返回 (绝对x, 绝对y, 节点)；没有返回 None。"""
    for ax, ay, n, _d in walk(root, s):
        if (n.get(s["type"]) == s["container"] and ay == rule["y"]
                and (not rule["h"] or num(n, s["h"]) == rule["h"])
                and (not rule["w"] or num(n, s["w"]) == rule["w"])):
            return (ax, ay, n)
    return None


def tab_buttons(tab, s):
    """底栏里的可点击项（**只取 nav_types**），按显示顺序。

    ⚠️ 底栏容器里常有非按钮的装饰（高亮条、分隔线），直接按 children 下标编号会错位。
    """
    return [c for c in (tab[2].get(s["children"]) or [])
            if isinstance(c, dict) and c.get(s["type"]) in s["nav_types"]]


def tab_slots(tab, s):
    """底栏各按钮的 (中心x, 中心y, goto)，**绝对坐标**（底栏位置 + 子控件相对偏移）。"""
    tx, ty = tab[0], tab[1]
    out = []
    for c in tab_buttons(tab, s):
        out.append((tx + num(c, s["x"]) + num(c, s["w"]) // 2,
                    ty + num(c, s["y"]) + num(c, s["h"]) // 2,
                    c.get(s["goto"])))
    return out


def tab_slot_map(pages, s, rule, fallback=None):
    """底栏槽位（以按钮中心 x 为键）-> 目标页名。

    ⚠️ 为什么不用 children 下标：底栏通常**不给当前页生成按钮**，各页的按钮数量不同，
    下标会整体错位。按钮的 x 位置在所有页里是固定的，用它当键才稳。

    做法：扫每一页的底栏，同一 x 的按钮若带 goto 就记下来（跨页互相补齐）；
    仍有空槽时用配置项 checks.tab_pages 按 x 从左到右补齐。
    """
    slot = {}
    xs = set()
    for name, root in pages:
        tab = find_tabbar(root, s, rule)
        if tab is None:
            continue
        for cx, _cy, g in tab_slots(tab, s):
            xs.add(cx)
            if g:
                slot.setdefault(cx, g)
    if fallback:
        for cx, p in zip(sorted(xs), fallback):
            slot.setdefault(cx, p)
    return slot


def _nav(path):
    """把"先导航回该页"的点击序列展开成行。"""
    return ["%3d %3d %s" % (x, y, dest) for x, y, dest in path]


def bfs_path(graph, src, dst):
    """src -> dst 的最短点击序列 [(cx, cy, dest), ...]；不可达返回 None。"""
    if src == dst:
        return []
    prev = {src: None}
    q = deque([src])
    while q:
        n = q.popleft()
        for cx, cy, dest in graph.get(n, []):
            if dest in prev:
                continue
            prev[dest] = (n, cx, cy)
            if dest == dst:
                path, cur = [], dst
                while cur != src:
                    p, x, y = prev[cur]
                    path.append((x, y, cur))
                    cur = p
                return list(reversed(path))
            q.append(dest)
    return None


def main():
    ap = argparse.ArgumentParser(description="从设计源生成真点击用例")
    ap.add_argument("-o", "--out", help="输出文件（默认 stdout）")
    ap.add_argument("--only", help="只生成这些页面，逗号分隔")
    ap.add_argument("--config", help="指定配置文件")
    args = ap.parse_args()

    cfg = kit.load_config(args.config)
    s = sch(cfg)
    pages = kit.load_pages(cfg)
    entry = (cfg.get("checks") or {}).get("entry_page") or (pages[0][0] if pages else "")
    only = set(args.only.split(",")) if args.only else None

    buttons = []
    for name, root in pages:
        if only and name not in only:
            continue
        collect_buttons(root, name, s, buttons)

    graph = {}
    for b in buttons:
        graph.setdefault(b["page"], []).append((b["cx"], b["cy"], b["goto"]))

    # 底栏回归项（规则与 A5 共用同一处解析：y<=0 视为未配置）
    rule = tabbar_rule(cfg)
    slot_map = {}
    if rule:
        slot_map = tab_slot_map(pages, s, rule,
                                (cfg.get("checks") or {}).get("tab_pages"))

    lines = ["# 自动生成 —— 由 ui_debug_kit/tools/gen_clicks.py 从设计源推导",
             "# 配置：%s" % cfg["_abs"]["_config_path"],
             "# 用法：<仿真器>/bin/main.exe <本文件>",
             "# 每行：  x  y  点击后期望所在页面",
             ""]

    tested, skipped = 0, []
    for name, root in pages:
        if only and name not in only:
            continue
        path = bfs_path(graph, entry, name)
        if path is None:
            skipped.append(name)
            continue
        pbtns = [b for b in buttons if b["page"] == name]
        if not pbtns:
            continue

        lines.append("# ---- %s（%d 个跳转按钮）----" % (name, len(pbtns)))
        for b in pbtns:
            for x, y, dest in path:                  # 先导航回该页
                lines.append("%3d %3d %s" % (x, y, dest))
            lines.append("%3d %3d %s      # 「%s」-> %s"
                         % (b["cx"], b["cy"], b["goto"], b["label"][:12], b["goto"]))
            tested += 1
        lines.append("")

        tab = find_tabbar(root, s, rule) if rule else None
        if tab:
            slots = tab_slots(tab, s)
            tab_cy = tab[1] + (num(tab[2], s["h"]) // 2 or rule["h"] // 2)
            own_x = set(x for x, _y, _g in slots)
            # 回归一：点「当前页那一项」应原地不动（修复前会切到自己，表现为闪屏）
            for x, y, _g in slots:
                if slot_map.get(x) == name:
                    lines.extend(_nav(path))
                    lines.append("%3d %3d %s      # 回归：点当前页底栏项应原地不动"
                                 % (x, y, name))
            # 回归二：本页底栏缺失的槽位（通常是"当前页那一项"没生成按钮），
            # 点下去必须留在原页 —— 若这里被别的内容压占，就会误跳到别的页。
            # 「点了画面来回跳」的第二个成因，就是这么抓出来的。
            for x in sorted(slot_map):
                if x in own_x:
                    continue
                lines.extend(_nav(path))
                lines.append("%3d %3d %s      # 回归：底栏空槽位点击不应跳转"
                             % (x, tab_cy, name))
        lines.append("")

    text = "\n".join(lines) + "\n"
    if args.out:
        io.open(args.out, "w", encoding="utf-8").write(text)
        print("已写入 %s：%d 行，覆盖 %d 个按钮" % (args.out, len(lines), tested))
    else:
        sys.stdout.write(text)

    if skipped:
        sys.stderr.write("\n[不可达] 以下 %d 屏从 %s 点不到，其按钮未生成用例：\n"
                         % (len(skipped), entry))
        for sname in skipped:
            sys.stderr.write("   - %s\n" % sname)
        sys.stderr.write("  修法：在设计源里给它们的入口卡片补 goto，再重跑本脚本。\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
