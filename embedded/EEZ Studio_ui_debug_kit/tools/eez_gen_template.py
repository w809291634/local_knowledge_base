# -*- coding: utf-8 -*-
"""通用 EEZ 生成器模板（LVGL / no flow）。

输入：
  --src    design_source.json（页面 + 节点声明）
  --base   eez_base.json（EEZ 工程骨架）
  --out    输出 .eez-project
  --base-dir  资源相对目录（默认 src 所在目录）
  --tpl-dir   EEZ 拖拽模板目录（默认 kit/reference/eez_widget_syntax/templates）

内置硬规则：
  - 控件只从模板克隆，字段集不超出模板（A14）。
  - 按钮子标签必须 content 尺寸，禁止等于按钮盒；内置 BTN_CHILD 断言。
  - 居中按钮 align/text_align=CENTER；左/右例外用 LEFT_MID/RIGHT_MID + 父 pad。
  - Slider MAIN 透明；轨道由设计源的独立 6px 容器提供；top=track_y-9；KNOB pad=-4。
  - 读数 Label 的几何由设计源给“原文实测盒”，不要用点击热区盒。
  - 字体按 token 分 TTF；无 text-anchor 按 middle。
"""
import argparse
import copy
import io
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TPL = os.path.abspath(os.path.join(
    HERE, "..", "reference", "eez_widget_syntax", "templates"))

TYPE_OF = {
    "container": "LVGLContainerWidget",
    "label": "LVGLLabelWidget",
    "button": "LVGLButtonWidget",
    "switch": "LVGLSwitchWidget",
    "slider": "LVGLSliderWidget",
    "line": "LVGLLineWidget",
}
CODE = {"container": "w", "label": "st", "button": "go",
        "switch": "sw", "slider": "sl", "line": "ln"}

TPL = None


def oid():
    return str(uuid.uuid4())


def load_templates(tpl_dir):
    global TPL
    TPL = {}
    for t in set(TYPE_OF.values()) | {"LVGLScreenWidget"}:
        TPL[t] = json.load(io.open(os.path.join(tpl_dir, t + ".json"), encoding="utf-8"))


def clone(wtype):
    obj = copy.deepcopy(TPL[wtype])

    def fix(v):
        if isinstance(v, dict):
            return {k: fix(x) for k, x in v.items()}
        if isinstance(v, list):
            return [fix(x) for x in v]
        if isinstance(v, str) and v.startswith("__") and v.endswith("OBJID__"):
            return oid()
        return v
    return fix(obj)


def style_def(obj, part="MAIN", state="DEFAULT", **props):
    ls = obj.setdefault("localStyles", {"objID": oid()})
    df = ls.setdefault("definition", {}).setdefault(part, {}).setdefault(state, {})
    df.update(props)
    return obj


def color(v, default=None):
    return default if (not v or v == "none") else v


def make_node(spec, page_id, idx, theme, page_index):
    kind = spec["type"]
    obj = clone(TYPE_OF[kind])
    top = spec.get("ezz_y", spec["y"])
    if kind == "slider" and "ezz_y" not in spec and "track_y" in spec:
        top = spec["track_y"] - 9
    obj["left"], obj["top"] = spec["x"], top
    obj["width"], obj["height"] = spec["w"], spec["h"]
    obj["leftUnit"] = obj["topUnit"] = "px"
    obj["widthUnit"] = obj["heightUnit"] = "px"

    if kind == "container":
        obj["widgetFlags"] = "|".join(
            f for f in obj["widgetFlags"].split("|")
            if f not in ("CLICKABLE", "CLICK_FOCUSABLE", "PRESS_LOCK"))
        obj["clickableFlag"] = False
        fill, stroke = color(spec.get("fill")), color(spec.get("stroke"))
        style_def(obj, bg_color=fill or "#000000",
                  bg_opa=spec.get("fill_opa", 255) if fill else 0,
                  radius=spec.get("radius", 0),
                  border_width=1 if stroke else 0,
                  border_color=stroke or "#000000")

    elif kind == "label":
        obj["text"] = spec["text"]
        obj["textType"] = "literal"
        style_def(obj, text_color=spec.get("color", "#EDF4FF"),
                  text_font=spec["font"], text_opa=spec.get("text_opa", 255),
                  text_align=spec.get("align", "center").upper(),
                  bg_opa=0, border_width=0)

    elif kind == "button":
        child = obj["children"][0]
        child["text"] = spec["text"]
        child["textType"] = "literal"
        child["left"], child["top"] = 0, 0
        # 硬规则：子标签永远 content，禁止等于按钮盒。
        child["widthUnit"] = child["heightUnit"] = "content"
        align = spec.get("align", "center")
        if align == "left":
            child_align = "LEFT_MID"
            style_def(obj, pad_left=12, pad_right=0)
        elif align == "right":
            child_align = "RIGHT_MID"
            style_def(obj, pad_left=0, pad_right=12)
        else:
            child_align = "CENTER"
            style_def(obj, pad_left=0, pad_right=0)
        style_def(child, text_color=spec.get("color", "#EDF4FF"),
                  text_font=spec["font"],
                  text_opa=0 if spec.get("text_hidden") else 255,
                  text_align=align.upper(), align=child_align)
        fill, stroke = color(spec.get("fill")), color(spec.get("stroke"))
        if spec.get("transparent") or not fill:
            style_def(obj, bg_opa=0, radius=spec.get("radius", 0),
                      border_width=1 if stroke else 0,
                      border_color=stroke or "#000000")
        else:
            style_def(obj, bg_color=fill, bg_opa=255, radius=spec.get("radius", 0),
                      border_width=1 if stroke else 0,
                      border_color=stroke or "#000000")
        if spec.get("goto"):
            obj["eventHandlers"].append({
                "objID": oid(), "eventName": "CLICKED", "handlerType": "action",
                "action": "nav_goto", "userData": page_index.get(spec["goto"], 0),
            })

    elif kind == "switch":
        pad = -2
        style_def(obj, pad_top=pad, pad_bottom=pad, pad_left=pad, pad_right=pad,
                  border_width=0)
        style_def(obj, part="INDICATOR", bg_color=spec.get("color", "#3FD0C9"),
                  bg_opa=255, radius=999)
        style_def(obj, part="KNOB", bg_color="#FFFFFF", bg_opa=255, radius=999)

    elif kind == "slider":
        obj["min"], obj["max"] = 0, 100
        obj["value"] = spec.get("value", 65)
        obj["previewValue"] = spec.get("value", 65)
        style_def(obj, pad_top=9, pad_bottom=9, pad_left=0, pad_right=0,
                  bg_color="#243244", bg_opa=0, radius=3, border_width=0)
        style_def(obj, part="INDICATOR", bg_color=spec.get("color", "#3FD0C9"),
                  bg_opa=255, radius=3)
        style_def(obj, part="KNOB", bg_color="#FFFFFF", bg_opa=255, radius=999,
                  pad_top=-4, pad_bottom=-4, pad_left=-4, pad_right=-4)

    elif kind == "line":
        obj["points"] = spec["points"]
        obj["widthUnit"] = obj["heightUnit"] = "px"
        obj["widgetFlags"] = "GESTURE_BUBBLE"
        style_def(obj, line_color=spec.get("color", "#3FD0C9"),
                  line_width=spec.get("width", 2), line_rounded=True,
                  bg_opa=0, border_width=0)

    code = CODE[kind]
    if kind == "button" and not spec.get("goto"):
        code = "hw"
    elif kind == "label" and spec.get("role") == "read":
        code = "hr"
    obj["identifier"] = "%s_%s%02d" % (page_id, code, idx)
    return obj


def make_page(page, theme, page_index):
    pid = page.get("key") or re.sub(r"[^0-9A-Za-z_]", "_", page["name"])
    root = clone("LVGLScreenWidget")
    root["left"] = root["top"] = 0
    root["width"], root["height"] = page.get("width", 800), page.get("height", 480)
    style_def(root, bg_color=theme.get("bg", "#000000"), bg_opa=255,
              radius=0, border_width=0)
    root["identifier"] = "screen_" + pid
    for i, spec in enumerate(page["screen"]["children"], 1):
        root["children"].append(make_node(spec, pid, i, theme, page_index))
    return {
        "objID": oid(), "components": [root], "connectionLines": [],
        "localVariables": [], "componentGroups": [], "userProperties": [],
        "name": pid, "left": 0, "top": 0,
        "width": page.get("width", 800), "height": page.get("height", 480),
        "isUsedAsUserWidget": False, "createAtStart": True,
        "deleteOnScreenUnload": False,
    }


def assert_button_children(pages):
    bad = []
    for pg in pages:
        for w in pg["components"][0]["children"]:
            if w.get("type") != "LVGLButtonWidget":
                continue
            ch = (w.get("children") or [None])[0]
            if not ch:
                bad.append((pg["name"], w.get("identifier"), "没有子标签"))
                continue
            if ch.get("widthUnit") != "content" or ch.get("heightUnit") != "content":
                bad.append((pg["name"], w.get("identifier"),
                            "单位 %s/%s" % (ch.get("widthUnit"), ch.get("heightUnit"))))
            if ch.get("width") == w.get("width") and ch.get("height") == w.get("height"):
                bad.append((pg["name"], w.get("identifier"), "子标签几何等于按钮盒"))
            if not (ch.get("text") or "").strip():
                bad.append((pg["name"], w.get("identifier"), "子标签文本为空"))
    if bad:
        for b in bad[:20]:
            print("  BTN_CHILD FAIL", b)
        raise SystemExit("BTN_CHILD FAIL：%d 个按钮子标签违规" % len(bad))
    n = sum(1 for pg in pages for w in pg["components"][0]["children"]
            if w.get("type") == "LVGLButtonWidget")
    print("[BTN_CHILD] PASS：%d 个按钮子标签均为 content 尺寸" % n)


def assert_cmap(texts, ttf_path):
    from fontTools.ttLib import TTFont
    if not os.path.isfile(ttf_path):
        raise SystemExit("字体不存在：%s" % ttf_path)
    f = TTFont(ttf_path)
    cmap = set()
    for t in f["cmap"].tables:
        cmap.update(t.cmap.keys())
    miss = sorted({c for s in texts for c in s if ord(c) not in cmap})
    if miss:
        raise SystemExit("F3 FAIL：%s 缺字形 %s" % (
            ttf_path, " ".join("U+%04X(%s)" % (ord(c), c) for c in miss)))


def ranges_from_chars(chars):
    codes = sorted({ord(c) for c in chars if ord(c) >= 32}) or list(range(32, 127))
    ranges, start, prev = [], codes[0], codes[0]
    for c in codes[1:]:
        if c == prev + 1:
            prev = c
        else:
            ranges.append((start, prev))
            start = prev = c
    ranges.append((start, prev))
    return ranges


def make_fonts(texts_by_token, ttf_by_token):
    out = []
    for name in sorted(texts_by_token, key=lambda k: int(k[2:])):
        px = int(name[2:])
        ttf = ttf_by_token.get(name, "fonts/msyh.ttf")
        chars = set()
        for s in texts_by_token[name]:
            chars.update(s)
        chars.update(chr(c) for c in range(32, 127))
        ranges = ranges_from_chars(chars)
        out.append({
            "objID": oid(), "name": name,
            "description": "设计源 %d px 档（同源生成，勿手改）" % px,
            "renderingEngine": "LVGL",
            "source": {"objID": oid(), "filePath": ttf, "size": px},
            "bpp": 4, "threshold": 128, "glyphs": [], "screenOrientation": "all",
            "alwaysBuild": False,
            "lvglRanges": ",".join(str(a) if a == b else "%d-%d" % (a, b)
                                   for a, b in ranges),
            "lvglSymbols": "", "lvglAdditionalSources": [],
            "lvglGlyphs": {"objID": oid(),
                           "encodings": [{"from": a, "to": b} for a, b in ranges]},
        })
    return out


def generate(src, base, out, base_dir, tpl_dir):
    data = json.load(io.open(src, encoding="utf-8"))
    proj = json.load(io.open(base, encoding="utf-8"))
    load_templates(tpl_dir)
    proj["objID"] = oid()
    theme = data.get("theme", {})
    ttf_by_token = data.get("ttf_by_token", {
        "cn16": "fonts/msyh.ttf", "cn24": "fonts/msyhbd.ttf",
        "cn64": "fonts/msyhbd.ttf"})
    biz = [p for p in data["pages"] if not p.get("h5_only")]
    page_index = {p["name"]: i for i, p in enumerate(biz)}
    pages = [make_page(p, theme, page_index) for p in biz]
    assert_button_children(pages)

    texts_by_token = {}
    all_by_token = {}
    for p in biz:
        for n in p["screen"]["children"]:
            t = n.get("text") or ""
            if t:
                texts_by_token.setdefault(n["font"], []).append(t)
                all_by_token.setdefault(n["font"], []).append(t)
    for token, texts in all_by_token.items():
        ttf = ttf_by_token.get(token, "fonts/msyh.ttf")
        assert_cmap(texts, os.path.join(base_dir, ttf))

    proj["userPages"] = pages
    proj["actions"] = [{
        "objID": oid(), "name": "nav_goto",
        "description": "统一跳转：native 按 userData（页索引）loadScreen，只实现一次回调",
        "implementationType": "native", "userProperties": [],
    }]
    proj["fonts"] = make_fonts(texts_by_token, ttf_by_token)
    proj["bitmaps"] = []
    proj["colors"] = []
    if "screen" in data:
        g = proj.setdefault("settings", {}).setdefault("general", {})
        g["displayWidth"] = data["screen"].get("w", 800)
        g["displayHeight"] = data["screen"].get("h", 480)
        g["flowSupport"] = False
    io.open(out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(proj, ensure_ascii=False, indent=2) + "\n")
    print("[EEZ_GEN] %s" % out)
    print("  业务页 %d ｜ 节点 %d ｜ 字体档 %d" % (
        len(pages), sum(len(p["components"][0]["children"]) for p in pages),
        len(proj["fonts"])))


def main():
    ap = argparse.ArgumentParser(description="通用 EEZ 生成器模板（LVGL/no flow）")
    ap.add_argument("--src", required=True, help="design_source.json")
    ap.add_argument("--base", required=True, help="eez_base.json")
    ap.add_argument("--out", required=True, help="输出 .eez-project")
    ap.add_argument("--base-dir", default=None, help="资源路径基准目录")
    ap.add_argument("--tpl-dir", default=DEFAULT_TPL)
    a = ap.parse_args()
    base_dir = a.base_dir or os.path.dirname(os.path.abspath(a.src))
    generate(a.src, a.base, a.out, base_dir, a.tpl_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
