# 定时器 / PWM / ADC / DMA（跨芯片通用原理 + STM32 实现）

> `⚠校核` 见 `ERRATA-单片机外设和调试基础知识.md`。文档里这一部分**公式正确率低**（ARR+1、倍频、转换时间），
> 用前务必回看这里的标注。

## 1. 定时器分类（STM32F4）

| 类型 | 型号 | 位数 | 通道 | 特点 |
|---|---|---|---|---|
| 高级 | TIM1、TIM8 | 16 | 4 | **互补输出 + 可编程死区 + 刹车** |
| 通用(宽) | TIM2、TIM5 | **32** | 4 | 可 DMA |
| 通用(窄) | TIM3、TIM4 | 16 | 4 | 可 DMA |
| 通用(简) | TIM9~TIM14 | 16 | 2 | 只向上计数；文档表格写"产生 DMA 请求：没有" `⚠校核C` |
| 基本 | TIM6、TIM7 | 16 | **0** | 主要用来触发 DAC |

- **H7 的分类**：基本 TIM6/7；通用 TIM2/3/4/5/12/13/14/15/16/17；高级 TIM1/8；另有 **HRTIM**（高分辨率）与 **LPTIM1~5**。
- `⚠校核C`：文档把基本定时器写成"向上、向下、向上/下"三种 —— 基本定时器一般只向上计数。

## 2. 时钟：最容易算错的一处

| 规则 | 内容 |
|---|---|
| 通用规则 | APBx 预分频 = 1 ⇒ `TIMCLK = APBx`；预分频 = 2/4/8/16 ⇒ **TIMCLK = APBx × 2** |
| F103 | 各定时器均 72MHz（APB1 分频为 1） |
| F407 | TIM1/8/9/10/11（APB2）= **168MHz**；TIM2/3/4/5/12/13/14（APB1）= **84MHz** |
| `⚠校核B` | 文档两处写"定时器 1、8 在 APB2 不用乘 2""挂载 APB2 直接 84MHz" —— **都是错的**，与同文 168MHz/PSC=167 互斥 |
| 计数频率 | `f_cnt = CK_INT / (PSC + 1)`；`⚠校核C`：文档有处写成 `72Mhz/psc+1`（漏括号，歧义） |
| GD32 / AT32 | GD32 用 `RCU_CFG1.TIMERSEL` 选 CK_APBx/2x/4x；AT32 的时钟命名是 `crm_*`（见 `mcu-chip-families/`） |

## 3. 时基、更新事件与预装载

| 项 | 内容 |
|---|---|
| 例值 | 500ms ⇒ `PSC=8399`（1MHz 计数）、`ARR=4999`；0.2ms 时基 ⇒ `PSC=16799`；0.5ms 时基 ⇒ `PSC=41999`，**"总定时时间 = (ARR+1) × 0.5ms"** |
| 捕获时间 | `TIME = ARR × 溢出次数 + val` |
| `CKD`/`tDTS` | `tDTS = Tck_tim / 2、/4`（`TIM_CKD_DIV1/2/4`）；**只影响 ETR/TIx 数字滤波、输入捕获、死区时基**，不影响计数 |
| `RCR`（重复计数器） | 8 位 0~255，**实际更新次数 = RCR + 1**（TIM1/TIM8 才有） |
| ARR 预装载 | `APRE=0` ⇒ 改 ARR 当前周期就生效；`APRE=1` ⇒ 下一周期生效。CCR 侧对应 `OCxPE`（`TIM_OCxPreloadConfig`） |

## 4. PWM

- **模式 1**：`CNT < CCR` 时输出**有效电平**；**模式 2** 相反；有效电平高低由 `OxPolarity` 决定。
- **占空比 = CCR / (ARR + 1)**。文档 ARR=19、CCR=5 ⇒ 25% 是对的；
  但同一章例题"ARR=50 ⇒ 周期 50us""CCR=10 ⇒ 高电平 1/5"、以及 `TB6612_CWFULL_VALUE = PERIOD_VALUE(=ARR)` **都漏了 +1**
  ⇒ 要真 100% 占空比，`CCR ≥ ARR+1`。`⚠校核C`
- **边沿对齐 vs 中央对齐**：中央对齐时"0 → ARR−1 → 再向下到 1"，波形对称，适合电机/开关电源。
- 死区：`DeadTime` 走 `DTG[7:0]` **分段编码，不是线性乘 t_DTS**；文档注释"100 ⇒ 100×时钟周期(约500ns)"与
  "80MHz 时每单位 12.5ns ⇒ 约1.25μs"互斥，且 `DT = DTG[7:0] × 1/(CLK/PRESCALER)` 是错的
  （死区时基是 `t_DTS`，来自 CK_INT 与 CKD，**与 PSC 无关**）。`⚠校核C`

## 5. 编码器模式（测速实用）

- `SMS`：`001` 只 TI1 计数、`010` 只 TI2、`011` **双边沿计数（计数值是实际脉冲数的 4 倍）**；只有 CH1/CH2 能用。
- `ARR=65535` + `int16_t` 转换 ⇒ 借补码直接得到正负方向值；`__HAL_TIM_IS_TIM_COUNTING_DOWN()` 0=正转 1=反转。
- **`TIM_EncoderInterfaceConfig` 必须放在 `TIM_ICInit` 之后**，否则极性会被 ICInit 覆盖回去（隐蔽 bug）。
- 测速毛刺治理：换 A/B 相序、前推霍尔、加 RC 滤波后突增消失；
  **不稳信号建议直接用定时器编码器模式（自带滤波 + 方向）**；PID 内对测量值超限加保护（超限给固定 ±10 占空比）。
- `⚠校核`：文档 ISR 里调 `delay_us(1)`，与"中断时间不要超过 5us"自相矛盾。

## 6. 定时器级联 / 重映射坑

- 内部触发 `ITRx` = **"把一个定时器当另一个的预分频器"**；`TRGO`=Reset 可作同步源（也可给 ADC/DMA 触发）；`MSM` 可禁用主从模式。
- **F1 重映射坑**：`GPIO_FullRemap_TIM2` 会把 CH3/CH4 移到 PB10/PB11 ⇒ **USART3 失效**；
  改 `PartialRemap1` 或不重映射。F1 TIM3 部分重映射宏 `__HAL_AFIO_REMAP_TIM3_PARTIAL()` **在 F4 不存在，要删**。
- HAL 生成坑：PWM 必须走 `HAL_TIM_PWM_MspInit`（CubeMX 可能误生成 `Base_MspInit`）+ `HAL_TIM_MspPostInit` 配引脚；
  生成的代码常**缺 `HAL_TIM_PWM_Start`**。`htim->State == RESET` 才会调 `PWM_MspInit`。

## 7. ADC

| 项 | 内容 | 范围 |
|---|---|---|
| 电压换算 | `实际电压 = (ADC值/4096) × 3.3`；精度 `3300mV/4095 ≈ 0.8mV` | 12 位通用 |
| 工程量线性化 | `Ov = (Osh−Osl)×(Iv−Isl)/(Ish−Isl) + Osl`；4–20mA ↔ 6400–32000、0–10V ↔ 0–32000 | 通用(PLC 习惯) |
| 转换时间 | **F1：`TCONV = 采样时间 + 12.5 周期`**；ADCCLK=14M、采样 1.5 周期 ⇒ 14 周期 = 1μs；72M/6=12M、239.5+12.5=252 ⇒ 21μs。`⚠校核C`：文档把此式沿用到 F4/H7（**F4/H7 固定周期数随分辨率变化**，且 F4 公式表在原文是空表） | F1 |
| 时钟上限 | "不要让 ADC 时钟超过 14M"（F1）；F4 `ADCCLK = PCLK2/4 = 84/4 = 21MHz`、"最好不要超过 36MHz"；H743 同写 36M | F1/F4/H7 |
| 采样时间 | `SMP[2:0]`（`ADC_SMPR1/SMPR2`），**每通道可不同**；F1 最长 `ADC_SAMPLETIME_239CYCLES_5`；文档 F4 段出现 `ADC_SampleTime_480Cycles` | F1/F4 |
| 通道 | F103 有 3 个 12 位 ADC；"多达 18 个通道 = 16 外部 + 2 内部"；**VREFINT 在 ADC1 通道 17**；规则序列 `NbrOfConversion` 1~16，Rank 超出则不转换；F4 可选 12/10/8/6 位。`⚠校核C`：同文又写"F1 21 个 / F4 24 个通道"，口径不一致 | F1/F4 |
| 模式 | 单次/连续/扫描/间断；**要用 ADC+DMA 必须先使能连续转换模式**；Continuous 与 Discontinuous 不可共存 | 通用 |
| 触发 | F1 外部触发源例：`ADC_ExternalTrigConv_T1_CC1 / T1_CC2 / T2_CC2 / T3_T / T4_CC4`（→ 用定时器触发采样是标准做法）；软件触发需 `ADC_SoftwareStartConvCmd` | F1 |
| 引脚映射 | PC4→ADC1_IN14；PA6→ADC1_Channel_6；PA5→ADC1 通道 5；F407：PC2→ADC123_IN12、PC3→ADC123_IN13；**H743：PC3→ADC12_INP13，而 `PC3_C`→ADC3_INP1**；`_C` 后缀（PA0_C/PA1_C/PC2_C/PC3_C）与 Pxy 是**两个独立焊盘**，由 SYSCFG 模拟开关选择 ⇒ 引脚表要分型号抄 | F1/F4/H7 |
| DMA 配合 | `hdma_adc1.Instance = DMA1_Channel1`；`PINC_DISABLE / MINC_ENABLE`、半字(HALFWORD)、`DMA_CIRCULAR`；**"先做 DMA 初始化，再做 ADC 初始化"**；`HAL_ADC_Start_DMA(&hadc1,(uint32_t*)buf,64)` | F1 |
| 校准 | `HAL_ADCEx_Calibration_Start(&hadc1)`；标准库：ResetCalibration→等→StartCalibration→等（**F1 的 HAL 没有这个校准**） | F4 |
| 硬件稳定性 | 引脚对 GND 跨 1uF 电容；软件用中位值平均滤波；`2.4V ≤ VDDA ≤ VDD(3.6V)`、`2.4V ≤ VREF+ ≤ VDDA`、`VREF− = VSSA`、`VREF− ≤ VIN ≤ VREF+` | 通用 |
| **结构体未清零的连锁坑** | RT-Thread + 标准库：结构体没 `={0}` ⇒ `ADC_ExternalTrigConv` 是垃圾值 ⇒ `CR2` 配错 ⇒ **EOC 永不置位、SR 里 OVR 一直有**；对策：赋初值或逐成员赋值，读 EOC 前先清 OVR | F4 |
| ⚠ 循环 DMA 读值 | 文档的滤波函数注释"获取一个通道的所有数据"，但 `DMA_CIRCULAR` + 64 缓冲**没挂半传/全传回调** ⇒ 读到的是新旧混合数据，且数组长度与宏不一致有越界风险 | 代码级隐患 |

## 8. DMA

### 基础约束（F1/F4）
- 传输量寄存器 `DMA_CNDTRx` / `DMA_SxNDTR` 是 **16 位 ⇒ 最大 65535**；**NDTR=0 时即使使能也无事务、无完成中断**。
- **发送长度不得为 0（会卡死）**；DMA 未传完**不得改动发送缓存**；发送前用信号量等上一次 TC。
- 外设地址不增（`DMA_PeripheralInc_Disable`）、内存地址增；Normal 模式传完 CNDTR 清零并停止，
  **重载前必须先关 DMA 通道**。

### F1 vs F4 结构差异（移植时最费时间）
| 项 | F1 | F4 |
|---|---|---|
| 组织 | DMA1/DMA2 × 固定 **通道 Channel1~7/8** | DMA1/DMA2 × **8 Stream**，每 Stream 用 `CHSEL[2:0]`（SxCR 位 27:25）选 8 个请求通道 |
| 映射示例 | ADC1→`DMA1_Channel1`；串口例用 DMA1_Ch5/6/3 | USART1_TX=`DMA2_Stream7+Ch4`、USART1_RX=`DMA2_Stream5+Ch4`、SPI1_RX=Stream0/2+Ch3、DCMI=`DMA2_Stream1+Ch1`、SDIO=`DMA2_Stream3+Ch4` |
| 规则 | 通道固定绑定外设 | 一个 Stream 同一时刻只能配一个 Channel；同一外设可出现在多个 (Stream,Ch) 组合，选定即独占该 Stream |
| 双缓冲 | **不支持** | 支持（`DBM`/`CT` 位 19 指示当前目标是 M0AR/M1AR，**只对存储器侧双缓冲**；回调 `XferM1CpltCallback`） |
| 存储器到存储器 | — | **仅 DMA2**；禁循环模式与直接模式（FIFO 必开）；`PFCTRL` 被硬件强制 0（DMA 恒为流控制器）；CubeMX 里 Channel 可任选，PeriphInc 对应源、MemInc 对应目标 |
| 优先级 | 软件 4 级（VeryHigh/High/Medium/Low）+ 同级按通道号小者优先；大容量/互联型 **DMA1 优先于 DMA2** | 按流/请求编号 |

### 标志与使能顺序（**硬规矩**）
- 5 个标志：`HTIF / TCIF / TEIF / FEIF / DMEIF`；使能位 `HTIE/TCIE/TEIE/DMEIE`(SxCR) + `FEIE`(SxFCR)。
- 清除方式：**写 1 到 `DMA_LIFCR` / `DMA_HIFCR`**。
- **"EN 置 1 之前必须先清掉对应事件标志，否则 DMA 无法使能"** —— 与串口那节呼应。
- HAL：`__HAL_DMA_ENABLE_IT` / `__HAL_DMA_CLEAR_FLAG`；标志成对定义 `DMA_FLAG_TCIF0_4 … TCIF3_7`；
  `HAL_DMA_IRQHandler` 按 `StreamIndex` 移位，abort 时写 `regs->IFCR = 0x3FU<<StreamIndex`；
  TE 错误时轮询等 EN 清零（`timeout = SystemCoreClock/9600`）；`__HAL_LINKDMA` 绑定 `Parent`；
  **该版 HAL 在 `USE_RTOS=1` 时直接 `#error`**，多任务要自己加信号量。

### FIFO / 突发 / 数据宽度（F4）
- 每 Stream 独立 **4 字(4×32bit) FIFO**；阈值 `FTH[1:0]` = 1/4、1/2、3/4、满；`DMDIS=1` 才使能 FIFO。
- **FIFO 阈值内容必须等于整数个"存储器突发"**，否则一开流就 `FEIFx` 并自动关流。
- `MBURST(位24:23)/PBURST(位22:21)` = INCR4/8/16；**仅指针递增(PINC/MINC=1)时才允许**；
  不得跨 1KB 边界，且产生 AHB 错误时 DMA **不报错**（隐蔽）。直接模式只能单次。
- 循环模式 + 存储器突发：`NDTR` 必须是 `(Mburst节拍 × Msize / Psize)` 的倍数，
  还须是"外设突发 × 外设数据宽度"乘积的倍数。
- `PSIZE/MSIZE` 字节/半字/字；**源目标宽度不等时的自动打包拆包只有 FIFO 模式可用**；
  地址须按宽度对齐；直接模式下 `MSIZE` 被硬件强制等于 `PSIZE`。
- 外设流控制器（`PFCTRL=1`）只有 SDIO 等能发结束信号的外设可用；使能后 `NDTR` 只读且被强制 0xFFFF，
  **已传输数 = 0xFFFF − NDTR**；外设流控下禁止循环模式。
- `⚠校核C`：文档把"一个字 32 位"写成"32 字节"；`USARTx_RX` 映射写成 DMA1（实为 DMA2）；位名 `FEIO` 应为 `FEIE`；
  "循环模式不会触发 FDT 中断"（另有 AI 段落误述）；`PBURST 在外设→存储器没有作用`（不准确）。

### H7 的额外一条
**DMA 不能访问 DTCM**；请求号改走 **DMAMUX**（`Init.Request = DMA_REQUEST_DCMI`，不再用 `CHSEL`）；
缓存一致性见 `sd-card-dcmi-fsmc-sram.md` §4。

## 9. 一句话记忆表

| 忘了就查这句 |
|---|
| 定时器时钟：APB 分频≠1 就 **×2**；`f_cnt = CK_INT/(PSC+1)`，`定时 = (ARR+1)/f_cnt` |
| PWM 占空比 **= CCR/(ARR+1)**，100% 要 CCR ≥ ARR+1 |
| 编码器：**双边沿模式计数是实际值的 4 倍**；`EncoderInterfaceConfig` 放最后 |
| ADC+DMA：**先开连续模式**，DMA 初始化早于 ADC，F1 用 DMA1_Channel1 |
| DMA：**EN 之前清标志**；NDTR 不能为 0；**最大 65535** |
| F4 找 DMA 通道：先查"Stream + Channel"映射表，别按 F1 的通道号想当然 |
