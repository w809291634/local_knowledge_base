# 代码配方：UART / RS485 / CAN（照抄原文 + 用法 + 验证）

> 配套 `serial-uart-rs485-can-modbus.md`。**代码全部照抄原 docx**，只删无关行、加 `// ← 关键`；
> 未改任何数值/宏名/寄存器名。`⚠校核` = 原文可疑处，**保留原样未修正**。
> 行号指 `单片机外设和调试基础知识.docx` 导出文本的位置（17a=硬件通信方式前半，17c=SPI/485/CAN 段）。

## 1. 串口初始化（标准库）

来源 17a:501、753 | 适用 F4 标准库（F1 差异见下）
```c
RCC_AHB1PeriphClockCmd(USARTx_GPIO_RCC, ENABLE);      // F1 用 RCC_APB2Periph_GPIOx
RCC_APB2PeriphClockCmd(USARTx_RCC, ENABLE);           // USART2/3 走 APB1，函数别选错
GPIO_PinAFConfig(USARTx_TX_GPIO, USARTx_TX_PIN_NUM, GPIO_AF_USART1);   // F1 无此步
GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF;  GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;
GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_UP;  GPIO_Init(USARTx_TX_GPIO, &GPIO_InitStructure);
USART_InitStructure.USART_BaudRate = bound;           USART_InitStructure.USART_WordLength = USART_WordLength_8b;
USART_InitStructure.USART_StopBits = USART_StopBits_1; USART_InitStructure.USART_Parity = USART_Parity_No;
USART_InitStructure.USART_HardwareFlowControl = USART_HardwareFlowControl_None;
USART_InitStructure.USART_Mode = USART_Mode_Rx | USART_Mode_Tx;
USART_Init(USARTx, &USART_InitStructure);
USART_ITConfig(USARTx, USART_IT_RXNE, ENABLE);        // 需中断才写
NVIC_Init(&NVIC_InitStructure);                       // 见 recipes-clock-gpio-nvic.md §6
USART_Cmd(USARTx, ENABLE);
```
- **F1 写法**（17a:854）：TX = `GPIO_Mode_AF_PP`、RX = `GPIO_Mode_IN_FLOATING`，**无 `GPIO_PinAFConfig`**。
- **HAL F1**（17a:824）：TX = `GPIO_MODE_AF_PP`+`GPIO_SPEED_FREQ_HIGH`，RX = `GPIO_MODE_INPUT`+`GPIO_NOPULL`（原文注"F1 作为 RX 是浮空输入"）。

用法/验证：`bound` 填 9600/115200；USART1/6 在 APB2、2/3/4/5 在 APB1 ⇒ 时钟使能函数按总线选。
示波器量 TX 空电平应为高、位宽 = 1/波特率；或 TX-RX 短接自发自收。

## 2. 串口 ISR 模板：**必须"标志位 + 使能位"双判**

来源 17a:312（HAL 本体）、569（应用层） | 适用 F1/F4
```c
/* HAL 内部判法：同一向量下 RXNE/TXE/IDLE 共存，只判标志会误进 */
if (((isrflags & USART_SR_RXNE) != RESET) && ((cr1its & USART_CR1_RXNEIE) != RESET))
{ UART_Receive_IT(huart); return; }

/* 应用层：RXNE 收进环形缓冲（读 DR 即清 RXNE） */
void USART1_IRQHandler(void){
  if( USART_GetITStatus(USARTx, USART_IT_RXNE) == SET ){
    shell_ringbuf[Write_Index] = (char)USART_ReceiveData(USARTx);   // ← 读 DR 清标志
    Write_Index++; Write_Index = Write_Index % USARTx_RINGBUF_SIZE;
  }
}
```
约束（原文 348/406 行）：**中断时间不超过 5us**；ISR 内只用 `rt_ringbuffer_putchar` 这类底层函数，**不要 printf**。
`⚠校核`：原文 518 行 `USART_ClearFlag(USART3, USART_IT_RXNE)` —— 把 `USART_IT_xx`（中断宏）传给 ClearFlag；
ClearFlag 参数属 `USART_FLAG_xx` 一族，RXNE 本就靠读 DR 清。原文 287 行表格把 ORE 的使能位写成 `TXNEIE`（应属 RXNEIE 一族）。

## 3. DMA + IDLE 空闲中断收环形缓冲（完整套路，最常复用）

来源 17a:501/554（配置）、624（跨环拷贝）、645/684（正常模式重设） | 适用 F4 标准库
```c
/* ① DMA 配置 */
RCC_AHB1PeriphClockCmd((u32)DMA_Streamx>(u32)DMA2 ? RCC_AHB1Periph_DMA2 : RCC_AHB1Periph_DMA1, ENABLE);
DMA_DeInit(DMA_Streamx);
while (DMA_GetCmdStatus(DMA_Streamx) != DISABLE){}        // ← 等 DMA 可配置
UARTDMA_InitStructure.DMA_Channel             = channel;  // CHSEL，见 §4
UARTDMA_InitStructure.DMA_PeripheralBaseAddr  = (uint32_t)&USARTx->DR;
UARTDMA_InitStructure.DMA_Memory0BaseAddr     = (uint32_t)ringbuf;
UARTDMA_InitStructure.DMA_DIR                 = DMA_DIR_PeripheralToMemory;
UARTDMA_InitStructure.DMA_BufferSize          = RINGBUF_SIZE;
UARTDMA_InitStructure.DMA_PeripheralInc       = DMA_PeripheralInc_Disable;   // ← 外设地址不增
UARTDMA_InitStructure.DMA_MemoryInc           = DMA_MemoryInc_Enable;
UARTDMA_InitStructure.DMA_PeripheralDataSize  = DMA_PeripheralDataSize_Byte;
UARTDMA_InitStructure.DMA_MemoryDataSize      = DMA_MemoryDataSize_Byte;
UARTDMA_InitStructure.DMA_Mode                = DMA_Mode_Circular;  // 方式二用 DMA_Mode_Normal
UARTDMA_InitStructure.DMA_Priority            = DMA_Priority_Medium;
UARTDMA_InitStructure.DMA_FIFOMode            = DMA_FIFOMode_Disable;
UARTDMA_InitStructure.DMA_MemoryBurst         = DMA_MemoryBurst_Single;
UARTDMA_InitStructure.DMA_PeripheralBurst     = DMA_PeripheralBurst_Single;
DMA_Init(DMA_Streamx, &UARTDMA_InitStructure);   // 不开 DMA 传输中断，靠串口 IDLE（原文 594 行注释）
DMA_Cmd(DMA_Streamx, ENABLE);
/* ② 挂接 */
USART_DMACmd(USARTx, USART_DMAReq_Rx, ENABLE);
USART_ITConfig(USARTx, USART_IT_IDLE, ENABLE);
/* ③ ISR：算写索引 */
if( USART_GetITStatus(USARTx, USART_IT_IDLE) == SET ){
  USART_ReceiveData(USARTx);                                   // 读 SR+DR 序列清 IDLE
  Write_Index = (RINGBUF_SIZE - DMA_GetCurrDataCounter(USARTx_RX_DMA_STREAM)) % RINGBUF_SIZE;
}
/* ④ 主循环取数：跨缓冲区尾要分两段 */
if (Read_Index + data_len > RINGBUF_SIZE){
  int len1 = RINGBUF_SIZE - Read_Index, len2 = data_len - len1;
  memcpy(temp, ringbuf + Read_Index, len1); memcpy(temp + len1, ringbuf, len2);
} else memcpy(temp, ringbuf + Read_Index, data_len);
Read_Index = (Read_Index + data_len) % RINGBUF_SIZE;
/* ⑤ flush */ Read_Index = Write_Index;
/* ⑥ 正常模式每帧后重设 */
DMA_Cmd(USART1_USE_DMA_RX_STREAM, DISABLE);
DMA_ClearFlag(DMA2_Stream5, DMA_FLAG_TCIF5|DMA_FLAG_FEIF5|DMA_FLAG_DMEIF5|DMA_FLAG_TEIF5|DMA_FLAG_HTIF5);
DMA_SetCurrDataCounter(USART1_USE_DMA_RX_STREAM, RX_RECEIVE_BUF_SIZE);
DMA_Cmd(USART1_USE_DMA_RX_STREAM, ENABLE);
```
原文 691 行的硬结论：**"如果没有清除状态标志位的话，DMA 是无法使能的"**。
判"有没有新数据"用 `Write_Index != Read_Index`（原文"修改2"），**不要**用 `Receive_flag`（"方法1 不可靠"）。
清/改标志的临界保护（624 行）：`USARTx->CR1 &= ~USART_CR1_IDLEIE; Receive_flag=0; USARTx->CR1 |= USART_CR1_IDLEIE;`
`⚠校核`：684 行把 `DMA_FLAG_xxIF5` 与 `DMA2_Stream5` **写死成流 5** —— 换流号必须换对应流的 flag 宏；
645 行清 IDLE 写成裸语句 `USART1->SR; USART1->DR;`（未接返回值，可能被优化掉），684 行的
`ClearFlag = USART1->SR; ClearFlag = USART1->DR;` 才是可靠写法。

## 4. printf 重定向三种（选一条，别混）

来源 17a:1058 / 1063 / 1078 | 适用 MDK
```c
/* A. MicroLIB + 寄存器直发（最快，不占 HAL 栈） */
int fputc(int ch, FILE *stream){
    while((USART1->ISR & 0X40) == 0);      /* 等发送完成(TC=bit6) */
    USART1->TDR = (uint8_t)ch;
    return ch; }
/* B. MicroLIB + HAL 函数（省事，稍慢） */
int fputc(int ch, FILE *f){ HAL_UART_Transmit(&huart1,(uint8_t*)&ch,1,0xffff); return ch; }
/* C. 不勾 MicroLIB：必须去半主机，否则脱离调试器直接卡死 */
#pragma import(__use_no_semihosting)
void _sys_exit(int x){ x = x; }
struct __FILE { int handle; };  FILE __stdout;
int fputc(int ch, FILE *stream){ while((USART1->ISR & 0X40)==0); USART1->TDR=(uint8_t)ch; return ch; }
```
`⚠校核`：原文 1050 行自述这段寄存器取自 **STM32L431**，`ISR/TDR` 是 L4/F7 的串口 IP 命名；
**F1/F4 应为 `SR`/`DR`**（TC 仍是 bit6）。A/C 需勾 Use MicroLIB，C 不勾。
验证：`printf("hello")` 串口助手可见；勾/不勾 MicroLIB 决定走 A/B 还是 C。

## 5. WK2114 一扩四（器件专属骨架，结构可套用到任何"串口扩展芯片"）

来源 17a:255（修改版本2） | 适用 F4 + WK2114（主口挂 MCU 的 USART，高波特率 460800）
```c
void  Wk2114_WriteByte(unsigned char b){ uart2_putc(b); delay_us(50); } // ← 原文注"延时比较重要"
int   Wk2114_ReadByte (void){ uint16_t t=0;
  while(Wk2114_IrqStatus==0){ delay_us(1); if(++t>899) return 0; }      // ← 超时与真收到 0x00 不可区分 ⚠校核
  Wk2114_IrqStatus=0; return Wk2114_Buffer; }                            // 数据由主口 RX 中断回调置入
static void Wk2114WriteReg(unsigned char port,unsigned char reg,unsigned char b){
  Wk2114_WriteByte(((port-1)<<4)+reg); Wk2114_WriteByte(b); }            // 写：((port-1)<<4)+reg
static unsigned char Wk2114ReadReg(unsigned char port,unsigned char reg){
  Wk2114_WriteByte(0x40+((port-1)<<4)+reg); return Wk2114_ReadByte(); }  // 读：再加 0x40
void Wk2114_Rest(void){ WK2114_REST_L; delay_ms(300); WK2114_REST_H; delay_ms(20); }   // v1 是 H-L-100ms-H-20ms
void Wk2114BaudAdaptive(void){ Wk2114_Rest(); Wk2114_WriteByte(0x55); delay_ms(500); } // 复位后发 0x55 自适应
void Wk2114SetBaud(unsigned char port,int baud){   // baud1/baud0/pres 查表，按 11.0592MHz 算，换晶振须重算
  scr = Wk2114ReadReg(port, WK2XXX_SCR); Wk2114WriteReg(port, WK2XXX_SCR, 0);   // 先关收发
  Wk2114WriteReg(port, WK2XXX_SPAGE, 1);
  Wk2114WriteReg(port, WK2XXX_BAUD1, baud1); Wk2114WriteReg(port, WK2XXX_BAUD0, baud0);
  Wk2114WriteReg(port, WK2XXX_PRES,  pres);
  Wk2114WriteReg(port, WK2XXX_SPAGE, 0);  Wk2114WriteReg(port, WK2XXX_SCR, scr);  // 恢复
}
void Wk2114_ExIrqCallback(void){          // IRQ=PB7 下降沿（EXTI9_5）<!-- 项目专有 -->
  do{ status = Wk2114ReadReg(1, WK2XXX_GIFR);
      if(status & WK2XXX_UT1INT)
        while( Wk2114ReadReg(1, WK2XXX_FSR) & WK2XXX_RDAT )
          { byte1 = Wk2114ReadReg(1, WK2XXX_FDAT); /*回调分发*/ }
      /* UT2/UT3/UT4 同构 */
  }while( (0x0f & Wk2114ReadReg(1, WK2XXX_GIFR)) != 0 );   // 读完 GIFR 即清中断
}
```
上电顺序：`IOInit → 主口高速初始化 → Rest → 写 0x55 自适应 → PortInit(GENA→GRST→GIER→SIER→FCR=0xFF→page1 设触点→SCR 收发使能) → SetBaud`。
验证：子口回环能通、IRQ 脚有下降沿；`RFTL/TFTL` 值与注释对不上时以手册为准（`⚠校核`：`0x40` 两处注释分别写"1 个字节"与"64 个字节"）。

## 6. RS485 方向控制

来源 17c:617/637 | 适用 F4 标准库
```c
/* 使能脚 = DE(高有效) 与 RE(低有效) 并联后的 GPIO */
GPIO_InitStructure.GPIO_Pin = GPIO_Pin_8; GPIO_InitStructure.GPIO_Mode = GPIO_Mode_OUT;
GPIO_InitStructure.GPIO_OType = GPIO_OType_PP; GPIO_Init(GPIOG, &GPIO_InitStructure);
RS485_TX_EN = 0;                                  // ← 默认接收模式
/* 发送套路：DE=1 → 发数据 → 等 TC → DE=0（等 TC 复用 §2 的 putc 写法） */
USART_ClearFlag(USARTx, USART_FLAG_TC); USARTx->DR = data;
while( USART_GetFlagStatus(USARTx, USART_FLAG_TC) == RESET );
```
`⚠校核`（17c:629~645）：`RS485_Init` 里配置 PG8 前**未使能 GPIOG 时钟** ⇒ 写寄存器无效、方向脚不动。
必须先 `RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOG, ENABLE)`。

## 7. CAN 初始化（BTR / MCR / 滤波器 / 回环自测）

来源 17c:1797~1810 | 适用 F1/F4 bxCAN 标准库
```c
RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);
RCC_APB1PeriphClockCmd(RCC_APB1Periph_CAN1, ENABLE);
/* PA11=RJ、PA12=TJ，GPIO_Mode_AF + GPIO_PinAFConfig(.., GPIO_AF_CAN1) */
CAN_InitStructure.CAN_TTCM = DISABLE;  CAN_InitStructure.CAN_ABOM = DISABLE;  CAN_InitStructure.CAN_AWUM = DISABLE;
CAN_InitStructure.CAN_NART = ENABLE;   // 禁止自动重传
CAN_InitStructure.CAN_RFLM = DISABLE;  // 原文注释"报文不锁定，新的覆盖旧的"  ⚠校核：与位义解释冲突，见 ERRATA B
CAN_InitStructure.CAN_TXFP = DISABLE;  // 原文注释"优先级由报文标识符决定"    ⚠校核：同上
CAN_InitStructure.CAN_Mode = mode;     // 先 CAN_Mode_LoopBack 自测
CAN_InitStructure.CAN_SJW = tsjw;  CAN_InitStructure.CAN_BS1 = tbs1;  CAN_InitStructure.CAN_BS2 = tbs2;
CAN_InitStructure.CAN_Prescaler = brp;                 // 原文注"分频系数 Fdiv 为 brp+1"
CAN_Init(CAN1, &CAN_InitStructure);                    // 库内部：置 INRQ→写 BTR→清 INRQ

CAN_FilterInitStructure.CAN_FilterNumber = 0;
CAN_FilterInitStructure.CAN_FilterMode  = CAN_FilterMode_IdMask;
CAN_FilterInitStructure.CAN_FilterScale = CAN_FilterScale_32bit;
CAN_FilterInitStructure.CAN_FilterIdHigh  = ((ext_id<<3) >> 16) & 0xffff;   // ← 扩展 ID 必须左移 3 位
CAN_FilterInitStructure.CAN_FilterIdLow   = (u16)(ext_id<<3) | CAN_ID_EXT;
CAN_FilterInitStructure.CAN_FilterMaskIdHigh = 0xffff;                       // 全 1 = 精确匹配
CAN_FilterInitStructure.CAN_FilterMaskIdLow  = 0xffff;                       // 全 0 = 全收
CAN_FilterInitStructure.CAN_FilterFIFOAssignment = CAN_Filter_FIFO0;
CAN_FilterInitStructure.CAN_FilterActivation = ENABLE;
CAN_FilterInit(&CAN_FilterInitStructure);              // 内部先置 FINIT=1 再配 FMR/FSR/FAR，最后 FINIT=0
CAN_ITConfig(CAN1, CAN_IT_FMP0, ENABLE);               // + NVIC(CAN1_RX0_IRQn)
```
**波特率算法（原文）**：`波特率 = Fpclk1 / ((tbs1+1 + tbs2+1 + 1) * brp)`
- F4（APB1=42M）：`CAN1_Mode_Init(CAN_SJW_1tq, CAN_BS2_6tq, CAN_BS1_7tq, 6, CAN_Mode_LoopBack)` ⇒ 42M/((7+6+1)×6) = **500k**
- F103（36M）：TS1=8、TS2=7、BRP=3 ⇒ 36M/((9+8+1)×3) = **500k**（原文给的是 36M/((9+8+1)×4)，注意笔误嫌疑）
用法三条硬要求：① `brp` 传给库时**库内部已 −1**（寄存器实为 0~1023）；② `TxMessage.IDE` 必须与过滤器低位
的 `CAN_ID_EXT` 一致（原文 1831 行："这里一定要设置正确，否则发送的数据不正确"）；
③ 先跑**回环模式自发自收**（掩码全 0 时任何 ID 都能进），再接总线看 `CAN_TransmitStatus`。
`⚠校核`：17c:1318 行 `CAN_InitStructure.CAN_BS1 = 13;` 是讲解性伪代码，标准库要用 `CAN_BS1_13tq` 枚举。

## 8. MODBUS RTU 帧序（原文唯一实例：睿尔曼夹爪 RS485）

来源 17d:4356~4380 | 适用：任何 Modbus RTU 主站
```
0x03 读：地址 + 0x03 + 寄存器地址(2B) + 读取数量(2B) + CRC(2B)
0x06 写单：地址 + 0x06 + 寄存器地址(2B) + 数据(2B) + CRC(2B)
0x10 写多：地址 + 0x10 + 寄存器地址(2B) + 数据量(2B) + 字节量(1B) + 数据n + CRC(2B)
```
`⚠校核 / 原文缺口`：**CRC 函数实现、构帧 C 代码、主站状态机与重试逻辑，原文一律没有**（相关表格是空的）。
CRC 参数（多项式/初值/字节序）原文未给 ⇒ 需要时另查 Modbus 规范，不要以为经验库已覆盖。
验证：读坐标模式寄存器 `0x002B` 回读比对（原文实测做法）。`<!-- 项目专有：rm_* API、寄存器 0x002B -->`

## 9. 通用易误用点汇总（原文原话，照做就少踩坑）

| # | 原文结论 | 行号 |
|---|---|---|
| 1 | TXE 中断不用时**必须失能**，否则一直进中断 | 17a:243 |
| 2 | 进 ISR 必须**标志位 + 使能位双判** | 17a:244 |
| 3 | RXNE 靠读 DR 清；ORE/IDLE 靠**先读 SR 再读 DR** | 17a:242/275 |
| 4 | **使能 DMA 前先清标志**；公司版在 `USART_Cmd` 之前清 `RXNE\|IDLE` | 17a:691/713 |
| 5 | 判"有没有数据"用 `Write_Index != Read_Index`，不用标志位 | 17a:639 |
| 6 | WK2114 `delay_us(50)` 那句"**延时比较重要**" | 17a:255 |
| 7 | 换晶振必须重算 WK2114 波特率表（原表按 11.0592MHz） | 17a:255 |
| 8 | 485 方向脚配置前要开 GPIO 时钟 | 17c:629 |
| 9 | CAN 先回环自测；`IDE` 与过滤器标志位必须一致 | 17c:1831 |
| 10 | 中断里不要 `printf`（会阻塞、会破坏 ≤5us 约束） | 17a:348/406 |
