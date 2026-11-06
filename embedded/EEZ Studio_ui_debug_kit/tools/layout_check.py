# -*- coding: utf-8 -*-
"""共用布局自查（跨工程）：几何重叠 + 越界 + 零尺寸 + 相似度门槛。

用法：
  python tools/layout_check.py <工程.eez-project> [--min-sim 99] [--max-overlap 0.2]

判据（任何一条不过 → 退出码 1）：
  L1 控件框不越出页面、宽高 > 0
  L2 结构性控件之间不得"部分重叠"（绝对值坐标；排除 _deco/隐藏浮层/父子/文本标签按钮）
  L3 页内 identifier 唯一
  L4 如果工程里有 designer_annotated/d5_相似度.txt，且传了 --min-sim，则逐页/平均都必须达标

为什么需要 L2：D5 比的是"画布 vs 设计图"，两边同源，设计源自己叠了也会一致；
重叠只有几何规则能查（w78 实测 detail_camera 控件框压到下一行 53%）。
"""
import io
import json
import os
import re
import sys

STRUCT = {"LVGLContainerWidget", "LVGLListWidget", "LVGLChartWidget", "LVGLBarWidget",
          "LVGLSliderWidget", "LVGLTextareaWidget", "LVGLKeyboardWidget"}


def walk_abs(comps, ox=0, oy=0, hidden=False, anc=()):
    for c in comps:
        h = hidden or c.get("hiddenFlag") is True
        x, y = ox + int(c.get("left", 0)), oy + int(c.get("top", 0))
        yield c, x, y, h, anc
        for k in walk_abs(c.get("children") or [], x, y, h, anc + (id(c),)):
            yield k


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    proj_path = sys.argv[1]
    min_sim = None
    max_overlap = 0.2
    for i, a in enumerate(sys.argv):
        if a == "--min-sim" and i + 1 < len(sys.argv):
            min_sim = float(sys.argv[i + 1])
        if a == "--max-overlap" and i + 1 < len(sys.argv):
            max_overlap = float(sys.argv[i + 1])

    proj = json.load(io.open(proj_path, encoding="utf-8"))
    g = proj["settings"]["general"]
    W, H = g["displayWidth"], g["displayHeight"]
    fails = []
    n_overlap = 0
    n_ctrl = 0

    for pg in proj["userPages"]:
        name = pg["name"]
        ids = [c.get("identifier") for c, *_ in walk_abs(pg["components"]) if c.get("identifier")]
        if len(ids) != len(set(ids)):
            fails.append("L3 页 %s identifier 重复" % name)

        nodes = []
        for c, x, y, h, anc in walk_abs(pg["components"]):
            cw, ch = int(c.get("width", 0)), int(c.get("height", 0))
            if cw <= 0 or ch <= 0:
                fails.append("L1 页 %s 控件 %s 宽高为 0" % (name, c.get("identifier")))
            if x < -2 or y < -2 or x + cw > W + 2 or y + ch > H + 2:
                if c.get("hiddenFlag") is not True:
                    fails.append("L1 页 %s 控件 %s 越界 (%d,%d,%d,%d)"
                                 % (name, c.get("identifier"), x, y, cw, ch))
            if c["type"] in STRUCT and not h and c.get("identifier") \
                    and "_deco" not in c["identifier"]:
                nodes.append((c, x, y, anc))
        n_ctrl += len(nodes)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, ax, ay, aa = nodes[i]
                b, bx, by, ab = nodes[j]
                if id(a) in ab or id(b) in aa:
                    continue
                aw, ah = int(a["width"]), int(a["height"])
                bw, bh = int(b["width"]), int(b["height"])
                ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
                iy = max(0, min(ay + ah, by + bh) - max(ay, by))
                if ix * iy <= 0:
                    continue
                if ((ax <= bx and ay <= by and ax + aw >= bx + bw and ay + ah >= by + bh) or
                        (bx <= ax and by <= ay and bx + bw >= ax + aw and by + bh >= ay + ah)):
                    continue
                small = min(aw * ah, bw * bh)
                if small and ix * iy / float(small) >= max_overlap:
                    n_overlap += 1
                    fails.append("L2 页 %s 控件 %s 与 %s 部分重叠 %d%%"
                                 % (name, a["identifier"], b["identifier"],
                                    int(ix * iy * 100 / small)))

    # L4 相似度门槛（读 D5 产物）
    sim_file = os.path.join(os.path.dirname(os.path.abspath(proj_path)),
                            "designer_annotated", "d5_相似度.txt")
    sim_msg = "无 D5 记录"
    if os.path.isfile(sim_file):
        txt = io.open(sim_file, encoding="utf-8").read()
        m_avg = re.search(r"平均相似度\s*([\d.]+)%", txt)
        m_min = re.search(r"最低\s*([\d.]+)%", txt)
        if m_avg:
            sim_msg = "平均 %.2f%%" % float(m_avg.group(1))
            if m_min:
                sim_msg += " ｜ 最低 %.2f%%" % float(m_min.group(1))
            if min_sim is not None:
                vals = [float(m_avg.group(1))] + ([float(m_min.group(1))] if m_min else [])
                if min(vals) < min_sim:
                    fails.append("L4 相似度低于 %.1f%%（%s）" % (min_sim, sim_msg))

    print("[LAYOUT] 页 %d ｜ 结构控件 %d ｜ 重叠 %d ｜ 相似度 %s"
          % (len(proj["userPages"]), n_ctrl, n_overlap, sim_msg))
    print("[LAYOUT] " + ("PASS" if not fails else "FAIL"))
    for f in fails[:30]:
        print("  !! " + f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
