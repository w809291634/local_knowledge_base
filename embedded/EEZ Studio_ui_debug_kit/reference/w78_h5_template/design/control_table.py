# -*- coding: utf-8 -*-
"""控件清单表（第②步的出口产物）：从同一份设计源导出，供用户逐行改口径。

改口径请改 `design/pages.py`（控件语义表）与 `design/nav_map.py`（跳转目标），重跑本脚本；
**不要直接改这份 md**，否则它就变成第二真值。

数据流向 6 类、层级、手势边全部复用 `overview_pro.build()`，与 H5 评审页同源同判据。
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import simple_control as sc        # noqa: E402
import export_ui as eu             # noqa: E402
import overview_pro as ov          # noqa: E402
import pages as pg                 # noqa: E402

OUT = os.path.join(os.path.dirname(sc.OUT), "designer_annotated", "控件清单.md")

CAT = {"scene": "场景卡(按钮)", "nav": "跳转按钮", "back": "返回按钮",
       "toggle": "开关", "slider": "滑块", "read": "只读数据卡",
       "value": "设备读数", "uivalue": "UI 读数"}
# Wi-Fi 弹层/对话框控件在 overview 里拆成独立展开态卡，不计入基础页控件表
WIFI_STATE = {"弹层·密码框", "弹层·连接", "弹层·关闭", "弹层·键盘",
              "对话框·忘记", "对话框·断开", "对话框·取消"}


def main():
    data = ov.build()
    raw = eu.page_data()
    rows = []
    n_ctl = n_ges = 0
    io_cnt = {}
    for p in data["order"]:
        if p not in raw:  # 预览专用页不进入业务控件清单
            continue
        d = data["pages"][p]
        cat_by_n = {r["n"]: r["cat"] for r in raw[p]["rows"]}
        tag = "状态页" if d["status"] else ""
        cnt = {}
        for r in d["rows"]:
            n_ctl += 1
            code = pg.IO_CODE[r["io"]]
            cnt[code] = cnt.get(code, 0) + 1
            io_cnt[r["io"]] = io_cnt.get(r["io"], 0) + 1
            rows.append("| %s%s | L%d | %d | %s | %s | %s | %s | %s | %s%02d | (%d,%d,%d,%d) |" % (
                p, ("（" + tag + "）" if tag else ""), d["layer"], r["n"], r["name"],
                CAT.get(cat_by_n[r["n"]], cat_by_n[r["n"]]), ov.IO_NAME[r["io"]],
                r["act"], r["target"] or "—", code, cnt[code], *r["box"]))
        for g in d["gesture"]:
            n_ges += 1
            io_cnt["gesture"] = io_cnt.get("gesture", 0) + 1
            rows.append("| %s%s | L%d | ✋ | %s | 滑动手势区 | 跳动手势 | %s | %s | (%d,%d,%d,%d) |" % (
                p, ("（" + tag + "）" if tag else ""), d["layer"], g["label"], g["to"],
                g["go"], *g["box"]))

    head = [
        "# 控件清单（由 design/control_table.py 从设计源导出，勿手改）",
        "",
        "> 真值在 `design/pages.py`（控件语义表）+ `design/nav_map.py`（跳转目标）+ "
        "`design/simple_control.py`（几何）。",
        "> 要改口径就改上面三处再重跑本脚本；数据流向/层级/手势与 H5 评审页同源"
        "（`design/overview_pro.py`）。",
        "> 本表每条在 EEZ 中必须是真实控件（开关/滑块/按钮/输入/进度/图表/读数），"
        "A12 硬门禁校验；透明容器冒充即 FAIL。设备读数（温度/湿度/百分比/功率/状态）"
        "也单独成 `value` 行。",
        "",
        "| 屏 | 层 | 徽标 | 名称 | 控件类型 | 数据流向 | 作用（点击/滑动后） | 跳转目标 | 代号 | 框 (x,y,w,h) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    dyn = ["", "## 动态条目区（设计图不画对象，运行期由应用代码创建）",
           "",
           "> 条目数量随程序/环境变化，不固化为控件，也不画进设计图；"
           "H5 以青色虚线框标出（`design/pages.py` 的 `DYN_ZONES` 是唯一真值）。",
           "",
           "| 屏 | 区域 | 说明 | 框 (x,y,w,h) |",
           "|---|---|---|---|"]
    for z in pg.DYN_ZONES:
        dyn.append("| %s | %s | %s | (%d,%d,%d,%d) |" % (
            z["page"], z["name"], z["note"], *z["box"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(head + rows + dyn) + "\n")

    # 门禁：导航闭环 + 六类齐全 + 计数与设计源一致
    no_back = [p for p in data["order"] if p != data["order"][0]
               and not any(r["io"] == "nav" for r in data["pages"][p]["rows"])]
    print("written", OUT)
    print("[GATE] 控件 %d 手势边 %d 行数 %d 分类计数 %s"
          % (n_ctl, n_ges, len(rows), sorted(io_cnt.items())))
    visible_raw = sum(
        len([r for r in raw[p]["rows"]
             if not (p == "Wi-Fi 设置" and r["name"] in WIFI_STATE)])
        for p in data["order"] if p in raw)
    assert n_ctl == visible_raw, "控件行数与设计源不符"
    assert set(io_cnt) >= {"in_read", "out_read", "in_write", "out_write", "nav", "gesture"}, \
        "6 类数据流向里缺类"
    assert not no_back, "这些页没有任何跳转/返回控件：%s" % no_back
    assert all(z["page"] in data["order"] for z in pg.DYN_ZONES), \
        "动态条目区指向不存在的页"


if __name__ == "__main__":
    main()
