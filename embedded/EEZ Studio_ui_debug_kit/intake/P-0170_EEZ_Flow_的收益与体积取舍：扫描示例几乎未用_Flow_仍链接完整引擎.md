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

## ★ 追加补充（2026-10-21）：官方手册核对后的能力边界与应用场景

### 1. 官方定义：Flow 到底提供了什么

已核对本地归档的官方《EEZ Studio Reference Guide》：

- P.39--42：Flow 是把可视 Widget 与不可见 Action 用两种线连成的流程图逻辑。
  **Sequence line** 只传递执行时机，**Data line** 同时传递 integer、string、struct 等数据。
- P.40--41：一个项目可以有多个并行 Flow；每个活跃 Flow 保留自己的局部变量、输入值和
  组件内部状态，所有活跃 Flow 共用执行队列。这正是 `executionQueueSize` 存在、且会占用
  静态 SRAM 的原因，不是无意义的生成冗余。
- P.50、P.54：User Widget 与 User Action 可以封装并复用界面片段或无界面的流程，减少多页
  重复维护。
- P.58--60：变量可被表达式读取；`Watch` 监听变化、`SetVariable` 批量赋值、
  `IsTrue` / `Compare` / `SwitchCase` 分支。控件属性可写表达式，变量变更时 Label 等控件会更新。
- P.102--103：Flow 引擎生成 `eez-flow.cpp/.h`；压缩定义、执行队列大小、表达式求值栈是官方
  列出的 Flash/SRAM 取舍项。压缩定义旨在节省 Flash、代价是 SRAM；实际项目仍必须 A/B 测量
  （本地最小模板曾出现 LZ4 连带开销抵消收益，不能只凭选项名判断）。

### 2. Flow 值得使用的具体场景（按收益排序）

| 场景 | Flow 怎么做 | 本仓库/手册实证 | 为什么比手写 C 有收益 |
|---|---|---|---|
| 一个状态驱动多个控件 | 一个全局变量同时绑定输入控件、指示控件和文本；可调控件用 assignable 双向回写 | `w67-w3-w2-slider-arc-bar`：`g_val` 同步 Slider、Arc、Bar、Label | 免写 VALUE_CHANGED 回调、状态缓存和多处刷新代码；改绑定关系不碰 C |
| 多控件选择同步 | 多个 assignable 控件绑定同一变量，或 `VALUE_CHANGED → SetVariable` | `w23-w59-w73-w16-select-switch`：Dropdown 与 Roller 同绑 `g_sel` | 避免两个控件各存一份状态后互相覆盖 |
| 纯 UI 条件与状态呈现 | `Watch → IsTrue / SwitchCase → SetVariable / 属性表达式`，控制显隐、颜色、文案、按钮可用性 | 官方 P.58；如 `wifi_state` 控制“连接中”、错误文案、禁用重复点击 | 产品状态变化主要改流程图和表达式，避免在 C 中散落 UI if/else |
| 页面导航与交互链 | 事件 → Switch/条件 → LVGL Action 的 Change Screen/Previous Screen；可带转场、延时和页面栈 | `gesture-page-switch`：GESTURE → Switch（方向）→ LVGL Change Screen；官方 A43 | 导航规则、目标页与转场可视化；不需要手写多个 LVGL 事件回调 |
| 页面进入/退出初始化 | `OnEvent(Page open/close)` → Action 链，按页面生命周期更新 UI | 官方 A53 | 页面级初始化、刷新和清理规则集中，减少散落在 `create_screen_*` 的用户代码 |
| 动效与定时编排 | `Animate` 控制页面时间线；`Delay` 暂停后续流程；`Loop + Delay` 组成非阻塞循环 | 官方 A2、A15、A42；本地 P-0131 已验证纯 Flow 可实现滚轮动效 | 常见缩放、透明度、旋转、分步提示不必为每个效果写 LVGL 定时器 |
| 可复用 UI 业务片段 | User Widget 封装“设置项/状态卡”；User Action 封装“清除旧选中→设置新选中→切页”等动作组 | 官方 P.50、P.54 | 一处修正覆盖多处，适合导航栏、设置项、弹层开关等重复模式 |

### 3. 不应为了“全 EEZ”而强行使用 Flow 的场景

1. **动态长度列表、动态建行、虚拟列表**：LVGL 侧 Flow 数组在 C++ 运行时是定长容器，
   并没有通用的 LVGL repeater/运行时建控件能力。`app-wifi-scan-flow` 的 AP 行必须继续由
   `wifi_ui_sync.cpp` 读取 `io` 数组并调用 `lv_list_add_button()`；这是正确的 native 边界，不是
   Flow 没配好。
2. **硬件驱动、网络协议、NVS/密码、跨线程回调、硬实时/高频数据处理**：留在 `io_*.cpp` 或
   平台任务。Flow 只接收已经整理好的 UI 状态或投递命令，不能在驱动回调里碰 LVGL/Flow。
3. **只有静态控件、单一点击回调、没有表达式/页面/动画/复用逻辑的页面**：完整引擎成本无法
   被摊薄，优先评估关闭 Flow 后的原生 LVGL 或 EEZ 非 Flow 导出方案。

### 4. 对 app-wifi-scan-flow v4 的结论

当前工程只做“扫描结果动态 List”：`vars.h` 无 Flow 全局变量、`native_vars[]` 只有 NONE、
`assets` 仅 588B，刷新动作也直接进入 native 命令环；真正的列表状态、排序和绘制均在 C 侧。
因此现在保留 Flow 主要是在为未来的密码半页、页面导航、局部动画和表单状态机预留能力，
并没有产生与其体积相称的当期收益。

若后续仍保持“单页扫描 + native List”范围，应做 Flow on/off 的最终固件 A/B 后再决定去留。
若补齐密码半页、`wifi_state` 分支、页面转场和 EEZ 动效，则推荐采用**混合边界**：
Flow 管“可见状态、导航、动效、简单表单联动”，native 管“扫描/连接/NVS/密码生命周期/动态列表”。
这样才是用约 90--260KB Flash、约 3--28KB RAM 换取实际维护收益，而非只为生成一个静态壳付费。
