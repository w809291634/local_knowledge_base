# SDK 分层、编译与烧录（杰理 soundbox SDK 通用）

> 适用：杰理 BR23 系 soundbox SDK（3.1.0 实测），其他内核结构相同、路径中的 `br23` 换成对应内核名。
> 路径均相对 SDK 工程根。

## 1. 分层与"开源/闭源"边界 —— 决定你能怎么学这套 SDK

| 层 | 位置 | 可见性 |
|---|---|---|
| 业务/模式 | `apps/soundbox/` | 源码可见，最常改 |
| 公共功能 | `apps/common/`（audio/key/ui/config/dev_manager/fat_nor/debug/update/usb…） | 源码可见 |
| 板级配置 | `apps/soundbox/board/br23/board_*` | 源码可见（宏 + platform_data） |
| CPU/外设驱动 | `cpu/br23/` | 源码可见（UART/SPI/IIC/PWM/ADC/定时器/UI 驱动） |
| **闭源库** | `include_lib/liba/br23/*.a`（**82 个 `.a`**） + 只有头文件的 `include_lib/{system,driver,media,btstack,btctrler,update}` | **只有头文件** |

**结论**：OS、蓝牙协议栈、音频算法、部分驱动实现都在 `.a` 里。学习方式是**改配置宏 + 填注册表 + 看串口 log**，
读源码这条路在库层走不通。别把时间花在"找 btstack 的 c 文件"上。

## 2. 工程与构建

- 两套工程入口：CodeBlocks 的 `AC695N_soundbox.cbp`，以及**以 Makefile 为准**（`Makefile`）。
- 工具链：pi32v2 版 clang。Windows 在 `C:/JL/pi32/bin`（`clang.exe` / `pi32v2-lto-wrapper.exe` / `pi32v2-lto-ar.exe`），
  系统库 `C:/JL/pi32/pi32v2-lib/r3`；Linux 在 `/opt/jieli/pi32v2/bin`。
  **工具链版本随 SDK 版本走**（3.1.0 = 2.4.6），换 SDK 版本要一起换工具链。
- 关键编译参数：`-target pi32v2 -mcpu=r3 -integrated-as -flto -Oz -g -fno-common -fallow-pointer-null
  -fprefer-gnu-section -fms-extensions -Wundef`（`Makefile:59-74`）。`-flto` 意味着**跨文件内联 + LTO**，
  改一个头文件可能引发大面积重编与符号变化。
- 命令：`make all`（编译并下载）、`make VERBOSE=1`、`make clean`。
- **Linux 两个前置**（`Makefile` 头部注释）：① 从 `http://pkgman.jieliapp.com/doc/all` 取包解压到 `/opt/jieli`，
  保证 `/opt/jieli/common/bin/clang` 存在；② `ulimit -n 8096`，否则**链接因打开文件数不足而失败**。
  Linux 还要 `-D__SHELL__`（否则 download 脚本处理不对）。
- Windows 下用 VSCode：默认构建任务跑 `.vscode/winmk.bat all`，它把 `SDK/tools/utils` 加进 PATH 再
  `make -j %NUMBER_OF_PROCESSORS%`；`tools/make_prompt.bat` 开一个能手敲 make 的 cmd。
  **不要在裸 cmd 里直接 `make`** —— 找不到 `make.exe`/`mkdir_win` 等（都在 `tools/utils`）。

## 3. 新增一个 `.c` 文件要做的事（最容易踩）

1. 加进 `Makefile` 的 `c_SRC_FILES`（本工程用户文件集中在 `Makefile:721-727`）。**没加进去的文件不会报错，只是不参与编译。**
2. 新建目录的话，`INCLUDES` 加 `-I`（已有 `apps/user_apps/`、`apps/user_apps/hardware` 在 `Makefile:210-211`）。
3. IntelliSense 侧要手工同步 `.vscode/c_cpp_properties.json` 的 `includePath` 与 `defines`
   （`defines` 必须与 Makefile 的 `DEFINES` 一致，两处会漂移 → 红色波浪线但能编译）。
4. 起任务的还要在 `apps/soundbox/common/task_table.c` 登记任务名/优先级/栈（见 `app-task-state-machine.md`）。
5. **`SYS_EVENT_HANDLER`、`module_initcall`、`__initcall` 靠段自动登记，不用改 Makefile** —— 这是这套 SDK 的主要挂载方式。
6. `make all` 的 `pre_build` 会重新预处理三处：`sdk_ld.c → sdk.ld`、`sdk_used_list.c → .used`、
   `tools/download.c → download.bat`（`Makefile:782-791`）。**手改 `sdk.ld` 或 `download.bat` 会被覆盖**，要改源头。

## 4. 产物与烧录链（`cpu/br23/tools/`）

`download.bat`（由 `download.c` 生成）做的事，按顺序：

1. `llvm-objcopy` 从 `sdk.elf` 切出 `.text` / `.data` / `.data_code` 和 **10 个 overlay 段**
   （aec/wav/ape/flac/m4a/amr/dts/fm/mp3/wma）。
2. `remove_tailing_zeros -mark ff` 处理 aec/fm/mp3/wma 段。
3. `copy /b ... + bank.bin app.bin` 合成 `app.bin`。
4. `copy effect_file\music_base.bin eq_cfg_hw.bin` —— **默认调音数据来自 `effect_file/music_base.bin`**。
5. 调 `download\standard\download.bat` 真正烧录：
   `isd_download.exe -tonorflash -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin
   -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all`
   （同目录有密钥 `193-AC690X-B718.key`，`-key` 参数默认注释掉。另有注释掉的 `-format vm` / `-format cfg`
   用于单独格式化 VM 区 / BT 配置区。）
6. `fw_add.exe -noenc -fw jl_isd.fw -add ota.bin -type 100` 生成 `jl_isd_all.fw` / `jl_isd_nor.fw` 并打入 `script.ver`；
   `ufw_maker.exe -fw_to_ufw` 得 **`update.ufw` / `nor_update.ufw`**（给终端/量产用的单文件）。

**长按复位配置**在 `cpu/br23/tools/isd_config.ini`：长按时间**只接受 00/04/08**，其他值按 04 处理；
同文件还有 `RESET_MODE`、`VDBG1_PORT`（端口+波特率编码）、`POWER_DELAY`、`UTTX/URTX`、`lrc_ws_inc` 等。

**注意**：`cpu/br23/tools/` 下的 `app.bin`/`sdk.elf`/`sdk.map`/`symbol_tbl.txt`（单文件约 10 万行）
以及 `objs/**/*.o` 若被 git 跟踪，一次提交会产生几万到十几万行 diff。入库前先确认 `.gitignore` 覆盖到它们。

## 5. 配套工具版本（3.1.0 手册记录，务必与 SDK 对齐）

烧写器 V2.26.1 · 一拖八 V3.1.7 · 测试盒 V12.6 · 配置工具 V2.0.2 · **工具链 2.4.6** · effectTool 0.1.8 · FW 编辑 2.0.47。
终端侧统一入口是 `客户终端使用工具 入口/给终端的入口文件.jlxproj`（本质是 Lua 脚本，见
`online-config-tool-mass-production.md`）。
