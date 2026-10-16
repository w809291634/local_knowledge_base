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
| **J-Link Remote Server** | 目标机插 USB 跑 Server，开发机远程连 | 默认端口 **19020**（已由 V6.86e 配置页截图 `Listening port (default = 19020)` 证实，见 §5.2） |
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

## 5. 截图层补充（第 1 章 13 张图逐张读，2026-10-16）

> 上面几节的界面细节原文只存在于截图里。这里只录"看图才知道"的部分，行内标 `（ch01/00N）` 指导出图序号。

### 5.1 ST-Link 自制固件升级：界面判据

| 现象（截图所见） | 含义 / 处置 |
|---|---|
| Keil `Options for Target` → **Debug** 页 `Use: ST-Link Debugger`，点确定后弹 `ST-LINK Firmware Upgrade: Old ST-LINK firmware detected. Do you want to upgrade it?` | Keil 侧能识别到"固件偏旧"，但**它只提示、不替你升到目标版本**；要做 V2-1/V2-A/V2-B 仍须自己用 CubeProgrammer 刷 `V2.J28.M18`（ch01/003） |
| CubeProgrammer 的 `ST-Link Upgrade` 页里 **`Device Connect` 按钮是灰的**，弹窗 `ST-Link is not in the DFU mode. Please restart it.` | **没进 DFU 的直接判据就是按钮灰 + 这句报错**。处置：空接（不连目标板）→ 拔插 mini USB → 再点 Device Connect（ch01/004） |
| 升级完成弹窗 `Upgrade is successful.`，主窗口下方出现形如 `STM32 +STMB Debugger V2.J37.M7` 的版本串 | 版本串以工具显示为准，不要凭 Keil 提示判断；截图末段字符不清 `⚠校核D`（ch01/005） |

### 5.2 J-Link Remote Server：两个版本的界面不一样，别照旧图找按钮

| 版本 | 截图里的界面 | 要点 |
|---|---|---|
| **V6.34f** | 启动即弹两选一：`Use LAN` / `Use Tunnel server`；主窗口只有拓扑图 + `Stay on top` + 日志区 + 底部状态行（ch01/007、008） | 老版**没有**端口与连接串设置项 |
| **V6.86e** | 配置页分两块：`J-Link connection`（`USB` + `Serial No.` / `TCP/IP`）、`Server settings`（`Use LAN` / `Use SEGGER tunnel server` / `Use custom tunnel server`）+ **`Listening port (default = 19020)`**；主窗口多出 `Connection information`：`Connection type = LAN`、**`Client connection string = ip 192.168.56.1`**（带 Copy 按钮）、`Show log`（ch01/009） | §2 里"默认端口 19020"的**依据就是这一屏**（原 `⚠校核D` 可解除） |

**连接成功/失败的判据（重要，容易记反）**：

- 日志 `Connected to J-Link with S/N -1` 在"等待客户端"和"客户端已连上"**两种状态下都出现**（ch01/008 与 ch01/012 对比）
  ⇒ **`S/N -1` 不是"没插到调试器"的判据**，不能拿它判断链路好坏。
- 真判据是**拓扑图连线颜色 + 底部状态行**：红线上带 `X` = 未连上（状态行 `Waiting for client connection`）；
  绿线 + 日志出现 `Client connected.` + 状态行 `Connected to 192.168.100.132 - Idle` = 已连上（ch01/012）。

### 5.3 开发机（IAR）侧填的是穿透地址，不是目标机 IP

`Options → Tools → J-Link/J-Trace → Connection` 页（ch01/010）：

| 项 | 截图取值 | 说明 |
|---|---|---|
| Communication | 选 **`TCP/IP`**（不是 USB），下拉 `IP address` | 选 USB 就变成本地调试了 |
| IP address | **`zhiyun360.com:25508`**（FastTunnel 类穿透给的 `域名:端口`） | **常见混淆点**：目标机 Server 监听 19020，穿透映射出的外网端口是另一个（这里是 25508）。开发机填的是**穿透端口**，不是 19020 |
| Interface | `SWD`（`JTAG` 未选），`TAP number = 0` | 与本地调试一致 |

**首次连接会长时间停在** `Busy — Starting debugger session: Loading debug file`（ch01/011）：
调试信息文件要整份走穿透链路，**慢 ≠ 断**，不要在这一步重启 Server/隧道，否则端口会重新分配更难排。

