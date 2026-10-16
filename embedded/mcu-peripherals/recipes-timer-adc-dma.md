# 代码配方：定时器 / ADC / DMA（照抄原文 + 用法 + 验证）

> 配套 `timer-pwm-adc-dma.md`。行号指原文导出文本位置；`⚠校核` = 原文可疑处保留原样；
> `原文无代码` = 只有文字/图，不要当已有依据。

## 1. 定时器

### 1.1 时基与算式
`定时时间 = (ARR+1) × (PSC+1) / Tclk`；原文实测填法（18:330-335，F1/F4 标准库）：
```c
TIM_TimeBaseInitStruct.TIM_Prescaler = psc;
TIM_TimeBaseInitStruct.TIM_Period    = arr;      // 原文强调："输入参数时要减一"
```
档位对照：84MHz 下 `0.1ms ⇒ PSC=8399`、`0.2ms ⇒ PSC=16799`、`0.5ms 时基 ⇒ PSC=41999`，总时间 = `(ARR+1)×0.5ms`。
CubeMX 生成的裸时基（18:187，F4 HAL）：
```c
htim2.Instance = TIM2;  htim2.Init.Prescaler = 0;  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
htim2.Init.Period = 4294967295;                   // 32 位定时器满量程
htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;   // ← 与"APRE=1 下一周期生效"对应关系要留意
if (HAL_TIM_Base_Init(&htim2) != HAL_OK) Error_Handler();
```
`⚠校核`：18:341 注释 `Tout=(MOTOR_PWM_MAX*(Prescaler+1))/Ft` 中 `MOTOR_PWM_MAX` 漏了 +1
（Period 已写 `MOTOR_PWM_MAX-1`，故应为 `(Period+1)`）。
验证：示波器量输出脚周期（原文实测 120us 与波形吻合）；`RCC_GetClocksFreq()`/`HAL_RCC_GetPCLK1Freq()` 确认定时器时钟是 ×1 还是 ×2。

### 1.2 PWM 输出：**顺序 + CubeMX 常漏的两处**
调用顺序（缺一步就"配了没波"）：
`HAL_TIM_Base_Init → ConfigClockSource → HAL_TIM_PWM_Init → MasterConfigSynchronization →
HAL_TIM_PWM_ConfigChannel(×N) → ConfigBreakDeadTime → HAL_TIM_MspPostInit(配引脚) → HAL_TIM_PWM_Start`
```c
/* 来源 18:1638 */
sConfigOC.OCMode = TIM_OCMODE_PWM1;      // 模式1：CNT<CCR 输出有效电平
sConfigOC.Pulse  = 0;
sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1);
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);                    // ← CubeMX 不生成，必须手补
__HAL_TIM_SET_COMPARE(&htim1, motor_channel[number], speed); // ← 运行中只改这个
```
```c
/* 来源 18:722-725：CubeMX 生成代码里缺失、需手补 */
HAL_GPIO_WritePin(GPIOE, GPIO_PIN_7, GPIO_PIN_SET);
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
```
标准库对应（18:378-384）：`TIM_OCMode_PWM1` + `TIM_OCPolarity_High` + `TIM_OC3PreloadConfig(...,TIM_OCPreload_Enable)`
+ `TIM_SetCompare3(...)` —— **三个函数的通道号必须配套**（OC3 就都用 3）。
占空比：`占空比 = CCR/(ARR+1)`；**要 100% 需 CCR ≥ ARR+1**（`⚠校核` 见主题篇 §4）。

### 1.3 输入捕获
`原文无独立测频/测宽完整骨架`，只有 IC 初始化形态（18:1266）：
```c
TIM_ICInitStructure.TIM_Channel  = TIM_Channel_2;
TIM_ICInitStructure.TIM_ICFilter = 0xF;            // ← 滤波拉满抗抖动
TIM_ICInit(ENCODER_TIM, &TIM_ICInitStructure);
```
用法：配合 `TIM_GetCaptureX()` + 更新中断计溢出次数，算式即 `TIME = ARR×溢出次数 + val`。

### 1.4 编码器模式（**函数顺序是关键**）
F1 标准库（18:1257/1266/1285-1292）：
```c
TIM_TimeBaseStructure.TIM_Prescaler     = 0;
TIM_TimeBaseStructure.TIM_CounterMode   = TIM_CounterMode_Up;
TIM_TimeBaseStructure.TIM_Period        = 65535;      // ← 借补码直接得正负
TIM_TimeBaseStructure.TIM_ClockDivision = TIM_CKD_DIV1;
TIM_TimeBaseInit(ENCODER_TIM, &TIM_TimeBaseStructure);
TIM_ICStructInit(&TIM_ICInitStructure);
TIM_ICInitStructure.TIM_Channel  = TIM_Channel_2;
TIM_ICInitStructure.TIM_ICFilter = 0xF;
TIM_ICInit(ENCODER_TIM, &TIM_ICInitStructure);
TIM_EncoderInterfaceConfig(ENCODER_TIM, TIM_EncoderMode_TI2,
                           TIM_ICPolarity_Rising, TIM_ICPolarity_BothEdge);   // ← ⑤必须放最后
TIM_Cmd(ENCODER_TIM, ENABLE);
```
原文注（18:1288）：**"一定要把这个函数放在 ICInit 下面，保证能够把 ICInit 配置的极性覆盖"**。
读值（18:1294-1300）：
```c
int16_t Encoder_Get(void){ int16_t t = TIM_GetCounter(TIM3); TIM_SetCounter(TIM3, 0); return t; }
/* HAL 版： pluse[n] = (int16_t)__HAL_TIM_GET_COUNTER(&htim3); __HAL_TIM_SET_COUNTER(&htim3,0); */
```
HAL 初始化：`TIM_Encoder_InitTypeDef{ EncoderMode = TIM_ENCODERMODE_TI12; IC1Filter = 15; ... }`
+ `HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL)`（18:1586）。
要点：**只有 CH1/CH2 能用**；TI12 双边沿时**计数是实际脉冲数的 4 倍 ⇒ 要 /4**（18:1366）；
方向判据 `__HAL_TIM_IS_TIM_COUNTING_DOWN()`。
`<!-- 项目专有 -->` xcar 四电机 `pluse[]` + 增量式 PID（超限给固定 ±10 占空比）是该工程做法，别当通用。

### 1.5 级联与触发同步
`ITRx` = "把一个定时器当另一个的预分频器"（18:102/242）；
主片 `sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;`（UG 位产生脉冲）、`MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE`
（原文 437-443：MSM 禁用即各自独立）。典型用途：**PWM 周期起点触发 ADC 采样**、以及给 DMA/ADC 提供同步 TRGO。

### 1.6 F1 重映射坑（真实事故）
```c
/* 来源 18:1415/1420 */
GPIO_PinRemapConfig(GPIO_PartialRemap2_TIM2, ENABLE);  // CH3/CH4 落到 PB10/PB11 → USART3 失效
GPIO_PinRemapConfig(GPIO_PartialRemap1_TIM2, ENABLE);  // ← 正确：用 PartialRemap1 或不重映射
```
另：F1 的 `__HAL_AFIO_REMAP_TIM3_PARTIAL()` 在 **F4 不存在，移植要删**（15:424 区）。

## 2. ADC

### 2.1 F1 标准库 ADC + DMA 连续采集（完整序列，19:322）
```c
RCC_APB2PeriphClockCmd(RCC_APB2Periph_ADC1 | RCC_APB2Periph_GPIOA, ENABLE);
RCC_ADCCLKConfig(RCC_PCLK2_Div6);                       // 72/6 = 12MHz（勿超 14MHz）
GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AIN; GPIO_Init(GPIOA, &GPIO_InitStructure);
ADC_DeInit(ADC1);
ADC_InitStructure.ADC_Mode = ADC_Mode_Independent;
ADC_InitStructure.ADC_ScanConvMode      = DISABLE;       // 单通道 DISABLE、多通道 ENABLE
ADC_InitStructure.ADC_ContinuousConvMode= ENABLE;        // ← 用 DMA 必须连续模式
ADC_InitStructure.ADC_ExternalTrigConv  = ADC_ExternalTrigConv_None;
ADC_InitStructure.ADC_DataAlign = ADC_DataAlign_Right;
ADC_InitStructure.ADC_NbrOfChannel = 1;                  // 多通道时 = 通道数；Rank 超出则不转换
ADC_Init(ADC1, &ADC_InitStructure);
ADC_RegularChannelConfig(ADC1, ADC_Channel_5, 1, ADC_SampleTime_239Cycles5);
ADC_DMACmd(ADC1, ENABLE);                                // ← 先挂 DMA 命令
ADC_Cmd(ADC1, ENABLE);
ADC_ResetCalibration(ADC1); while(ADC_GetResetCalibrationStatus(ADC1));   // 校准两步
ADC_StartCalibration(ADC1); while(ADC_GetCalibrationStatus(ADC1));
ADC_SoftwareStartConvCmd(ADC1, ENABLE);
```
DMA 侧（19:322）方向是 `DMA_DIR_PeripheralSRC`（外设→内存），`DMA_PeripheralInc_Disable` +
`DMA_MemoryInc_Enable` + `HalfWord` + `DMA_Mode_Circular`，通道 `DMA1_Channel1`（ADC1）。
**HAL 版顺序铁律**（19:304/375）：
```c
MX_DMA_Init();      // ← 先 DMA
MX_ADC1_Init();     // 再 ADC
HAL_ADCEx_Calibration_Start(&hadc1);
HAL_ADC_Start_DMA(&hadc1, (uint32_t*)ADCConvertedValue, 64);
/* MspInit 里必须： __HAL_LINKDMA(hadc, DMA_Handle, hdma_adc1);  */   // 19:270
```
多通道：`ScanConvMode = ENABLE`、`NbrOfConversion = n`、每通道 `sConfig.Rank = ADC_REGULAR_RANK_1..n`。

### 2.2 内部通道与采样时间实算
```c
ADC_TempSensorVrefintCmd(ENABLE);    // 温度=通道16、VREFINT=通道17（F1）
/* 换算需 datasheet 校准值，原文无公式代码 */
/* 采样+转换时间实算（19:247-251）：12MHz 下 239.5+12.5 = 252 周期 ⇒ 21us */
```
F4：`ADC_Prescaler_Div4 ⇒ ADCCLK = 84/4 = 21MHz`（19:581，勿超 36MHz）。
`⚠校核`：19:122 "采样时间=（采样周期+12.5周期）1/ADC时钟频率" 缺乘号；19:141 把"最大 1MHz / 上限 14MHz"混写；
**12.5 周期这个式子是 F1 的，F4/H7 随分辨率不同**（原文对应表格为空）。

### 2.3 结构体未清零 → EOC 不来、OVR 常置（真实事故）
```c
/* 出错写法 */ ADC_InitTypeDef ADC_InitStructure;            // 没初始化 ⇒ ADC_ExternalTrigConv 是垃圾值
/* ⇒ CR2 配错 ⇒ 触发被解释成外部触发 ⇒ EOC 永不置位、SR 里 OVR 一直有、AdcGet 超时返 0 */
/* 修正写法（二选一，19:467-475） */
ADC_InitTypeDef ADC_InitStructure = {0};                      // ①清零
/* ②或每个成员都显式赋值 */
/* 清 OVR（19:488，ADC_ClearFlag 源码）： */ ADCx->SR = ~(uint32_t)ADC_FLAG;
/* 原文注："应该是 ADCx->SR &= ~(uint32_t)ADC_FLAG；不过状态位…这样写也是可以的" */
```
配套硬件/软件稳定性（原文）：引脚对 GND 跨 1µF；软件用中位值平均滤波；
`2.4V ≤ VDDA ≤ VDD`、`2.4V ≤ VREF+ ≤ VDDA`、`VREF− = VSSA`、`VREF− ≤ VIN ≤ VREF+`。
`⚠校核`：文档的 DMA 循环采集**没有挂半传/全传回调** ⇒ 读到的是新旧混合数据，且数组长度与宏不一致有越界风险。

## 3. DMA

### 3.1 F1 `DMA_Init` 全字段（20:378）
```c
DMA_InitStructure.DMA_PeripheralBaseAddr = USART1_DR_Base;
DMA_InitStructure.DMA_MemoryBaseAddr     = (uint32_t)SendBuff;
DMA_InitStructure.DMA_DIR                = DMA_DIR_PeripheralDST;   // 发送方向
DMA_InitStructure.DMA_BufferSize         = 500;
DMA_InitStructure.DMA_PeripheralInc      = DMA_PeripheralInc_Disable;   // ← 外设地址不增
DMA_InitStructure.DMA_MemoryInc          = DMA_MemoryInc_Enable;
DMA_InitStructure.DMA_PeripheralDataSize = DMA_PeripheralDataSize_Byte;
DMA_InitStructure.DMA_MemoryDataSize     = DMA_MemoryDataSize_Byte;
DMA_InitStructure.DMA_Mode               = DMA_Mode_Normal;             // 循环采集用 DMA_Mode_Circular
DMA_InitStructure.DMA_Priority           = DMA_Priority_Medium;
DMA_InitStructure.DMA_M2M                = DMA_M2M_Disable;             // ← 存储器到存储器才置 ENABLE
DMA_Init(DMA1_Channel4, &DMA_InitStructure);
DMA_Cmd(DMA1_Channel4, ENABLE);
DMA_ITConfig(DMA1_Channel4, DMA_IT_TC, ENABLE);
```
`⚠校核`：20:433 "一个字认为是 32 字节、半字 16 字节" ⇒ 单位应为**位**。

### 3.2 F4 Stream + CHSEL + LINKDMA（20:1135/1142；HAL 20:2141）
```c
while (DMA_GetCmdStatus(DMA2_Stream3) != DISABLE){}   // ← 等流真正停下来才能配
DMA_DeInit(DMA2_Stream3);
DMA_InitStructure.DMA_Channel            = DMA_Channel_4;      // ← CHSEL[2:0]，SxCR 位 27:25
DMA_InitStructure.DMA_PeripheralBaseAddr = (u32)&SDIO->FIFO;
DMA_InitStructure.DMA_Memory0BaseAddr    = (u32)mbuf;
DMA_InitStructure.DMA_DIR                = dir;
DMA_InitStructure.DMA_BufferSize         = 0;                  // ← 0 不传输，必须先设值再使能
DMA_InitStructure.DMA_Mode               = DMA_Mode_Normal;   // 双缓冲/连续见 §3.5
DMA_InitStructure.DMA_Priority           = DMA_Priority_VeryHigh;
DMA_InitStructure.DMA_FIFOMode           = DMA_FIFOMode_Enable;
DMA_InitStructure.DMA_MemoryBurst        = DMA_MemoryBurst_INC4;
DMA_InitStructure.DMA_PeripheralBurst    = DMA_PeripheralBurst_INC4;
DMA_Init(DMA2_Stream3, &DMA_InitStructure);
/* HAL： */ hdma.Init.Channel = DMA_CHANNEL_4;  HAL_DMA_Init(&hdma);
           __HAL_LINKDMA(huart, hdmarx, hdma_uart_rx);   // 绑到外设句柄
```
`⚠校核`：20:2198 `Init.MemBurst = DMA_PBURST_SINGLE;` 用 PBURST 宏去配 MemBurst（原文如此）；
"当 PINC=0 时应把 PBURST 清 00"只在 FIFO 模式下才有意义。

### 3.3 循环模式"已收多少"的算法（20:421/425）
```c
Write_Index = (RINGBUF_SIZE - DMA_GetCurrDataCounter(STREAM)) % RINGBUF_SIZE;   // IDLE/半满中断里更新
*(pdata + i) = ringbuf[(Read_Index + i) % RINGBUF_SIZE];
Read_Index   = (Read_Index + length) % RINGBUF_SIZE;
```

### 3.4 正常模式重发的**正确顺序**（20:27/1231，最常被写反）
```c
DMA_ClearFlag(STREAM, DMA_FLAG_TCIF7|DMA_FLAG_FEIF7|DMA_FLAG_DMEIF7|DMA_FLAG_TEIF7|DMA_FLAG_HTIF7);
DMA_Cmd(STREAM, DISABLE);                        // ← 原文顺序是先清标志再关；见下方校核
DMA_SetCurrDataCounter(STREAM, len);
memcpy(CLI_DMA_SendBuff, str, len);              // ← 未传完不得改动发送缓存
DMA_Cmd(STREAM, ENABLE);
/* 中断里同款： DMA_ClearITPendingBit → DMA_SetCurrDataCounter → DMA_Cmd(ENABLE) */
```
`⚠校核`：原文另一处（20:227 附近）顺序是 `DISABLE → ClearFlag → SetCurrDataCounter → ENABLE`，
**流还忙时先清标志可能立刻又被置位** ⇒ 采用"先 DISABLE、确认停了、再清标志"更稳。
配套铁律：**发送长度不得为 0**（会卡死）；发送前用信号量等上一次 TC；
**EN 置 1 前必须先清事件标志，否则 DMA 根本使能不了**。

### 3.5 双缓冲（F4/H7，DCMI 例）
```c
HAL_DMAEx_MultiBufferStart(&hdma, (uint32_t)&DCMI->DR, mem0addr, mem1addr, memsize);
__HAL_DMA_ENABLE_IT(&hdma, DMA_IT_TC);
/* 判 CT 位决定当前半区： */
if (DMA1_Stream1->CR & (1<<19)) { /* 正在写 buf1，可处理 buf0 */ } else { /* 反之 */ }
/* 或用 XferHalfCpltCallback / XferCpltCallback 分别处理 M0/M1 */
```
（F1 无 DBM；标准库版是 `DMA_DoubleBufferModeConfig/DMA_DoubleBufferModeCmd`，见 I2S 例 §4。）

### 3.6 H7 的 cache 维护位置（唯一原文实例）
```c
/* 来源 20:2198：DCMI 收数据回调里 */
dcmi_data_len += Dma_MultiBuffer_size;
SCB_CleanInvalidateDCache();       // 原文注："如果不清理缓存，图像数据会出现乱码"
```
⇒ 方向性总结：**DMA 写内存 → CPU 读之前**清+无效化；**CPU 写内存 → 让 DMA 发送之前**应做 clean
（原文没有这段代码，属我给出的推论，需自查：用 `SCB_CleanDCache_by_Addr` 或把缓冲设 Non-cacheable）。
另：**H7 的 DMA 不能访问 DTCM ⇒ 双缓冲 buf 不要放 DTCM**（20:2202）。

## 4. 播放通路示例：I2S + DMA 双缓冲（与 `audio-i2s-wav.md` 配对）

```c
/* 来源 17d:4275/4332/4286，F4 */
I2S2_TX_DMA_Init(buf0, buf1, num);     // DMA1_Stream4/Channel_0、&SPI2->DR、HalfWord、DMA_Mode_Circular
DMA_DoubleBufferModeConfig(stream, buf1, DMA_Memory_0);
DMA_DoubleBufferModeCmd(ENABLE);
DMA_ITConfig(DMA1_Stream4, DMA_IT_TC, ENABLE);
/* 播放链 */
wav_decode_init();                       // 解析头，算 ByteRate = 采样率×通道×(位深/8)
I2S2_SampleRate_Set(wavctrl.samplerate); // 查表设 PLLI2SN/R/I2SDIV/ODD
i2s_tx_callback = wav_i2s_dma_tx_callback;
f_open(...); f_lseek(file, wavctrl.datastart);
wav_buffill(); wav_buffill();             // 先把两块缓冲都填满
while (wavtransferend == 0);              // 等中断
/* 回调里按 CT 位决定填哪块： */
if (DMA1_Stream4->CR & (1<<19)) { wavwitchbuf = 0; /* 可填 buf1 */ } else { wavwitchbuf = 1; }
wavtransferend = 1;                        // 暂停时填 0
```
24bit 素材要转成 32bit 帧存（`wav_buffill`，17d:4338）。

## 5. 验证清单（每次改完按这个顺序确认）

| 目标 | 验证动作 |
|---|---|
| 定时器周期对不对 | 示波器量输出脚；或读 `CNT/ARR` 反算 |
| PWM 占空比 | 量高电平时间；怀疑 `ARR+1` 就把 ARR 改成已知值反推 |
| 编码器方向 | 手转一下看 `int16` 正负是否稳定；不对就换 TI1/TI2 或极性 |
| ADC 值 | 万用表量引脚电压，比对 `值×3.3/4096` |
| EOC 不来 | 先查 `SR` 的 OVR、再查结构体有没有清零 |
| DMA 不动 | 仿真看 `NDTR/CNDTR` 是否递减；查是否先清了标志、长度是否非 0 |
| H7 数据乱 | 先怀疑 cache，把缓冲设 Non-cacheable 复测 |
