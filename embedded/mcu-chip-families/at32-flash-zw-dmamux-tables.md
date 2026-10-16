# AT32F435/437 手册表格唯一副本（ZW-SRAM 分配 / 系统选项 / 闪存结构 / IOMUX / DMAMUX）

> 来源：《单片机外设和调试基础知识.docx》第 4 章 **截图层**，2026-10-16 逐张读（028 张图全部过完）。
> 这些表在原文里**只以图片存在**（文字层是空表），本文件就是本地唯一可检索副本。
> `（ch04/0NN）` = 导出截图序号，对应关系见 `Temp/mcu_doc/media/ch04/INDEX.tsv`。
> 结论与踩坑解读在 `at32.md` §6；冲突项集中在 `embedded/mcu-peripherals/ERRATA-*.md` 的 H 类。
> **截图分辨率有限，看不清的格子一律写"截图不清"，没有补全。**

## 1. 零等待区 ZW 与 SRAM 的此消彼长（ch04/003）

**同一块 352 KB 空间在"片上 SRAM"与"闪存零等待区 ZW"之间分配**：

| 配置 | 片上 SRAM | 闪存零等待 ZW |
|---|---|---|
| 默认 | 96 KB | 256 KB |
| 扩展 | 224 KB | 128 KB |

⇒ **要 SRAM 就得牺牲取指加速区**，这是 AT32 与 STM32（CCM/ART 固定划分）最大的思路差别；
分配档位由 §2 的系统选项位决定，**且改写有前提条件**（见 §2"注意"行）。

## 2. 表 5-6 扩充的系统选项 `EOPB[7:0]`（ch04/006）

按闪存容量分三组，编码值 = "片上 SRAM + 闪存零等待延迟区域" 的分配：

### 2.1 256 K 档（用位 [1:0]）

| 编码 | SRAM + ZW |
|---|---|
| 00 | 512 K + 128 K |
| 01 | 448 K + 192 K |
| 10、11 | 384 K + 256 K（**出厂默认**） |

- 位 2：保留不用。
- **注意（照抄）**：位 1~0 的改写**只能在安全库区未启动的情况下实现**。

### 2.2 448 K 档（用位 [2:0]）

| 编码 | SRAM + ZW |
|---|---|
| 000 | 512 K + 128 K |
| 001 | 448 K + 192 K |
| 010 | 384 K + 256 K（**出厂默认**） |
| 011 | 320 K + 320 K |
| 100 | 256 K + 384 K |
| 101、110、111 | 192 K + 448 K |

- 位 3：保留不用（**位号截图小，疑为位 3**）。
- 注意：位 2~0 的改写只能在安全库区未启动的情况下实现。

### 2.3 1024 K 及以上档（用位 [2:0]）

| 编码 | SRAM + ZW |
|---|---|
| 000 | 512 K + 128 K |
| 001 | 448 K + 192 K |
| 010 | 384 K + 256 K（**出厂默认**） |
| 011 | 320 K + 320 K |
| 100 | 256 K + 384 K |
| 101 | 192 K + 448 K |
| 110、111 | 128 K + 512 K |

- 位 3：保留不用。
- 注意：位 2~0 的改写只能在安全库区未启动的情况下实现。

> 三档表里的 "512K 字节" 是 SRAM 侧的**编码档位名**，与 §1 的 96/224 KB 不是同一口径
> （§1 是某具体型号的实配），**别拿 §1 的数去反推 §2 的编码**。

## 3. 闪存存储结构（ch04/004、005）

### 3.1 4032 Kbytes 型号 —— 每扇区 4 K、双 Bank（ch04/004）

| 结构 | 名称 | 地址范围 |
|---|---|---|
| 主存储器 | 片 1（Bank1）2048 KB · 区块 0 · 扇区 0 | 0x0800 0000 – 0x0800 0FFF |
| | 扇区 1 | 0x0800 1000 – 0x0800 1FFF |
| | 扇区 2 | 0x0800 2000 – 0x0800 2FFF |
| | 扇区 15 | 0x0800 F000 – 0x0800 FFFF |
| | 区块 1 · 扇区 16 | 0x0801 0000 – 0x0801 0FFF |
| | 扇区 31 | 0x0801 F000 – 0x0801 FFFF |
| | 区块 31 · 扇区 496 | 0x081F 0000 – 0x081F 0FFF |
| | 扇区 511 | 0x081F F000 – 0x081F FFFF |
| | 片 2（Bank2）1984 KB · 区块 32 · 扇区 512 | 0x0820 0000 – 0x0820 0FFF |
| | 扇区 527 | 0x0820 F000 – 0x0820 FFFF |
| | 区块 62 · 扇区 992 | 0x083E 0000 – 0x083E 0FFF |
| | 扇区 1007 | 0x083E F000 – 0x083E FFFF |
| 信息块 | 启动程序代码区 16 KB | 0x1FFF 0000 – 0x1FFF 3FFF |
| | 用户系统数据区 4 KB | 0x1FFF C000 – 0x1FFF CFFF |

### 3.2 1024 Kbytes 型号 —— 每扇区 2 K、每块 32 扇区（ch04/005）

| 结构 | 名称 | 地址范围 |
|---|---|---|
| 主存储器 | 片 1（Bank1）512 KB · 区块 0 · 扇区 0 | 0x0800 0000 – 0x0800 07FF |
| | 扇区 1 | 0x0800 0800 – 0x0800 0FFF |
| | 扇区 2 | 0x0800 1000 – 0x0800 17FF |
| | 扇区 31 | 0x0800 F800 – 0x0800 FFFF |
| | 区块 1 · 扇区 32 | 0x0801 0000 – 0x0801 07FF |
| | 扇区 63 | 0x0801 F800 – 0x0801 FFFF |
| | 区块 7 · 扇区 224 | 0x0807 0000 – 0x0807 07FF |
| | 扇区 255 | 0x0807 F800 – 0x0807 FFFF |
| | 片 2（Bank2）512 KB · 区块 8 · 扇区 256 | 0x0808 0000 – 0x0808 07FF |
| | 扇区 287 | 0x0808 F800 – 0x0808 FFFF |
| | 区块 15 · 扇区 480 | 0x080F 0000 – 0x080F 07FF |
| | 扇区 511 | 0x080F F800 – 0x080F FFFF |
| 信息块 | 启动程序代码区 16 KB | 0x1FFF 0000 – 0x1FFF 3FFF |
| | 用户系统数据区 512 B | 0x1FFF C000 – 0x1FFF C1FF |

**直接可用的三条**：
1. **扇区大小随容量档不同（4 KB vs 2 KB）** ⇒ 做 IAP/参数存储时擦除粒度必须按型号选，
   写死 `0x1000` 在 1024K 档上会越界擦到隔壁扇区。
2. **双 Bank 分界在 0x0820 0000（4032K 档）** ⇒ 做双备份 OTA 时"两个 bank 各放一份"在这颗上是真的可分区的。
3. **用户系统数据区只有 4 KB（4032K 档）/ 512 B（1024K 档）** ⇒ 校准参数、序列号放这里要按 512 B 预算。

## 4. GPIO 复用功能配置表（ch04/009，6.2.8）

| 配置模式 | IOMC | OM | PULL |
|---|---|---|---|
| 复用推挽无上拉/下拉 | 10 | 0 | 00 或 11 |
| 复用推挽上拉 | 10 | 0 | 01 |
| 复用推挽下拉 | 10 | 0 | 10 |
| 复用开漏无上拉/下拉 | 10 | 1 | 00 或 11 |
| 复用开漏上拉 | 10 | 1 | 01 |
| 复用开漏下拉 | 10 | 1 | 10 |
| 复用输入无上拉/下拉 | 10 | x | 00 或 11 |
| 复用输入上拉 | 10 | x | 01 |
| 复用输入下拉 | 10 | x | 10 |

`ODRV[1:0]` 列在图里为空白，强度实际由 **HDRV** 承担（照抄）：

| HDRV | 含义 |
|---|---|
| 000 | 输出模式，适中电流推动/吸入能力 |
| 001 | 输出模式，较大电流推动/吸入能力 |
| 010 | 输出模式，适中电流推动/吸入能力 |
| 011 | 输出模式，适中电流推动/吸入能力 |
| 1xx | 输出模式，极大电流推动/吸入能力 |

适用条件（照抄）：**仅对复用输出或双向复用功能起作用**。

> ⚠校核：000 / 010 / 011 三档在图里都写作"适中"，而 001 是"较大"、1xx 是"极大" ⇒
> 中间档的措辞几乎肯定有 OCR 串行（正常应是 适中/较大/超强 之类递进）。
> **驱动强度真值必须回 AT32 手册**，别按本表选档。

## 5. IOMUX 引脚复用矩阵（ch04/010、011，6.2.9）

列 = `MUX0…MUX15`，行 = `PA0…PA15`。**图分辨率低，定时器前缀在图里显示为 `TMRR`（疑为 `TMR`）**，
下面只列可辨认的格子，未列出的按"截图不清"处理，**不要当空**。

### 5.1 MUX0–MUX7（ch04/010）

| 脚 | 可辨认的复用 |
|---|---|
| PA0 | MUX1 `TMRR2_CH1/TMRR2_EXT`、MUX2 `TMRR5_CH1`、MUX3 `TMRR_EXT`、MUX4 `I2C2_SCL`、MUX7 `USART2_CTS` |
| PA1 | MUX1 `TMRR2_CH2`、MUX2 `TMRR5_CH2`、MUX4 `I2C2_SDA`、MUX5 `SPI1_MOSI/I2S_SD`、MUX7 `USART2_RTS_DE` |
| PA2 | MUX1 `TMRR2_CH3`、MUX2 `TMRR5_CH3`、MUX3 `TMRR_CH1`、MUX7 `USART2_TX` |
| PA3 | MUX1 `TMRR2_CH4`、MUX2 `TMRR5_CH4`、MUX3 `TMRR_CH2`、MUX4 `I2C2_MCK`、MUX7 `USART2_RX` |
| PA4 | MUX5 `SPI1_CS/I2S1_WS`、MUX6 `SPI2_CS/I2S1_WS`、MUX7 `USART2_CK` |
| PA5 | MUX1 `TMRR2_CH1/TMRR2_EXT`、MUX3 `TMRR6_CH1C`、MUX5 `SPI1_SCK/I2S1_CK` |
| PA6 | MUX1 `TMRR1_BRK`、MUX2 `TMRR3_CH1`、MUX3 `TMRR_BRK`、MUX5 `SPI1_MISO`、MUX6 `I2C2_MCK` |
| PA7 | MUX1 `TMRR1_CH1C`、MUX2 `TMRR3_CH2`、MUX3 `TMRR_CH1C`、MUX5 `SPI1_MOSI/I2S_SD` |
| PA8 | MUX0 `CLKOUT1`、MUX1 `TMRR1_CH1`、MUX4 `I2C3_SCL` |
| PA9 | MUX1 `TMRR1_CH2`、MUX4 `I2C3_SMBA`、MUX5 `SPI2_SCK/I2S2_CK`、MUX7 `USART1_TX` |
| PA10 | MUX1 `TMRR1_CH3`、MUX5 `SPI2_MOSI/I2S2_SD`、MUX6 `I2S4_MCK`、MUX7 `USART1_RX` |
| PA11 | MUX1 `TMRR1_CH4`、MUX4 `I2C2_SCL`、MUX5 `SPI2_CS/I2S2_WS`、MUX6 `SPI4_MISO`、MUX7 `USART1_CTS` |
| PA12 | MUX1 `TMRR1_EXT`、MUX4 `I2C2_SDA`、MUX5 `SPI2_MISO`、MUX7 `USART1_RTS_DE` |
| PA13 | MUX0 `JTMS/SWDCK`、MUX1 `I2C_OUT`、MUX6 `SPI2_MISO` |
| PA14 | MUX0 `JTCK/SWCLK`、MUX5 `SPI2_MOSI/I2S2_SD` |
| PA15 | MUX0 `JTDI`、MUX1 `TMRR2_CH1/TMRR2_EXT`、MUX5 `SPI1_CS/I2S1_WS`、MUX6 `SPI3_CS/I2S3_WS`、MUX7 `USART1_TX` |

### 5.2 MUX8–MUX15（ch04/011）

| 脚 | 可辨认的复用 |
|---|---|
| PA0 | MUX8 `UART4_TX`、MUX11 `EMAC_MII_CRS`、MUX15 `EVENTOUT` |
| PA1 | MUX8 `UART4_RX`、MUX9 `OSPI1_I03`、MUX11 `EMAC_MII_RX_CLK/RMII_REF_CLK`、MUX15 `EVENTOUT` |
| PA2 | MUX10 `SDIO2_CK`、MUX11 `EMAC_MDIO`、MUX14 `XMC_D4`、MUX15 `EVENTOUT` |
| PA3 | MUX9 `OSPI1_I03`、MUX10 `SDIO2_CMD`、MUX11 `EMAC_MII_COL`、MUX14 `XMC_D6`、MUX15 `EVENTOUT` |
| PA4 | MUX8 `USART1_TX`、MUX10 `SDIO2_D4`、MUX11 `SDIO2_D0`、MUX13 `DVP_HSYNC`、MUX14 `XMC_D0`、MUX15 `EVENTOUT` |
| PA5 | MUX8 `USART1_RX`、MUX9 `OSPI1_I02`、MUX10 `SDIO2_D5`、MUX11 `SDIO2_D1`、MUX13 `DVP_PIXCLK`、MUX14 `XMC_D7`、MUX15 `EVENTOUT` |
| PA6 | MUX1 `TMRR3_CH1`、MUX9 `OSPI1_I00`、MUX10 `SDIO2_D2`、MUX11 `SDIO1_CK`、MUX14 `XMC_D8`、MUX15 `EVENTOUT` |
| PA7 | MUX1 `TMRR4_CH1`、MUX9 `OSPI1_I01`、MUX11 `EMAC_MII_RX_DV/RMII_CRS_DV`、MUX12 `XMC_SD_NWE`、MUX13 `SDIO2_D3`、MUX14 `SDIO3_D7`、MUX15 `EVENTOUT` |
| PA8 | MUX8 `USART2_TX`、MUX9 `OTG1_SOF`、MUX11 `SDIO1_D0`、MUX14 `XMC_A4`、MUX15 `EVENTOUT` |
| PA9 | MUX8 `I2C1_SCL`、MUX9 `OTG1_VBUS`、MUX11 `SDIO1_D1`、MUX13 `DVP_D0`、MUX15 `EVENTOUT` |
| PA10 | MUX8 `I2C1_SDA`、MUX9 `OTG1_ID`、MUX13 `DVP_D1`、MUX15 `EVENTOUT` |
| PA11 | MUX8 `USART3_TX`、MUX9 `CAN1_RX`、MUX10 `OTG1_D-`、MUX13 `DVP_D2`、MUX15 `EVENTOUT` |
| PA12 | MUX8 `USART3_RX`、MUX9 `CAN1_TX`、MUX10 `OTG1_D+`、MUX13 `DVP_D3`、MUX15 `EVENTOUT` |
| PA13 | MUX10 `OTG1_OE`、MUX15 `EVENTOUT` |
| PA14 | MUX8 `USART2_TX`、MUX15 `EVENTOUT` |
| PA15 | MUX8 `USART2_RX`、MUX9 `OSPI1_IO1`、MUX10 `OSPI1_IO2`、MUX11 `XMC_NE2/XMC_NRD`、MUX15 `EVENTOUT` |

**可复用的结构性结论**（比单个格子稳）：
- **PA 口每个复用功能都占一个 MUX 槽位（0~15），且 `MUX15` 恒为 `EVENTOUT`** ⇒ 想确认某脚是否已被占用，
  看它有没有被配成非 0 的 MUX 值即可。
- **PA13/PA14 的 MUX0 是 SWD** ⇒ 与 `at32.md` 里"释放调试脚"的问题同源；把 PA13/14 配成别的 MUX 就再也连不上调试器。
- **SPI/I2S 共用同一格**（如 `SPI1_SCK/I2S1_CK`）⇒ AT32 上 SPI 与 I2S 是**同一硬件的两种协议**，
  配了 I2S 就不能再要 SPI，这与 STM32 一致但**位域名不同**（`spi_i2s_*`）。

## 6. AT32_Work_Bench 时钟页取值（ch04/007、008）

| 项 | 图里取值（照抄） |
|---|---|
| 时钟源 | `高速外部时钟 HEXT` 下拉、`低速外部时钟 LEXT = 关闭`、`时钟输出1` 复选框 |
| 源频率 | `hext (4~25MHz) = 8.000000`、`lick = 40`、`lest = 32.768`、`hick = 8` |
| PLL | `CRM_PLLCFG = 0x00042201`；`pll_ns`、**`pll_p /144（51~500）`**、`pll_fr /4` |
| 系统时钟 | `sclk select = 288.000 MHz`、`sclk(4, 288MHz) = 288.000` |
| AHB | `ahbdiv /1` |
| USB | `usbdiv /6`（hick to usb） |
| SysTick | `systick (/8) = 36.000` |
| APB1 | `apb1div /2 (*2)` → `apb1 peripheral = 144.000`（**144 MHz max**）、`apb1 tmr = 288.000` |
| APB2 | `apb2div /2 (*2)` → `apb2 peripheral = 144.000`、`apb2 tmr = 288.000` |
| 其他 | `adc/dma/xmc/gpio/bp/spi1/asc = 288.000` |
| **红字限制（照抄）** | `Usage limited: Temperature range -40~85 degree, VDD must over 3.0V.` |

⇒ **跑 288 MHz 是有条件的**：温度 −40~85℃ 且 **VDD > 3.0 V** ⇒ 供电只有 2.7~3.0V 的电池产品不能按 288M 设计。
⇒ APB 外设 144 MHz 上限、定时器自动 ×2 到 288 MHz ⇒ 与 GD32 的"显式选 x1/x2/x4"不同，
**AT32 的 `(*2)` 是工具自动算的**，移植时定时器分频要按 `apb2 tmr` 而不是 `apb2 peripheral` 算。

## 7. SPI 配置项全清单（ch04/012、013、014、015、016~020）

### 7.1 下拉选项（照抄，文字层完全没有）

**`配置SPI1模式`（ch04/012，共 11 项）**：`关闭`、`主机全双工模式`、`从机全双工模式`、
`主机半双工接收模式`、`主机半双工发送模式`、`从机半双工接收模式`、`从机半双工发送模式`、
`主机全双工仅接收模式`、`主机全双工仅发送模式`、`从机全双工仅接收模式`、`从机全双工仅发送模式`。

**`配置硬件CS信号`（ch04/013，3 项）**：`关闭`、`硬件CS输入信号`、`硬件CS输出信号`。

### 7.2 CPOL/CPHA 两块波形图（ch04/014、015）

两图共用波形：`CS` 拉低选中、`SCK` 脉冲、`Sampling` 采样箭头落在**第一个边沿**；
`MISO/MOSI` 位序 `MSB | DATA | … | DATA | LSB`。

| 图 | 面板取值（照抄） |
|---|---|
| 014 | 接口协议 `Motorola模式`、帧位个数 `8位`、最先传输位 `MSB先行传输`、时钟频率分频系数 `4`、时钟频率(0-50 MHz) `36 MHz`、**时钟极性 `低电平`**、时钟相位 `第一个边沿进行数据捕获` |
| 015 | 同上，**时钟极性 `高电平`** |

面板 Tab 条：`参数设置 | GPIO设置 | 中断设置 | NVIC设置 | DMA设置 | EDMA设置`
⇒ **AT32 的 DMA 与 EDMA 是两个独立配置页**（与 §8 的 `DMA1 CH0~7` + `EDMA` 对应）。

### 7.3 SPI1 驱动 LCD（不走 DMA）的完整勾选态（ch04/016~020）

| 页 | 项 | 状态 |
|---|---|---|
| 模式与 CS | 模式 | `Full Duplex Master` |
| | 硬件 CS | **勾选**（`NSS Output` 使能） |
| | `NSS Pulse Mode` / `Input Only` / `2-Bit/4-Bit Mode` | 均未勾 |
| 基本参数 | 帧格式 | `16 Bits` |
| | 从选 | `Slave Select Hardware` |
| | 首字节 | `MSB First` |
| 时钟参数 | `CPOL` / `CPHA` | `Low` / `1st Edge` ⇒ **SPI 模式 0** |
| | 分频 | `/256`（可选 `/2 … /256`） |
| 高级参数 | `CRC Calculation` / `DMA Mode` | 均未勾 |
| SWD | `SWD Pins` | **未勾**（勾上会占用 SWD 脚） |

⇒ 84 MHz APB2 下 `/256` ≈ 328 kbit/s，是"先点亮再看"的保守起步值；
⇒ **`SWD Pins` 这一项就是"配完 SPI 调试器连不上"的开关**，与 §5 的 PA13/PA14 结论一致。

## 8. 表 9-3 DMA1 / DMA2 请求弹性映射（ch04/022）—— 本库唯一副本

**适用前提（照抄）**：`仅适用于 AT32F435 系列`。请求源编号 **1~123**，即 `dmamux_init` 的 `request_id`。

### 8.1 外部中断与存储器类（1~12）

| 编号 | 请求源 | 编号 | 请求源 |
|---|---|---|---|
| 1 | 内存到内存 | 7 | DMARDMA1 |
| 2 | EXINT_LINE0 | 8 | EADC1 |
| 3 | EXINT_LINE1 | 9 | ETMR1 |
| 4 | EXINT_LINE2 | 10 | USBFS1 |
| 5 | EXINT_LINE…（**截图不清**） | 11 | USBFS2 |
| 6 | DMAWRINT | 12 | SDIO1 |

### 8.2 定时器类（13~56）

| 定时器 | 请求源 | 编号 |
|---|---|---|
| TM1 | CH1 / CH2 / CH3 / CH4 | 13 / 14 / 15 / 16 |
| TM2 | CH1 / CH2 / CH3 / CH4 | 17 / 18 / 19 / 20 |
| TM3 | CH1 / CH2 / CH3 / CH4 | 21 / 22 / 23 / 24 |
| TM4 | TMR4_UP | 25 |
| TM5 | CH1 / CH2 / CH3 / CH4 | 26 / 27 / 28 / 29 |
| TM6 | TMR6_DACINT0 / TMR6_UP | 30 / 31 |
| TM7 | TMR7_ADCINT0 / TMR7_UP | 32 / 33 |
| TM8 | CH1 / CH2 / CH3 / CH4 | 34 / 35 / 36 / 37 |
| TM9 | CH1 / CH2 / UP / BKIN | 38 / 39 / 40 / 41 |
| TM10 | CH1 / CH2 / UP / BKIN | 42 / 43 / 44 / 45 |
| TM11 | CH1 / CH2 / UP / BKIN | 46 / 47 / 48 / 49 |
| TM12 | CH1 / CH2 / UP / BKIN | 50 / 51 / 52 / 53 |
| TM13 | CH1 / CH2 / UP / BKIN | 54 / 55（**UP/BKIN 编号截图不清**） |
| TM14 | TMR14_UP | 56 |

### 8.3 串口类（57~86）

| 外设 | 请求源（**注意列序不同**） | 编号 |
|---|---|---|
| USART1 | CTS / TX / RX / RTU | 57 / 58 / 59 / 60 |
| USART2 | CTS / TX / RX / RTU | 61 / 62 / 63 / 64 |
| USART3 | **TX / RX / CTS** / RTU | 65 / 66 / 67 / 68 |
| UART4 | TX / RX / RTU | 69 / 70 / 71 |
| UART5 | TX / RX / RTU | 72 / 73 / 74 |
| USART6 | CTS / TX / RX / RTU | 75 / 76 / 77 / 78 |
| UART7 | **TX / RX / CTS** / RTU | 79 / 80 / 81 / 82 |
| UART8 | **TX / RX / CTS** / RTU | 83 / 84 / 85 / 86 |

⇒ **USART3/UART7/UART8 的列序与其余不同** ⇒ 编号按行内位置对应，**不能按"CTS 总是第一个"推**。

### 8.4 SPI / I2C / 转换器 / 其他（87~123）

| 外设 | 请求源 | 编号 |
|---|---|---|
| SPI1 | TX / RX | 87 / 88 |
| SPI2 | TX / RX | 89 / 90 |
| SPI3 / SPI4 | TX / RX | 91 / 92 |
| SPI5 / SPI6 | TX / RX | 93 / 94 |
| I2C1 | TX / RX | 95 / 96 |
| I2C2 | TX / RX | 97 / 98 |
| I2C3 | TX / RX | 99 / 100 |
| I2C4 | TX / RX | 101 / 102 |
| SDIO1 | SDIO1 | 103 |
| CAN1 | TX_FIFO0 / RX_FIFO0 / RX_FIFO1 | 104 / 105 / 106 |
| CAN2 | TX_FIFO0 / RX_FIFO0 / RX_FIFO1 | 107 / 108 / 109 |
| CAN3 | TX_FIFO0 / RX_FIFO0 / RX_FIFO1 | 110 / 111 / 112 |
| ADC1 / ADC2 / ADC3 / ADC4 | 数据 | 113 / 114 / 115 / 116 |
| DAC1 | 请求1 / 请求2 | 117 / 118 |
| DAC2 | 请求1 / 请求2 | 119 / 120 |
| ACMP | 输出 | 121 |
| I2S1 | TX / RX | 122 / 123 |
| I2S2 ~ I2S6 | TX / RX | **截图不清（编号未列出）** |

> ⚠校核（**编号冲突，用前必核**）：
> ① `SDIO1` 同时是 **12** 和 **103**；② `SPI3/SPI4` 共用 91/92、`SPI5/SPI6` 共用 93/94；
> ③ 1~12 区间左列部分行对不齐。⇒ 这三处都是**截图并排两列造成的歧义**，
> **不能照本表直接填 `request_id`**，以工具生成的 `dmamux_init()` 实参或手册为准。

## 9. 表 9-4 DMAMUX 触发输入 / 同步输入（ch04/023）

**只承认前 23 项**（编号 0~23，图内清晰）：

| 信号 | 编号 | 信号 | 编号 |
|---|---|---|---|
| EXINT_LINE0 | 0 | EXINT_LINE12 | 12 |
| EXINT_LINE1 | 1 | EXINT_LINE13 | 13 |
| EXINT_LINE2 | 2 | EXINT_LINE14 | 14 |
| EXINT_LINE3 | 3 | EXINT_LINE15 | 15 |
| EXINT_LINE4 | 4 | DMARDMA1 | 16 |
| EXINT_LINE5 | 5 | DMAWRINT | 17 |
| EXINT_LINE6 | 6 | DMARDMA2 | 18 |
| EXINT_LINE7 | 7 | DMAWRINT2 | 19 |
| EXINT_LINE8 | 8 | TMR6_TRGO | 20 |
| EXINT_LINE9 | 9 | TMR2_TRGO | 21 |
| EXINT_LINE10 | 10 | RTC_ALARN | 22 |
| EXINT_LINE11 | 11 | RTC_WAKEUP | 23 |

> ⚠校核（**整段不采信**）：从编号 24 起图里是 `IISDO/IISDI … IIS140DO/IIS140DI` 连续 278 条
> （编号一路到 301）⇒ AT32F435 不可能有 140 个 I2S，**极可能是截图"信号列/编号列"串行产生的假数据**。
> 本库**只登记"此处有 24~301 段但内容不可信"**，禁止用于配置。

## 10. DMA 配置页实测取值（ch04/024~028）

### 10.1 基本配置（ch04/024）

| 项 | 可选值 | 图里选择 |
|---|---|---|
| 方向 | `Peripheral to Memory` / `Memory to Peripheral` / `Memory to Memory` | `Peripheral to Memory` |
| 外设数据宽度 | `Byte` / `Half Word` / `Word` | **`Half Word`** |
| 存储器数据宽度 | `Byte` / `Half Word` / `Word` | **`Half Word`** |
| 外设地址递增 | `Enable` / `Disable` | `Disable` |
| 存储器地址递增 | `Enable` / `Disable` | `Enable` |
| 循环模式 | `Enable` / `Disable` | `Disable` |
| 优先级 | `Very High` / `High` / `Medium` / `Low` | **`Very High`** |
| 缓冲大小 | 0~65535 | `0x0000FFFF` |

### 10.2 中断设置（ch04/025）

四类中断**全部勾选**：`Transfer Error Interrupt`、`Half-Transfer Interrupt`、
`Buffer Complete Interrupt`、`Block Transfer Complete Interrupt`。

### 10.3 DMA 请求参数（ch04/026）

| 项 | 可选值 | 图里选择 |
|---|---|---|
| 触发使能 | `Enable` / `Disable` | `Enable` |
| 请求重映射 | `Enable` / `Disable` | `Disable` |
| 同步类型 | `DMAMUX` / `EDMA` | `DMAMUX` |
| 同步源 | `DMAMUX` / `EDMA` | `DMAMUX` |
| 请求极性 | `Active Low` / `Active High` / `Rising Edge` / `Falling Edge` | `Active Low` |
| 请求生成模式 | `Single Short Mode` / `Single Long Mode` / `Repeat Short Mode` / `Repeat Long Mode` | `Single Short Mode` |
| DMA 模式 | `Normal Mode` / `Circular Mode` / `Double Normal Mode` / `Double Circular Mode` | `Normal Mode` |
| 流控 | `Enable` / `Disable` | `Enable` |
| 水位 | `1/4` / `1/2` / `3/4` / `Full` | `1/4` |
| 固定突发 | `Fixed Burst 16 Beat` 复选框 | **未勾** |

### 10.4 SPI1 + DMA 驱动 LCD 的实例（ch04/027、028）

| 项 | 取值 |
|---|---|
| DMA 通道 | `DMA1 Channel1` |
| 方向 | **`Memory to Peripheral`**（发送） |
| 外设请求 | **`SPI1_TX`** |
| 请求编号 | **`Request Id = 88`** |
| 数据宽度 | 外设 `Half Word` / 存储器 `Half Word` |
| 递增 | 外设 `Disable` / 存储器 `Enable` |
| 循环 / 优先级 / 缓冲 | `Disable` / `Very High` / `0x0000FFFF` |
| 中断 | 四类全勾 |
| 请求参数 | 与 §10.3 完全一致（`Trigger Enable`、`Remapping Disable`、`Synchronization Type/Source = DMAMUX`、`Active Low`、`Single Short Mode`、`Normal Mode`、`Flow Control Enable`、`Watermark 1/4`） |

> ⚠校核（**编号对不上**）：表 9-3 里 `SPI1_TX = 87`、`SPI1_RX = 88`，
> 而 WorkBench 的 `SPI1_TX` 填出的 `Request Id` 是 **88** ⇒ 两者矛盾（截图列位歧义或工具编号体系不同）。
> **以编译产物里的 `dmamux_init(...)` 实参为准**，别照文档手填。
> 另：该下拉框里还出现 `USART1_TX` 等异常选项（疑截图串位），未采信。

## 11. DMA 中断向量与标志表（ch04/021）

| 中断向量 | 挂的标志位 | 服务的通道 |
|---|---|---|
| `CH0INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel0、DMA2 Channel0 |
| `CH1INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel1、DMA2 Channel1 |
| `CH2INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel2、DMA2 Channel2 |
| `CH3INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel3、DMA2 Channel3 |
| `CH4INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel4、DMA2 Channel4 |
| `CH5INT` | `HTIF` / `TIF` / `ERIF` / `GIF` | DMA1 Channel5、DMA2 Channel5 |
| `CH6INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel6、DMA2 Channel6 |
| `CH7INT` | `HTIF` / `TIF` / `TERIF` / `GIF` | DMA1 Channel7、DMA2 Channel7 |

⇒ **一个向量覆盖 DMA1 与 DMA2 的同号通道** ⇒ ISR 里必须自己判 `dma_flag_status` 分清是哪个控制器的中断，
否则两个外设会互相吞标志。
> ⚠校核：CH5INT 行图中写 `ERIF`（其余行是 `TERIF`），疑笔误/OCR。

## 12. Keil DFP 包清单（ch04/001、002）

| Pack | 版本（日期） | 状态 |
|---|---|---|
| `Keil.AT32F4xx_DFP` | 1.3.7（图 001 标 2015-02-19；图 002 标 2021-05-19） | 已安装（Action = Remove） |
| `Keil.AT32F4xx_DFP` | 1.3.6 2021-03-18、1.3.5 2021-01-18、1.3.4 2020-10-16、1.3.3 2020-09-15、1.3.2 2020-08-15、1.3.1 2020-02-23、1.3.0 2019-12-26 | Offline |
| `ArteryTek.AT32F435_437_DFP` | **2.1.1（2022-08-23）**、2.0.6（2022-02-11） | Offline（待装） |
| Device 页 | 厂商 **ArteryTek**；Boards 页 `AT32F4xx Series 104 Devices`、`F302 Series 1 Device` | — |

> ⚠校核：`Keil.AT32F4xx_DFP 1.3.7` 的日期在两图里分别是 **2015-02-19** 与 **2021-05-19** ⇒ 至少一处 OCR/显示差异。
> **两包是否互斥、能否共存，图里没有任何提示** —— 小标题"紧接着安装 2.1.1"只说明安装顺序，
> 网传"旧包必须卸载否则识别不到 F435/437"**属推断，未验证**，不要当结论用。
