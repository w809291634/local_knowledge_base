# 时钟树 / GPIO 配置 / 中断与事件（NVIC + EXTI）

## 1. 时钟树：先分清型号，文档里的"STM32"多数只指 F1

| 型号 | 时钟源与上限（照抄） |
|---|---|
| **F1** | HSI **8MHz**、HSE 4~16MHz、LSI 40kHz、LSE 32.768kHz；PLL 输入可取 HSI/2、HSE、HSE/2，倍频 2~16，输出 ≤72MHz；AHB/APB2 最大 72MHz，**APB1 最大 36MHz**；AHB 分频 1/2/4/8/16/64/128/256/512；APB1/APB2 各 1/2/4/8/16；ADC 分频 2/4/6/8；**SDIO 固定 HCLK/2**；RTC 源 = LSE/LSI/HSE÷128；USB 需要 PLL 出 48M 或 72MHz(÷1.5/÷1)；**MCO = PA8**；APB 分频≠1 ⇒ 定时器时钟 ×2 |
| **F4** | `PLL_M=8 PLL_N=336 PLL_P=2 PLL_Q=7` ⇒ `8×336/(8×2)=168MHz`；`RCC->PLLCFGR = PLL_M \| (PLL_N<<6) \| (((PLL_P>>1)-1)<<16) \| PLLSRC_HSE \| (PLL_Q<<24)`；`SystemInit` 先开 HSI（CFGR 复位低 2 位=00），`SetSysClock` 再切 HSE+PLL；须同步改 `stm32f4xx.h` 的 `HSE_VALUE`。档位：HCLK=168、PCLK1=42、PCLK2=84 |
| **H743** | 六种源：HSI 64MHz、HSE 4~48MHz、LSE 32.768kHz、LSI≈32kHz、**CSI≈4MHz**、**HSI48=48MHz**；`Fvco = Fs×(plln/pllm)`、`Fsys = Fvco/pllp`；plln 4~512、pllm 2~63、pllp 2~128(偶)、pllq 1~128；25M 晶振推荐 160/5/2/4 ⇒ Fvco 800M、Fsys 400M、Fq 200M |
| H7 配置顺序 | ①`MODIFY_REG(PWR->CR3, PWR_CR3_SCUEN, 0)` ②设 VOS Scale1 并等 `PWR_D3CR_VOSRDY` ③OscConfig(HSE+HSI48，PLL VCOWIDE/RGE_2) ④ClockConfig(SYSCLK_DIV1、HCLK/2、APB1~4 各/2、FLASH_LATENCY) ⑤USB 电压检测/CSI/SYSCFG/IO 补偿 |
| H7 外设时钟 | **必须单独选源**：`RCC_FMCCLKSOURCE_D1HCLK`、GPIO `GPIO_AF12_FMC`；400/200/100MHz 时 APB1/APB2 的 `TIMxCLK = 200MHz` |

`⚠校核C`：文档把 F1 的说法写成"STM32 有 5 个时钟源/5 大类"（F4 有 HSI/HSI48/HSE/LSI/LSE/PLLI2S 等，H7 自己列了 6 种）；
"F1 PLL 倍频 2~16" 漏了 HSI/2 时的 **1.5 倍频**；H7 段 `FLASH_LATENCY_2` 与"400MHz/SysTick=400MHz 但 HCLK 实为 200MHz"的注释不自洽（作者未验证）。

**改晶振必改的两处（F1）**：`stm32f10x.h` 的 `HSE_VALUE`（默认 8M，CL 版本是 25M）+ `system_stm32f10x.c` 的
`SYSCLK_FREQ_72MHz`。只改一处 ⇒ 时钟与延时全错。

## 2. SysTick（Cortex-M 通用）

- 24 位**递减**计数器；到 0 自动重装并置 `COUNTFLAG`，可触发中断。
- 4 个寄存器：`STK_CSR 0xE000E010`、`STK_LOAD 0x14`、`STK_VAL 0x18`、`STK_CALIB 0x1C`
  （文档写作 `STK_CALRB` `⚠校核A`）。位：`ENABLE=1<<0`、`CLKSOURCE=1<<2`、`TICKINT=1<<1`、`COUNTFLAG=1<<16`。
- **时钟源可选 HCLK 或 HCLK/8**；文档一处写"SysTick 固定为 HCLK 的 1/8"，与同文
  `HAL_SYSTICK_CLKSourceConfig(SYSTICK_CLKSOURCE_HCLK)` 矛盾 `⚠校核B`。
- FreeRTOS：`LOAD = (configSYSTICK_CLOCK_HZ / configTICK_RATE_HZ) − 1`。
- RT-Thread 推荐：`HAL_SYSTICK_Config(HAL_RCC_GetHCLKFreq()/RT_TICK_PER_SECOND)` + HCLK 源 +
  `NVIC_SetPriority(SysTick_IRQn, 0xFF)`。
- **`SysTick_Config()` 内部已经做 `ticks−1`**，外面再减一次 ⇒ 周期少 1 个计数（文档"最终版本"就有这个重复减一，作者留了"为什么减一"未收口）`⚠校核C`。
- Keil 看内核外设：View → System view → Core peripherals → SysTick。

**微秒计时/延时套路（裸机，值得复用）**
```c
us_tick = SystemCoreClock / 1000000UL;          // F1 72MHz→72 计数/us；F4 168→168
// 跨 0 重载要累加：reload - now + start
micros() = tick * 1000 + (LOAD - VAL) / us_tick; // 单位 us
```
`⚠校核A`：文档另版公式写成 `(LOAD-ticks)*1000/SystemCoreClock`，量纲错（应 ×1e6），且 32 位乘法有溢出风险。
**裸忙等延时的实时性代价**：500us 延时放在优先级 6 的任务里，LED 周期实测漂到 569ms；放最高优先级才准
⇒ **忙等延时不能用于硬实时**。

## 3. GPIO 配置（以 F1 的 8 种模式为主，F4 改 MODER/AFR）

| 常见用途 | F1 模式 | 备注 |
|---|---|---|
| 按键输入 | 上拉/下拉输入 或 浮空输入（**复位后默认态**） | 文档称"浮空输入是复位后的状态" `⚠校核C` |
| LED/推挽输出 | 通用推挽输出 | |
| I2C SCL/SDA | **复用开漏 AF_OD** | 文档把 I2C 写成 AF_PP、把 TX/SPI 写成 AF_OD，**两者对调** `⚠校核C` |
| USART TX / SPI | **复用推挽 AF_PP** | 同上 |
| 外部中断 | 输入模式 + 配 EXTI 线 | |

- **矩阵键盘要用"模拟开漏"而非推挽**：同时按两个键（如"2"和"8"）时推挽会互相驱动、电平不定；
  做法：输出低 = OUTPUT + 写 0；输出高 = INPUT + 内部上拉（弱驱动）。
- 上拉电压：只有 **5V 容忍(FT)脚**才能上拉到 5V；文档一处笼统写"3.3V/5V/12V 都可以"，
  另一处写"不能超过 GPIO 耐压，3.6V 就不能上拉 5V" ⇒ **必须区分脚类型** `⚠校核C`。
- 位操作：`reg &= ~(...)` 清位、`reg |= (1<<5)` 置位，其余位不动；`GPIO_Pin_x` 可以或运算组合，
  但 `GPIO_PinAFConfig()` 的引脚参数**不可或**。
- **位带（bit-band）地址公式**：`BITBAND(addr,bitnum) = ((addr & 0xF0000000) + 0x2000000 + ((addr & 0xFFFFF)<<5) + (bitnum<<2))`；
  SRAM 别名区 `0x22000000`、外设 `0x42000000`；F1 的 `ODR` 偏移 = BASE+12、F4 = BASE+20(0x14)，`IDR` = +16(0x10)。
- 各家 AF 命名不同：STM32 `AFRL/AFRH` ↔ GD32 `GPIOx_AFSEL0/1` ↔ AT32 `IOMUX/MUXL/MUXH`（详见 `mcu-chip-families/`）。

## 4. 中断体系与优先级（Cortex-M 通用 + STM32 数值）

| 项 | 内容 |
|---|---|
| 向量 | 共 256 个 = **16 个内核异常 + 240 个外部 IRQ**；编号 1~15 为系统异常（**没有 0 号**），复位 = −3、NMI = −2、HardFault = −1，≥16 才是外设 IRQ |
| 同优先级 | 同时悬起时**响应编号小者** |
| 悬起位清除 | **服务例程开始时硬件自动清**（单实例） |
| PRIMASK 期间 | 请求仍被**悬起**，解除后照常触发（不会丢） |
| 优先级数值 | **越小越高**；MSB 对齐；最少 3 位（8 级）、最多 256 级；**亚优先级至少 1 位**；若从 bit7 开始分组 ⇒ 全变亚优先级 = **等于禁用嵌套** |
| 分组设置 | **只开机设一次** |
| F1/F4 分组表 | 占用 `IP[7:4]`：组0 `AIRCR[10:8]=111`(0 抢占/4 子)、组1=110、**组2=101(2/2，各 0-7)**、组3=100、组4=011(**4 抢占/0 子，0-15**)；抢占可打断，子优先级只决定同一抢占下的次序 |
| F4 位数 | 4 位优先级 / 16 级；通道数：F405xx/07xx、F415xx/17xx **82 个可屏蔽**（不含 CM4 的 16 根），F42xxx/43xxx 86 个。`⚠校核B`：同文另处写"F103 共 84 个中断 = 16 内核 + 68 可屏蔽"，与自身枚举（只到 59）矛盾 |
| NVIC 寄存器 | `ISER/ICER/ISPR/ICPR/IABR` 各 8×uint32；`IP[240]`（每中断 8 位、**只用高 4 位**）；`STIR`；`AIRCR = 0xE000ED00`，`VECTKEY` 写 `0x05FA`（读回 0xFA05），`PRIGROUP` 在 bit[10:8] |
| **`NVIC_DisableIRQ` 的正确边界** | 只有**负数内核异常号**（如 `SysTick_IRQn = −1`）不能用 ISER/ICER 索引；文档把 EXTI3/USART1~3 也列进"禁用会进硬件错误"的清单，是**以偏概全** `⚠校核C` |
| HAL 优先级死锁 | `HAL_Delay` 靠 SysTick 的 `uwTick`(1ms)；**在中断里调 HAL_Delay 且该中断优先级数值高于 SysTick（`TICK_INT_PRIORITY=15` 最低）就会死锁** |

## 5. 中断屏蔽三种手段（选型差别很大）

| 手段 | 效果 |
|---|---|
| `PRIMASK`（`CPSID I`/`CPSIE I`） | 屏蔽除 **复位 / NMI / HardFault** 外全部 |
| `FAULTMASK` | **连 HardFault 也屏蔽**；退出时自动清零 |
| `BASEPRI` | 按阈值屏蔽（优先级数值 ≥ 阈值的被挡）；**写 0 即停止屏蔽** |
| 实践 | **FreeRTOS 用 BASEPRI**（所以才有"可屏蔽中断优先级必须 ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY`"）；RT-Thread 用 PRIMASK（`enable(level)`：**level=0 才开中断**，传 1 无作用） |
| `⚠校核` | 文档一句"这里的优先级必须小于系统时钟的优先级"表述无意义，作者本意不可考；FreeRTOS 的正确约束是数值**≥** MAX_SYSCALL 才可调 API |

## 6. EXTI / 外部中断与事件（F1/F4）

| 项 | 内容 |
|---|---|
| 线数量 | **F1：19 条**（0~15 = IO、16 = PVD、17 = RTC 闹钟、18 = USB 唤醒）；**F4：文档列 0~22**（19 = ETH 唤醒、20 = OTG HS、21 = RTC 入侵/时间戳、22 = RTC 唤醒）。`⚠校核B`：同文写"F4 支持 22 个外部中断/事件"，与自己列的 23 条不符 |
| 限制 | **一条线同一时刻只能映射一个端口引脚**；IO 外部中断只占 **7 个向量**（EXTI0~4、EXTI9_5、EXTI15_10）；**标志位不自动清零** |
| F4 外部中断 7 步 | ①使能 **SYSCFG 时钟** ②GPIO 配输入 ③`SYSCFG_EXTILineConfig`（**与 M3 的 `GPIO_EXTILineConfig` 不同名**）④`EXTI_Init`（线/模式/触发/使能）⑤`NVIC_Init` ⑥写 ISR ⑦`EXTI_ClearITPendingBit` |
| HAL 二次进入修复 | **先 `__HAL_GPIO_EXTI_CLEAR_IT(pin)`，再 `HAL_NVIC_ClearPendingIRQ(IRQn)`**（顺序反了会漏/重触发；H7 实测） |
| NMI | F4 里 **NMI 被连到 CSS（时钟安全系统）**；文档写作"CCS" `⚠校核A` |
| 编码器/抖动 | 不稳输入优先用定时器编码器模式（自带滤波），见 `timer-pwm-adc-dma.md` §5 |
