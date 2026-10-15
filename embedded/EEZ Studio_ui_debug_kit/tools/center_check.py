#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""center_check.py —— 「元素在父对象里居中」静态检查（内核版）

把 cases/B9 的判据固化成可执行检查：**声明已经在的数，验证它到底居中没有。**

判据
----
只对「父容器**只有一个子对象**」的节点生效 —— 这正是"子元素应永远待在父正中"的意图集合
（图标方块 / 圆形按钮里的图标 / 徽标…）。
行内那种「图标 + 文字」的前置图标不在本集合：它们本就按固定 x 摆放，不是居中关系。

    左间隙 ≈ 右间隙，上间隙 ≈ 下间隙，各自相差 ≤ tol（默认 1px）

**这 1px 不是 bug**，是取整的固有代价：奇偶尺寸相减会落到 .5，
生成侧与宿主侧的舍入模式（half-even / half-up）必然产生 1px 差 —— 详见 cases/B9。

输入
----
任意"组件树 JSON"（与框架解耦），自动识别三种形状：

    {"pages": [{"name":..., "screen": {…}}, …]}     # 带页面的工程（默认）
    {…}                                             # 单棵树
    [{…}, {…}]                                      # 节点列表

节点里的键名全部可用参数覆盖（默认对齐常见写法），不依赖任何配置、只用标准库。

用法
----
    python center_check.py --tree <树.json>
    python center_check.py --tree tree.json --all           # 不限图标，查所有独子
    python center_check.py --tree tree.json --tol 0         # 严格判等
    python center_check.py --tree tree.json --json          # 机器可读输出
    python center_check.py --tree tree.json --strict-size   # 有节点缺内容尺寸也算失败

退出码：0 = 全部居中；1 = 有偏移（或 --strict-size 下有未知尺寸）；2 = 输入错误。
"""
import argparse
import json
import sys


def num(node, key, default=0):
    v = node.get(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def load_roots(path, pages_key):
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        sys.stderr.write("!! 读树失败: %s\n" % e)
        sys.exit(2)
    roots = []
    if isinstance(doc, dict) and pages_key in doc:
        for pg in doc[pages_key] or []:
            roots.append((pg.get("name", "?"), pg.get("screen") or pg))
    elif isinstance(doc, dict):
        roots.append(("<root>", doc))
    elif isinstance(doc, list):
        for i, n in enumerate(doc):
            roots.append((str(i), n))
    else:
        sys.stderr.write("!! 不认识的树形状\n")
        sys.exit(2)
    return [r for r in roots if isinstance(r[1], dict)]


def iter_tree(node, children_key):
    yield node
    for c in node.get(children_key) or []:
        if isinstance(c, dict):
            for x in iter_tree(c, children_key):
                yield x


def main():
    ap = argparse.ArgumentParser(description="「元素在父对象里居中」静态检查")
    ap.add_argument("--tree", required=True, help="组件树 JSON 路径")
    ap.add_argument("--pages-key", default="pages")
    ap.add_argument("--children-key", default="children")
    ap.add_argument("--id-key", default="id")
    ap.add_argument("--x-key", default="x")
    ap.add_argument("--y-key", default="y")
    ap.add_argument("--w-key", default="w")
    ap.add_argument("--h-key", default="h")
    ap.add_argument("--icon-key", default="_icon",
                    help="标记「此节点是图标」的键（默认 _icon）")
    ap.add_argument("--all", dest="check_all", action="store_true",
                    help="不限图标，检查所有『父容器唯一子对象』")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="左右/上下间隙允许相差多少 px（默认 1，取整固有代价）")
    ap.add_argument("--strict-size", action="store_true",
                    help="子对象缺内容尺寸（无法判定）时也判失败")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()

    K = {"children": a.children_key, "id": a.id_key,
         "x": a.x_key, "y": a.y_key, "w": a.w_key, "h": a.h_key}

    roots = load_roots(a.tree, a.pages_key)
    rows, nbad, nunk = [], 0, 0

    for page, root in roots:
        for node in iter_tree(root, K["children"]):
            kids = [c for c in (node.get(K["children"]) or []) if isinstance(c, dict)]
            if len(kids) != 1:
                continue
            ch = kids[0]
            if not a.check_all and a.icon_key and not ch.get(a.icon_key):
                continue

            pid = node.get(K["id"], "?")
            cid = ch.get(K["id"], "?")
            pw, ph = num(node, K["w"]), num(node, K["h"])
            cw, chh = num(ch, K["w"]), num(ch, K["h"])

            if not cw or not chh:
                nunk += 1
                rows.append({"page": page, "parent": pid, "child": cid,
                             "status": "unknown",
                             "note": "子节点缺内容尺寸（是不是没把真实宽高写回来？）"})
                continue

            gl = num(ch, K["x"]) - num(node, K["x"])
            gt = num(ch, K["y"]) - num(node, K["y"])
            gr = pw - gl - cw
            gb = ph - gt - chh
            dx, dy = gl - gr, gt - gb
            ok = abs(dx) <= a.tol and abs(dy) <= a.tol
            if not ok:
                nbad += 1
            rows.append({"page": page, "parent": pid, "child": cid,
                         "parent_size": [pw, ph], "child_size": [cw, chh],
                         "gaps": [gl, gr, gt, gb], "dx": dx, "dy": dy,
                         "status": "ok" if ok else "off"})

    if a.as_json:
        print(json.dumps({"rows": rows, "off": nbad, "unknown": nunk},
                         ensure_ascii=False, indent=2))
    else:
        print("居中检查：%d 处（父容器唯一子对象），偏差容限 %.0fpx" % (len(rows), a.tol))
        print("-" * 96)
        for r in rows:
            if r["status"] == "unknown":
                print("??  %-12s 父 %-18s 子 %-20s %s"
                      % (r["page"], r["parent"], r["child"], r["note"]))
            else:
                gl, gr, gt, gb = r["gaps"]
                print("%s %-12s 父 %-18s 子 %-20s 父%dx%d 子%dx%d  左%3g 右%3g 上%3g 下%3g"
                      % ("OK" if r["status"] == "ok" else "偏", r["page"],
                         r["parent"], r["child"],
                         r["parent_size"][0], r["parent_size"][1],
                         r["child_size"][0], r["child_size"][1],
                         gl, gr, gt, gb))
        print("-" * 96)
        if nbad:
            print("!! %d 处未居中：%s" % (
                nbad, ", ".join("%s/%s" % (r["parent"], r["child"])
                                for r in rows if r["status"] == "off")))
        else:
            print("全部居中 ✓" + ("（另有 %d 处因缺内容尺寸未能判定）" % nunk if nunk else ""))

    if nbad:
        return 1
    if nunk and a.strict_size:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
