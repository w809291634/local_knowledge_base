# -*- coding: utf-8 -*-
"""从设计帧识别设备读数文本，追加为 value 类控件（out_read）。

读数 = 温度/湿度/百分比/功率/电量/状态等从设备读来的值；标题、说明、按钮文案不算。
已经在现有控件框内的文本不重复标注（例如滑条旁的值、卡片里的状态）。
"""
import re

import simple_control as sc

UNITS = r"(°C?|%|W|kWh|Mbps|ms|dBm|次|分钟|小时|秒|K)"
STATUS = {"开", "关", "在线", "离线", "已连接", "已布防", "已撤防", "强", "弱",
          "正常", "运行正常", "制冷中", "制热中", "送风中", "已加密", "1080P"}
STATUS_RE = re.compile(r"(在线|离线|已连接|未连接|已布防|撤防|已接入|正在连接|"
                       r"已加入|已加密|已开启|未读|离家模式)")
TIME_RE = re.compile(r"\d{1,2}:\d{2}|刚才|昨天|今天")
DATE_RE = re.compile(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}月\d{1,2}日|"
                     r"周[一二三四五六日天]|(上午|下午|晚上|早上|中午)好")
COUNT_RE = re.compile(r"\d+\s*(个设备|个房间|个动作|条)")
INFO_RE = re.compile(r"(版本|固件|构建|网关).*\d|\d.*(版本|固件|构建|网关)")
# H5 批注：指定文本不生成 value 控件，仍由设计帧渲染为静态文本
SKIP = {("客厅", "1080P · 已加密")}
# 随滑条变化的 UI 值：属于 in_read（UI 自己控制），不是外部读数
UI_READ = {("窗帘详情", "70%"), ("设置", "无操作后 60 秒"),
           ("添加设备·配网中", "70%")}
UI_READ_SUB = ("开合 70%",)
EXCLUDE = ("请", "支持", "约需", "距离", "点击", "点「", "进入", "返回", "仅", "步",
           "调至", "升温", "降温", "断电", "保持", "需先", "第 ", "添加后", "后可",
           "自动布防", "自动撤防", "仍可", "不可用", "暂无设备")


def _texts(frame):
    out = []
    for m in re.finditer(r"<text([^>]*)>([^<]*)</text>", frame or ""):
        attrs, txt = m.group(1), m.group(2)
        if not txt.strip():
            continue

        def a(name, d=None):
            mm = re.search(name + r'="([^"]*)"', attrs)
            return mm.group(1) if mm else d

        out.append({"x": float(a("x", 0)), "y": float(a("y", 0)),
                    "size": float(a("font-size", 14)),
                    "fill": a("fill", "0xF4F7FB").upper().replace("#", "0x"),
                    "anchor": a("text-anchor", "start"), "text": txt})
    return out


LABELS = {"主控", "场景", "房间", "设备", "电源", "亮度", "色温", "定时", "模式",
          "风速", "开合度", "当前温度", "上限", "下限", "超限推送提醒", "通知", "能源",
          "设置", "Wi-Fi", "安防", "关于", "云台", "实时画面", "设备名称",
          "舒适区间与报警", "定时关闭", "定时开合", "定时通电", "过载保护"}


def _is_value(t):
    s = t["text"].strip()
    if not s or s in LABELS or any(w in s for w in EXCLUDE):
        return False
    if s.startswith("近 ") and "小时" in s:      # 「近 24 小时」是标题
        return False
    if s in STATUS or STATUS_RE.search(s):
        return True
    if TIME_RE.search(s) or DATE_RE.search(s) or COUNT_RE.search(s) or INFO_RE.search(s):
        return True
    return bool(re.search(r"\d", s) and re.search(UNITS, s))


def _icon_initial(t, texts):
    """类型卡里的「开/关」图标首字，不是状态读数：同页附近有以此字开头的长文本。"""
    s = t["text"].strip()
    if len(s) != 1:
        return False
    return any(len(u["text"].strip()) > 1 and u["text"].strip().startswith(s) and
               abs(u["x"] - t["x"]) < 90 and abs(u["y"] - t["y"]) < 45 for u in texts)


def _near_slider(t, rows):
    """滑条/进度条旁边的数值显示属于 UI 内部读（随控件变化）。"""
    for nm, cat, _act, _beh, b in rows:
        if cat != "slider" and nm != "进度":
            continue
        if (b[0] - 20 <= t["x"] <= b[0] + b[2] + 20 and
                b[1] - 10 <= t["y"] <= b[1] + b[3] + 10):
            return True
    return False


def _blocked(t, rows):
    """文字落在“本身就是控件”的小框里就不再单独标注。

    宽卡片/房间格/只读卡里的读数仍要标；开关/滑条自身的小框、按钮文案、
    输入框内容不重复标。
    """
    for nm, cat, _act, _beh, b in rows:
        if not (b[0] <= t["x"] <= b[0] + b[2] and b[1] <= t["y"] <= b[1] + b[3]):
            continue
        if cat in ("nav", "back", "scene"):
            if b[2] <= 220:
                return True
        elif cat in ("toggle", "slider"):
            if not (b[2] > 120 or b[3] > 60):
                return True
        elif cat == "read" and nm in ("搜索框", "设备名称"):
            return True
    return False


def _box(t):
    size = sc.ui_size(t["text"], t["size"])
    w = int(sum(size if ord(c) > 127 else size * 0.56 for c in t["text"])) + 4
    left = t["x"]
    if t["anchor"] == "middle":
        left = t["x"] - w / 2.0
    elif t["anchor"] == "end":
        left = t["x"] - w
    return (int(left), int(t["y"] - size * 0.92), w, int(size * 1.5))


def value_rows(page, frame, rows):
    """返回追加的 (name, 'value', 作用, '只刷新', box) 行。"""
    out = []
    texts = _texts(frame)
    for t in texts:
        name = t["text"].strip()
        if (page, name) in SKIP:
            continue
        if not _is_value(t) or _blocked(t, rows) or _icon_initial(t, texts):
            continue
        ui = ((page, name) in UI_READ or any(x in name for x in UI_READ_SUB)
              or (("%" in name or name.endswith("K")) and _near_slider(t, rows)))
        out.append((t["text"], "uivalue" if ui else "value",
                    "随 UI 滑条/状态变化" if ui else "显示设备读数", "只刷新", _box(t)))
    return out


def add_value_rows(pages):
    for i, (name, frame, entry, exit_, rows) in enumerate(pages):
        rows = list(rows or [])
        rows += value_rows(name, frame, rows)
        pages[i] = (name, frame, entry, exit_, rows)
