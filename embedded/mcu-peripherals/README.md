# mcu-peripherals/ — 单片机外设原理与用法（跨芯片通用）

> **来源**：用户的个人技术文档 `1_git_code/__gitee_code/study_doc/1-单片机相关文档/单片机外设和调试基础知识.docx`
> （48MB，33559 段、2862 个标题，2026-10 时点）。2026-10-16 逐章精读提炼。
> 原文里大量知识以**截图**形式存在，导出文本后为空表 → **本库只收录有文字依据的部分**，
> 缺正文的条目在各文件里明确写"文档此处为空表/无正文"，不猜测补齐。

## 本目录文件

| 文件 | 覆盖 |
|---|---|
| `serial-uart-rs485-can-modbus.md` | 通信分类与速率对比、UART（帧/波特率/中断/DMA 收/重定向/WK2114/ISP 下载）、RS485、CAN（含 bxCAN 位时序与过滤器）、MODBUS RTU |
| `i2c-spi-and-device-drivers.md` | I2C 协议与三套软件模拟实现、SPI 模式与 NSS、OLED(SSD1306/1316/96×32)、24C02、PCA9685、PCF8563、BMP280、MAX30102、TM1650、GT911、W25Q128、DM9051、圆屏 GC9A01 |
| `sd-card-dcmi-fsmc-sram.md` | SD/SDIO（卡型判别、命令与响应、SPI 模式固定 CRC）、摄像头 OV2640 + DCMI、外部 SRAM 与 FSMC/FMC 映射与时序 |
| `audio-i2s-wav.md` | I2S 时钟关系与 PLLI2S 分频、WAV 文件结构、WM8978 寄存器、录音播放通路 |
| `timer-pwm-adc-dma.md` | 定时器分类/时基/对齐模式/编码器/死区、ADC（转换时间/通道/模式/DMA/校准）、DMA（F1 通道 vs F4 流+通道/FIFO/双缓冲/流控制器/H7 缓存一致性） |
| `clock-gpio-nvic-exti.md` | F1/F4/H7/GD32/AT32 时钟树与 PLL、SysTick 与微秒计时、GPIO 模式与复用、NVIC 优先级分组、EXTI 线与屏蔽手段(PRIMASK/FAULTMASK/BASEPRI) |
| `ERRATA-单片机外设和调试基础知识.md` | **校核结论：原文中已被判定为错误/自相矛盾/单位笔误/型号错配的条目清单** |

### 代码配方（`recipes-*.md`，与上面主题篇一一对应）

> 每份都是**照抄原文的代码骨架** + 调用顺序 + 参数怎么算 + 怎么验证 + 易误用清单；
> 行号指向原文导出文本，`⚠校核` 处保留原样不修正，`原文无代码` 处**明确标注缺口**（不要以为库里有现成实现）。

| 文件 | 配哪篇 | 内容 |
|---|---|---|
| `recipes-uart-rs485-can-modbus.md` | serial-uart… | 串口初始化(F1/F4/HAL)、ISR 双判模板、**DMA+IDLE 环形缓冲全套**、printf 重定向三种、WK2114 全骨架、485 方向脚、CAN(BTR/滤波器/回环自测)、Modbus 帧序 |
| `recipes-i2c-spi-and-devices.md` | i2c-spi… | **三套软件 I2C 的 ACK 返回值口径对照表**、start/stop/读写骨架、OLED 写命令/Set_Pos/初始化序列/显存刷新、24C02 重复起始、PCA9685 设频、PCF8563 BCD、TM1650、SPI 初始化与分频、**W25Q128 跨页/跨扇区读-改-写**、DM9051 寄存器与 PHY 间接访问、GC9A01 MADCTL 与大小端 |
| `recipes-timer-adc-dma.md` | timer-pwm-adc-dma | 时基/PWM(CubeMX 缺的两处)/编码器(函数顺序铁律)/级联 TRGO/F1 重映射事故；ADC+DMA 完整序列、EOC 不来与 OVR 常置的真实成因；F1 `DMA_Init` 全字段、F4 Stream+CHSEL+LINKDMA、循环模式取数算法、**正常模式重发顺序**、双缓冲 CT 位、H7 cache 位置 |
| `recipes-clock-gpio-nvic.md` | clock-gpio-nvic | 改晶振两处宏、F4 `PLLCFGR` 组装、H7 时钟十步、SysTick 寄存器与"重复减一"、`micros()/hw_us_delay` 全文、FreeRTOS/RT-Thread 写法、CRL/CRH 直写与**位移未减 8 的坑**、位带宏、F4 外部中断七步、HAL 清标志两段、三种关中断粒度、RT-Thread 中断进出 |
| `recipes-sd-dcmi-fsmc-audio.md` | sd-card / audio | SDIO 初始化(CMD0/CMD8/ACMD41/单块读轮询/DMA)、**SPI 模式固定 CRC 值表**、OV2640 复位与窗口设置、DCMI 启动顺序、FSMC SRAM 全套字段、I2S+PLLI2S 采样率查表、双缓冲播放链；**WM8978/录音/SD 后续 CMD 序列原文无代码，已逐条标出** |

## 关联目录（不要在这里重复找）

- 崩溃与异常取证 → `embedded/debug-methodology/hardfault-crash-forensics.md`
- 调试器与仪器（ST-Link 自制、J-Link 远程、示波器）→ `embedded/debugger/stlink-jlink-remote-oscilloscope.md`
- 编译/链接/启动/烧录/Flash 与选项字节 → `embedded/mcu-toolchain-boot-flash/README.md`
- 各家芯片与 STM32 的差异、移植踩坑 → `embedded/mcu-chip-families/README.md`
- ZigBee / Z-Stack OSAL 机制 → `embedded/mcu-chip-families/zigbee-zstack-osal.md`
- C51 语言与链接器坑（已在库中，勿重复）→ `yjt/STC8H_8G/keil-c51-*.md`

## 三条入库规矩（本次整理自定，后续沿用）

1. **校核优先**：文档里的每一条数值/公式都当作"待验证"处理。凡与其他权威口径不符或前后自相矛盾的，
   一律写进 ERRATA 并在正文处标注 `⚠校核`，**不擅自替换成我认为正确的值**（除非是纯算术错误，也要注明"按算术应为…"）。
2. **作者自标注不确定的内容不得当结论**：原文里"不建议采纳""不知道具体作用""待查""原因不明"的段落，
   入库时保留但标注为 `未验证`，放在条目末尾而非结论位。
3. **项目事实不入库**：具体公司工程的上位机帧协议、板卡引脚表、血糖仪/小车/夹爪等方案参数、
   个人绝对路径与链接，都留在原 docx，不抄进经验库（依据 `yjt/PEMS/generality-boundaries-and-precedence.md`）。
   本库只收"换个项目还用得上"的部分。
