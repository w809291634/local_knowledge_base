# STC（8051）与 沁恒 CH（CH57x/CH58x/CH32V）

> 与已有 `yjt/STC8H_8G/keil-c51-language-pitfalls.md`、`keil-c51-overlay-function-pointer.md`、
> `keil-c51-pdata-overlay.md`、`board-config-three-layer-switches.md`、`stc8h-rom-budget-and-keil-optimize.md` **互补**：
> 那几篇讲"语言层/链接器层坑"，本篇讲"芯片层资源与寄存器"。**C51 的通用指针 3 字节、变参、Overlay 细节请去那三篇，本篇不重复。**
> `⚠校核` 见 `embedded/mcu-peripherals/ERRATA-*.md`。

## 1. STC8H（以 STC8H1K28 / 1K16 为主）

| 资源 | 内容 | 范围 |
|---|---|---|
| 存储 | **128B data + 128B idata + 1024B xdata**；最大 33K Flash；**EEPROM 512 字节、单页擦除、擦写 10 万次以上** | STC8H1K28 |
| 时钟 | **IRC ≤ 36MHz，常温精度 ±0.3%**；**ISP 区固定用 24MHz IRC**；上电复位先跑 ISP 程序，下载后按 ISP 设定的 IRC 运行；切外部晶振顺序 = 先使能 → 轮询稳定 → 写 `CLKSEL(FE00)`/`CLKDIV(FE01)`；**代码里 `FOSC` 必须等于 ISP 里选的频率** | STC8H★ |
| **XFR 访问** | 访问 `0xFA00~0xFFFF` 的扩展 SFR 必须 `P_SW2 |= 0x80`（EAXFR）+ 用 `MOVX`；宏 `EAXSFR()` / `EAXRAM()` | STC8G/8H★ |
| 定时器 | **T0~T4 共 5 个**；T0 模式 3 会占用成 NMI；T1 模式 0 = 16 位自动重装；**1T 模式周期 = (65536 − 重装值)/SYSclk，12T 模式再 ×12** | STC8H★ |
| 串口波特率 | UART1 波特率发生器可选 **T1 或 T2**（`AUXR.B0 = S1ST2`）；**UART2 固定用 T2**；1T 模式重载值 = `65536 − SYSclk/(4×波特率)`；24MHz@115200 误差 +0.16%、@9600 零误差 | STC8H1K28 |
| 串口引脚切换 | `S1_S(P_SW1 B7:6)`：00=P3.0/P3.1、01=P3.6/P3.7、10=P1.6/P1.7、11=P4.3/P4.4；`S2_S(P_SW2 B0)`：0=P1.0/P1.1、1=P4.6/P4.7 | STC8H1K28 |
| GPIO 四态 | `PxM1:PxM0` = **00 准双向 / 01 推挽 / 10 高阻 / 11 开漏**；**除 P3.0/P3.1 外上电默认都是高阻**；P5.4 复用为复位脚时内部 4K 上拉开约 **6.5ms** | STC8H★ |
| ADC | **10 位、12 通道，最快 500K/s**；通道 15 = 内部 1.19V BGV ⇒ 可用 `Vx = BGV/res_bg × res_x` 做比例测量（抗电源漂移） | STC8H1K28 |
| PWM | **PWMA = 4 对互补输出带死区**，PWMB = 4 路单端，其余功能完全相同；**与 T0~T4 完全独立、不占用它们**；1K28 **不支持 HSPWM** | STC8H1K16 |
| ISP 硬件选项 | "上电复位使用较长延时"写的是**配置字节而非 SFR**，需**重新上电**才生效；文档给 366.6 / 138.56 / 7.141ms（**作者自注：数值不在 PDF 原文，来自 CSDN 实测**） | STC8H |
| 4 线自动下载 | 芯片内 Bootloader **上电即监听 P3.0/P3.1 握手并自动测波特率**（扫描 2400~最高 115200）；用 **DTR/RTS 驱动三极管模拟"拔电再上电"**实现免按键 | STC8★ |
| 浮点代价 | 8 位 STC 无 FPU：`float` 链接软件库导致 ROM 暴涨（**一个 float 乘法约 +1.5K、`%f` 约 +5K**）⇒ 建议改定点数；STC32G 有 TFPU 但要用 C251 | STC8/15★ |

### STC 侧的坑（本篇最值钱的三条）

1. **轮询 + 中断混用会死锁**：一旦开了 `ES2`（UART2 中断），**ISR 里必须清 `S2TI/S2RI`**；
   否则 ISR 抢先把标志清掉，主循环里 `while(TI==0)` 的轮询**永远等不到 ⇒ 死锁**；
   反过来**不清标志就是中断风暴**。⇒ 同一串口不要混用轮询发送与中断接收，或统一由中断驱动。
2. **上电时序**：除 P3.0/P3.1 外所有 IO 上电为高阻 ⇒ 外部有下拉的负载（如 MOS 栅极）在上电瞬间状态不确定，需要外部确定态。
3. **USB 下载判据**：上电时 `P3.0/P3.1/P3.2` **不能同时为低**，否则会进 USB 下载模式
   （文档另一处写判据是 P3.2 经 4K 上拉读取，`⚠校核B` —— 两处不一致，以手册为准）。

### ⚠ 文档里不可用的两条"编译选项"
`#pragma OPTIMIZE(9)` = Favor Speed、`#pragma __declspec(noinline)/always_inline` ——
**Keil C51 优化级只有 0~8（语法 `OPTIMIZE(8,S/T)`），且不支持 `__declspec`**。这两条疑为 AI 生成内容，直接删。

## 2. 沁恒 CH 系列

### CH583（RISC-V + BLE5.3）规格
青稞 **V4A RV32IMAC**、32KB SRAM、**512KB Flash**、BLE5.3（2M/1M/500K/**125K** PHY）、RX **−98dBm**、TX **+6dBm**、
2×USB、4×UART、2×SPI、12 路 PWM、1×IIC、14 通道 12 位 ADC、14 路触摸、40 GPIO（**4 个 5V 容忍**）、最低 1.7V、AES-128、QFN48/28。
CH582 vs CH583：文档写"583 多一个 SPI、支持宽电压、48 脚固定"（`⚠校核C`：官方通常以引脚数/GPIO 数量区分，此说法无原文佐证）。

### Flash 映射与分区规划（**做 OTA/IAP 前必看**）
| 区 | 地址/容量（CH573/CH571） |
|---|---|
| CodeFlash | CH573 **448KB**(0~0x6FFFF)；CH573Q/CH571 **192KB**(0~0x2FFFF) |
| DataFlash | **32KB @ 0x70000** |
| BootLoader | 24KB @ 0x78000 |
| InfoFlash | 8KB @ 0x7E000 |
| SRAM | 18K（16K + 2K） |
| BLE SNV 默认 | **0x77E00（保留 512B）** |
| 示例冲突 | OTA 示例偏移 `0x7000`、IAP 示例偏移 `0x0000` ⇒ **合入同一工程必须互相避让** |
| 越界风险 | `BOOT_LOAD_CFG(0x7E000)`、`ROM_CFG_ADDR(0x7F000)` 在 DataFlash 32K **之外** |

### 时钟 / 中断 / ISR（RISC-V 特有，最容易翻车）
| 项 | 内容 |
|---|---|
| 时钟 | PLL = 32MHz × 15 = **480MHz** 再分频；`SYS_CLKTypeDef`：`0x40\|分频`，`0x48` = 60MHz；`GetSysClock()` 读 `R16_CLK_SYS_CFG(0x40001008)`；**20MHz 是 Flash 基本零等待点** |
| 定时器 | 4 × **26 位** TMR0~3（TMR1/2 带 DMA），计数时钟 = Fsys；另有 8 路 8 位 PWM4~11（周期固定 8 档） |
| 复用冲突 | 按优先级顺序仲裁：**PB23 RST# 优先、PWM11 最低** |
| **PFIC** | 256 中断、8 位优先级但**只有 [7:4] 有效**、数值小者优先、bit7 分两个抢占组、**只有 2 级嵌套**；**复位值 0 = 未配置 = 最高可编程优先级**；Reset/NMI/EXC 固定最高 |
| **ISR 属性（硬要求）** | 必须 `__attribute__((interrupt("WCH-Interrupt-fast")))` 或 `interrupt()`；否则按普通函数返回用 `ret` 而非 `mret` ⇒ **直接跑飞**；**RTOS 环境下禁用 fast 版**；`.highcode >RAM AT>FLASH` 把中断代码放 RAM |
| 下载 | 串口：**PA8(RXD1)/PA9(TXD1)/GND/VCC + PB22 BOOT**，先点下载再上电；USB：PB10/PB11；Code Flash 全擦需要 Link 供电后重上电；**复位脚擦除只有 WCH-LinkE / DAPLink / LinkW 支持**；CH32V003 8 脚版用 **PD1** 做调试下载 |

### BLE SDK 结构与参数（CH58x/573）
| 项 | 内容 |
|---|---|
| 组件 | TMOS / HAL / **BLE Stack（库不开放源码）** / Profiles |
| main 流程 | `SetSysClock → CH58X_BLEInit → HAL_Init → GAPRole_PeripheralInit → SimplePeripheral_createTask →` 循环 `TMOS_SystemProcess()` |
| 连接参数 | 间隔单位 **1.25ms**（7.5ms~4s）、从设备延迟 0~499、监督超时 100ms~32s；**有效间隔 = 间隔 × (1 + 从延)** |
| 库配置 | `BLE_MEMHEAP_SIZE ≥ 6K`；`BLE_BUFF_MAX_LEN` 只能取 **[27~251]** |
| **两条硬约束** | ① **含主机角色必须使用外部 32K 晶振**；② BLE 运行期间**禁止关全局中断 / 长 ISR**（会丢射频时序） |
