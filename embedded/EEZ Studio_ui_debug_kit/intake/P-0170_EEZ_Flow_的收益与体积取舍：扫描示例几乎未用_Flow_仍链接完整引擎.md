# P-0170 · EEZ Flow 的收益与体积取舍：扫描示例几乎未用 Flow 仍链接完整引擎

- **工程**：EEz_stidio_examples/app-wifi-scan-flow
- **日期**：2026-10-21
- **工具**：Codex
- **状态**：fixed
- **标签**：EEZ,Flow,资源消耗,选型,Flash,RAM,executionQueueSize,优化
- **关联提示词**：PR-0280

## 现象（看到什么）

用户观察到 eez-flow.cpp 体积很大，需要判断 Flow 的实际收益能否覆盖 Flash/RAM 代价。

## 复现（怎么稳定重现）

检查 app-wifi-scan-flow/src/ui/vars.h、ui.c、eez-flow.cpp 与 perf-tabview-native-vs-eez 的同构原生 LVGL 对照。

## 根因（真正的原因）

flowSupport=true 会生成通用 C++ Flow 运行时（表达式、绑定、动作队列、页面和组件状态机），即使工程只有很少的 Flow 行为也会链接引擎；当前扫描页的动态列表已由 native 直读 io 数组并用 LVGL List 渲染。

## 修复（做了什么）

沉淀选型准则：多页、变量绑定、表达式和动作编排密集时保留 Flow；静态/动态列表由 C 主导且 Flash 紧张时做 Flow 开关 A/B 后再决定。保留时先将 executionQueueSize 1000 降至已验证的 128，并只对 ui 组件评估 -Os、-fno-exceptions、-fno-rtti。此次不改工程代码。

## 证据（数字 / 命令输出）

当前 vars.h 无 Flow 全局变量，ui.c 的 native_vars[] 只有 NONE，assets 仅 588B、动作仅 action_scan_start，但 eez-flow.cpp 仍为 9,923 行且默认队列 1000。真机公平账单：未优化 EEZ 核心约 259KB Flash/28KB RAM；最小模板三项优化后引擎约 92.4KB Flash/3.4KB RAM。1000→128 队列实测省 10,464B RAM。

## 沉淀（新增断言 / 案例 / 文档）

新增 P-0170 与 index 索引；关联 P-0154、P-0157、P-0158、P-0159、P-0161。
