# P-0186 · LVGL 长按抬手后仍补发 CLICKED，把刚打开的模态换成另一个

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,输入注入,无头夹具,事件语义
- **关联提示词**：（无）

## 现象（看到什么）

长按已保存行：对话框先弹出，随后被同一次手势补发的 CLICKED 换成连接半页（模态互斥又把对话框关掉）。

## 复现（怎么稳定重现）

WIFI_NAVTEST=1 跑 main.exe，看 [ROWEV]/[UI] 顺序（诊断期临时打印）。

## 根因（真正的原因）

lv_indev.c:1046 一带，非编辑对象抬手时只对 short_click 判 long_pr_sent，CLICKED 是无条件 send_event 的。

## 修复（做了什么）

行事件里用手势标记吞尾巴：LONG_PRESSED 记下本行，CLICKED 命中同一行就丢弃并清标记，PRESSED 一律清零（否则标记泄漏，下一次正常点击被误吞）。

## 证据（数字 / 命令输出）

修复前 [NAV] FAIL「长按抬手补发的 CLICKED 没把对话框换成半页」；修复后 PASS 17 / FAIL 0，且反向测试证明断言真的挂在这条通路上。

## 沉淀（新增断言 / 案例 / 文档）

cases/B16 同族（框架默认行为改写声明）+ 本工程 EEZ_WORKFLOW §5.6
