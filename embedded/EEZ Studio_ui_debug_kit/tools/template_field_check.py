# -*- coding: utf-8 -*-
"""template_field_check.py —— 任意 .eez-project 的字段集门禁（A14 级）

判据：每个控件的字段集必须等于拖拽模板库里的同名模板；`identifier` 是放置期字段，不计。
用途：抓“生成器手搓字段/旧写法”和“模板升级后示例未跟”的系统性偏差。

用法：
    python template_field_check.py <a.eez-project> [b.eez-project ...]
    python template_field_check.py --all <root>
    python template_field_check.py --templates <templates_dir> ...   # 默认用 kit 镜像
退出码：0 = 全部一致；1 = 有偏差
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TPL = os.path.join(HERE, "..", "reference", "eez_widget_syntax", "templates")


def load_templates(tdir):
    tpl = {}
    for f in glob.glob(os.path.join(tdir, "*.json")):
        with open(f, encoding="utf-8") as fp:
            t = json.load(fp)
        if t.get("type"):
            tpl[t["type"]] = set(t.keys())
    return tpl


def check_project(path, tpl):
    with open(path, encoding="utf-8") as fp:
        proj = json.load(fp)
    widgets = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("objID") and node.get("type"):
                widgets.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(proj.get("userPages", []))
    walk(proj.get("userWidgets", []))
    covered = [w for w in widgets if w["type"] in tpl]
    patterns = {}
    for w in covered:
        t = tpl[w["type"]]
        extra = tuple(sorted(set(w) - t - {"identifier"}))
        missing = tuple(sorted(t - set(w) - {"identifier"}))
        if extra or missing:
            key = (w["type"], extra, missing)
            patterns[key] = patterns.get(key, 0) + 1
    return len(widgets), len(covered), patterns


def main():
    ap = argparse.ArgumentParser(description="字段集必须等于拖拽模板库（A14 级）")
    ap.add_argument("projects", nargs="*")
    ap.add_argument("--all", metavar="ROOT")
    ap.add_argument("--templates", default=DEFAULT_TPL)
    args = ap.parse_args()

    tpl = load_templates(args.templates)
    if not tpl:
        print("[FIELD_GATE] 模板目录为空：%s" % args.templates)
        return 2
    if args.all:
        files = sorted(p for p in glob.glob(os.path.join(args.all, "**", "*.eez-project"),
                                            recursive=True)
                       if "tmp" not in p.replace(os.sep, "/").split("/"))
    else:
        files = args.projects
    if not files:
        ap.print_help()
        return 2

    bad_total = 0
    for f in files:
        try:
            total, covered, patterns = check_project(f, tpl)
        except Exception as exc:
            print("[FIELD_GATE] SKIP %s (%s)" % (f, exc))
            continue
        bad = sum(patterns.values())
        bad_total += bad
        print("[FIELD_GATE] %s widgets=%d covered=%d ok=%d bad=%d  %s"
              % ("OK" if not bad else "FAIL", total, covered, covered - bad, bad, f))
        for (typ, extra, missing), n in sorted(patterns.items(), key=lambda kv: -kv[1]):
            print("    %-26s n=%3d 多=%s 缺=%s" % (typ, n, list(extra), list(missing)))
    print("[FIELD_GATE] 工程=%d 偏差控件合计=%d" % (len(files), bad_total))
    return 1 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
