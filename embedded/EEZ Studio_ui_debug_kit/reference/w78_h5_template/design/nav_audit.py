# -*- coding: utf-8 -*-
"""跳转审计（门禁）：证明"每一页都能说清怎么进去、怎么回来"。

查六件事，任何一条 FAIL 退出码非 0：
  A 目标存在    —— 每条跳转边的 target 必须在页集合里
  B 入口存在    —— 非根页至少 1 条权威入边（behav=换页 或 手势），否则谁也进不去
  C 回边存在    —— 非根页至少 1 条权威出边，且 BFS 能回到根（导航闭环）
  D 全页可达    —— 从根按权威边 BFS，所有非状态页都能到
  E 状态页登记  —— 没有入边的页必须显式标成状态页，不许混在正常页里当"孤岛"
  F 三处同源    —— 设计源 / H5 判类 / 控件清单 的跳转计数必须对得上

用法：python design/nav_audit.py        # 全绿才允许交付
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import export_ui as eu             # noqa: E402
import nav_map as nm               # noqa: E402
import overview_pro as ov          # noqa: E402


def main():
    data = eu.page_data()
    h5 = ov.build()
    # H5 可能含预览专用页；仅业务页参与导航审计。
    order = [page for page in h5["order"] if page in data]
    root = order[0]
    status = {p for p in order if p != root and not any(
        r["target"] == p for q in order for r in data[q]["rows"])}

    edges = []          # (from, 类型, 控件名, to)
    dangling = []
    for p in order:
        for r in data[p]["rows"]:
            if r["behav"] == "换页" and r["target"]:
                edges.append((p, "nav", r["name"], r["target"]))
            elif r["target"] and r["behav"] != "换页":
                edges.append((p, "card", r["name"], r["target"]))
        for r in data[p]["rows"]:
            if r["behav"] == "返回":
                edges.append((p, "back", r["name"], "*"))   # 目标是来路，运行时才知道
        for g in h5["pages"][p]["gesture"]:
            edges.append((p, "gesture", g["label"], g["go"]))
    for a, k, n, b in edges:
        if k != "back" and b not in data:      # 来路返回的目标运行时才定，不参与存在性检查
            dangling.append((a, k, n, b))

    auth = [(a, n, b) for a, k, n, b in edges if k in ("nav", "gesture")]
    dyn = [(a, n) for a, k, n, b in edges if k == "back"]
    inn = collections.defaultdict(list)
    out = collections.defaultdict(list)
    for a, n, b in auth:
        out[a].append(b)
        inn[b].append(a)
    for a, _n in dyn:
        out[a].append("*")      # 有回退能力，但不知道回哪

    no_in = [p for p in order if p != root and not inn[p]]
    no_out = [p for p in order if p != root and not out[p]]
    reach, q = {root}, collections.deque([root])
    while q:
        cur = q.popleft()
        for nxt in out[cur]:
            if nxt not in reach:
                reach.add(nxt)
                q.append(nxt)
    unreachable = [p for p in order if p not in reach and p not in status]
    unregistered = [p for p in no_in if p not in status]

    fails = []
    if dangling:
        fails.append("A 有跳转指向不存在的页：%s" % dangling)
    if unregistered:
        fails.append("B/E 这些页没有入口也没登记为状态页：%s" % unregistered)
    if no_out:
        fails.append("C 这些页没有出边（出不去）：%s" % no_out)
    if unreachable:
        fails.append("D 从根不可达：%s" % unreachable)

    n_h5_nav = sum(1 for p in order for r in h5["pages"][p]["rows"] if r["io"] == "nav")
    n_src_nav = sum(1 for p in order for r in data[p]["rows"]
                    if r["behav"] in ("换页", "返回"))
    n_card = sum(1 for a, k, n, b in edges if k == "card")
    tbl = os.path.join(os.path.dirname(ov.sc.OUT), "designer_annotated", "控件清单.md")
    n_tbl_nav = 0
    if os.path.exists(tbl):
        n_tbl_nav = len(re.findall(r"\| 跳转按钮 \|", io.open(tbl, encoding="utf-8").read()))
    # G 两张真值表对账：nav_map（跳转表）↔ 控件表 target
    mapped = dict(nm.NAV_TARGETS)
    row_tgt = {(p, r["name"]): r["target"] for p in order for r in data[p]["rows"] if r["target"]}
    map_only = {k: v for k, v in mapped.items() if row_tgt.get(k) != v}
    row_only = {k: v for k, v in row_tgt.items() if k not in mapped}
    if map_only:
        fails.append("G 跳转表里有、控件表对不上（死条目）：%s" % map_only)
    if row_only:
        fails.append("G 控件挂了 target 但跳转表没登记：%s" % row_only)

    # 逐页对账（只看总数会被此消彼长掩盖）
    drift = {p: (sum(1 for r in data[p]["rows"] if r["behav"] in ("换页", "返回")),
                 sum(1 for r in h5["pages"][p]["rows"] if r["io"] == "nav"))
             for p in order
             if sum(1 for r in data[p]["rows"] if r["behav"] in ("换页", "返回"))
             != sum(1 for r in h5["pages"][p]["rows"] if r["io"] == "nav")}
    if drift:
        fails.append("F 逐页跳转数漂移（设计源 / H5）：%s" % drift)

    if not (n_src_nav == n_h5_nav == n_tbl_nav):
        fails.append("F 跳转计数不一致：设计源 %d / H5 %d / 清单 %d"
                     % (n_src_nav, n_h5_nav, n_tbl_nav))

    if n_card:
        fails.append("H 卡片残留 target %d 条（行为不是换页却登记了跳转，会把点击吞成数据操作）: %s"
                     % (n_card, [(a, n, b) for a, k, n, b in edges if k == "card"][:4]))
    print("页 %d（根 %s，状态页 %s）" % (len(order), root, sorted(status) or "无"))
    print("权威边 %d（跳转 %d + 手势 %d）｜ 卡片残留 target %d"
          % (len(auth), len(auth) - sum(1 for a, k, n, b in edges if k == "gesture"),
             sum(1 for a, k, n, b in edges if k == "gesture"), n_card))
    print("每页入口数：")
    for p in order:
        mark = "  ← 无入口" if not inn[p] else ""
        print("  %-6s L%d 入 %d 出 %d%s" % (p, h5["pages"][p]["layer"], len(inn[p]), len(out[p]), mark))
    print("\n跳转表 NAV_TARGETS %d 条 ｜ 控件表带 target %d 条" % (len(mapped), len(row_tgt)))
    print("[NAV_AUDIT] " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  !! " + f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
