# -*- coding: utf-8 -*-
"""BTN_CHILD 通用门禁：任意 .eez-project 的按钮子标签必须 content 尺寸，禁止等于按钮盒。

用法：python tools/check_button_child.py <a.eez-project> [...]
"""
import io
import json
import sys


def check(path):
    proj = json.load(io.open(path, encoding="utf-8"))
    bad, total = [], 0
    for pg in proj.get("userPages", []):
        for w in pg.get("components", [{}])[0].get("children", []):
            if w.get("type") != "LVGLButtonWidget":
                continue
            total += 1
            ch = (w.get("children") or [None])[0]
            if not ch:
                bad.append((pg.get("name"), w.get("identifier"), "没有子标签"))
                continue
            if ch.get("widthUnit") != "content" or ch.get("heightUnit") != "content":
                bad.append((pg.get("name"), w.get("identifier"),
                            "单位 %s/%s" % (ch.get("widthUnit"), ch.get("heightUnit"))))
            if ch.get("width") == w.get("width") and ch.get("height") == w.get("height"):
                bad.append((pg.get("name"), w.get("identifier"), "子标签几何等于按钮盒"))
            if not (ch.get("text") or "").strip():
                bad.append((pg.get("name"), w.get("identifier"), "子标签文本为空"))
    for b in bad[:30]:
        print("  FAIL", b)
    print("[BTN_CHILD] %s 按钮 %d ｜ 违规 %d ｜ %s" %
          (path, total, len(bad), "PASS" if not bad else "FAIL"))
    return 1 if bad else 0


def main():
    if len(sys.argv) < 2:
        print("用法: python tools/check_button_child.py <a.eez-project> [...]")
        return 2
    rc = 0
    for p in sys.argv[1:]:
        rc |= check(p)
    return rc


if __name__ == "__main__":
    sys.exit(main())
