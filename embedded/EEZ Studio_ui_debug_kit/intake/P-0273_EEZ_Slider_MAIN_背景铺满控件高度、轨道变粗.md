# P-0273 · EEZ Slider MAIN 背景铺满控件高度、轨道变粗

- **工程**：多参数监护仪 UI（multipara_monitor_ui）
- **日期**：2026-11-08
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,Slider,轨道,生成器
- **关联提示词**：PR-0625

## 现象（看到什么）

24px 高 Slider 渲染出整块深色底板，设计图只要 6px 轨道；轨道位置与旋钮尺寸也偏。

## 复现（怎么稳定重现）

把 Slider 控件高度设成 24px、只靠 MAIN 的背景/pad 做轨道：EEZ 里 MAIN 背景铺满控件高度，轨道变成整块深色；设计 track.y 与控件 y 不同时还会整体偏移。

## 根因（真正的原因）

Slider 的 MAIN 背景是整控件高度，不能只靠 pad 得到 6px 轨道；轨道 y 需按设计 track.y 计算。

## 修复（做了什么）

独立 6px 容器当轨道，Slider MAIN bg_opa=0；top=track.y-9；KNOB pad=-4 得 16px 旋钮。

## 证据（数字 / 命令输出）

alarm_settings 93.36%→97.92%，sys_settings 93.18%→96.40%。

## 沉淀（新增断言 / 案例 / 文档）

- 通用生成器的 slider 分支固定：轨道用独立 6px 容器，Slider `MAIN bg_opa=0`，`top=track.y-9`，`KNOB pad=-4`。
- 文档：NO_FLOW §2.2 规则 ⑭、`reference/16` §3 规则 7、CHANGELOG v0.9.189。
