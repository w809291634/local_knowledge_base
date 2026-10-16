# 勘误与校核清单：《单片机外设和调试基础知识.docx》

> 精读时对原文做的技术校核结果。**用途**：① 引用该文档前先查这里，避免把错的值抄进代码；
> ② 修文档时按编号逐条更正；③ 长期看，这是"哪些知识点我自己一直记混"的镜子。
> 判定分三档：**高**（算术/同文自证/通用规格可直接推翻）、**中**（与主流手册口径不符但无原文可查证）、
> **无法判断**（原文对应正文是空表或缺失，没有依据）。**"无法判断"不等于错，只是别拿来当依据。**
> 未列出的条目 = 校核通过或未逐项核查，不代表已验证。

## A. 算术与单位错（高置信，可直接改）

| 位置 | 原文 | 问题 |
|---|---|---|
| 通信速率表 | "超高速模式 5Mbit/s，即 5M/8 = 525KB/s" | 5M/8 = **625KB/s**；同表其余行都按 /8 换算，唯此行不自洽 |
| 通信速率表 | "SPI 约有 50Mbps，即约 5.9MB/s" | 50/8 = 6.25MB/s |
| 通信速率表 | "CAN 1Mbps，即约 128KB/s" | 1M/8 = 125KB/s（且 CAN 还有帧开销，实际更低） |
| 波特率节 | "115.2kps = 0.115.2Mbps" | 数字写法错，应 0.1152Mbps |
| 停止位 | "停止位（1,15,2位）" | 应为 1、**1.5**、2 |
| RS485 | "RS485 最大**无线**传输距离为 1200 米" | 应为有线；同段本身在讲线缆与屏蔽 |
| 中断耗时 | "6μs → 9μs"却写"又增加了 2us" | 差值是 3μs |
| 采样率 | "196Khz" | 应为 192kHz（同节常量都是 192000） |
| DMA | "一个字认为是 32 字节，半字为 16 字节" | 应为 32/16 **位**（同文另一处写对了） |
| 调试章节 | "R13(SP)=0x20040000，栈起始 0x2004b310 → SP 比栈底低约 13KB" | 0xB310−0x0000 差 **44.8KB**；同章另一处减法算对了，独此错 |
| 调试章节 | "堆指针初始位于 0x2004b710" | 那是 **SP**，非堆；map 里 HEAP 另有其址(0x2004b110/512B) |
| us 换算 | `us = ms*1000 + (LOAD-ticks)*1000/SystemCoreClock` | 量纲错，应为 ×**1000000**/SystemCoreClock；168MHz 下按原式 168 个计数算出 0.001us |
| 笔误 | `STK_CALRB`、"重定向 fputs()"、"30PFS"、"杂类指示点"、"±2%~±2%"、"cmbacktrace" | 分别应为 STK_CALIB、fputc、30FPS、乱码、±2%、`cm_backtrace` |
| 断句 | "ST-Link V2.J16.S4…这个版本的固件是。" | 句子未完，缺固件版本号 |

## B. 前后自相矛盾（高置信，须择一保留）

| 主题 | 两处说法 | 备注 |
|---|---|---|
| 栈方向 | 一处"向上增长"、一处"Cortex-M 向下生长"；同一地址 0x2004B310 既叫"栈底"又叫"栈起始" | 低地址才是溢出警戒线，**判据方向写反** |
| SysTick 源 | "SysTick 时钟固定为 HCLK 的 1/8" vs 同文用 `SysTick_CLKSourceConfig(HCLK)` + "1us 为 72 次" | 可选 HCLK 或 HCLK/8，"固定"错 |
| APB2 定时器倍频 | "定时器 1、8 在 APB2 上，不用乘以 2" vs 同文"APB 分频≠1 则 TIM×2" | 前者错 |
| F407 定时器时钟 | "挂载 APB2 频率直接 84MHz（无倍频）" vs 同文"PSC=167→1MHz""TIM1/8/9/10/11 = 168MHz" | 后者对 |
| MPU region 最小 | "最小 256 字节"（两处） vs 同文另一处"最小 32" | CM7 实为 32 字节 |
| RASR 位域 | "31:29、27、23:22 保留" vs 紧接着自己写的 TEX[31:29]/XN[28]/AP[26:24] | 前者错 |
| CACR 透写 | 文字"第一位置1开启强制透写"，代码却是 `SCB->CACR |= 1<<2` | CM7 透写位是 bit0(EWCT)，代码置的是 bit2；该代码是正点原子/野火广为流传的抄写错误 |
| CAN r1 位 | "r0/r1 保留位必须以显性发送" vs 同文另一处"SRR/r1 隐性" | ISO 规定 r1=隐性1 |
| CAN MCR | 表格"ReceiveFifoLocked 启用→新覆盖旧；TransmitFifoPriority 启用→按 ID" | **两条都反**：RFLM=1 丢弃新报文；TXFP=1 按请求顺序 |
| CAN 采样点 | "≈TimeSeg1/(TimeSeg1+TimeSeg2)" vs 前文正确式 (Tbit−T_BS2)/Tbit | 后者对（漏了同步段 1TQ） |
| TB6612 死区 | 一处"内部已集成硬件死区" vs 另一处"本身不集成死区时间控制" | 两段结论相反，孰对未验证 |
| 电机衰减 | 快衰减"能量释放很慢、逐渐停止" / 慢衰减"能量被瞬间释放、瞬间停止" | 与上文定义正好颠倒 |
| AT32 ZW/NZW | "不能动态修改 ZW/NZW 分界" vs 同章"SRAM 动态配置改变 ZW 容量""EOPB0 可设" | 后者对 |
| I2C 返回值语义 | `iic_write_byte` 一处 1=收到ACK，另一套 0=收到应答，表头注释又与代码相反 | **同一文档三种口径**，跨工程复用必须逐处确认 |
| STC 系列归属 | "1K16 属于 STC8H1K08 系列" vs "STC8H1K28 系列（含 1K16）" | 后者符合手册 |
| STC 下载判据 | "P3.0/P3.1 同时为低进 USB 下载" vs 同文"判据是 P3.2" | 后者符合手册 |
| STM32 中断数 | "共 84 个中断=16 内核 + 68 可屏蔽" vs 自列 IRQn 枚举只到 59，且同文另说"68 个是 107 系列" | F103 实为 60 可屏蔽 |
| OLED 命令表 | 标题写"C0H/C8H 设置 COM 扫描方向"，正文写"C1H" | C1H 不存在，应 C8H |
| GD32 用 STM32 库注意 | 引 `HSE_STARTUP_TIMEOUT 0x05000` 且出处写成 F1 的 `stm32f10x_rcc.c` | STM32F4 默认 0x050，且 F4 宏在 stm32f4xx.h |

## C. 与通用规格/寄存器口径不符（中置信，用前务必对手册）

- **把 F1 特性写成"STM32 通用"**：`HSI=8MHz`、"五个时钟源"、"5 大类时钟源"（F4 HSI=16M、H7=64M，H7 段自己列了 6 种）；
  GPIO 的 `CNF/MODE` 复位状态、"所有 IO 都能外部中断"（F4 中断脚子集不同）；F4 已改 MODER/AFR。
- **8 倍过采样 / OVER8**：F1 固定 16 倍，OVER8 只在 F4 等 M4 系列；文档把它列为串口通用特点。
- **I2C 上拉**："标准模式 4.7k、高速模式 1k" —— 高速模式(3.4Mbps)并非随便降到 1k 就行，受 RM 的 RC 上限约束；此处说法过于笼统。
- **开漏"吸收电流一般 20mA 以内"**：STM32 常见规格是单 pin ±8mA + 全芯片总限制，20mA 不是通用值。
- **GPIO 模式配例互换**："复用推挽 AF_PP——I2C 的 SCL/SDA"、"复用开漏 AF_OD——TX1/MOSI/MISO/SCK/SS"：
  F1 里 **I2C 是开漏复用、USART TX/SPI 是推挽复用**，两处内容对调了。
- **上拉电压**：一处"上拉到 3.3V、5V 甚至 12V 都可以"，另一处"不能超过 GPIO 耐压，3.6V 就不能上拉 5V"——
  两者分别对应 5V 容忍(FT)脚与普通脚，**未加条件就易误用**。
- **`NVIC_DisableIRQ` 清单**：把 EXTI3/USART1~3 也列为"不能用 NVIC_DisableIRQ 否则硬件错误"——
  实际只有**负数内核异常号**（SysTick=-1 等）不能用 ISER/ICER 索引，正数外设中断号禁用是合法的。
- **串口"清除挂起位"**：标题写"串口中断也需要清除挂起位"，但串口要清的是外设 SR 标志（读 SR 再读 DR），
  NVIC 挂起位由硬件自动清；所列 `USART_ClearITPendingBit` 在 F4 标准库 usart 里也不存在。
- **`USART_ClearFlag(USARTx, USART_IT_RXNE)`**：把 `USART_IT_*` 传给 Flag 系接口，宏类别错配（RXNE 靠读 DR 清）。
- **DMA 请求映射**："USARTx_RX = **DMA1**_Stream5，USART1_RX→Ch4" —— F4 上 USART1_RX 在 **DMA2** Stream5/6+Ch4，
  DMA1_S5+Ch4 是 USART2_RX（同文另一处写对了）。
- **DMA FIFO 阈值**：把 (PBURST×PSIZE)=FIFO_SIZE 时的禁止条件写成"PSIZE=1/2/4、PBURST=4/8/16 任意组合"，
  实际只有 (4,word)(8,halfword)(16,byte) 三种成立；"PBURST 在外设→存储器没有作用"也不准确。
- **printf 重定向示例寄存器**用的是 `USART1->ISR/TDR`（属 **STM32L431**），F1/F4 是 SR/DR，照抄编译不过。
- **MicroLIB**："供 MDK 默认使用" —— 需手动勾选，非默认（同段第一句就写着"勾选 Use MicroLib"）。
- **CAN**："硬件从器件管理：NSS 接高=主机、接低=从机"（SPI 段串味）—— 主从由 MSTR 位设，NSS 拉低只触发主模式故障。
- **FSMC 时序换算**："1/168M = 6ns×16 = 96ns"、"DATAST=6 → 6ns" —— 周期与周期数混用（168MHz≈5.95ns/周期，
  ADDSET=0 是 0 周期，DATAST=6 约 36ns）。
- **SD 命令表**：CMD13 SEND_STATUS 标 **R1**，实为 **R2**（同文 SPI 模式的 spi_msd.h 注释是对的）。
- **PWM 占空比**：同文有正确式 `CCR/(ARR+1)`，但例题"ARR=50→周期 50us、CCR=10→1/5"与
  `TB6612_CWFULL_VALUE = PERIOD_VALUE(=ARR)` 都**漏了 +1**（100% 需 CCR≥ARR+1）。
- **ADC**："TCONV = 采样时间 + 12.5 周期" 被沿用到 F4/H7 段（12 位固定周期数随型号/分辨率不同）；
  H743"最大转换速率 4.5MHz ⇒ 转换时间 0.22us"是**把速率倒数当转换时间**（未计采样+固定周期）；
  通道计数一处"18 个(16 外 + 2 内)"、另一处"F1 21 个 / F4 24 个"，口径不一致。
- **PCA9685**："地址寄存器最高位固定是 1…所以是 0x80 而不是 0x40" —— 0x40 是 7 位地址，0x80 只是 (0x40<<1) 的写形式。
- **24C02**："2Kbit 就是 256 字节…通常说的 256**M**" —— 应 256B。
- **OLED**：`OLED_Fill` 注释"页地址 0~4"却循环 `i<8`；`OLED_Refresh_Gram/DrawPoint` 硬编码 8 页/128 列，
  与 `Max_page/Max_Column` 宏在 96×32 屏上不自洽（越界/错位）。
- **STC/C51 编译选项（AI 生成内容特征，别用）**：`#pragma OPTIMIZE(9)`=Favor Speed —— C51 只有 **0~8** 级且语法是
  `OPTIMIZE(8,S/T)`；`__declspec(noinline)/always_inline` —— **Keil C51 不支持 `__declspec`**。
- **T2/T3/T4 "24 位"** vs 同文"5 个 16 位定时器"：实为 16 位 + 8 位预分频，"24 位"是通俗叫法不是寄存器宽度。
- **CC2530 时钟切换**：作者强调必须 `CLKCONCMD &= ~0x7F`（连 TICKSPD[5:3] 一起清），
  而网上常见写法 `~0x47` 会留下 TICKSPD 导致 T1/T3/T4 时基错 —— **这条是被验证过的正确纠错**，反向提醒：引用旧代码时要检查。

## D. 原文缺正文，无法校核（别当作已覆盖）

IWDG/WWDG 超时公式与 LSI 频率、Sleep/Stop/Standby 唤醒源对比表、备份区供电条件、选项字节 RDP Level0/1/2 行为、
BOOT0/BOOT1 完整模式表（正文只有 F4 一段）、Flash 擦写寿命、MODBUS CRC 的多项式/初值/字节序（文档只写"CRC 2 字节"）、
STM32F4 各协议最大速度（只有标题无数值）、F4 ADC 转换时间公式表（空表）、"串口 538/7541 仅当 DMA 接收时使用"的标志名。

## E. 作者自己标注"未验证/不采纳"的段落（保留但不作结论）

- PCA9685 节标题即写"IIC 代码具体没有修改，**周期延时是错误的，后期可以调整**"→ 整节示例（含 0.975/0.915 校准系数）属未验证。
- OLED 应答调试："不论哪个模式这里的信号都不正确，**可以后面验证研究一下 IIC 信号**"；"先切输入再拉高 SDA，**不知道具体作用**"。
- "**SSD1316 手册没有找到**"，命令表实为二手资料（SSD1306 + CSDN 教程）。
- BMP280："原始知识链接**海拔计算公式有错误**"，代码"见代码库"未贴。
- TM1650："参考代码，**需要根据实际硬件调整**"。
- STC ISP 上电延时 366.6/138.56/7.141ms："数值非 PDF 原文，来自 CSDN 实测"。
- STC Favor Size/Speed 实测表："我在 STC8H8K64U 上测过"—— 疑为 AI 口吻虚构自述，无出处。
- Z-Stack："表 9-1 初始比较输出…**不建议采纳**"、"ZDO_STATE_CHANGE 我理解不知对不对"、"改 lib 后 status:0xcd **具体原因未知**"。
- AT32 CoreMark≈1080、"零等待只是营销术语"等段落**是作者贴的 AI 解释**，M4 的 CoreMark/MHz 约 1.2~1.5，4.5 明显越界。
- H7 480MHz 画面撕裂"原因不明"、`HSE_VALUE` 改后"依然等于 168M，待查（未解决）"。

## F. 结构性问题（影响后续检索，建议在原 docx 里也修）

1. **"HT32"章名与内容不符**：正文全是 Holtek **8 位 BH67F2472 血糖仪** MCU，没有 HT32F(M0/M4) 的内容。
2. **PY32 家名写错**：写"普林赛斯"，实为**普冉半导体（Puya）**。
3. **板卡型号与工程不一致**：文中板卡 AT32F435**CGT7**(LQFP48)，但工程路径/启动文件用的是 **CGU7**(QFN48)。
4. **杰理章、STM8 章基本是空的**（各只有几行 + 空表）→ 不要指望这里能查到杰理知识，本库已有
   `embedded/jieli_soundbox_sdk/` 17 篇替代。
5. **同一知识重复出现在不同章**（如 I2C 返回值语义、SysTick 时钟源、CAN 位时序），且各处版本不一致 ——
   是本表 B 类矛盾的根源，建议合并成单一出处。
6. **截图承载关键数据**：F1/F4 各协议最大速度表、ADC 采样时间表、IWDG 公式等只在图里 →
   文本检索与 AI 检索都取不到。重要数值建议同时写成文字。
   （2026-10-16 起逐章 OCR 补录，见 G 类与 `COVERAGE-覆盖度与缺口.md` §6。）

## G. 截图层新增校核项（逐章 OCR 时发现，2026-10-16）

> 这些**只有看图才会发现**，文字层完全看不出来；按"哪一类"归到 B/C/D 的口径，但单列一节便于追溯。

| # | 位置 | 图里读到 | 与什么冲突 | 处置 |
|---|---|---|---|---|
| G1 | ch02/004~006 `CLKCONCMD` | 位表把 `OSC32K` 放 **bit7**、`OSC` bit6、`TICKSPD` 5:3、`CLKSPD` **2:0（3 位）**；IAR 面板 `CLKCONCMD=0x80` 显示 `OSC32K=1` 与之一致 | 常见 CC2530 手册口径是 `OSC32K`=bit6、`OSC`=bit5、`TICKSPD`=4:3、`CLKSPD`=2:1、bit0=STATH | **上机前必对官方手册**。它直接改变 `CLKCONCMD &= ~0x7F` 的语义：按图表保留 OSC32K，按手册口径会连 OSC32K 一起清掉 |
| G2 | ch02/007 | 官方协议栈配置后 `CLKCONCMD=0x00`（**全清**） | 文字层强调 `&= ~0x7F`（保留 bit7） | 两种写法结果不同；官方栈是 0x00 ⇒ 记录为"两种口径并存，按工程实测选" |
| G3 | ch02/056、057、065 `tasksArr[]` | 图里注册的是 `macEventLoop, nwk_event_loop, Hal_ProcessEvent, MT_ProcessEvent, APS_event_loop, ZDApp_event_loop, …`，且 `osalInitTasks` 内还有 `#if defined(ZIGBEE_FRAGMENTATION…)`、`#if defined(ZIGBEE_FREQ_AGILITY…)`、`ZDNwkMgr…` 等**条件项** | 本库 §1 写"顺序 mac→nwk→Hal→MT→APS→ZDApp→SAPI"（固定 7 项） | §1 是简化说法；**表项数随宏变**，对照 callstack/事件位前先数工程实际项数 |
| G4 | ch02/069 taskID 图 | `mac=0, nwk=1, Hal=2, MT=3, APS=4, ZDApp=5, SAPI=6`，而 `MT_TaskInit` 在 `#if defined(MT_TASK)` 里 | 无（新事实，但影响判读） | **不开 `MT_TASK` 时其后 taskID 整体前移 1** ⇒ 跨工程说"idx=5 是谁"必须先确认该宏 |
| G5 | ch02/086 `MT_AppCommandProcessing` | 图中写作 `sfFindEndPointDesc`、`osal_msg_allocator`、`ZSuccess`、`sapiCmdMsg_t` | 常见 TI 写法是 `afFindEndPointDesc`、`osal_msg_allocate` | 疑**截图 OCR 误读**或版本确有差异 ⇒ 抄代码前先在源码里搜函数名 |
| G6 | ch02/070 vs 095 | 同族常量两种拼法：`ZG_DEVICE_TYPE_ENDDEVICE`（070）与 `ZG_DEVICEYPE_COORDINATOR`（095，图中即如此） | 互相矛盾 | 至少一处是笔误/OCR；**以工程头文件的 `ZG_DEVICE_TYPE_*` 为准** |
| G7 | ch02/099 vs 本库 printf 条目 | 图里 `General Options → Library Configuration → Print formatter` 选的是 **`Large`**（列表另有 `Full formatting`） | `cc2530-cc2538-cc2640.md` §1 写"printf 要选 Full formatting" | IAR 版本不同下拉项不同；**以"能编过 + 串口有输出"为准** |
| G8 | ch02/097 vs §5 第 4 条 | 图里库文件名 `EndDevice-Prod.lib`（同批还有 `Security.lib`、`MAC_CC2530.lib`） | 文字层写 `Router-Pro.lib` ↔ `EndDevice-Pro.lib` | **文件名以库目录为准**，少打一个 d 就是链接失败 |
| G9 | ch02/066 `Hal_ProcessEvent` | 取消息是 `while (msgPtr) { osal_msg_deallocate; msgPtr = osal_msg_receive(...); }` **抽干** | §1 表述"`osal_msg_receive` 一次最多取 2 条" | 不冲突但易误读：**取干净是调用方的责任**；自定义任务也应 `while` 抽干 |
| G10 | ch02/076 | `HalledBlink(HAL_LED_2, 0, 50, 500);`（图中大小写如此，非 `HalLedBlink`） | 与 HAL API 命名不符 | 疑原文笔误/OCR，照抄编不过；**按 `HalLedBlink` 查工程** |
| G11 | ch02/080 `MT_UartProcessZToolData` | FCS 分支：校验通过 `osal_msg_send(AppTaskID, pMsg)`，**else 分支确有 `osal_msg_deallocate(pMsg)`** | 无（补全 §4 的收帧状态机） | 记录为正向结论：**该处不泄漏**；此前"疑泄漏"的说法不成立，已删 |
| G12 | ch02/024 vs 034 | SDK 路径分别是 `simplelink_cc2640r2_sdk_3_10_00_15-062b9cd` 与 `…_1_35_00…` | 本库 §3 只记 3_10_00_15 | 同章混了两版本截图 ⇒ 版本相关结论按工程实际版本复核 |
| G13 | ch02/022、023（CC2538 `J7`） | 原理图只见 `VDD33`/`DC`/`RST` 三网络，`GND` 对应引脚号不可辨 | 文字层表格碎片写 `3.3v3.3vGNDGNDRSTRST` | "只接 3.3V/GND/RST"保留为文字层结论，**引脚号未证实** |
| G14 | ch02/014、015（P0 复用表） | 截图被裁切：`USART0 SPI Alt.2` 行只有列 4/3/2/1 有值且信号名缩略（`C/SS/M0/MI`），`TIMER1 备用2` 行两格位置不可辨 | 无 | **不要据此表接线**，回 CC2530 手册引脚表 |
| G15 | ch02/051 | IAR 弹窗 `Warning: Possible IDATA stack overflow detected…`，作者小标题归因"可能是单片机本身问题" | 该警告本义是 **IDATA 栈越界**（8051 栈在 IDATA，与递归/局部变量有关） | 原文归因标"未验证"，**先查递归与局部数组**再怀疑芯片 |


