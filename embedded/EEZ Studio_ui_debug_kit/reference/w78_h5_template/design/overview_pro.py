# -*- coding: utf-8 -*-
"""全览专业版（单文件 H5）：满足用户 5 条口径。

① 控件按数据流向分 6 类：内读 / 外读 / 内写 / 外写 / 跳转按钮 / 跳动手势
② 每页帧上按 6 色描边 + 序号，一眼看出哪些是控件
③ 跳转按钮画直线箭头 + 目标页胶囊；跳动手势画页面边缘的弧形箭头
④ 分层规则：一级 = 与主页同一种切换方式可达（pageview tab / 侧栏）；
   从一级进入的新页 = 二级，依次类推
⑤ 三个视图可切换：分层总览 / 跳转演练（帧上真控件可点真跳页，带真机方向横滑）/ 高清设计图

数据全部来自 pages.PAGES + nav_map + export_ui.page_data()，不另画界面。
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import simple_control as sc        # noqa: E402
import pages as pg                 # noqa: E402
import export_ui as eu             # noqa: E402

OUT = os.path.join(sc.OUT, "overview_pro.html")
OUT_FRAG = os.path.join(sc.OUT, "overview_pro.fragment.html")

IO_COLORS = {
    "in_read": "#7fb3ff", "out_read": "#8fa2b8", "in_write": "#c08cff",
    "out_write": "#5fd3a6", "nav": "#f2b45c", "gesture": "#ff8fb8",
}
IO_NAME = {
    "in_read": "内部读", "out_read": "外部读", "in_write": "内部写",
    "out_write": "外部写", "nav": "跳转按钮", "gesture": "跳动手势",
}
IO_DESC = {
    "in_read": "从 UI 自身取数（页名、计数、缓存时间）",
    "out_read": "从硬件取数（传感值、功率、画面）",
    "in_write": "写 UI 层数据（已读、筛选、配色、本地设置）",
    "out_write": "写硬件（开关、亮度、开合、模式、布防）",
    "nav": "按钮/返回 → 跳到指定页",
    "gesture": "左右滑动 → 切换界面",
}

# 个别控件的数据流向按语义覆盖，不靠通用规则猜
OVERRIDES = {
    ("全部设备", "搜索框"): "in_read",
    ("离线态", "同步信息"): "in_read",
    ("主卧", "晚安模式"): "in_read",
    ("灯详情", "添加定时"): "in_write",
    ("场景详情", "编辑动作"): "in_write",
    ("能源统计", "今日"): "in_write",
    ("能源统计", "本周"): "in_write",
}

ROOMS = ["客厅", "主卧", "厨房", "浴室"]
DETAILS = ["灯详情", "空调详情", "窗帘详情", "传感详情", "插座详情", "摄像头详情"]


def gestures():
    """{页: [(方向标签, 目标说明, 手势框)]}，框在页面左右边缘。"""
    g = {}
    cyc = ROOMS + DETAILS
    for i, p in enumerate(cyc):
        nxt = cyc[(i + 1) % len(cyc)]
        prv = cyc[(i - 1) % len(cyc)]
        who = "房间页" if p in ROOMS else "详情页"
        g[p] = [{"label": "← 滑", "to": "上一个%s：%s" % (who, prv),
                 "go": prv, "box": (0, 130, 26, 260)},
                {"label": "→ 滑", "to": "下一个%s：%s" % (who, nxt),
                 "go": nxt, "box": (774, 130, 26, 260)}]
    g["能源统计"] = [{"label": "← → 滑", "to": "切换 今日 / 本周 视图",
                  "go": "能源统计", "box": (0, 130, 26, 260)}]
    return g


def io_of(page, row):
    k = OVERRIDES.get((page, row["name"]))
    if k:
        return k
    if row["behav"] in ("换页", "返回"):
        return "nav"
    if row["behav"] == "下发硬件":
        return "out_write"
    if row["cat"] == "uivalue":
        return "in_read"
    if row["cat"] in ("read", "value"):
        return "out_read"
    return "in_write"


def _rects(svg):
    out = []
    for m in re.finditer(r'<rect([^>]*?)/?>', svg or ""):
        a = m.group(1)

        def g(n):
            mm = re.search(n + r'="([^"]*)"', a)
            return mm.group(1) if mm else None
        try:
            out.append((float(g("x") or 0), float(g("y") or 0),
                        float(g("width") or 0), float(g("height") or 0)))
        except ValueError:
            pass
    return out


def _glyph_box(svg, cat, box):
    """整卡开关/滑条：从设计帧里找出卡内实际 glyph，供 H5 把序号标在控件本体上。"""
    rs = [r for r in _rects(svg)
          if r[0] >= box[0] and r[1] >= box[1] and
          r[0] + r[2] <= box[0] + box[2] and r[1] + r[3] <= box[1] + box[3]]
    if cat == "toggle":
        cand = [r for r in rs if 40 <= r[2] <= 50 and 22 <= r[3] <= 26]
        return cand[0] if cand else None
    cand = [r for r in rs if r[3] <= 8 and r[2] >= 80]
    if cand:
        b = max(cand, key=lambda x: x[2])
        return (b[0], b[1] - 7, b[2], 20)
    return None


def build():
    data = eu.page_data()
    order = [t for (t, _f, _e, _x, _r) in pg.PAGES]
    parents = {}
    for p, d in data.items():
        for r in d["rows"]:
            if r["target"]:
                parents.setdefault(r["target"], []).append((p, r["name"], r["cat"]))
    depth = {order[0]: 0}
    changed = True
    while changed:
        changed = False
        for p, d in data.items():
            if p not in depth:
                ds = [depth[a] + 1 for (a, _n, _c) in parents.get(p, []) if a in depth]
                if ds:
                    depth[p] = min(ds)
                    changed = True
    status = {q for q in order if q != order[0] and not parents.get(q)}
    for q in status:
        depth[q] = 1            # 状态页不单独成层：按它服务的页面归层

    ges = gestures()
    WIFI_SHEET = {"弹层·密码框", "弹层·连接", "弹层·关闭", "弹层·键盘"}
    WIFI_DLG = {"对话框·忘记", "对话框·断开", "对话框·取消"}
    out = {}
    for p in order:
        d = data[p]
        rows = []
        for r in d["rows"]:
            if p == "Wi-Fi 设置" and (r["name"] in WIFI_SHEET or r["name"] in WIFI_DLG):
                continue                     # 弹层控件在单独的“展开态”卡里标，别画在基础页上
            io_k = io_of(p, r)
            mb = None
            if r["cat"] in ("toggle", "slider") and (r["box"][2] > 120 or r["box"][3] > 60):
                gb = _glyph_box(d["svg"], r["cat"], r["box"])
                mb = list(gb) if gb else None
            rows.append({"n": r["n"], "name": r["name"], "io": io_k,
                         "cat": r["cat"], "act": r["act"], "box": r["box"],
                         "markBox": mb,
                         "target": r["target"] if io_k == "nav" else "",
                         "dyn": r["behav"] == "返回"})
        out[p] = {"svg": d["svg"], "rows": rows, "layer": depth[p] + 1,
                  "status": p in status,
                  "entry": d["entry"], "exit": d["exit"],
                  "gesture": ges.get(p, [])}

    # 弹层展开态（设计预览帧，不是 EEZ 页）：让密码半页/忘记框的控件也有正确位置与序号
    b = sc.WIFI_BOXES
    sheet_rows = [
        {"n": 1, "name": "密码框", "io": "out_read", "cat": "read", "act": "", "box": list(b["pwd_ta"]), "target": "", "dyn": False},
        {"n": 2, "name": "连接", "io": "out_write", "cat": "scene", "act": "", "box": list(b["connect"]), "target": "", "dyn": False},
        {"n": 3, "name": "关闭", "io": "out_write", "cat": "scene", "act": "", "box": list(b["pwd_close"]), "target": "", "dyn": False},
        {"n": 4, "name": "键盘", "io": "out_read", "cat": "read", "act": "", "box": list(b["keyboard"]), "target": "", "dyn": False},
    ]
    dlg_rows = [
        {"n": 1, "name": "忘记", "io": "out_write", "cat": "scene", "act": "", "box": list(b["dlg_forget"]), "target": "", "dyn": False},
        {"n": 2, "name": "断开", "io": "out_write", "cat": "scene", "act": "", "box": list(b["dlg_disconnect"]), "target": "", "dyn": False},
        {"n": 3, "name": "取消", "io": "out_write", "cat": "scene", "act": "", "box": list(b["dlg_cancel"]), "target": "", "dyn": False},
    ]
    out["Wi-Fi 密码半页"] = {"svg": sc.wifi_sheet_frame(), "rows": sheet_rows, "layer": 5,
                           "status": False, "entry": "Wi-Fi 设置·弹层", "exit": "Wi-Fi 设置",
                           "gesture": []}
    out["忘记网络"] = {"svg": sc.wifi_dialog_frame(), "rows": dlg_rows, "layer": 5,
                     "status": False, "entry": "Wi-Fi 设置·对话框", "exit": "Wi-Fi 设置",
                     "gesture": []}
    # 动态条目区：设计图不画对象，H5 只框区域；条目由应用代码在运行期创建
    zones = {}
    for z in pg.DYN_ZONES:
        assert z["page"] in out, "动态区指向不存在的页：%s" % z["page"]
        x, y, w, h = z["box"]
        assert 0 <= x and 0 <= y and x + w <= 800 and y + h <= 480, "动态区越界：%s" % z["name"]
        tag = "动态区 · 运行期由应用代码生成"
        zones.setdefault(z["page"], []).append({
            "name": z["name"], "box": list(z["box"]), "note": z["note"],
            "tag": tag, "tagw": len(tag) * 11 + 16})
    for p in out:
        out[p]["dynz"] = zones.get(p, [])
    # 开机自检：H5 设计预览页（不进 EEZ、不参与导航；单行动态字条）
    boot_rows = [
        {"n": 1, "name": "进度条", "io": "out_read", "cat": "read",
         "act": "自检进度 0–100%", "box": [140, 300, 520, 8], "target": "",
         "markBox": None, "dyn": False},
        {"n": 2, "name": "状态字条", "io": "out_read", "cat": "read",
         "act": "随当前检测项切换（单行）", "box": [300, 332, 186, 18],
         "target": "", "markBox": None, "dyn": True},
    ]
    out["开机自检"] = {"svg": sc.boot_init_frame(), "rows": boot_rows, "layer": 1,
                       "status": False, "entry": "上电", "exit": "主控",
                       "gesture": [], "dynz": []}
    order = ["开机自检"] + order
    lost = [(p, r["n"], r["name"]) for p in order if p in data for r in out[p]["rows"]
            if any(q["name"] == r["name"] and q["behav"] == "换页" for q in data[p]["rows"])
            and r["io"] != "nav"]
    assert not lost, "覆盖判类吃掉了换页控件的跳转：%s" % lost
    return {"pages": out, "order": order,
            "io": {"color": IO_COLORS, "name": IO_NAME, "desc": IO_DESC},
            "layerNote": {1: "一级：与主页同一种切换方式可达（本工程无 pageview tab / 侧栏，故只有主控）",
                          2: "二级：从一级页用按钮进入的新子页",
                          3: "三级：从二级页进入的新子页",
                          4: "四级：从三级页进入的新子页",
                          5: "五级：从四级页进入的新子页"}}


CSS = r"""
:root{--bg:#05080f;--bg2:#0a0f18;--card:#121822;--edge:#27313f;--t1:#f4f7fb;--t2:#b9c4d4;
--t3:#75859c;--nav:#f2b45c;--r:14px;--f:"Microsoft YaHei","PingFang SC","Noto Sans SC",system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1300px 700px at 15% -15%,#0e1522,#05080f 62%);
color:var(--t1);font:13px/1.65 var(--f);-webkit-font-smoothing:antialiased}
header{position:sticky;top:0;z-index:30;background:rgba(10,15,24,.88);backdrop-filter:blur(10px);
border-bottom:1px solid var(--edge);padding:9px 22px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.brand{font-size:14px;font-weight:700;letter-spacing:.3px}
.tabs{display:flex;gap:6px}
.btn{font:12px var(--f);color:var(--t1);background:#1a2230;border:1px solid var(--edge);
border-radius:999px;padding:5px 13px;cursor:pointer;transition:.15s}
.btn:hover{background:#222c3c}
.btn.on{border-color:var(--nav);color:var(--nav);background:rgba(242,180,92,.12)}
.sp{flex:1}
.crumb{color:var(--t3);font-size:12px}.crumb b{color:var(--nav)}
main{padding:18px 22px 40px;max-width:2100px;margin:0 auto}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px;padding:10px 14px;
border:1px solid var(--edge);border-radius:var(--r);background:rgba(18,24,34,.6)}
.lg{display:inline-flex;align-items:center;gap:7px;font-size:11.5px;color:var(--t2);
border:1px solid var(--edge);border-radius:999px;padding:3px 11px 3px 8px;cursor:pointer;transition:.15s}
.lg:hover{border-color:#3a4658}
.lg.off{opacity:.35}
.lg i{width:10px;height:10px;border-radius:3px;flex:none}
.lg b{font-weight:600}
.lg em{font-style:normal;color:var(--t3);margin-left:2px}
h2.sec{display:flex;align-items:center;gap:10px;font-size:12px;font-weight:600;letter-spacing:1.4px;
color:var(--t3);text-transform:uppercase;margin:26px 0 12px}
h2.sec:after{content:"";flex:1;height:1px;background:var(--edge)}
h2.sec .cnt{color:#5a6a80;letter-spacing:0;text-transform:none;font-size:11.5px}
.layerrow{display:flex;gap:18px;overflow-x:auto;padding:4px 4px 18px;scroll-snap-type:x proximity}
.layerrow::-webkit-scrollbar{height:9px}
.layerrow::-webkit-scrollbar-thumb{background:#22303f;border-radius:8px}
.pcard{position:relative;flex:0 0 auto;width:520px;border:1px solid var(--edge);border-radius:var(--r);
background:var(--card);overflow:hidden;cursor:pointer;transition:.16s;scroll-snap-align:start}
.pcard:hover{border-color:#3a4658;transform:translateY(-2px)}
.pcard.sel{border-color:var(--nav);box-shadow:0 0 0 2px var(--nav),
  0 14px 34px rgba(0,0,0,.5)}
.pcard.sel:after{content:"已选中";position:absolute;top:-10px;left:14px;font-size:10.5px;
  font-weight:700;color:#05080f;background:var(--nav);border-radius:999px;padding:1px 9px}
.pcard.flash{animation:pop .9s ease}
@keyframes pop{0%{box-shadow:0 0 0 2px var(--nav),0 0 0 0 rgba(242,180,92,.55)}
70%{box-shadow:0 0 0 2px var(--nav),0 0 0 18px rgba(242,180,92,0)}
100%{box-shadow:0 0 0 2px var(--nav),0 0 0 0 rgba(242,180,92,0)}}
#dock{display:none;position:sticky;top:78px;border:1px solid var(--nav);border-radius:18px;
  background:var(--bg2);padding:12px 12px 14px;max-height:calc(100vh - 96px);overflow:auto}
.wrap.docked #dock{display:block}
.wrap.docked{display:grid;grid-template-columns:minmax(0,1fr) minmax(520px,46vw);gap:18px;align-items:start}
#dock h3{margin:0 0 2px;font-size:15px;display:flex;align-items:center;gap:8px}
#dock .dh{color:var(--t3);font-size:11.5px;margin:0 0 10px}
#dock svg{display:block;width:100%;height:auto;background:#05080f;border-radius:12px}
#dockscrim{position:fixed;inset:0;background:rgba(3,6,12,.62);z-index:54;display:none}
@media (max-width:1400px){
  .wrap.docked{display:block}
  #dock{position:fixed;top:64px;right:14px;bottom:14px;left:auto;width:min(760px,92vw);
    z-index:55;max-height:none;box-shadow:0 24px 60px rgba(0,0,0,.6)}
  body.docked #dockscrim{display:block}
}
.pcard .stt{position:absolute;top:8px;right:8px;font-size:10.5px;color:#ff7a6b;border:1px solid #5a3038;border-radius:999px;padding:1px 7px;background:rgba(5,8,15,.7)}
.pcard .cap{padding:8px 11px;display:flex;align-items:center;gap:7px;font-size:13px;font-weight:600}
.pcard .cap .c{margin-left:auto;color:var(--t3);font-size:11px;font-weight:400}
.pcard svg.mini{display:block;width:100%;height:auto;background:#05080f}
.pcard .tags{padding:2px 11px 12px;display:block}
.tg{display:flex;flex-wrap:wrap;align-items:center;gap:4px 5px;margin:0 0 6px}
.tg:last-child{margin-bottom:0}
.tl{flex:0 0 78px;display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:700;
border:1px solid;border-radius:999px;padding:1px 8px;background:rgba(5,8,15,.5)}
.tl em{font-style:normal;margin-left:auto;font-weight:400;color:var(--t2);font-size:11px}
.pill{display:inline-flex;align-items:center;gap:6px;font:11px var(--f);border:1px solid var(--edge);
border-radius:999px;padding:2px 10px 2px 7px;color:var(--t2);cursor:pointer;transition:.15s;background:none}
.pill:hover{border-color:var(--nav);color:var(--nav)}
.pill i{width:7px;height:7px;border-radius:50%;flex:none;background:#f2b45c}
.pill.nav{background:#f2b45c;border-color:#f2b45c;color:#05080f;font-weight:700}
.pill.nav b{font-weight:900}
.pill.nav:hover{background:#ffc873;border-color:#ffc873;color:#05080f}
.pill.back{background:rgba(242,180,92,.10);border-color:#f2b45c;color:#f2b45c;font-weight:700}
.pill.back:hover{background:rgba(242,180,92,.28);border-color:#ffc873;color:#ffc873}
.pill.ges b{font-weight:900}
.pill.ges:hover{background:#ffa5c6;border-color:#ffa5c6;color:#05080f}
.pill.static{border-color:transparent;background:rgba(117,133,156,.09);color:#8b9aac;font-weight:400}
.pill.static:hover{border-color:transparent;color:#8b9aac;background:rgba(117,133,156,.14)}
g.hi rect{stroke-width:4!important;opacity:1!important}
g.hi circle{r:12}
.badge{font-size:10.5px;font-weight:700;border:1px solid var(--nav);color:var(--nav);
border-radius:999px;padding:1px 8px}
.stage{display:grid;grid-template-columns:minmax(0,1fr) 430px;gap:18px;align-items:start}
.big{border:1px solid var(--edge);border-radius:18px;overflow:hidden;background:#05080f;position:relative}
.big .pg{display:block}
.big svg{display:block;width:100%;height:auto}
svg g.hot{cursor:pointer}
svg g.hot>rect:not(.hit):not(.hitg){transition:.12s}
svg g.hot:hover>rect:not(.hit):not(.hitg){stroke-width:4}
svg rect.hit{fill:rgba(242,180,92,.10)}
svg g.hot:hover rect.hit{fill:rgba(242,180,92,.32)}
svg g.hot:active rect.hit{fill:rgba(242,180,92,.62)}
svg rect.hitg{fill:rgba(255,143,184,.12)}
svg g.hot:hover rect.hitg{fill:rgba(255,143,184,.34)}
svg g.hot:active rect.hitg{fill:rgba(255,143,184,.6)}
.trailbar{display:flex;align-items:center;gap:7px;flex-wrap:nowrap;overflow-x:auto;margin:0 0 10px;
  padding-bottom:2px;font-size:12px;color:var(--t3)}
.trailbar>*{flex:0 0 auto}
.trailbar .t{border:1px solid var(--edge);border-radius:999px;padding:1px 9px;color:var(--t2)}
.trailbar .t.now{border-color:var(--nav);color:var(--nav);font-weight:700}
.trailbar .ta{color:#44536a}
.btn[disabled]{opacity:.4;cursor:default}
.side{border:1px solid var(--edge);border-radius:18px;background:var(--bg2);padding:14px;
position:sticky;top:78px}
.side h3{margin:0 0 4px;font-size:15px}
.side .m{color:var(--t3);font-size:11.5px;margin:0 0 12px}
.grp{margin:0 0 12px}
.grp .gt{display:flex;align-items:center;gap:7px;font-size:11.5px;color:var(--t3);margin-bottom:5px}
.grp .gt i{width:9px;height:9px;border-radius:3px}
.grp .gt em{font-style:normal;color:#5a6a80;margin-left:auto;font-size:11px}
.item{display:flex;gap:8px;align-items:baseline;padding:4px 0;font-size:12px;
border-bottom:1px solid #101823}
.item:last-child{border-bottom:0}
.item .k{font-size:10.5px;color:var(--t3);min-width:18px}
.item .go{margin-left:auto;color:var(--nav);font-size:11.5px;cursor:pointer}
.item .go:hover{text-decoration:underline}
.hint{color:var(--t3);font-size:11.5px;line-height:1.75;margin:10px 0 0}
.gesline{display:flex;align-items:center;gap:8px;font-size:12px;color:#ff8fb8;
border:1px dashed #ff8fb8;border-radius:999px;padding:4px 12px;margin-top:8px}
@media (max-width:1250px){.stage{grid-template-columns:1fr}.side{position:static}}
/* 批注模式 */
#annpanel{position:fixed;right:22px;bottom:22px;width:310px;z-index:60;background:#0e1520;
  border:1px solid #ff5d5d;border-radius:14px;padding:12px;color:#e8eef7;font-size:12px;
  box-shadow:0 18px 40px rgba(0,0,0,.5);display:flex;flex-direction:column;gap:8px}
#annpanel[hidden]{display:none}
#annpanel .ah{display:flex;align-items:center;gap:8px}
#annpanel .ah b{font-size:13px;color:#ffb3b3;flex:1}
#annpanel textarea{width:100%;min-height:70px;resize:vertical;background:#05080f;color:#e8eef7;
  border:1px solid #27313f;border-radius:8px;padding:8px;font:12px/1.5 inherit}
#annpanel label{display:flex;align-items:center;gap:6px;color:#ffb3b3}
#annpanel .af{display:flex;gap:8px;justify-content:flex-end}
#annbar{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:58;
  display:none;align-items:center;gap:10px;background:#2a1414;border:1px solid #ff5d5d;
  color:#ffd7d7;border-radius:999px;padding:7px 14px;font-size:12px;box-shadow:0 8px 24px rgba(0,0,0,.4)}
#annbar.on{display:flex}
.annmark{pointer-events:none}
#ctxmenu{position:fixed;z-index:70;min-width:190px;background:#0e1520;border:1px solid #f2b45c;
  border-radius:10px;padding:6px;color:#e8eef7;font-size:12px;box-shadow:0 14px 34px rgba(0,0,0,.55)}
#ctxmenu[hidden]{display:none}
#ctxmenu .ct{color:#f2b45c;font-size:11px;padding:4px 8px 6px;border-bottom:1px solid #27313f;margin-bottom:4px}
#ctxmenu button{display:block;width:100%;text-align:left;background:none;border:0;color:#e8eef7;
  padding:7px 8px;border-radius:6px;font:12px inherit;cursor:pointer}
#ctxmenu button:hover{background:#1c2430}
"""

JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const IO = D.io;
let view = 'layers', cur = D.order[0];
let marksOn = true;              // 高清设计图默认显示全部控件标注（开关/滑条等）

/* ---- 批注模式：只采集修改指令，不改工程文件 ---- */
const ANN_KEY = 'w78_annotations_v2';
let anns = {};
try { anns = JSON.parse(localStorage.getItem(ANN_KEY) || '{}') || {}; } catch (e) { anns = {}; }
let annDraft = null, ctxTarget = null;
function annsOf(p){ return anns[p] || (anns[p] = []); }
function annTotal(){ return Object.keys(anns).reduce((n,p)=>n+anns[p].length,0); }
function annFor(p,n){ return annsOf(p).find(a=>a.type==='control' && a.n===n); }
function saveAnns(){ localStorage.setItem(ANN_KEY, JSON.stringify(anns)); }
function annMarks(page){
  const list = anns[page] || [];
  if(!list.length) return '';
  let s = '<g class="annmark">';
  list.forEach((a,ix)=>{
    if(a.type==='control'){
      const r = D.pages[page] && D.pages[page].rows.find(x=>x.n===a.n);
      if(!r) return;
      const b = r.markBox || r.box, tag = a.action==='delete' ? '删' : '改';
      s += '<rect x="'+b[0]+'" y="'+b[1]+'" width="'+b[2]+'" height="'+b[3]+
           '" rx="8" fill="none" stroke="#ff5d5d" stroke-width="2.2" stroke-dasharray="6 4"/>'+
           '<circle cx="'+(b[0]+b[2])+'" cy="'+b[1]+'" r="9" fill="#ff5d5d"/>'+
           '<text x="'+(b[0]+b[2])+'" y="'+(b[1]+4)+'" font-size="9.5" font-weight="700" '+
           'fill="#fff" text-anchor="middle" font-family="sans-serif">'+tag+'</text>';
    } else {
      s += '<g data-pin="'+a.id+'" style="pointer-events:all">'+
           '<circle cx="'+a.x+'" cy="'+a.y+'" r="7" fill="#ff5d5d" stroke="#fff" stroke-width="2"/>'+
           '<text x="'+a.x+'" y="'+(a.y+3.5)+'" font-size="8" font-weight="700" fill="#fff" '+
           'text-anchor="middle" font-family="sans-serif">'+(ix+1)+'</text></g>';
    }
  });
  return s + '</g>';
}
function annUI(){
  const n = annTotal(), bar = document.getElementById('annbar');
  const c = document.getElementById('anncount');
  if(c) c.textContent = n + ' 条批注';
  if(bar) bar.classList.toggle('on', n > 0);
  const ex = document.getElementById('anexport');
  if(ex) ex.textContent = n ? ('导出批注 ('+n+')') : '导出批注';
}
function annClose(){
  annDraft = null;
  const p = document.getElementById('annpanel');
  if(p) p.hidden = true;
}
function annOpen(a){
  annDraft = a;
  const p = document.getElementById('annpanel');
  document.getElementById('anntitle').textContent = a.type==='control'
    ? (a.page+' · #'+a.n+' '+(a.name||'')) : (a.page+' · ('+a.x+','+a.y+')');
  document.getElementById('annnote').value = a.note || '';
  const del = document.getElementById('anndel');
  del.checked = a.action === 'delete';
  document.getElementById('anndelrow').style.display = a.type==='control' ? 'flex' : 'none';
  p.hidden = false;
  document.getElementById('annnote').focus();
}
function annSave(){
  if(!annDraft) return;
  const d = annDraft, note = document.getElementById('annnote').value.trim();
  const del = document.getElementById('anndel').checked && d.type==='control';
  const list = annsOf(d.page);
  const idx = list.findIndex(x=> d.type==='control'
    ? (x.type==='control' && x.n===d.n) : (x.type==='pin' && x.id===d.id));
  if(!note && !del){
    if(idx>=0) list.splice(idx,1);
  } else {
    const rec = {type:d.type, page:d.page, note:note};
    if(d.type==='control'){
      rec.n = d.n; rec.name = d.name || ''; rec.box = d.box || null;
      rec.action = del ? 'delete' : 'modify';
    } else {
      rec.id = d.id; rec.x = d.x; rec.y = d.y;
    }
    if(idx>=0) list[idx] = rec; else list.push(rec);
  }
  saveAnns(); annClose(); render(); annUI();
}
function annExport(){
  const items = [];
  Object.keys(anns).forEach(p=>anns[p].forEach(a=>items.push(Object.assign({page:p}, a))));
  const blob = new Blob([JSON.stringify({project:'w78-smart-home', generated:new Date().toISOString(), items:items}, null, 2)],
                        {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'w78_annotations.json';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href), 1000);
}
function annLoc(svg, ev){
  const pt = svg.createSVGPoint();
  pt.x = ev.clientX; pt.y = ev.clientY;
  const loc = pt.matrixTransform(svg.getScreenCTM().inverse());
  return [Math.round(loc.x), Math.round(loc.y)];
}

const hist = [];                      // {view, cur, y, rows}
function pushState(){
  hist.push({view:view, cur:cur, y:window.scrollY,
    rows:[...document.querySelectorAll('.layerrow')].map(r=>r.scrollLeft)});
  if(hist.length>60) hist.shift();
}
function popState(){
  const h = hist.pop();
  if (!h) return false;
  view = h.view; cur = h.cur; trail = []; render();
  requestAnimationFrame(()=>{
    window.scrollTo(0, h.y);
    document.querySelectorAll('.layerrow').forEach((r,i)=>
      { r.scrollLeft = (h.rows && h.rows[i]) || 0; });
  });
  return true;
}
let ioOn = new Set(Object.keys(IO.color));

function showIo(r){ return ioOn.has(r.io); }

/* 帧上叠加：6 色控件框 + 序号 + 跳转箭头 + 手势弧 */
function mark(page, opts){
  const p = D.pages[page], o = opts || {};
  const lane = (o.lane !== false) && !o.slim;
  const VW = lane ? 992 : 800;
  let s = '<svg viewBox="0 0 '+VW+' 480" xmlns="http://www.w3.org/2000/svg">' + p.svg;
  if (lane) s += '<rect x="816" y="0" width="176" height="480" fill="#0a0f18"/>'
    + '<line x1="816" y1="0" x2="816" y2="480" stroke="#27313f"/>'
    + '<text x="828" y="16" font-size="10.5" fill="#5a6a80" font-family="sans-serif">'
    + '目标页</text>';
  s += '<defs>'
    + '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"'
    + ' orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#f2b45c"/></marker>'
    + '<marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"'
    + ' orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#ff8fb8"/></marker>'
    + '</defs>';
  if (o.marks !== false){
    (p.dynz||[]).forEach(z=>{        // 动态条目区：只画虚线框；条目不进设计图，运行期由应用代码创建
      const b=z.box, col='#57d3ff', ty=b[1]+b[3]-22;   // 标签放区底，避开顶部序号徽标
      const tx=b[0]+b[2]-z.tagw-6;
      s += '<g class="dynz">'
        + '<rect x="'+b[0]+'" y="'+b[1]+'" width="'+b[2]+'" height="'+b[3]+'" rx="10"'
        + ' fill="none" stroke="'+col+'" stroke-width="2" stroke-dasharray="9 6" opacity=".9"/>'
        + '<rect x="'+tx+'" y="'+ty+'" width="'+z.tagw+'" height="18" rx="9" fill="'+col+'" opacity=".92"/>'
        + '<text x="'+(tx+7)+'" y="'+(ty+12.5)+'" font-size="10.5" font-weight="700" fill="#05080f"'
        + ' font-family="sans-serif">'+z.tag+'</text></g>';
    });
    p.rows.filter(showIo).forEach(r=>{
      const b=r.box, mb=r.markBox || b, comp=!!r.markBox, col=IO.color[r.io];
      const hot = o.hot ? (r.io==='nav' && (r.target || r.dyn)) : (o.hotBack && r.dyn);
      const attrs = !hot ? '' : (r.dyn ? ' class="hot" data-back="1"'
                                       : ' class="hot" data-go="'+r.target+'" data-dir="1"');
      const del = (anns[page]||[]).some(a=>a.type==='control' && a.n===r.n && a.action==='delete');
      s += '<g id="'+(o.pid||'x')+'-'+r.n+'" data-rn="'+r.n+'"'+(del?' opacity=".18"':'')+attrs+'>';
      if (comp) s += '<rect x="'+(b[0])+'" y="'+(b[1])+'" width="'+b[2]+'" height="'+b[3]+
        '" fill="none" stroke="'+col+'" stroke-width="1" rx="10" opacity=".28"/>';
      s += '<rect x="'+(mb[0]-1.5)+'" y="'+(mb[1]-1.5)+'" width="'+(mb[2]+3)+'" height="'+(mb[3]+3)+
           '" fill="none" stroke="'+col+'" stroke-width="'+(o.slim?1.8:2.4)+'" rx="8" opacity="'+
           (o.slim?0.9:1)+'"/>';
      if (hot) s += '<rect class="hit" x="'+b[0]+'" y="'+b[1]+'" width="'+b[2]+'" height="'+b[3]+
        '" rx="8" pointer-events="all"/>';
      if (r.io==='nav' && o.slim){          // 缩略图上也画一小段跳转箭头
        s += '<path d="M'+(b[0]+b[2]+2)+','+(b[1]+b[3]/2)+' h14" stroke="#f2b45c"'+
             ' stroke-width="2.4" marker-end="url(#ar)"/>';
      }
      const isVal = r.cat === 'value';
      const bcx = isVal ? (mb[0] - 16 >= 0 ? mb[0] - 16 : mb[0] + mb[2] + 16)
                        : (comp ? (mb[0] - 14 >= 0 ? mb[0] - 14 : mb[0] + mb[2] + 14) : mb[0] + 1);
      const bcy = (isVal || comp) ? mb[1] + mb[3] / 2 : mb[1] + 1;
      s += '<circle cx="'+bcx+'" cy="'+bcy+'" r="'+(o.slim?8:11)+'" fill="'+col+'"/>'+
           '<text x="'+bcx+'" y="'+(bcy+(o.slim?3.6:5))+'" font-size="'+(o.slim?8.5:11)+
           '" font-weight="700" fill="#05080f" text-anchor="middle" font-family="sans-serif">'+
           r.n+'</text></g>';
      if (r.io==='nav' && r.target && !o.slim && !lane){
        const dir=(b[0]+b[2]+210<800)?1:-1;
        const sx=dir>0?b[0]+b[2]+2:b[0]-2, ty=b[1]+b[3]/2, tx=sx+dir*40;
        s += '<path d="M'+sx+','+ty+' h'+(dir*38)+'" stroke="#f2b45c" stroke-width="2.2"'+
             ' marker-end="url(#ar)"/>';
        const label='→ '+r.target, w=label.length*12+16;
        const lx=dir>0?tx+3:tx-w-3;
        s += '<rect x="'+lx+'" y="'+(ty-12)+'" width="'+w+'" height="24" rx="12" fill="#f2b45c"/>'+
             '<text x="'+(lx+w/2)+'" y="'+(ty+4.5)+'" font-size="11.5" font-weight="700" fill="#05080f"'+
             ' text-anchor="middle" font-family="sans-serif">'+label+'</text>';
      }
    });
    if (lane){
      const navs = p.rows.filter(r=>r.io==='nav' && r.target && showIo(r))
                         .sort((a,c)=>a.box[1]-c.box[1]);
      const step = Math.max(21, Math.min(30, 452 / Math.max(navs.length,1)));
      navs.forEach((r,i)=>{
        const b=r.box, cy=22+i*step+step/2, sx=b[0]+b[2], sy=b[1]+b[3]/2;
        if (o.hot) s += '<g class="hot" data-go="'+r.target+'" data-dir="1">';
        s += '<path d="M'+sx+','+sy+' C'+(sx+70)+','+sy+' 780,'+cy+' 820,'+cy+'" '
           + 'fill="none" stroke="#f2b45c" stroke-width="1.6" opacity=".85"'
           + ' marker-end="url(#ar)"/>';
        s += '<rect x="824" y="'+(cy-11)+'" width="162" height="22" rx="11" fill="#f2b45c"/>'+
             '<text x="834" y="'+(cy+4)+'" font-size="11.5" font-weight="700" fill="#05080f"'+
             ' font-family="sans-serif">'+r.n+'. → '+r.target+'</text>';
        if (o.hot) s += '</g>';
      });
    }
    p.gesture.filter(()=>showIo({io:'gesture'})).forEach(g=>{
      const b=g.box, cx=b[0]+b[2]/2, y0=b[1]+8, y1=b[1]+b[3]-8;
      const bulge = b[0] < 400 ? 34 : -34;
      if (o.hot) s += '<g class="hot" data-go="'+g.go+'" data-dir="'+(g.label.indexOf('←')===0?-1:1)+'">'+
        '<rect x="'+b[0]+'" y="'+b[1]+'" width="'+b[2]+'" height="'+b[3]+'" class="hitg" pointer-events="all"/></g>';
      s += '<path d="M'+cx+','+y0+' q'+bulge+','+((y1-y0)/2)+' 0,'+(y1-y0)+'" fill="none"'+
           ' stroke="#ff8fb8" stroke-width="2.4" stroke-dasharray="7 6" marker-end="url(#ag)"/>';
      s += '<text x="'+(cx+bulge*0.62)+'" y="'+((y0+y1)/2)+'" font-size="11" fill="#ff8fb8"'+
           ' text-anchor="middle" font-family="sans-serif">'+g.label+'</text>';
    });
  }
  if (o.hotBack && o.marks === false) {          // 无标注视图（高清设计图）也要能点返回
    p.rows.filter(r=>r.dyn).forEach(r=>{
      const b=r.box;
      s += '<g class="hot" data-back="1"><rect class="hit" x="'+b[0]+'" y="'+b[1]+'" width="'+
           b[2]+'" height="'+b[3]+'" rx="8" pointer-events="all"/></g>';
    });
  }
  return s + annMarks(page) + '</svg>';
}

function pill(r,page){
  const dp=' data-page="'+page+'" data-rn="'+r.n+'"';
  if (!r.target) return '<button class="pill back" data-back="1" data-hi="'+r.n+'"'+dp+
    ' title="目标=来路（运行时决定）；在总览里点它 = 回到上一次浏览的页">'+
    '<i style="background:#f2b45c"></i>'+r.n+'. '+r.name+' <b>‹</b> 来路</button>';
  return '<button class="pill nav" data-go="'+r.target+'" data-hi="'+r.n+'"'+dp+'>'+r.n+'. '+r.name+
         ' <b>→</b> '+r.target+'</button>';
}
function tagIo(r,page){
  return '<span class="pill static" data-hi="'+r.n+'" data-page="'+page+'" data-rn="'+r.n+
         '" title="'+r.act+'"><i style="background:'+IO.color[r.io]+'"></i>'+r.n+'. '+r.name+'</span>';
}
function tally(d){
  return d.rows.length + ' 控件';
}

/* 底部标签：按 6 类分行，固定顺序（可操作在前、数据在后），不再按控件序号交错 */
const IO_ORDER = ['nav', 'gesture', 'out_write', 'in_write', 'out_read', 'in_read'];
function tagLine(k, items){
  return '<div class="tg"><span class="tl" style="color:' + IO.color[k] + ';border-color:' +
    IO.color[k] + '">' + IO.name[k] + '<em>' + items.length + '</em></span>' + items.join('') + '</div>';
}
function tags(d,page){
  const lines = [];
  IO_ORDER.forEach(k=>{
    if (!ioOn.has(k)) return;
    if (k === 'gesture'){
      const g = d.gesture;
      if (g.length) lines.push(tagLine(k, g.map(x=>'<span class="pill ges" data-go="'+x.go+
        '" title="'+x.to+'">'+x.label+' <b>→</b> '+x.to+'</span>')));
      return;
    }
    const rs = d.rows.filter(r=>r.io===k);
    if (!rs.length) return;
    lines.push(tagLine(k, rs.map(r=>(k==='nav')?pill(r,page):tagIo(r,page))));
  });
  return lines.join('') || '<div class="tg"><span class="m">当前筛选下无控件</span></div>';
}

/* 视图 1：分层总览（每层横向） */
function vLayers(){
  const by={};
  D.order.forEach(p=>{const l=D.pages[p].layer;(by[l]=by[l]||[]).push(p);});
  return Object.keys(by).sort().map(l=>
    '<h2 class="sec"><span class="badge">L'+l+'</span>'+D.layerNote[l]+
    '<span class="cnt">'+by[l].length+' 页</span></h2>'+
    '<div class="layerrow">'+by[l].map(p=>{
      const d=D.pages[p];
      return '<div class="pcard'+(p===cur?' sel':'')+'" data-sel="'+p+'" data-dock="'+p+'" title="点开右侧放大图">'+
          (d.status?'<div class="stt">状态页</div>':'')+
        mark(p,{slim:true,marks:marksOn,pid:p,hotBack:true}).replace('<svg ','<svg class="mini" ')+
        '<div class="cap">'+p+'<span class="c">'+tally(d)+'</span></div>'+
        '<div class="tags">'+tags(d,p)+'</div></div>';
    }).join('')+'</div>').join('');
}

/* 视图 2：跳转演练——帧上真控件可点就真跳页（按真机方向横滑），6 类标注与右栏清单都保留 */
let trail = [];
function sideHtml(p){
  const d=D.pages[p];
  const groups=['nav','gesture','out_write','in_write','out_read','in_read']
    .filter(k=>ioOn.has(k));
  const list=groups.map(k=>{
    let items = k==='gesture'
      ? d.gesture.map(g=>'<div class="item"><span class="k">✋</span><span>'+g.label+
                         '</span><span class="go" style="color:#ff8fb8" data-go="'+g.go+
                         '" data-dir="'+(g.label.indexOf('←')===0?-1:1)+'">'+g.to+'</span></div>')
      : d.rows.filter(r=>r.io===k).map(r=>'<div class="item" data-page="'+p+'" data-rn="'+r.n+
        '" title="右键：删除 / 修改 / 加提示"><span class="k">'+r.n+'</span>'+
        '<span>'+r.name+'</span>'+(r.target?'<span class="go" data-go="'+r.target+'" data-dir="1">→ '+r.target+
        '</span>':'<span class="go" style="color:var(--t3);cursor:default">'+r.act+'</span>')+'</div>');
    if(!items.length) return '';
    return '<div class="grp"><div class="gt"><i style="background:'+IO.color[k]+'"></i>'+
      IO.name[k]+'<em>'+IO.desc[k]+'</em></div>'+items.join('')+'</div>';
  }).join('');
  const dyn = (d.dynz||[]).length
    ? '<div class="grp"><div class="gt"><i style="background:#57d3ff"></i>动态条目区'+
      '<em>设计图不画对象，运行期由应用代码生成</em></div>'+
      d.dynz.map(z=>'<div class="item"><span class="k">⇅</span><span>'+z.name+'</span>'+
        '<span class="go" style="color:#57d3ff;cursor:default">'+z.note+'</span></div>').join('')+
      '</div>' : '';
  return '<h3>'+p+'页 <span class="badge">L'+d.layer+'</span></h3>'+
    '<p class="m">'+d.rows.length+' 个控件 · 入口：'+d.entry.replace(/^入口：/,'')+
    ' · 出口：'+d.exit.replace(/^出口：/,'')+'</p>'+
    (list||'<p class="m">当前筛选下没有控件</p>')+dyn+
    '<p class="hint">点帧上橙色控件 = 真跳到目标页（新页从右滑入）；点左右边缘粉色条 = '+
    '按手势方向滑页；‹ 上一页 = 反向滑回。序号 = 右栏行号，顶栏色签可按类隐藏。</p>';
}
function trailHtml(){
  const path = trail.concat([cur]);
  return '<button class="btn" id="trailback"'+(trail.length?'':' disabled')+'>‹ 上一页</button>'+
    '<button class="btn" id="trailhome">回主控</button>'+
    path.map((x,i)=>'<span class="t'+(i===path.length-1?' now':'')+'">'+x+'</span>')
        .join('<span class="ta">→</span>');
}
function vJump(){
  const d=D.pages[cur];
  return '<div class="stage"><div>'+
    '<div class="trailbar">'+trailHtml()+'</div>'+
    '<div class="big" id="bigbox"><div class="pg">'+mark(cur,{hot:true,marks:marksOn})+'</div></div>'+
    (d.gesture.length?'<div class="gesline">✋ 本页手势：'+
      d.gesture.map(g=>g.label+' → '+g.to).join('；')+'</div>':'')+
    '</div><div class="side" id="side">'+sideHtml(cur)+'</div></div>';
}
function swapBig(p){
  const host=document.getElementById('bigbox'); if(!host) return;
  host.innerHTML = '<div class="pg">' + mark(p,{hot:true,marks:marksOn}) + '</div>';   // 直接换页，不做滑动
}
function crumbText(){
  return trail.length ? cur + '  ← ' + trail[trail.length-1] : cur + '（无来路）';
}
function refreshJump(){
  const s=document.getElementById('side'); if(s) s.innerHTML=sideHtml(cur);
  const t=document.querySelector('.trailbar'); if(t) t.innerHTML=trailHtml();
  document.getElementById('crumb').textContent=crumbText();
}
function pushTrail(p){
  if(!p) return;
  if(trail[trail.length-1] === p) return;       // 连续同一页不重复记
  trail.push(p); if(trail.length>10) trail.shift();
}
function navJump(p, dir){
  if(!p || !D.pages[p] || p===cur) return;
  pushState(); pushTrail(cur);
  cur=p;
  swapBig(p, dir||1); refreshJump();
}
function navBack(){
  if(!trail.length) return false;
  cur=trail.pop(); swapBig(cur,-1); refreshJump(); return true;
}

function stateCards(){
  const ks=['Wi-Fi 密码半页','忘记网络'].filter(k=>D.pages[k]);
  if(!ks.length) return '';
  return '<h2 class="sec">Wi-Fi 弹层状态（默认隐藏；编号为本状态内序号）</h2>'+
    '<div class="layerrow">'+ks.map(k=>
      '<div class="pcard" data-sel="'+k+'" data-dock="'+k+'" title="点开右侧放大图" style="width:660px">'+
      mark(k,{marks:marksOn,lane:false,hotBack:false}).replace('<svg ','<svg class="mini" ')+
      '<div class="cap">'+k+'<span class="c">800×480 · 原尺寸</span></div></div>').join('')+
    '</div>';
}

/* 视图 3：高清设计图（每层横向、原尺寸；控件标注可开关，默认开） */
function vDesign(){
  const by={};
  D.order.forEach(p=>{const l=D.pages[p].layer;(by[l]=by[l]||[]).push(p);});
  return Object.keys(by).sort().map(l=>
    '<h2 class="sec"><span class="badge">L'+l+'</span>'+D.layerNote[l]+'</h2>'+
    '<div class="layerrow">'+by[l].map(p=>
      '<div class="pcard'+(p===cur?' sel':'')+'" data-sel="'+p+'" data-dock="'+p+'" title="点开右侧放大图" style="width:660px">'+
      mark(p,{marks:marksOn,lane:false,hotBack:true}).replace('<svg ','<svg class="mini" ')+
      '<div class="cap">'+p+'<span class="c">800×480 · 原尺寸</span></div></div>').join('')+
    '</div>').join('') + stateCards();
}

function legend(){
  return Object.keys(IO.color).map(k=>
    '<button class="lg'+(ioOn.has(k)?'':' off')+'" data-io="'+k+'">'+
    '<i style="background:'+IO.color[k]+'"></i><b>'+IO.name[k]+'</b>'+
    '<em>'+IO.desc[k]+'</em></button>').join('')
    + '<span class="end" style="margin-left:auto;color:#5a6a80;font-size:11.5px">'
    + '总览内：点跳转标签 → 平滑滑到目标页并加选中外框；点卡片本体 → 右侧停靠栏出带标注放大图（再点卡片 / 点空白处 / Esc 收起）；'
    + '返回 = 回到上一次浏览位置</span>';
}

function render(){
  document.getElementById('legend').innerHTML = legend();
  document.getElementById('body').innerHTML =
    view==='layers'?vLayers():view==='jump'?vJump():vDesign();
  document.getElementById('crumb').textContent = cur;
  const mt=document.getElementById('mtoggle');
  if(mt) mt.textContent = '标注：' + (marksOn?'开':'关');
  annUI();
  document.querySelectorAll('.tabs .btn').forEach(b=>
    b.classList.toggle('on', b.getAttribute('data-v')===view));
}
function selectCard(p){                       // 只选卡不记来路（返回时用）
  const el=document.querySelector('.pcard[data-sel="'+p+'"]');
  if(!el) return false;
  document.querySelectorAll('.pcard').forEach(c=>
    c.classList.toggle('sel', c.getAttribute('data-sel')===p));
  const rows=[...document.querySelectorAll('.layerrow')];
  rows.forEach(r=>r.style.scrollSnapType='none');   // snap 会把平滑滑动过程拽回卡头
  el.scrollIntoView({behavior:'smooth', block:'center', inline:'center'});
  clearTimeout(selectCard.t);
  selectCard.t=setTimeout(()=>rows.forEach(r=>r.style.scrollSnapType=''), 600);
  el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
  cur=p; document.getElementById('crumb').textContent=crumbText();
  return true;
}
function reveal(p){
  if(!document.querySelector('.pcard[data-sel="'+p+'"]')) return false;
  const prev = cur;
  if(!selectCard(p)) return false;
  if(prev !== p){ pushTrail(prev); }
  if(dockOn) openDock(p, true, true);     // 放大图跟着换页，但不重复记来路
  return true;
}
function go(p, dir){
  if (!p) return;
  if (view==='jump'){ navJump(p, dir); return; }
  if (view==='layers'){ pushState(); if(reveal(p)) return; cur=p; view='jump'; trail=[]; render(); return; }
  if (p===cur) return;
  pushState();
  cur=p; render();
}
/* 右侧停靠放大栏：点卡片开/关，钉住不跟随鼠标；窄窗口自动改成右侧浮层 */
let dockOn = false;
function openDock(p, keepPos, fromBack){
  const d = D.pages[p]; if(!d) return;
  if(!fromBack && p !== cur){ pushTrail(cur); }
  dockOn = true; cur = p;
  document.getElementById('dock').innerHTML =
    '<h3>'+p+'页 <span class="badge">L'+d.layer+'</span>'+
    '<button class="btn" id="dockx" style="margin-left:auto">✕ 收起</button></h3>'+
    '<p class="dh">'+d.rows.length+' 控件 · 原 800×480 · 再点卡片、点空白处或按 Esc 收起</p>'+
    mark(p,{marks:marksOn,lane:false,hotBack:true}).replace('<svg ', '<svg class="dsvg" ');
  document.getElementById('wrap').classList.add('docked');
  document.body.classList.add('docked');
  document.getElementById('dockx').onclick = closeDock;
  document.getElementById('crumb').textContent = p;
  document.querySelectorAll('.pcard').forEach(c=>
    c.classList.toggle('sel', c.getAttribute('data-sel')===p));
  const el = document.querySelector('.pcard.sel');
  if (el && !keepPos) el.scrollIntoView({block:'nearest', inline:'center'});
}
function closeDock(){
  dockOn = false;
  document.getElementById('wrap').classList.remove('docked');
  document.body.classList.remove('docked');
}
document.addEventListener('click', e=>{
  if(e.target.closest('#dockscrim') || e.target.closest('#dockx')){ closeDock(); return; }
  const io=e.target.closest('[data-io]');
  if(io){const k=io.getAttribute('data-io');
    ioOn.has(k)?ioOn.delete(k):ioOn.add(k); render(); return;}
  const t=e.target.closest('[data-v]');
  if(t){closeDock(); view=t.getAttribute('data-v'); trail=[]; render(); return;}
  if(e.target.closest('[data-back]')){
    if(view==='jump'){ navBack(); }
    else {
      const h = trail.pop();                  // 与演练共用同一套来路
      const to = (h && D.pages[h]) ? h : D.order[0];
      if(dockOn) closeDock();                 // 返回不是"放大"，先把放大图收掉
      selectCard(to);
      if(!h){ document.getElementById('crumb').textContent = to + '（没有来路，已回主控）'; }
      return;
    }
  }
  if(e.target.closest('#trailback')){ navBack(); return; }
  if(e.target.closest('#trailhome')){ navJump(D.order[0], -1); return; }
  const g=e.target.closest('[data-go]');
  if(g){ go(g.getAttribute('data-go'), g.hasAttribute('data-dir')?+g.getAttribute('data-dir'):1); return; }
  const dk=e.target.closest('[data-dock]');
  if(dk){ const p=dk.getAttribute('data-dock');
    (dockOn && cur===p) ? closeDock() : openDock(p); return; }
  if(dockOn && !e.target.closest('#dock')) closeDock();   // 点空白处即收起，不用刻意找关闭键
});
window.addEventListener('keydown', e=>{ if(e.key==='Escape') back(); });
function back(){
  if (view==='jump' && trail.length){ navBack(); return; }
  if(dockOn){ closeDock(); return; } popState();
}
document.addEventListener('mouseover', e=>{
  const t=e.target.closest('[data-hi]'); if(!t) return;
  const card=t.closest('.pcard'); if(!card) return;
  const g=card.querySelector('g[id$="-'+t.getAttribute('data-hi')+'"]');
  if(g) g.classList.add('hi');
});
document.addEventListener('mouseout', e=>{
  const t=e.target.closest('[data-hi]'); if(!t) return;
  const card=t.closest('.pcard'); if(!card) return;
  const g=card.querySelector('g.hi'); if(g) g.classList.remove('hi');
});
function esc(s){
  return String(s||'').replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
function putControl(page, row, patch){
  const list = annsOf(page);
  const i = list.findIndex(x=>x.type==='control' && x.n===row.n);
  const rec = Object.assign({type:'control', page:page, n:row.n, name:row.name,
    box:row.box, action:'modify', note:''}, i>=0?list[i]:{}, patch);
  if(i>=0) list[i] = rec; else list.push(rec);
}
function dropAnn(page, pred){
  const list = anns[page] || [];
  const i = list.findIndex(pred);
  if(i>=0) list.splice(i,1);
}
function ctxClose(){
  const m = document.getElementById('ctxmenu');
  if(m) m.hidden = true;
  ctxTarget = null;
}
function ctxOpen(cx, cy, page, row, pt, pinId){
  ctxClose();
  const m = document.getElementById('ctxmenu');
  const ex = row ? annFor(page,row.n) : null;
  const pinA = pinId ? (anns[page]||[]).find(x=>x.type==='pin' && x.id===pinId) : null;
  let html = '<div class="ct">'+esc(row ? (page+' · #'+row.n+' '+row.name)
                                        : (pinA ? (page+' · 提示') : (page+' · 页面')))+'</div>';
  if(row){
    html += '<button data-a="del">'+((ex&&ex.action==='delete')?'取消删除':'标记删除')+'</button>';
    html += '<button data-a="edit">修改说明…</button>';
    html += '<button data-a="addpinrow">在控件上加提示标签…</button>';
    if(ex) html += '<button data-a="clear">清除该控件批注</button>';
  } else if(pinA){
    html += '<button data-a="editpin">修改提示…</button>';
    html += '<button data-a="clearpin">删除提示</button>';
  } else {
    html += '<button data-a="addpin">在此加提示标签…</button>';
  }
  m.innerHTML = html;
  m.hidden = false;
  const w = m.offsetWidth, h = m.offsetHeight;
  m.style.left = Math.max(6, Math.min(cx, innerWidth - w - 8)) + 'px';
  m.style.top = Math.max(6, Math.min(cy, innerHeight - h - 8)) + 'px';
  ctxTarget = {page:page, row:row, pt:pt, pin:pinA};
}
document.addEventListener('contextmenu', e=>{
  const item = e.target.closest('.item[data-rn], .pill[data-rn]');
  if(item){
    const page = item.getAttribute('data-page');
    const n = +item.getAttribute('data-rn');
    const r = D.pages[page] && D.pages[page].rows.find(x=>x.n===n);
    if(r){ e.preventDefault(); ctxOpen(e.clientX,e.clientY,page,r,null); }
    return;
  }
  const host = e.target.closest('.pcard, .big, #dock');
  if(!host || e.target.closest('#ctxmenu')) return;
  const page = host.getAttribute('data-sel') || cur;
  const pin = e.target.closest('[data-pin]');
  if(pin){ e.preventDefault(); ctxOpen(e.clientX,e.clientY,page,null,null,pin.getAttribute('data-pin')); return; }
  const svg = e.target.closest('svg');
  if(svg){ const xy = annLoc(svg,e); e.preventDefault(); ctxOpen(e.clientX,e.clientY,page,null,xy); }
});
document.getElementById('ctxmenu').addEventListener('click', e=>{
  const b = e.target.closest('button');
  if(!b || !ctxTarget) return;
  const a = b.getAttribute('data-a'), t = ctxTarget;
  ctxClose();
  if(a==='del'){
    const ex = annFor(t.page,t.row.n);
    if(ex && ex.action==='delete'){
      if(ex.note) ex.action='modify'; else dropAnn(t.page,x=>x.type==='control'&&x.n===t.row.n);
    } else putControl(t.page,t.row,{action:'delete'});
  } else if(a==='edit'){
    const ex = annFor(t.page,t.row.n) || {type:'control', page:t.page, n:t.row.n,
      name:t.row.name, box:t.row.box, action:'modify', note:''};
    annOpen(ex); return;
  } else if(a==='clear'){
    dropAnn(t.page,x=>x.type==='control'&&x.n===t.row.n);
  } else if(a==='addpinrow'){
    const b2 = t.row.markBox || t.row.box;
    annOpen({type:'pin', page:t.page, x:b2[0]+b2[2]/2, y:b2[1]+b2[3]/2,
             id:Date.now()+'_'+Math.random().toString(36).slice(2,6), note:''}); return;
  } else if(a==='editpin'){
    annOpen(t.pin); return;
  } else if(a==='clearpin'){
    dropAnn(t.page,x=>x.type==='pin'&&x.id===t.pin.id);
  } else if(a==='addpin'){
    annOpen({type:'pin', page:t.page, x:t.pt[0], y:t.pt[1],
             id:Date.now()+'_'+Math.random().toString(36).slice(2,6), note:''}); return;
  }
  saveAnns(); render(); annUI();
});
document.addEventListener('click', e=>{ if(!e.target.closest('#ctxmenu')) ctxClose(); });
window.addEventListener('keydown', e=>{ if(e.key==='Escape') ctxClose(); });

function boot(){
  document.getElementById('back').onclick=back;
  document.getElementById('home').onclick=()=>go(D.order[0]);
  document.getElementById('mtoggle').onclick=()=>{marksOn=!marksOn;render();};
  document.getElementById('anexport').onclick=annExport;
  document.getElementById('anngo').onclick=()=>{annExport();
    alert('已导出 w78_annotations.json。\n把文件交给 AI，改设计源后重新生成 H5/EEZ（④）。');};
  document.getElementById('annsave').onclick=annSave;
  document.getElementById('anncancel').onclick=annClose;
  document.getElementById('annx').onclick=annClose;
  const v=location.hash.slice(1);
  if(['layers','jump','design'].includes(v)) view=v;
  render();
}
if(document.readyState==='loading') window.addEventListener('DOMContentLoaded', boot); else boot();
"""

HTML = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Haven Home · 全览专业版</title><style>__CSS__</style></head><body>
<header>
  <span class="brand">Haven Home · 全览专业版</span>
  <div class="tabs">
    <button class="btn" data-v="layers">分层总览</button>
    <button class="btn" data-v="jump">跳转演练</button>
    <button class="btn" data-v="design">高清设计图</button>
    <button class="btn" id="mtoggle">标注：开</button>
    <button class="btn" id="anexport">导出批注</button>
  </div>
  <button class="btn" id="back">‹ 返回</button>
  <button class="btn" id="home">回主控</button>
  <span class="sp"></span>
  <span class="crumb">当前页 <b id="crumb">主控</b></span>
</header>
<main><div id="legend" class="legend"></div>
<div class="wrap" id="wrap"><div id="body"></div><aside id="dock"></aside></div></main>
<div id="dockscrim"></div>
<div id="annpanel" hidden>
  <div class="ah"><b id="anntitle">批注</b><button class="btn" id="annx">×</button></div>
  <textarea id="annnote" placeholder="修改说明（删除时可留空）"></textarea>
  <label id="anndelrow"><input type="checkbox" id="anndel"> 标记删除（仅 H5 预览隐藏）</label>
  <div class="af"><button class="btn" id="anncancel">取消</button><button class="btn" id="annsave">保存批注</button></div>
</div>
<div id="annbar"><span id="anncount">0 条批注</span>
  <button class="btn" id="anngo">导出并返回 ④</button></div>
<div id="ctxmenu" hidden></div>
<script id="data" type="application/json">__DATA__</script>
<script>__JS__</script></body></html>"""


def fragment(html):
    """整页 → 可直接嵌进对话/宿主页的片段：同一份 CSS+JS，不另写第二版。"""
    css = html.split("<style>")[1].split("</style>")[0]
    body = html.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    skin = ("#h5ov{background:radial-gradient(1300px 700px at 15% -15%,#0e1522,#05080f 62%);"
            "color:#f4f7fb;min-height:100vh}")
    return (u'<div id="h5ov">\n<style>\n' + skin + u"\n" + css + u"\n</style>\n"
            + body + u"\n</div>")


def main():
    payload = build()
    html = (HTML.replace("__CSS__", CSS).replace("__JS__", JS)
            .replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(html)
    io.open(OUT_FRAG, "w", encoding="utf-8", newline="\n").write(fragment(html))
    n_io = {}
    for p, d in payload["pages"].items():
        for r in d["rows"]:
            n_io[r["io"]] = n_io.get(r["io"], 0) + 1
    n_ges = sum(len(d["gesture"]) for d in payload["pages"].values())
    layers = sorted({d["layer"] for d in payload["pages"].values()})
    print("written", OUT)
    print("written", OUT_FRAG, "（可内联片段）")
    print("[GATE] 页 %d 层 %s 控件 %d 手势边 %d 分类计数 %s"
          % (len(payload["order"]), layers,
             sum(len(d["rows"]) for d in payload["pages"].values()), n_ges,
             json.dumps(n_io, ensure_ascii=False)))
    assert all(k in n_io for k in ("in_read", "out_read", "in_write",
                                   "out_write", "nav")), "6 类里有一类没控件"
    assert_js(html)


def assert_js(html):
    """产出的页面脚本必须语法可解析：生成器写出坏页面 = 打开全白，比报错更坑。"""
    js = html.rsplit("<script>", 1)[1].rsplit("</script>", 1)[0]
    import subprocess
    import tempfile
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as f:
            f.write(js)
            path = f.name
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        import os as _os
        _os.unlink(path)
        assert r.returncode == 0, "页面 JS 语法错误: " + (r.stderr or "")[:500]
        print("[GATE] 页面 JS 语法 OK（node --check）")
    except FileNotFoundError:
        print("[GATE] 跳过 JS 语法检查（本机没有 node）")


if __name__ == "__main__":
    main()
