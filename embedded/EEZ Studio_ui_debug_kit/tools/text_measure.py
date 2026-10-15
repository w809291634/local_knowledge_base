# -*- coding: utf-8 -*-
"""
text_measure.py —— 文本真实宽度与字形度量（居中/换行/越界判定都要用它）

关键点（PLAYBOOK §4.3/§4.5）：
  - 宽度要按**实际生效的字号**算（设计稿常写不存在的中间号，会被回退）
  - 图标字符必须切到**图标字体**，否则宽度和字形都错
  - 居中用**净宽**；换行判定用**含余量**的宽度

用法：
    python text_measure.py "<文本>" --font <字体名>
    python text_measure.py "<文本>" --size 14 --margin
    python text_measure.py --batch texts.txt --font <字体名> --width-limit 60
    python text_measure.py "<文本>" --font <字体名> --centered-in 64   # 给居中算 x
    python text_measure.py                                            # 跑自检样本
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402


def measure(tm, text, font=None, size=None, margin=False, limit=None, centered_in=None):
    net = tm.width(text, font, size)
    withm = tm.width(text, font, size, margin=True)
    px = tm.px_of(font, size)
    w, up, dn = tm.glyph_metrics(text, font, size)
    line = "%-30r px=%-3d 净宽=%-7.1f 含余量=%-7.1f 墨迹偏移=%s..%s" % (
        text[:28], px, net, withm,
        ("%+d" % up) if up is not None else "?", ("%+d" % dn) if dn is not None else "?")
    if limit:
        line += "   %s" % ("OK" if net <= limit else "★超出框宽 %.1f（会折行）" % (net - limit))
    print(line)
    if centered_in is not None:
        print("     居中于 %d 宽 → x = %.1f（净宽居中；不要用固定宽+对齐属性）"
              % (centered_in, centered_in / 2.0 - net / 2.0))
    return net


def main():
    ap = argparse.ArgumentParser(description="文本度量（ui_debug_kit）")
    ap.add_argument("text", nargs="?", help="要量的文本")
    ap.add_argument("--font", default=None, help="字体名（取自 config.fonts.name_to_px）")
    ap.add_argument("--size", type=int, default=None, help="像素字号（字体名未知时用）")
    ap.add_argument("--margin", action="store_true", help="同时给出含 8px 防换行余量的宽度")
    ap.add_argument("--width-limit", type=float, default=None, help="与该框宽比较，判断是否折行")
    ap.add_argument("--centered-in", type=float, default=None, help="给该宽度做居中，输出 x")
    ap.add_argument("--batch", default=None, help="每行一条文本的文件")
    args = ap.parse_args()

    cfg = kit.load_config()
    tm = kit.TextMeasurer(cfg)
    print("字体: %s" % kit.cfg_path(cfg, "fonts.device_ttf"))
    print("字号表: %s" % tm.name_to_px)
    print("-" * 72)

    if args.batch:
        with open(args.batch, "r", encoding="utf-8") as f:
            for ln in f:
                s = ln.rstrip("\n")
                if s:
                    measure(tm, s, args.font, args.size, args.margin, args.width_limit, args.centered_in)
    elif args.text is not None:
        measure(tm, args.text, args.font, args.size, args.margin, args.width_limit, args.centered_in)
    else:
        # 没给参数就跑一组自检样本（用配置里第一个字体名，字号取自其映射）
        print("（未给文本，跑自检样本）")
        fname = next(iter(tm.name_to_px), None)
        if not fname:
            print("!! config.fonts.name_to_px 为空，请先填好字体名映射")
            return 2
        for s in ("Hello", "Mixed 混排 123", "· — 【】"):
            measure(tm, s, fname)
    return 0


if __name__ == "__main__":
    sys.exit(main())
