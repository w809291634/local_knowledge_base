# -*- coding: utf-8 -*-
"""
audit_ui.py —— 回归断言集（只读，不改任何文件）

定位：把过去踩过的每一个坑固化成一条**可执行断言**，改 UI 时不会再重犯。
每条断言都对应一个真实出过问题的案例，注释里写明「不这么写会怎样」。

检查项（A1~A10，编号稳定，便于在报告里引用）：
  A1 字体名一致性  设计源里的字体名必须在「已声明字体」中（否则静默回退默认字号）
  A2 字体基线      工程声明的 ascent 必须等于实测值 line_height - base_line
  A3 主题内边距    会吃默认主题偏移的控件类型，必须显式写 pad_* = 0
  A4 文本对齐      禁止「固定宽度 + text_align 居中/右对齐」（保存时会重算成负数）
  A5 底栏侵占      带底栏的页，其它元素不得压进底栏区（否则点它跳去了底栏）
  A6 字体开关      生成代码引用的字体，必须在运行时配置里开启（否则真机编译失败）
  A7 当前页标记    「高亮项」不等于「当前页」，设计源里必须显式传当前页名
  A8 链路忠实性    设计源跳转数 == 工程连线数 == 生成代码回调数
  A9 部件开关      生成代码用到的 LVGL 部件，必须在运行时配置里开启（A6 的「部件版」）
  A10 样式值语法   颜色等样式值必须符合目标框架的取值语法（写错时工具多半静默忽略）

一切路径与阈值都来自 ui_debug_kit.config.json，**脚本内不含任何工程信息**。
缺哪份输入，对应项就自动跳过（打印"跳过"而不是报错）。

用法：
    python audit_ui.py              # 全量
    python audit_ui.py A3 A6        # 只跑指定项
退出码：0 = 无 ERROR；1 = 有 ERROR（WARN 不阻断）
"""
import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

ERRORS, WARNS = [], []


def err(code, msg):
    ERRORS.append("[%s] %s" % (code, msg))


def warn(code, msg):
    WARNS.append("[%s] %s" % (code, msg))


# --------------------------------------------------------------------------- #
# 通用读取
# --------------------------------------------------------------------------- #

def sch(cfg):
    """tree_schema 归一化：字段映射 + 类型取值 + 样式路径。换框架只改配置。"""
    s = cfg.get("tree_schema", {}) or {}
    tv = s.get("type_values", {}) or {}
    return {
        "children": s.get("children", "children"),
        "x": s.get("x", "x"), "y": s.get("y", "y"),
        "w": s.get("w", "w"), "h": s.get("h", "h"),
        "type": s.get("type", "type"), "text": s.get("text", "text"),
        "font": s.get("font", "font"), "goto": s.get("goto", "goto"),
        "container": tv.get("container", "container"),
        "button": tv.get("button", "button"),
        "label": tv.get("label", "label"),
        "style_key": s.get("style_key", "style"),
        "main_part": s.get("main_part", "MAIN"),
        "default_state": s.get("default_state", "DEFAULT"),
        "width_unit_key": s.get("width_unit_key", "wUnit"),
        "content_unit_value": s.get("content_unit_value", "content"),
        "nav_types": s.get("nav_types", [tv.get("button", "button")]),
    }


def num(node, key, default=0):
    try:
        return int(node.get(key) or default)
    except (TypeError, ValueError):
        return default


def walk(node, sch_, parent=(0, 0), depth=0, skip=None):
    """递归组件树，yield (绝对x, 绝对y, 节点, 深度)。skip 子树整体跳过。"""
    if not isinstance(node, dict):
        return
    if skip is not None and node is skip:
        return
    ax = parent[0] + num(node, sch_["x"])
    ay = parent[1] + num(node, sch_["y"])
    yield ax, ay, node, depth
    for c in (node.get(sch_["children"]) or []):
        for r in walk(c, sch_, (ax, ay), depth + 1, skip):
            yield r


def style_main(node, sch_):
    """取节点 MAIN/DEFAULT 下的样式字典（兼容直接平铺在 style 上的写法）。"""
    st = node.get(sch_["style_key"]) or {}
    if sch_["main_part"] in st:
        st = (st.get(sch_["main_part"]) or {}).get(sch_["default_state"]) or {}
    return st if isinstance(st, dict) else {}


def pages_of(cfg):
    return kit.load_pages(cfg)


def tabbar_rule(cfg):
    """底栏识别规则 {y,h,w}；未配置返回 None（A5 跳过）。

    注意：y<=0 一律视为"未配置"——底栏（页面底部那条）不可能从 y=0 开始；
    模板里 checks.tab_bar 的占位值就是 {y:0,...}，若不这样判，新工程忘了改就会
    把 y=0 的页根/顶栏当成底栏，导致 A5 误报或静默失效。
    """
    t = (cfg.get("checks") or {}).get("tab_bar")
    if not isinstance(t, dict) or "y" not in t:
        return None
    if int(t.get("y", 0) or 0) <= 0:
        return None
    W, _ = kit.screen_size(cfg)
    return {"y": int(t["y"]), "h": int(t.get("h", 0) or 0),
            "w": int(t.get("w", W or 0) or 0)}


def font_c_files(cfg):
    """实测字体 C 文件列表（用于算真实基线）。"""
    pat = kit.cfg_path(cfg, "paths.font_c")
    if not pat:
        g = kit.cfg_path(cfg, "project.gen_dir")
        pat = os.path.join(g, "ui_font_*.c") if g else None
    if not pat:
        return []
    return sorted(glob.glob(pat))


# --------------------------------------------------------------------------- #
# A1 字体名一致性
# --------------------------------------------------------------------------- #

def a1_font_names(cfg, code="A1"):
    """不检查会怎样：字体名拼错时工具链大多不报错，而是静默回退成默认字号 ——
    「大标题变成小字」，肉眼看只是有点怪，极难定位。"""
    known, is_builtin = kit.font_names(cfg)
    s = sch(cfg)
    bad = []
    for name, root in pages_of(cfg):
        for _ax, _ay, n, _d in walk(root, s):
            for key in (s["font"], "text_font"):
                v = n.get(key)
                if v and v not in known and not is_builtin(v):
                    bad.append((name, key, v))
            tf = style_main(n, s).get("text_font") or n.get(s["style_key"], {}).get("text_font") \
                if isinstance(n.get(s["style_key"]), dict) else None
            if tf and tf not in known and not is_builtin(tf):
                bad.append((name, "style.text_font", tf))
    for pg, k, v in bad:
        err(code, "%-12s %s = %s 不在已声明字体中" % (pg, k, v))
    print("  %s 字体名一致性   : %s" % (code, "OK" if not bad else "%d 处未知字体" % len(bad)))


# --------------------------------------------------------------------------- #
# A2 字体基线
# --------------------------------------------------------------------------- #

def a2_font_baseline(cfg, code="A2"):
    """不检查会怎样：编辑器按它自己声明的 ascent 画字，与固件里烘焙字体的真实基线
    差几个像素 ——「文字画高了、底部超出画布」。只影响预览不影响固件，所以 WARN。"""
    measured = {}
    for path in font_c_files(cfg):
        txt = io.open(path, encoding="utf-8", errors="ignore").read()
        lh = re.search(r"\.line_height\s*=\s*(\d+)", txt)
        bl = re.search(r"\.base_line\s*=\s*(\d+)", txt)
        if lh and bl:
            measured[os.path.basename(path).lower()] = int(lh.group(1)) - int(bl.group(1))
    if not measured:
        m = (cfg.get("fonts") or {}).get("metrics") or {}
        for px, v in m.items():                      # 退回配置里的实测值
            if isinstance(v, dict) and "line_height" in v and "base_line" in v:
                for nm, p in ((cfg.get("fonts") or {}).get("name_to_px") or {}).items():
                    if str(p) == str(px):
                        measured["ui_font_%s.c" % nm.lower()] = int(v["line_height"]) - int(v["base_line"])
    if not measured:
        print("  %s 字体基线       : 跳过（未找到字体 C，也未配 fonts.metrics）" % code)
        return

    pf = kit.cfg_path(cfg, "project.project_file")
    decl = []
    if pf and os.path.isfile(pf):
        try:
            decl = json.load(io.open(pf, encoding="utf-8")).get("fonts") or []
        except Exception:
            decl = []
    bad = []
    for f in decl:
        if not isinstance(f, dict):
            continue
        nm = f.get("name") or ""
        asc = f.get("ascent")
        real = measured.get("ui_font_%s.c" % nm.lower())
        if real is not None and asc is not None and int(asc) != real:
            bad.append((nm, asc, real))
    for nm, got, real in bad:
        warn(code, "%-28s ascent=%s，实测应为 %d（预览偏 %+dpx）"
             % (nm, got, real, (int(got) if got else 0) - real))
    print("  %s 字体基线       : %s" % (code, "OK" if not bad else "%d 项不符（WARN）" % len(bad)))


# --------------------------------------------------------------------------- #
# A3 默认主题内边距
# --------------------------------------------------------------------------- #

def a3_theme_padding(cfg, code="A3"):
    """不检查会怎样：默认主题给某些控件类型加内边距，子控件整体偏移 ——
    「工程坐标 != 渲染坐标」，文字被推出画布、图标挤出按钮外。
    哪些类型会偏移由 theme_defaults 决定；偏移为 0 的框架本项自动跳过。"""
    th = (cfg.get("theme_defaults") or {})
    risky = [t for t, v in th.items()
             if isinstance(v, dict) and (int(v.get("dx", 0) or 0) or int(v.get("dy", 0) or 0))]
    if not risky:
        print("  %s 主题内边距     : 跳过（theme_defaults 全为 0，该框架无此坑）" % code)
        return
    s = sch(cfg)
    pads = ["pad_top", "pad_bottom", "pad_left", "pad_right"]
    bad = []
    for pname, root in pages_of(cfg):
        for _ax, _ay, n, _d in walk(root, s):
            if n.get(s["type"]) not in risky:
                continue
            main = style_main(n, s)
            for k in pads:
                if str(main.get(k, "")).strip() != "0":
                    bad.append((pname, n.get(s["type"]), k, main.get(k)))
    for pg, t, k, v in bad:
        err(code, "%-12s %s 的 %s = %r，必须为 \"0\"" % (pg, t, k, v))
    print("  %s 主题内边距     : %s" % (code, "OK" if not bad else "%d 处缺失" % len(bad)))


# --------------------------------------------------------------------------- #
# A4 文本对齐
# --------------------------------------------------------------------------- #

def a4_text_align(cfg, code="A4"):
    """不检查会怎样：用「固定宽度 + text_align 居中」做对齐时，工具链保存工程会按
    它自己的字宽重算 left，可能算出负数 —— 文字直接跑出画布左边。
    正确做法是 content 宽度 + 按真实文本宽度算出的 x。"""
    s = sch(cfg)
    bad = []
    for pname, root in pages_of(cfg):
        for _ax, _ay, n, _d in walk(root, s):
            if n.get(s["type"]) != s["label"]:
                continue
            if s["width_unit_key"] and n.get(s["width_unit_key"]) == s["content_unit_value"]:
                continue
            st = style_main(n, s)
            ta = str(st.get("text_align") or n.get("text_align") or "").upper()
            if ta in ("CENTER", "RIGHT"):
                bad.append((pname, n.get(s["text"]) or "", ta))
    for pg, t, ta in bad:
        err(code, "%-12s label「%s」固定宽 + text_align=%s（改用 content 宽 + 算 x）"
            % (pg, t[:10], ta))
    print("  %s 文本对齐       : %s" % (code, "OK" if not bad else "%d 处风险" % len(bad)))


# --------------------------------------------------------------------------- #
# A5 底栏侵占
# --------------------------------------------------------------------------- #

def a5_tabbar_overlap(cfg, code="A5"):
    """不检查会怎样：列表行压进底栏区域，点击时命中层级更高的底栏按钮 ——
    用户点「通用设置」，画面却跳去了别的页。这是「点了画面来回跳」的头号成因。"""
    rule = tabbar_rule(cfg)
    if not rule:
        print("  %s 底栏侵占       : 跳过（未配 checks.tab_bar）" % code)
        return
    s = sch(cfg)
    bad = []
    for pname, root in pages_of(cfg):
        tab = None
        for _ax, ay, n, _d in walk(root, s):
            if (n.get(s["type"]) == s["container"] and ay == rule["y"]
                    and (not rule["h"] or num(n, s["h"]) == rule["h"])
                    and (not rule["w"] or num(n, s["w"]) == rule["w"])):
                tab = n
                break
        if tab is None:
            continue
        for _ax, ay, n, d in walk(root, s, skip=tab):
            if n is root or d == 0:
                continue
            bottom = ay + num(n, s["h"])
            if bottom > rule["y"]:
                bad.append((pname, n.get(s["type"]), ay, bottom))
    for pg, t, top, bot in bad:
        err(code, "%-12s %s 占据 y=%d..%d，压进底栏(y>=%d)" % (pg, t, top, bot, rule["y"]))
    print("  %s 底栏侵占       : %s" % (code, "OK" if not bad else "%d 处重叠" % len(bad)))


# --------------------------------------------------------------------------- #
# A6 字体开关
# --------------------------------------------------------------------------- #

def strip_font_guards(text):
    """去掉 `#if LV_FONT_X ... #endif` 整块。

    为什么必须这样做：生成器给「内置字体查表」加的就是这层保护 ——
    `#if LV_FONT_MONTSERRAT_8 / { "MONTSERRAT_8", &lv_font_montserrat_8 } / #endif`。
    这种引用在开关为 0 时**根本不会编译进去**，不是「引用但未开启」。
    早期版本直接全文正则匹配，于是每次都在有守护的字体上报假阳性。
    """
    out, stack = [], []
    for line in text.splitlines():
        st = line.strip()
        if re.match(r"#\s*if", st):
            stack.append(bool(re.match(r"#\s*if\s+LV_FONT_", st)))
            out.append("")
            continue
        if re.match(r"#\s*endif", st):
            if stack:
                stack.pop()
            out.append("")
            continue
        out.append("" if any(stack) else line)
    return "\n".join(out)


def a6_font_switches(cfg, code="A6"):
    """不检查会怎样：生成代码引用了某字体，但运行时配置里开关是 0 ——
    PC 模拟器能编过（模拟器那份配置不同），真机直接报 undeclared。
    典型「本地能跑、上机炸」。

    两个必须的细节（都是实测踩出来的）：
      1. **先剥掉 `#if LV_FONT_X ... #endif` 守护块**：生成器给内置字体查表加的
         就是这层保护，开关为 0 时那些引用根本不会编译进去，直接全文匹配会假阳性。
      2. 工程**自烘焙**的字体符号（如 `ui_font_xxx`）不走 `LV_FONT_*` 开关，
         用 `checks.font_switch_ignore` 排除；这类字体的存在性由 A2/A8 覆盖。
    """
    gen = kit.cfg_path(cfg, "paths.screens_c") or os.path.join(
        kit.cfg_path(cfg, "project.gen_dir") or "", "screens.c")
    conf = kit.cfg_path(cfg, "paths.lv_conf") or kit.cfg_path(cfg, "paths.runtime_conf")
    if not (os.path.isfile(gen) and conf and os.path.isfile(conf)):
        print("  %s 字体开关       : 跳过（未配 paths.screens_c 或 paths.lv_conf）" % code)
        return
    prefix = (cfg.get("checks") or {}).get("font_symbol_prefix", "lv_font_")
    src = io.open(gen, encoding="utf-8", errors="ignore").read()
    if (cfg.get("checks") or {}).get("font_guard_aware", True):
        src = strip_font_guards(src)
    used = set(re.findall(re.escape(prefix) + r"([a-z0-9_]+)", src))
    text = io.open(conf, encoding="utf-8", errors="ignore").read()
    macro = (cfg.get("checks") or {}).get("font_macro", "LV_FONT_%s")
    # 工程**自烘焙**的字体（有自己的 .c 符号）不靠 LV_FONT_* 开关，用这个跳过。
    # 只有框架**内置**字体才需要开关；不配则一律按内置处理（老行为）。
    ignore = (cfg.get("checks") or {}).get("font_switch_ignore") or []
    missing, skipped = [], 0
    for name in sorted(used):
        m = re.search(r"#define\s+" + re.escape(macro % name.upper()) + r"\s+(\d)", text)
        if not m:
            if any(re.search(p, name) for p in ignore):
                skipped += 1
                continue
            missing.append((name, "未定义"))
        elif m.group(1) == "0":
            missing.append((name, "开关为 0"))
    for name, why in missing:
        err(code, "生成代码引用 %s%s，但运行时配置中%s" % (prefix, name, why))
    print("  %s 字体开关       : %s（无条件引用的内置字体 %d 种%s）"
          % (code, "OK" if not missing else "%d 种未开启" % len(missing), len(used),
             "，另 %d 种在 #if 守护内已跳过" % skipped if skipped else ""))


# --------------------------------------------------------------------------- #
# A7 当前页标记
# --------------------------------------------------------------------------- #

def a7_current_page_marker(cfg, code="A7"):
    """不检查会怎样：底栏的「高亮项」只表示点亮的图标，不等于「当前是哪一屏」。
    二级页也带底栏但当前页并不是那个 Tab，若用「索引 != 高亮索引」判断，
    就会误删它们回主页的正常跳转。必须显式传当前页名。"""
    builder = kit.cfg_path(cfg, "project.builder")
    if not (builder and os.path.isfile(builder)):
        print("  %s 当前页标记     : 跳过（未配 project.builder）" % code)
        return
    src = io.open(builder, encoding="utf-8").read()
    pat = (cfg.get("checks") or {}).get("current_page_marker")
    pat = pat or r'tabbar\(\s*\d+\s*,\s*cur\s*=\s*[\'"](\w+)[\'"]'
    fn2page = dict((b, a) for a, b in re.findall(r'\("(\w+)",\s*(s\d+)\)', src))
    bad, cur, hits = [], None, 0
    for line in src.split("\n"):
        m = re.match(r"def (s\d+)\(\):", line)
        if m:
            cur = m.group(1)
            continue
        if "tabbar(" in line and not line.strip().startswith("def tabbar"):
            hits += 1
            page = fn2page.get(cur)
            cm = re.search(pat, line)
            if not cm:
                bad.append((page or cur, "未显式传当前页名"))
            elif page and cm.group(1) != page:
                bad.append((page, "当前页=%s 与实际页名不符" % cm.group(1)))
    for pg, why in bad:
        err(code, "%-12s 底栏 %s" % (pg, why))
    if not hits:
        print("  %s 当前页标记     : 跳过（生成器里没有匹配 %r 的调用 —— 该工程可能不是"
              "『底栏 Tab』形态，无需显式传当前页名）" % (code, pat))
        return
    print("  %s 当前页标记     : %s（检查 %d 处）"
          % (code, "OK" if not bad else "%d 处不符" % len(bad), hits))


# --------------------------------------------------------------------------- #
# A8 链路忠实性
# --------------------------------------------------------------------------- #

def a8_chain_parity(cfg, code="A8"):
    """不检查会怎样：设计源改了但忘了重新生成，或生成半途失败，产物停留在旧版本 ——
    效果图上的按钮上机根本没有。数量对账 1 秒发现问题。
    （数量一致不代表内容一致，但数量不一致一定是链路断了）"""
    s = sch(cfg)
    chk = cfg.get("checks") or {}
    dsl_n = 0
    for _name, root in pages_of(cfg):
        for _ax, _ay, n, _d in walk(root, s):
            if n.get(s["goto"]):
                dsl_n += 1

    nums = {"design": dsl_n}
    pf = kit.cfg_path(cfg, "project.project_file")
    if pf and os.path.isfile(pf):
        try:
            data = json.load(io.open(pf, encoding="utf-8"))
            key = chk.get("links_key", "connectionLines")
            container = chk.get("links_container", "userPages")
            items = data if container in (None, "", "root") else (data.get(container) or [])
            nums["project"] = sum(len(p.get(key) or []) for p in items if isinstance(p, dict))
        except Exception:
            pass

    gen = kit.cfg_path(cfg, "paths.screens_c") or os.path.join(
        kit.cfg_path(cfg, "project.gen_dir") or "", "screens.c")
    if os.path.isfile(gen):
        pat = chk.get("event_cb_pattern", "lv_obj_add_event_cb")
        nums["code"] = len(re.findall(re.escape(pat),
                                      io.open(gen, encoding="utf-8", errors="ignore").read()))

    ok = len(set(nums.values())) == 1
    if not ok:
        err(code, "三层数量不一致 %s（应为 设计源 == 工程 == 生成代码）" % nums)
    print("  %s 链路忠实性     : %s  %s" % (code, "OK" if ok else "不一致", nums))


# --------------------------------------------------------------------------- #
# A9 LVGL 部件开关
# --------------------------------------------------------------------------- #

# 核心/基类部件，没有对应的 LV_USE_* 开关，不参与检查
_CORE_CREATORS = {"obj", "screen"}


def widget_c_files(cfg):
    """参与扫描的生成 C 文件：screens.c + gen_dir 下除字体/图片外的 .c。"""
    out = []
    sc = kit.cfg_path(cfg, "paths.screens_c")
    if sc and os.path.isfile(sc):
        out.append(sc)
    g = kit.cfg_path(cfg, "project.gen_dir")
    if g and os.path.isdir(g):
        for p in sorted(glob.glob(os.path.join(g, "*.c"))):
            b = os.path.basename(p).lower()
            if b.startswith(("ui_font_", "ui_image_")) or p in out:
                continue
            out.append(p)
    return out


def a9_widget_switches(cfg, code="A9"):
    """不检查会怎样：生成代码调用了某部件（如 `lv_switch_create`），
    但运行时配置里该部件的开关（`LV_USE_SWITCH`）是 0 —— 模拟器那份 lv_conf.h
    不一定与工程同步，典型「本地能跑、上机炸」。A6 管字体，这条管**部件**。

    判定只针对「配置里存在该开关、但被关成 0」的情况；配置里根本没有的
    （核心部件，如 lv_obj_create）一律跳过，避免假阳性。"""
    conf = kit.cfg_path(cfg, "paths.lv_conf") or kit.cfg_path(cfg, "paths.runtime_conf")
    files = widget_c_files(cfg)
    if not (conf and os.path.isfile(conf) and files):
        print("  %s 部件开关       : 跳过（未配 paths.lv_conf 或找不到生成代码）" % code)
        return
    text = io.open(conf, encoding="utf-8", errors="ignore").read()
    used = set()
    for p in files:
        used |= set(re.findall(r"lv_([a-z0-9]+)_create\s*\(",
                               io.open(p, encoding="utf-8", errors="ignore").read()))
    used -= _CORE_CREATORS
    off = []
    for name in sorted(used):
        m = re.search(r"#define\s+" + re.escape("LV_USE_" + name.upper()) + r"\s+(\d)", text)
        if m and m.group(1) == "0":
            off.append("LV_USE_" + name.upper())
    for macro in off:
        err(code, "生成代码用到的部件在运行时配置里被关闭：%s = 0（会「本地能跑、上机炸」）" % macro)
    print("  %s 部件开关       : %s（用到 %d 种部件）"
          % (code, "OK" if not off else "%d 种被关闭" % len(off), len(used)))


# --------------------------------------------------------------------------- #
# A10 样式值语法（静默失效类）
# --------------------------------------------------------------------------- #

DEFAULT_COLOR_PROPS = ["bg_color", "bg_grad_color", "border_color", "outline_color",
                       "shadow_color", "text_color", "line_color", "arc_color",
                       "img_recolor", "img_src"]
DEFAULT_COLOR_PATTERNS = [r"^#?[0-9a-fA-F]{3,6}$", r"^0[xX][0-9a-fA-F]{6}$"]


def iter_style_props(node, sch_):
    """展开 style 下**所有** part/state 的属性（A3/A4 只看 MAIN/DEFAULT，这里要看全）。"""
    st = node.get(sch_["style_key"])
    if not isinstance(st, dict):
        return []
    out = []
    for part, states in st.items():
        if not isinstance(states, dict):
            continue
        for state, props in states.items():
            if not isinstance(props, dict):
                continue
            for k, v in props.items():
                out.append((part, state, k, v))
    return out


def a10_style_value_syntax(cfg, code="A10"):
    """不检查会怎样：**样式值写错语法时工具链大多不报错，只是忽略或只在 GUI 报**，
    产物和设计源悄悄不一致。最典型的是颜色：

        bg = 0x2a3044                # Python 里这是 int 2764868
        → 序列化后 bg_color = "2764868"   # 不是 0xRRGGBB
        → 目标工具 ColorFormat.parse 认不出 → isValid()=false
        → GUI 树上报 "invalid color"，但 **CLI 构建依然说"零错误零警告"**

    所以要按「目标框架接受的取值语法」白名单校验，别指望构建帮你拦。

    配置（都给了默认值，只在换框架时改）：
        checks.color_props            颜色类属性名（style 里的键）
        checks.color_node_keys        直接写在节点上的简写颜色键（如 DSL 的 bg/color）
        checks.color_value_patterns   合法颜色的正则白名单
    """
    chk = cfg.get("checks") or {}
    props = set(chk.get("color_props") or DEFAULT_COLOR_PROPS)
    node_keys = list(chk.get("color_node_keys") or [])
    pats = [re.compile(p) for p in (chk.get("color_value_patterns") or DEFAULT_COLOR_PATTERNS)]
    if not props and not node_keys:
        print("  %s 样式值语法     : 跳过（未配 checks.color_props / color_node_keys）" % code)
        return
    s = sch(cfg)
    bad = []

    def judge(page, where, key, val):
        if not isinstance(val, str):
            bad.append((page, where, key, val,
                        "值为 %s（%r），序列化后会变成十进制" % (type(val).__name__, val)))
            return
        t = val.strip()
        if not any(p.match(t) for p in pats):
            bad.append((page, where, key, val, "不匹配任何合法颜色格式"))

    for pname, root in pages_of(cfg):
        for _ax, _ay, n, _d in walk(root, s):
            where = "%s[%s]" % (n.get(s["type"]), n.get(s.get("id") or ""))
            for part, state, k, v in iter_style_props(n, s):
                if k in props:
                    judge(pname, "%s %s.%s" % (where, part, state), k, v)
            for k in node_keys:
                if k in n:
                    judge(pname, where, k, n[k])

    for pg, where, key, val, why in bad:
        hint = ""
        if not isinstance(val, str) and isinstance(val, int):
            hint = " ← 少写了引号（应该写成字符串 \"0x%06x\"）" % val
        err(code, "%-10s %s  %s = %r：%s%s" % (pg, where, key, val, why, hint))
    print("  %s 样式值语法     : %s" % (code, "OK" if not bad else "%d 处不合法" % len(bad)))


CHECKS = {
    "A1": a1_font_names,
    "A2": a2_font_baseline,
    "A3": a3_theme_padding,
    "A4": a4_text_align,
    "A5": a5_tabbar_overlap,
    "A6": a6_font_switches,
    "A7": a7_current_page_marker,
    "A8": a8_chain_parity,
    "A9": a9_widget_switches,
    "A10": a10_style_value_syntax,
}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="UI 回归断言集 A1~A10")
    ap.add_argument("codes", nargs="*", help="只跑指定项，如 A3 A6")
    ap.add_argument("--config", help="指定配置文件")
    args = ap.parse_args()

    cfg = kit.load_config(args.config)
    only = set(c.upper() for c in args.codes)
    print("=" * 68)
    print("回归断言集：%d 屏 / %d 条检查   [%s]"
          % (len(pages_of(cfg)), len(CHECKS), cfg["_abs"]["_config_path"]))
    print("=" * 68)
    for code in sorted(CHECKS):
        if only and code not in only:
            continue
        CHECKS[code](cfg)
    print("-" * 68)
    for w in WARNS:
        print("  WARN  " + w)
    for e in ERRORS:
        print("  ERROR " + e)
    print("-" * 68)
    print("  ERROR %d   WARN %d" % (len(ERRORS), len(WARNS)))
    if not ERRORS:
        print("  结论：无阻断项，可以进入下一层测试。")
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
