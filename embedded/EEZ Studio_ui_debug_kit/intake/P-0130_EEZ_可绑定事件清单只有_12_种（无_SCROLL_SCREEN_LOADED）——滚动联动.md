# P-0130 · EEZ 可绑定事件清单只有 12 种（无 SCROLL/SCREEN_LOADED）——滚动联动类动效无法在 EEZ 声明

> ★ 标题结论已被推翻（2026-10-16 深夜）：常驻轮询链（Start→Loop→Delay→objGetDisplayY/objStyleSetProperty）纯 EEZ flow 即可实现，见文末更正与 P-0131；12 事件清单本身仍为准。

- **工程**：Design Watch（watch UI 工程）
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：EEZ,事件,SCROLL,asar,滚动联动,wheel,能力边界
- **关联提示词**：PR-0217

## 现象（看到什么）

AppList 滚轮动效（滑动中按滚动位置逐帧缩放）想从 EEZ 里声明触发，找不到任何口子。

## 复现（怎么稳定重现）

解包 app.asar 查 LVGL 控件事件枚举：事件 map 以 HOVER_LEAVE:{code:12} 收尾；全部事件名带引号检索：SCROLL=0 命中。

## 根因（真正的原因）

EEZ 的 LVGL 事件选项仅 12 种基础事件（PRESSED/PRESS_LOST/SHORT_CLICKED/SINGLE_CLICKED/DOUBLE_CLICKED/TRIPLE_CLICKED/LONG_PRESSED/LONG_PRESSED_REPEAT/CLICKED/RELEASED/HOVER_OVER/HOVER_LEAVE）；SCROLL 类与 SCREEN_LOADED 不在其中（个别控件有专属事件如 Tabview VALUE_CHANGED，但不含滚动）。叠加 flow 表达式无法读取滚动位置 → 滚动联动动效在 EEZ 内不可表达。

## 修复（做了什么）

按铁律『EEZ 实在表达不了→通知用户』处置：动效走 native（watch/src/native/applist_wheel.c，仿真 main 已接、真机加一行 applist_wheel_init()）；触发用 C 侧 lv_obj_add_event_cb(SCROLL/SCREEN_LOADED)。可选折中：把缩放曲线参数以 EEZ native 变量登记实现 Studio 内可见/可调。

## 证据（数字 / 命令输出）

asar 事件 map 片段（LONG_PRESSED_REPEAT:8→HOVER_LEAVE:12 收尾）；grep '"SCROLL"'=0、'"SCREEN_LOADED"'=0。

## 沉淀（新增断言 / 案例 / 文档）

（待补）

## ⚠ 本条结论已被推翻（2026-10-16 深夜，见 P-0131）

"只有事件面、没有滚动事件 → 动效必须 native"不成立：**LVGLActionComponent 没有绑定事件也能常驻运行**——
Start（无入线组件在 flow 启动即执行）→ Loop(to 给大数) → Delay(30ms) 轮询 → objGetDisplayY + objStyleSetProperty，
纯 EEZ flow 即可覆盖"按滚动位置逐帧改样式"。本条的 12 事件清单仍然正确（事件面事实无误），
但"因此表达不了"是**推理错误**：动效不一定要事件驱动，轮询链同样成立。native 方案已退役（报告 §18）。
