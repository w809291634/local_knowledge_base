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
