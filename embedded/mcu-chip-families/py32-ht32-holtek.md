# PY32（普冉）与 "HT32"（实为 Holtek 8 位 BH67F2472）

> `⚠校核` 见 `embedded/mcu-peripherals/ERRATA-*.md`。**两条重要的"名字坑"先看**：
> ① 文档把 PY32 写成"普林赛斯"，实际是 **普冉半导体（Puya，puyasemi.com）**；
> ② 文档"HT32"章标题下的内容**全是 Holtek（盛群）8 位单片机 BH67F2472**，没有任何 HT32F(M0/M4) 正文
> ⇒ 想找 HT32F 的资料不要来这一篇。

## 1. PY32（以 PY32F002B 为例）

| 项 | 内容 |
|---|---|
| 内核 | Cortex-M0+ |
| Keil 支持包 | 在 `keil.arm.com` 搜 `py32` |
| 固件库 | `PY32F002B_Firmware_V1.2.1.zip` |
| **最大的坑：PC0 默认是 NRST** | Option Byte 把 PC0 配成了复位脚 ⇒ 即使 `MODER0/OTYPER0/ODR0` 写 0 也**读出来恒高、`IDR0=1`**，把 PC0 当普通 GPIO 用完全不通 |
| 解法 | 写选项字节：`OB_SWD_PB6_NRST_PC0 = 0x00000000` ↔ `OB_SWD_PB6_GPIO_PC0 = FLASH_OPTR_NRST_MODE`；必须走 `HAL_FLASH_OBProgram()` + `HAL_FLASH_OB_Launch()`（**OB_Launch 会立即复位**） |
| 禁止做法 | **不能**用 `GPIOx_AFR` 复用切换来绕开 NRST 功能 |
| 查询方法 | 读 `FLASH->OPTR & FLASH_OPTR_NRST_MODE` 判断当前配置 |
| 附带规格 | NRST 模式的毛刺过滤最小 **20µs** |
| 复用价值 | 这一类"引脚被选项字节征用"的问题在 STM32 上是 `nBOOT0/nJRQ/PDR_ON` 等；**症状相同：寄存器写了没效果。先查选项字节，再查时钟** |

作者为此自制了 `User_Flash_Enable_PC0_GPIO()` 函数（项目内脚本，不入库）。

## 1.1 截图层补充 · 第 5 章（3 张图全读，2026-10-16）

### (a) 选项位表：PC0 / PB6 的三种归属（ch05/003，**文字层没有这张表**）

| 位 | 名称 | 读写 | 功能（照抄） |
|---|---|---|---|
| 31 : 15 | Reserved | – | – |
| 14 | `NRST_MODE` | RW | 与 `SWD_MODE` 组合决定 PC0/PB6 归属 |
| 13 | `SWD_MODE` | RW | 同上 |

组合编码（`NRST_MODE` `SWD_MODE`，照抄）：

| 编码 | PC0 | PB6 |
|---|---|---|
| `0 X` | **NRST** | **SWD** |
| `1 0` | **GPIO** | SWD |
| `1 1` | **SWD** | GPIO |

⇒ 三条以前没写全的结论：
1. **默认态是 `0X`** ⇒ PC0 天生是复位脚、PB6 天生是 SWD ⇒ 这就是 §1"写寄存器没反应"的根因位。
2. **`1 1` 是把 SWD 从 PB6 挪到 PC0**（此时 PB6 释放成普通 GPIO）
   ⇒ 需要**同时保住 PC0 和 PB6 两个普通 IO** 时，唯一出路是把调试口挪到 PC0（代价：失去常规 SWD 脚，
   要改用 SWD 的另一对脚或放弃在线调试）。**这一档以前完全没记录。**
3. 想"PC0 当 GPIO 且保留 SWD"只有 **`1 0`** 一种写法 ⇒ 对应 §1 的 `OB_SWD_PB6_GPIO_PC0`。
   **`0 X` 与 `1 1` 都会让 PC0 不是普通输出**，别以为设成 `1 1` 也能当 GPIO。

### (b) Keil 支持包（ch05/001）

Pack 商店里 Puya 的 PY32 **按子系列分成多个 DFP 包**，每行右侧是 `Download version x.y.z` 链接 + 设备数
（图里可辨三行，版本号分别 **1.3.0 / 1.2.0 / 1.1.0**；子系列名与设备数**截图不清**）。
⇒ 与 §1"在 `keil.arm.com` 搜 py32"一致，但要点是**别只装一个包**：
   PY32F002 与 PY32F0xx 其他子系列的头文件/算法库不通用，装错包的表现是"能建工程但没有对应型号"。

### (c) PY32F002B 型号清单（ch05/002，选型手册页）

标题 `PY32F002B系列`（"超值MCU"），下列 5 个型号 + `查看更多`：
`PY32F002BF1S6`、`PY32F002BF1S16`(疑)、`PY32F002BW1SS6`(疑)、`PY32F002BD1SS6`(疑)、`PY32F002BF1SL7`
⇒ **后四个的封装后缀截图不清，不要据此下单/选型**；可确认的是同一 F002B 系列下有 **F1S6 / W1S / D1S / L7** 等多种封装与容量档。

## 2. Holtek 8 位 BH67F2472（血糖仪方案 MCU）

### 芯片规格（照抄）
| 项 | 值 |
|---|---|
| 内核 | **8 位**，指令 115 条，**硬件堆栈 16 层** |
| 存储 | Flash **32K×16**、RAM **2048×8**、**True EEPROM 2048×8**（不用模拟、不怕掉电） |
| IO | 58 |
| 模拟 | **12bit ADC（6 外部通道）+ 12bit DAC + 2 个 OPA** |
| 显示 | LCD 驱动 36×4 / 34×6 / 32×8 |
| 通信 | **USIM×2**（可配 SPI/I²C/UART）+ 独立 SPI |
| 其他 | IAP、**OCDS**（在线调试，占用 PA0/PA2） |
| 电压/频率 | 4M/8M → 2.2~5.5V；**12M → 2.7~5.5V**；16M → 3.3~5.5V；16MHz 下指令周期 0.25µs |
| 时钟源 | HIRC 4/8/12M、LIRC 32k、HXT、LXT 32.768k |
| 系统时钟分频 | `SCC` 的 `CKS2~0` 选 `fH` 或 `fH÷2~÷64`；`FHS`/`FSS` 选高速/低速源 |
| 功耗模式 | 6 种：快速 / 低速 / 休眠 / 空闲0 / 空闲1 / 空闲2（由 `FHIDEN`/`FSIDEN` 组合决定） |

### 模拟前端（血糖测量的核心，通用方法可复用）
| 寄存器 | 位 |
|---|---|
| `OPA1C` | `OPA1OFM`、`OPA1RS`、`OPA1EN`、`OPA1OF4~0` |
| `GSC` | `GSW3` = VG 接地；`GSW2/1/0` 把 `OP1S2/1/0` 接到 `OP1O` |
| `IREFC` | `OP2DO`、`OP1DO`、`IREFEN`、`BATDEN`、`DACVRS1~0`；**VDAC 可提供 0~0.5×VDACVREF** |
| `SADC0` | `START`、`ADBZ`、`ADCEN`、`ADRFS`、`SACS3~0` |
| `SADC1` | `SAINS2~0`（输入选择）、`SAVRS1~0`（参考）、`SACKS2~0`（= fSYS ÷1/2/4/8/16/32/64/128） |

**两条硬性时序/安全规则（文档明确写，务必记住）**：
1. **选择内部信号作输入时（`SAINS=001~110`），`SACS` 必须设成 `0110~1111` 让外部通道浮空**；
2. **选择 AVDD / VDACVREF 作参考时，VREF 引脚必须复用为别的功能**，否则**可能损毁芯片**。

### 测量方法（"测两次相减"的电流型传感方案）
```
ΔV / RF = 电流        // RF = 反馈电阻
实测：基线 400mV、RF = 49.9kΩ、ΔV = 220.70mV ⇒ 4.42µA
标定：9KΩ ↔ 2.601V，90KΩ ↔ 0.620V
流程：Opa1_VosCalibration() → initBgmDcCurrent() → getBgmDcCurrent()
```
⇒ 这套"先做偏置/失调校准（Vos Calibration），再用反馈电阻把电压差换算成电流"的做法
**适用于所有电化学/电流型传感器前端**，与是不是 Holtek 芯片无关。

### 工具与烧录
| 项 | 内容 |
|---|---|
| 调试器 | e-Link、e-Link32 lite（HT32MCU，SWD）、HT-IDE3000 + HT8 CodeConfig、HT32 ICP Tool |
| **ICP 烧录脚** | **PA0 = ICPDA、PA2 = ICPCK**，加 VDD/VSS；与 OCDS 是同一对脚 |
| 中断向量复用 | **串口中断与 USIM 的 SPI/I²C 共用同一个向量** ⇒ 必须在中断里判来源 |
| 定时基准 | Timebase0 向量 `0x24`；低速模式下 `_pscr = 0x03` + `_tb0c` 仍能得 1s（作者实测） |
| 作者自标未验证 | 低速模式 CKS 全 1 时串口不打印，"不知道具体原因" |
