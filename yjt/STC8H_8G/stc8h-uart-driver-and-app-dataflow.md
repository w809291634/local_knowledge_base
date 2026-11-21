# STC8H/8G UART 驱动框架与应用层数据流

> 适用：STC8H/8G + Keil C51 + STC 官方 UART 库 + `common/drv/drv_uart`
> 来源：GM202611004 WTW 定制352生发帽 V1.0.0（2026-11-20）
> 说明：按当前工程实际代码整理；UART1 用于蓝牙，UART2 用于调试或灯板。

## 0. 结论先行

- **前后台拉取模型**：中断只把字节写进固定缓冲，应用在主循环里取数据、拼帧、分发，不用回调、不用动态内存。
- **三层**：STC 库中断环形缓冲 → `drv_uart` 初始化封装 → `app_protocol` 主循环解析/发送队列。
- **接收靠“空闲标志”**：每收到 1 字节，ISR 把 `RX_TimeOut` 置 5；Timer0 每 1ms 递减；主循环只在 `RX_TimeOut==0` 时取数据。
- **发送是两级队列**：应用层帧队列（16 槽、100ms 帧间隔）+ STC 库字节发送。
- 当前 `UART_QUEUE_MODE=0`，`TX1_write2buff()` 是**阻塞发送**，不是 STC 库队列模式。
- UART2 调试与灯板二选一；调试优先时灯板模式自动改为 99。

## 1. 文件分工

| 层 | 文件 | 职责 |
| --- | --- | --- |
| 芯片库中断 | `stc8g_8h_lib/STC8G_H_UART_Isr.c` | 收字节写缓冲、置超时；发送完成清 `B_TX_busy` |
| 芯片库配置 | `stc8g_8h_lib/STC8G_H_UART.c` | `UART_Configuration()`、`TX1_write2buff()` |
| 驱动层 | `common/drv/drv_uart/drv_uart.c` | `comm_drv_uart_init()`，配置参数、引脚、NVIC |
| 板级配置 | `Source/board/board_config.h` | 波特率、引脚、BRT、缓冲区长度、调试开关 |
| 应用协议 | `Source/app/app_protocol.c` | 主循环取字节、拼帧、校验、发送队列 |
| 业务协议 | `Source/app/app_protocol_ble.c` | 命令分发、D1/D2/B4 |
| 灯板串口 | `Source/app/app_driver_board.c` | UART2 只发 `5A A5 CMD` |
| 调试日志 | `Source/board/debug_log.c` + `apl_kprintf` | UART2 阻塞打印 |

## 2. 数据流

```text
UART1 RX 中断
  └─ RX1_Buffer[128]
     COM1.RX_Cnt（写索引）
     COM1.RX_TimeOut = 5
            │
            │ 主循环，等待 RX_TimeOut == 0
            ▼
app_proto_update()
  s_rx_rd（读索引）
  └─ proto_feed_byte()
     └─ s_frame[32] → 帧首/长度/XOR 校验
        └─ proto_handle_cmd()
           └─ app_protocol_ble：命令处理、D1/D2/B4
              └─ app_proto_send()
                 └─ s_txq[16][32]（帧队列）
                    └─ 100ms 节流 + BT 连接门控
                       └─ TX1_write2buff()（阻塞）
                          └─ TI 中断清 B_TX_busy
```

## 3. 当前配置

| 项目 | UART1 | UART2 |
| --- | --- | --- |
| 用途 | 蓝牙 BLE | 调试或灯板 |
| 波特率 | 9600/8N1 | 调试 1,000,000/8N1；灯板 9600/8N1 |
| 引脚 | P3.6/P3.7 | P1.0/P1.1 |
| 波特率发生器 | Timer1 | Timer2 |
| 接收 | 使能 | 关闭 |
| 缓冲区 | RX 128；TX 128（仅队列模式使用） | RX 128；TX 128（仅队列模式使用） |
| 中断优先级 | Priority_1 | Priority_1 |

`board_config.h` 关键宏：

```c
#define BOARD_CFG_COM_TX1_LENTH    128
#define BOARD_CFG_COM_RX1_LENTH    128
#define BOARD_CFG_COM_TX2_LENTH    128
#define BOARD_CFG_COM_RX2_LENTH    128
#define BOARD_CFG_STC8G_8H_LIB_UART_QUEUE_MODE  0
```

`UART_QUEUE_MODE` 是全局宏，同时作用于 UART1/UART2。当前为 0，所以所有 UART 都是阻塞发送，`TX1_Buffer/TX2_Buffer` 不参与编译。

## 4. 中断层

`STC8G_H_UART_Isr.c` 的 UART1 中断做两件事：

```c
if (RI)
{
    RI = 0;
    RX1_Buffer[COM1.RX_Cnt] = SBUF;
    if (++COM1.RX_Cnt >= COM_RX1_Lenth) COM1.RX_Cnt = 0;
    COM1.RX_TimeOut = TimeOutSet1;   /* 当前库值 5 */
}

if (TI)
{
    TI = 0;
    COM1.B_TX_busy = 0;              /* 阻塞发送模式：清忙标志 */
}
```

要点：

- `COM1.RX_Cnt` 是写索引，ISR 自动回绕。
- `RX_TimeOut` 由 ISR 置 5，**不会自动递减**；必须由 1ms 定时器调用 `app_proto_tick_1ms()` 递减。
- `UART_QUEUE_MODE=0` 时，发送完成中断只清 `B_TX_busy`；`TX1_write2buff()` 依靠它退出阻塞等待。
- `UART_QUEUE_MODE=1` 时才会用到 STC 库的 `TX1_Buffer` 和 `TX_send/TX_write` 队列；当前工程不使用。
- **UART2 即使只发不收，也必须开 UART 中断**，否则 `B_TX_busy` 永远不清，第一次发送就会卡死。

## 5. 驱动层

`comm_drv_uart_init(n)` 只做初始化，不提供收发 API，收发仍用 STC 库：

```c
comm_drv_gpio_init(GPIO_P3, GPIO_Pin_6 | GPIO_Pin_7, GPIO_PullUp);
comm_drv_uart_init(UART1);
```

顺序要求：

1. 先把 RX/TX 引脚配为 `GPIO_PullUp`。
2. 再调用 `comm_drv_uart_init()`。
3. 再使用 `TX1_write2buff()` / `RX1_Buffer`。

驱动内部固定做三件事：

- `UART_Configuration()`：模式、波特率、BRT、接收使能。
- `UART1_SW()` / `UART2_SW()`：切换引脚。
- `NVIC_UARTx_Init(ENABLE, prio)`：**不管 `rx_en` 是否为 0 都开中断**，保证发送完成中断可用。

## 6. 应用层接收（重点）

`app_proto_update()` 每轮主循环调用：

```c
static uint8_t xdata wr;

wr = COM1.RX_Cnt;                       /* 快照写索引，避免边读边写 */
if (wr >= COM_RX1_Lenth) log_e("rx1c,%bu", wr);

while (COM1.RX_TimeOut == 0 && s_rx_rd != wr)
{
    proto_feed_byte(RX1_Buffer[s_rx_rd]);
    s_rx_rd++;
    if (s_rx_rd >= COM_RX1_Lenth) s_rx_rd = 0;
}

if (COM1.RX_TimeOut == 0 && s_frame_pos != 0)
{
    log_e("rxto");
    s_rx_bad++;
    proto_rx_reset(1u);                 /* 半包超时，丢弃并打印 */
}

app_ble_proto_update();
proto_txq_poll();
```

关键点：

- **只在 `RX_TimeOut==0` 时取数据**：即最后一字节后空闲约 5ms，认为一帧接收结束。
- `s_rx_rd` 是应用读索引，`COM1.RX_Cnt` 是 ISR 写索引；用 `wr` 快照避免读取过程中被 ISR 改掉。
- 半包超时：`s_frame_pos != 0` 且已空闲，说明帧没收完，直接丢弃并打印 `rxto`。
- 这套结构不阻塞 ISR，不需要在中断里解析协议。

帧状态机规则（`proto_feed_byte()`）：

| 检查 | 规则 |
| --- | --- |
| 帧首 | 第 1 字节必须为 0x00，否则丢弃（蓝牙模块文本通知也走这里） |
| 长度 | 第 3 字节为 LEN，第 4 字节必须为 0，LEN 范围 6~32 |
| 收齐 | 累计字节数等于 LEN 后进入解析 |
| XOR | 从 PCB 到 DATA 末尾异或，与最后 1 字节比较 |
| 分发 | `proto_handle_cmd(cmd, &s_frame[5], LEN-6)` |

限制：

- RX 缓冲 128 字节，单帧最大 32 字节。
- 如果外部持续发送且没有 5ms 以上空闲，主循环不会取数据，128 字节环形缓冲可能被覆盖；协议侧要保证帧间有间隔。

## 7. 应用层发送（重点）

发送分两级：

1. **应用帧队列**：`s_txq[16][32]`，环形留 1 槽，实际最多缓存 15 帧；帧间最小间隔 100ms。
2. **STC 字节发送**：`TX1_write2buff()`，当前为阻塞模式，每字节等到 TI 中断清 `B_TX_busy` 才返回。

组帧：

```c
len = payload_len + 6;
x = PCB ^ no ^ len ^ cmd;
/* PCB | NO | LEN_L | LEN_H | CMD | DATA... | XOR */
```

行为：

- `app_proto_send()` 组帧后入队，返回 1 表示入队成功，0 表示帧过长或队列满（打印 `txqful`）。
- `proto_txq_poll()` 每轮主循环推进；未到 100ms 不发下一帧。
- `BOARD_CFG_APP_PROTO_TX_BLE_GATE_EN=1` 时，未连接直接丢弃队头帧。
- 关机前 `app_proto_tx_flush()` 阻塞发完队列；因为底层是阻塞发送，返回时最后一字节已发出。
- 应用层 100ms 间隔是为了让蓝牙模块把每帧作为独立通知转发，避免 App 端粘包。

## 8. 1ms 超时节拍

Timer0 中断：

```c
void Timer0_ISR_Handler(void) interrupt TMR0_VECTOR
{
    tickCnt_Update();
    app_proto_tick_1ms();
}
```

`app_proto_tick_1ms()`：

```c
if (COM1.RX_TimeOut) COM1.RX_TimeOut--;
```

`app_proto_init()` 初始化时清空：

- `COM1.RX_Cnt = 0`
- `COM1.RX_TimeOut = 0`
- 帧状态 `s_frame_len/s_frame_pos/s_frame_xor`
- 发送队列头尾、上次发送时刻
- 发送序号

## 9. UART2 两种用途

### 调试

- 1,000,000/8N1，P1.0/P1.1，接收关闭。
- `kprintf` / `log_x` 走 `TX2_write2buff()`，阻塞发送。
- 与 UART2 灯板互斥；两项同时开时，灯板方式自动改为 99。

### 灯板

- 9600/8N1，接收关闭。
- 三字节帧 `5A A5 CMD`：
  - 关闭 `0x80`
  - 连续全/前/中/后 `0x81/0x82/0x83/0x84`
  - 脉冲全/前/中/后 `0x91/0x92/0x93/0x94`
- 状态变化立即发送；`app_driver_board_update()` 每秒重发当前命令。
- 只发不收，无 ACK。

## 10. 移植到新工程

1. `board_config.h` 打开 `BOARD_CFG_COMM_DRV_USE_UARTn` 和对应库层开关。
2. 配置 `BAUD/PIN_SEL/BRT/RX_EN/BAUD_DOUBLE/PRIORITY`。
3. 配置 `COM_TXn_LENTH/COM_RXn_LENTH`。
4. 打开 `BOARD_CFG_STC8G_H_LIB_ENABLE_UART_ISR`。
5. 把 RX/TX 引脚配成 `GPIO_PullUp`。
6. 调 `comm_drv_uart_init(UARTn)`。
7. Timer0 1ms 中断调 `app_proto_tick_1ms()`（如果使用本协议层）。
8. 应用层按“读索引 + 写索引 + 空闲标志”实现取数。
9. 发送按“应用帧队列 + 底层阻塞字节发送”实现。
10. 用回环测试帧首、长度、XOR、粘包和断连。

## 11. 常见坑

- **先配 GPIO 再初始化 UART**，否则引脚状态不对，收发失败。
- **UART2 只发也要开 UART 中断**，否则 `B_TX_busy` 不清，阻塞发送卡死。
- **不要在中断里打印或做协议解析**；ISR 只写缓冲/清标志。
- **不要在 `RX_TimeOut != 0` 时取数据**，可能拿到半帧。
- **区分两种“队列”**：应用层 `s_txq` 是帧队列；STC 库 `TX1_Buffer` 只在 `UART_QUEUE_MODE=1` 时启用。当前工程是 0，底层阻塞。
- **阻塞发送会占用主循环时间**：9600 下 32 字节约 33ms，帧要短。
- **未连接时上报帧会被丢弃**，不会缓存重发。
- **队列满会丢新帧**，`app_proto_send()` 返回 0；当前业务层没有检查返回值。
- **帧首不是 0x00 一律丢弃**，蓝牙模块的连接/断开文本不会误入协议。
- **RX 缓冲 128 字节**，连续无间隔数据要留余量。

## 12. 验收清单

- [ ] 回环收发正常，帧首、LEN、XOR 正确。
- [ ] 半帧超时能丢弃并打印 `rxto`。
- [ ] 连续 10 帧不粘包、顺序正确。
- [ ] 队列满时打印 `txqful`，不破坏已有帧。
- [ ] 未连接时不发送，重连后新数据恢复。
- [ ] 关机 flush 能发完最后一帧。
- [ ] UART2 调试与灯板不同时启用。
- [ ] 1ms 节拍运行，`RX_TimeOut` 能正常递减。
