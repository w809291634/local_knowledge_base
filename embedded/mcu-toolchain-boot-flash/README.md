# 工具链、启动、Flash 与烧录（Keil/GCC + STM32 各家）

> 来源：《单片机外设和调试基础知识.docx》第 12/13 章精读，2026-10-16。
> 与 `embedded/ide/iar-keil-ide-issues.md`（IDE 层坑）、`embedded/mcu-peripherals/serial-uart-rs485-can-modbus.md`
> （printf 重定向细节）互补。`⚠校核` 见 `embedded/mcu-peripherals/ERRATA-*.md`。

## 1. 启动链与堆栈定义

| 项 | 内容 | 范围 |
|---|---|---|
| 向量表布局 | **0x00 放栈顶初值、0x04 放复位向量** | Cortex-M 通用 |
| 启动文件里的堆栈 | `Stack_Size EQU 0x00000400`、`Heap_Size EQU 0x00000200` | Keil |
| 执行顺序 | `Reset → SystemInit → __main → main` | Keil |
| `SystemInit` 干什么 | **F1 HAL 版只设 VTOR/外部存储器，不配时钟**；F4/H7 版会开 FPU：`SCB->CPACR \|= ((3UL<<10*2)\|(3UL<<11*2))`（CP10/CP11 = Full Access） | F1/F4/H7 |
| `HAL_Init` 时跑什么 | F4 跑 **HSI 16MHz**、H7 跑 **HSI 64MHz**（所以 `HAL_Delay` 在此之前精度依赖 HSI） | F4/H7 |
| **`HSE_VALUE` 必须与实晶振一致** | 否则所有派生时钟与延时全错（H7 V7 板是 25MHz） | 通用 |
| 裸机 malloc 原理 | MicroLIB 分支导出 `__heap_base/__heap_limit`；标准库分支用 `__user_initial_stackheap` 返回 **R0=堆基址、R1=栈顶、R2=堆顶、R3=栈底** | Keil |
| scatter 示例 | `RW_SRAM123 0x30000000 0x48000`（288KB）；`*.o (RESET, +First)`；`.ANY (+RO/+RW/+ZI)` | Keil 专属 |
| **确认堆栈不重叠** | 在 map 文件里查 `Heap_Mem` 与 `Stack_Mem` 两段地址 | Keil |
| 链接错误码 | `L6411E No compatible library ... __main` ⇒ 库与前缀/架构不匹配（实测 c_* = 标准库、mc_* = MicroLIB） | Keil |
| MicroLIB 限制 | 禁半主机、**无文件 I/O、非线程安全**；重定向 `fputc` 就能用 printf；**需要手动勾选，不是默认**（文档"供 MDK 默认使用"错 `⚠校核C`） | Keil |
| 体积实测 | Code：标准库 5480 / MicroLIB 5168 / MicroLIB+printf 4100 | 参考量级 |
| DSP 库 | 宏 `ARM_MATH_CM4/ARM_MATH_CM7, __FPU_PRESENT=1, __CC_ARM`；M4F 加 `arm_cortexM4lf_math.lib`；报 `uses VFP register arguments, xxx does not` ⇒ **浮点 ABI 与库不匹配**，换库而不是改代码 | F4/H7、Keil/GCC |
| 优化取舍（C51） | Keil C51 优化级只有 **0~8**，语法 `OPTIMIZE(8,S/T)`；文档出现的 `#pragma OPTIMIZE(9)` 与 `__declspec(noinline)` **C51 不支持** `⚠校核C` | C51 |

## 2. 启动模式与串口/USB 烧录

| 项 | 内容 | 范围 |
|---|---|---|
| BOOT 采样时刻 | **复位后第 4 个 SYSCLK 上升沿锁存** BOOT 引脚 | F4 |
| 模式表 | `BOOT0=0` → 主 Flash（`0x08000000` 别名到 `0x00000000`）；`BOOT0=1,BOOT1=0` → 系统存储器（**`0x1FFF0000`**，串口 ISP）；`1/1` → SRAM | F4 |
| 冷知识 | **退出 Standby 模式会重新采样 BOOT 引脚** | F4 |
| 串口 ISP 可用外设 | USART1(PA9/PA10)、USART3(PB10/PB11 与 PC10/PC11)、CAN2(PB5/PB13)、USB DFU(PA11/PA12) | F4（引自 RM0090；`⚠校核C` CAN2 引脚作者未与 AN2606 交叉核对） |
| ISP 时的时钟 | USART 以 **HSI 16MHz** 跑 ⇒ ISP 波特率按 HSI 算；CAN/USB 需要 **4~26MHz 且为 1MHz 整数倍**的 HSE | F4 |
| 工具流程 | STM32 Flash Loader Demonstrator：置 `BOOT0=1/BOOT1=0` → Timeout 5s → 烧完**改回 BOOT0=0** 才运行 | 通用 |
| 一键下载电路的副作用 | flyMcu 流控可能把芯片卡在复位态 ⇒ 串口终端"卡死"、调试器也连不上（另见 debugger 篇） | 通用 |
| 4 线串口自动下载原理（C51 侧同构） | 芯片内 Bootloader **上电即监听 P3.0/P3.1 握手 + 自动测波特率**（扫描 2400~115200）；用 DTR/RTS 驱动三极管模拟"拔电再上电"实现免手按 | STC |

## 3. Flash / 存储器映射（型号差异极大，别混用）

### F4（1MB 示例）
| 项 | 值 |
|---|---|
| 扇区划分 | 4×16KB + 1×64KB + 7×128KB |
| 系统存储器（bootloader） | `0x1FFF0000 ~ 0x1FFF77FF`（30KB） |
| OTP | `0x1FFF7800 ~ 0x1FFF7A0F`（528B） |
| 选项字节 | `0x1FFFC000`（16B） |
| 解锁密钥 | `FLASH_KEY1 = 0x45670123`、`FLASH_KEY2 = 0xCDEF89AB` |
| 规则 | **编程前必须先擦**；`1→0` 可直接写、`0→1` 必须擦；`BSY=1` 时禁止写 `CR` |
| 错误标志 | `PGAERR / PGPERR / PGSERR / WRPERR`（地址/编程/段/写保护 四类，报错时按位判） |
| 代价 | **写/擦期间读 Flash 会锁总线**（影响取指，做双 bank/下载时要考虑） |
| F1 侧 | C8T6 = 64KB，**扇区(页) 1KB = 0x400**，一次写 16 位半字。`⚠校核C`：文档把 C8T6 归"小容量"（按 ST 分级是**中容量**，但 64×1KB 页这个数据本身对） |
| H7 侧 | **双 bank，各 8×128KB 扇区**；编程以 **256bits（一个 flash word）** 为单位；ECC 每 256bits 配 10bit；**没有 ART 加速器，改用 Cache** |

### H7 内存地图（值得背，分配缓冲区全靠它）
| 区 | 容量 | 地址 |
|---|---|---|
| AXI SRAM (SRAM1~3? 实为 D1 SRAM) | 512KB | `0x24000000` |
| SRAM1/2/3 | 128/128/32KB | `0x30000000 / 0x30020000 / 0x30040000` |
| SRAM4 | 64KB | `0x38000000` |
| BKPSRAM | 4KB | `0x38800000` |
| **DTCM** | 128KB | `0x20000000` |
| **ITCM** | 64KB | `0x00000000` |
> TCM **只有 CPU 和 MDMA 能访问** ⇒ 普通 DMA 缓冲区不能放 DTCM（与 `mcu-peripherals/sd-card-dcmi-fsmc-sram.md` §4 同一条坑）。

### AT32 的"零等待区 ZW / 非零等待区 NZW"（该家特有，容易配错）
- 默认 SRAM 96K → ZW 256K（`0x0800_0000~0x0803_FFFF`）+ NZW 768K；SRAM 224K → ZW128K/NZW896K。
- **NZW 执行速率约为 ZW 的 0.4 倍**（240MHz → 约 96MHz）。
- F435/437：SRAM 选 512K 模式 ⇒ ZW 只能 128K；选 128K 模式 ⇒ ZW 可到 512K；用 `EOPB0` 配置。
- 系统数据字节：**高字节必须是低字节的反码**，否则报 `USDERR`，且更新后要复位才生效。
- `⚠校核B`：文档一处"不能动态修改 ZW/NZW 分界"与同章"EOPB0 可设/SRAM 动态配置"矛盾。

## 4. IAP / 跳转与软件复位（照抄可用）

```c
JumpAddress = *(volatile unsigned *)(addr + 4);   // 取目标区栈顶后的复位向量
__set_MSP(*(volatile unsigned *)addr);            // 先设 MSP
((void (*)(void))JumpAddress)();                  // 跳转
// 软件复位（把所有中断关掉再复位，避免半途被打断）
__set_FAULTMASK(1); NVIC_SystemReset();
```
要点：跳转前要**停掉外设与中断、把向量表偏移 VTOR 改掉**（否则新程序的中断全飞）；
双 bank 芯片要考虑**擦写与执行是否同 bank**（`⚠校核C`：文档"擦 ZW 必须把擦写函数放 SRAM"过强，AT32 是双 bank，只有同 bank 才受限）。

## 5. 看门狗

- 原文对 IWDG 只留一句："**由专用低速时钟 (LSI) 驱动，主时钟故障时仍然工作**"（这就是它相对 WWDG 的意义）。
- `⚠校核D`：**IWDG/WWDG 的超时公式、LSI 典型 40kHz、WWDG 窗口与预分频、选项字节 RDP 级别行为、
  Sleep/Stop/Standby 唤醒源对比、备份区供电条件、Flash 擦写寿命** 在原 docx 中都是**空表/截图**，无文字依据。
  ⇒ 需要时另查手册，不要以为经验库已覆盖。

## 6. 工具链层的取舍清单

| 需求 | 选择 | 注意 |
|---|---|---|
| 省 Flash + 快速 printf | MicroLIB + 重定向 `fputc` | 无文件 I/O、非线程安全 |
| 要 `float` 格式化 | 标准库或自己 `vsnprintf` | C51 上 `%f` 约多占 5K ROM（见 `yjt/STC8H_8G/`） |
| 调试器连不上 | 查 NRST、SWD 脚占用、一键下载电路流控 | 见 debugger 篇 |
| 改完时钟数不对 | 检查 `HSE_VALUE`/`HEXT_VALUE` + `SystemInit`/`system_*_clock` | 两处都要改 |
| 链接报 ABI 不匹配 | 换对应浮点 ABI 的库 | 不要改编译选项硬凑 |
