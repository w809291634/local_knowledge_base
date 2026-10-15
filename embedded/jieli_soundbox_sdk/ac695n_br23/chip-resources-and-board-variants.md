# AC695N / BR23：芯片资源表与 19 个板级对应关系

> **型号 ≠ 内核**：编译宏 `CONFIG_CPU_BR23`、烧录 `-dev br23`；芯片系列是 AC695N/AC696N（手册 Ch7 p50 明确这份 SDK 覆盖两系列）。
> 本文件只收**型号/内核相关**的事实，通用打法在 `../common/`。

## 1. 能力表（手册 p6-p9，判断"能不能做"的第一手依据）

| 项 | 支持内容 |
|---|---|
| 解码 | CVSD / MSBC / SBC / AAC / G729 / MP3 / WMA / FLAC / APE / M4A / AMR / DTS / G726 / MIDI + 加密播放 |
| 编码 | CVSD / MSBC / G726 / MP3 / ADPCM / SBC |
| 蓝牙 | 经典 + BLE + TWS + 对箱 + **内置 FM 发射与接收**（50k/100k 步进） |
| 音源通路 | iis / hdmi / spdif 音源 **暂不支持** |
| EQ/DRC | 在线调试 **20 段** |
| 特效 | 魔音 / 啸叫抑制 / 变速 / 闪避 / 消人声 / 变调 / 电音 |
| 按键 | iokey / adkey / irkey / touchkey / rdekey / slidekey |
| DAC | 8 种通道组合：MONO_L、MONO_R、LR、MONO_LR_DIFF、DUAL_LR_DIFF、三声道×2（前L前R后L/后R）、四声道（`board_config.h:44-53`） |
| ADC | **同时 3 路 ad**；4 路 dac 组合 |
| 显示 | **仅 led + 断码 lcd**（点阵屏见版本史 3.0.0） |
| 系统时钟 | 最高 **240 MHz** |
| 无线充电 | **只在充电仓方案支持** |
| 中断 | 不可屏蔽中断优先级 ≥6 不开屏蔽 |
| 升级 | U盘 / SD；支持 uboot ui、io 保持、**ufw 只识别后缀** |

## 2. 时钟表（BR23 `cpu/br23/clock_cfg.h`，功耗与算力预算）

各模式 idle 时钟：BT/MUSIC **24**、FM **48**、LINEIN **96**、PC **120**、REC/RTC/SPDIF **12**、BOX **24**。
算法时钟举例：`AEC16K_ADV 120`、`DEC_MP3 46`。接口与"用完必须 remove"见 `../common/app-task-state-machine.md` §6。

## 3. 中断默认优先级（`apps/soundbox/board/br23/irq_config.c` 的 `irq_pro_list[]`）

范围 0(低)~7(高)，官方"不建议改"。已知关键值：`IRQ_TIME2_IDX` = **6**（`TCFG_LED7_RUN_RAM` 时，关总中断仍能进）否则 5；
`IRQ_TIME3_IDX` = 3（红外/RF 都用它）；UART0/1 = 3；UART2 = 0；CTMU = 1；PORT 唤醒 = 3。
**任务优先级另有一套：0~6**，见 `task_table.c`。

## 4. 19 个板级 → 型号 / 方案映射（`apps/soundbox/board/br23/`，`board_config.h:8-41`）

当前生效：`CONFIG_BOARD_AC695X_DEMO`。

| 板级目录 | 型号/方案 |
|---|---|
| `board_ac695x_demo` | AC695x 通用 demo（**本工程的开发基线**） |
| `board_ac6951_kgb_v1` / `board_ac695x_audio_effects` | AC6951 / K歌宝（音效方案板） |
| `board_ac6951g` | AC6951G |
| `board_ac6952e_lighter` | AC6952E，**蓝牙点烟器** |
| `board_ac6954a_demo` | AC6954A，**SPDIF-HDMI-IIS 测试板** |
| `board_ac6955f_headset_mono` | AC6955F，**蓝牙带卡耳机** |
| `board_ac695x_charging_bin` | 智能充电仓（**无线充电唯一可用方案**） |
| `board_ac695x_multimedia_charging_bin` | 多媒体充电仓 + 发射器 |
| `board_ac695x_btemitter` | 蓝牙发射器 |
| `board_ac695x_tws` / `board_ac695x_tws_box` | 纯对箱 / 对箱 |
| `board_ac695x_soundcard` | 声卡 |
| `board_ac695x_smartbox` | 杰理之家 APP 音箱（**所有协议开关的示例板级**） |
| `board_ac695x_lcd` | **唯一带屏板级** |
| `board_ac695x_megaphone` | 大声公 / 扩音器 |
| `board_ac695x_cvp_develop` | 第三方清晰语音处理模块开发 |
| `board_ac6083a` / `board_ac6083a_iap` | **AC6083A**（不同一颗芯片），`_iap` 为 IAP 版本 |

**板级自带警告**（`board_config.h:23-36`）：`audio_effects` 与 `megaphone` 两块板已按现有芯片资源优化配置音效组合，
**改了配置导致数据流卡顿就表示不支持（触及芯片性能极限）** —— 这两块板没有"再压榨"的空间。

**结构陷阱**：`board_config.h` 虽然只选一个 `CONFIG_BOARD_*`，但**无条件 include 了全部板级 cfg**（`:53-74`），
靠各 cfg 内部 `#ifdef CONFIG_BOARD_X` 自我隔离。改错文件里的宏可能完全没作用。

## 5. 已确认的型号差异点（只这些，别的不成立）

| 差异 | 内容 | 来源 |
|---|---|---|
| **AC696N vs AC695N 调音工具** | AC696N **暂不支持新版调音工具**，沿用旧工具；AC695N 用新版 | 配置工具说明 p1 注意事项5、p7 条9 |
| **升级 IO 保持** | `DEV_UPDATE_SUPPORT_JUMP` **目前只有 br23 / br25 支持** | `app_config.h:376` |
| Flash 容量影响 EQ 特性 | `CONFIG_SOUNDBOX_FLASH_256K` 决定 `EQ_HW_UPDATE_COEFF_ONLY_EN` / `EQ_HW_LR_ALONE`（非 256K 才开） | `apps/soundbox/log_config/lib_media_config.c:43-46` |
| EQ 内核/多声道 | `EQ_CORE_V1` / `EQ_LITE_CODE` 决定多声道与异步能力 | 同文件 `:50-64` |
| 涂鸦 port 命名 | 涂鸦适配层文件名是 `tuya_ble_port_AD697x.c`（**AC697X** 命名） | `apps/.../tuya/` |
| 省晶振方案 | 省晶振**不支持蓝牙与内置 FM** | 发布说明 1.0.0 累积清单 |
| 芯片修订版相关 | 3.0.3/3.0.4 提到"D 版芯片兼容 / D 版芯片抗干扰优化"，3.0.5 "芯片兼容性 + 不开机补丁" | 发布版本信息 p3-p9 |

**手册未给型号差异对照表**（封装/引脚数/存储配置/外设差异都没有成表）；
"某音效只在特定型号可用"的清单也**未见说明**。要做型号选型必须另找芯片 datasheet，不能靠这份 SDK 手册。

## 6. 蓝牙 DUT / 测试模式（型号相关且容易懵）

`CONFIG_BT_MODE != BT_NORMAL` 时 `app_config.h:87-148` 会批量 `#undef`：
关 TWS / SD / PC / PWMLED / ADKEY / IOKEY，`TCFG_BD_NUM=1`，开 BLE，TX buffer 加大到 6K。
→ **BQB/DUT 版本上"按键全失灵、放不了 U 盘"是设计行为**，不是 bug。

## 7. 数学库（BR23 内置，做 DSP 前先看这里）

`REAL_FFT_FUN / REAL_IFFT_FUN / COMPLEX_FFT_FUN / COMPLEX_IFFT_FUN(int *data, int blockbit, int *outdata, int same)`，
`same` = data 与 outdata 是否同地址（手册 p55-57）。
内置函数**只有 11 个**：sin / cos / arctan(y/x) / sqrt(x²+y²) / sinh / cosh / exp / arctanh(y/x) / sqrt(x²−y²) /
ln(x·2^y) / sqrt(x)。定点 `MathFunc_fix.h`、浮点 `MathFunc_float.h`，入口 `math.h`。
**约束：`exp` 输入限 [-10, 4.852]；sin/cos 输入不含 π；arctan 输出已乘 π。**
