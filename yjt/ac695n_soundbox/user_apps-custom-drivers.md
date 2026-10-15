# AC695N 512 项目自写驱动：RF315 遥控 / DMX512 / 断码屏 SEG / PWM 灯

> 工程：AC695N soundbox SDK 3.1.0，`SDK/apps/user_apps/`（约 1800 行自写代码），基线板级 `board_ac695x_demo`。
> 与 SDK 通用机制相关的部分只写"接入点"，细节在 `embedded/jieli_soundbox_sdk/`。
> 采集：2026-10-15，全部为源码直读 + git 历史，路径相对 `SDK/`。

## 0. 模块清单与接入点

| 模块 | 干什么 | 挂进 SDK 的方式 |
|---|---|---|
| `rf_decode.c/h` | PB05 上 315MHz 遥控脉宽码解码（24bit） | 自建线程 `"rf_decode"`（登记在 `task_table.c`），`module_initcall` 自启 |
| `rf_keyhandle.c/h` | 把 RF 键值变成按键事件 | `struct key_driver_para rfkey_scan_para` + `KEY_DRIVER_TYPE_RF`，**旁路**不发电改投消息 |
| `hardware/users_seg.c/h` | 7 脚断码屏（4 位数字 + 图标）主/子界面 | `LED7_PLATFORM_DATA` + `const struct ui_dis_api users_led7_main` 注册进 `ui_dis_main[]` |
| `dmx512.c/h` | DMX512 一发一收（250kbps，513 字节包） | 两个独立 UART 实例 + 事件处理 |
| `hardware/hardware_pwm_led.c/h` | PWM 推灯 | `timer_pwm_init` / `mcpwm_init` |
| `hardware/uart.c/h` | 通用 UART 样板 | **当前未编译**（Makefile:727 注释掉） |
| `hardware/delay.c/h` | `delay_88us`/`delay_200us`（nop 循环 2330 次） | 直接调用，**非阻塞场景不适用长延时** |
| `user_config.h` | 全部引脚与使能宏集中处 | 被 `apps/soundbox` 侧 include |

调用点：`users_seg_config()` 在 `apps/soundbox/task_manager/bt/bt.c:1225`（`app_bt_task` 内），
`dmx512_rx_config()` / `rf_config()` / `hardware_pwm_led_config()` 在同一处**被注释掉**，当前只跑 SEG。

---

## 1. RF315 解码（`rf_decode.c` + `rf_keyhandle.c`）

### 解码原理（值得复用的套路）
- **TIMER3 每 1ms 轮询 PB05 电平**，用 3bit 移位滤波：`filter==7` 判高、`==0` 判低（`:52-72`）。
- 24bit 脉宽码：高宽 > 低宽 = 1（`:83`）；**满 25 个下降沿判成功**，取低 24 位存 `__rf_data`（`:126`）。
- 成功后 `os_taskq_post_msg("rf_decode", 1, MSG_RF_RECV_FLAG)`，`MSG_RF_RECV_FLAG = 0xA5`
  —— 头文件明确要求**不得与 `key_event_deal.h` 的 rf 事件号撞**。
- **时序保护**：`local_irq_disable()` + `AT_VOLATILE_RAM_CODE`（`:33-38`）；
  `request_irq(IRQ_TIME3_IDX, **7**, ...)` 取最高优先级（`:195`）；
  `set_rf_clk()` 自动搜分频使 `PRD` 落在 `0x100~0x7fff`；
  `MAX_PULSE=30 / MIN_PULSE=3`（`:49`，注释：**最小脉宽不应小于滤波宽度**）。
- 线程 `rf_decode_task_handler`（`:222`）由 `module_initcall(rf_decode_task_init)`（`:398`）自启；
  线程内 `syscfg_read/write(CFG_USER_RF_ADDR)`（id=2，用户区 1~49 合法），
  **注释指出 syscfg 不能早于相关模块初始化前调用**；收到 `KEY_RF_LEARN` 才落盘地址（`:261`）。

### 按键接入（旁路模式）
- `rfkey_scan_para`（`:35`）：`scan_time=38ms`、`filter_time=1`、`long_time=750/38`、
  `hold_time=(750+150)/38`、`click_delay_time=0`。
  **注释里的两条硬规矩**：抬起后等待连击数 >20 会让单击变迟钝 ⇒ 设 0；**扫描频率必须大于信号周期**。
- 注册：`key_driver.c:332 sys_s_hi_timer_add(&rfkey_scan_para, key_driver_scan, 38)`。
- 识别到 `KEY_DRIVER_TYPE_RF` 后**不发系统按键事件**（`key_driver.c:234-252`），改查
  `rf_key_table[10][KEY_EVENT_MAX]`（`:11-19`，实际 6 个键值 `0x02/0x08/0x01/0x04/0x0C/0x06`
  → CLICK/LONG/HOLD/LOOSE/DOUBLE/TRIPLE）后 `os_taskq_post_msg("rf_decode", 1, msg)`。
- `rf_get_keyvalue()`（`:98`）用 `code[4]` 数组**兼作"按下/抬起"识别与消抖**，
  `FILTER_TIME_MAX=3` **不可为 0**（否则越界，`:97`）；地址判据 `rf_data>>4 != rf_addr`（`:147`）；
  **函数内部会清 `rf_data`**（`:177` 注释提醒后续要用值得先取走）。
- **键值位宽是硬约束：4 位**。`user_config.h:15` 注明"如果是 8 位的键值，要修改相应的驱动"。

### 学习（配码）状态机 `rf_learn()`（`:241`）
`0 → 1 → 2 → 3` 四态；进入需**连续 `RF_LEARN_FILTER_CNT(3)` 次看到学习键**（防误触，返回 1 表示误触发）；
总窗口 5s；有效长按阈值 `RF_LEARN_VALID_TIME/38/2 - 3`（`:237`，作者按实测把时长除以 2）；
松手判据 1s（`rf_data>>4` 与学习地址不同即视为松手）；成功才
`os_taskq_post_msg("rf_decode", 2, KEY_RF_LEARN, addr)`（`:348`）。
**⚠ 学习期间 `get_value()` 一律返回 `NO_KEY`**（`:142`）—— 否则别的键值会被误识别成操作。

---

## 2. DMX512（`dmx512.c`）

- **发与收必须用两个不同 UART 实例**（`:25` 注释：同一串口不能同时收发）。
- RX：`dmx512_rx_config()`（`:209`）= 250000bps、`is_9bit=1`、`frame_length=1024`、`rx_timeout=20ms`、`tx_pin=-1`；
  三级缓存 `cbuf/rxbuf/txbuf` 各 1024 且 `aligned(4)`（`:21-23`）。
  ISR `uart_module_isr_hook`（`:165`）**只投 `SYS_DEVICE_EVENT`**；
  `uart_module_event_handler`（`:125`）`read()` 到二级缓存再 `uart_module_event_deal`，
  **`len < 513` 直接丢弃**（`:89`）。
- TX：`dmx512_send_start()`（`:264`）流程是这套实现的核心技巧：
  1. **Break 靠手动把 TX 脚拉低 `delay_88us()`**（不用硬件 break 功能）；
  2. `dmx512_tx_config()` 开串口 —— **开串口本身会把脚拉高约 31.5us，正好充当 MAB**（`:283` 注释）；
  3. `uart_module_tx` 发 513 字节（含 SC 起始码）；
  4. 置高 + 关上下拉 + `dmx512_tx_close()`；
     **⚠ 必须再 `gpio_set_direction(TX, 0)` 才真有高电平输出**（`:295` 注释）；
  5. `delay_200us()` 收尾。
- `dmx512_transpond()`（`:305`）：从 `rxbuf+1` 拷 513 字节（跳过被当起始信号的那个 0 字节）再发 —— 做转发板用。
- `dmx512_send_test()`（`:326`）：用 513 字节包的第 1/2 字节做从机开关（`0xA5` 关 / `0x5A` 开）。
- **⚠ 疑似 bug（未上机确认）**：`:130` 与 `:143` 用
  `strcmp(e->arg, DEVICE_EVENT_FROM_UART_RX_OVERFLOW)` 判事件，而该宏是**整型四字符码**
  （`include_lib/system/event.h:86`）、`e->arg` 是 `void*`。SDK 正确写法是 `(u32)e->arg == ...`
  （见 `cpu/br23/uart_test.c:46`）。同样的写法在 `hardware/uart.c:42` 也有一处。
  → **溢出/超时事件分支实际上永远不会进**，需要上机验证后改。

---

## 3. 断码屏 SEG（`hardware/users_seg.c`）

实现骨架与踩过的坑（**这几条是本项目最值钱的调试结论**）：

- 7 脚扫描用 **PB00–PB06**（`:8-18`）；注册 `users_led7_main{ui=UI_USERS_LED_MENU, open, ui_main, ui_user, close}`
  （`:25-31`），配套 `apps/soundbox/include/ui/style_led7.h:24` 的 `UI_USERS_LED_MENU` 与 `:77-78` 的
  `MENU_SHOW_NUM_1/2`；`users_seg_config()`（`:195`）= `led7_init` + `ui_set_main_menu`。
- 主界面套路（`:54`）：`show_lock(1)` → `setX(0)` → `show_null()` → 逐个 `show_icon()` → `show_string("tley")` → `show_lock(0)`。
- **⚠ `show_lock` 必须包住整段**，否则 2ms 扫描会在"清空"和"填新值"之间显示空帧，肉眼可见闪烁。
- 子界面 `ui_user` 用 `switch(menu)` 分派，**命中返 true、default 返 false**（交回公共 `ui_common`）。
- **60s 倒计时（`MENU_SHOW_NUM_2`，`:115`）的实现套路**：
  `sys_timer_add(NULL, __call_show_num_2, 1000)` 的回调里**只做一件事**——
  `ui_set_tmp_menu(MENU_SHOW_NUM_2, 1100, 0, NULL)` 把自己重新投成子界面；
  用 `timer_id == 0` 区分首帧，**避免每帧 `show_null` 引起闪烁**（`:135-140`）；
  并在 `ui_get_app_menu(0) != MENU_SHOW_NUM_2` 时兜底 `sys_timer_del` + 复位 `cnt`（`:120-133`）。
- **⚠ 作者写下的两条限制**（`:109-111` 注释，务必记住）：
  ① **界面超时时间必须大于 `sys_timer_add` 的周期**，否则功能没跑完就回主页；
  ② **`sys_timer` 到时会打断当前界面显示**。
- **⚠ 为什么是 1100ms 而不是 1000ms**：`ui_set_tmp_menu` 的 ret_time 按 `(ms+99)/100` 向上取整成 100ms 份数，
  1000ms 与 1000ms 定时器周期贴边，会被判定为已到期而提前回主页。**改这里要同时改 bt.c 与 `__call_show_num_2` 两处。**
- **⚠ `users_seg_config()` 放在 `app_bt_task` 的代价**：每次进 BT 模式都会重跑 `led7_init`
  → 多一次 malloc（驱动里不 free 前一份，`led7_driver.c:672`）+ 一次无效 `UI_INIT`。
  初始化应挪到 `board_init` 或只做一次的入口。
- 早期用全局 `is_cnt_flag` 让主界面在倒计时期间不显示，后改成 `ui_get_app_menu(0)` 判当前子界面 + 兜底删定时器
  —— 解决"界面来回切换时定时器残留"。**判"我现在该不该画"要用框架给的当前菜单 ID，不要自己加全局标志位。**

---

## 4. PWM 灯（`hardware/hardware_pwm_led.c`）

- `hardware_pwm_led_config()`（`:5`）= `timer_pwm_init(JL_TIMER0, 10000, 994, PA05, 0)` +
  `(JL_TIMER1, 10000, 994, PA12, 0)`（≈99.4% 占空比，duty/fre 0~10000）。
- `hardware_mcpwm_led_config()`（`:43`）= mcpwm CH0、边沿对齐 1kHz、duty 5000、PA00/PA01 互补输出。
- 4 个 on/off 函数目前是**空壳**（`:19-38`）。
- 注意 `PA05` 与 `hardware/uart.c` 的 RX 同脚，二者只能取其一。

## 5. 引脚资源冲突表（实测结论，本项目最重要的一张表）

| 脚 | 项目内占用 | 同脚的其他占用（SDK 侧） | 结论 |
|---|---|---|---|
| **PB05** | SEG pin[5] **且** `RF_DECODE_PIN` | UT0 **TX 与 RX 双硬脚**（`uart_dev.c:766,770`）、T3 PWM 硬脚、**BR23 充电 LDO5V 检测专用脚**（`charge.c:128/148/157/380/409`、`chargestore.c:210`）、mcpwm CH3 H | **最严重**。SEG 每 2ms 把 PB05 推成输出，与 RF 的输入配置直接互斥；TIMER3 又同时被 `irflt.c:10` 与 `rf_decode.c:4` 声明 |
| **PB01** | SEG pin[1] **且** `DMX512_RECV_DATA_PIN` | **UT1_RX 硬脚**（`uart_dev.c:770`）、`AD_CH_PB1`、IOKEY POWER（DISABLE） | **是冲突**：开 `dmx512_rx_config()` 后 UT1 会把 PB01 抢为串口 RX |
| PB00 | SEG pin[0] | 软 IIC CLK（DISABLE）、IOKEY PREV（DISABLE）、UT1_TX 硬脚、mcpwm CH1 H | 目前不冲突（除启用 mcpwm CH1） |
| PB02 | SEG pin[2] | **板载 led7 pin[6]**（`board.c:504`）、IOKEY NEXT（DISABLE）、mcpwm CH1 L | 与板载 led7 表重叠，靠 users_seg 的二次 init 覆盖 |
| PB03 | SEG pin[3] | 软 IIC DAT（DISABLE）、LINEIN 检测脚（LINEIN 关）、T2 PWM 硬脚、`AD_CH_PB3` | 目前不冲突 |
| PB04 | SEG pin[4] | UT0_TX 硬脚、`AD_CH_PB4`、mcpwm CH2 H | 目前不冲突 |
| PB06 | SEG pin[6] | `TCFG_PWMLED_PIN`（PWMLED 当前 DISABLE，未生效）、TOUCH_KEY0（DISABLE）、UT0_RX 硬脚 | 启用 pwm_led 会撞 |
| PC04 | `DMX512_SEND_DATA_PIN` | **板载 led7 pin[4]**（`board.c:502`）、UT2_TX 硬脚、mcpwm CH5 H、`AD_CH_PC4` | 与板载 led7 表重叠 |
| PA05 | `uart.c` RX + `hardware_pwm_led` T0 脚 | UT0_TX 硬脚、`AD_CH_PA5` | uart.c 未编译，启用即与 T0 PWM 撞 |
| PA10 | — | **`TCFG_ADKEY_PORT`（当前 ENABLE）**、UT2_RX 硬脚、mcpwm CH4 L | AD 按键在用，动 UT2/mcpwm 要避开 |
| PA12 | `hardware_pwm_led` T1 脚 | UT0_RX 硬脚、`AD_CH_PA12` | 与 UT0 非硬脚方案二选一 |
| DP/DM | — | **log 口 `TCFG_UART0_TX_PORT=IO_PORT_DP`**、在线调音 `TCFG_TOOL_TX/RX` | 占用了就不能挪作他用 |
| PA03 | — | `TCFG_FLASH_DEV_SPI_CS_PORT` | 内置 flash CS，禁用 |

**板载 led7 表（PC00–PC05 + PB02）与 users_seg 表（PB00–PB06）不共存**，
靠 `users_seg_config()` 二次 `led7_init` 覆盖生效，代价是一次 malloc 泄漏 + 一次无效 `UI_INIT`。

**当前为何没炸**：`bt.c` 里 `rf_config()` 与 `dmx512_rx_config()` 都是注释状态，只有 SEG 在跑。
**一旦启用 RF 或 DMX512 接收，PB05 / PB01 必须先重新分配。**

## 6. 开发节奏（git 历史提炼，作者 voidobserve，2024-09-12~13，14 个提交）

```
a6b95a5 Initial
42063b4 简单实现 DMX-512 发送 → 75c77de 一发一收稳定
0a9cbc8 加 RF315 解码 → d74dee1 DMX512+PWM+rf 接收线程多功能测试
a24f42c → c037f14 → 7a8387d → 3bcaa9f RF 学习（可重复学习 + 掉电保存）
38f06f9 可以显示字符、图标 → a31ed04 主界面 → 6ab5367 按键进字节面 → e84d3ba 倒计时显示 → b4d68fa 优化倒计时逻辑
```

**节奏特征**：先单点跑通 → 再补协议细节 → 最后做状态机与滤波；**每一步上机验证后才提交**。
这条对本项目的价值：SEG 那 5 个提交每个都只动 5 个左右源文件，问题范围天然可控。

`38f06f9` 那次改动清单（很有代表性）：新建 `users_seg.c` 87 行；把 `led7_show_lock` 从 static 改为导出
（`led7_driver.c:632`）；在 `led7_driver_cfg.h` 新增 `UI_LED7_PIN7_TRUE_TABLE4` 共 66 行；
Makefile +2；`task_table.c` 加 `"users_seg" 3/512/128`；
**同时把 bt.c 里的 dmx512 与 pwm 初始化注释掉腾 IO** —— 这本身就是"引脚不够就先让位"的实操记录。

## 7. 构建侧遗留

- `apps/user_apps/hardware/uart.c` **在 Makefile:727 被注释掉**（`# apps/user_apps/hardware/uart.c\`），
  且 `user_test_uart_config()` 在 bt.c 里没有调用点 → 要用时既取消注释又要补调用。
- `hardware/uart.h` 与 SDK 的 `asm/uart.h` / `uart.h` **同名**（其头注释已写"工程中有同名头文件，不能直接使用"），
  include 顺序会造成拿到错的那个。
- `apps/soundbox/user_apps/` 路径不存在，`SDK/README.md` 那句"用户程序在./apps/user_apps路径下"
  指的是 `apps/user_apps`，别按 README 的话去找 `apps/soundbox/user_apps`。
