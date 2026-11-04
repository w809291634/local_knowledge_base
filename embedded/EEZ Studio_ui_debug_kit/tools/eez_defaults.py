#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EEZ 默认控件结构采集器（工程无关）。

从一批**能正常打开**的 .eez-project 里，按控件类型采出「默认字段结构」，
写成一个可被生成器复用的 JSON。生成新工程时用它做模板，只改几何/identifier/文本。

为什么需要它（2026-11-04 实测，PR-0473/0475）：
  凭印象拼控件字段会静默出错——EEZ 的按钮没有 text 字段（文字在子标签里），
  写错了不报错，只是整屏一个字都不显示。默认结构必须**取自真实工程**。

用法：
  python tools/eez_defaults.py --scan <目录> --out <默认结构.json>
  python tools/eez_defaults.py a.eez-project b.eez-project --out defaults.json

产物结构：
  { 类型名: {组件字段…（objID→"__OID__"，几何/文本/identifier 归零）}, ... }
  另加 "button_child": 按钮内部子标签的模板（若采到）。

采样规则：同类型取**字段签名最常见**的那个；`children` 里同型子控件单独提炼
（如 LVGLButtonWidget → button_child），父模板的 children 置空。
"""
import argparse
import collections
import glob
import io
import json
import os


def walk(comps):
    for c in comps:
        yield c
        for k in walk(c.get("children") or []):
            yield k


def blank(node, top=True):
    """把工程相关值清空，只留结构。"""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "objID":
                out[k] = "__OID__"
            elif k in ("identifier", "text"):
                out[k] = ""
            elif k in ("left", "top", "width", "height"):
                out[k] = 0
            elif k == "eventHandlers":
                out[k] = []
            elif k == "children":
                out[k] = []
            else:
                out[k] = blank(v, False)
        return out
    if isinstance(node, list):
        return [blank(x, False) for x in node]
    return node


def harvest(paths):
    by_type = collections.defaultdict(list)
    child_of = collections.defaultdict(list)
    for p in paths:
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception:
            continue
        for page in d.get("userPages", []):
            for c in walk(page.get("components") or []):
                t = c.get("type")
                if not t or t.endswith("ActionComponent"):
                    continue
                by_type[t].append(c)
                for kid in (c.get("children") or []):
                    child_of[(t, kid.get("type"))].append(kid)

    def pick(items):
        sig = collections.Counter(tuple(sorted(i.keys())) for i in items)
        want = sig.most_common(1)[0][0]
        for i in items:
            if tuple(sorted(i.keys())) == want:
                return i
        return items[0]

    out = {}
    for t, items in sorted(by_type.items()):
        out[t] = blank(pick(items))
    for (parent, kid_t), items in sorted(child_of.items()):
        # 按「父类型+子类型」分开命名：同一个父控件可能挂多种子控件，
        # 只按"父类型"命名会撞车（实测把按钮的文字标签采成了容器）。
        out["%s+%s" % (parent, kid_t)] = blank(pick(items))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projects", nargs="*")
    ap.add_argument("--scan", default=None, help="扫描该目录下所有 .eez-project")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    paths = list(a.projects)
    if a.scan:
        paths += glob.glob(os.path.join(a.scan, "**", "*.eez-project"), recursive=True)
    paths = sorted(set(os.path.abspath(p) for p in paths if os.path.isfile(p)))
    assert paths, "没找到工程文件"
    out = harvest(paths)
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print("扫描 %d 个工程 → %d 种控件结构 → %s" % (len(paths), len(out), a.out))
    for k, v in out.items():
        print("  %-28s %d 字段" % (k, len(v)))


if __name__ == "__main__":
    main()
