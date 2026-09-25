# -*- coding: utf-8 -*-
"""
tree_check.py —— 组件树静态体检（PLAYBOOK §2.6 的第 1~4 类）

检查项：
  1) 几何越界      —— 元素墨迹（按 config 的墨迹偏移估算）是否超出画布
  2) 文本换行      —— 文本真实宽度 > 框宽 → 会被折行
  3) 字体名有效性  —— 引用的字体是否在"已声明字体"里（否则会被回退 → 字号变小）
  4) 引用完整性    —— goto 目标是否存在、图片/字体是否已声明（0 死链）
  5) 入口页        —— 第一页是否为约定的入口页

字段映射由 config.json 的 tree_schema 决定，换框架只改那里。

用法：
    python tree_check.py                      # 用 config 里的设计源
    python tree_check.py --src 别的.json
    python tree_check.py --json out.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402


def run(cfg, src=None):
    sch = cfg.get("tree_schema", {}) or {}
    W, H = kit.screen_size(cfg)
    geom_ok = bool(W and H)
    if not geom_ok:
        print("⚠️ screen.w / screen.h 未配置 → 跳过几何与折行检查（只查字体名/跳转/入口页）")
    tm = kit.TextMeasurer(cfg)
    have_metrics = kit.HAS_PIL
    if not have_metrics:
        print("⚠️ 未安装 Pillow → 跳过文本度量（折行 / 按墨迹的越界），"
              "只做字体名 / 跳转 / 入口页 与纯几何框检查。装好 Pillow 重跑即可补齐。")
    known_fonts = kit.declared_fonts(cfg)
    issue = {"overflow": [], "wrap": [], "bad_font": [], "dead_link": [], "entry": [],
             "no_ink": []}

    pages = kit.load_pages(cfg) if not src else _load_pages_from(cfg, src, sch)
    page_names = [p[0] for p in pages]

    entry = (cfg.get("checks") or {}).get("entry_page")
    if entry and page_names and page_names[0] != entry:
        issue["entry"].append("第一页是 %r，期望 %r" % (page_names[0], entry))
    if entry and entry not in page_names:
        issue["entry"].append("入口页 %r 不在页面列表里" % entry)

    links = set()
    for pname, root in pages:
        for node, depth in kit.walk_tree(root, sch):
            if not isinstance(node, dict):
                continue
            typ = node.get(sch.get("type", "type"), "?")
            x = node.get(sch.get("x", "x"), 0) or 0
            y = node.get(sch.get("y", "y"), 0) or 0
            w = node.get(sch.get("w", "w"))
            h = node.get(sch.get("h", "h"))
            text = node.get(sch.get("text", "text"))
            font = node.get(sch.get("font", "font"))
            goto = node.get(sch.get("goto", "goto"))
            image = node.get(sch.get("image", "image"))
            if goto:
                links.add((pname, goto))

            # 字体名有效性（内置字体不算未声明）
            if font and known_fonts and font not in known_fonts and not kit.is_builtin_font(cfg, font):
                issue["bad_font"].append((pname, font, (text or "")[:14]))

            # 几何 / 换行（需要屏幕尺寸；文本度量额外需要 Pillow）
            if text and geom_ok and have_metrics:
                px = tm.px_of(font)
                net = tm.width(text, font)
                boxw = float(w) if isinstance(w, (int, float)) and w else net
                off = kit.ink_offset(cfg, px)
                ink_top = y + (off[0] if off else 1)
                ink_bot = y + (off[1] if off else px + 1)
                if x < -0.5 or ink_top < -0.5 or x + boxw > W - 0.5 or ink_bot > H - 0.5:
                    issue["overflow"].append(
                        (pname, (text or "")[:16],
                         "x=%.0f..%.0f ink_y=%.0f..%.0f" % (x, x + boxw, ink_top, ink_bot)))
                if isinstance(w, (int, float)) and w and net > w + 0.5:
                    issue["wrap"].append((pname, (text or "")[:16], "文本%.0f > 框%.0f" % (net, w)))
            elif geom_ok and isinstance(w, (int, float)) and isinstance(h, (int, float)) and w and h:
                if x < -1 or y < -1 or x + w > W + 1 or y + h > H + 1:
                    issue["overflow"].append((pname, typ, "x=%.0f..%.0f y=%.0f..%.0f"
                                              % (x, x + w, y, y + h)))

    for pname, target in sorted(links):
        if target not in page_names:
            issue["dead_link"].append((pname, target))

    return {"pages": page_names, "issue": issue, "links": sorted(links)}


def _load_pages_from(cfg, src, sch):
    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in sch.get("pages", ["pages"]):
        if key in data:
            data = data[key]; break
    out = []
    for p in (data if isinstance(data, list) else [data]):
        out.append((p.get(sch.get("page_name", "name"), "?"),
                    p.get(sch.get("page_root", "screen"), p)))
    return out


def main():
    ap = argparse.ArgumentParser(description="组件树静态体检（ui_debug_kit）")
    ap.add_argument("--src", default=None, help="设计源文件（默认取 config）")
    ap.add_argument("--json", default=None, help="结果写 JSON")
    ap.add_argument("--show", type=int, default=8, help="每类最多打印几条")
    args = ap.parse_args()

    cfg = kit.load_config()
    r = run(cfg, args.src)
    it = r["issue"]
    print("页面数: %d   入口页: %s" % (len(r["pages"]), r["pages"][0] if r["pages"] else "?"))
    print("跳转引用: %d 个" % len(r["links"]))

    labels = {"overflow": "几何越界", "wrap": "文本会被折行", "bad_font": "字体名未声明",
              "dead_link": "死链", "entry": "入口页", "no_ink": "无墨迹"}
    total = 0
    for k, lab in labels.items():
        items = it.get(k) or []
        total += len(items)
        mark = "OK  " if not items else "FAIL"
        print("  [%s] %-12s %d" % (mark, lab, len(items)))
        for x in items[:args.show]:
            print("        %s" % (x,))
        if len(items) > args.show:
            print("        ... 还有 %d 条" % (len(items) - args.show))

    print("\n结论: %s" % ("全部通过 ✓" if total == 0 else "发现 %d 个问题" % total))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
        print("json -> %s" % args.json)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
