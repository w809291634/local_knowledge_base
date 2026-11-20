# STC8H/8G 应用框架模板（前后台 + 软定时器 + 单状态机）

> 适用：STC8H/8G + Keil C51 + `stc8g_8h_lib` + `common/drv`
> 来源：GM202611004 WTW 定制352生发帽 V1.0.0（2026-11-20）
> 编译基线：0 Error / 0 Warning，data=120.3 xdata=1133 const=1400 code=17448
> 说明：只记录当前工程实际存在的结构、调用顺序和约定；未落地的设计不写入正文。

## 0. 结论先行

- 无 RTOS，前后台结构：中断只做 1ms tick、UART 收发、蜂鸣方波；业务全部在主循环。
- 五层：芯片库 → `common/drv` → `common/apl` → `Source/board` + `Source/app` → `main.c`。
- 全局只有一个扁平 `g_state`（xdata），当前没有分组子结构。
- 状态入口唯一：`app_state_enter()`；输出出口唯一：`app_state_apply_outputs()`；秒基准唯一：`g_state.second_tick_ms`。
- 主循环四步顺序固定：软定时器 → 应用状态 → 灯板刷新 → 协议。
- APP 上报在 `app_protocol_ble.c::app_ble_proto_update()`，用函数内 static 快照比较，按 D1 → D2 → B4 顺序发送。
- 配置集中在 `board_config.h`，三层开关 + 末尾 `#error` 依赖检查。

## 1. 适用与不适用

适合：

- 单 MCU、无操作系统、状态机型设备。
- RAM/Flash 紧张，需要编译期裁剪模块。
- 输入输出数量固定、业务周期在毫秒到秒级。

不适合：

- 需要长阻塞任务、多线程并发、文件系统、网络协议栈。
- 需要复杂动态内存或大量浮点运算。

## 2. 目录模板

```text
<工作区>/
├─ stc8g_8h_lib/                STC 官方外设库
└─ project/stc8h_project/
   ├─ common/
   │  ├─ drv/                   drv_xxx 通用驱动
   │  └─ apl/                   apl_soft_timer、apl_kprintf、pubsub、eventos
   └─ STC8H4K64_template/
      ├─ MDK/                   Keil 工程、Listings、Objects
      └─ Source/
         ├─ main.c              hw_init → app_init → while(1)
         ├─ main.h
         ├─ board/
         │  ├─ board_config.h   应用参数 + 三层开关 + 引脚 + 依赖检查
         │  └─ debug_log.c/.h   分级日志
         └─ app/
            ├─ app_state.c/.h         状态机、秒节拍、保护、统一输出
            ├─ app_io.c/.h            GPIO、指示灯状态管理、电源保持
            ├─ app_battery.c/.h       电量采样分档、充电输入、NV 电量
            ├─ app_ntc.c/.h           NTC 采样、查表、错误码
            ├─ app_buzzer.c/.h        蜂鸣器节拍
            ├─ app_driver_board.c/.h  灯板 PWM/UART/无灯板
            ├─ app_protocol.c/.h      帧格式、收发、队列、连接门控
            ├─ app_protocol_ble.c/.h  命令分发、D1/D2/B4、治疗 ID
            ├─ app_ble_nv.c/.h        EEPROM 记录
            ├─ app_key.h
            ├─ app_key_input_lite.c   单键扫描适配
            └─ timer_isr.c            Timer0/3 用户中断
```

## 3. 分层与依赖

| 层 | 目录/文件 | 职责 | 约束 |
| --- | --- | --- | --- |
| 芯片库 | `stc8g_8h_lib/` | UART/Timer/PWM/ADC/EEPROM/GPIO | 只被 drv 层直接调用 |
| 通用驱动 | `common/drv/` | 外设初始化与读写，统一 `comm_drv_xxx_*` | 不包含业务判断 |
| 应用基础库 | `common/apl/` | 1ms tick、软定时器、kprintf、pubsub | 不包含产品逻辑 |
| 板级/业务 | `Source/board`、`Source/app` | 配置、状态机、采样、输出、协议 | 普通业务模块不直接改 SFR |
| 入口 | `main.c` | 初始化与主循环 | 只编排，不写业务 |

依赖方向：`app → board → drv → 芯片库`。`app_io`、`app_buzzer`、`app_driver_board` 是引脚级模块，允许直接操作 sbit/SFR。

## 4. 启动流程

`hw_init()` 顺序：

1. `EAXSFR()`、`EA = 1`。
2. UART2 调试口（`BOARD_CFG_COMM_DRV_UART2_DEBUG=1` 时）：GPIO + `comm_drv_uart_init(UART2)`。
3. `app_io_hw_init()`：指示灯、灯带、按键、检测脚；不改变 P1.3 电源保持脚的上电状态。
4. UART1：9600/8N1，P3.6/P3.7 + `comm_drv_uart_init(UART1)`。
5. `app_driver_board_hw_init()`：PWM/UART2/无灯板三种模式之一。
6. `comm_drv_timer_init(Timer0)`：1ms 系统 tick。
7. ADC：P0.0/P0.1 高阻 + `comm_drv_adc_init()` + `softTimer_DelayMS(2)`。

`app_init()` 顺序：

1. `softTimer_Init()`（`SOFT_TIMER_LITE=0`）。
2. `app_buzzer_init()`：P2.1 + Timer3 500us 方波。
3. `app_state_init()`：清零 `g_state`，默认全头/连续/12 分钟，初始化输出与关机软定时器。
4. `app_battery_init()`：从 NV 恢复电量档。
5. `app_key_init(app_state_on_key)`：建立 10ms 按键扫描。
6. `app_proto_init()`：帧状态、发送队列、治疗 ID 种子。
7. 打印启动摘要。

顺序注意：

- 当前顺序是先 `EA=1`，再初始化 UART2 调试口。
- ADC 初始化后代码等待 2ms 再采样，保证上电稳定。
- `app_state_init()` 先于 `app_battery_init()`：前者建立默认状态，后者只覆盖电量档。

## 5. 主循环

```c
void main(void)
{
    hw_init();
    app_init();
    while (1)
    {
        softTimer_Update();          /* 按键10ms、蜂鸣节拍、关机延时 */
        app_state_update();          /* 戴帽/充电/每秒采样/倒计时/保护/按键 → 统一输出 */
        app_driver_board_update();   /* 串口灯板每秒重发；PWM模式无操作 */
        app_proto_update();          /* 收包解析、上报判断、发送队列节流 */
    }
}
```

顺序原因：

- `app_state_update()` 先完成状态与输出，`app_proto_update()` 最后在同一轮内看到最新状态并上报。
- 发送队列的 100ms 节流由 `app_proto_update()` 末尾 `proto_txq_poll()` 推进。

中断职责：

| 中断 | 周期 | 只做 |
| --- | --- | --- |
| Timer0 | 1ms | `tickCnt_Update()`、`app_proto_tick_1ms()` |
| Timer3 | 500us | `Buzzer_ISR_Tick()` |
| UART1 | 字节 | STC 库接收缓冲/发送完成标志 |

## 6. 全局变量 `g_state`

当前是单一扁平结构，只有一份实例：

```c
typedef struct
{
    /* ---------- 状态与治疗参数（APP 上报源） ---------- */
    uint8_t  state;              /* APP_STATE_* | 【上报】B0/B2/B4 | 状态迁移→D1 */
    uint8_t  mode;               /* 连续/脉冲 | 【上报】B0/B4/D2 | 变化→D2+B4 */
    uint8_t  zone;               /* 前额/头顶/后脑/全头 | 【上报】B0/B4/D2 | 变化→D2+B4 */
    uint16_t set_seconds;        /* 设定秒数 | 【上报】B0/B4/D2 | 变化→D2+B4 */
    uint16_t remaining_seconds;  /* 剩余秒数 | 【上报】B4 | 每秒变化→B4 */

    /* ---------- 输入检测 ---------- */
    uint8_t  battery_level;      /* 0~3，0xFF 未知 | 【上报】B0/B4 | 档位变化→B4 */
    uint8_t  hat_worn;           /* 1戴帽/0未戴 | 【仅触发】变化→B4，不进载荷 */
    uint16_t battery_mv;         /* 电压 mV | 【本地】保护判断 */
    uint16_t temperature_x10;    /* 温度×10 | 【本地】保护判断 */
    uint8_t  temp_alarm;         /* 正常/告警/停止 | 【本地】保护判断 */

    /* ---------- 保护延时（本地） ---------- */
    uint8_t  off_delay;          /* 延时关机剩余秒，0=未触发 */
    uint32_t hat_ready_ms;       /* 戴上后允许恢复输出的时刻 */

    /* ---------- 老化（本地） ---------- */
    uint8_t  aging_phase;        /* 1输出/0停止 */
    uint16_t aging_sec;          /* 老化阶段剩余秒 */

    /* ---------- 输出与事件（本地） ---------- */
    uint8_t  driver_state;       /* 最后下发的灯板编码 */
    uint8_t  buzzer;             /* 待执行提示 */
    uint8_t  key_events;         /* KEY_EVT_* 事件位 */

    /* ---------- 空闲与秒基准（本地） ---------- */
    uint16_t idle_seconds;       /* 空闲秒 */
    uint32_t second_tick_ms;     /* 整秒节拍基准 */
} app_state_data_t;

extern app_state_data_t xdata g_state;
```

标记含义：

- `【上报】`：直接进入协议帧。
- `【仅触发】`：只触发上报，不进载荷。
- `【本地】`：只参与本机控制，不上报。

APP 上报字段清单：

| 类别 | 字段 | 说明 |
| --- | --- | --- |
| 直接进帧（6） | `state`、`mode`、`zone`、`set_seconds`、`remaining_seconds`、`battery_level` | 对应 B0/B2/B4/D2 |
| 仅触发（1） | `hat_worn` | 变化触发 B4，载荷里没有该字段 |
| 帧外上报状态（2） | `s_treat_id`、`s_treat_valid` | 位于 `app_protocol_ble.c`，用于 D1/D2 |
| 本地（12） | 其余字段 | 不参与上报 |

帧对应：

| 帧 | 使用的字段 |
| --- | --- |
| B0 | `state`、`mode`、`zone`、`set_seconds`、`battery_level` |
| B2 | `state`（另回显动作类型） |
| B4 | `state`、`mode`、`zone`、`set_seconds`、`remaining_seconds`、`battery_level` |
| D1 | 由 `state` 迁移驱动；`s_treat_id`、`s_treat_valid` |
| D2 | `mode`、`zone`、`set_seconds`、`s_treat_id` |

字段顺序和类型与实际 `app_state.h` 一致，注释只用于分类。自动检测与发送规则见 11.3。

模块私有状态（不放进 `g_state`）：

| 模块 | 状态 |
| --- | --- |
| `app_protocol_ble.c` | `s_rsp[7]`、`s_timestamp`、`s_treat_id`、`s_treat_valid`、`app_ble_proto_update()` 内 `s_last_state/mode/zone/set/remain/hat/battery` |
| `app_protocol.c` | `s_tx_no`、`s_rx_rd`、`s_rx_ok`、`s_rx_bad`、`s_tx_frame[32]`、`s_txq[16][32]`、`s_txq_len[16]`、队头/队尾/上次发送时刻、`s_frame[32]` 等 |
| `app_io.c` | `s_led_state`（每灯 2 位目标）、`s_led_out`（每灯 1 位实际输出） |
| `app_battery.c` | `s_fall_cnt`（降档确认计数，函数内 static） |
| `app_ntc.c` | `s_ntc_err`（上次错误码） |
| `app_state.c` | `s_aging_cnt`、`s_aging_ms`；`app_state_update()` 内 `s_hat_prev` |
| `app_key_input_lite.c` | `s_on_evt`、`s_long_fired` |

约定：

- 可变数据放 `xdata`；常量表放 `code`；模块内部状态用 `static`。
- 不使用动态内存。
- 当前做法：新增全局状态放入 `g_state`；只在模块内部使用的不导出。
- 当前不采用 `g_app.xxx` 分组子结构，本文档不虚构该结构。

## 7. 状态机

| 状态 | 含义 |
| --- | --- |
| `APP_STATE_OFF` | 关机，负载与灯全灭，释放电源保持 |
| `APP_STATE_POWER_ON` | 长按开机过程，已拉高电源保持 |
| `APP_STATE_STANDBY` | 开机待机 |
| `APP_STATE_RUNNING` | 治疗运行，倒计时 |
| `APP_STATE_PAUSED` | 暂停，保留参数与剩余时间 |
| `APP_STATE_CHARGING` | USB 在位且充电中 |
| `APP_STATE_CHARGED` | USB 在位且已充满 |
| `APP_STATE_AGING` | 老化，输出/停止各 60s |

`app_state_enter()` 的进入条件（当前代码）：

| 目标 | 条件 |
| --- | --- |
| 任意非法值 | 拒绝 |
| 与当前相同 | 直接返回成功，不重置计时 |
| `AGING → 非 OFF` | 拒绝 |
| `OFF` | 任何状态都允许 |
| `POWER_ON` | 只能从 `OFF` 进入 |
| `STANDBY` | 不能从 `OFF` 进入 |
| `RUNNING` | `off_delay==0`，且当前为 `STANDBY/PAUSED`，保护检查通过 |
| `PAUSED` | 只能从 `RUNNING` 进入 |
| `AGING` | 不能从 `OFF` 进入 |
| `CHARGING/CHARGED` | 非老化状态都可进入 |

进入动作：

- `OFF`：`app_state_power_off()`。
- `POWER_ON`：`app_vdd_on()`，`remaining_seconds = set_seconds`。
- `CHARGING/CHARGED`：`app_vdd_on()`，`battery_mv = INVALID`；`CHARGED` 时 `battery_level=3`；响 1 声。
- `AGING`：清延时关机，固定连续+全头，`battery_level=3`，`aging_phase=1`，`aging_sec=60`，响 1 声。
- `STANDBY/RUNNING/PAUSED`：不改电源保持，负载由输出函数处理。

统一收敛点：

| 逻辑 | 函数 |
| --- | --- |
| 空闲重置 | `app_state_touch()` |
| 延时关机登记/取消 | `app_state_request_off()` / `app_state_clear_off()` |
| 工作条件 | `app_state_work_guard()` |
| 状态判断 | `app_state_is_charging()` / `app_state_is_working()` |

### 7.1 `app_state_update()` 顺序

1. 读 `hat_worn`；摘下→戴上边沿且当前为 `RUNNING` 时，`hat_ready_ms = now + 1000`。
2. `app_state_update_charge()`：USB/STAT → `CHARGING/CHARGED`；老化状态只认 USB 拔插；拔充静音关机。
3. `app_state_update_tick()`：秒节拍、采样、倒计时、延时关机、空闲。
4. `app_state_update_key()`：按键业务。
5. `app_state_apply_outputs()`；灯板下发失败 → 进入 `PAUSED`。
6. 清 `key_events`。

### 7.2 按键处理

| 场景 | 行为 |
| --- | --- |
| 延时关机中 | 全部屏蔽 |
| `OFF` | 只响应长按触发；短按/松开忽略 |
| `CHARGING/CHARGED` | 只响应短按，累计 5 次进老化；每次短按响 1 声；长按屏蔽 |
| `AGING` | 所有按键屏蔽 |
| 长按 | `OFF → POWER_ON`；其他已开机状态 → `OFF` |
| 长按松开 | 状态为 `POWER_ON` → `STANDBY` |
| 短按 | 先 `app_state_set_zone(ALL)`，再 `app_state_toggle_work()`；成功响 1 声 |

## 8. 每秒节拍

`app_state_update_tick()` 实际顺序：

1. 计算 `seconds = (now - second_tick_ms) / 1000`，为 0 返回。
2. `app_ble_proto_tick_sec(seconds)`：治疗 ID 种子累加。
3. 老化分支：阶段倒计时，切换输出/停止，输出阶段开始响 1 声；随后打印状态并返回（不采样、不保护、不空闲关机）。
4. 运行分支：剩余时间倒计时；到 0 回待机、恢复默认时长、响 5 声；未戴帽每秒提示 1 声；已戴帽且温度告警每秒 2 声。
5. `app_sample_sensors()`：电池采样、NTC 采样、温度等级、超温延时关机、低电延时关机、运行保护。
6. 重新取时并推进 `second_tick_ms`。
7. `off_delay` 倒计时：充电中且非超温则清除；到点进入 `OFF`。
8. 空闲计时：运行/充电/有提示音时清零；其他非 OFF 状态累计，到 180s 响 3 声，约 3s 后断电。
9. 打印每秒状态。

关键参数（`board_config.h`）：

| 参数 | 当前值 |
| --- | --- |
| 默认治疗时长 | 720s（12 分钟） |
| 空闲关机 | 180s |
| 低电延时 | 3s |
| 超温延时 | 4s |
| 戴帽恢复延时 | 1000ms |
| 老化阶段 | 60s |
| 老化进入次数/间隔 | 5 次 / 500ms |
| 未戴帽提示音 | 开启 |
| NTC 故障停光 | 关闭 |
| 电池采样故障停机 | 关闭 |
| 戴帽检测 | 开启 |
| 灯带跟随戴帽 | 开启 |

## 9. 统一输出

`app_state_apply_outputs()` 顺序：

1. 灯板目标：
   - 老化：`aging_phase && hat_worn` → `mode|zone`。
   - 其他：仅 `RUNNING` 且 `hat_worn` 且 `hat_ready_ms` 已到，并且 `guard==OK` 或（`LOW_BATTERY` 且 `off_delay` 非 0）→ `mode|zone`。
   - 目标变化才调用 `app_driver_board_set_state()`。
2. 电量/充电双色灯：`app_battery_get_leds(state != OFF)`。
3. 蓝牙灯：关机灭；已连接常亮；未连接慢闪。
4. 工作灯：`RUNNING`、老化输出阶段、或灯板非 OFF 时常亮。
5. 灯带：`BOARD_CFG_APP_LED_STRIP_FOLLOW_HAT=1` 时，`hat_worn && (RUNNING || 老化输出阶段)` 通电。
6. 蜂鸣：按 `g_state.buzzer` 执行后清零。

指示灯闪烁由 `app_led_update()` 统一生成：慢闪 500ms 翻转，快闪 125ms 翻转。

## 10. 模块职责

| 模块 | 实际接口 | 职责 |
| --- | --- | --- |
| `app_io` | `app_io_hw_init`、`app_led_set_state`、`app_led_update`、`app_vdd_on/off`、各输入读取 | GPIO 与灯状态，不含业务判断 |
| `app_battery` | `app_battery_init/sample/get_voltage_mv/charge_input/can_work/get_leds/level_percent` | 采样、分档、迟滞、NV 电量、双色灯目标 |
| `app_ntc` | `app_ntc_get_temperature_x10` | 采样、查表插值、错误码 |
| `app_buzzer` | `app_buzzer_init` | 注册方波/静音回调，启动 Timer3 |
| `app_driver_board` | `app_driver_board_hw_init/set_state/update` | 灯板编码输出 |
| `app_protocol` | `app_proto_init/update/send/tx_flush/tick_1ms` | 收包、拼帧、校验、发送队列、连接门控 |
| `app_protocol_ble` | `app_ble_proto_init/update/tick_sec`、`app_ble_report_off`、`proto_handle_cmd` | 命令分发、D1/D2/B4、治疗 ID |
| `app_ble_nv` | `app_ble_nv_load/save_sync_id`、`app_ble_nv_load/save_battery` | 9 字节记录读写与校验 |
| `app_key_input_lite` | `app_key_init` | 50ms 消抖、2s 长按、事件上报 |
| `app_state` | `app_state_init/update/enter/toggle_work/set_mode/set_zone/set_time/apply_outputs` | 状态机与统一输出 |

## 11. APP 上报模型（当前实现）

### 11.1 帧字段

B0（A0 响应，5 字节）：

| 偏移 | 字段 |
| --- | --- |
| 0 | 工作模式一 |
| 1 | 工作状态 |
| 2 | 设定时间-秒 |
| 3 | 设定时间-分 |
| 4 | 电量百分比 |

B2（A2 响应，3 字节）：

| 偏移 | 字段 |
| --- | --- |
| 0~1 | 动作类型（小端） |
| 2 | 工作状态 |

B4（查询/主动，7 字节）：

| 偏移 | 字段 |
| --- | --- |
| 0 | 工作模式一 |
| 1 | 工作状态 |
| 2 | 设定时间-秒 |
| 3 | 设定时间-分 |
| 4 | 剩余时间-秒 |
| 5 | 剩余时间-分 |
| 6 | 电量百分比 |

D1（5 字节）：

| 偏移 | 字段 |
| --- | --- |
| 0~3 | 治疗 ID（小端） |
| 4 | 治疗状态：01 运行 / 02 停止 / 03 暂停 / 04 继续 |

D2（7 字节）：

| 偏移 | 字段 |
| --- | --- |
| 0~3 | 治疗 ID（小端） |
| 4 | 工作模式一 |
| 5 | 设定时间-秒 |
| 6 | 设定时间-分 |

工作模式一 = `zone | mode`：分区 0x10/0x20/0x30/0x40，模式 0x04 连续 / 0x08 脉冲。

工作状态位：

| 位 | 含义 |
| --- | --- |
| bit7:6 | 01 开机 / 10 关机 |
| bit5:4 | 00 无充电 / 01 充电中 / 10 充满 |
| bit3:2 | 10 常规（本机固定） |
| bit1:0 | 00 条件不足 / 01 运行 / 10 停止 / 11 暂停 |

当前状态字节值：关机 0x8A、待机/开机过程/老化 0x4A、运行 0x49、暂停 0x4B、充电 0x5A、充满 0x6A。

### 11.2 自动变化字段

| 字段 | 变化方式 | 触发 |
| --- | --- | --- |
| 剩余时间 | 自动周期 | 运行中每秒 -1，B4 每秒 |
| 工作状态 | 自动事件 | 状态切换、USB、充电/充满 |
| 电量百分比 | 自动事件 | 档位变化、充满固定 3 档 |
| 治疗状态 | 治疗事件 | 开始/暂停/继续/结束 |
| 治疗 ID | 治疗事件 | 新治疗取号 |
| 工作模式一 | 手动 | A1 设置、按键切全头 |
| 设定时间 | 手动 | A1 时间设定/±/重置 |

### 11.3 APP 自动检测上报

检测入口：

```text
app_proto_update()
  └─ app_ble_proto_update()   每轮主循环调用一次
```

检测方式：`app_ble_proto_update()` 内 static 快照，与当前值逐项比较。

```c
/* 首轮：只建立快照，不上报 */
if (s_last_state == 0xFFu)
{
    s_last_state   = state;
    s_last_mode    = mode;
    s_last_zone    = zone;
    s_last_set     = set_seconds;
    s_last_remain  = remain;
    s_last_hat     = hat_worn;
    s_last_battery = battery_level;
    return;
}
```

字段触发矩阵：

| 检测源 | 比较方式 | 自动发送 | 变化类型 |
| --- | --- | --- | --- |
| `state` | `state != s_last_state` | D1（按迁移映射）+ B4 | 状态事件 |
| `mode/zone/set_seconds` | 任一不相等 | D2 + B4 | 参数变化 |
| `remaining_seconds` | `remain != s_last_remain` | B4 | 自动周期（运行中每秒） |
| `battery_level` | `battery_level != s_last_battery` | B4 | 采样事件 |
| `hat_worn` | `hat_worn != s_last_hat` | B4 | 戴帽事件（仅触发） |
| 其他本地字段 | 不参与比较 | 无 | — |

D1 状态迁移映射：

| 状态迁移 | D1 |
| --- | --- |
| `PAUSED → RUNNING` 且治疗有效 | 0x04 继续，沿用 ID |
| 其他 → `RUNNING` | 新 ID + 0x01 运行 |
| → `PAUSED` | 0x03 暂停（治疗有效时） |
| → 其他状态 | 0x02 停止（治疗有效时） |

B4 发送条件（满足任一）：

- 状态变化，且目标不是 `POWER_ON`；
- `mode/zone/set_seconds` 变化；
- 剩余时间变化；
- 戴帽状态变化；
- 电量档变化。

D2 发送条件：

- `mode/zone/set_seconds` 任一变化；
- 新治疗开始（`treat_started`）。

发送顺序：

```text
D1 → D2 → B4
```

每轮结束无条件更新快照：

```c
s_last_state   = state;
s_last_mode    = mode;
s_last_zone    = zone;
s_last_set     = set_seconds;
s_last_remain  = remain;
s_last_hat     = hat_worn;
s_last_battery = battery_level;
```

上电与关机：

- 上电首轮只建立快照，不上报。
- 关机走 `app_ble_report_off()`：保存时间戳；治疗有效时补发 D1 停止；再发 B4。

当前实现注意（事实）：

- B4 载荷没有戴帽字段，但 `hat_worn` 变化仍会触发 B4。
- `app_ble_send_d1/d2/query` 内部调用 `app_proto_send()` 后未检查返回值；队列满时快照仍会更新，下一轮不重发。

### 11.4 治疗 ID

- `s_timestamp`：时间戳种子，启动从 NV 恢复；`app_ble_proto_tick_sec()` 每秒累加。
- A0 带 4 字节时间戳时，只有大于当前种子才接受并写入 NV。
- 新治疗：`s_treat_id = s_timestamp++`。
- 暂停/继续：沿用 `s_treat_id`。
- 关机：`app_ble_report_off()` 保存 `s_timestamp`；治疗仍有效时补发 D1 停止，再发 B4。
- 正常关机后重启 ID 不重复；异常掉电不保存。

### 11.5 命令响应

| 命令 | 响应 |
| --- | --- |
| A0 | B0，再补一帧 B4 |
| A1 | B4 |
| A2 | B2 |
| A4 | B4 |
| F0 | F1（主/次/修订） |

异常长度：A1 payload 少于 2 字节不响应；A2 长度不为 2 或动作未知不响应。

### 11.6 公用取数/打包函数

| 函数 | 用途 |
| --- | --- |
| `app_ble_mode1()` | 模式一 |
| `app_ble_work_sta()` | 工作状态字节 |
| `app_ble_remain_sec()` | 剩余时间（非工作态返回设定时间） |
| `app_ble_fill_ssmm()` | 秒/分两字节 |
| `app_ble_fill_tid()` | 治疗 ID 四字节 |
| `app_battery_level_percent()` | 电量百分比 |

新增上报字段时，先复用上述函数；不要在各帧里重复写位运算和单位换算。

## 12. `board_config.h` 配置

分区：

1. 应用侧配置：`BOARD_CFG_APP_*`，业务参数与开关。
2. 固件版本、系统时钟。
3. 库模块级开关：`BOARD_CFG_STC8G_H_LIB_ENABLE_*`。
4. 库实例级开关：`BOARD_CONFIG_STC8G_8H_LIB_USE_*`。
5. 驱动层开关：`BOARD_CFG_COMM_DRV_USE_*`。
6. Driver pin config：引脚、波特率、PWM 参数。
7. 依赖检查：`#if defined(A) && !defined(B) → #error`。

固定资源分配：

| 资源 | 用途 |
| --- | --- |
| Timer0 | 1ms 系统 tick |
| Timer1 | UART1 波特率 |
| Timer2 | UART2 波特率 |
| Timer3 | 蜂鸣器 1kHz（500us 翻转） |
| 软定时器 0 | 蜂鸣节拍 |
| 软定时器 1 | 按键 10ms 扫描 |
| 软定时器 2 | 关机断电延时 |

新增驱动/开关时，同步补末尾依赖检查；GPIO 的 `USE_Pn` 没有编译期安全网，改调用点前先核对。

## 13. 通信底座 `app_protocol`

帧格式：

```text
PCB(0x00) | NO | LEN_L | LEN_H | CMD | DATA... | XOR
LEN = DATA 长度 + 6
XOR = PCB 到 DATA 末尾逐字节异或
```

接收：

- UART1 中断写入 STC 库环形缓冲。
- 主循环按读索引取字节，帧首必须为 0x00，否则丢弃。
- 收满 `LEN` 后校验 XOR，再调用 `proto_handle_cmd()`。

发送：

- `app_proto_send()` 组帧后入队。
- 队列 16 槽，环形留 1 槽，实际最多缓存 15 帧。
- 帧间隔 100ms；`proto_txq_poll()` 在主循环推进。
- `BOARD_CFG_APP_PROTO_TX_BLE_GATE_EN=1` 时，未连接直接丢弃队头帧。
- 关机前 `app_proto_tx_flush()` 阻塞发完队列。

## 14. NV 记录

EEPROM 0x0000 起 9 字节：

| 字节 | 内容 |
| --- | --- |
| 0~1 | 魔术字 0x53 0x49 |
| 2~5 | 时间戳（小端） |
| 6 | 电量档（0~3，0xFF 未知） |
| 7 | Byte0~6 异或 |
| 8 | Byte7 取反 |

写入时机：

- 首次定档、电量档变化。
- A0 时间戳变大。
- 正常关机保存时间戳。

规则：

- 电量只保存 1~3 档；0 档按 1 档写入。
- 上电无有效记录时电量为未知、时间戳从 0 开始。
- 写入前擦除扇区，写后回读校验 ID 和电量；同值不重复擦写。

## 15. 日志

- `debug_log.h`：`DBG_TAG` + `DBG_LVL`，按 `log_i/log_w/log_e` 分级。
- 调试串口 UART2 1,000,000/8N1；关闭调试时 `log_x` 为空操作。
- 业务日志按状态变化打印，另有每秒状态汇总。
- 协议帧日志：原始 HEX + 固定列宽中文说明，由 `BOARD_CFG_APP_PROTO_LOG_FIELD_EN` 控制。
- C51 单条 `log_x` 变参实参不超过 12 字节；超长必须拆成多条。

## 16. 代码约定与 C51 注意

- 文件内函数默认 `static`；公开接口在 `.h` 声明。
- 可变数据放 `xdata`；常量表放 `code`；避免大结构体按值传递。
- 连续状态值用枚举；错误码用宏；参数集中 `board_config.h`。
- 公共逻辑只保留一份：状态判断、延时关机、空闲、输出、分档、上报取数。
- 中断内不打印、不延时、不做业务判断。
- 通过函数指针调用的函数，其局部变量必须 `static`（OVERLAY 风险）。
- 不能用 `data` 作变量/形参/成员名。
- NV 记录位于 IAP 0x0000，所在 512 字节扇区要求代码不占用 0xFE00~0xFFFF。
- 当前 `STC8H4K64_24M.uvproj` 的 IROM 为 `0xFFF9`、`ReserveString` 为空，map 中没有 RESERVED 块，说明**当前工程文件未实际预留**；新建或交付前必须恢复 `IROM=0xFE00` + `RESERVE(C:0xFE00-C:0xFFFF)`，并用 map/hex 验证。

## 17. 新建工程步骤

1. 复制模板工程，改工程名、版本号、设备名。
2. 修改 `board_config.h` 的引脚、波特率、PWM 参数、应用开关。
3. 先跑通 Timer0 1ms tick 和 UART2 日志。
4. 接按键、指示灯、蜂鸣器，验证扫描与节拍。
5. 接 ADC/NTC/电池，验证分档与保护。
6. 接灯板输出（PWM 或 UART）。
7. 接协议与 NV，验证 A0/A1/A2/A4/F0、D1/D2/B4。
8. 编译检查 0 Error，查看 data/xdata/code 余量。
9. 按功能清单逐项测试。

## 18. 验收清单

- [ ] Keil 编译 0 Error / 0 Warning。
- [ ] `data`、`xdata`、`code` 余量满足要求。
- [ ] 已确认 IROM/Reserve 配置生效，代码未进入 0xFE00~0xFFFF（当前工程文件尚未配置，见第 16 节）。
- [ ] 冷启动、复位、掉电重启正常。
- [ ] 状态迁移符合 `app_state_enter()` 条件表。
- [ ] 上报帧字段偏移、长度、XOR 正确。
- [ ] 运行中 B4 每秒一帧，D1/D2 在对应事件触发。
- [ ] 未连接时不发送；重连后新的上报恢复。
- [ ] NV 记录可恢复，电量与治疗 ID 正常。

## 19. 关联经验

- `yjt/STC8H_8G/board-config-three-layer-switches.md`
- `yjt/STC8H_8G/keil-c51-language-pitfalls.md`
- `yjt/STC8H_8G/keil-c51-overlay-function-pointer.md`
- `yjt/STC8H_8G/workflow-verification-discipline.md`
