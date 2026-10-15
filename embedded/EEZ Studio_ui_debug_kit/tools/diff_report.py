# -*- coding: utf-8 -*-
"""
diff_report.py —— 图像差异量化（对照修复的第 1~2 步）

用法：
    python diff_report.py 期望图.png 实际图.png
    python diff_report.py 期望目录/ 实际目录/            # 按同名文件批量比对
    python diff_report.py a.png b.png --grid 40 --thr 64 --json out.json
    python diff_report.py a.png b.png --overlay out.png  # 导出差异标红图

判读（详见 PLAYBOOK §2.4）：
    big == 0                     → 一致
    big/total < accept_pct 且形状一致 → 抗锯齿/取整，可忽略
    否则                         → 看 hot 热点定位到元素
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402


def _pairs(a, b):
    if os.path.isdir(a) and os.path.isdir(b):
        names = sorted(n for n in os.listdir(a) if n.lower().endswith(".png"))
        for n in names:
            pb = os.path.join(b, n)
            if os.path.isfile(pb):
                yield n, os.path.join(a, n), pb
    else:
        yield os.path.basename(a), a, b


def _overlay(ref_path, act_path, out_path, thr=64):
    from PIL import Image
    d_out = os.path.dirname(os.path.abspath(out_path))
    if d_out:
        os.makedirs(d_out, exist_ok=True)
    a = Image.open(ref_path).convert("RGB")
    b = Image.open(act_path).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    from PIL import ImageChops
    d = ImageChops.difference(a.convert("L"), b.convert("L")).point(lambda v: 255 if v >= thr else 0)
    out = a.copy(); px_d, px_o = d.load(), out.load()
    for y in range(a.height):
        for x in range(a.width):
            if px_d[x, y]:
                px_o[x, y] = (255, 40, 40)
    out.save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser(description="图像差异量化（ui_debug_kit）")
    ap.add_argument("ref", help="期望图/目录")
    ap.add_argument("act", help="实际图/目录")
    ap.add_argument("--grid", type=int, default=40, help="热点聚类块大小（默认 40）")
    ap.add_argument("--thr", type=int, default=None, help="结构性差异阈值（默认取 config）")
    ap.add_argument("--json", default=None, help="把结果写成 JSON")
    ap.add_argument("--overlay", default=None, help="导出差异标红图（仅单图模式）")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    cfg = kit.load_config()
    big_thr = args.thr or int((cfg.get("checks") or {}).get("diff_big_threshold", 64))
    accept = float((cfg.get("checks") or {}).get("diff_accept_pct", 0.05))

    results = {}
    worst = None
    for name, ra, rb in _pairs(args.ref, args.act):
        r = kit.diff_report(ra, rb, grid=args.grid, big_thr=big_thr)
        results[name] = r
        if worst is None or r["pct"] > results[worst]["pct"]:
            worst = name
        if not args.quiet:
            flag = "一致" if r["big"] == 0 else ("可忽略" if r["pct"] < accept else "★有结构性差异")
            print("%-18s big=%-8d (%.4f%%)  mid=%-8d  %s%s"
                  % (name, r["big"], r["pct"], r["mid"], flag,
                     "" if r["size_ok"] else "  [尺寸不一致: %s vs %s]" % (r["size_ref"], r["size_act"])))
            for (gx, gy), cnt in r["hot"][:4]:
                print("      热点 x=%d..%d y=%d..%d : %d px" % (gx, gx + args.grid, gy, gy + args.grid, cnt))
            if r["bbox"]:
                print("      差异包围盒 %s" % (r["bbox"],))

    if args.overlay and not os.path.isdir(args.ref):
        print("overlay -> %s" % _overlay(args.ref, args.act, args.overlay, big_thr))

    if worst is not None and not args.quiet:
        w = results[worst]
        print("\n结论: 最大差异在 [%s] = %.4f%%  ->  %s"
              % (worst, w["pct"], "一致" if w["big"] == 0 else
                 ("可忽略（光栅化差异）" if w["pct"] < accept else "需排查（结构性差异）")))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            import json
            json.dump(results, f, ensure_ascii=False, indent=1)
        print("json -> %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
