# 串行总线：UART / RS485 / CAN / MODBUS

> 来源见 `README.md`。`⚠校核` 指向 `ERRATA-单片机外设和调试基础知识.md` 的对应条目。
> 适用范围列里的 `F1/F4/H7` 指 STM32 系列，其他家芯片写清型号。

## 1. 通信分类与速率（通用，用作选型基准）

| 维度 | 内容 | 范围 |
|---|---|---|
| 方向 | 单工=单向；半双工=双向但**同一时刻只单向**（"切换方向的单工"）；全双工=同时双向 | 通用 |
| 同步性 | 同步=带时钟线（SPI/I2C）；异步=无时钟（UART/单总线，靠约定波特率 + 起止位） | 通用 |
| 接口线 | UART(TXD/RXD/GND) 异步全双工；1-Wire(DQ) 异步半双工；SPI(SCK/MISO/MOSI) 同步全双工；I2C(SCL/SDA) **同步半双工** | 通用 |
| I2C | 标准 100Kbps(12.5KB/s, 位周期 10us)、快速 400Kbps(50KB/s)、高速 3.4Mbps(435KB/s)、"超高速 5Mbit/s" `⚠校核A` | 通用 |
| SPI | "约 50Mbps ≈ 5.9MB/s" `⚠校核A`（按 /8 应 6.25MB/s） | 通用（转抄） |
| UART | 9600bps≈1.2KB/s、115200bps≈14.4KB/s | 通用 |
| RS232 | 共地、±12V、约 20Kbps、点对点、"最大 15 米" `⚠校核A/C`（距离与速率不可同时成立；表中"20KB/s"单位可疑） | 通用 |
| RS485 | 2 线差分、半双工、多点；10m 时 35Mbps、1200m 时 100kbps；常规 32 节点（特制 128/256/400） | 通用 |
| CAN | <40m 可达 1Mbps；40m~10km 时 <5Kbps `⚠校核A`（1Mbps→125KB/s，非 128） | 通用 |
| 其他 | SDIO >10Mbps；LVDS 655Mbps~1.923Gbps；HDMI 1.3=10.2Gbps、2.0=18Gbps | 通用 |
| STM32 上限 | "F1 串口最大波特率 4.5M"；**F4 节只有标题无数值**（`⚠校核D`） | F1 |

## 2. UART

### 帧与波特率（通用）
- 帧 = 起始位 1 + 数据 5~9 + 校验 0/1 + 停止 1/1.5/2。`⚠校核A`（原文"1,15,2"）
- **波特率 → 时长**：2Mbps ⇒ 1 位 0.5us；8N1 每字符 10 位 ≈ **5μs**；8E1/8O1/8N2 为 11 位 ≈ **5.5μs**；
  10 字符 = 50μs / 55μs。
- 数据位 8/9；校验位**占用第 9 位**（所以 9 位数据与校验互斥）。
- 波特率公式 ` baud = fCK / (16 × USARTDIV)`，`fCK` 是该 USART 的外设时钟；
  过采样 16/8 倍（**8 倍过采样只有 F4 等 M4 系列，F1 固定 16 倍** `⚠校核C`）。
- 寄存器：`SR`（状态）/`DR`（数据）/`BRR`（分频）。

### 中断：必须"标志位 + 使能位"一起判（高频坑）
- **RXNE**：使能 `RXNEIE`；**读 DR 即清除**。
- **TXE**：使能 `TXEIE`；写 DR 清除，发送完成后硬件又会置 1。
  ⇒ **"不需要发送时必须关掉 TXEIE，否则持续进中断"**。
- 同一 USART 的所有中断共用一个向量 ⇒ ISR 里**必须同时判标志位和使能位**，
  否则 RXNE 进来时 TXE 也为 1，会误执行发送分支。
- IDLE（空闲线路）标志清除方式：**先读 SR 再读 DR**（只读 DR 不够）`⚠校核C`。
- 常见写错：把 `USART_IT_RXNE` 传给 `USART_ClearFlag/GetFlagStatus`（应使用 `USART_FLAG_*`）`⚠校核C`。
- 所谓"串口中断要清 NVIC 挂起位"：串口实际要清的是**外设 SR 标志**，NVIC 挂起由硬件自动清 `⚠校核C`。

### DMA 接收的两种工作方式（F1/F4 都适用）
| 方式 | 做法 |
|---|---|
| 循环模式 | `DMA_Mode_Circular` + `USART_IT_IDLE` + 读写双索引，**不需要复位 DMA** |
| 正常模式 | 读完必须：`DISABLE` → `DMA_ClearFlag`（TC/HT/TE/DME/FE 五个）→ `DMA_SetCurrDataCounter` → `ENABLE` |
- 已收长度 = `RINGBUF_SIZE − DMA_GetCurrDataCounter()`；写索引 = `(RINGBUF_SIZE − Count) % SIZE`。
- **"没有清除状态标志位的话，DMA 是无法使能的"**（EN=1 前必须清标志，见 `timer-pwm-adc-dma.md` §DMA）。
- 环形缓冲跨尾 bug：`shell_input(buf+Read_Index, len)` 在跨过缓冲区尾时会读错 ⇒
  修法①拆两段 `memcpy`；修法②把 `Receive_flag` 改成判 `Write_Index != Read_Index`。
- flush 序列：USART DISABLE → 关 IDLE → `Read=Write` → ClearFlag(IDLE) → 使能。
- 实测：超级终端里一次发满缓冲"至少需要 1050"字节量级。

### HAL 收串口的分支顺序（F1/F4 通用）
`HAL_UART_Receive_IT` 使能 PE+ERR+RXNE；`IRQHandler` **先读 SR/CR1/CR3**；
`errorflags==0` 才走 RXNE→`HAL_UART_IRQHandler` 内的 `UART_Receive_IT`；
有错误时**需要 EIE 或 RXNEIE/PEIE 之一使能**才会处理；再判 TXE→TC；
`RxXferCount` 减到 0 时关三个中断 + 状态置 READY + `RxCpltCallback`；
无校验取 `DR & 0x00FF`，**有校验取 `DR & 0x007F`**。

### 引脚与数量
- F103 最多 5 个 USART；F4 最多 8 个（F407 常见 6 个）。`⚠校核C`（文档数量段把 F1/F4 混写）
- **F4 引脚是 TTL，不能直连 RS232/DB9**，必须电平转换；CH340 是 TTL→USB，要装驱动；**TX↔RX 交叉**。

### printf 重定向（多处写法差异，容易照抄错）
| 路线 | 做法 | 范围 |
|---|---|---|
| Keil + MicroLIB | 勾选 Use MicroLIB ⇒ 只需重定义 `fputc` | Keil |
| 标准 C 库 | 必须 `#pragma import(__use_no_semihosting)` + `_sys_exit` stub + `struct __FILE{int handle;} FILE __stdout;`，否则**脱离调试器就卡死（半主机）** | Keil |
| 寄存器直发 | `while((USART1->ISR & 0X40)==0); USART1->TDR=ch;` — **ISR/TDR 是 L431 命名，F1/F4 是 SR/DR** `⚠校核C` | 型号相关 |
| 自定义 kprintf | `vsnprintf` 到 static buf 再发，避开 printf 体积 | 通用 |
| CC2530 | `__near_func int putchar(int c){UTX0IF=0;U0DBUF=c;while(UTX0IF==0);return c;}`；协议栈版走 `at_uart_write` | CC2530 |
| 三种输出通道 | **ITM/SWO**：硬件单向、高速、几乎不影响 CPU；**半主机(BKPT)**：暂停 CPU、双向、慢、占体积；**UART**：最通用 | 通用 |

### WK2114 串口一扩四（器件专属）
| 项 | 值 |
|---|---|
| 主口波特率 | v1 用 230400、v2 用 460800；子口默认 38400 |
| 中断/复位脚 | IRQ = PB7 下降沿（走 EXTI9_5）；REST 低有效复位 |
| 复位时序 | v1：H→L 100ms→H 20ms；v2：L 300ms→H 20ms |
| 寄存器地址算法 | 写 `((port−1)<<4)+reg`；读 `0x40 + 同上`；FIFO 区 `0x80`/`0xC0` |
| 波特率基准 | **"根据 11.0592MHz 外部晶振计算"** ⇒ 换晶振必须重算 |
| 关键寄存器 | SPAGE1 下 `BAUD1/BAUD0/PRES`、`RFTL/TFTL`、`FCR=0xFF` |
| 自适应识别 | 复位后主口发 `0x55` |
| ISR 逻辑 | 循环读 `GIFR` 判 `UTxINT`，再 `while(FSR & RDAT)` 读 `FDAT`；`(0x0F & GIFR)!=0` 继续 |
| 代码内注释 | `delay_us(50);//延时比较重要` ⇒ 删/改必坏 |
| ⚠校核 | `RFTL=0x40` 两处注释分别写"1 个字节"和"64 个字节"（0x40=64）；`TFTL=0x10` 写"256 个字节"vs"16 个字节"（0x10=16）；`gier |= WK2XXX_UT1RST` 出现在"使能子串口中断"分支里，疑为 INTEN 类宏笔误；`ReadByte` 超时返 0 与真收到 0x00 不可区分 |

### ISP 下载与串口的互踩（经验，很实用）
- **flyMcu 一键下载电路**流控可能把芯片卡在复位态 ⇒ **SecureCRT/MobaXterm 串口"卡死"、调试器连不上**；
  文档明确写："用串口终端时，不要使用带 ISP 下载功能的那个终端"。
- 未接线就收到乱码 ⇒ 判为干扰；接带地线的屏蔽线后正常；TX/RX 短接可自测；
  "STM32 能拉低、CC2530 拉不动"是**驱动能力差异**而非软件问题。
- 官方串口 ISP：USART1(PA9/10)、USART3(PB10/11 与 PC10/11)、CAN2(PB5/13)、USB DFU(PA11/12) —— 详见
  `embedded/mcu-toolchain-boot-flash/README.md`。

## 3. RS485

| 项 | 内容 | 范围 |
|---|---|---|
| 电平 | "1" = +(2~6)V 压差；"0" = −(2~6)V 压差 | 通用 |
| 收发控制 | SP3485：`DE` 高=发送使能、`RE` 低=接收使能、`RO`/`DI` 为收数据/输入；**"全双工 485"实际是 RS422** | 器件/通用 |
| 匹配阻抗 | 总线**两端各 120Ω**（=特性阻抗） | 通用 |
| 偏置电阻 | 保证空闲时 AB 压差约 **200mV**，防逻辑混乱（正点原子战舰 R19/R22、探索者 R38/R40） | 通用 |
| 拓扑 | 推荐点对点/线型总线；**禁止星型、环型** | 通用 |
| 方向切换时序 | 本切片未展开（要等 TX 完成标志 TC 再翻 DE，否则末字节被截）——**需另行补证** | — |
| 坑 | 未使能 GPIO 时钟（`RCC_AHB1Periph_GPIOG`）时配置寄存器无效 ⇒ PG8 方向脚失效 | F4 |

## 4. CAN

### 物理与时序（通用）
- **显性 = 逻辑 0**（CANH≈3.5V、CANL≈1.5V、差≈2V）；**隐性 = 逻辑 1**（2.5/2.5、差 0V）；
  **显性位"覆盖"隐性位（线与）** ⇒ 仲裁里 ID 小者胜。终端电阻 120Ω。
- 仲裁只在**总线空闲**时、从 SOF 开始逐位进行，**中途不可抢占**。
  前 11 位 ID 相同则标准帧（RTR=0 显性）胜扩展帧（SRR=1 隐性）；数据帧胜远程帧；`0x7F8~0x7FF` 为 Bosch 保留。
- **位时序**：1 位 = `Sync_Seg`(固定 1TQ) + `Prop_Seg`(1~8) + `PBS1`(1~16) + `PBS2`(1~8)；
  STM32 把 PTS+PBS1 合并成 BS1。
  `波特率 = fCAN_CLK / (Prescaler × 总TQ)`；例：42M/((6+7+1)×6)=500k（F407, APB1=42M）、36M/((9+8+1)×4)=500k（F103）。
  **采样点 = (Tbit − BS2) / Tbit**，例 16TQ/BS2=2 ⇒ 87.5%，推荐 **75%~90%**。`⚠校核B/C`（另一处公式漏了同步段）
- 同步：SOF 下降沿**硬同步**；帧内 1→0 边沿**重同步** —— 沿提前则延长 BS1、滞后则缩短 BS2，幅度 ≤ SJW(1~4TQ)。
- 三采样（`CAN_BTR[SAM]`）= 主采样点及前 1、2TQ 多数表决，**只增强抗干扰、不提速率**。
- 帧字段位宽（照抄）：标准帧 SOF(1)+ID(11)+RTR(1)+控制场(6)+数据(0~64)+CRC(15+1 界定符)+ACK(槽1+界定1)+EOF(7 隐性)；
  扩展帧另加 SRR(1)+IDE(1)+ID(18)；**DLC 只允许 0~8**。`⚠校核B`（r1 电平两处矛盾）

### STM32 bxCAN（F1/F4）
- 规格：CAN 2.0A/B、最高 1Mbps、**3 个发送邮箱**、**2 个 3 级接收 FIFO**、过滤器组最多 28
  （F103 普通型 14、互联型 28；F407 CAN1/CAN2 共 28）。
- `MCR` 位：**ABOM**（自动退出 Bus-off：监测到 **128 个连续 11 隐性位**序列即退出）、
  **NART**(bit4，不自动重传)、**RFLM**(bit3，FIFO 满时丢弃新报文)、**TXFP**(bit2，按接收顺序而非 ID 排发送优先级)。
  `⚠校核B`：文档表格里 RFLM/TXFP 的行为**写反了**。
- 测试模式：`BTR` 的 LBKM（回环）/SILM（静默）。
- **滤波器必须在 `FINIT=1` 时配置**：`FM1R`(屏蔽/列表)、`FS1R`(位宽 16/32)、`FFA1R`(关联 FIFO)、`FA1R`(激活)；
  掩码模式下**屏蔽位 1 = 必须匹配**；扩展 ID 要 `ext_id<<3` 填进 `FiRx` 并按 TIR 位对齐、或 `CAN_ID_EXT(0x4)`。
- HAL 写 BTR 时 **Prescaler 要 −1**。
- TTCAN：`TimeTriggeredMode=ENABLE` 时**必须 `AutoRetransmission=DISABLE`**（ISO 11898-4 要求，保证时隙确定性）；
  H7/G4 的 FDCAN 有专门 `TSCtrl`。
- `⚠校核C`：`f_CAN_CLK` 文档举例写"通常是 APB1（如 45MHz）"，与 F4 的 APB1=42M 不符。

## 5. MODBUS RTU（通用）

| 项 | 内容 |
|---|---|
| 帧 | `从机地址(1) + 功能码(1) + 数据 + CRC(2)` |
| 常用功能码 | `0x03` 读寄存器、`0x06` 写单个寄存器、`0x10` 写多个寄存器 |
| 数据模型 | 线圈 = 1 bit；寄存器 = 16 bit = 2 字节 |
| 与 485 关系 | Modbus RTU 主站轮询、**从站不能主动发**；物理层常用 RS485 |
| ⚠校核D | **CRC 的多项式/初值/字节序文档没给**（只写"CRC 2 字节"）⇒ 不要以为库里已写明；标准实现是 `0xA001` 反射多项式、初值 `0xFFFF`、**低字节先发**，但这属"另行查证"，非本库结论 |
