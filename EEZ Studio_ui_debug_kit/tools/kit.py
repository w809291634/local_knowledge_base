# -*- coding: utf-8 -*-
"""
kit.py —— ui_debug_kit 公共库

职责：
  - 读取 config.json（自动向上/向下查找，支持从任意工程子目录调用）
  - 路径解析（配置里可写相对路径，一律相对 config.json 所在目录）
  - 图像工具：灰度化、墨迹包围盒、触底判定、逐像素差异量化 + 热点聚类
  - 文本度量：按字符切换字体（图标私有区用图标字体）

依赖：**按需**依赖 Pillow（PIL）。
  - 纯逻辑工具（audit_ui / gen_clicks / run_gate）只用标准库，没装 Pillow 也能跑；
  - 图像类工具（tree_check / ink_check / diff_report / text_measure）用到时才检查，
    缺 Pillow 会给出明确的安装提示，而不是在 import 阶段就崩掉。

作为库使用：
    import kit
    cfg = kit.load_config()
    img = kit.open_gray(path)
    print(kit.ink_bbox(img, thr=140))
"""
import json
import os
import sys

try:
    from PIL import Image, ImageChops, ImageFont
    HAS_PIL = True
except Exception:      # pragma: no cover
    Image = ImageChops = ImageFont = None
    HAS_PIL = False


def require_pil(what=""):
    """图像/字体度量类功能的前置检查。没装 Pillow 时给出可执行的安装提示。"""
    if not HAS_PIL:
        raise RuntimeError(
            "%s需要 Pillow。请安装后重试：\n"
            "    <工程里的 venv>/Scripts/python.exe -m pip install Pillow fontTools\n"
            "或在配置 binaries.python_venv 里指定已装 Pillow 的解释器。" % (what + " " if what else ""))
    return True


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

# 配置查找顺序：
#   1) 环境变量 UI_DEBUG_KIT_CONFIG 指定的文件
#   2) 从 cwd 向上找 PROJECT_CONFIG_NAME（工程侧配置，推荐）
#   3) 从 cwd 向上找 "config.json"（简易场景）
#   4) 工具箱目录下的 "config.json"（最不推荐，会把工程信息留在工具箱里）
# 工具箱自带的是 config.template.json（纯占位符模板），不算配置。
PROJECT_CONFIG_NAME = "ui_debug_kit.config.json"
FALLBACK_CONFIG_NAME = "config.json"

# 这些键一定是"说明性文本"，不做路径解析（即使里面含 "/"）
_NON_PATH_KEYS = {"name", "platform", "note", "kind", "origin", "child_coords",
                  "design_coords", "comment", "desc", "_comment"}


def _looks_like_path(key, value):
    if not isinstance(value, str):
        return False
    if key.startswith("_") or key.endswith("_note") or key in _NON_PATH_KEYS:
        return False
    return ("/" in value or "\\" in value or value in (".", ".."))


def _walk_up_for(start, filename, limit=8):
    d = os.path.abspath(start)
    for _ in range(limit):
        p = os.path.join(d, filename)
        if os.path.isfile(p):
            return p
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def find_config(start=None):
    """定位配置文件。返回路径；找不到时抛出带指引的 FileNotFoundError。

    查找顺序：
      1) 环境变量 UI_DEBUG_KIT_CONFIG
      2) 从 start / 当前工作目录向上找 <PROJECT_CONFIG_NAME>
      3) 从 start / 当前工作目录向上找 <FALLBACK_CONFIG_NAME>
      4) 从工具箱目录向上找（覆盖"从别处调用工具箱"的情况）
    """
    env = os.environ.get("UI_DEBUG_KIT_CONFIG")
    if env and os.path.isfile(env):
        return os.path.abspath(env)

    kit_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    roots = []
    for r in (start, os.getcwd(), kit_dir):
        if r:
            r = os.path.abspath(r)
            if r not in roots:
                roots.append(r)

    for name in (PROJECT_CONFIG_NAME, FALLBACK_CONFIG_NAME):
        for r in roots:
            p = _walk_up_for(r, name)
            if p:
                return p

    raise FileNotFoundError(
        "找不到配置文件。请在【你的工程里】新建 %s（可从本工具箱的 %s 复制后填写），"
        "或用环境变量 UI_DEBUG_KIT_CONFIG 指定路径。详见 CONFIG.md。"
        % (PROJECT_CONFIG_NAME, os.path.join(kit_dir, "config.template.json")))


def load_config(path=None):
    """读配置，并把所有像路径的字符串解析成绝对路径。

    解析结果放在 cfg["_abs"] 里，键名形如 "section.key"；
    另提供 cfg["_abs"]["base"]（配置文件所在目录）与 "_config_path"。
    """
    p = os.path.abspath(path) if path else find_config()
    base = os.path.dirname(p)
    with open(p, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_abs"] = {"base": base, "_config_path": p}
    for section in ("project", "fonts", "paths"):
        for k, v in (cfg.get(section) or {}).items():
            if not _looks_like_path(k, v):
                continue
            full = v if os.path.isabs(v) else os.path.join(base, v)
            cfg["_abs"][section + "." + k] = os.path.normpath(full)
    return cfg


def cfg_path(cfg, dotted, default=None):
    """取配置里的（已解析的）路径；没有则回退到字面值。"""
    if dotted in cfg["_abs"]:
        return cfg["_abs"][dotted]
    cur = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def screen_size(cfg):
    """画布尺寸。未配置时返回 (0, 0)——调用方应据此跳过几何检查并给出提示。"""
    s = cfg.get("screen", {}) or {}
    return int(s.get("w", 0) or 0), int(s.get("h", 0) or 0)


# --------------------------------------------------------------------------- #
# 图像
# --------------------------------------------------------------------------- #

def open_gray(path):
    require_pil("读图")
    return Image.open(path).convert("L")


def in_range(img, x0, y0, x1, y1):
    """把矩形裁到图像范围内（左闭右开）。"""
    return (max(0, int(x0)), max(0, int(y0)),
            min(img.width, int(x1)), min(img.height, int(y1)))


def ink_bbox(img, x0=0, y0=0, x1=None, y1=None, thr=140):
    """返回矩形内所有"墨迹"像素的包围盒 (x0,y0,x1,y1)（闭区间）；无墨迹返回 None。

    ⚠️ 这是"实际像素"边界，不是控件框。判断越界/裁切一律用它。
    """
    x1 = img.width if x1 is None else x1
    y1 = img.height if y1 is None else y1
    b = in_range(img, x0, y0, x1, y1)
    if b[2] <= b[0] or b[3] <= b[1]:
        return None
    px = img.load()
    xs, ys, n = [], [], 0
    for y in range(b[1], b[3]):
        for x in range(b[0], b[2]):
            if px[x, y] > thr:
                xs.append(x); ys.append(y); n += 1
    if not n:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def row_profile(img, x0=0, x1=None, thr=140):
    """返回每行的墨迹像素数列表（用于看"哪一行有内容"）。"""
    x1 = img.width if x1 is None else x1
    b = in_range(img, x0, 0, x1, img.height)
    px = img.load()
    return [sum(1 for x in range(b[0], b[2]) if px[x, y] > thr) for y in range(img.height)]


def col_profile(img, y0=0, y1=None, thr=140):
    """返回每列的墨迹像素数列表。"""
    y1 = img.height if y1 is None else y1
    b = in_range(img, 0, y0, img.width, y1)
    px = img.load()
    return [sum(1 for y in range(b[1], b[3]) if px[x, y] > thr) for x in range(img.width)]


def is_uniform_row(img, y, tol=2):
    """该行是否"整行近似同色"→ 通常是分隔线/底色，不是内容。"""
    px = img.load()
    first = px[0, y]
    lo = hi = first
    for x in range(1, img.width):
        v = px[x, y]
        if v < lo: lo = v
        if v > hi: hi = v
        if hi - lo > tol:
            return False
    return True


def edge_touch(img, side, thr=140, min_count=10, skip_uniform=True):
    """边界（last 行/列）是否还有内容墨迹。

    side: 'bottom' | 'top' | 'left' | 'right'
    返回 (bool, 命中的墨迹像素数)。整行/列近似同色时视为分隔线，返回 False。
    """
    side = side.lower()
    if side in ("bottom", "top"):
        y = img.height - 1 if side == "bottom" else 0
        if skip_uniform and is_uniform_row(img, y):
            return False, 0
        cnt = sum(1 for x in range(img.width) if img.getpixel((x, y)) > thr)
    else:
        x = img.width - 1 if side == "right" else 0
        cnt = sum(1 for y in range(img.height) if img.getpixel((x, y)) > thr)
    return cnt >= min_count, cnt


def diff_report(ref_path, act_path, grid=40, big_thr=64, mid_thr=24, gray=True):
    """逐像素差异量化。

    返回 dict:
      big / mid   : 差异像素数
      pct         : big 占全图百分比
      hot         : 热点区域 [(x0,y0,count), ...]（按 grid 分块聚类）
      bbox        : 差异区域的包围盒（big 阈值下）
      size_ok     : 两图尺寸是否一致
    """
    require_pil("图像差异比对")
    a = Image.open(ref_path)
    b = Image.open(act_path)
    size_ok = (a.size == b.size)
    if gray:
        a = a.convert("L"); b = b.convert("L")
    else:
        a = a.convert("RGB"); b = b.convert("RGB")
    if not size_ok:
        b = b.resize(a.size)          # 显式缩放，并在结果里标注 size_ok=False
    dif = ImageChops.difference(a, b)
    if dif.mode != "L":
        dif = dif.convert("L")
    hist = dif.histogram()
    total = a.width * a.height
    big = sum(hist[big_thr:])
    mid = sum(hist[mid_thr:big_thr])
    px = dif.load()
    pts = [(x, y) for y in range(dif.height) for x in range(dif.width) if px[x, y] >= big_thr]
    from collections import Counter
    hot = Counter(((x // grid * grid, y // grid * grid) for x, y in pts)).most_common(10)
    bbox = None
    if pts:
        bbox = (min(p[0] for p in pts), min(p[1] for p in pts),
                max(p[0] for p in pts), max(p[1] for p in pts))
    return {"big": big, "mid": mid, "pct": (100.0 * big / total if total else 0.0),
            "hot": hot, "bbox": bbox, "size_ok": size_ok,
            "size_ref": a.size, "size_act": Image.open(act_path).size}


# --------------------------------------------------------------------------- #
# 文本度量
# --------------------------------------------------------------------------- #

def is_icon_char(ch, ranges=None):
    """是否落在图标/符号私有区（默认：U+E000..U+F8FF 与 emoji 区）。"""
    cp = ord(ch)
    for lo, hi in (ranges or [(0xE000, 0xF8FF), (0x1F300, 0x1FAFF)]):
        if lo <= cp <= hi:
            return True
    return False


class TextMeasurer(object):
    """按字符切换字体：图标字符用图标字体，其余用正文字体。

    用法：
        tm = TextMeasurer(cfg)
        w = tm.width("首页", 14)                 # 净宽（用于居中）
        w2 = tm.width("首页", 14, margin=True)   # 含 8px 防换行余量（用于换行判定）
    """

    def __init__(self, cfg=None, fallback_px=14, margin_px=8):
        self.cfg = cfg or load_config()
        f = self.cfg.get("fonts", {}) or {}
        self.ttf = cfg_path(self.cfg, "fonts.device_ttf")
        self.icon_ttf = cfg_path(self.cfg, "fonts.icon_ttf")
        self.name_to_px = {k: int(v) for k, v in (f.get("name_to_px") or {}).items()}
        self.builtin_patterns = f.get("builtin_patterns") or ["*_*"]
        self.icon_ranges = f.get("icon_private_ranges")
        self.fallback_px = int(fallback_px)
        self.margin_px = int(margin_px)
        self._cache = {}
        self._icon_cache = {}

    def px_of(self, font_name, size=None):
        """字体名 → 像素大小。

        规则（按优先级）：
          1) 命中 name_to_px → 用它
          2) 名字形如 <前缀>_<数字> 且前缀命中 builtin_patterns → 取数字
             （内置字体常这样命名，由运行时自带，不需要在工程里声明）
          3) 显式传入的 size
          4) fallback_px（会由 CLI 给出告警）
        """
        if font_name in self.name_to_px:
            return self.name_to_px[font_name]
        if isinstance(font_name, str):
            from fnmatch import fnmatch
            for pat in self.builtin_patterns:
                if fnmatch(font_name, pat):
                    tail = font_name.rsplit("_", 1)[-1]
                    if tail.isdigit():
                        return int(tail)
        if size is not None:
            return int(size)
        return self.fallback_px

    def _font(self, px):
        require_pil("文本度量")
        if px not in self._cache:
            self._cache[px] = ImageFont.truetype(self.ttf, int(px))
        return self._cache[px]

    def _icon_font(self, px):
        require_pil("图标文本度量")
        if not self.icon_ttf or not os.path.isfile(self.icon_ttf):
            return None
        if px not in self._icon_cache:
            try:
                self._icon_cache[px] = ImageFont.truetype(self.icon_ttf, int(px))
            except Exception:
                self._icon_cache[px] = None
        return self._icon_cache[px]

    def width(self, text, font_name=None, size=None, margin=False):
        px = self.px_of(font_name, size)
        f = self._font(px)
        fi = self._icon_font(px)
        w = 0.0
        for ch in (text or ""):
            ft = fi if (fi is not None and is_icon_char(ch, self.icon_ranges)) else f
            try:
                w += ft.getlength(ch)
            except Exception:
                w += px
        return w + (self.margin_px if margin else 0)

    def glyph_metrics(self, text, font_name=None, size=None):
        """(净宽, 墨迹相对行框顶的上偏移, 下偏移)。

        注意：PIL 的 getbbox(ch) 返回的就是**相对行框顶**的坐标，
        不要再减 ascent（踩过一次：减完得到负数偏移）。
        配置里的 ink_offset_from_box_top 是实测值，优先用于越界判定。
        """
        px = self.px_of(font_name, size)
        f = self._font(px)
        fi = self._icon_font(px)
        top, bot, w = 1e9, -1e9, 0.0
        for ch in (text or ""):
            ft = fi if (fi is not None and is_icon_char(ch, self.icon_ranges)) else f
            try:
                bb = ft.getbbox(ch)
                w += ft.getlength(ch)
                top = min(top, bb[1]); bot = max(bot, bb[3])
            except Exception:
                w += px
        if top > bot:
            return w, None, None
        return w, top, bot


def ink_offset(cfg, px):
    """取配置里该字号的墨迹上/下偏移（相对框顶），没有则 None。"""
    m = ((cfg.get("fonts") or {}).get("ink_offset_from_box_top") or {})
    v = m.get(str(px))
    return tuple(v) if v else None


# --------------------------------------------------------------------------- #
# 组件树
# --------------------------------------------------------------------------- #

def walk_tree(node, schema, depth=0):
    """按 schema 映射遍历组件树，yield (node, depth)。"""
    if not isinstance(node, dict):
        return
    yield node, depth
    for child in node.get(schema.get("children", "children")) or []:
        for item in walk_tree(child, schema, depth + 1):
            yield item


def declared_fonts(cfg):
    """已声明字体名集合 = config 的 fonts.name_to_px + 目标工程文件里声明的字体。

    注意：内置字体（运行时自带，如 LVGL 的 MONTSERRAT_*）通常不在工程里声明，
    由 is_builtin_font() 单独判定，不算"未声明"。
    """
    names = set((cfg.get("fonts", {}) or {}).get("name_to_px", {}).keys())
    pf = cfg_path(cfg, "project.project_file")
    if pf and os.path.isfile(pf):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                data = json.load(f)
            for fnt in (data.get("fonts") or []):
                if isinstance(fnt, dict) and fnt.get("name"):
                    names.add(fnt["name"])
                elif isinstance(fnt, str):
                    names.add(fnt)
        except Exception:
            pass
    return names


def is_builtin_font(cfg, name):
    """内部字体判定（与框架无关）。

    优先用 config.fonts.builtin_patterns 里的通配模式；没配时用**命名约定启发式**
    （形如 `<前缀>_<数字>` 的名字通常是运行时自带的内置字体）。
    """
    import re
    from fnmatch import fnmatch
    pats = (cfg.get("fonts") or {}).get("builtin_patterns") or []
    if pats:
        return any(fnmatch(name or "", p) for p in pats)
    return bool(re.match(r"^[A-Za-z_]*[A-Za-z]_[0-9]{1,3}$", name or ""))


def font_names(cfg):
    """(已声明字体集合, 内置字体判定函数)。供各检查脚本复用，避免各写一份。"""
    return declared_fonts(cfg), (lambda n: is_builtin_font(cfg, n))


def load_pages(cfg):
    """读设计源，返回 [(页名, 页根节点), ...]。"""
    path = cfg_path(cfg, "project.design_src")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sch = cfg.get("tree_schema", {}) or {}
    for key in sch.get("pages", ["pages"]):
        if key in data:
            data = data[key]
            break
    pages = []
    for p in (data if isinstance(data, list) else [data]):
        name = p.get(sch.get("page_name", "name"), "?")
        root = p.get(sch.get("page_root", "screen"), p)
        pages.append((name, root))
    return pages


# --------------------------------------------------------------------------- #
# CLI 自检
# --------------------------------------------------------------------------- #

def _main():
    argv = sys.argv[1:]
    cfg = load_config(argv[0] if argv else None)
    W, H = screen_size(cfg)
    print("config : %s" % cfg["_abs"]["_config_path"])
    print("project: %s" % cfg.get("project", {}).get("name"))
    print("screen : %dx%d" % (W, H))
    if not W or not H:
        print("  ⚠️ screen.w / screen.h 未配置 —— 几何类检查会被跳过，请先填好")
    print("base   : %s" % cfg["_abs"]["base"])
    print("--- 已解析路径 ---")
    for k in sorted(cfg["_abs"]):
        if k.startswith("_"):
            continue
        print("  %-22s %s" % (k, cfg["_abs"][k]))
    print("--- 关键路径存在性 ---")
    for key in ("project.root", "project.design_src", "project.project_file",
                "project.gen_dir", "fonts.device_ttf", "fonts.icon_ttf",
                "paths.preview_dir", "paths.native_dir"):
        v = cfg["_abs"].get(key)
        if v is None:
            print("  %-22s (未配置)" % key); continue
        print("  %-22s %s  %s" % (key, "OK " if os.path.exists(v) else "缺失", v))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
