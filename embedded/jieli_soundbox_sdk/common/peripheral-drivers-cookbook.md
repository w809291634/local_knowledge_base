# 外设驱动速查与独占资源表（BR23 实测，接口形态跨型号通用）

> 用法：先在本表找到"入口函数 + 最小例 + 硬约束 + 独占资源"，再去 `*_test.c` 抄骨架。
> **本 SDK 自带的 `*_test.c` 几乎全部被 `#if 0` 包住**（这是最大的隐藏福利：现成最小可用例，但要自己打开）。
> 路径相对 SDK 根。

## 1. GPIO 函数族

头文件 `include_lib/driver/cpu/br23/asm/gpio.h`。编号规则：**PA=0-15、PB=16-31、PC=32-47、PD=48-55**
（`IO_GROUP_NUM=16`，`:66-72`），`IO_PORT_DP/DM` 排在 `IO_MAX_NUM` 之后（`:140`）。

| 用途 | 接口 |
|---|---|
| 方向 | `gpio_set_direction(g, 1=输入)` `:224`；`gpio_direction_output(g, val)` `:257` |
| 输出值 / 读写 | `gpio_set_output_value` `:235`；`gpio_read` `:397` / `gpio_write` `:415` |
| 上下拉 | `gpio_set_pull_up` `:279` / `gpio_set_pull_down` `:302`（0=关） |
| 数字输入使能 | `gpio_set_die` `:344` / `gpio_set_dieh` `:354`（**做数字输入必须 die=1**） |
| 驱动能力 | `gpio_set_hd0` `:324` + `gpio_set_hd` `:334`（两位合起来 `11` = 最强） |
| 引脚复用输出 | `gpio_output_channle` `:388`；`gpio_uart_rx_input` `:454`；`gpio_irflt_in` `:433`；`gpio_set_uart0` `:491` |

**标准"输入检测"四件套**（本工程 RF 解码就是这么写的，`rf_decode.c:213-216`）：
`pull_up=0 → pull_down=0 → die=1 → direction=1`。少 die=1 时 `gpio_read` 读不到电平。

## 2. UART

- 接口：`uart_dev_open() / uart_dev_close()`（`include_lib/driver/cpu/br23/asm/uart_dev.h:169`）。
- 最小例：`cpu/br23/uart_test.c:174 uart_dev_test_main()`（**整文件被 `#if 0` 包住**，`uart_test.c:6`；
  `uart_bt_product.c` 同样）。
- **硬件脚位表**（`uart_dev.c:762-774`，不在表内的脚要走复用）：

| | TX 可选 | RX 可选 |
|---|---|---|
| UT0 | PA05 / PB04 / **PB05** / PA11 | PA06 / PB06 / **PB05** / PA12 |
| UT1 | PB00 / PC00 / PA00 / DP | **PB01** / PC01 / PA01 / DM |
| UT2 | PA02 / PA09 / PB09 / PC04 | PA03 / PA10 / PB10 / PC05 |

  非硬脚：`gpio_output_channle()` 出 TX + `gpio_uart_rx_input()` 入 RX（`uart_dev.c:870-880`）。
- 硬约束：
  - `rx_cbuf_size` **必须非 0 且是 2 的幂**，否则 `uart_dev_open` 直接返回 NULL（`:819-823`）——典型"打开失败但没有错误信息"。
  - buffer 要 `aligned(4)`。
  - `CONFIG_UARTx_ENABLE_TX_DMA=1`（`:45-53`）时**中断里不能调 `write()`**（内部要 pend 信号量）。
  - 事件码 `DEVICE_EVENT_FROM_UART_RX_OVERFLOW / _OUTTIME` 是**整型四字符码**（`include_lib/system/event.h:86`），
    正确判法是 `(u32)e->arg == DEVICE_EVENT_FROM_UART_RX_OVERFLOW`（`uart_test.c:46`）；
    **`strcmp(e->arg, ...)` 是错的**（`e->arg` 是 `void*`，四字符码不是字符串）。
- 口占用现状：log 口 = `TCFG_UART0_TX_PORT=IO_PORT_DP`（demo cfg `:47`，`debug_uart_init` 在 `board_ac695x_demo.c:855-864`，
  RX 不接、波特率 `TCFG_UART0_BAUDRATE 460800`）；在线调音口 `TCFG_TOOL_TX/RX`（cfg `:553-554`）。
  **`chargestore` 只用 UART0/1、`chargebox` 同时独占 UART1+UART2**（`chargestore.c:178`、`chargebox_hw.c:194`，都带 ASSERT）；
  `app_config.h:388` 还写了"串口升级与 chargestore 抢 UART1"。

## 3. SPI

- 接口：`spi_open/spi_send_byte/spi_recv_byte/spi_dma_send/spi_dma_recv/spi_close`（`spi.c:524/381/410/599/577/671`）。
- 最小例：`spi_test.c:129 spi_test_main()`（`#if 0`）。文件头 README（`:8-22`）四条硬约束：
  ① **CS 由 API 之外自己控**；② DMA 地址 4 对齐；③ 板级必须定义 `spi1_p_data/spi2_p_data` 否则**编译不过**；
  ④ **带 flash 的芯片别用 spi0**（和内置 flash 抢）。

## 4. IIC（两路实现，接口对称）

- 硬件：`hw_iic_init()`（`iic_hw.c:192`）；软件：`soft_iic_init()`（`iic_soft.c:71`）。
  配套都提供 start/stop/tx_byte/rx_byte/read_buf/write_buf/suspend/resume。
- 配置表在板级 `.c`（`board_ac695x_demo.c:559`，demo 配 CLK=PB00 / DAT=PB03，cfg `:55-56`），
  但 demo 板 `TCHFG_SOFT_I2C_ENABLE=DISABLE`（注意宏名本身拼写是 `TCHFG`，grep 时别漏）。
- 最小例：`iic_eeprom_test.c:244 eeprom_test_main()`、`iic_slave_test.c:210/239`（均 `#if 0`）。

## 5. PWM：两套完全不同的东西

**(a) mcpwm / timer_pwm（`cpu/br23/mcpwm.c`）**
- `mcpwm_init(struct pwm_platform_data*)`（`:252`）；**硬件 H/L 脚对是固定的**（`:15-16`）：
  CH0=PA00/PA01、CH1=PB00/PB02、CH2=PB04/PB06、CH3=PB09/PB10、CH4=PA09/PA10、CH5=PC04/PC05。
  **ch ≥ 3 不支持任意脚映射**（`:272-277` 直接报错）。
- `timer_pwm_init(JL_TIMERx, fre, duty, port, output_ch)`（`:524`）：T0=PA05、T1=PA12、T2=PB03、T3=PB05 为硬件脚，
  非硬件脚**必须给 `output_ch`**，否则返回 -1。占空比 = duty/fre，范围 0~10000（10000=100%）。
- 最小例：`mcpwm_test()`（`mcpwm.c:333`）。

**(b) pwm_led（专用推灯硬件，`cpu/br23/pwm_led.c`）**
- `pwm_led_init(&pwm_led_data)`（`:275`）、`pwm_led_mode_set/clk_set/display_mode`（`pwm_led.h:180-194`），
  板级用 `LED_PLATFORM_DATA_BEGIN/END` 宏（`pwm_led.h:170`）。
- demo 板 `TCFG_PWMLED_ENABLE=DISABLE`（cfg `:465`，因 `TCFG_ADKEY_LED_IO_REUSE=DISABLE`）。

**(c) RGB 灯串（`cpu/br23/led_spi.c`）**：`led_spi_init/led_spi_send_rgbbuf(_isr)`（`:33/79/98`），
**硬编码 SPI1 + PORT'B'(=PC05)、8MHz**；完整例 `ledc_test.c:434 my_led_test()`（`#if 0`）。

## 6. 红外 / 触摸 / ADC

- **irflt**：固定 `JL_TIMER3` + `IRQ_TIME3_IDX`（`irflt.c:10-12`）。流程 `ir_input_io_sel()`（→ `gpio_irflt_in` + die + input，`:169`）
  → `ir_output_timer_sel()`（注册优先级 5，`:182`）。**⚠ TIMER3 与本工程 `rf_decode.c` 抢同一个定时器**
  （IR 当前 DISABLE 所以没炸，同时开必炸）。
- **plcnt**（脉冲计数触摸）：`plcnt_init()`（`plcnt.c:223`）；**ctmu**：`ctmu_init()`（`ctmu.c:295`，
  `IRQ_CTM_IDX` 优先级 1，需 `TCFG_CTMU_TOUCH_KEY_ENABLE`）。
- **ADC**：`adc_add_sample_ch / adc_get_value / adc_get_voltage`（`adc_api.c:42/97/130`）。
  **通道只有这些**：PA1/PA5/PA6/PA10/PA12/**PB1**/PB3/PB4/PB8/PB10/PC4/PC6/DP/PC5（`asm/adc_api.h:6-20`）。
  → adkey 要占一个 ADC 通道（demo 板 `TCFG_ADKEY_PORT=PA10`，cfg `:231`，当前 ENABLE）。

## 7. 定时器：选错会直接影响功耗（务必区分）

| 接口 | 执行上下文 | 对低功耗的影响 |
|---|---|---|
| `sys_timer_add/del`（`include_lib/system/timer.h:76`） | sys_timer 线程发消息给**注册它的那个线程**执行 | 会唤醒系统；精度 10ms |
| `sys_hi_timer_add` / `sys_s_hi_timer_add`（`timer.h:260/278`，=`usr_timer_add(...,1/0)`） | 高优先级 | **只要注册着，系统永远不进 power_down**，删掉才会 |
| `sys_hi_timeout_add` | **中断里执行** | power_down 期间节拍停止，唤醒后继续 ⇒ **定时间隔变成不固定** |
| `app_timer.c`（`cpu/br23/app_timer.c`） | **独占 JL_TIMER2 / `IRQ_TIME2_IDX`，2ms 一次** | 只用于 `app_timer_led_scan()` 注册的扫描函数（`:71-91,104`）；注释警告"被低功耗使用，用时要关低功耗"（`:29`） |

按键扫描用的是 `sys_s_hi_timer_add`（`key_driver.c`）。led7 显示扫描挂在 `app_timer` 的 2ms 上（见
`led7-display-and-ui-framework.md`）。

## 8. 充电与端口唤醒

- `charge_init()`（`charge.c:539`）、`charge_start/close`（`:232/255`）。
  **⚠ BR23 专属坑：LDO5V 检测复用 PB05，驱动会强制读写 PB05 的内部下拉**（`charge.c:128/148/157/380/409`、
  `chargestore.c:210`）。demo 板 `TCFG_CHARGE_ENABLE=DISABLE`（cfg `:97`）。**任何想用 PB05 做别的事之前先查这条。**
- `port_wkup_interrupt_init(port, edge, cb)`（`port_wkup.c:30`）：独立 `JL_WAKEUP` 模块，
  **只有 1 路**（固定 input channel0、`IRQ_PORT_IDX` 优先级 3），且**低功耗下中断无效**（`:5-7`）；
  例 `my_port_wkup_test()`（`:77`）。

## 9. 其他

- `overlay_code.c:84 overlay_load_code(type)`：把 AEC/WAV/APE/FLAC/M4A/AMR/DTS/FM 代码搬进**同一块 RAM 段**
  （overlay），所以"同时用两种大算法"受段容量限制，不只是算力问题。
- `irq_config.c`（`apps/soundbox/board/br23/irq_config.c`）的 `irq_pro_list[]` 定死所有中断默认优先级：
  `IRQ_TIME2_IDX` 在 `TCFG_LED7_RUN_RAM` 时为 **6**（关总中断仍能进），否则 5（`:12-17`）；`IRQ_TIME3_IDX=3`；
  UART0/1=3、UART2=0。
- `localtws/`（`localtws.c:215 __initcall(localtws_globle_init)`）是**对箱本地音频转发**，与外设无关，别当本地总线驱动读。
- `setup.c` 是 CPU 早期初始化与异常入口（多段 `#if 0`，异常解析实现真身在闭源库），见 `logging-exception-debug.md`。
