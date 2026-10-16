# 调试器实操：ST-Link 自制 / J-Link 远程 / 示波器

> 与 `debugger-jlink-stlink-wchlink.md`（救砖、双接口双驱动）互补。来源：《单片机外设和调试基础知识.docx》调试章，2026-10-16。

## 1. ST-Link 自制（型号与固件版本必须对上）

| 项 | 内容 |
|---|---|
| 标准 V2 固件 | `V2.J16.S4`（原文此处句子截断，版本号后的说明缺失 `⚠校核A`） |
| **做 V2-1 / V2-A / V2-B** | **必须** 用 `V2.J28.M18` —— 用错固件是"做出来只能认到 V2 普通版"的常见原因 |
| 升级工具 | `STM32CubeProgrammer`（**需要 JRE**） |
| 升级前置 | 设备必须先进 **DFU 模式**：空接（不连目标板）→ 插拔 mini USB 线 → 在 CubeProgrammer 里 `Device Connect` |
| 与 GD32 的交叉坑 | GD32 官方口径"ST-Link 仅完美支持 F1 系列"（属厂商 FAQ 措辞，不是绝对技术限制，`⚠校核C`）⇒ 用 ST-Link 烧/调 GD32 出问题时要考虑换 J-Link/GD-Link |
| SWD 接线 | **SWDIO = PA13、SWCLK = PA14 + GND**；VCC 只用于检压、不供电 |
| JTAG 额外占用 | TDI=PA15、TDO=PB3、nTRST=PB4；`__HAL_AFIO_REMAP_SWJ_NOJTAG()` 可释放 **PB3/PB4** |
| 常见"引脚莫名不能用" | F1 复位后 `SWJ_CFG=000` ⇒ **JTAG 全启用，PB3/PB4 默认是 JTAG 脚**；文档一处写"默认已部分禁用、PB3/PB4 可当普通 GPIO"是错的（同文自己给了释放函数）`⚠校核C` |
| 兼容 | DAPLink / ST-Link / J-Link 在 SWD 上完全兼容 |
| Keil 特有 | 下载后必须按复位才运行 ⇒ **NRST 没接到调试器**所致 |

## 2. J-Link 远程调试（跨网段/异地调试的可行方案）

| 方案 | 做法 | 要点 |
|---|---|---|
| **J-Link Remote Server** | 目标机插 USB 跑 Server，开发机远程连 | 默认端口 **19020**（文档只说高版本软件里可见，未给手册依据 `⚠校核D`） |
| 内网穿透 | ngrok / **FastTunnel** | 无公网 IP 时用；文档提到 `H:\ngrok2.exe`（个人路径，不入库） |
| 支持的 IDE | IAR / SES / **Ozone** / 远程 GDB | 文档给的是"内网穿透实现 jlink 远程 GDB"的实操路线 |
| 适用场景 | 板子在实验室、人在外面；或目标机只有 USB 而无网口 | 与 `debugger-jlink-stlink-wchlink.md` 的救砖流程配合使用 |

## 3. 示波器（普源 DS1102 型号实操）

| 控件 | 作用 | 易错点 |
|---|---|---|
| 垂直 scale 旋钮 | 通道灵敏度缩放 | **点击**可归零（自动设置） |
| 水平 scale 旋钮 | 时基缩放 | 同上，点击归零 |
| 垂直位置旋钮 | 位移 | 点击回零 |
| 面板下方按钮 | 选时基 / **ROLL** / **XY** | **XY 模式会覆盖其他设置**，看完记得切回 |
| `level` 旋钮 | 触发电平，可读数 | 波形左右漂 = 没触发到 ⇒ 先调 level 再谈测量 |

**用法与外设的对应**（来自本次精读的实测经验）：
- 判 I2C/SPI 时序、软件模拟 I2C 的真实延时 —— 文档反复强调**"必须用逻辑分析仪/示波器实测"**，
  名义 `delay_us(1)` 实测可能是 1.25us 或 4us（CC2530 那套延时表见 `mcu-peripherals/i2c-spi-and-device-drivers.md` §2）。
- 量睡眠占比：在 `sleep_enter/exit_callback` 里翻一个 IO（`APP_IO_DEBUG_1/0`），
  看占空比即知"多久真在低功耗"，比串口打点更不干扰系统（见 `jieli_soundbox_sdk/common/power-consumption-debug.md`）。
- 量 PWM/编码器：直接看周期与占空，验证 `ARR+1` 类算错（见 `mcu-peripherals/timer-pwm-adc-dma.md` §4）。

## 4. 一句话清单

| 症状 | 先查这里 |
|---|---|
| 自制 ST-Link 只认成普通 V2 | 固件应是 `V2.J28.M18` |
| CubeProgrammer 升级失败 | 没进 DFU（空接 + 插拔线 + Device Connect）/ 没装 JRE |
| PB3/PB4 当 GPIO 不工作 | JTAG 默认占用，调 `REMAP_SWJ_NOJTAG` |
| Keil 下载后不跑 | NRST 未接调试器 |
| 远程调试连不上 | 端口 19020、Server 是否在被调试机、穿透工具通道是否掉线 |
| 波形一直左右漂 | level 触发电平没设对 |
