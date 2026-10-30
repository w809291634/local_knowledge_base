# P-0219 · 逐屏截图验证每页都弹 SDL 窗口，屏幕一直闪；改为内存 display 无窗口批量出图

- **工程**：w78-tabview-smart-home
- **日期**：2026-10-30
- **工具**：Qoder
- **状态**：fixed
- **标签**：仿真,截图,无头,闪屏,SDL,批量,验证体验
- **关联提示词**：PR-0403

## 现象（看到什么）

核对 25 屏时循环启动 PC 仿真，每页都创建 SDL 窗口，屏幕连续闪烁；用户要求后台验证。

## 复现（怎么稳定重现）

旧截图模式用 lv_sdl_window_create 建窗口，SIM_PAGE/SIM_SHOT 每页一个进程；25 页连续运行时窗口反复出现。

## 根因（真正的原因）

截图模式没有无头分支，仍走 SDL 显示；且一次进程只截一页，重复初始化/出窗。

## 修复（做了什么）

SIM_SHOT 默认改走内存 display：lv_display_create + 全屏 framebuffer + no-op flush，不初始化 SDL；SIM_SHOT=all 一个进程遍历 25 页输出到 SIM_OUT_DIR；SIM_WINDOW=1 才走 SDL；run_sim.bat 增加 shots 子命令。

## 证据（数字 / 命令输出）

无头批量 25 页全部输出成功；与旧 SDL 截图逐页比较 max 平均通道差 0.0（25/25 完全一致）；运行过程不建 SDL 窗口。

## 沉淀（新增断言 / 案例 / 文档）

NO_FLOW/FLOW §1.3 快照流水线加“截图默认无窗口”条款；工程 README 增加 run_sim.bat shots；本记录。
