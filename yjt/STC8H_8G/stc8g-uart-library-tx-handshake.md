# STC8G 库串口发送依赖 UART ISR——关掉 ISR 整机挂死（严重）

> 适用：使用 `STC8G_H_UART.c` 的 `TX1_write2buff()` / `PrintString1()` / 由 kprintf 走库发送的 STC8G-8H 工程；`UART_QUEUE_MODE` 取 0 或 1 都适用
> 来源工程：STC8H1K08 家用红蓝光治疗仪固件（2026-10-13：为省 ROM 关 ISR，烧录后整机无法运行，当日全部回退）
> 目标：讲清"非队列模式 ≠ 不依赖中断"，并划定省 ROM 的正确边界。

## 结论先行

**不要关 `BOARD_CFG_STC8G_H_LIB_ENABLE_UART_ISR`，也不要为省 ROM 去取消 UART 的 NVIC 注册。**
`UART_QUEUE_MODE = 0`（非队列）只是**没有环形发送缓冲**，字节级握手仍然要靠 ISR；关掉后第一次打印就会停在 `while(COM1.B_TX_busy);` 死循环。

## 1. 症状

- 编译 **0 Error 0 Warning**，hex 大小正常，看不出任何异常；烧录后**整机像"不运行"**：显示、按键、出光全无反应。
- 挂死点在**第一次串口打印**，所以现象取决于"第一条 `log_iraw` 落在初始化流程的哪一步"——可能上电即死，也可能跑一小段才死。
- 现场极易误判为"程序没烧进去 / 芯片坏了"，因为没有任何错误提示。

## 2. 根因（库源码，逐行核对过）

`stc8g_8h_lib/STC8G_H_UART.c` 的非队列分支：

```c
SBUF = dat;
COM1.B_TX_busy = 1;         /* 置忙 */
while(COM1.B_TX_busy);      /* 死等 */
```

而 `COM1.B_TX_busy` **只在 `stc8g_8h_lib/STC8G_H_UART_ISR.c` 里被清零**：

```c
void UART1_ISR_Handler(void) interrupt UART1_VECTOR
{
    if(TI) { TI = 0; ... COM1.B_TX_busy = 0; }   /* 唯一清零处 */
}
```

⇒ **ISR 是清这个软件标志的唯一途径**。ISR 不编、不注册 NVIC，`B_TX_busy` 永远是 1。

## 3. 判据与修法

- **判据**：只要还在用库的发送函数，`BOARD_CFG_STC8G_H_LIB_ENABLE_UART_ISR` 必须打开、对应 UART 的 NVIC 必须注册。
- 若确实要彻底去掉 UART 中断（例如发布版完全不留串口），**必须同时替换库的发送函数**，自己写：

```c
SBUF = dat;
while(!TI);     /* 等硬件 TI，而不是等库的软件标志 */
TI = 0;
```

并保持 `UART_QUEUE_MODE = 0`。**只关 ISR 而不换发送函数 = 必挂。**
- **收益对比**（本工程实测）：这套"关 ISR + 取消 NVIC 注册"只省约 **156 B**；而整个关掉调试打印（`BOARD_CONFIG_DBG_NODBG = 1`）会让 kprintf + UART + 库整体不参与链接，**省约 1.1 KB**。大头在这里，不值得为一两百字节冒挂机风险。

## 4. 方法论教训（比这条坑本身更重要）

"`UART_QUEUE_MODE = 0` ⇒ 纯查询发送 ⇒ 不需要中断" —— 这个推断**是错的**，因为它查询的正是 ISR 才会清的**软件标志**。

⇒ **判断一条省 ROM 的改动是否安全，必须去读被调用函数的源码，而不是从宏名/配置名去推断语义。**
同类高风险项：端口初值（见 `yjt/STC8H_8G/stc8h-gpio-power-on-latch-and-sfr-access.md`）、中断使能、库的内部握手。
