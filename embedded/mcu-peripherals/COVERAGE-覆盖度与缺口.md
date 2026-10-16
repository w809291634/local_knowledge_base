# 覆盖度与缺口（源：单片机外设和调试基础知识.docx）

> 目的：**把"整理到什么程度、还差什么"变成可核对的数字**，避免误以为已经全量入库。
> 统计时间 2026-10-16；方法：python-docx 解析 + 按 H1 切章 + 统计表块是否为空（空表块 = 该处内容**只存在于截图**里）。

## 1. 源文档体量

| 指标 | 数值 |
|---|---|
| 文件大小 | 48.1 MB（其中**内嵌图片 1018 张**：782 PNG + 234 JPEG + 1 GIF + 1 EMF，共 46.2 MB） |
| 段落 / 表格对象 | 33,559 段 / 4,713 个表格对象 |
| 标题 | H1=21、H2=254、H3=716、H4=971、H5=702、H6=162、H7=20、H8=16 |
| 导出纯文本（按章切分后去重） | 31,905 行，其中**有字行 17,768** |
| 表格块 | 4,704 个，其中**空表块 3,387 个 ⇒ 约 72% 的表格内容只有截图、没有文字** |

**入库结果**：`embedded/mcu-peripherals/`（6 主题 + 5 配方 + ERRATA + 本文件）、
`embedded/mcu-chip-families/`（6 主题 + 1 配方）、`embedded/mcu-toolchain-boot-flash/`、
`embedded/debug-methodology/hardfault-crash-forensics.md`、`embedded/debugger/stlink-jlink-remote-oscilloscope.md`，
合计约 **3,100 行**。

⇒ **这是蒸馏，不是转录**：约 17.8k 有字行压到约 3.1k 行，压缩比约 5.7:1；
且**图片里的内容一张都没有提取**（1018 张全未 OCR）。

## 2. 逐章覆盖矩阵

"细分数" = 该章 H3/H4/H5/H6 小标题数量之和，用来表示实际颗粒度。

| # | 章 | 有字行 | 空表块(仅截图) | 细分数 | 已入库到 | **未覆盖 / 只有结论** |
|---|---|---|---|---|---|---|
| 01 | 单片机调试基础方法 | 250 | 35 | 37 | `debug-methodology/hardfault-crash-forensics.md`、`debugger/stlink-jlink-remote-oscilloscope.md` | H4 里 25 个小节只挑了 callstack/cm_backtrace/memset/ST-Link/J-Link/示波器；**寄存器现场截图 35 处未 OCR** |
| 02 | TI CC2530 + Z-Stack | 1309 | 460 | 248 | `mcu-chip-families/cc2530-cc2538-cc2640.md`、`zigbee-zstack-osal.md`、`recipes-code-skeletons.md` §5 | **CC2530 裸机外设无代码配方**（当时被"由别路负责"漏掉）；水温传感器驱动、CC2640 协议栈各章、ZDO/绑定细节、**协调器上位机协议属项目事实未入库** |
| 03 | GD32 | 145 | 32 | 23 | `mcu-chip-families/gd32.md`、recipes §1 | GDF4xx 系列差异表未逐条；**HXTAL/AF 表原图未 OCR** |
| 04 | AT32 | 1085 | 581 | 258 | `mcu-chip-families/at32.md`、recipes §2 | **最大未覆盖体量**：XMC、DVP/摄像头、USB、加密、CAN、ADC 触发、TMR 各例只到骨架；ZW/NZW 无代码；**581 个空表 = 一半以上信息在图里** |
| 05 | PY32 | 34 | 24 | 9 | `py32-ht32-holtek.md` | 体量极小；PC0=NRST 已收全 |
| 06 | HT32（实为 Holtek 8 位） | 408 | 104 | 73 | `py32-ht32-holtek.md` | OPA/SADC/血糖流程已收；**H4=33 里校准算法、LCD 驱动段、USIM 配置只到摘要** |
| 07 | STC | 1554 | 155 | 133 | `stc-c51-and-ch32-wch.md`、recipes §3 | EEPROM/Flash 读写擦、PWMA 死区、看门狗、掉电唤醒 —— **原文本身无代码**；`OPTIMIZE(9)`/`__declspec` 等 AI 段已入 ERRATA 但正文未逐条重写 |
| 08 | CH（沁恒） | 561 | 228 | 140 | 同上 + recipes §4 | **H5=55**：SPI/I2C/GPIO 中断/USB/触摸/ADC 例程未逐条；BLE 各 Profile 只收骨架 |
| 09 | 杰理 | 10 | 14 | 2 | — | 本章近乎空；已由 `embedded/jieli_soundbox_sdk/` 17 篇 + 该 SDK 源码替代 |
| 10 | STM8 | 17 | 2 | 2 | 一句（IDE/license） | 本章近乎空 |
| 11 | `/*** STM32`（分节标记） | 3 | 0 | 0 | — | 无内容 |
| 12 | 程序示例 | 258 | 26 | 43 | 部分进 `recipes-clock-gpio-nvic`、`recipes-timer-adc-dma` | **H2=33 个示例只做了 2~3 个**；KEY_Scan、软件定时器、ppm 换算只留结论 |
| 13 | STM32 基础杂类 | 2716 | 398 | 324 | `mcu-toolchain-boot-flash/README.md`、`recipes-clock-gpio-nvic.md`（位带/H7 内存/scatter/MicroLIB） | **FreeRTOS 与 RT-Thread 移植、CubeMX 注意、常见编译链接错误清单、RTC/备份区、看门狗、选项字节/RDP** 多数只有结论或原文空表 |
| 14 | 时钟总结 | 271 | 32 | 46 | `clock-gpio-nvic-exti.md` + recipes §1-4 | 覆盖较完整；F1 `SetSysClockTo72` 函数体原文无 |
| 15 | 中断和事件 | 541 | 65 | 73 | 同上 §5-7 | 覆盖较完整；`__set_BASEPRI`/`portENTER_*` 原文无码 |
| 16 | GPIO 复用与配置 | 224 | 51 | 22 | 同上 + ERRATA（AF 对调、20mA、CRH 位移） | 复用映射表**只在截图里**，未 OCR |
| 17a | 通信基础 + 串口 | 616 | 114 | 122 | `serial-uart-rs485-can-modbus.md` + recipes | F1/F4 各协议速度表在图里 |
| 17b | I2C 与 OLED 传感器 | 812 | 105 | 248 | `i2c-spi-and-device-drivers.md` + recipes | **PCA9685 通道映射、GT911 读坐标、MAX30102、BMP280 只到摘要**；OLED 命令表原图未 OCR |
| 17c | SPI / 485 / CAN | 1581 | 130 | 466 | 两个主题篇 + 两个 recipes | **H4=341/H5=301 的本章是最大细分数**：CAN 报文过滤器分组策略、SPI Flash 文件系统层、485 组网实例只挑主干 |
| 17d | SD / 摄像头 / SRAM / 音频 / Modbus | 2795 | 344 | 741 | `sd-card-dcmi-fsmc-sram.md`、`audio-i2s-wav.md` + recipes | FATFS 移植、音频编解码、Modbus 从站、**WM8978 初始化序列**多数原文无码；SD 后续 CMD 无码 |
| 18 | STM32 定时器 | 998 | 183 | 130 | `timer-pwm-adc-dma.md` + recipes | 输入捕获完整例、一主多从同步、HRTIM 未做 |
| 19 | ADC | 389 | 54 | 70 | 同上 | F4/H7 转换时间表**只在图里**；注入/差分模式未收 |
| 20 | DMA | 1187 | 250 | 156 | 同上 | MDMA、请求映射总表**在图里**；缓冲长度规则未逐条 |
| 21 | LCD 和触摸屏原理 | 4 | 0 | 0 | — | 本章是空壳，内容在另一份 docx《LCD触摸屏幕原理》 |

## 3. 三类缺口（按"补起来的价值"排序）

**① 截图里的独有信息（3,387 个空表块 / 1,018 张图，目前零提取）**
最高价值的部分：各类**引脚复用映射表、寄存器位域表、公式表、波形与逻辑分析仪截图、F4/H7 外设速度表、SD/CAN/ADC 时序图**。
这些不是"重复内容"，很多是**唯一副本**，文字里根本不存在 ⇒ 现在库里只有"该处有图"这一事实。

**② 已读到但未入库的蒸馏损耗（字数上限导致）**
每章的 H4/H5 细分数远大于我的条目数，尤其 ch04(AT32)、13(杂类)、17c(SPI/CAN)、17d(SD/音频)。
表现：只留了骨架与坑，没留**逐外设完整例程**与"第二种、第三种写法"。

**③ 结构性空洞（原文自己就没有）**
CC2530 裸机代码配方（我分工时漏接）、杰理章、STM8 章、LCD 章、WM8978 初始化序列、STC 的 EEPROM/PWM/看门狗代码、
IWDG/WWDG 公式、选项字节 RDP、Standby 唤醒源表 —— 这些**不该由我编**，要么另找手册，要么等原文补齐。

## 4. 补法与成本（等你定优先级，我不擅自开）

| 方案 | 做法 | 成本 | 建议 |
|---|---|---|---|
| A 图片提取 | 从 docx 导出图片按章归档，我用多模态逐张读、只录"唯一副本"类表格 | 1,018 张全做不现实；**按章挑前 200~300 张**（17 章 693 空表最密、02 章 460、13 章 398）可行 | **推荐，收益最高**：这是唯一"不做就永久丢"的部分 |
| B 补蒸馏损耗 | 对 ch04 / ch13 / ch17c / ch17d 再走一轮，取消字数上限，按"一外设一段"出配方 | 4~6 个并行任务，产出预计再 +2,000~3,000 行 | 次优先，尤其 ch04 AT32 |
| C 补结构性空洞 | 需要**外部资料或上机**（手册、正点原子/野火例程、实测），不能从这份 docx 得到 | 逐条列进 ERRATA D 档即可 | 只做记录，不编造 |
| D 同目录其他 18 份 docx（约 215 MB） | 与本篇同一套流程（含各自 COVERAGE 档） | 每份 1~2 轮 | 《LCD触摸屏幕原理》最该先做（本篇 5 处指向它） |

**当前可核对结论**：文字层已**通读全部 21 章**，入库约 3,100 行；
**图片层 0 提取**、**H4 以下细粒度约 1,800+ 小节未按条目收录**、**同目录其余 18 份文档未开始**。

## 5. 同一资料区里还没动的文档（实测目录清单）

路径 `F:\1_git_code\__gitee_code\study_doc\1-单片机相关文档\`，共 19 份 docx（本篇只是其中 1 份）
＋ 子目录 `AI生成的文档\BLE蓝牙服务结构详解_V5.docx`。上位目录 `study_doc\` 还有
`2-高级编程文档`、`3-其他学习`、`常见问题诊断过程汇总`、`待整合知识点.docx` 等，均**未纳入本篇范围**。

| 优先级 | 文件 | 体量 | 说明 |
|---|---|---|---|
| 高 | `LCD触摸屏幕原理.docx` | 37.8 MB | 本篇第 21 章是空壳，5 处内容指向它 |
| 高 | `RT-Thread基础知识.docx` | 29.2 MB | 库里现有 `embedded/rt-thread/rt-thread-pitfalls.md` 只来自另一份《问题解决和汇总 v1.2》，非本篇 |
| 高 | `esp32_8266系列蓝牙wifi知识_freeRTOS.docx` | 29.9 MB | 与 `embedded/esp32/` 直接相关 |
| 中 | `C语言基础知识.docx` | 35.1 MB | 语言层，与 `yjt/STC8H_8G/keil-c51-*` 有交集 |
| 中 | `emwin基础知识和项目.docx` | 11.2 MB | GUI，接 LCD 篇之后做 |
| 中 | `嵌入式软件包的移植适配和用法.docx` | 11.3 MB | 移植通用方法 |
| 中 | `KEIL_MDK-IAR-GCC-MinGW软件基础知识.docx` | 12.6 MB | 库里 `embedded/ide/`、`mcu-toolchain-boot-flash/` 只覆盖了零星点 |
| 中 | `蓝牙_wifi_http_mqtt等协议标准.docx` | 6.6 MB | 协议标准 |
| 中 | `单片机硬件知识.docx` | 5.1 MB | 硬件层 |
| 低 | `OTA_IAP实现基础知识.docx` | 5.8 MB | 与杰理 OTA 篇有交集 |
| 低 | `玄铁AFP蓝牙等单片机相关基础知识.docx` | 3.3 MB | |
| 低 | `OpenHarmony基础知识.docx` | 3.1 MB | |
| 低 | `STM32运行ai的调研.docx` | 2.3 MB | |
| 低 | `arduino相关基础知识及其库.docx` | 0.6 MB | |
| 低 | `STM32移植microPython.docx`、`正点原子综合例程.docx` | 0.03/0.05 MB | 体量极小 |
| 项目事实 | `yjt益健堂相关单片机相关基础知识.docx`(4.4 MB)、`公司设备_opennode_wifi相关基础知识.docx`(5.5 MB) | 9.9 MB | 按入库规矩 3，**公司/项目专属参数不入库**，只挑可复用的踩坑点 |
