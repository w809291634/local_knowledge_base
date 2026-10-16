# mcu-chip-families/ — 各家芯片与 STM32 的差异、移植踩坑

> 来源：《单片机外设和调试基础知识.docx》各芯片族章节精读，2026-10-16。
> 目的只有一个：**换芯片/换家时，先在这里查"哪一点会咬人"**，而不是等编译过不了再猜。
> `⚠校核` 见 `embedded/mcu-peripherals/ERRATA-单片机外设和调试基础知识.md`。
> 逐章"哪些只到骨架、哪些在原图里没提取"→ `embedded/mcu-peripherals/COVERAGE-覆盖度与缺口.md`。

| 文件 | 内容 |
|---|---|
| `gd32.md` | GD32F4xx 时钟/库命名/AF 表差异，**用 STM32 库直换的 4 个具体不兼容点**；§5 收**完整时钟树截图数据**（TIMER0 在 APB2、ADC 双分频链、PH0/PH1=HXTAL、MDMA+EDMA、QEI0） |
| `at32.md` | AT32F435/437 与 F403A：时钟与 PLL 命名、库函数名、**ZW/NZW 零等待分区**、XMC、外设映射；§7 是截图层结论汇总 |
| `at32-flash-zw-dmamux-tables.md` | **手册表格唯一副本（原文只有图）**：ZW↔SRAM 352KB 分配、表 5-6 `EOPB` 三档编码、闪存结构 4032K/1024K、6.2.8 复用+HDRV、6.2.9 IOMUX MUX0~15、WorkBench 288MHz 取值与供电限制、SPI 11 种模式、**表 9-3 DMAMUX 请求映射 1~123**、表 9-4 触发源、DMA 配置页与中断向量 |
| `py32-ht32-holtek.md` | PY32（普冉）PC0=NRST 的选项字节坑；"HT32"章实为 Holtek 8 位 BH67F2472 血糖仪方案 |
| `stc-c51-and-ch32-wch.md` | STC8H 全系要点（时钟/XFR/定时器/串口/GPIO/ADC/PWM/ISP 下载/C51 语言层）+ 沁恒 CH57x/CH58x/CH32V（RISC-V PFIC、Flash 映射、BLE SDK） |
| `cc2530-cc2538-cc2640.md` | CC2530 外设实操（时钟切换必须连 TICKSPD 一起清、T1/PWM、printf、内部 flash）、CC2538 救砖、CC2640 环境与坑 |
| `zigbee-zstack-osal.md` | **Z-Stack OSAL 运行机制**（任务轮询/事件位/消息队列/软定时器）+ 端点/地址/NV/串口帧/工程适配 |
| `recipes-code-skeletons.md` | **各家代码配方**：GD32 改晶振/HSE 超时/`SPI1_SetSpeed` 为何删；AT32 `wk_spi1_init`+`dmamux_init` 三件套+288MHz 填法+`nvic_irq_enable`；STC `EAXSFR`+T1 波特率(含 1T 公式)+UART2 中断与轮询死锁+定时器 1T；CH `GetSysClock`+BLE main 骨架+**ISR 必须带 `WCH-Interrupt-fast`**；Z-Stack 描述符注册/`SAPI_ProcessEvent` 全文/`AF_DataRequest`/NV/MT |

## 跨族的共性结论（比单条更值钱）

1. **"兼容 STM32"意味着头文件与函数名能改，不意味着行为能改。**
   GD32/AT32 的寄存器位域、AF 编号、时钟默认值都与 STM32 有差异，直换 STM32 库的典型症状是
   **外设能初始化但时序/速率/引脚功能不对**（不是编译错误）。
2. **各家命名映射表要背第一列**：`RCC↔RCU(GD32)/CRM(AT32)`、`TIM↔TIMER(GD32)/TMR(AT32)`、
   `HSE↔HXTAL`、`HSI↔IRC16M/HICK`、`EXTI↔EXINT`、`AFRL/AFRH↔AFSEL0/1↔IOMUX/MUXL/MUXH`。
3. **晶振宏是"改了没生效"的头号来源**：`HSE_VALUE`(STM32) / `HXTAL_VALUE`(GD32，默认 25M) /
   `HEXT_VALUE`(AT32) 必须与实晶振一致，且工程宏也要同步定义。
4. **零等待区/Flash 加速器的存在会改变你的代码布局决策**：STM32 的 ART/预取、AT32 的 ZW/NZW（NZW 只有约 0.4 倍速）、
   GD32 的"零等待"厂商口径 `⚠校核C`。跑不满主频先查这个，不是查算法。
5. **8 位机（STC/Holtek/CC2530）与 32 位机的关键差异不是算力，而是**：
   内存模型与指针宽度（C51 3 字节通用指针、Holtek 无统一存储模型）、
   **定时器位宽与时基随 SYSclk 变**、以及"每循环几个时钟"依赖编译器 ⇒ 微秒级延时必须实测。
6. **调试器与烧录通道的绑定关系**：Holtek 用 e-Link/ICP(PA0/PA2)、STC 用串口 + 自动握手(P3.0/P3.1 + P3.2 判据)、
   WCH 用串口 PA8/PA9 + PB22 BOOT 或 USB PB10/PB11、TI 用 Debug Adapter(XDS110/CC-Debugger)。
   **换芯片时先把烧录路径确认好**，否则连"能不能进去"都是问题。
