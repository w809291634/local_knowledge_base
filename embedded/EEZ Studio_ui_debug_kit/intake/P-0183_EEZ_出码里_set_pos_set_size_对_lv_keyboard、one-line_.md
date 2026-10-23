# P-0183 · EEZ 出码里 set_pos/set_size 对 lv_keyboard、one-line lv_textarea 不是字面几何

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,EEZ出码,几何,仿真核对
- **关联提示词**：（无）

## 现象（看到什么）

半页按设计坐标出码、preflight 几何对账全绿，仿真渲染却键盘只剩一行且掉到屏底，输入框高度从 36 塌成 17。

## 复现（怎么稳定重现）

app-wifi-scan-conn-no-flow：把 overlay_root 临时显形跑 PC_SIM 截图；或读 design/sim_cmake/main.c 的 WIFI_KBPROBE 探针输出。

## 根因（真正的原因）

lv_keyboard 构造函数 lv_obj_align(obj, LV_ALIGN_BOTTOM_MID,0,0)（lv_keyboard.c:452）使 lv_obj_set_pos 变成相对底边中点的偏移；lv_textarea_set_one_line(true) 内部 lv_obj_set_height(obj, LV_SIZE_CONTENT)（lv_textarea.c:557）覆盖显式高度。

## 修复（做了什么）

设计源里给键盘显式 align=TOP_LEFT（EEZ localStyles MAIN/DEFAULT 支持 align 键），给 one-line 输入框用 pad_top/pad_bottom=(设计高-行高)/2 撑高度（行高要实测，cn14=19）；按钮底色不得与所在面板同色。

## 证据（数字 / 命令输出）

探针实测 修复前 kb abs=(16,280)-(479,411)/ta h=17 → 修复后 kb abs=(8,188)-(471,319)/ta h=35；build/sim_shots/sheet_open.png 4 行键齐全；preflight [④A] 两条新守卫反向测试 rc=1、复原 rc=0。

## 沉淀（新增断言 / 案例 / 文档）

cases/B16（新）+ EEZ_FIRST_WORKFLOW_NO_FLOW.md §0.3 几何口径 + 本工程 preflight [④A] 守卫
