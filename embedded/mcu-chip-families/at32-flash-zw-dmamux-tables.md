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

### 7.3 SPI1 驱动 LCD（不走 DMA）的完整勾选态（ch04/016~020，**界面是中文**）

| 页 | 项 | 图里取值 |
|---|---|---|
| 配置模式和硬件CS（016） | 模式 | `主机全双工模式` |
| | 硬件 CS 信号 | **`关闭`** |
| 配置基本参数（017） | 接口协议 | `Motorola模式` |
| | 帧位个数 | **`8位`** |
| | 最先传输位 | `MSB先传输` |
| 配置时钟参数（018） | 时钟频率分频系数 | **`8`** |
| | 时钟频率(0-50 MHz) | **`18 MHz`**（灰色只读，由分频系数自动算出） |
| | 时钟极性 / 时钟相位 | `低电平` / `第一个边沿进行数据捕获` ⇒ **SPI 模式 0** |
| 高级参数（019） | CRC 校验 | `关闭` |
| | CS 信号类型 | **`软件CS`**（与 016"硬件 CS 关闭"呼应） |
| SWD调试模式（020） | 调试接口 | `SWD` |
| | SWO | **未勾选** |

⇒ **`时钟频率` 框只读、由分频系数自动算** ⇒ 想改速率只能改分频系数；在代码里另设波特率会在下次生成时被覆盖。
⇒ 该实例是 **8 位帧 + 软件 CS** ⇒ 驱动 LCD 时 **DC(命令/数据) 脚必须自己用 GPIO 控制**，不是硬件 NSS。

## 8. 表 9-3 DMA1 / DMA2 请求弹性映射（ch04/022）—— 本库唯一副本

**表头结构（照抄）**：`DMA1MUX 请求` + **三组** `DMAMUX 请求`，每组含"编号 + 来源"两子列，编号到 **128**。
⇒ **关键读法**：同一外设会出现**两个不同编号**（如 `SPI1_RX` 在 10 和 106），
因为**DMA1 用 DMA1MUX 编号、DMA2/其余用 DMAMUX 编号，是两套表并排**，不是原文矛盾。
`reserved` 表示该编号未分配请求源，**不要拿来用**。

| # | DMA1MUX 来源 | # | 来源 | # | 来源 | # | 来源 |
|---|---|---|---|---|---|---|---|
| 1 | DMA1_MUXREQ01 | 33 | USART1_TX | 65 | TIMR3_CH4 | 97 | reserved |
| 2 | DMA1_MUXREQ02 | 34 | reserved | 66 | TIMR3_TRIG | 98 | reserved |
| 3 | DMA1_MUXREQ03 | 35 | reserved | 67 | TIMR3_CH1 | 99 | reserved |
| 4 | DMA1_MUXREQ04 | 36 | ADC2 | 68 | TIMR3_CH2 | 100 | reserved |
| 5 | ADC1 | 37 | reserved | 69 | TIMR3_CH3 | 101 | reserved |
| 6 | DAC1 | 38 | reserved | 70 | TIMR3_CH4 | 102 | reserved |
| 7 | reserved | 39 | SDIO1 | 71 | TIMR4_OVERFLOW | 103 | SDIO2 |
| 8 | TIMR2_OVERFLOW | 40 | QSPI1 | 72 | TIMR5_CH1 | 104 | QSPI2 |
| 9 | TIMR7_OVERFLOW | 41 | DAC2 | 73 | TIMR5_CH2 | 105 | DVP |
| 10 | **SPI1_RX** | 42 | TIMR1_CH1 | 74 | TIMR5_CH3 | 106 | **SPI1_RX** |
| 11 | **SPI1_TX** | 43 | TIMR1_CH2 | 75 | TIMR5_CH4 | 107 | **SPI1_TX** |
| 12 | SPI2_RX | 44 | TIMR1_CH3 | 76 | TIMR5_OVERFLOW | 108 | SPI2_RX |
| 13 | SPI2_TX | 45 | TIMR1_CH4 | 77 | SPI3_TX | 109 | SPI3_TX |
| 14 | SPI3_RX | 46 | TIMR1_OVERFLOW | 78 | reserved | 110 | I2S2_EXT_RX |
| 15 | SPI3_TX | 47 | TIMR1_TRIG | 79 | reserved | 111 | I2S2_EXT_TX |
| 16 | I2C1_RX | 48 | TIMR1_HALL | 80 | I2S3_EXT_RX | 112 | I2S3_EXT_RX |
| 17 | I2C1_TX | 49 | TIMR8_CH1 | 81 | I2S3_EXT_TX | 113 | I2S3_EXT_TX |
| 18 | I2C2_RX | 50 | TIMR8_CH2 | 82 | reserved | 114 | UART6_RX |
| 19 | I2C2_TX | 51 | TIMR8_CH3 | 83 | reserved | 115 | UART6_TX |
| 20 | I2C3_RX | 52 | TIMR8_CH4 | 84 | reserved | 116 | UART7_RX |
| 21 | I2C3_TX | 53 | TIMR8_OVERFLOW | 85 | UART8_TX | 117 | UART7_TX |
| 22 | reserved | 54 | TIMR8_TRIG | 86 | TIMR20_CH1 | 118 | UART8_RX |
| 23 | reserved | 55 | TIMR8_HALL | 87 | TIMR20_CH2 | 119 | UART8_TX |
| 24 | UART1_RX | 56 | TIMR2_CH1 | 88 | TIMR20_CH3 | 120 | reserved |
| 25 | UART1_TX | 57 | TIMR2_CH2 | 89 | TIMR20_CH4 | 121 | reserved |
| 26 | UART2_RX | 58 | TIMR2_CH3 | 90 | TIMR20_OVERFLOW | 122 | reserved |
| 27 | UART2_TX | 59 | TIMR2_CH4 | 91 | reserved | 123 | reserved |
| 28 | UART3_RX | 60 | TIMR2_OVERFLOW | 92 | reserved | 124 | reserved |
| 29 | UART3_TX | 61 | TIMR3_CH1 | 93 | TIMR20_TRIG | 125 | TIMR2_TRIG |
| 30 | UART4_RX | 62 | TIMR3_CH2 | 94 | TIMR20_HALL | 126 | TIMR4_TRIG |
| 31 | UART4_TX | 63 | TIMR3_CH3 | 95 | reserved | 127 | TIMR4_TRIG |
| 32 | UART5_RX | 64 | TIMR3_CH4 | 96 | （截图不清） | 128 | （截图不清） |

**从这张表能直接得到的结论**：
1. **`SPI1_TX` 有两个编号：DMA1 侧 11、DMAMUX 侧 107** ⇒ 填 `request_id` 前**必须先确定用的是哪个 DMA 控制器**，
   这是 AT32 DMA 配置最常见的"配了不动作"原因。
2. `TIMR4_TRIG` 在 126 与 127 **重复出现**、`SPI3_TX` 出现在 15/77/109 三处 ⇒ 截图列位仍有歧义，
   **抄编号时以"控制器 + 该控制器对应的列"为准**（ERRATA H2）。
3. 1~4 是 `DMA1_MUXREQ01~04` 占位 ⇒ **DMA1 的前 4 个 MUX 槽是留给"自定义映射"的**，不是外设请求。
4. 出现 `QSPI1/QSPI2`、`DVP`、`SDIO2`、`TIMR20`、`UART6/7/8` ⇒ 这些是 **AT32F435 相对 STM32F4 多出来的资源**，
   移植时容易漏配。

## 9. 表 9-4 DMAMUX EXINT LINE 触发输入 / 同步输入（ch04/023）

| 编号 | 来源 | 编号 | 来源 |
|---|---|---|---|
| 0 | `exit_gpio[0]` | 16 | `DMA_MUXext1` |
| 1 | `exit_gpio[1]` | 17 | `DMA_MUXext2` |
| 2 | `exit_gpio[2]` | 18 | `DMA_MUXext3` |
| 3 | `exit_gpio[3]` | 19 | `DMA_MUXext4` |
| 4 | `exit_gpio[4]` | 20 | `DMA_MUXext5` |
| 5 | `exit_gpio[5]` | 21 | `DMA_MUXext6` |
| 6 | `exit_gpio[6]` | 22 | `DMA_MUXext7` |
| 7 | `exit_gpio[7]` | 23 | reserved |
| 8 | `exit_gpio[8]` | 24 | reserved |
| 9 | `exit_gpio[9]` | 25 | reserved |
| 10 | `exit_gpio[10]` | 26 | reserved |
| 11 | `exit_gpio[11]` | 27 | reserved |
| 12 | `exit_gpio[12]` | 28 | reserved |
| 13 | `exit_gpio[13]` | 29 | reserved |
| 14 | `exit_gpio[14]` | 30 | reserved |
| 15 | `exit_gpio[15]` | 31 | reserved |

⇒ **触发/同步输入只有两类可用**：16 路外部中断线（`exit_gpio[0..15]`）与 7 路 `DMA_MUXext1~7`，编号 23~31 全保留。
⇒ 想做"外部信号触发一次 DMA 搬运"就用 `exit_gpio[n]`；`DMA_MUXext` 是**软触发线**。

## 10. DMA 配置页实测取值（ch04/024~028，SPI1 + DMA 驱动 LCD）

**选项卡行（ch04/024 照抄）**：`参数设置` | `GPIO设置` | `中断设置` | `NVIC设置` | **`DMA设置`（当前选中）** | `EDMA设置`
⇒ **DMA 与 EDMA 是两个独立页**（两套资源），配 SPI1_TX 用的是 DMA 页。

| 页 | 项 | 图里取值 |
|---|---|---|
| DMA设置（024、027） | DMA 请求 | `SPI1_TX` |
| | 通道 | **`DMA1通道1`** |
| | 传输方向 | `内存到外设` |
| | 优先级 | **`中`** |
| 中断设置（025、028） | 传输完成 (FDT) | **`开启`** |
| | 半传输完成 (HDT) | `关闭` |
| | 传输错误 (DTERR) | `关闭` |
| | 同步溢出 (SYNCOVF) | `关闭`（**灰色不可编辑**） |
| DMA请求参数（026、028） | 模式 | `普通` |
| | 外设地址递增 | **`关闭`** |
| | 内存地址递增 | **`开启`** |
| | 外设数据宽度 | **`字节`** |
| | 内存数据宽度 | **`字节`** |

⇒ **发送 SPI 的标准组合**：内存到外设 + 外设不递增 + 内存递增 + 字节宽度 + 只开 FDT。
⇒ 与 §7.3 的"8 位帧"一致 ⇒ **AT32 的 SPI 走 8 位时 DMA 两侧宽度都填"字节"**；
若把数据宽度配成半字节/字而 SPI 是 8 位，表现为"发一半丢一半"。
⇒ `SYNCOVF` 灰色 ⇒ **该通道不支持同步溢出中断**，别在代码里等这个标志。

## 11. DMA 中断事件 / 标志 / 清除 / 使能对照（ch04/021）

| 中断事件 | 事件标志位 | 清除控制位 | 使能控制位 |
|---|---|---|---|
| 半传输 | `HDTF` | `HDTFC` | `HDTIEN` |
| 传输完成 | `FDTF` | `FDTFC` | `FDTIEN` |
| 传输错误 | `DTERRF` | `DTERRFC` | `DTERRIEN` |

⇒ **三组"标志 / 清除 / 使能"名字一一对应**（后缀 `F` / `FC` / `IEN`）⇒
ISR 里**写 `xxFC` 清标志**，不是写 0 清 `xxF`；漏清就是"进一次中断再也不进"。
⇒ 表里**没有"块传输完成"一类的事件**（AT32 的 DMA 只有半传输/传输完成/传输错误三种）。

## 12. Keil DFP 包清单（ch04/001、002）

| Pack | 版本（日期） | 状态 |
|---|---|---|
| `Keil.AT32F4xx_DFP` | 1.3.7（图 001 标 2015-02-19；图 002 标 2021-05-19） | 已安装（Action = Remove） |
| `Keil.AT32F4xx_DFP` | 1.3.6 2021-03-18、1.3.5 2021-01-18、1.3.4 2020-10-16、1.3.3 2020-09-15、1.3.2 2020-08-15、1.3.1 2020-02-23、1.3.0 2019-12-26 | Offline |
| `ArteryTek.AT32F435_437_DFP` | **2.1.1（2022-08-23）**、2.0.6（2022-02-11） | Offline（待装） |
| Device 页 | 厂商 **ArteryTek**；Boards 页 `AT32F4xx Series 104 Devices`、`F302 Series 1 Device` | — |

> ⚠校核：`Keil.AT32F4xx_DFP 1.3.7` 的日期在两图里分别是 **2015-02-19** 与 **2021-05-19** ⇒ 至少一处显示/OCR 差异。
> **两包是否互斥、能否共存，图里没有任何提示** —— 小标题"紧接着安装 2.1.1"只说明安装顺序，
> 网传"旧包必须卸载否则识别不到 F435/437"**属推断，未验证**，不要当结论用。
