# -*- coding: utf-8 -*-
"""共用布局自查（跨工程）：几何重叠 + 越界 + 零尺寸 + 页骨架间距 + 相似度门槛。

用法：
  python tools/layout_check.py <工程.eez-project> [--min-sim 99] [--max-overlap 0.2]
                              [--divider 88]

判据（任何一条不过 → 退出码 1）：
  L1 控件框不越出页面、宽高 > 0
  L2 结构性控件之间不得"部分重叠"（绝对值坐标；排除 _deco/隐藏浮层/父子/文本标签按钮）
  L3 页内 identifier 唯一
  L4 如果工程里有 designer_annotated/d5_相似度.txt，且传了 --min-sim，则逐页/平均都必须达标
  L5 页骨架间距（需 --divider Y）：页头带控件必须同一 y/同高；内容控件距分隔线 ≥12px
  L6 组内等距（需 --layout-json）：同页同尺寸卡片纵向/横向 pitch 必须一致（±1px）
  L7 最小净距：互相独立、可交互的控件之间净距 ≥8px

  加 --warn 时 L6/L7 只打印告警、不改退出码（先清历史包袱，再转硬门禁）。

为什么需要 L2：D5 比的是"画布 vs 设计图"，两边同源，设计源自己叠了也会一致；
重叠只有几何规则能查（w78 实测 detail_camera 控件框压到下一行 53%）。
为什么需要 L5：D5/重叠都查不出"这一页按钮比别的页低了 8px、列表离按钮近了 10px"，
这类间距漂移只能跨页比对页头带与内容起始线（w78 Wi-Fi 页实测）。
为什么需要 L6/L7：卡片是装饰 rect，EEZ 里没有对应控件，D5/L2 都看不见"两张卡贴死"；
同尺寸个体等距与独立控件最小净距只能从设计源导出的 layout_boxes.json 判（w78 设置页实测）。
"""
import io
import json
import os
import re
import sys

STRUCT = {"LVGLContainerWidget", "LVGLListWidget", "LVGLChartWidget", "LVGLBarWidget",
          "LVGLSliderWidget", "LVGLTextareaWidget", "LVGLKeyboardWidget"}
GUTTER = 12.0          # 内容控件顶边距页头分隔线的最小间距
MIN_GAP = 8.0          # 独立可交互控件之间的最小净距
INTERACTIVE = {"LVGLButtonWidget", "LVGLSwitchWidget", "LVGLSliderWidget",
               "LVGLTextareaWidget", "LVGLListWidget", "LVGLRollerWidget",
               "LVGLKeyboardWidget", "LVGLChartWidget", "LVGLBarWidget",
               "LVGLCheckboxWidget"}


def walk_abs(comps, ox=0, oy=0, hidden=False, anc=()):
    for c in comps:
        h = hidden or c.get("hiddenFlag") is True
        x, y = ox + int(c.get("left", 0)), oy + int(c.get("top", 0))
        yield c, x, y, h, anc
        for k in walk_abs(c.get("children") or [], x, y, h, anc + (id(c),)):
            yield k


def top_controls(comps):
    """页内一层控件：穿透 LVGLScreenWidget 外壳，不再进容器内部。"""
    out = []
    for c in comps or []:
        if c.get("type") == "LVGLScreenWidget":
            out += top_controls(c.get("children") or [])
        else:
            out.append(c)
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    proj_path = sys.argv[1]
    min_sim = None
    max_overlap = 0.2
    divider = None
    layout_json = None
    warn = "--warn" in sys.argv
    for i, a in enumerate(sys.argv):
        if a == "--min-sim" and i + 1 < len(sys.argv):
            min_sim = float(sys.argv[i + 1])
        if a == "--max-overlap" and i + 1 < len(sys.argv):
            max_overlap = float(sys.argv[i + 1])
        if a == "--divider" and i + 1 < len(sys.argv):
            divider = float(sys.argv[i + 1])
        if a == "--layout-json" and i + 1 < len(sys.argv):
            layout_json = sys.argv[i + 1]

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

    # L5 页骨架间距：页头带控件跨页同 y/同高；内容控件距分隔线 ≥12px
    n_space = 0
    if divider is not None:
        for pg in proj["userPages"]:
            name = pg["name"]
            top = []
            for c in top_controls(pg["components"]):
                if c.get("hiddenFlag") is True or \
                        c["type"] in ("LVGLScreenWidget", "LVGLLabelWidget") or \
                        "_deco" in str(c.get("identifier") or ""):
                    continue
                top.append((c.get("identifier") or c["type"],
                            int(c.get("left", 0)), int(c.get("top", 0)),
                            int(c.get("width", 0)), int(c.get("height", 0))))
            band = [t for t in top if t[2] + t[4] <= divider]
            if band:
                ys, hs = {}, {}
                for t in band:
                    ys[t[2]] = ys.get(t[2], 0) + 1
                hy = max(ys, key=ys.get)
                for t in band:
                    if t[2] == hy:
                        hs[t[4]] = hs.get(t[4], 0) + 1
                hh = max(hs, key=hs.get)
                for cid, x, y, w_, h_ in band:
                    if abs(y - hy) > 2 or abs(h_ - hh) > 2:
                        n_space += 1
                        fails.append("L5 页 %s 页头控件 %s y/h=%d/%d，基线 %d/%d"
                                     % (name, cid, y, h_, hy, hh))
            for cid, x, y, w_, h_ in top:
                if divider - 1 <= y < divider + GUTTER:
                    n_space += 1
                    fails.append("L5 页 %s 控件 %s 顶边 y=%d，距分隔线 %dpx < %dpx"
                                 % (name, cid, y, int(y - divider), int(GUTTER)))

    # L6 组内等距 + L7 最小净距（可单跑 --warn 先出报告）
    space_msgs = []
    if layout_json and os.path.isfile(layout_json):
        boxes = json.load(io.open(layout_json, encoding="utf-8"))
        for name, bs in boxes.items():
            for axis in ("y", "x"):
                gkey = ("x", "w", "h") if axis == "y" else ("y", "w", "h")
                groups = {}
                for bx in bs:
                    groups.setdefault(tuple(bx[k] for k in gkey), []).append(bx[axis])
                for ps in groups.values():
                    ps = sorted(set(ps))
                    if len(ps) < 3:
                        continue
                    ds = [b - a for a, b in zip(ps, ps[1:])]
                    if max(ds) - min(ds) > 1:
                        space_msgs.append(
                            "L6 页 %s %s向同尺寸卡片间距不等：%s"
                            % (name, "纵" if axis == "y" else "横",
                               "/".join(str(d) for d in ds)))
    for pg in proj["userPages"]:
        name = pg["name"]
        nodes = []
        for c in top_controls(pg["components"]):
            if c["type"] not in INTERACTIVE or c.get("hiddenFlag") is True:
                continue
            if "_deco" in str(c.get("identifier") or ""):
                continue
            nodes.append((c.get("identifier") or c["type"], int(c.get("left", 0)),
                          int(c.get("top", 0)), int(c.get("width", 0)),
                          int(c.get("height", 0))))
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b = nodes[i], nodes[j]
                ax, ay, aw, ah = a[1:]
                bx, by, bw, bh = b[1:]
                ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
                iy = max(0, min(ay + ah, by + bh) - max(ay, by))
                gap = None
                if ix > 0 and iy == 0:
                    gap = max(ay - (by + bh), by - (ay + ah))
                elif iy > 0 and ix == 0:
                    gap = max(ax - (bx + bw), bx - (ax + aw))
                if gap is not None and 0 <= gap < MIN_GAP:
                    space_msgs.append("L7 页 %s 控件 %s↔%s 净距 %.0fpx < %.0f"
                                      % (name, a[0], b[0], gap, MIN_GAP))

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

    print("[LAYOUT] 页 %d ｜ 结构控件 %d ｜ 重叠 %d ｜ 间距 %d ｜ L6/L7 %d ｜ 相似度 %s"
          % (len(proj["userPages"]), n_ctrl, n_overlap,
             n_space if divider is not None else -1,
             len(space_msgs) if layout_json else -1, sim_msg))
    print("[LAYOUT] " + ("PASS" if not fails and (warn or not space_msgs) else "FAIL"))
    for f in fails[:30]:
        print("  !! " + f)
    for m in space_msgs[:30]:
        print(("  ~ " if warn else "  !! ") + m)
    if not warn:
        fails += space_msgs
    return 0 if (not fails) else 1


if __name__ == "__main__":
    sys.exit(main())
