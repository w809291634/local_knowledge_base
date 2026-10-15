# 配置存储：VM / syscfg / SDFILE / 量产配置 bin（杰理 SDK 通用）

## 1. 三者分工

| 机制 | 是什么 | 用途 | 关键接口 |
|---|---|---|---|
| **VM** | flash 模拟 EEPROM 区 | 掉电保存的用户参数（音量、频道、配对信息、闹钟…） | `vm_init` / `vm_check_all` / `vm_defrag`（`include_lib/system/device/vm.h:62,107,117`） |
| **syscfg** | VM 之上的统一 ID 读写层 | 按 `item_id` 读写一块数据 | `syscfg_read/write/dma_write`（`include_lib/system/syscfg_id.h:37,40-55`） |
| **SDFILE** | 内置 flash 上的文件系统 | 存提示音、字库、EQ bin、资源 | 挂载 `mnt/sdfile`，分区 `/app/` + `/res/`（`app_config.h:68-80`，`USE_SDFILE_NEW`） |
| **量产配置 bin** | 配置工具生成的 `cfg_tool.bin` | 蓝牙名/MAC/音量/提示音/开关等**产品级默认值** | `cfg_file_parse()`（`include_lib/system/user_cfg.h:105`）在 `board_init` 早期读入 |

实测样本（工程里的 `log.md`）：`[SDFILE]VM size: 0x20000 @ 0x5e000`、`disk capacity 2048 KB`、`sdfile mount succ`，
随后一串 `[USER_CFG]read new cfg bt name config:jl_soundbox_lihui`、`aec_cfg mic_gain:3 dac_gain:22` ——
这就是量产配置 bin 在起作用。

## 2. syscfg 的 ID 分区与硬约束

- ID 分区（`syscfg_id.h:60-68`）：**1~49 用户区**、100~127（VM + bin + BTIF）、**512~700 只读硬件参数区**（如 `CFG_IOKEY_ID=522`）。
  app 侧自己的 ID 在 `apps/soundbox/include/user_cfg_id.h`（例：`VM_FM_EMITTTER_FREQ=1`、`VM_USB_MIC_GAIN=5`、
  `VM_ALARM_0..4=6..10`、`CFG_RCSP_ADV_HIGH_LOW_VOL=19`、`..._EQ_MODE_SETTING=20`、`..._EQ_DATA_SETTING=21`、
  `..._MIC=25`、`..._LED=26`、`..._KEY=27`、`CFG_MISC_DRC_SETTING=28`、`..._REVERB_ON_OFF=29`、
  `VM_ALARM_RING_NAME_0..2=30..32`）。
- **`buf` 必须 4 字节对齐**；**禁止在中断上下文写**（`syscfg_id.h:40-55`）。
- 手册给的接口形态：`int syscfg_read(u16 item_id, void *buf, u16 len)`，`item_id` 用户可用范围 **1~60**（p13 §2.2）。
- **`syscfg_read/write` 不能早于相关模块初始化**——在 `board_init` 之前的 initcall 里调用会拿到空值。
  自定义模块想掉电保存，安全做法是在自己的业务线程里读写（本工程 RF 学习地址存在 id=2，
  于 `rf_decode` 线程内 `syscfg_read/write(CFG_USER_RF_ADDR)`）。

## 3. VM 的"整理"会制造卡顿

VM 用量到 **80% 会触发 defrag（整理）**，整理期间有明显耗时/卡顿（`vm.h:84,104` 注释）。
所以 `app_task_loop` 的空转处每轮都调 `vm_check_all(0)` —— **把整理放在系统空闲时做**。
反过来说：**模式任务里长阻塞 = VM 整理和按键清理一起被卡住**。

现象对照：偶发"操作变慢一下又恢复"→ 先怀疑 VM 整理，再查 GC 式写放大（高频写 VM 项是根因）。

## 4. 新增一个"掉电保存项"的标准做法

1. 在 `apps/soundbox/include/user_cfg_id.h` 挑一个用户区 id（1~49），命名 `CFG_XXX`；
2. 定义结构体，**注意 4 字节对齐**；
3. 读写放在业务线程/任务里，不在 ISR、不在早期 initcall；
4. 需要考虑"首次开机没有该项"的默认值分支（`syscfg_read` 返回长度不足即为未写过）；
5. 若希望被**配置工具**改，还要走 `cfg_tool.bin` 那条路（见 `online-config-tool-mass-production.md`），两者不要重复存。

## 5. SDFILE / fat_nor / nor 存储

- 内置 flash 走 SDFILE（`mnt/sdfile`，`/app/` 与 `/res/`）；外挂 norflash 走 `apps/common/fat_nor`、`rec_nor`。
- 资源文件（提示音 `tone.cfg`、`eq_cfg_hw.bin`）都是 `-res` 参数打进 flash 的资源区，
  通过 SDFILE 以文件 ID 访问（EQ 文件 ID 0x3，见 `apps/soundbox/include/app_sound_box_tool.h:45-46`）。
- 版本说明 1.0.0 的累积清单里提到"外挂 flash 的 fat 分区 / 提示音分区 / 录音分区"是那时加的（发布说明 33–50 号条目）。

## 6. 设备管理与热插拔（与存储强相关）

- 静态设备表：`apps/common/dev_manager/dev_reg.c:16-163`，每项 `{logo, name, storage_path, root_path, fs_type}`，
  **带 `_rec` 后缀的项是录音分区**。
- `dev_manager_init()` 建 `"dev_mg"` 任务并挂静态设备（sdfile / rec_nor / fat_nor 等）
  （`dev_manager.c:1081`、`:1005-1045`）。
- 热插拔：驱动发 `DEVICE_EVENT_IN/OUT` → `dev_status_event_filter()`（`apps/common/dev_status.c:132-208`）
  → `mount()`（:74）/ `unmount()`（:102）进链表 → `music_task_dev_online_start()`（:185）通知 music 模式。
  **valid 位的含义是"有没有可播文件"，不是"有没有插卡"**（`:33`）——所以格式化后插 U 盘不切模式是正常行为。
- `music_task_dev_online_start` 也是"自动切到音乐模式"的入口，改这块要注意模式切换是异步且有退出检查。
