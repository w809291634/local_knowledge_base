# -*- coding: utf-8 -*-
"""
ink_check.py —— 墨迹（真实像素）检测：包围盒 / 边界触边 / 行分布

为什么不能"量控件框"：控件框只是布局声明，实际像素常因
父容器默认 padding、字体上下留白而与框不一致（PLAYBOOK §2.5）。

用法：
    python ink_check.py <图.png>                        # 全图墨迹包围盒 + 四条边触边检查
    python ink_check.py <图.png> --box X Y W H          # 只看这个矩形（**要紧包单个元素**）
    python ink_check.py <图.png> --rows --cols          # 打印行/列墨迹分布
    python ink_check.py <图.png> --against L T W H      # 与"声明框"对比，算出实际偏移
    python ink_check.py <目录>/                          # 批量

--against 的四个数是：声明框 left top width height（相对同一坐标系）。
输出 dx/dy = 墨迹左上 − 声明框左上，即"实际偏移"。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402


def check_one(path, cfg, box=None, thr=None, rows=False, cols=False, against=None):
    W, H = kit.screen_size(cfg)
    thr = thr or int((cfg.get("screen") or {}).get("ink_threshold", 140))
    img = kit.open_gray(path)
    print("== %s  (%dx%d)  thr=%d" % (os.path.basename(path), img.width, img.height, thr))

    if box:
        bb = kit.ink_bbox(img, box[0], box[1], box[0] + box[2], box[1] + box[3], thr=thr)
    else:
        bb = kit.ink_bbox(img, thr=thr)
    print("   墨迹包围盒: %s" % (str(bb) if bb else "（该区域无墨迹）"))

    if bb:
        problems = []
        if bb[0] < 0 or bb[1] < 0 or bb[2] > img.width - 1 or bb[3] > img.height - 1:
            problems.append("超出画布")
        print("   距四边: 上%d 下%d 左%d 右%d"
              % (bb[1], img.height - 1 - bb[3], bb[0], img.width - 1 - bb[2]))
        if problems:
            print("   !! %s" % ", ".join(problems))

    # 四条边是否有内容触边（自动跳过整行同色的分隔线）
    edge_hits = []
    for side in ("top", "bottom", "left", "right"):
        hit, cnt = kit.edge_touch(img, side, thr=thr,
                                 skip_uniform=bool((cfg.get("screen") or {}).get("last_row_is_separator", True)))
        if hit:
            edge_hits.append("%s(%d px)" % (side, cnt))
    print("   触边: %s" % (", ".join(edge_hits) if edge_hits else "无 ✓"))

    if against:
        l, t, w, h = against
        if bb:
            print("   声明框 left=%d top=%d %dx%d  →  墨迹偏移 dx=%+d dy=%+d"
                  % (l, t, w, h, bb[0] - l, bb[1] - t))
            print("      ⚠️ 若非 0：父容器/控件可能有默认 padding/border（PLAYBOOK §4.2 / 案例 B3）")
            print("      ⚠️ --box 必须**紧包单个元素**；若框内混了多个元素，偏移量是混合结果、无意义")
        else:
            print("   声明框 left=%d top=%d %dx%d  →  该区域无墨迹（元素未渲染？）" % (l, t, w, h))

    if rows or cols:
        if rows:
            prof = kit.row_profile(img, thr=thr)
            ys = [y for y, c in enumerate(prof) if c]
            if ys:
                print("   有内容的行: %d..%d" % (min(ys), max(ys)))
                for y in range(max(0, min(ys) - 2), min(img.height, max(ys) + 3)):
                    print("     y=%-4d %3d %s" % (y, prof[y], "#" * min(60, prof[y] // 2)))
        if cols:
            prof = kit.col_profile(img, thr=thr)
            xs = [x for x, c in enumerate(prof) if c]
            if xs:
                print("   有内容的列: %d..%d" % (min(xs), max(xs)))
    return bb


def main():
    ap = argparse.ArgumentParser(description="墨迹检测（ui_debug_kit）")
    ap.add_argument("target", help="图片或目录")
    ap.add_argument("--box", nargs=4, type=int, metavar=("X", "Y", "W", "H"), help="只看该矩形")
    ap.add_argument("--against", nargs=4, type=int, metavar=("L", "T", "W", "H"),
                    help="与声明框对比，输出偏移")
    ap.add_argument("--thr", type=int, default=None)
    ap.add_argument("--rows", action="store_true", help="打印行分布")
    ap.add_argument("--cols", action="store_true", help="打印列分布")
    args = ap.parse_args()

    cfg = kit.load_config()
    if os.path.isdir(args.target):
        for n in sorted(os.listdir(args.target)):
            if n.lower().endswith(".png"):
                check_one(os.path.join(args.target, n), cfg, args.box, args.thr, args.rows, args.cols)
                print()
    else:
        check_one(args.target, cfg, args.box, args.thr, args.rows, args.cols, args.against)
    return 0


if __name__ == "__main__":
    sys.exit(main())
