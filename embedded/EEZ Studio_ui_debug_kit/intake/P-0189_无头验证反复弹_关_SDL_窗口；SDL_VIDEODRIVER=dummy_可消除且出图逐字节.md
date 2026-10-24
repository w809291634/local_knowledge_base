# P-0189 · 无头验证反复弹/关 SDL 窗口；SDL_VIDEODRIVER=dummy 可消除且出图逐字节一致

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：无头验证,SDL,仿真窗口,回归
- **关联提示词**：PR-0360

## 现象（看到什么）

跑稳定性回归要连开 8~10 次仿真，桌面窗口一闪一闪开关（用户点名质疑）。

## 复现（怎么稳定重现）

连续跑 design/shot_states.py 或 WIFI_NAVTEST=1 main.exe 多次即可见。

## 根因（真正的原因）

PC_SIM 用 lv_sdl_window_create() 开真窗口；每次验证都是新起进程，没有理由要求它在桌面出现。

## 修复（做了什么）

验证入口（shot_states.py / preflight --with-sim）统一设 SDL_VIDEODRIVER=dummy；需要肉眼看窗口时用 SHOT_STATES_WINDOWED=1 显式恢复。注入的鼠标事件走同一条 SDL 事件→indev 链路，dummy 不影响判定。

## 证据（数字 / 命令输出）

dummy 模式：[NAV] 17 PASS/0 FAIL；idle/done/sheet_open 三屏与有窗口版SHA256 相同；整套六屏重拍后与基线逐字节一致，桌面不再弹窗。

## 沉淀（新增断言 / 案例 / 文档）

本工程 EEZ_WORKFLOW §5.4 + 各验证脚本默认值
