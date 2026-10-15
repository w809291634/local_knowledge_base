# 配置三层开关体系与宏互斥（杰理 SDK 通用）

> 杰理 SDK 的功能不是"改代码打开"，而是**三层宏逐层收敛**。看不懂这三层，就会出现在 A 处改了、被 B 处覆盖、
> 最后在 C 处才生效的迷案。

## 1. 三层是什么

| 层 | 文件 | 作用 | 能不能随手改 |
|---|---|---|---|
| 层 1 板级选择 | `apps/soundbox/board/br23/board_config.h` | 只留一个 `CONFIG_BOARD_*` 生效（本工程 `:8` 为 `CONFIG_BOARD_AC695X_DEMO`），随后**无条件 include 全部板级 cfg**（`:53-74`） | 换板只改这一行 |
| 层 2 功能开关 | 各板级 `board_xxx_cfg.h`（demo 板 1059 行、344 个 `TCFG_*`）+ `board_xxx.c` | 定义硬件细节（引脚、外设有无、按键表、音频参数）；每个 cfg 内部再用 `#ifdef CONFIG_BOARD_X` 把自己隔离开（如 `key_table/adkey_table.c:7`） | 这里是主战场 |
| 层 3 app 方向 | `apps/soundbox/include/app_config.h`（406 行） | 定 app 层默认值，文件里明确写着"**禁止直接改、要在板级重定义**"（`:23-30`） | 一般别动，动之前先确认板级有无重定义 |

宏值最终落去三处：`task_table.c` 的任务裁剪与栈、板级 `.c` 里的 `xxx_platform_data` 结构、代码里的 `#if` 分支。

## 2. 层与层之间的"联动覆盖"—— 最容易背刺的地方

`app_config.h` 里存在**条件性批量改写**，不是简单默认值：

- **测试模式/DUT**：`CONFIG_BT_MODE != BT_NORMAL` 时批量 `#undef`（`:87-148`）——关 TWS/SD/PC/PWMLED/ADKEY/IOKEY、
  `TCFG_BD_NUM=1`、开 BLE、TX buffer 加大到 6K。所以"DUT 版本上按键不灵"不是 bug。
- **IR 键禁低功耗**（`:359`）、**串口升级与 chargestore 抢 UART1**（`:388`）。
- 板级 cfg 里也有强制联动，例如开了混响会**强制关 AEC、关动态 EQ、关多带 DRC、强制开 EQ/DRC、
  把 `EQ_SECTION_MAX` 从 20 改成 25**（demo cfg `:600-625`）。

**排查口诀**：某个 `TCFG_x` 改成 1 却没效果 → 在 `app_config.h` 和板级 cfg 里 grep 这个宏名，看有没有被 `#undef`/`#define` 二次改写。

## 3. 官方明确的互斥组合（会以 `#error` 或运行时异常出现）

手册 §1.6（p12）列出的组合，实测在 `board_ac695x_demo_cfg.h` 尾部（`:982-1045`）以 `#error` 落地：

- EQ 在线调节 **不可与** usb mic + sd/mic 口 同开。
- flash 的 spi 口 = lcd 的 spi 口 → 必须关一个。
- `TRANS_DATA` / `DUERO_DNA` / `ANCS_CLIENT` **三选一**。
- 对箱（TWS）不支持音频转发；`TWS + 混响` 时混响只能 ECHO / MEGAPHONE（`:1045`），且不支持 M4A（`:1001`）。
- 无损格式（APE/FLAC/DTS）+ 混响：该 `#error` **已被注释掉**，只留判断（`:986-988`）→ 属于"官方不再拦但未必跑得动"。
- 闪避（dodge）必须开自定义音量调节（`:990`）。
- 等响度必须 数字音量 + EQ 总使能 + 关闭其他模式 EQ（`:1014-1021`）。
- 动态 EQ 必须 DRC + 多带 DRC（`:1025-1031`）。
- 2.1/2.2 声道 需要 `TCFG_EQ_DIVIDE_ENABLE`，且不支持 linein 独立 eq/drc（`:1033-1039`）；独立 EQ 需四声道 DAC 模式（`:1040`）。
- norflash 方案必须关 UI。
- TWS 暂不支持录音。
- FM 开混响时不支持混合录音（`:1009`）。

手册末尾红字：**所有宏定义不要写在编译警告（`#warning`）之后** —— 位置本身有约束。

## 4. 板级自带的性能警告

`board_config.h:23-36` 对 `AC695X_AUDIO_EFFECTS`（K歌宝）与 `AC695X_MEGAPHONE`（大声公）两块板明确写：
板级已按现有芯片资源优化配置好音效组合，**如果修改某些配置导致数据流卡顿，即表示不支持（触及芯片性能极限）**。
→ 这两块板上的音效改动没有"能不能优化"的余地，卡顿即结论。

## 5. 运行时配置 vs 编译期配置的分界

`USE_CONFIG_BIN_FILE` 与一组 `USE_CONFIG_*_SETTING`（`app_config.h` / 手册 p10 §1.4）决定某一类参数
是**从量产配置文件读**还是**编译期写死**：

- 例：`USE_CONFIG_STATUS_SETTING`（灯状态与提示音）、`USE_CONFIG_AUDIO_SETTING`、`USE_CONFIG_MIC_TYPE_SETTING`、
  `USE_CONFIG_AUTO_OFF_SETTING`、`USE_CONFIG_COMBINE_VOL_SETTING`。
- 板级 `.c` 里会有一份 `STATUS_CONFIG status_config = {...}` 兜底表（`.tone = {charge_start/charge_full/power_on/
  power_off/lowpower/max_vol/phone_in/phone_out/phone_activ/bt_init_ok/bt_connect_ok/bt_disconnect/
  tws_connect_ok/tws_disconnect = INDEX_TONE_*}`），配置文件不存在时才用它。
- **分工**：配置工具改的是**数据**（蓝牙名/MAC/功率/自动关机/TWS 配对码/晶振微调/MIC/音量/提示音/EQ）；
  宏决定的是**这项走哪条路 + 模块本身有没有编译进来**。两者都对了才生效。
  详见 `online-config-tool-mass-production.md` 与 `config-storage-vm-sdfile-syscfg.md`。
