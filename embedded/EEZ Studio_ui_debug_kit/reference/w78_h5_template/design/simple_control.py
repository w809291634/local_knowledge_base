# -*- coding: utf-8 -*-
"""简化主控 + 房间页设计图：主控（场景+房间），房间页（设备方格）。"""
import base64
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "designer_simple")
W, H = 2520, 720

BG, CARD, CARD2, EDGE = "#05080F", "#151B24", "#1C2430", "#273140"
T1, T2, T3 = "#F4F7FB", "#B9C4D4", "#75859C"
ACCENT, GREEN, RED, TEAL = "#F2B45C", "#5FD3A6", "#FF7A6B", "#5FD3C6"
BLUE = "#7FB3FF"
PURPLE = "#C08CFF"

# 控件分类色 = 单一口径（跳转图 / 预览图 / 标注图共用）
CAT_COLORS = {
    "nav": ACCENT,      # 房间卡：跳转
    "back": TEAL,       # 返回按钮
    "scene": PURPLE,    # 场景按钮：执行不跳页
    "toggle": GREEN,    # 开关：接硬件
    "slider": BLUE,     # 滑条：接硬件
    "read": T3,         # 只读传感：不接行为
}


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def r(x, y, w, h, fill, stroke="none", rx=8):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}"/>')


UI_CN, UI_NUM, UI_BIG = 12, 24, 32


def ui_size(text, size=10):
    """镜像字库策略：只有 12px 带汉字；24/32 只给纯 ASCII 数字/符号。"""
    s = str(text)
    if any(ord(c) > 127 for c in s):
        return UI_CN
    if size >= 34:
        return UI_BIG
    if size >= 20:
        return UI_NUM
    return UI_CN


def t(x, y, s, size=10, color=T2, weight="400", anchor="start"):
    size = ui_size(s, size)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>')


def line(x1, y1, x2, y2, color=EDGE, w=1):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{w}"/>')


_BG_B64 = None


def bg_image():
    """页面固定背景图（与运行期 A:/assets/ui_bg.png 同一张，base64 内嵌）。"""
    global _BG_B64
    if _BG_B64 is None:
        try:
            with open(os.path.join(ROOT, "assets", "ui_bg.png"), "rb") as f:
                _BG_B64 = base64.b64encode(f.read()).decode("ascii")
        except OSError:
            _BG_B64 = ""
    if not _BG_B64:
        return r(0, 0, 800, 480, BG)
    return ('<image x="0" y="0" width="800" height="480" preserveAspectRatio="none" '
            'href="data:image/png;base64,%s"/>' % _BG_B64)


def card(x, y, w, h, rx=12):
    # data-card 只用于导出布局框（L6 等距检查），不参与渲染
    return r(x, y, w, h, CARD, EDGE, rx).replace("<rect ", '<rect data-card="1" ', 1)


def btn(x, y, w, h, label, fill=ACCENT, fg=BG, size=11, sub=""):
    size = ui_size(label, size)
    out = [r(x, y, w, h, fill, "none", h / 2),
           t(x + w / 2, y + h / 2 + size * 0.35, label, size, fg, "600", "middle")]
    if sub:
        out.append(t(x + w / 2, y + h / 2 + size * 0.35 + 13, sub, 8,
                     fg if fg == T1 else "#2A2418", "400", "middle"))
    return "".join(out)


def toggle(x, y, on=True):
    return (r(x, y, 44, 24, ACCENT if on else "#222B38", "none", 12) +
            r(x + (22 if on else 2), y + 2, 20, 20, "#FFFFFF", "none", 10))


def slider(x, y, w, p):
    return (r(x, y, w, 6, "#222B38", "none", 3) +
            r(x, y, w * p, 6, ACCENT, "none", 3) +
            f'<circle cx="{x + w * p}" cy="{y + 3}" r="7" fill="#FFFFFF" '
            f'stroke="{BG}" stroke-width="2"/>')


def tag(x, y, text="只读"):
    return (r(x, y, 34, 16, CARD2, EDGE, 6) +
            t(x + 17, y + 11, text, 8, T3, "400", "middle"))


# 主控顶部 4 个二级页入口（设备 / 能耗 / 通知 / 设置）= 单一真值
HEADER_ENTRIES = [("设备", 540, 26, 56, 28), ("能耗", 600, 26, 56, 28),
                  ("通知", 660, 26, 56, 28), ("设置", 720, 26, 56, 28)]
SECURITY_PILL = (640, 86, 116, 20)


def header_home():
    out = [bg_image(),
           t(40, 44, "主控", 26, T1, "700"),
           t(40, 66, "晚上好，李然 · 5月18日 周一", 10, T3),
           t(268, 40, "22° 晴", 12, T2, "600"),
           t(268, 58, "室内 23.5° · 48%", 9, T3)]
    for (label, x, y, w, h) in HEADER_ENTRIES:
        out.append(btn(x, y, w, h, label, CARD2, T1, 9))
    out.append(r(700, 20, 14, 14, RED, "none", 7))
    out.append(t(707, 31, "2", 8, "#FFFFFF", "700", "middle"))
    out.append(line(40, 116, 760, 116))
    # status strip
    out.append(r(40, 84, 720, 24, CARD2, "none", 12))
    out.append(r(52, 92, 8, 8, GREEN, "none", 4))
    out.append(t(66, 100, "已布防 · 离家模式", 9, T2))
    out.append(t(250, 100, "12 个设备在线", 9, T3))
    out.append(t(420, 100, "4 个房间", 9, T3))
    out.append(btn(*SECURITY_PILL, "安防 ›", CARD2, TEAL, 8))
    return "".join(out)


def header_room(name, sub):
    out = [bg_image(),
           btn(*BACK_BOX, "‹ 主控", CARD2, T1, 9),
           t(128, 46, name, 24, T1, "700"),
           t(128, 66, sub, 10, T3),
           line(40, 88, 760, 88)]
    return "".join(out)


# 主控页 2x2 房间卡几何 = 单一真值（标注图 import 这里，不手抄）
ROOM_GRID = {"x0": 40, "dx": 360, "y0": 278, "dy": 98, "w": 340, "h": 86}
SCENE_ROW = {"x": 40, "y": 160, "w": 168, "h": 74, "dx": 180}
SCENES = [("回家", "12 个设备"), ("离家", "全屋关闭"),
          ("晚安", "6 个设备"), ("影院", "4 个设备")]


def room_card_box(i):
    g = ROOM_GRID
    return (g["x0"] + (i % 2) * g["dx"], g["y0"] + (i // 2) * g["dy"],
            g["w"], g["h"])


# 房间页设备方格几何 + 返回按钮几何 = 单一真值
TILE_GRID = {"x0": 40, "dx": 248, "y0": 124, "dy": 168, "w": 224, "h": 150}
BACK_BOX = (40, 28, 72, 28)


def tile_box(i):
    g = TILE_GRID
    return (g["x0"] + (i % 3) * g["dx"], g["y0"] + (i // 3) * g["dy"],
            g["w"], g["h"])


def scene_box(i):
    s = SCENE_ROW
    return (s["x"] + i * s["dx"], s["y"], s["w"], s["h"])


def boot_init_frame():
    """开机自检页（设计预览，不进 EEZ）：渐变背景 + 发光徽标 + 进度条 + 单行动态字条。"""
    out = ['<defs>'
           '<linearGradient id="boot-bg" x1="0" y1="0" x2="0" y2="1">'
           '<stop offset="0" stop-color="#080D18"/><stop offset="1" stop-color="#0F1829"/>'
           '</linearGradient>'
           '<linearGradient id="boot-mark" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#27466A"/><stop offset="1" stop-color="#16263E"/>'
           '</linearGradient>'
           '<linearGradient id="boot-bar" x1="0" y1="0" x2="1" y2="0">'
           '<stop offset="0" stop-color="#4CC2FF"/><stop offset="1" stop-color="#8FE6FF"/>'
           '</linearGradient>'
           '<radialGradient id="boot-glow">'
           '<stop offset="0" stop-color="#4CC2FF" stop-opacity="0.30"/>'
           '<stop offset="1" stop-color="#4CC2FF" stop-opacity="0"/>'
           '</radialGradient>'
           '</defs>',
           r(0, 0, 800, 480, "url(#boot-bg)"),
           '<ellipse cx="400" cy="140" rx="180" ry="126" fill="url(#boot-glow)"/>',
           r(40, 34, 30, 30, ACCENT, "none", 9),
           t(55, 54, "H", 14, BG, "700", "middle"),
           t(82, 37, "HAVEN HOME", 17, T1, "700"),
           t(82, 60, "系统自检", 10, T3),
           t(760, 40, "v1.0.0", 10, T3, "400", "end")]
    # 中央应用标：圆角方块 + 房子 + 环形进度
    out += ['<circle cx="400" cy="128" r="88" fill="none" stroke="#4CC2FF" '
            'stroke-opacity="0.12" stroke-width="8"/>',
            '<circle cx="400" cy="128" r="88" fill="none" stroke="#2A3B52" stroke-width="3"/>',
            '<circle cx="400" cy="128" r="88" fill="none" stroke="#4CC2FF" stroke-width="3" '
            'stroke-linecap="round" stroke-dasharray="232.2 552.9" '
            'transform="rotate(-90 400 128)"/>',
            '<rect x="344" y="72" width="112" height="112" rx="28" '
            'fill="url(#boot-mark)" stroke="#3A688F" stroke-width="1"/>',
            '<polygon points="400,118 370,148 430,148" fill="#F0F7FF"/>',
            r(378, 148, 44, 32, "#F0F7FF", "none", 2),
            r(392, 162, 16, 18, "#1E3452", "none", 1),
            t(400, 222, "系统初始化", 16, T1, "700", "middle"),
            t(400, 246, "正在检查硬件与网络", 10, T3, "400", "middle")]
    # 进度条（42%）
    out += [t(140, 286, "自检进度", 10, T3),
            r(140, 300, 520, 8, "#1A2535", "none", 4),
            r(140, 300, 218, 8, "url(#boot-bar)", "none", 4),
            '<circle cx="358" cy="304" r="6" fill="#D6F2FF"/>',
            t(660, 282, "42%", 11, T2, "700", "end")]
    # 单行动态字条
    out += ['<circle cx="304" cy="338" r="4" fill="#4CC2FF"/>',
            t(316, 343, "正在检查 Wi-Fi 模块…", 13, T2)]
    # 页脚
    out += [line(40, 432, 760, 432),
            t(40, 446, "请勿断电", 10, T3),
            t(760, 446, "HAVEN HOME", 10, T3, "400", "end")]
    return "".join(out)


def main_frame():
    out = [header_home(),
           t(40, 148, "场景", 11, T3)]
    for i, (name, sub) in enumerate(SCENES):
        x, y, w, h = scene_box(i)
        out.append(btn(x, y, w, h, name,
                       ACCENT if i == 0 else CARD2, BG if i == 0 else T1,
                       14, sub))
    out.append(t(40, 264, "房间", 11, T3))
    rooms = [("客厅", "23.5°", "5 个设备 · 湿度 48%"),
             ("主卧", "24.0°", "2 个设备 · 湿度 50%"),
             ("厨房", "22.8°", "3 个设备 · 湿度 55%"),
             ("浴室", "23.1°", "1 个设备 · 湿度 62%")]
    for i, (name, temp, sub) in enumerate(rooms):
        x, y, w, h = room_card_box(i)
        out += [card(x, y, w, h),
                t(x + 14, y + 24, name, 13, T1, "600"),
                t(x + 14, y + 54, temp, 22, T1, "700"),
                t(x + 14, y + 72, sub, 8, T3),
                t(x + w - 26, y + 46, "›", 22, ACCENT, "400", "end")]
    return "".join(out)


def tile(x, y, name, sub, value="", control="toggle", on=True, readonly=False,
         scene=False):
    out = [card(x, y, TILE_GRID["w"], TILE_GRID["h"])]
    out.append(r(x + 14, y + 14, 26, 26, CARD2, "none", 8))
    out.append(t(x + 27, y + 32, name[:1], 12, ACCENT if not readonly else T3,
                 "700", "middle"))
    out.append(t(x + 50, y + 24, name, 11, T1, "600"))
    out.append(t(x + 50, y + 40, sub, 8, T3))
    if value:
        out.append(t(x + 14, y + 76, value, 20, T1, "700"))
    if not scene:                       # 场景格没有「详情」，只有「执行」
        dx, dy, dw, dh = TILE_DETAIL_BTN
        out.append(btn(x + dx, y + dy, dw, dh, "详情", CARD2, ACCENT, 8))
    if readonly:
        out.append(tag(x + 104, y + 16))
        out.append(t(x + 14, y + 124, "状态只读", 8, T3))
    elif scene:
        ex, ey, ew, eh = SCENE_EXEC_BTN
        out.append(btn(x + ex, y + ey, ew, eh, "执行", CARD2, ACCENT, 9))
    elif control == "toggle":
        out.append(toggle(x + 166, y + 104, on))
    elif control == "slider":
        out.append(slider(x + 14, y + 112, 196, 0.7))
        out.append(t(x + 14, y + 104, "开合 70%", 8, T3))
    return "".join(out)


def room_frame(name, sub, data):
    """房间页：设备列表驱动。<=6 台铺满 2 行；>6 台纵向滚动（底部露半行 + 滚动条）；0 台走空态。"""
    out = [header_room(name, sub), t(40, 112, "设备", 11, T3)]
    if not data:
        out += [card(40, 124, 720, 300),
                t(400, 240, "本房间暂无设备", 18, T2, "600", "middle"),
                t(400, 272, "添加后可在这里开关、调光、看状态", 10, T3, "400", "middle"),
                btn(320, 306, 160, 40, "＋ 添加设备", ACCENT, BG, 11)]
        return "".join(out)
    x0, y0, w, h = TILE_VIEW
    scroll = len(data) > TILE_COLS * TILE_ROWS
    cid = "clip-" + str(abs(hash(name)) % 10000)
    out.append('<clipPath id="%s"><rect x="%d" y="%d" width="%d" height="%d" rx="8"/></clipPath>'
               % (cid, x0, y0, w, h))
    out.append('<g clip-path="url(#%s)">' % cid)
    for i, d in enumerate(data):
        x, y, _w, _h = tile_box(i)
        out.append(tile(x, y, *d))
    out.append("</g>")
    if scroll:
        total = len(data)
        rows = (total + TILE_COLS - 1) // TILE_COLS
        out.append(r(784, y0 + 8, 4, h - 16, "#1b2432", "none", 2))
        kh = max(40, int((h - 16) * TILE_ROWS / rows))
        out.append(r(784, y0 + 8, 4, kh, ACCENT, "none", 2))
        out.append(t(40, 466, "↓ 共 %d 台，可上下滑动" % total, 9, T3))
    return "".join(out)


# 4 个房间的设备方格 = 单一真值（房间页设计图与跳转/预览图共用）
ROOM_TILES = {
    "客厅": [
        ("主灯", "客厅 · 3000K", "80%", "toggle", True, False, False),
        ("落地灯", "客厅 · 暖光", "", "toggle", False, False, False),
        ("窗帘", "客厅", "", "slider", True, False, False),
        ("空调", "制冷 · 自动", "23.5°", "toggle", True, False, False),
        ("温湿度", "客厅", "23.5° / 48%", None, False, True, False),
        ("摄像头", "1080P · 已加密", "实时", None, False, True, False),
    ],
    "主卧": [
        ("床头灯", "主卧 · 暖光", "20%", "toggle", True, False, False),
        ("主灯", "主卧", "", "toggle", False, False, False),
        ("窗帘", "主卧", "", "slider", False, False, False),
        ("空调", "制冷 · 静音", "24.0°", "toggle", True, False, False),
        ("温湿度", "主卧", "24.0° / 50%", None, False, True, False),
        ("晚安模式", "全屋灯关 · 布防", "", None, False, False, True),
    ],
    "厨房": [
        ("主灯", "厨房", "", "toggle", False, False, False),
        ("插座", "厨房", "", "toggle", True, False, False),
        ("燃气传感", "厨房 · 待命", "正常", None, False, True, False),
    ],
    "浴室": [
        ("暖灯", "浴室", "", "toggle", False, False, False),
        ("排风", "浴室", "", "toggle", True, False, False),
        ("漏水传感", "浴室 · 待命", "正常", None, False, True, False),
    ],
}

# 表头副标题沿用已核对过的文案（客厅/主卧的“N 个设备”待用户确认后再改）
ROOM_SUBS = {
    "客厅": "5 个设备 · 23.5°C · 湿度 48%",
    "主卧": "2 个设备 · 24.0°C · 湿度 50%",
    "厨房": "3 个设备 · 22.8°C · 湿度 55%",
    "浴室": "3 个设备 · 23.1°C · 湿度 62%",
}

ROOM_ORDER = ["客厅", "主卧", "厨房", "浴室"]

# ---- 设备类型与排序（同类相邻；同类内保持添加顺序）----
TYPE_ORDER = ["灯", "窗帘", "空调", "插座", "排风", "传感器", "摄像头", "场景"]
DEVICE_TYPE = {
    "主灯": "灯", "床头灯": "灯", "暖灯": "灯", "落地灯": "灯",
    "窗帘": "窗帘", "空调": "空调", "插座": "插座", "排风": "排风",
    "温湿度": "传感器", "燃气传感": "传感器", "漏水传感": "传感器",
    "摄像头": "摄像头", "晚安模式": "场景",
}


def room_devices(room):
    """该房间的设备列表 = 设计源唯一真值；按类型分组后返回（房间页与控件表共用）。"""
    tiles = ROOM_TILES[room]
    return sorted(tiles, key=lambda d: TYPE_ORDER.index(DEVICE_TYPE.get(d[0], "场景")))


# 动态设备区的可视范围：3 列 × 2 行 = 6 格；超出 → 纵向滚动
TILE_COLS, TILE_ROWS = 3, 2
TILE_VIEW = (40, 112, 744, 352)     # 设备区可视框（x,y,w,h），第 3 行只露一条


def room_is_scroll(room):
    return len(room_devices(room)) > TILE_COLS * TILE_ROWS


# ---- 二级页几何（标注图 import，不手抄）----
TILE_DETAIL_BTN = (158, 12, 52, 24)     # 设备格内「详情」按钮（相对格子原点）
SCENE_EXEC_BTN = (14, 104, 196, 32)     # 场景格内「执行」按钮（相对格子原点）
SUB_BACK_BOX = (40, 28, 96, 28)
DETAIL_BOXES = {
    "power": (296, 126, 60, 32),
    "bright": (52, 205, 316, 26),
    "cct": (52, 260, 316, 26),
    "timer1": (696, 130, 60, 32),
    "timer2": (696, 180, 60, 32),
    "timer_add": (420, 232, 120, 32),
    "info": (40, 300, 720, 140),
}
NOTIFY_BOXES = {
    "read_all": (620, 28, 140, 28),
    "rows": [(660, 126, 80, 28), (660, 210, 80, 28), (660, 294, 80, 28)],
    "clear": (40, 372, 120, 32),
}
ENERGY_BOXES = {
    "today": (500, 28, 72, 28),
    "week": (580, 28, 72, 28),
    "chart": (40, 104, 440, 300),
    "share": (500, 104, 260, 300),
}
SETTINGS_BOXES = {
    "dark": (696, 118, 60, 32),
    "notify": (696, 178, 60, 32),
    "lock": (500, 244, 240, 22),
    "net": (40, 284, 720, 52),
    "about": (40, 344, 720, 52),
    "reset": (40, 404, 140, 32),
}
SETTINGS_ROWS = [("深色模式", "界面配色"), ("通知提醒", "主控铃铛角标"),
                 ("自动锁屏", "无操作后 60 秒")]
# 设置页所有整行卡共用同一行距（52 高 + 8 间隙）；禁止再写死 y，避免某行贴住上一行
SETTINGS_ROW_H = 52
SETTINGS_ROW_GAP = 8
SETTINGS_ROW_PITCH = SETTINGS_ROW_H + SETTINGS_ROW_GAP
SETTINGS_ROW_Y0 = 104


def sub_header(title, sub, back_label):
    return [bg_image(),
            btn(*SUB_BACK_BOX, back_label, CARD2, T1, 9),
            t(152, 46, title, 24, T1, "700"),
            t(152, 66, sub, 10, T3),
            line(40, 88, 760, 88)]


def detail_frame():
    b = DETAIL_BOXES
    out = sub_header("主灯", "客厅 · 3000K · 在线", "‹ 返回")
    out += [card(40, 104, 340, 180),
            t(60, 140, "电源", 12, T2, "600"),
            toggle(*b["power"][:2], True),
            t(60, 200, "亮度", 12, T2, "600"),
            slider(60, 218, 300, 0.8), t(300, 200, "80%", 10, T3),
            t(60, 258, "色温", 12, T2, "600"),
            slider(60, 276, 300, 0.45), t(300, 258, "3000K", 10, T3),
            card(400, 104, 360, 180),
            t(420, 130, "定时", 12, T2, "600"),
            # 动态条目区：设计图不画对象，运行期由应用代码创建定时行
            btn(*b["timer_add"], "添加定时", CARD2, ACCENT, 9),
            card(40, 300, 720, 140),
            t(60, 328, "设备信息（只读）", 12, T2, "600"),
            t(60, 356, "信号强度", 9, T3), t(60, 376, "强", 16, T1, "600"),
            t(240, 356, "固件版本", 9, T3), t(240, 376, "1.4.2", 16, T1, "600"),
            t(420, 356, "累计用电", 9, T3), t(420, 376, "36.8 kWh", 16, T1, "600"),
            t(620, 356, "最近上报", 9, T3), t(620, 376, "2 分钟前", 16, T1, "600"),
            tag(690, 320)]
    return "".join(out)


def notify_frame():
    b = NOTIFY_BOXES
    out = sub_header("通知", "示例：3 条 · 2 条未读", "‹ 主控")
    out.append(btn(*b["read_all"], "全部已读", CARD2, ACCENT, 9))
    # 动态条目区：设计图不画对象，运行期由应用代码创建通知行
    out.append(btn(*b["clear"], "清空列表", CARD2, T1, 9))
    return "".join(out)


def energy_frame():
    b = ENERGY_BOXES
    out = sub_header("能源", "今日 12.4 kWh · 本月 268 kWh", "‹ 主控")
    out += [btn(*b["today"], "今日", ACCENT, BG, 9),
            btn(*b["week"], "本周", CARD2, T1, 9),
            card(40, 104, 440, 300),
            t(60, 132, "近 7 日用电（只读）", 12, T2, "600")]
    vals = [0.45, 0.62, 0.38, 0.78, 0.55, 0.9, 0.66]
    for i, v in enumerate(vals):
        h = 180 * v
        out.append(r(70 + i * 56, 360 - h, 36, h, ACCENT if i == 5 else CARD2,
                     "none", 4))
        out.append(t(88 + i * 56, 378, f"{18 + i}日", 8, T3, "400", "middle"))
    out += [card(500, 104, 260, 300),
            t(520, 132, "房间占比（只读）", 12, T2, "600")]
    for i, (room, pct) in enumerate([("客厅", "38%"), ("主卧", "27%"),
                                     ("厨房", "22%"), ("浴室", "13%")]):
        y = 156 + i * 56
        out += [t(520, y, room, 10, T1, "600"),
                t(740, y, pct, 10, T2, "600", "end"),
                r(520, y + 8, 220, 6, "#222B38", "none", 3),
                r(520, y + 8, 220 * int(pct[:-1]) / 100.0, 6, ACCENT, "none", 3)]
    return "".join(out)


def settings_frame():
    b = SETTINGS_BOXES
    out = sub_header("设置", "Haven Home · 网关在线", "‹ 主控")
    for i, (name, sub) in enumerate(SETTINGS_ROWS):
        y = SETTINGS_ROW_Y0 + i * SETTINGS_ROW_PITCH
        out += [card(40, y, 720, SETTINGS_ROW_H),
                t(60, y + 24, name, 12, T1, "600"),
                t(60, y + 40, sub, 8.5, T3)]
    out.append(toggle(*b["dark"][:2], True))
    out.append(toggle(*b["notify"][:2], True))
    out += [slider(520, 252, 200, 0.5)]
    for i, (name, val) in enumerate([("Wi-Fi", "Haven_5G · 已连接 · 信号强"),
                                     ("关于", "版本 1.0.0 · 构建 2026-05-18")]):
        y = SETTINGS_ROW_Y0 + (i + len(SETTINGS_ROWS)) * SETTINGS_ROW_PITCH
        out += [card(40, y, 720, SETTINGS_ROW_H),
                t(60, y + 24, name, 12, T1, "600"),
                t(60, y + 40, val, 8.5, T3),
                t(736, y + 29, "›", 16, ACCENT, "400", "end")]
    out.append(btn(*b["reset"], "恢复默认", CARD2, RED, 9))
    return "".join(out)


# ---------------- Wi-Fi 连接（完全参考 app-wifi-scan-conn-no-flow 的单页+弹层结构） ----------------
WIFI_BOXES = {
    # 与其它二级页同一页骨架：动作按钮在页头带 (y=28,h=28)，内容从 y=104 起
    "scan": (640, 28, 120, 28),
    "list": (40, 104, 720, 348),
    "hint": (40, 458, 700, 16),
    # 密码半页（默认隐藏）
    "scrim": (0, 0, 800, 480),
    "sheet": (0, 220, 800, 260),
    "sheet_handle": (384, 226, 32, 3),
    "pwd_ssid": (24, 236, 640, 24),
    "pwd_close": (752, 230, 32, 32),
    "pwd_ta": (24, 286, 520, 40),
    "connect": (560, 286, 216, 40),
    "keyboard": (24, 336, 752, 136),
    # 忘记对话框（默认隐藏）
    "dlg_scrim": (0, 0, 800, 480),
    "dlg_card": (220, 140, 360, 200),
    "dlg_ssid": (240, 200, 320, 18),
    "dlg_hint": (240, 222, 320, 16),
    "dlg_forget": (240, 288, 96, 36),
    "dlg_disconnect": (352, 288, 96, 36),
    "dlg_cancel": (464, 288, 96, 36),
}


def wifi_frame():
    """默认态：空 list_box（行由 native 按扫描结果动态创建）+ 扫描 + 底部提示。"""
    out = sub_header("Wi-Fi", "点「扫描」发现网络", "‹ 设置")
    out += [btn(*WIFI_BOXES["scan"], "扫描", CARD2, ACCENT, 9)]
    return "".join(out)


def wifi_sheet_frame():
    """设计预览用：密码半页展开态（EEZ 里是 overlay_root，默认隐藏）。"""
    b = WIFI_BOXES
    out = [wifi_frame(),
           r(0, 0, 800, 480, "#000000", "none", 0),
           r(*b["sheet"], "#101720", "none", 0),
           r(*b["sheet_handle"], EDGE, "none", 2),
           t(24, 254, "YJT-1号楼办公", 18, T1, "700"),
           t(760, 254, "×", 18, T2, "400", "middle"),
           r(24, 286, 520, 40, CARD2, EDGE, 8),
           t(36, 311, "输入密码", 11, T3),
           btn(560, 286, 216, 40, "连接", ACCENT, BG, 11)]
    out.append(_keyboard(336))
    return "".join(out)


def wifi_dialog_frame():
    """设计预览用：忘记确认框展开态（EEZ 里是 dlg_root，默认隐藏）。"""
    b = WIFI_BOXES
    out = [wifi_frame(),
           r(0, 0, 800, 480, "#000000", "none", 0),
           r(*b["dlg_card"], "#101720", EDGE, 14),
           t(240, 172, "忘记此网络？", 15, T1, "700"),
           t(240, 210, "YJT-1号楼办公", 11, T2),
           t(240, 234, "将删除已保存的密码，下次连接需重新输入。", 9.5, T3),
           btn(240, 288, 96, 36, "忘记", "#3A1A18", RED, 10),
           btn(352, 288, 96, 36, "断开", CARD2, T1, 10),
           btn(464, 288, 96, 36, "取消", CARD2, T1, 10)]
    return "".join(out)


def _keyboard(y):
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    out = []
    for r_i, chars in enumerate(rows):
        for c_i, ch in enumerate(chars):
            kx, ky = 24 + c_i * 72, y + r_i * 40
            out += [r(kx, ky, 64, 34, CARD2, "none", 6),
                    t(kx + 32, ky + 23, ch, 12, T1, "500", "middle")]
    by = y + 3 * 40
    out += [r(24, by, 64, 34, CARD2, "none", 6),
            t(56, by + 23, "123", 10, T2, "400", "middle"),
            r(96, by, 392, 34, CARD2, "none", 6),
            t(292, by + 23, "空格", 10, T2, "400", "middle"),
            r(496, by, 64, 34, CARD2, "none", 6),
            t(528, by + 23, "删除", 9, T2, "400", "middle"),
            r(568, by, 208, 34, ACCENT, "none", 6),
            t(672, by + 23, "完成", 11, BG, "600", "middle")]
    return "".join(out)


def living_frame():
    return room_frame("客厅", ROOM_SUBS["客厅"], ROOM_TILES["客厅"])


def bedroom_frame():
    return room_frame("主卧", ROOM_SUBS["主卧"], ROOM_TILES["主卧"])


def main():
    os.makedirs(OUT, exist_ok=True)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="Microsoft YaHei,Noto Sans SC,'
        f'PingFang SC,sans-serif">',
        r(0, 0, W, H, BG, "none", 0),
        t(40, 46, "Haven Home · 主控 + 房间页设计", 28, T1, "700"),
        t(40, 70, "主控 = 场景 + 房间；房间页 = 设备小方格；先不做侧栏和复杂跳转",
          12, T2),
        t(40, 96, "主控", 10, ACCENT),
        t(860, 96, "客厅（房间模板）", 10, ACCENT),
        t(1680, 96, "主卧（同一模板，换设备）", 10, ACCENT),
    ]
    out.append(f'<g transform="translate(40,110)">{main_frame()}</g>')
    out.append(f'<g transform="translate(860,110)">{living_frame()}</g>')
    out.append(f'<g transform="translate(1680,110)">{bedroom_frame()}</g>')
    out += [t(40, 636, "规则", 14, T1, "700"),
            t(40, 660, "主控只放场景和房间；房间卡整块可点，进入后用左上角“‹ 主控”返回。",
              10, T2),
            t(40, 680, "房间内每格一个设备：灯/窗帘/空调可操作，温湿度/摄像头只读；"
                       "不做每格透明跳转。", 10, T2),
            t(40, 700, "动态先不做；确认布局后再决定是否保留回家/晚安等 3 个场景动效。",
              10, T3)]
    out.append("</svg>")
    svg = os.path.join(OUT, "_control_concept.svg")
    io.open(svg, "w", encoding="utf-8", newline="\n").write("".join(out))
    print("written", svg)
    try:
        import cairosvg
        png = os.path.join(OUT, "_control_concept.png")
        cairosvg.svg2png(url=svg, write_to=png, output_width=2000,
                         output_height=571)
        print("written", png)
    except Exception as e:
        print("png skip", e)


if __name__ == "__main__":
    main()
