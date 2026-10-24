# EEZ no-flow：native 文件与文件夹分层

适用于“EEZ 生成 UI 树 + native 补功能 + PC/真机双环境”的 LVGL 工程。

## 推荐树（默认轻量版）

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
├── app/                                    [项目可变：业务文件保持扁平，不建功能子目录]
│   ├── watch_model.*                       业务真值；无 LVGL、无 SDK
│   ├── watch_view.*                        model / 平台快照 → 全部 objects.* 刷新
│   ├── watch_events.*                      按钮回调、透明点击区、事件绑定
│   └── watch_logic.*                       初始化与持续状态调度
│
├── platform/                               [硬件可变：PC 与真机共用接口、实现二选一]
│   ├── watch_platform.h                    时间、BLE、传感器、PWM、声音的窄接口
│   ├── pc/watch_platform_pc.c              宿主时间、模拟数据、日志
│   └── device/watch_platform_device.c      真机 RTC、BLE、传感器、PWM、NVS 接入点
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
| 改运动/闹钟/计算器等产品规则 | `src/native/app/watch_events.*` 与 `watch_model.*` |
| 改主表盘或功能页的数据回显 | `src/native/app/watch_view.*` |
| 改计时、测量结束、持续进度规则 | `src/native/app/watch_logic.*` |
| 改 PC 模拟数据、真机 RTC/BLE/传感器/PWM | `src/native/platform/pc/` 或 `device/` |
| 改返回关系、Tab 路由 | `src/native/navigation/` |
| 改 AppList、图表等动态控件手势 | `src/native/widgets/` |
| 升级 Rxroller | `src/native/third_party/rxroller/` 连同台账整体处理 |

**不要做的事**：不在 `src/ui/` 改业务；不让 `platform/` 引用 `objects.*`；不在
`app/` 随意复制 UI 坐标；不直接手改 `generated/` 或 `third_party/`。

## 依赖方向

`design → src/ui ← native/app`，`native/app → native/platform`。

- `app/watch_model.*` 不得引用 LVGL 或平台头，保证可用无头断言验证。
- `app/watch_events.*` 可以登记 LVGL 回调、读取输入值，更新 model 后请求 view 刷新。
- `app/watch_view.*` 只读 model/平台快照，只写 `objects.*`。
- `app/watch_logic.*` 只负责初始化和 tick，不读取 `objects.*`。
- platform 不得引用 EEZ 对象。
- `navigation` 只处理去向；状态变更必须进入 `app`。
- 动态透明点击层的几何不手填；从 `design/` 生成常量，或让 EEZ 生成透明控件。

### PC / device 的编译选择

PC 仿真不定义 `WATCH_PLATFORM_DEVICE`，所以只编译出 `platform/pc/` 的接口实现；
真机工程定义该宏后，PC 文件不产生符号，必须由 `platform/device/` 提供同名实现。这样
`app/` 永远只包含 `watch_platform.h`，不会有 `#ifdef PC` 分支，也不会重复链接符号。

## 文件层函数职责

| 层 | 函数形态 | 示例 | 不应承担的工作 |
| --- | --- | --- | --- |
| `app/watch_model.*` | 数据结构、纯状态真值 | `alarm.enabled[0] = true` | `lv_label_set_text()`、SDK 调用 |
| `app/watch_view.*` | model/快照到 `objects.*` 的单向投影 | `watch_view_render_sport()` | 改业务真值、绑定事件 |
| `app/watch_events.*` | LVGL 事件回调、状态迁移、平台命令 | `on_start()`、`watch_events_bind()` | 定时推进、页面去向、BLE 报文细节 |
| `app/watch_logic.*` | 初始化和持续状态定时调度 | `logic_tick()` | 读取 `objects.*`、绑定单击事件、页面去向 |
| `platform/watch_platform.h` | 时间/传感器/BLE/PWM/存储的窄接口 | `watch_platform_get_local_time()` | 引用 EEZ 对象 |
| `navigation/*` | 页面与 Tab 去向 | `go_applist()` | 持有闹钟/计时状态 |
| `widgets/*` | 专用动态控件的手势、布局、绘制 | `list_snap_edge()` | 管理其他页面业务 |

调用方向固定为：**事件 → events → model → view / platform**；持续状态由 `logic` 推进。`view` 只读 model，
`platform` 只接命令或提供快照；这样 PC 模拟和真机驱动替换时不会触及 UI/业务代码。

## 哪些固定，哪些会随应用变化

| 目录 | 分类 | 固定不动的部分 | 每个应用会变化的部分 |
| --- | --- | --- | --- |
| `app/watch_model.*` | 项目层 | 无 UI / 无驱动依赖的规则 | 状态字段、持久化、数据来源 |
| `app/watch_view.*` | 项目层 | model 单向投影到 UI | 页面对象、文案、视觉回显 |
| `app/watch_events.*` | 项目层 | 输入→状态→平台命令的顺序 | 功能规则、输入处理 |
| `app/watch_logic.*` | 项目层 | 统一 tick 与初始化顺序 | 持续状态规则、调度周期 |
| `platform/watch_platform.h` | 框架半固定 | 接口边界 | 某产品实际需要的接口集合 |
| `platform/pc/` / `platform/device/` | 硬件层 | 同一接口二选一 | PC 模拟、SDK、芯片、引脚、传感器、BLE 协议 |
| `navigation/` | 框架半固定 | 仅处理去向 | 页面路由、返回与 Tab 策略 |
| `widgets/` | 项目层 | EEZ 父层 + 设计源几何的约束 | 滚轮、图表、键盘等控件实现 |
| `third_party/` | 冻结层 | 上游原文、许可证、补丁台账 | 只有升级上游版本时变化 |
| `generated/` / `src/ui/` | 生成层 | 不手改、可覆盖重建 | 由设计源自动生成的内容 |

一句话：**产品状态改 model，回显改 view，输入改 events，持续任务改 logic，硬件与 PC 仿真改 platform，设计调整改 design。**

## 迁移纪律

1. 先移动一层并完整编译/回归，再继续拆域；不要“整理目录”与改行为混在同一批。
2. 上游件稳定前不搬家；路径、生成脚本、许可证、台账必须同步迁移。
3. 每个新增外设先完成 PC 模拟接口和断言，最后才接真机实现。
4. **搬家前先查“按文件名写死的自检”**：任何 `for fn in (...)` + “文件不存在就跳过”的检查，
   在文件改名或进子目录的当天就会静默清零，仍然报绿（实测抓到两处，见 P-0188）。
   覆盖面一律改成递归遍历目录，并加“找到的文件数低于阈值即 FAIL”的兜底。
5. 搬家是否只改了结构，用**渲染逐字节比对**自证：迁移前后各出一套仿真图比 SHA256，
   加上行为断言集（如 `[NAV]`）不变，才算“零行为改动”。

## 扩展与迁移规则（重要）

默认不做功能子目录，但当 `watch_logic.c` 同时承担输入、回显和 tick 时，应先平铺拆为
`app/watch_model.*`、`watch_view.*`、`watch_events.*`、`watch_logic.*` 四组文件。

1. 先归位独立职责：`watch_nav.* → navigation/`、AppList 三文件 → `widgets/applist/`、
   上游滚轮件 → `third_party/rxroller/`、设计派生表 → `generated/`；同步脚本与台账路径。
2. 只有某个功能继续超过约 800 行、需要独立测试、或多人高频冲突时，才在 **同一 `app/`
   目录平铺** 增加 `sport.*`、`alarm.*` 等文件；不为每个功能新建目录。
3. `platform/` 从一开始就保留 `pc/` 与 `device/`：PC 构建不定义 `WATCH_PLATFORM_DEVICE`，
   真机构建定义该宏；两边不可同时定义 `watch_platform_*` 接口。

### watch 工程当前落地状态（2026-10-24）

```text
已完成：
- `app/watch_model.*`、`app/watch_view.*`、`app/watch_events.*`、`app/watch_logic.*` 平铺业务层；
- `platform/watch_platform.h` + `platform/pc/` / `platform/device/` 作为 PC/真机二选一边界；
- `navigation/watch_nav.*`、`widgets/applist/`、`third_party/rxroller/`、`generated/app_rows.*`；
- 手写源文件按“私有状态 / 小工具 / 回调或算法 / 调度 / 对外入口”增加区块注释。
```

不要因“看起来分层”而增加 `features/<name>/` 等功能子目录；`view/events/logic` 是按技术职责
拆出的平铺文件，`platform/pc/device` 是为保证 PC 与真机实现二选一的必要边界。

## 手写文件注释纪律

一个文件内部用区块标题代替无意义的目录嵌套，推荐顺序为：

```c
/* ===== 1. 模块私有状态与常量 ===== */
/* ===== 2. 小工具 / 坐标换算 ===== */
/* ===== 3. 事件回调或核心算法 ===== */
/* ===== 4. 定时任务 ===== */
/* ===== 5. 对外初始化与公开接口 ===== */
```

注释写“为什么要在这里处理、有哪些边界”，不复述函数名。`generated/` 与
`third_party/` 禁止为了排版手改；生成器或上游升级会覆盖它们。

## 判据

- 新功能不应让单个职责文件无限增长；达到拆分阈值后仍只在 `app/` 内平铺拆分。
- PC 与真机切换只能替换 `platform/`，业务和 UI 渲染不改。
- 生成 `src/ui` 后，native 不因路径或头文件布局失效。
