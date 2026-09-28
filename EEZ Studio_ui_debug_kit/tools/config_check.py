# -*- coding: utf-8 -*-
"""
config_check.py —— 工程配置适配体检（ui_debug_kit）

回答一个问题：**工具箱的配置真的对这个工程生效了吗？**

依次核对四类一致性，任何一类对不上都会导致门禁"静默降级"
（看着 PASS，其实该查的没查）：

| 类 | 核对什么 | 对不上的后果 |
|---|---|---|
| A 路径 | 配置里写的每个文件/目录是否真实存在 | 脚本跳过或直接崩 |
| B 屏幕 | screen.w/h 是否等于设计源与工程文件里的实际尺寸 | 越界检查算错基准 |
| C 字体 | name_to_px / icon 私有区是否覆盖设计源实际用到的字体与码位 | 未声明字体误报、图标宽度算错 |
| D 结构 | tree_schema 的键名与类型是否匹配设计源真实结构 | 组件树遍历不到，体检形同虚设 |
| E 门禁 | checks.gates 挂的脚本是否存在 | 闸门被 SKIP，等于没挂 |

用法：
    python tools/config_check.py            # 在工程根目录跑
    python tools/config_check.py --strict   # WARN 也算不通过
退出码：0=通过，1=有 ERROR（或 --strict 下有 WARN）。
"""
import argparse
import glob
import json
import os
import re
import sys

import kit  # noqa: E402

# 配置里这些目录是运行时产物（跑一次 gate 后才出现），缺失不算错
RUNTIME_DIRS = {"paths.preview_dir", "paths.render_dir", "paths.work_dir",
                "paths.native_dir", "paths.font_c"}


def _projcfg_dir(cfg):
    return os.path.dirname(os.path.abspath(cfg.get("__path__") or kit.PROJECT_CONFIG_NAME))


def _rel(cfg, dotted_or_path):
    """把配置里的相对路径解析成绝对路径（相对配置文件所在目录）。"""
    p = dotted_or_path
    if not p:
        return None
    p = os.path.expanduser(p.replace("\\", "/"))
    if not os.path.isabs(p):
        base = _projcfg_dir(cfg)
        p = os.path.normpath(os.path.join(base, p))
    return p


def _get(cfg, dotted, default=None):
    cur = cfg
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


class Report(object):
    def __init__(self):
        self.rows = []

    def add(self, level, group, item, detail):
        self.rows.append((level, group, item, detail))

    ok = lambda self, g, i, d: self.add("OK", g, i, d)          # noqa: E731
    warn = lambda self, g, i, d: self.add("WARN", g, i, d)      # noqa: E731
    err = lambda self, g, i, d: self.add("ERROR", g, i, d)      # noqa: E731
    info = lambda self, g, i, d: self.add("INFO", g, i, d)      # noqa: E731

    def summary(self):
        n = {"ERROR": 0, "WARN": 0, "OK": 0, "INFO": 0}
        for lv, _g, _i, _d in self.rows:
            n[lv] = n.get(lv, 0) + 1
        return n


# --------------------------------------------------------------------------- #
# A. 路径
# --------------------------------------------------------------------------- #
def check_paths(cfg, rep):
    base = _projcfg_dir(cfg)

    paths = []
    for k in ("root", "design_dir", "design_src", "project_file", "gen_dir", "builder"):
        v = _get(cfg, "project." + k)
        if v:
            paths.append(("project." + k, v))
    for k in ("python", "python_venv", "node"):
        v = _get(cfg, "binaries." + k)
        if v:
            paths.append(("binaries." + k, v))
    for k in ("device_ttf", "icon_woff", "icon_ttf"):
        v = _get(cfg, "fonts." + k)
        if v:
            paths.append(("fonts." + k, v))
    for k in ("preview_dir", "render_dir", "native_dir", "work_dir",
              "screens_c", "lv_conf", "font_c"):
        v = _get(cfg, "paths." + k)
        if v:
            paths.append(("paths." + k, v))
    v = _get(cfg, "runtime.exe")
    if v:
        paths.append(("runtime.exe", v))

    for key, raw in paths:
        abs_p = _rel(cfg, raw)
        exists = os.path.exists(abs_p) if abs_p else False
        if not exists and "*" in raw:
            hits = sorted(glob.glob(abs_p)) if abs_p else []
            exists = bool(hits)
            if hits:
                rep.ok("A 路径", key, "%d 个文件匹配 %s" % (len(hits), raw))
                continue
        if exists:
            rep.ok("A 路径", key, raw)
        elif key in RUNTIME_DIRS:
            rep.info("A 路径", key, "尚不存在（运行时产物）：%s" % raw)
        else:
            rep.err("A 路径", key, "**不存在**：%s -> %s" % (raw, abs_p))

    # 旧工程绝对路径残留
    txt = json.dumps(cfg, ensure_ascii=False)
    for m in sorted(set(re.findall(r"[A-Za-z]:[\\/][^\\/\"]{3,}", txt))):
        cand = m.replace("\\\\", "\\")
        if os.path.exists(cand) or "Windows" in cand or "Program Files" in cand:
            continue
        rep.warn("A 路径", "旧工程残留", "配置里的绝对路径已失效：%s" % m)


# --------------------------------------------------------------------------- #
# B. 屏幕
# --------------------------------------------------------------------------- #
def _load_design(cfg):
    src = _rel(cfg, _get(cfg, "project.design_src"))
    if not src or not os.path.isfile(src):
        return None
    with open(src, "r", encoding="utf-8") as f:
        return json.load(f)


def check_screen(cfg, rep, design):
    W, H = kit.screen_size(cfg)
    if not (W and H):
        rep.err("B 屏幕", "screen.w/h", "未配置 → 越界与折行检查会被整体跳过")
        return (W, H)
    rep.ok("B 屏幕", "screen.w/h", "%d x %d" % (W, H))

    if isinstance(design, dict):
        s = design.get("screen") or {}
        dw, dh = s.get("w"), s.get("h")
        if dw and dh:
            if (dw, dh) != (W, H):
                rep.err("B 屏幕", "设计源尺寸", "设计源 %sx%s ≠ 配置 %sx%s" % (dw, dh, W, H))
            else:
                rep.ok("B 屏幕", "设计源尺寸", "设计源与设计配置一致 %dx%d" % (dw, dh))
        psz, npg = set(), 0
        for p in (design.get("pages") or []):
            if isinstance(p, dict) and p.get("width") and p.get("height"):
                npg += 1
                psz.add((p["width"], p["height"]))
        bad = sorted(s for s in psz if s != (W, H))
        if bad:
            rep.warn("B 屏幕", "各页尺寸", "%d 个页尺寸与屏幕不一致：%s" % (len(bad), bad[:3]))
        elif psz:
            rep.ok("B 屏幕", "各页尺寸", "%d 页全部 %dx%d" % (npg, W, H))

    pf = _rel(cfg, _get(cfg, "project.project_file"))
    if pf and os.path.isfile(pf):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                proj = json.load(f)
            lv = (((proj.get("settings") or {}).get("general") or {})
                  .get("display") or {})
            pw, ph = lv.get("displayWidth"), lv.get("displayHeight")
            if pw and ph and (int(pw), int(ph)) != (W, H):
                rep.err("B 屏幕", "目标工程尺寸",
                        "EEZ 工程 %sx%s ≠ 配置 %sx%s" % (pw, ph, W, H))
            elif pw and ph:
                rep.ok("B 屏幕", "目标工程尺寸", "EEZ 工程一致 %sx%s" % (pw, ph))
        except Exception as e:
            rep.warn("B 屏幕", "目标工程尺寸", "读不了工程文件：%s" % e)
    return (W, H)


# --------------------------------------------------------------------------- #
# C. 字体
# --------------------------------------------------------------------------- #
def _collect_nodes(design, sch):
    """返回 (所有节点 list, 文本 list)"""
    nodes, texts = [], []

    def walk(n):
        if not isinstance(n, dict):
            return
        nodes.append(n)
        t = n.get(sch.get("text", "text"))
        if isinstance(t, str):
            texts.append(t)
        for c in n.get(sch.get("children", "children")) or []:
            walk(c)

    pages = design or {}
    lst = pages.get("pages") if isinstance(pages, dict) else pages
    for p in (lst or []):
        if isinstance(p, dict):
            walk(p.get(sch.get("page_root", "screen"), p))
    return nodes, texts


def check_fonts(cfg, rep, design):
    n2p = _get(cfg, "fonts.name_to_px", {}) or {}
    rep.ok("C 字体", "name_to_px", "%d 种字号：%s" % (len(n2p), sorted(n2p.values())))

    # 设计源实际用到的字体
    sch = _get(cfg, "tree_schema", {}) or {}
    nodes, texts = _collect_nodes(design, sch) if design else ([], [])
    fontkey = sch.get("font", "font")
    used = sorted({n[fontkey] for n in nodes if isinstance(n.get(fontkey), str)})
    unknown = [f for f in used if f not in n2p]
    if unknown:
        # 内置字体是允许的
        really = [f for f in unknown if not kit.is_builtin_font(cfg, f)]
        if really:
            rep.err("C 字体", "未登记字号", "设计源用到但 name_to_px 里没有：%s" % really)
        else:
            rep.ok("C 字体", "未登记字号", "%s 均为内置字体，不需要登记" % unknown)
    else:
        rep.ok("C 字体", "设计源字体", "%d 种字体全部已登记" % len(used))

    # 图标私有区 vs 实际图标字符
    ranges = _get(cfg, "fonts.icon_private_ranges", []) or []
    chars = set()
    for t in texts:
        chars.update(t)
    for n in nodes:
        for key in ("glyphs",):
            v = n.get(key)
            if isinstance(v, str):
                chars.update(v)
    # 把目标工程里声明的 symbol 也算进去（EEZ 侧的权威集合）
    pf = _rel(cfg, _get(cfg, "project.project_file"))
    if pf and os.path.isfile(pf):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                proj = json.load(f)
            for fnt in (proj.get("fonts") or []):
                for s in (fnt.get("lvglAdditionalSources") or []):
                    chars.update(s.get("lvglSymbols") or "")
                chars.update(fnt.get("lvglSymbols") or "")
        except Exception:
            pass

    def in_range(c):
        o = ord(c)
        return any(a <= o <= b for a, b in ranges)

    icons = sorted(c for c in chars if 0xE000 <= ord(c) <= 0xF8FF or ord(c) >= 0xF0000)
    outside = [c for c in icons if not in_range(c)]
    if icons and outside:
        rep.err("C 字体", "图标私有区",
                "%d 个图标字符落在 icon_private_ranges 之外：%s"
                % (len(outside), " ".join("U+%04X" % ord(c) for c in outside[:12])))
    elif icons:
        rep.ok("C 字体", "图标私有区", "%d 个图标字符全部落在私有区内 %s"
               % (len(icons), ranges))

    # 实测数据：bk领域的 font_metrics / ink_offset
    has_metrics = bool(_get(cfg, "fonts.metrics"))
    has_ink = bool(_get(cfg, "fonts.ink_offset_from_box_top"))
    if has_ink:
        rep.ok("C 字体", "墨迹偏移", "已填实测值，越界判定按真实字形框")
    else:
        # tree_check 已支持在无该配置时自动用 PIL 实测墨迹框，故这里只是精度提示而非错误
        rep.info("C 字体", "墨迹偏移",
                 "未配 fonts.ink_offset_from_box_top → tree_check 自动回落到 "
                 "PIL 实测字形墨迹框（比 y+1..y+px+1 的旧保守估计更严）")
    if not has_metrics:
        rep.info("C 字体", "fonts.metrics", "为空（当前工具用 device_ttf + PIL 实测）")


# --------------------------------------------------------------------------- #
# D. 结构
# --------------------------------------------------------------------------- #
def check_schema(cfg, rep, design):
    sch = _get(cfg, "tree_schema", {}) or {}
    if not isinstance(design, dict):
        rep.err("D 结构", "设计源", "读不到设计源，无法核对 tree_schema")
        return

    # 顶层 pages 容器
    key = (sch.get("pages") or ["pages"])[0]
    if key in design:
        rep.ok("D 结构", "pages 容器", "'%s' 命中（%d 页）"
               % (key, len(design.get(key) or [])))
    else:
        rep.err("D 结构", "pages 容器", "设计源里没有 '%s' 键 → 组件树遍历为空" % key)
        return

    pages = design.get(key) or []
    first = pages[0] if pages and isinstance(pages[0], dict) else {}
    pn = sch.get("page_name", "name")
    pr = sch.get("page_root", "screen")
    if pn in first:
        rep.ok("D 结构", "page_name", "'%s' 命中，第一页 = %r" % (pn, first.get(pn)))
    else:
        rep.err("D 结构", "page_name", "'%s' 不是页对象的键（实际键：%s）"
                % (pn, list(first.keys())))
    if pr in first:
        rep.ok("D 结构", "page_root", "'%s' 命中" % pr)
    else:
        rep.err("D 结构", "page_root", "'%s' 不是页根节点的键（实际键：%s）"
                % (pr, list(first.keys())))

    # 入口页
    entry = _get(cfg, "checks.entry_page")
    names = [p.get(pn) for p in pages if isinstance(p, dict)]
    if entry:
        if entry == names[0]:
            rep.ok("D 结构", "entry_page", "%r 是第一页" % entry)
        elif entry in names:
            rep.warn("D 结构", "entry_page", "%r 存在但不是第一页（第一页是 %r）"
                     % (entry, names[0]))
        else:
            rep.err("D 结构", "entry_page", "%r 不在页面列表 %s 里" % (entry, names))

    # 节点字段键名覆盖率（抽样所有节点）
    nodes, _texts = _collect_nodes(design, sch)
    total = len(nodes)
    for name, k in (("x", sch.get("x", "x")), ("y", sch.get("y", "y")),
                    ("w", sch.get("w", "w")), ("h", sch.get("h", "h")),
                    ("children", sch.get("children", "children")),
                    ("type", sch.get("type", "type"))):
        hit = sum(1 for n in nodes if k in n)
        if name == "children":
            hit = sum(1 for n in nodes if n.get(k) or k in n)
        if hit == 0 and total:
            rep.err("D 结构", "键 '%s'" % name,
                    "%d 个节点里 0 个有键 '%s' → 该维度检查全部失效" % (total, k))
        elif total and hit < total * 0.5:
            rep.warn("D 结构", "键 '%s'" % name, "只 %d/%d 个节点有 '%s'" % (hit, total, k))
        else:
            rep.ok("D 结构", "键 '%s'" % name, "%d/%d 个节点有 '%s'" % (hit, total, k))

    for name, k in (("text", sch.get("text", "text")),
                    ("goto", sch.get("goto", "goto")),
                    ("font", sch.get("font", "font")),
                    ("image", sch.get("image", "image"))):
        hit = sum(1 for n in nodes if isinstance(n.get(k), str) and n.get(k))
        if hit == 0:
            rep.info("D 结构", "键 '%s'" % name, "没有节点用到 '%s'（可能本工程无此字段）" % k)
        else:
            rep.ok("D 结构", "键 '%s'" % name, "%d 个节点用到 '%s'" % (hit, k))

    # 类型分布 vs 声明类型
    tk = sch.get("type", "type")
    real = {}
    for n in nodes:
        t = n.get(tk)
        if isinstance(t, str):
            real[t] = real.get(t, 0) + 1
    declared = (sch.get("type_values") or {})
    missing = sorted(set(real) - set(declared.values()) - {""})
    if missing:
        rep.warn("D 结构", "type_values",
                 "设计源还有这些类型未在 type_values 声明：%s；"
                 "tree_check 靠遍历而非类型过滤仍能查到，但 G2 的 nav_types 判定会漏"
                 % ", ".join("%s(%d)" % (t, real[t]) for t in missing))
    else:
        rep.ok("D 结构", "type_values", "声明类型已覆盖设计源全部类型 %s"
               % sorted(real.items()))

    nav = sch.get("nav_types") or []
    if nav:
        rep.info("D 结构", "nav_types", "%s（用于 G2 跳转体检）" % nav)
    tabs = _get(cfg, "checks.tab_bar")
    if tabs is None:
        rep.info("D 结构", "tab_bar", "未配置 → A5/A7 底栏类断言自动跳过（本工程非底栏形态）")


# --------------------------------------------------------------------------- #
# E. 门禁
# --------------------------------------------------------------------------- #
def check_gates(cfg, rep):
    gates = _get(cfg, "checks.gates", []) or []
    if not gates:
        rep.warn("E 门禁", "gates", "一条都没挂 → 只会跑内置的 G1/G4")
    for g in gates:
        code = g.get("code", "?")
        script = _rel(cfg, g.get("script"))
        if script and os.path.exists(script):
            need = "需要 PIL" if g.get("need_pil") else ""
            rep.ok("E 门禁", code, "%s 存在 %s" % (g.get("script"), need))
        else:
            rep.warn("E 门禁", code, "脚本不存在，会被 SKIP：%s" % g.get("script"))

    for code, script in (("G2", "./design/check_nav.py"),):
        if any(c for c in gates if g.get("code") == code):
            continue
        p = _rel(cfg, script)
        if os.path.exists(p):
            rep.warn("E 门禁", code, "脚本存在但没挂进 checks.gates → 从不执行")
        else:
            rep.info("E 门禁", code, "本工程未提供 %s（该闸门不参与）" % script)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="工程配置适配体检（ui_debug_kit）")
    ap.add_argument("--config", default=None)
    ap.add_argument("--strict", action="store_true", help="WARN 也算不通过")
    args = ap.parse_args()

    cfg = kit.load_config(args.config)
    cfg["__path__"] = os.path.abspath(args.config or _find_config())
    rep = Report()

    print("=" * 72)
    print("UI 配置适配体检")
    print("=" * 72)
    print("  配置：%s" % cfg["__path__"])
    print("  工程：%s" % _get(cfg, "project.name", "?"))
    print()

    design = _load_design(cfg)
    if design is None:
        rep.err("A 路径", "project.design_src", "设计源读不到，后续 C/D 项无法核对")

    check_paths(cfg, rep)
    check_screen(cfg, rep, design)
    check_fonts(cfg, rep, design)
    check_schema(cfg, rep, design)
    check_gates(cfg, rep)

    cur_g = None
    for lv, g, item, detail in rep.rows:
        if g != cur_g:
            print("\n【%s】" % g)
            cur_g = g
        mark = {"OK": "  ✓", "WARN": "  ⚠", "ERROR": "  ✗", "INFO": "  ·"}[lv]
        print("%s %-16s %s" % (mark, item, detail))

    n = rep.summary()
    print("\n" + "-" * 72)
    print("  OK %d / WARN %d / ERROR %d / INFO %d"
          % (n["OK"], n["WARN"], n["ERROR"], n["INFO"]))
    if n["ERROR"]:
        print("  → 配置未适配：上面标 ✗ 的项会让门禁漏检或误判，必须先修。")
    elif n["WARN"] and args.strict:
        print("  → 无致命项，但 --strict 下有 WARN。")
    elif n["WARN"]:
        print("  → 主体已适配，WARN 是精度损失或功能未挂，不影响结论成立。")
    else:
        print("  → 完全适配。")
    print("-" * 72)
    return 1 if (n["ERROR"] or (args.strict and n["WARN"])) else 0


def _find_config():
    return kit.PROJECT_CONFIG_NAME


if __name__ == "__main__":
    sys.exit(main())
