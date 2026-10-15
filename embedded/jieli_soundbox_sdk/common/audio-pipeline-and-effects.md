# 音频链路、音效模块与在线调音（杰理 SDK 通用）

## 1. 三条链的数据流

### 解码链（播放）
```
各通路解码器  cpu/br23/audio_dec/audio_dec_{bt,file,fm,linein,pc,spdif,record,tone}.c
   ↓ 每路 open 时挂 music_eq_open()      bt:553  file:578  fm:406  linein:366  pc:601  spdif:535
mixer（多路 PCM 叠加）                    audio_dec.c:78
   ↓ 可在 mixer 和 last 之间插数据流       audio_dec.c:807-870（注释原文即如此）
数字反相 / 等响度 / 声道切换 / 频谱 / 人声消除 / automute
   ↓
default_dac
```
- 解码任务由 `audio_dec_init()` 创建（`audio_dec.c:665-672`）；可开独立输出任务 `TCFG_AUDIO_DEC_OUT_TASK`。
- 混合录音另有 `recorder_mixer`（`:104-106`）。
- `mix_buff` 长度 `AUDIO_MIXER_LEN = 128*2*2`（声卡 cyclic 模式 ×6）—— `cpu/br23/audio_config.h:8-11`。

### src / sync 的角色（变采样与时钟对齐）
- `stream_src.c:143 stream_src_open(target_sr)`：变采样；**采样率相同会自动关掉硬件 SRC**（`:50-56`）。
- `stream_sync.c:138 stream_sync_open()`：`audio_buf_sync_open` + SRC，按缓冲水位（`begin/top/bottom_per`、`inc/dec_step`）
  做**时钟同步**（蓝牙/线路输入与本地 DAC 时钟不同源时才需要）。
- `stream_entry.c:33`：链路末端的回调出口节点。SRC 实例上限 **5（开混合录音）/ 3**（`audio_dec.c:68-70`）。

### 编码链（录音/通话）
`audio_enc.c`：mic ADC → 软件重采样（`:201`）→ `audio_aec_inbuf`（`:53`）；
`audio_enc_recoder.c:804-820` 按 WAV/PCM、G726、MP3 分支；落盘由独立任务做
（`apps/common/audio/encode/encode_write_file.c`：`enc_write_file_task:103` / `enc_write_file_open:277`）。
SBC / mic 采集在 `audio_sbc_codec.c`、`audio_mic_codec.c`；混合录音 `audio_recorder_mix.c`。

### 音效链（混响/K歌，mic 通路）
`cpu/br23/audio_mic/mic_effect.c:961-1031` 显式串流：
```
mic 入口 → 能量检测 → noisegate → mic_eq0/drc0 → 移频啸叫 → 陷波啸叫 → 变声
        → reverb/echo → mic_eq4/drc4 → gain → channel_zoom → DAC
        （另分流 usbmic / 录音）
```
配套：`mic_stream.c`、`simpleAGC.c`、`effect_linein.c`、`loud_speaker.c`。
数字音量：`apps/common/audio/audio_digital_vol.c`（open:83、run:541、自定义音量表:673）。

## 2. 支持的格式（三处口径不同，别混）

| 层 | 位置 | 内容 |
|---|---|---|
| app 播放解码表 | `apps/common/audio/decode/decode.c:28-47` | `wtg/msbc/sbc/mty/aac/mp3/wma/wav` + 条件加 `midi/mid/wts`。**这张表里没有 flac/ape 字符串** |
| 底层枚举 | `include_lib/media/media_develop/media/audio_base.h:6-35` | 含 `FLAC/APE/M4A/AMR/DTS/APTX/LDAC/OPUS/SPEEX/ALAC/G726` |
| 各路所需主频 | `audio_dec_file.c:68-85` | 覆盖 APE/FLAC/DTS/M4A/ALAC/MIDI |

→ **要播 flac/ape 必须同时在 app 表里加解码器 + 打开对应 `TCFG_DEC_*_ENABLE`**（demo 板 `cfg:758-774` 全 DISABLE），
只改底层枚举没用。LDAC/aptX 只有枚举，BR23 侧实现与开关**未见说明**。
蓝牙侧 AAC 由 `TCFG_BT_SUPPORT_AAC`（`cfg:765`，demo=0）控制，分支见 `audio_dec_bt.c:349/953/1036`。

采样率/位宽硬约束：混响通路固定 44100（`cfg:632-634` `TCFG_REVERB_SAMPLERATE_DEFUAL`/`MIC_EFFECT_SAMPLERATE`）；
AEC 只支持 8000/16000（`apps/soundbox/include/aec_user.h:57,68`）；动态 EQ 需 32bit 输入（`cfg:521`）；
EQ 多声道（3~8）需 `EQ_CORE_V1`（`apps/soundbox/log_config/lib_media_config.c:49-52`）。
音量档：模拟 28（差分 21）/ 联合 22 / 数字 100 / 数字组 30（`cpu/br23/audio_config.h:76-84`）。

## 3. 音效模块与开关（全部在板级 cfg）

| 模块 | 开关 | 位置 | 备注 |
|---|---|---|---|
| EQ | `TCFG_EQ_ENABLE` + 分模式（BT_MUSIC/PHONE/MUSIC_MODE/LINEIN/FM/SPDIF/PC/AUDIO_OUT/MIC_EFFECT_POST_EQ） | `cfg:508-518` | `EQ_SECTION_MAX 20`（`:520`），**开混响后被强制改 25**（`:601-602`）；默认 10 段 31Hz-16kHz 曲线在 `cpu/br23/audio_effect/eq_config.c:17-60`；四声道独立 `TCFG_EQ_DIVIDE_ENABLE` |
| DRC | `TCFG_DRC_ENABLE` + 分模式 | `:524-533` | 多带 DRC `TCFG_AUDIO_MDRC_ENABLE` 三态（`:522`） |
| 动态 EQ | `TCFG_DYNAMIC_EQ_ENABLE` | `:521` | 依赖 DRC + 多带 DRC |
| 混响/回声 | `TCFG_MIC_EFFECT_ENABLE`（`:586`）+ `TCFG_MIC_EFFECT_SEL`=REVERB/ECHO/REVERB_ECHO/MEGAPHONE（`:590-594`） | | 模块位枚举 `cpu/br23/audio_mic/mic_stream.h:6-23`（REVERB/ECHO/PITCH/NOISEGATE/DODGE/DVOL/HOWLING/HOWLING_TRAP/FILT/EQ/ENERGY_DETECT/SOFT_SRC/LINEIN/DIGIT_ENHANCE/声压）；默认选配 `audio_mic/effect_reg.c:5-18` |
| 啸叫抑制 | 移频 + 陷波 | `mic_effect.c:987-991` | |
| 降噪 | noisegate（`mic_effect.c:971`）；通话 ANS | `aec_user.h:14` | |
| 变声/魔音 | `TCFG_MIC_VOICE_CHANGER_ENABLE`（`:597`） | 11 种模式见 `audio_effect/audio_voice_changer_demo.c:40-113` | |
| 通话 AEC | `aec_user.h:12-23`：AEC/NLP/ANS/AGC/TDE，三模式 | | SMS 增强版需更多 RAM/MIPS（`:25-34`） |
| 其他 | 虚拟低音、环绕声、2.1/2.2 声道、等响度、人声消除、闪避、电音、变速、魔音、啸叫抑制 | 手册能力表 p6-p9 | 互斥见 `config-three-layers-and-macro-mutex.md` §3 |

## 4. 在线调音（EQ 工具 / 混响工具）完整流程

1. **板级开宏**：EQ 用 `TCFG_EQ_ONLINE_ENABLE`；混响用 `TCFG_MIC_EFFECT_ONLINE_ENABLE`
   （它会自动强制 `TCFG_ONLINE_ENABLE=1`）。本 SDK 实际对应 `TCFG_EFFECT_TOOL_ENABLE` / `TCFG_ONLINE_ENABLE`（`cfg:544,555`）。
2. **连接**：**串口，默认 USB 虚拟口 DP/DM，115200**；普通 uart 调试时**不要勾"蓝牙串口"**。
   口可改 `TCFG_TOOL_TX_PORT` / `TCFG_TOOL_RX_PORT`（`cfg:552-553`）。混响工具首连弹密码框，默认 **`000`**。
3. **选模式**：EQ 5 种（通话宽带/窄带上下行 + 普通音频），四声道独立时 8 种（FL/FR/RL/RR）；
   混响 5 种（纯回声、男变女、女变男、娃娃音、魔音）。
4. **导出参数文件**：EQ → `eq_cfg_hw.bin`；混响 → `effects_cfg.bin`。放进 `cpu/br23/tools/`，
   在 `download.bat` 的 `-res` / `-resone.cfg` 后追加。
   **当前 SDK 的 `tools/download.bat:65` 实际是 `copy .\effect_file\music_base.bin eq_cfg_hw.bin`** ——
   即默认用 `effect_file/music_base.bin`，直接替换 `eq_cfg_hw.bin` 会被这一步覆盖。
5. **生效（关键，最常漏）**：必须**关掉在线调试宏** + **使能"使用 eq 文件"宏 `TCFG_USE_EQ_FILE`**，重新编译烧录。
   在线调试宏开着时，工具下发的值不会被固件当作最终配置。
6. **离线编辑**：工具"打开固件配置（离线编辑）"；`TCFG_EQ_DIVIDE_ENABLE=1` 时 EQ 工具版本选 **0.7.3.0**，
   其余 AC695N 选 **0.7.2.0**；段数不得大于 SDK 的 `EQ_SECTION_MAX`；通话上下行 EQ 默认最大 3 段。
7. **工具版本**：PC 端 EffectTool（入口"杰理SDK工具 1.0.15"里的 effectTool；3.1.0 配套 0.1.8）。
8. **协议帧**（工具与固件之间的调试协议）：`5A AA A5 + CRC16 + L + T + SQ + DATA`，
   `T=0x00` 回复 / `0x12` 主动；CMD `0x23` 查基本信息、`0x0B` 查文件大小、`0x0C` 读内容、`0x22` 准备写
   （`apps/soundbox/include/app_sound_box_tool.h:9-56`）。EQ bin 的文件 ID 是 0x3（`:45-46`）。

参数存放：`eq_cfg_hw.bin` = `SDFILE_RES_ROOT_PATH"eq_cfg_hw.bin"`；混响侧同名入口 `effects_adj.c:25`；
在线调试可把参数存进 VM（`EQ_ONLINE_FILE_SAVE`，`include_lib/media/eq_func_define.h:29`，
装配于 `lib_media_config.c:32-35`）。

## 5. 开混响时代码会强制改的东西（改不动就查这里）

`cfg:600-625`：关 AEC、关动态 EQ、关多带 DRC、强制开 EQ 与 DRC、`EQ_SECTION_MAX` → 25。
另有一批 `#error`（`:982-1045`）：对箱音源转发不得开混响/录音/DRC；TWS+混响不支持 M4A；
FM 开混响不支持混合录音；TWS 时混响仅 ECHO/MEGAPHONE；闪避需自定义数字音量；等响度需数字音量且关其他模式 EQ；
2.1/2.2 需 `TCFG_EQ_DIVIDE_ENABLE`；独立 EQ 需四声道 DAC 模式。

## 6. 性能与资源

- 两份音效 PDF 的"功能概述/模块调用关系/性能要求"章节**正文为空** → 具体 MIPS/RAM 指标**未见说明**。
- 可用来判断占用的线索：解码占用率跟踪 `TCFG_AUDIO_DECODER_OCCUPY_TRACE`（`audio_config.h:20`）；
  SRC 实例上限 3/5；EQ 分频器阶数越高 MIPS 越大。
- overlay 机制（AEC/WAV/APE/FLAC/M4A/AMR/DTS/FM 共用一块 RAM 段）意味着**同时启用的大算法受段容量限制**，
  见 `peripheral-drivers-cookbook.md` §9。
- 触及性能极限的表现 = 数据流卡顿，官方态度是"即表示不支持"（见 `config-three-layers-and-macro-mutex.md` §4）。
- 多路解码具体路数上限：**未见说明**。
