# -*- coding: utf-8 -*-
"""tab_parent_check.py —— Tab 结构门禁：LVGLTabWidget 必须挂在 LVGLTabviewWidget 下

背景：Tab 是 EEZ Components Palette 里的独立控件，但 EEZ 规定它只能作为 Tabview 的子对象。
挂在 Screen 直下时 GUI Checks 报 `Invalid position of Tab widget inside Widgets Structure`，
而 headless 构建不查这层结构（P-0033 / skills.md §11.20）。本脚本把该不变量做成常驻门禁。

用法：
    python tab_parent_check.py <a.eez-project> [b.eez-project ...]
    python tab_parent_check.py --all <root>       # 递归扫 root 下所有 .eez-project
退出码：0 = 无违例；1 = 有违例
"""
import glob
import json
import os
import sys

TAB = "LVGLTabWidget"
HOST = "LVGLTabviewWidget"


def check(path):
    with open(path, encoding="utf-8") as fp:
        proj = json.load(fp)
    tabs = 0
    hosts = 0
    bad = []

    def rec(node, parent_type):
        nonlocal tabs, hosts
        if isinstance(node, dict):
            typ = node.get("type")
            if typ == TAB:
                tabs += 1
                if parent_type != HOST:
                    bad.append((node.get("identifier") or node.get("objID"), parent_type))
            elif typ == HOST:
                hosts += 1
            for key, val in node.items():
                if isinstance(val, (dict, list)):
                    rec(val, typ if key == "children" else parent_type)
        elif isinstance(node, list):
            for val in node:
                rec(val, parent_type)

    for page in proj.get("userPages", []):
        for comp in page.get("components", []):
            rec(comp, None)
    for widget in proj.get("userWidgets", []):
        rec(widget, None)
    return tabs, hosts, bad


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "--all":
        root = args[1] if len(args) > 1 else "."
        files = sorted(p for p in glob.glob(os.path.join(root, "**", "*.eez-project"),
                                            recursive=True)
                       if "tmp" not in p.replace(os.sep, "/").split("/"))
    else:
        files = args

    total_tabs = 0
    viol = 0
    for f in files:
        try:
            tabs, hosts, bad = check(f)
        except Exception as exc:
            print("[TAB_GATE] SKIP %s (%s)" % (f, exc))
            continue
        total_tabs += tabs
        viol += len(bad)
        status = "OK" if not bad else "FAIL"
        print("[TAB_GATE] %s tabs=%d tabview=%d %s  %s" % (status, tabs, hosts,
              "违例=%d" % len(bad) if bad else "违例=0", f))
        for ident, parent in bad:
            print("    !! Tab %s 的父级是 %s（应为 %s）" % (ident, parent, HOST))

    print("[TAB_GATE] 共 %d 个工程，Tab %d 个，违例 %d 个" % (len(files), total_tabs, viol))
    return 1 if viol else 0


if __name__ == "__main__":
    sys.exit(main())
