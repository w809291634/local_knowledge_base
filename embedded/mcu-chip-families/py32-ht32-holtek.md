# PY32（普冉）与 "HT32"（实为 Holtek 8 位 BH67F2472）

> `⚠校核` 见 `embedded/mcu-peripherals/ERRATA-*.md`。**两条重要的"名字坑"先看**：
> ① 文档把 PY32 写成"普林赛斯"，实际是 **普冉半导体（Puya，puyasemi.com）**；
> ② 文档"HT32"章标题下的内容**全是 Holtek（盛群）8 位单片机 BH67F2472**（文字层与 42 张截图一致，
> 官网归类 `Health Care Flash MCU / Glucose Meter LCD Flash MCU`），**没有 HT32F(M0/M4) 正文**
> ⇒ 想找 HT32F 的资料不要来这一篇。（2026-10-16 曾误判"截图里有 HT32F"，那是未看图先写的结论，已删除。）

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
| ~~作者自标未验证~~ **已结案** | 低速模式 `CKS=111` 时串口不打印："不知道具体原因" —— **根因见 §3.1（波特率发生器时钟是 `f_H`，低速模式下 `f_H` 可关）** |

## 3. 截图层补充 · 第 6 章 001–042（2026-10-16 逐张读）

> `（ch06/0NN）` 见 `Temp/mcu_doc/media/ch06/INDEX.tsv`。文字层只给了寄存器**名字清单**，
> 位定义/真值表/向量号**只在图里** ⇒ 本节是唯一副本。看不清一律标"截图不清"。

### 3.1 本章最有价值的一条：低速模式串口不打印的**根因**（ch06/033 + 032）

- `USIMn UART 数据传输方框图（UnSWM=0）`：`TSR(MSB…LSB) → UTXn`、`URXn → RSR → Buffer → UnTXR_RXR ↔ 数据总线`，
  而 **`Baud Rate Generator` 的时钟输入标的是 `f_H`**。
- 系统工作模式表（ch06/032）：**低速模式 = `CKS2~CKS0 = 111` → `f_SYS = f_SUB`，此时 `f_H` 可关（表注 ⁽¹⁾）**。
- ⇒ **两者合起来就是根因**：低速模式下波特率发生器失去 `f_H` ⇒ 波特率不成立 ⇒ 串口不出字。
  **§2 末尾那条"作者自标不知道具体原因"的未验证项，至此可以结案**：
  对策 = 低速模式要打印就必须保持 `f_H` 上电（改 `CKS` 档位或先切回快速模式打印），或把 UART 换到不依赖 `f_H` 的时基上（图里没给这种选项 ⇒ 需查手册确认）。

### 3.2 时钟与模式（ch06/030、031、032、034）

| 项 | 图里内容（照抄） |
|---|---|
| 振荡器（030） | `HXT` 外部高速晶振 **400kHz~16MHz**（脚 `OSC1/OSC2`）；`HIRC` 内部高速 RC **4/8/12MHz**；`LXT` **32.768kHz**（`XT1/XT2`）；`LIRC` **32kHz** |
| 高速侧（031） | `HIRC/HXT` 由 **`HIRCEN/HXTEN`** 使能 → 选择器 **`FHS`** → 经 `IDLE0/SLEEP` 门控得 `f_H` → **`Prescaler` 出 `f_H、f_H/2、f_H/4、f_H/8、f_H/16、f_H/32、f_H/64、f_SUB`，由 `CKS2~CKS0` 选 → `f_SYS`**，并可输出到 **`CLO` 脚** |
| 低速侧（031） | `LXT/LIRC` 由 **`LXTEN`** 使能 → 选择器 **`FSS`** → `IDLE2/SLEEP` 门控 → `f_SUB`；`f_LIRC` 直接输出 |
| 六种模式（032） | 快速 / 低速 / 空闲0 / 空闲1 / 空闲2 / 休眠，由 **`FHIDEN`、`FSIDEN`、`CKS2~CKS0`** 组合决定（表里逐行给出 CPU、`f_SYS/f_H/f_SUB/f_LIRC` 的 On/Off） |
| 时基（034） | `f_SYS / f_SYS/4 / f_SUB` 经 **`CLKSEL[1:0]`** → `f_PSC` → 预分频 → **`f_PSC/2^8 ~ f_PSC/2^15`**；再经与门 **`TB0ON`+`TB0[2:0]`**、**`TB1ON`+`TB1[2:0]`** 出 Time Base 0/1 中断 |

⇒ **时基可以选 `f_SUB`** ⇒ 空闲/低速下仍需计时就用 `f_SUB` 档；这与 §"定时基准 Timebase0"配套。
⇒ 文字层"6 种功耗模式"由本表**逐项证实**（不是 4 组合的算术问题：空闲0/1/2 是 `FHIDEN/FSIDEN` 的三种有效组合 + 快速/低速/休眠）。

### 3.3 中断向量表（ch06/035，唯一副本）

顶部注：**`EMI auto disabled in ISR`**；优先级 High → Low 按表序。

| 中断 | 请求标志 | 使能位 | 向量 |
|---|---|---|---|
| INT0 Pin | `INT0F` | `INT0E` | **04H** |
| INT1 Pin | `INT1F` | `INT1E` | 08H |
| A/D | `ADF` | `ADE` | 0CH |
| M.Function 0/1/2 | `MF0F/MF1F/MF2F` | `MF0E/MF1E/MF2E` | 10H/14H/18H |
| INT2 Pin | `INT2F` | `INT2E` | 1CH |
| INT3 Pin | `INT3F` | `INT3E` | 20H |
| Time Base 0/1 | `TB0F/TB1F` | `TB0E/TB1E` | **24H**/28H |
| USIM0/USIM1 | `USIM0F/USIM1F` | `USIM0E/USIM1E` | 2CH/30H |
| SPI | `SPIF` | `SPIE` | 34H |

⇒ **向量间隔 4 字节**、所有中断共用总开关 `EMI`、**进 ISR 硬件自动关 EMI** ⇒
嵌套中断要自己在退出前重开；`Time Base 0 = 0x24` 与 §"工具与烧录"里那条实测一致（证实）。
⇒ §"串口中断与 USIM 的 SPI/I²C 共用同一个向量"在表里对得上：**USIM0/USIM1 各一个向量**，
而 USIM 可配成 UART/SPI/I²C ⇒ **同一 USIM 的不同模式共用该 USIM 的向量**，不是与独立 SPI(34H) 共用。

### 3.4 OPA / IREFC 位表与真值表（ch06/010~014，唯一副本）

| 寄存器 | 位 7 → 0（照抄） | R/W | POR |
|---|---|---|---|
| `OPA1C` | `OPA1OFM \| OPA1RS \| OPA1EN \| OPA1OF4 \| OPA1OF3 \| OPA1OF2 \| OPA1OF1 \| OPA1OF0` | 全 R/W | 全 0 |
| `OPA2C` | 同构（`OPA2…`） | 全 R/W | 全 0 |
| `GSC` | `— — — — \| GSW3 \| GSW2 \| GSW1 \| GSW0` | 低 4 位 R/W | 低 4 位 0 |
| `IREFC` | `OP2DO \| OP1DO \| — \| IREFEN \| BAIDEN \| — \| DACVRS1 \| DACVRS0` | **`OP2DO/OP1DO` 只读**；`IREFEN/BAIDEN/DACVRS1/0` R/W | 全 0 |

**`OPA1OFM`/`OPA1RS` 对开关网络 S0/S1/S2 的真值表（照抄，`x` = Don't care）**：

| `OPA1OFM` | `OPA1RS` | S0 | S1 | S2 |
|---|---|---|---|---|
| 0 | x | ON | ON | OFF |
| 1 | 0 | OFF | ON | ON |
| 1 | 1 | ON | OFF | ON |

⇒ **`OFM/RS` 两位决定三路模拟开关的接法** ⇒ 换增益/接法只动这两位，
`OPA1OF4~OF0` 是 5 位"输出反馈选择"字段（与 §`OPA1C` 位表配套，文字层没给位宽）。
⇒ `IREFC` 的 `OP1DO/OP2DO` 是**只读回读**位 ⇒ 想判运放数字输出状态只能读、不能写。

### 3.5 ADC 寄存器与数据对齐（ch06/036~042，唯一副本）

| 寄存器 | 位 7 → 0（照抄） |
|---|---|
| `SADC0` | `START \| ADBZ \| ADCEN \| ADRFS \| SACS3 \| SACS2 \| SACS1 \| SACS0`（**`ADBZ` 是只读**，其余 R/W，POR 全 0） |
| `SADC1` | `SAINS2 \| SAINS1 \| SAINS0 \| SAVRS1 \| SAVRS0 \| SACKS2 \| SACKS1 \| SACKS0`（全 R/W，POR 全 0） |
| `SADOL` | `ADRFS=0`：`D3 D2 D1 D0 — — — —`；`ADRFS=1`：`D7…D0` |
| `SADOH` | `ADRFS=0`：`D11…D4`；`ADRFS=1`：`— — — — D11 D10 D9 D8` |

| `SAVRS[1:0]` | 参考源 |
|---|---|
| `00`、`11` | **`V_REF` 引脚**（外部参考） |
| `01` | **`AV_DD`**（ADC 电源电压） |
| `10` | **`V_DACVREF`**（DAC 参考电压） |

- 通道（ch06/036、037）：外部 **`AN0~AN5`** 由 **`SACS3~SACS0`** 选通（**引脚共用选择**）；
  内部信号 **`OP1S0/OP1S1/OP2O/V_DAC0/V_DD/4`** 由 **`SAINS2~SAINS0`** 选通；
  `V_DD/4` 由 `BATDEN` + **15K/5K 分压**得到；A/D 时钟 = **`f_SYS ÷ 2^n (n=0~7)`**，由 `SACKS2~SACKS0` 控。
- **注 1（照抄）**：选 `OP1Sn (n=0~2)` 时，实际测的是"**经 OP1Sn 引脚实现的 OPA1 输出电压**"。
- **注 2（照抄）**：`BATDEN` 位在 **`IREFC`** 里（不在 SADC 寄存器）。
> ⚠校核：ch06/038 同一张表里行名写作 **`ADFRS`**、位定义写作 **`ADRFS`** ⇒ 图内两种拼法并存（照抄，疑原文笔误）。
> ⚠校核：`ADRFS=0/1` 两种对齐方式**必须与读法配套**；文字层没提这个位 ⇒
> 换 `ADRFS` 不重算移位 = 数值莫名差 16 倍，这是本芯片 ADC 的头号坑。

### 3.6 调试器与烧录（ch06/002~006，唯一副本）

| 项 | 图里内容 |
|---|---|
| BH67F2472 工具行（002） | `ICE Type = e-Link`、`ICE Part No = e-Link + BH67F2472`、**`Programming Timing = Flash Type-31`**、**`ICP Type = ICP-2C`**、**`ICPCK = PA2`**、**`OCDSDA = PA0`**、**`OCDSCK = PA2`** |
| e-Link32 Lite vs Pro（003） | Lite：内部供电 `3.3V 或 5V（需手动焊接）`、**无离线烧录**、接口 `SWD + 虚拟 UART`、支持 `HT32 Flash MCU`、烧录软件 `HT32_ICP_Tool`、尺寸 `36.7×15×6.8mm`；Pro：内部供电不支持、离线烧录 `SPI Flash 8Mbit`、尺寸 `84×42×13mm` |
| 指示灯/供电跳线（004） | 绿灯常亮 = USB 连接成功、熄灭 = USB 未识别；蓝灯闪烁 = 烧录中、熄灭 = 待机；**跳线焊 1-2 = 烧录器供 5V、焊 2-3 = 供 3.3V、默认不焊 = 由目标板自供** |
| 排针（005、006） | `1 VDD`、`2 SWDIO`、`3/5/9 GND`、`4 SWCLK`、`6 NC`、`7 VCOM_RXD`、`8 VCOM_TXD`、`10 nRST`（正面偶数脚、背面奇数脚） |

⇒ **`ICP-2C` + `PA0/PA2`** 与 §"ICP 烧录脚 PA0=ICPDA、PA2=ICPCK"完全对上，且补了 **`Flash Type-31`** 这个烧录时序选项（选错会烧不进去）。
⇒ **e-Link32 Lite 只支持 HT32（32 位）族，不支持 BH67F2472** ⇒ 8 位机必须用 **e-Link**（002 行）；
   这是"手里只有 e-Link32 Lite 却连不上 8 位 Holtek"的原因。

### 3.7 血糖前端的通用方法（ch06/016~029，去掉产品参数后的可复用部分）

- **两步测量法**（022~028）：空试纸时 `V_RF = I×R_F = 0`、输出被虚短钳在偏置（图内 **`V_out = 300mV`**，
  文字层注"我们实际是 400mV" ⇒ **以板卡实测为准**）；滴血后 `V_out2 = V_bias + I_glucose × R_F`；
  **两次相减消偏置** ⇒ `I_glucose = ΔV / R_F`；最后 `血糖 = f(I, 温度)`。
- **失调校准代码**（018）：`Opa1_Voscancellation()` —— 写 `_opadc = 0x01` 进 Vos 校准模式 → 延时 →
  `0xFF` → 循环 32 次读 `_op1do` 判决极性做逐位逼近 → 取两次平均写回 → 收尾 `0x1F`。
- **跨阻前端**（017）：`AD8552` 类运放，反馈 **`180k` 并 `100nF`**（增益 + 带宽限制）、输入串 `10R`、
  同相端偏置 `1.5V`、输出串 `10K`、钳位二极管 `SMF6.5CA`。
- **片内档位切换**（020）：`OP1S0/OP1S1/OP1S2` 三脚分别接 **4.99K / 49.9K / 490K** ⇒
  用 `S0/S1/S2` 开关网络换跨阻档 ⇒ **量程切换靠开关选反馈电阻，不改软件增益**。
> 板级位号（R174/R175/R176/C211/STRIP TEST）与实测数值（400/820/220.7031/1272/4422 等）属产品参数，
> 只保留"脚用途 + 方法"，不作为通用知识引用。
