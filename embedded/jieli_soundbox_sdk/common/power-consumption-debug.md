# 功耗调试方法（杰理 SDK 通用，实测数据来自 BR23）

> 核心认知：**功耗不是"哪里耗电"，而是两个问题 —— 能不能进 `power_down`，以及进去后被多频繁地唤醒。**
> 出处：`doc/功能模块说明文档/功耗调试说明书.pdf` V1.0（2020-11-20，9 页）+ 代码核对。

## 1. 先建立观测手段（不要拿电流表直接试）

| 手段 | 做法 | 证据 |
|---|---|---|
| **打点法** | `sleep_enter_callback` 里 `putchar('<')`，`sleep_exit_callback` 里 `putchar('>')`，看 log 里 `<>` 出现的密度 | 手册 p5；代码 `board_ac695x_demo.c:1079-1091`（**默认注释掉**，且注释写着"此函数禁止添加打印"） |
| **IO 翻转法（推荐）** | 同上两个回调里用 `APP_IO_DEBUG_1(A,6)` / `APP_IO_DEBUG_0(A,6)` 翻 PA6，示波器看占空比 = 睡眠占比 | `board_ac695x_demo.c:1079-1091` |
| 注册回调 | `power_set_callback(TCFG_LOWPOWER_LOWPOWER_SEL, sleep_enter_callback, sleep_exit_callback, board_set_soft_poweroff)` | 同文件 `:1120` |

打点法会**自身改变功耗**（打印本身就是唤醒+IO 活动），量产排查优先用 IO 翻转法。

## 2. 进不了低功耗：让系统自己告诉你谁在忙

打开两处打印（`app_config.h` 的 `LIB_DEBUG` 置 1、`lib_driver_config.c` 的 `log_tag_const_d_PMU` 置
`CONFIG_DEBUG_LIB(TRUE)`，该文件第 77 行默认是 FALSE），系统会刷：

```
Name : xxx busy
```

机制：`power_down` 前会**逐个查询已注册模块的 `is_idle`，任一返回 0 就不进低功耗**
（`include_lib/driver/cpu/br23/asm/power_interface.h:282-298`：`struct lp_target{name; is_idle;}` + `REGISTER_LP_TARGET` 宏）。
SDK 内注册点举例：`apps/common/update/update.c:631`、各 `apps/soundbox/task_manager/*`。

→ **排查顺序：看哪个模块一直 busy → 去那个模块查它的 `is_idle` 为什么返回 0 → 通常是某个外设没关/某个定时器在跑/某个任务在轮询。**

## 3. 定时器的选择直接决定待机电流（三条对比）

| 接口 | 唤醒影响 | 结论 |
|---|---|---|
| `sys_timer_add` | sys_timer 线程发消息给注册线程，精度 10ms，**会唤醒系统** | 手册明确建议**谨慎使用**；周期越短待机越费 |
| `sys_hi_timer_add` | 优先级高于 power_down，**只要注册着，系统永远不进 power_down**，直到被删除 | 待机期间还想进低功耗就**必须先删** |
| `sys_hi_timeout_add` | 在中断执行，power_down 期间**节拍停止**、唤醒后继续 → **定时间隔变成不固定** | 不能用于需要真实周期性的场合 |

SDK 自身的设备检测（SD 卡 / USB / LINEIN）都注册了较短周期定时器，**开越多检测项，唤醒越频繁**（手册 p6）。

## 4. 唤醒频率的正常基线

`power_down` 自身约 **500ms** 周期唤醒（手册 p6）→ 正常应看到"缓慢的 `<>`"。
除此之外被别的调度或 IO 中断唤醒就是异常来源。IO 唤醒结构（p7 截图）：

```c
struct port_wakeup { u8 pull_up_down_enable; u8 edge; u8 attribute /*=BLUETOOTH_RESUME*/; u16 iomap /*IO_PORTB_01*/; };
struct wakeup_param { struct port_wakeup port[1..3]; ... sub; charge; };
```
另有独立模块 `port_wkup_interrupt_init()`，但**只有 1 路且低功耗下中断无效**（`cpu/br23/port_wkup.c:5-7`）。

## 5. 蓝牙侧

- **未连接**时功耗大头是 inquiry_scan / page_scan / 回连。手段：`set_idle_period_slot(1600)`，
  实际时间 = `1600 × 0.625ms = 1s`。**设太大会导致每次从空闲切回工作状态耗时变长、可能影响连接**（手册 p7）。
- 连接后无操作会进 **sniff** 进一步降耗。
- BLE 靠调广播间隔与通讯间隔。
- 极端手段（只留 BLE）：`bt_close_bredr()` / `bt_init_bredr()`（手册 p8 截图，内部走
  `USER_CTRL_WRITE_SCAN_DISABLE / CONN_DISABLE / PAGE_CANCEL / CONNECTION_CANCEL / POWER_OFF / INQUIRY_CANCEL`
  + `sys_auto_sniff_controle` + `btctrler_task_close_bredr`）。
- 相关配置坑：IR 键会禁低功耗（`app_config.h:359`）；`chargestore`/`charge` 类外设会强制读写 PB05
  （`embedded/jieli_soundbox_sdk/common/peripheral-drivers-cookbook.md` §8）。

## 6. 实测电流（手册 p9 表，单位 mA，MAX/MIN/AVG；LDO vs DCDC）

| 场景 | LDO | DCDC |
|---|---|---|
| 未连蓝牙（bredr） | 3.98 / 0.305 / **1.14** | 4.322 / 0.302 / **0.737** |
| bredr 连接待机 | **0.090** | **0.532** |
| ble 未连（广播 1s） | 0.328 | 0.285 |
| ble 连接（500ms 通讯一次） | 0.370 | 0.300 |
| bredr 未连 + ble 未连 | 1.202 | 0.732 |
| bredr 连接待机 + ble 连接 | 0.953 | 0.667 |

量级感受：**平均 0.3~1.3 mA，峰值 3~10 mA**。
**反直觉的一条：bredr 连接待机 LDO 0.090 mA 远好于 DCDC 0.532 mA** —— DCDC 并非在所有场景都更省，
选型要按实际工作场景比，不能只看典型值。

## 7. 漏电排查顺序（手册 p9 §4.2）

1. **最常见是 IO 漏电**：外部硬件有上拉/下拉，而 IO 被设成相反的输出方向，两端压差形成持续电流。
   → 必须结合实际硬件电路与 IO 应用状态逐脚分析（`pull_up/pull_down/direction/output_value` 四元组）。
2. 先用"**比较干净的硬件环境**"摸底（最小系统），再上实际样机。
3. 上样机后**按模块一个一个拆分分析**（关掉一个模块看电流台阶），不要整体反复试。

## 8. 文档没给的东西（别当成已知）

- **必须关的外设清单、电流表接法、具体裁剪代码步骤**：文档未提及。
- **睡眠/待机的正式模式划分表**：文档只隐含三级 `power_down` / `sniff` / 软关机，无定义表。
- **型号差异**：全文只写 AC695N 平台，表内只区分 LDO/DCDC 供电，未标注芯片型号差异。
