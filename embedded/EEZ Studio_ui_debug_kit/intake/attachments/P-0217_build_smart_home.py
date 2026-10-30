# -*- coding: utf-8 -*-
"""批1：6 页原生控件预生成（800x480）

- 背景图只保留装饰/卡片/图标/复杂视觉；
- 文字 → EEZ Label（字体子集后续烘）；
- 按钮/胶囊/分段/开关/滑条 → 可见原生 EEZ 控件（有真实按压态）；
- 输出 haven-home.eez-project，6 屏。
"""
import base64
import hashlib
import io
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import design_source as ds
import design_view as dv

TEMPLATE = os.path.join(ROOT, "..", "watch-app-list-no-flow",
                        "watch-app-list-no-flow.eez-project")
OUT = os.path.join(ROOT, "haven-home.eez-project")
BG_DIR = os.path.join(ROOT, "build", "batch1_bg")
FONT_FILE = os.path.join(ROOT, "fonts", "simhei.ttf")
W, H = 800, 480
PAGE_IDS = ["home", "rooms", "living", "lighting", "climate", "curtains"]
FONT_SIZES = []
FONT_CHARS = set()
FONT_NAME = "cn"

BASE_FLAGS = ("CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|"
              "SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|"
              "SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE")
IMG_FLAGS = ("ADV_HITTEST|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|"
             "SCROLLABLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|"
             "SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE")
SKIP_BG = {"text", "toggle", "slider", "btn", "pill", "seg"}
_fnt = {}


def oid(key):
    return str(uuid.UUID(hashlib.md5(key.encode()).hexdigest()))


def hexcol(c):
    return "0x" + c.lstrip("#").upper()


def lighten(c, u=0.18):
    c = c.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * u)
    g = int(g + (255 - g) * u)
    b = int(b + (255 - b) * u)
    return "#%02X%02X%02X" % (r, g, b)


def ttf(px):
    if px not in _fnt:
        from PIL import ImageFont
        _fnt[px] = ImageFont.truetype(FONT_FILE, int(px))
    return _fnt[px]


def bucket(px):
    return min(FONT_SIZES, key=lambda s: (abs(s - px), s))


def font_name(px):
    return "%s%d" % (FONT_NAME, bucket(px))


def measure(text, px):
    return ttf(px).getbbox(text or " ", anchor="ls")


def styles(part_default, parts=None):
    d = {"MAIN": {"DEFAULT": {"pad_top": 0, "pad_bottom": 0, "pad_left": 0,
                              "pad_right": 0, "pad_row": 0, "pad_column": 0,
                              "border_width": 0, "outline_width": 0}}}
    d["MAIN"]["DEFAULT"].update(part_default)
    for pname, pval in (parts or {}).items():
        if "|" in pname:
            part, state = pname.split("|", 1)
            d.setdefault(part, {}).setdefault(state, {}).update(pval)
        elif pname in ("PRESSED", "CHECKED", "FOCUSED", "DISABLED",
                       "SELECTED"):
            d["MAIN"].setdefault(pname, {}).update(pval)
        else:
            d.setdefault(pname, {"DEFAULT": {}})
            d[pname]["DEFAULT"].update(pval)
    return {"objID": oid("st" + json.dumps(d, sort_keys=True)),
            "definition": d}


def widget(key, wtype, x, y, w, h, flags, local, extra=None):
    o = {"objID": oid(key), "type": wtype,
         "left": int(round(x)), "top": int(round(y)),
         "width": int(round(w)), "height": int(round(h)),
         "customInputs": [], "customOutputs": [],
         "style": {"objID": oid("ref" + key), "useStyle": "default",
                   "conditionalStyles": [], "childStyles": []},
         "timeline": [], "eventHandlers": [],
         "leftUnit": "px", "topUnit": "px", "widthUnit": "px",
         "heightUnit": "px", "widgetFlags": flags,
         "hiddenFlagType": "literal", "clickableFlagType": "literal",
         "flagScrollbarMode": "OFF", "checkedStateType": "literal",
         "disabledStateType": "literal", "states": "", "groupIndex": 0,
         "localStyles": local,
         "identifier": key.replace(".", "_").replace("-", "_")}
    if extra:
        o.update(extra)
    o["children"] = []
    return o


def label(key, text, px, color, x, y, anchor="start", op=1, ls=0):
    pxb = bucket(px)
    box = measure(text, pxb)
    tw, th = box[2] - box[0], box[3] - box[1]
    lx = x - box[0]
    if anchor == "middle":
        lx = x - (box[0] + box[2]) / 2.0
    elif anchor == "end":
        lx = x - box[2]
    ly = y + box[1]
    la = {"text_color": hexcol(color), "text_font": font_name(px)}
    if op < 1:
        la["text_opa"] = int(op * 255)
    if ls:
        la["text_letter_space"] = int(ls)
    l = widget("%s.l" % key, "LVGLLabelWidget", lx, ly,
               max(tw + 4, 8), max(th + 2, 8), "GESTURE_BUBBLE",
               styles(la),
               extra={"text": text, "textType": "literal",
                      "longMode": "CLIP", "recolor": False,
                      "useStaticText": True})
    FONT_CHARS.update(text)
    return l


def button(key, x, y, w, h, text, px, bg, fg, radius=None,
           flags=BASE_FLAGS):
    r = radius if radius is not None else h / 2.0
    b = widget(key, "LVGLButtonWidget", x, y, w, h, flags,
               styles({"bg_color": hexcol(bg), "bg_opa": 255,
                       "radius": int(r)},
                      parts={"PRESSED": {
                          "bg_color": hexcol(lighten(bg)),
                          "bg_opa": 255}}))
    if text:
        b["children"].append(label(key + ".t", text, px, fg,
                                   w / 2.0, h / 2.0 + px * 0.35,
                                   anchor="middle"))
    return b


def toggle_widget(key, e):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    on = bool(e["on"])
    sw = widget(key, "LVGLSwitchWidget", x, y, w, h,
                "CHECKABLE|CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|"
                "PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|"
                "SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE",
                styles({"bg_color": hexcol(ds.TRACK), "bg_opa": 255,
                        "radius": h / 2},
                       parts={"INDICATOR": {"bg_opa": 0},
                              "INDICATOR|CHECKED": {
                                  "bg_color": hexcol(ds.ACCENT),
                                  "bg_opa": 255},
                              "KNOB": {"bg_color": "0xFFFFFF",
                                       "bg_opa": 255},
                              "KNOB|CHECKED": {"bg_color": "0xFFFFFF",
                                               "bg_opa": 255}}))
    sw["checkedState"] = on
    sw["checkedStateType"] = "literal"
    return sw


def slider_widget(key, e):
    x, y, w = e["x"], e["y"], e["w"]
    h = 6
    pct = int(round(max(0, min(1, e["p"])) * 100))
    return widget(key, "LVGLSliderWidget", x, y - h // 2, w, h,
                  BASE_FLAGS,
                  styles({"bg_color": hexcol(ds.TRACK), "bg_opa": 255,
                          "radius": 3},
                         parts={"INDICATOR": {"bg_color": hexcol(e["color"]),
                                              "bg_opa": 255, "radius": 3},
                                "KNOB": {"bg_color": "0xFFFFFF",
                                         "bg_opa": 255,
                                         "radius": 20,
                                         "pad_top": 11, "pad_bottom": 11,
                                         "pad_left": 11, "pad_right": 11,
                                         "border_width": 3,
                                         "border_color": hexcol(ds.BG),
                                         "border_opa": 255}}),
                  extra={"min": 0, "minType": "literal", "max": 100,
                         "maxType": "literal", "mode": "NORMAL",
                         "value": pct, "valueType": "literal",
                         "previewValue": pct, "enableAnimation": False})


def seg_widget(key, e):
    x, y, w, h = e["x"], e["y"], e["w"], e["h"]
    labels = e["labels"]
    n = len(labels)
    cw = w / n
    out = [widget(key + ".track", "LVGLContainerWidget", x, y, w, h,
                  "GESTURE_BUBBLE",
                  styles({"bg_color": hexcol(ds.CARD), "bg_opa": 255,
                          "radius": h / 2}))]
    for i, txt in enumerate(labels):
        sel = i == e["sel"]
        out.append(button("%s.s%d" % (key, i), x + cw * i + 2, y + 2,
                          cw - 4, h - 4, txt, 11,
                          ds.ACCENT if sel else ds.CARD,
                          ds.BG if sel else ds.TEXT2, radius=(h - 4) / 2))
    FONT_CHARS.update("".join(labels))
    return out


def make_bg(p, path):
    bg, elems = p["draw"](0)
    keep = [e for e in elems if e["t"] not in SKIP_BG]
    defs, body = dv.render_page(keep, "bg" + p["id"])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d" font-family="%s"><defs>%s</defs>'
           '<rect width="100%%" height="100%%" fill="%s"/>'
           '<g>%s</g></svg>') % (W, H, W, H, ds.FONT, "".join(defs),
                                 bg, body)
    import cairosvg
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=path,
                     output_width=W, output_height=H)


def overlay_widget(key, box, radius):
    x, y, w, h = box
    return widget(key, "LVGLButtonWidget", x, y, w, h, BASE_FLAGS,
                  styles({"bg_color": "0xFFFFFF", "bg_opa": 0,
                          "radius": int(radius)},
                         parts={"PRESSED": {"bg_color": "0xFFFFFF",
                                            "bg_opa": 36,
                                            "radius": int(radius)}}))


def hits_for(p):
    """给标注过的触控区域补原生按压层（在可见控件之下）。"""
    out = []
    seen = set()

    def add(box, radius, tag):
        box = tuple(box)
        if box in seen:
            return
        seen.add(box)
        out.append(overlay_widget("hit.%s.%s.%d" % (p["id"], tag, len(out)),
                                  box, radius))

    for i in range(len(ds.NAV)):
        add((8, 62 + i * 38, 60, 38), 12, "nav")
    for e in p["draw"](0)[1]:
        if e.get("card"):
            add((e["x"], e["y"], e["w"], e["h"]), e.get("r", 18), "card")
    for row in ds.CONTROLS.get(p["id"], []):
        _num, boxes, desc, _target, typ, _hw = row
        if desc == "侧栏一级导航":
            continue
        if typ == "卡片":
            rad = 18
        elif typ in ("按钮", "分段", "图标按钮"):
            rad = boxes[0][3] / 2.0
        elif typ == "手势":
            rad = boxes[0][3] / 2.0
        else:
            rad = 10
        tag = {"按钮": "btn", "开关": "sw", "滑条": "sld", "分段": "seg",
               "卡片": "card", "列表": "list", "手势": "gest",
               "图标按钮": "icon"}.get(typ, "ctl")
        for b in boxes:
            add(b, rad, tag)
    return out


def controls_for(p):
    out = []
    for e in p["draw"](0)[1]:
        t = e["t"]
        key = "c.%s.%d" % (p["id"], len(out))
        if t == "toggle":
            out.append(toggle_widget(key, e))
        elif t == "slider":
            out.append(slider_widget(key, e))
        elif t == "btn":
            out.append(button(key, e["x"], e["y"], e["w"], e["h"], e["s"],
                              e["size"], e["fill"], e["color"], e["r"]))
        elif t == "pill":
            out.append(button(key, e["x"], e["y"], e["w"], e["h"], e["s"],
                              e["size"], e["fill"], e["color"],
                              e["h"] / 2.0))
        elif t == "seg":
            out.extend(seg_widget(key, e))
    return out


def labels_for(p):
    out = []
    for i, e in enumerate(p["draw"](0)[1]):
        if e["t"] == "text":
            out.append(label("t.%s.%d" % (p["id"], i), e["s"], e["size"],
                             e["color"], e["x"], e["y"], e["anchor"],
                             e["op"], e["ls"]))
    return out


def screen(name, children):
    s = widget("scr." + name, "LVGLScreenWidget", 0, 0, W, H,
               "CLICKABLE|PRESS_LOCK|CLICK_FOCUSABLE|GESTURE_BUBBLE|"
               "SNAPPABLE|SCROLLABLE|SCROLL_ELASTIC|SCROLL_MOMENTUM|"
               "SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER",
               styles({"bg_color": hexcol(ds.BG), "radius": 0,
                       "clip_corner": False}))
    s["children"] = children
    s["identifier"] = "scr_" + name
    return s


def page_obj(name, scr, first):
    return {"objID": oid("page." + name), "components": [scr],
            "connectionLines": [], "localVariables": [],
            "componentGroups": [], "userProperties": [],
            "name": name, "left": 0, "top": 0, "width": W, "height": H,
            "isUsedAsUserWidget": False, "createAtStart": first,
            "deleteOnScreenUnload": False}


def build():
    global FONT_SIZES
    sizes = set()
    for pid in PAGE_IDS:
        p = next(x for x in ds.PAGES if x["id"] == pid)
        for e in p["draw"](0)[1]:
            if e["t"] == "text":
                sizes.add(e["size"])
            elif e["t"] in ("btn", "pill"):
                sizes.add(e["size"])
            elif e["t"] == "seg":
                sizes.add(11)
    FONT_SIZES = sorted(sizes)
    os.makedirs(BG_DIR, exist_ok=True)
    pages = []
    bitmaps = []
    for pid in PAGE_IDS:
        p = next(x for x in ds.PAGES if x["id"] == pid)
        bg_path = os.path.join(BG_DIR, pid + ".png")
        make_bg(p, bg_path)
        bmp = "bg_" + pid
        bitmaps.append({"objID": oid("bmp." + bmp), "name": bmp,
                        "description": "批1 装饰背景 " + p["name"],
                        "image": "data:image/png;base64," +
                        base64.b64encode(open(bg_path, "rb").read()).decode(),
                        "bpp": 32, "alwaysBuild": True})
        ch = [widget("img.%s.bg" % pid, "LVGLImageWidget", 0, 0, W, H,
                     IMG_FLAGS, styles({}),
                     extra={"image": bmp, "imageType": "literal",
                            "setPivot": False, "pivotX": 0, "pivotY": 0,
                            "zoom": 256, "angle": 0, "innerAlign": "CENTER",
                            "sizeMode": "VIRTUAL", "value": 0,
                            "valueType": "literal", "previewValue": 0})]
        ch[0]["identifier"] = "bg_" + pid
        ch += labels_for(p)
        ch += hits_for(p)
        ch += controls_for(p)
        pages.append(page_obj(pid, screen(pid, ch), pid == "home"))

    codes = set(range(32, 127))
    for ch_ in FONT_CHARS:
        codes.add(ord(ch_))
    ranges = ["32-126"] + [str(c) for c in sorted(codes) if c > 126]
    enc = [{"from": 32, "to": 126}] + \
          [{"from": c, "to": c} for c in sorted(codes) if c > 126]
    fonts = []
    for px in FONT_SIZES:
        fonts.append({"objID": oid("font.cn%d" % px), "name": "cn%d" % px,
                      "description": "批1 %d px 字体子集" % px,
                      "renderingEngine": "LVGL",
                      "source": {"objID": oid("fontsrc.cn%d" % px),
                                 "filePath": "fonts/simhei.ttf", "size": px},
                      "bpp": 4, "threshold": 128, "glyphs": [],
                      "screenOrientation": "all", "alwaysBuild": False,
                      "lvglRanges": ",".join(ranges), "lvglSymbols": "",
                      "lvglAdditionalSources": [],
                      "lvglGlyphs": {"objID": oid("glyphs.cn%d" % px),
                                     "encodings": enc}})

    proj = json.load(io.open(TEMPLATE, encoding="utf-8"))
    g = proj["settings"]["general"]
    g["displayWidth"], g["displayHeight"] = W, H
    g["circularDisplay"] = False
    g["displayBorderRadius"] = 0
    g["flowSupport"] = False
    proj["settings"]["general"] = g
    proj["fonts"] = fonts
    proj["bitmaps"] = bitmaps
    proj["variables"] = {"objID": oid("vars"), "globalVariables": []}
    proj["actions"] = []
    proj["userPages"] = pages
    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(proj, ensure_ascii=False, indent=2) + "\n")
    io.open(os.path.join(ROOT, "build", "font_chars.txt"), "w",
            encoding="utf-8").write("".join(sorted(FONT_CHARS)))
    print("written:", OUT, "pages=", len(pages), "fonts=", len(fonts),
          "bitmaps=", len(bitmaps), "chars=", len(FONT_CHARS))


if __name__ == "__main__":
    build()
