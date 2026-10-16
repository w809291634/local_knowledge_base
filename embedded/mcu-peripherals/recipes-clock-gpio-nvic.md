# 代码配方：时钟 / SysTick / GPIO / NVIC / EXTI（照抄原文）

> 配套 `clock-gpio-nvic-exti.md`。`⚠校核` = 原文可疑处保留原样；`原文无代码` = 只有文字/截图，**不要当已有依据**。

## 1. 改晶振必改的两处宏（"时钟数不对"的头号原因）

```c
// ① stm32f10x.h —— 晶振频率
#define HSE_VALUE       ((uint32_t)8000000)     // ← 按实际晶振改（默认 8M；CL 版为 25M）
// ② system_stm32f10x.c —— 目标主频档位（只保留一个 #define 生效）
#define SYSCLK_FREQ_72MHz  72000000
```
来源 14:38/44 | 适用 F1 标准外设库。
F4 同理：`stm32f4xx.h` 的 `HSE_VALUE`（**库默认 25000000**，14:79-82）+ `system_stm32f4xx.c` 的档位宏。
验证：`RCC_GetClocksFreq()`（**用结构体变量，不要传野指针**，14:186-190）读回 SYSCLK/HCLK/PCLK1/PCLK2；
或 **MCO = PA8** 输出给示波器量（14:23）；H7 上 MCO1=PA8、MCO2=PC9。

`原文无代码`：F1 `SetSysClockTo72` 的函数体（`RCC->CFGR` 写法、`CR_HSERDY` 等待、`PLLMul`、`FLASH_ACR` latency）
**不在这四份切片里**，只有一句 `void RCC_SYSCLKConfig(uint32_t RCC_SYSCLKSource)` 原型（14:106）。
可确认的顺序是：*使能 HSE → 等稳定 → 配 PLL → 等 PLL 锁定 → 切 SYSCLK 源 → 配分频*。**补齐要看 system_stm32f10x.c 原文，不要凭这段编。**

## 2. F4 的 PLL 组装（照抄）
```c
#define PLL_M   8      // HSE 预分频：填晶振的 MHz 数
#define PLL_N   336    // 倍频
#define PLL_P   2      // 168M = HSE/M*N/P
#define PLL_Q   7      // USB/SDIO：480M/Q = 48M  ← 关键
RCC->PLLCFGR = PLL_M | (PLL_N << 6) | (((PLL_P >> 1) - 1) << 16) |
               (RCC_PLLCFGR_PLLSRC_HSE) | (PLL_Q << 24);
```
来源 14:69-76 | 适用 F4。
`SystemInit` 先开 HSI（`CFGR` 复位低 2 位 = 00），`SetSysClock` 再切 HSE + PLL。

## 3. H7 时钟配置（完整顺序，一步都不能换）
```c
MODIFY_REG(PWR->CR3, PWR_CR3_SCUEN, 0);                          // ← 允许改供电配置
__HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);   // ← VOS1
while ((PWR->D3CR & (PWR_D3CR_VOSRDY)) != PWR_D3CR_VOSRDY){}     // ← 等电压就绪
rcc_osc_init_handle.OscillatorType = RCC_OSCILLATORTYPE_HSE | RCC_OSCILLATORTYPE_HSI48;
rcc_osc_init_handle.HSEState = RCC_HSE_ON;   rcc_osc_init_handle.HSI48State = RCC_HSI48_ON;
rcc_osc_init_handle.PLL.PLLState = RCC_PLL_ON;
rcc_osc_init_handle.PLL.PLLSource = RCC_PLLSOURCE_HSE;
rcc_osc_init_handle.PLL.PLLN = plln;  rcc_osc_init_handle.PLL.PLLM = pllm;
rcc_osc_init_handle.PLL.PLLP = pllp;  rcc_osc_init_handle.PLL.PLLQ = pllq;
rcc_osc_init_handle.PLL.PLLVCOSEL = RCC_PLL1VCOWIDE;
rcc_osc_init_handle.PLL.PLLRGE = RCC_PLL1VCIRANGE_2;
ret = HAL_RCC_OscConfig(&rcc_osc_init_handle);                   // ← 先 Osc 后 Clock
rcc_clk_init_handle.ClockType = RCC_CLOCKTYPE_SYSCLK | RCC_CLOCKTYPE_HCLK |
        RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2 | RCC_CLOCKTYPE_D1PCLK1 | RCC_CLOCKTYPE_D3PCLK1;
rcc_clk_init_handle.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
rcc_clk_init_handle.SYSCLKDivider  = RCC_SYSCLK_DIV1;
rcc_clk_init_handle.AHBCLKDivider  = RCC_HCLK_DIV2;             // 400M → HCLK 200M
rcc_clk_init_handle.APB1CLKDivider = RCC_APB1_DIV2;              // APB2/3/4 同
ret = HAL_RCC_ClockConfig(&rcc_clk_init_handle, FLASH_LATENCY_2); // ← 带 FLASH 等待周期
HAL_PWREx_EnableUSBVoltageDetector();  __HAL_RCC_CSI_ENABLE();
__HAL_RCC_SYSCFG_CLK_ENABLE();         HAL_EnableCompensationCell();
```
来源 14:141（表 2676） | 适用 H743 HAL。
25M 晶振推荐 `plln=160, pllm=5, pllp=2, pllq=4` ⇒ `Fvco=800M、Fsys=400M、Fq=200M`。
`⚠校核`：`FLASH_LATENCY_2` 是原文值 —— 400MHz 下是否合规需查 H743 手册的 VOS1 频率-等待周期表；
原文同处注释称"SysTick=400MHz"而 HCLK 实为 200MHz，**不自洽，别照抄结论**。

## 4. SysTick

### 寄存器（14:228）
```
STK_CSR   0xE000E010  控制    STK_LOAD  0xE000E014  重载
STK_VAL   0xE000E018  当前值  STK_CALRB 0xE000E01C  校准
```
`⚠校核`：`STK_CALRB` 拼写应为 **`STK_CALIB`**。位定义：`ENABLE=1<<0`、`INT=1<<1`、`CLK=1<<2`、`COUNTFLAG=1<<16`。

### `SysTick_CLKSourceConfig` 与 `SysTick_Config` 的关系（**重复减一**就在这）
- `SysTick_CLKSourceConfig()`（misc.c）选时钟源：HCLK 或 HCLK/8；
- `SysTick_Config(ticks)`（core_cmX.h）配置并开中断，**内部已经做 `ticks-1`**。
```c
/* 原文"最终版本"（14:281/290）—— 外层又减了一次 ⇒ LOAD 少 2，周期偏短 ⚠校核 */
uint32_t reloadValue = (SystemCoreClock / SYSTICK_FREQ_HZ) - 1;
SysTick_Config(reloadValue);
/* 正确写法：直接传 SystemCoreClock / SYSTICK_FREQ_HZ，不预先减 1 */
```
`⚠校核`：14:27"通过 8 分频后送给 SysTick"只是 REFCLK 默认路径，**不是固定 1/8**（12:204 就是按 HCLK 直供用的）。

### 微秒计时 / 微秒延时（照抄最可靠那版，14:290 表 2692）
```c
void SysTick_Init(void){
    SysTick_CLKSourceConfig(SysTick_CLKSource_HCLK);
    uint32_t reloadValue = (SystemCoreClock / SYSTICK_FREQ_HZ) - 1;   // ⚠见上
    SysTick_Config(reloadValue);
    NVIC_SetPriority(SysTick_IRQn, BOARD_CONFIG_SYSTICK_IRQ_PREEMPT_PRIOR);
}
void SysTick_Handler(void){ sysTickCounter++; }
uint64_t micros(void){
    uint64_t time_ms=0, time_us=0; uint32_t reload=0, now=0, systick=0, us_tick=0;
    us_tick = SystemCoreClock / 1000000UL;                 // 72M→72、168M→168 计数/us
    __disable_irq();                                       // ← 原子读
    reload = SysTick->LOAD;  now = SysTick->VAL;
    time_ms = (uint64_t)tick_get() * SYSTICK_PERIOD_MS;
    __enable_irq();
    systick = reload - now;
    time_us = time_ms * 1000 + (uint64_t)systick / us_tick;
    return time_us; }
void hw_us_delay(unsigned int us){                         // 注意不要超 32 位范围
  unsigned int start, now, reload, us_tick, tcnt = 0;
  start = SysTick->VAL; reload = SysTick->LOAD;
  us_tick = SystemCoreClock / 1000000UL;                  // ← 前提：SysTick 源 = HCLK
  do { now = SysTick->VAL;
       if (now != start)                                  // ← 跨 0 重载要累加
         tcnt += (now < start) ? (start - now) : (reload - now + start);
       start = now;
  } while (tcnt < us_tick * us); }
```
`⚠校核`：原文"豆包版"（表 2690）`us = ms*1000 + (LOAD-ticks)*1000/SystemCoreClock` —— 后半项算出来是 **ms 不是 us**，
量纲错（应为 `*1000000/SystemCoreClock` 或如上 `/us_tick`），且 32 位乘法有溢出风险。
**实时性警告**（原文实测）：500µs 忙等放在优先级 6 的任务里，LED 周期从 500ms 漂到 **569ms**；
放最高优先级才准 ⇒ **忙等延时不可用于硬实时**。

### FreeRTOS / RT-Thread 的 SysTick 写法
```c
/* FreeRTOS（14:252，RVDS ARM_CM4F port.c）—— 直写寄存器，这里减 1 是对的 */
portNVIC_SYSTICK_CTRL_REG = 0UL;  portNVIC_SYSTICK_CURRENT_VALUE_REG = 0UL;
portNVIC_SYSTICK_LOAD_REG = (configSYSTICK_CLOCK_HZ / configTICK_RATE_HZ) - 1UL;
portNVIC_SYSTICK_CTRL_REG = (portNVIC_SYSTICK_CLK_BIT_CONFIG | portNVIC_SYSTICK_INT_BIT | portNVIC_SYSTICK_ENABLE_BIT);

/* RT-Thread 推荐（14:271，表 2688） */
void rt_hw_systick_init(void){
#if defined (SOC_SERIES_STM32H7)
    HAL_SYSTICK_Config(HAL_RCCEx_GetD1SysClockFreq() / RT_TICK_PER_SECOND);   // ← H7 取 D1 域时钟
#else
    HAL_SYSTICK_Config(HAL_RCC_GetHCLKFreq() / RT_TICK_PER_SECOND);
#endif
    HAL_SYSTICK_CLKSourceConfig(SYSTICK_CLKSOURCE_HCLK);
    NVIC_SetPriority(SysTick_IRQn, 0xFF);                 // ← 节拍给最低优先级
}
/* F1 + RTT 的微秒补偿写法（14:329，表 2701）：
   usTick = (SysTick->LOAD + 1UL) / (1000000 / RT_TICK_PER_SECOND); */
```
验证：Keil `View → System View → Core Peripherals → SysTick Timer` 看 LOAD/VAL；
`hw_us_delay(500)` 前后翻转一个 IO，逻辑分析仪量高电平 ≈500µs（原文就是这么验的）。

## 5. GPIO

### F1 寄存器直写 + CRL/CRH 位移（16:58，表 2833）
```c
RCC->APB2ENR |= 1<<2;                          // 使能 PORTA 时钟
GPIOA->CRL &= 0XFFFFFFF0;  GPIOA->CRL |= 0X00000008;   // PA0：CNF=01(上下拉输入) MODE=00 ← 域在 bit[3:0]
GPIOE->CRL &= 0XFFF0FFFF;  GPIOE->CRL |= 0X00080000;   // PE4：域在 bit[19:16] ⇒ 位移 = 4*n
```
F1 八种模式名：`AIN / IN_FLOATING / IPD / IPU / Out_OD / Out_PP / AF_OD / AF_PP`（16:154-161）；
`CNF[1:0]+MODE[1:0]` 组合表在 16:52。**EXTI 脚必须配成输入模式**（16:205）。
`⚠校核`：① 16:190-191 把 `AF_PP` 配给 I2C(SCL/SDA)、`AF_OD` 配给 SPI/TX —— **对调了**（I2C 须开漏复用）；
② 16:168"开漏吸收电流一般 20mA 以内"偏大，单脚电流以数据手册电气表为准；
③ **引脚 8~15 用 CRH，位移是 `4*(n-8)`** —— 原文只给了 CRL 例子，照抄 `4*n` 到 CRH 就越位（这正是库里 `SDA_IN` 宏犯的错）。

### 位带宏（F103；13:3931 表 2609）
```c
#define BITBAND(addr, bitnum) ((addr & 0xF0000000) + 0x2000000 + ((addr & 0xFFFFF) << 5) + (bitnum << 2))
#define MEM_ADDR(addr)  *((volatile unsigned long *)(addr))
#define BIT_ADDR(addr, bitnum)   MEM_ADDR(BITBAND(addr, bitnum))
#define GPIOB_ODR_Addr (GPIOB_BASE + 12)   // F1 输出用 ODR
#define GPIOB_IDR_Addr (GPIOB_BASE + 8)    // F1 输入用 IDR  ← 关键：不是 ODR
#define PBout(n)  BIT_ADDR(GPIOB_ODR_Addr, n)
#define PBin(n)   BIT_ADDR(GPIOB_IDR_Addr, n)     // n < 16
```
`⚠校核`：F407 版只有偏移不同（原文 13:3943：**ODR = BASE+20(0x14)、IDR = BASE+16(0x10)**）；
位带别名区基址 SRAM `0x22000000`、外设 `0x42000000`。M4 位带只覆盖外设低 1MB，用前核对映射。
验证：`PBout(5)=1;` 万用表量 PB5，再读回 `GPIOB->ODR` bit5。

### F4/H7 HAL 填法（`原文无 MODER/OTYPER/PUPDR/SPEEDER 直写码`）
```c
gpio_init_struct.Pin = GPIO_PIN_0|GPIO_PIN_1|GPIO_PIN_8;   // ← Pin 可以或
gpio_init_struct.Mode = GPIO_MODE_AF_PP;
gpio_init_struct.Pull = GPIO_PULLUP;
gpio_init_struct.Speed = GPIO_SPEED_FREQ_HIGH;
gpio_init_struct.Alternate = GPIO_AF12_FMC;                 // ← AF 编号查该型号 datasheet
HAL_GPIO_Init(GPIOD, &gpio_init_struct);                    // HAL 内部写 MODER/OTYPER/PUPDR/AFR
/* EXTI 输入： Mode = GPIO_MODE_IT_RISING;  Pull = GPIO_PULLDOWN; */   // 15:519
```
`GPIO_PinAFConfig()` **不可或运算**（逐脚配），而 `GPIO_Init` 的 `Pin` 可以或、
但**入口参数不能 A 口 E 口混在一个结构体里**（12:167-174）。

## 6. NVIC / EXTI

### 优先级分组三种写法（15:107-113）
```c
/* 标准库 misc.c —— 本身就是 CMSIS 直写 AIRCR */
void NVIC_PriorityGroupConfig(uint32_t g){ SCB->AIRCR = AIRCR_VECTKEY_MASK | g; }  // VECTKEY=0x05FA<<16
NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);      // ← 全系统只设一次；分组位在 AIRCR[10:8]
/* HAL 等价：HAL_NVIC_PriorityGroupConfig() —— 原文无此代码；CMSIS 同名函数是 NVIC_SetPriorityGrouping() */
```
`⚠校核`：文档未给 `NVIC_PriorityGroup_2` 的宏值 ⇒ 无法验证它与 AIRCR[10:8] 的对应；写代码时用宏别用裸值。

### 使能 + 优先级（两种库）
```c
/* 标准库（15:100-105） */
NVIC_InitStructure.NVIC_IRQChannel = USART1_IRQn;
NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 3;
NVIC_InitStructure.NVIC_IRQChannelSubPriority = 3;
NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;  NVIC_Init(&NVIC_InitStructure);
/* HAL（15:519，成对写） */
HAL_NVIC_SetPriority(DCMOTOR_ENCODER_IRQn, 0, 0);
HAL_NVIC_EnableIRQ(DCMOTOR_ENCODER_IRQn);
```

### F4 外部中断 7 步（15:233-247，含全部关键函数）
```c
RCC_APB2PeriphClockCmd(RCC_APB2Periph_SYSCFG, ENABLE);       // ① ← 必使能 SYSCFG，否则映射无效
GPIO_Init();                                                 // ② IO 配输入
SYSCFG_EXTILineConfig(EXTI_PortSourceGPIOE, EXTI_PinSource2);// ③ ← M4 用这个；M3 是 GPIO_EXTILineConfig
EXTI_InitStructure.EXTI_Line    = EXTI_Line2;
EXTI_InitStructure.EXTI_Mode    = EXTI_Mode_Interrupt;
EXTI_InitStructure.EXTI_Trigger = EXTI_Trigger_Falling;
EXTI_InitStructure.EXTI_LineCmd = ENABLE;  EXTI_Init(&EXTI_InitStructure);   // ④
NVIC_Init();                                                 // ⑤
void EXTI2_IRQHandler(void){ ... }                           // ⑥ 只有 7 个向量：0/1/2/3/4/9_5/15_10
EXTI_ClearITPendingBit(EXTI_Line2);                          // ⑦ ← 标志不会自动清
```
HAL 版清标志两段（15:519，**顺序不能反**，H7 实测）：
```c
void EXTI1_IRQHandler(void){
  __HAL_GPIO_EXTI_CLEAR_IT(DCMOTOR_ENCODER_PIN);   // ① 清 EXTI 挂起
  HAL_NVIC_ClearPendingIRQ(DCMOTOR_ENCODER_IRQn);  // ② 清 NVIC 悬起，防二次进入
}
```

### 关中断三种粒度（15:551-560）
```c
__disable_irq();  lcd_refresh();  __enable_irq();        // PRIMASK：屏蔽除复位/NMI/HardFault 外全部
__set_FAULTMASK(1); NVIC_SystemReset();                  // 连 HardFault 也屏蔽，用于安全复位
__asm void INTX_DISABLE(void){ CPSID I  BX LR }          // MDK 裸写等价
/* BASEPRI：FreeRTOS 的开关中断就是控制它（15:473） */
/* ⚠ __set_BASEPRI 与 portENTER_CRITICAL 的示例代码不在这四份切片里，勿凭空引用 */
```

### RT-Thread 中断进出（15:488 + 13:134）
```c
void rt_interrupt_enter(void){ rt_base_t level;
  level = rt_hw_interrupt_disable();  rt_interrupt_nest++;  rt_hw_interrupt_enable(level); }
/* 底层是 PRIMASK 读写： MRS r0,PRIMASK / CPSID I ... MSR PRIMASK,r0 */
void SysTick_Handler(void){ rt_interrupt_enter(); HAL_IncTick(); rt_tick_increase(); rt_interrupt_leave(); }
```
**任何调 RT-Thread IPC 的 ISR 都要 enter/leave 包起来**，否则调度时机不对。

## 7. 两处被夸大的清单（照抄时会踩坑）

`⚠校核`：
1. 15:541-548"EXTI3/4/9_5、USART1/2/3 都不能用 `NVIC_DisableIRQ`，否则进硬件错误" ——
   **只有负数 IRQn（`SysTick_IRQn = −1` 等）会因 `(IRQn>>5)` 越界出问题**，正数外部中断禁用是合法的，别照抄这份清单。
2. 15:310/424"时钟安全系统 **CCS**" 拼写应为 **CSS**（Clock Security System；13:444 写法正确），F4 的 NMI 挂到 CSS。
3. 屏蔽期间产生的中断请求**仍被悬起**，开中断后会补发（15:816-817）——所以"关中断执行一段代码"不能当作"丢弃事件"的手段。
