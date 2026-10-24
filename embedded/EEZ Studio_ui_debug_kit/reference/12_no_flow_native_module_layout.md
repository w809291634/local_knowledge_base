# EEZ no-flow：native 文件与文件夹分层

适用于“EEZ 生成 UI 树 + native 补功能 + PC/真机双环境”的 LVGL 工程。

## 推荐树（最终目标）

**标记说明**：`[生成]`＝永不手改；`[冻结]`＝只随上游升级整体变化；
`[项目可变]`＝每个产品重写；`[硬件可变]`＝随芯片、外设、协议变化；
`[框架半固定]`＝目录职责不变，路由/API 细节可变。

```text
design/                                      [项目可变：唯一设计源]
├── design_source.py                         页面、控件、字体码位的真值
├── build_*.py                               生成 .eez-project / native 生成数据
└── sim_cmake/                               PC 仿真入口、夹具、构建配置

src/ui/                                      [生成：EEZ 覆盖式产物，禁止手改]
├── screens.* / images.* / fonts.*
└── ...

src/native/
├── app/                                    [项目可变：产品功能本身]
│   ├── model/                              无 LVGL、无 SDK 的业务真值
│   │   └── watch_model.*                   步数、闹钟、计时、设置等数据
│   ├── features/                           事件→状态迁移；按功能域拆分
│   │   ├── sport.* / alarm.* / media.*
│   │   └── settings.* / timer.*
│   ├── view/                               状态→objects.*；只刷新 UI
│   │   ├── watchface.*
│   │   └── sport_view.* / alarm_view.* ...
│   └── watch_logic.*                       应用装配、注册事件、创建调度器
│
├── platform/                               [硬件可变：PC 与真机替换边界]
│   ├── platform_api.h                      接口契约；UI/业务只依赖这一层
│   ├── pc/                                 宿主时间、模拟数据、日志、PC 输入
│   └── device/                             RTC、BLE、传感器、PWM、NVS、芯片 SDK
│
├── navigation/                             [框架半固定：只处理页面去向]
│   └── watch_nav.*                         返回、Tab、路由表；不保存业务状态
│
├── widgets/                                [项目可变：专用动态控件]
│   └── applist/                            行创建、吸附、手势；父对象来自 EEZ
│
├── third_party/                            [冻结：上游件及其证据链]
│   └── rxroller/                           原文、LICENSE、补丁脚本、移植台账
│
└── generated/                              [生成：设计源派生的 native 数据]
    └── app_rows.*                          App 顺序、图标、screen 指针；禁止手改
```

### 看目录就能判断“该改哪里”

| 需求变化 | 唯一应该修改的位置 |
| --- | --- |
| 改页面、坐标、文案、图片、字体码位 | `design/` |
| 改运动/闹钟/计算器等产品规则 | `src/native/app/features/` 与 `model/` |
| 改主表盘或功能页的数据回显 | `src/native/app/view/` |
| 改 PC 模拟数据、真机 RTC/BLE/传感器/PWM | `src/native/platform/pc/` 或 `device/` |
| 改返回关系、Tab 路由 | `src/native/navigation/` |
| 改 AppList、图表等动态控件手势 | `src/native/widgets/` |
| 升级 Rxroller | `src/native/third_party/rxroller/` 连同台账整体处理 |

**不要做的事**：不在 `src/ui/` 改业务；不让 `platform/` 引用 `objects.*`；不在
`features/` 手填 UI 坐标；不直接手改 `generated/` 或 `third_party/`。

## 依赖方向

`design → src/ui ← native/app ← native/platform`。

- `app` 可读取 `objects.*`、调用 platform 接口，但 platform 不得引用 EEZ 对象。
- `watch_state` 不得引用 LVGL 或平台头，保证可用无头断言验证。
- `navigation` 只处理去向；状态变更必须进入 `app`。
- 动态透明点击层的几何不手填；从 `design/` 生成常量，或让 EEZ 生成透明控件。

## 文件层函数职责

| 层 | 函数形态 | 示例 | 不应承担的工作 |
| --- | --- | --- | --- |
| `app/*_model` | 数据结构、纯状态迁移 | `alarm.enabled[0] = true` | `lv_label_set_text()`、SDK 调用 |
| `app/*_logic` | LVGL 事件回调、状态机、定时调度 | `on_start()`、`logic_tick()` | BLE 报文细节、页面去向 |
| `app/*_view` | 状态到 `objects.*` 的单向投影 | `watchface_render()` | 改业务真值 |
| `platform/*` | 时间/传感器/BLE/PWM/存储的窄接口 | `platform_get_time()` | 引用 EEZ 对象 |
| `navigation/*` | 页面与 Tab 去向 | `go_applist()` | 持有闹钟/计时状态 |
| `widgets/*` | 专用动态控件的手势、布局、绘制 | `list_snap_edge()` | 管理其他页面业务 |

调用方向固定为：**事件 → logic → model → view / platform**。`view` 只读 model，
`platform` 只接命令或提供快照；这样 PC 模拟和真机驱动替换时不会触及 UI/业务代码。

## 哪些固定，哪些会随应用变化

| 目录 | 分类 | 固定不动的部分 | 每个应用会变化的部分 |
| --- | --- | --- | --- |
| `model/` | 项目层 | 无 UI / 无驱动依赖的规则 | 状态字段、持久化、数据来源 |
| `features/` | 项目层 | 状态机不直接操作硬件的规则 | 功能域及其业务规则 |
| `view/` | 项目层 | model 单向投影到 UI | 页面对象、文案、视觉回显 |
| `platform/platform_api.h` | 框架半固定 | 接口边界、线程归属 | 某产品实际需要的接口集合 |
| `platform/pc/` | 框架半固定 | 模拟实现、日志、夹具形态 | 模拟数据曲线、PC 输入协议 |
| `platform/device/` | 硬件层 | 不引用 UI 的边界 | SDK、芯片、引脚、传感器、BLE 协议 |
| `navigation/` | 框架半固定 | 仅处理去向 | 页面路由、返回与 Tab 策略 |
| `widgets/` | 项目层 | EEZ 父层 + 设计源几何的约束 | 滚轮、图表、键盘等控件实现 |
| `third_party/` | 冻结层 | 上游原文、许可证、补丁台账 | 只有升级上游版本时变化 |
| `generated/` / `src/ui/` | 生成层 | 不手改、可覆盖重建 | 由设计源自动生成的内容 |

一句话：**产品需求改 model/features/view，硬件变化改 platform/device，PC 仿真改
platform/pc，设计调整改 design，第三方与生成层不要手改。**

## 迁移纪律

1. 先移动一层并完整编译/回归，再继续拆域；不要“整理目录”与改行为混在同一批。
2. 上游件稳定前不搬家；路径、生成脚本、许可证、台账必须同步迁移。
3. 每个新增外设先完成 PC 模拟接口和断言，最后才接真机实现。

## 渐进迁移顺序（重要）

不要把“按功能拆文件”和“搬目录”混为一批。推荐顺序如下：

1. **先拆 `app/watch_logic.c`**：按 `watchface`、`sport`、`alarm`、`media`、`settings`
   拆出功能域；必要的共享 `watch_model.*` 先落地。每抽一个域都跑一次完整回归。
2. **再迁移基础设施**：把 `watch_nav.*` 移入 `navigation/`；把专用列表、其配置、行数据、
   上游滚轮件一并移入 `widgets/applist/`。同步修改生成器与移植脚本中的路径。
3. **最后拆平台实现**：将当前默认适配层拆为 `platform_pc.*` 与 `platform_device.*`；前者
   提供主机时间/模拟数据/日志，后者对接 RTC、BLE、传感器、PWM、NVS。

### watch 工程当前落地状态（2026-10-24）

```text
已完成： app/watch_model.*、app/watchface.*、platform/watch_platform.*
进行中： app/watch_logic.c → sport / alarm / media / settings
暂不移动：watch_nav.*、watch_list_native.*、watch_list_config.h、app_rows.*、rxroller/
```

其中“暂不移动”不是遗漏：滚轮已经过多轮手势/吸附/横滑回归，应先让业务功能文件稳定，
再做一次专门的路径迁移与回归，避免把交互回归归因混进目录调整。

## 判据

- 新功能不应让 `watch_logic.c` 无限增长；按运动、闹钟、媒体、设置等域拆分。
- PC 与真机切换只能替换 `platform/`，业务和 UI 渲染不改。
- 生成 `src/ui` 后，native 不因路径或头文件布局失效。
