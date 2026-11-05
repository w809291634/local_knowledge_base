# P-0226 · 单页示例结构移植到多屏工程：遮罩挂错屏、快照拍不到 layer_top

- **工程**：w78-tabview-smart-home
- **日期**：2026-11-05
- **工具**：Qoder
- **状态**：fixed
- **标签**：EEZ,结构移植,多屏,lv_layer_top,快照,Wi-Fi,list,半页
- **关联提示词**：PR-0507

## 现象（看到什么）

用户对比成熟示例 `app-wifi-scan-conn-no-flow` 后指出 w78 的 Wi-Fi 连接页结构不对：
示例是「一个 Wi-Fi 页 + lv_list 动态行 + 密码半页 + 忘记对话框」，w78 却是三个独立页面
（Wi-Fi 设置 / 密码 / 连接中），列表是 5 个静态行。

按示例结构改完后：连接时日志有 `busy show`，但仿真截图看不到转圈遮罩。

## 根因（真正的原因）

1. 示例是**单屏**工程，`wifi_busy` 把全屏遮罩建在 `objects.main` 上；w78 是多屏，
   `objects.main` 不是当前活动屏 → 遮罩不可见。
2. `lv_snapshot_take(lv_screen_active())` **只拍当前 screen，不包含 `lv_layer_top`**；
   遮罩挂在 layer_top，所以截图里永远看不到它（屏上其实有）。

## 修复（做了什么）

- `widgets/wifi_busy/wifi_busy.cpp`：遮罩改挂 `lv_layer_top()`，多屏下始终盖住当前屏；
  `CLICKABLE` 仍负责“连接期间不可操作”。
- Wi-Fi 页 EEZ 结构按示例重建：`list_box`（LVGL List，行 native 动态建）+ `overlay_root`
  （scrim+sheet+pwd_ta+kb_main）+ `dlg_root`；删除「Wi-Fi 密码」「Wi-Fi 连接中」两屏。
- native 分层按示例移植：`app/{wifi_events,wifi_logic,wifi_view}` + `navigation/{wifi_nav,wifi_bind}`
  + `widgets/{wifi_list,wifi_busy,wifi_eye}` + `platform/`；删除自研 `wifi_ui.cpp`。
- 本工程 no-flow 不生成 EEZ action，按钮回调集中在 `navigation/wifi_bind.cpp` 挂。

## 证据（数字 / 命令输出）

- 导航边 82 → 72（两页删除），`[NAV] 72/72 PASS`。
- 假后端流程：扫描 12 个 AP → 开半页 → 密码 → 连接 → 新网络置顶并标记「已连接」；
  截图 `designer_annotated/wifi_ui.png`、`wifi_sheet.png`、`wifi_flow.png`。
- D5：24 页平均 **98.53%**，Wi-Fi 页 **99.48%**；D1–D8 全 PASS。

## 沉淀（新增断言 / 案例 / 文档）

- CHANGELOG v0.9.101；多屏/单屏差异两条写进条目。
- 以后从单屏示例移植：先查“对象挂在哪张屏/哪层”，`lv_snapshot` 证据要排除 layer_top
  （用可见性断言或整窗截图）。
