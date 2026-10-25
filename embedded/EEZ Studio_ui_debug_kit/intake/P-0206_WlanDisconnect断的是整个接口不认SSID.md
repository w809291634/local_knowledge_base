# P-0206 · WlanDisconnect 断的是整个接口，不认 SSID

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-25
- **工具**：Qoder
- **状态**：fixed
- **标签**：wlanapi,WlanDisconnect,语义,误伤
- **关联提示词**：PR-0380

## 现象（看到什么）

长按菜单加「断开」时，最直观的写法是 `io_wifi_disconnect(ssid)` → `WlanDisconnect(h, &guid, NULL)`。
但对话框对"已保存"的行都能打开——包括**没连上的**行；照写的话，点一个未连接网络的「断开」
会把**当前正在用的另一条连接**断掉。

## 复现（怎么稳定重现）

已连接 A 时，对未连接的 B 调 `WlanDisconnect(&guid)`：接口直接断开，A 掉线。API 没有 SSID 参数。

## 根因（真正的原因）

`WlanDisconnect` 是**接口级**操作（`WLAN_CONNECTION_PARAMETERS` 里没有 SSID），
Windows 的模型是"一个无线接口同时只有一条基础结构连接"。按 SSID 断开只在该 SSID 就是当前连接时有意义。

## 修复（做了什么）

`io_wifi_disconnect(ssid)` 先查快照里该 SSID 的 `connected` 位：不是当前连接 → 只把标题写成
「未连接 X」，**不调** `WlanDisconnect`；是当前连接 → 断开、立刻回查列表、写「已断开 X」。
假世界同口径（清 connected 位 + 重排）。

## 证据（数字 / 命令输出）

`[NAV] RESULT: PASS 57 / FAIL 0`（新增 8 条：有按钮 / 三颗同高同宽 / 关窗 / connected 清零 /
文案点名 / 全表无已连接）；反向测试（掐掉调用）rc=1、3 条红；
几何门禁 `btn_dlg_disconnect 出码=(116,92,92,32) 设计=(116,92,92,32)`。

## 沉淀（新增断言 / 案例 / 文档）

**被 UI 直接触发的"断开/删除/清理"类系统调用，先确认作用域是"这一条"还是"整个资源"**；
作用域更粗的（接口级、进程级、全局配置），调用前必须比对目标是否就是当前对象，否则会误伤旁边的东西。
