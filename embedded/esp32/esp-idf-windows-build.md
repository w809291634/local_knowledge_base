# 本机 ESP-IDF 命令行构建通路（Windows；IDF v5.5.5 + Git Bash 冲突）

适用范围：**这台机器上的所有 ESP-IDF 工程**（非某个工程专属）。从
`esp32-p4-lvgl9-touch-lcd-debug-optimization.md` §21 拆出（2026-10-11），那份文档以后只留指针。
项目侧的作业卡（子命令名差异、分区/产物、调试开关）见
`../EEZ Studio_ui_debug_kit/reference/09_build_flash_debug_lvgl_demo_ai.md`。

## 1. 唯一入口 = IDF 根那对脚本

```
D:\esp32_8266_files\esp-idf-v5.5.5_ol> idf_cmd_init.bat && idf_build.bat <cmd>
```

- `idf_cmd_init.bat`：`:11-13` 写死 `IDF_PATH` / `IDF_TOOLS_PATH` / `IDF_PYTHON`，`:73` 调 `export.bat` 补全 PATH
  （`tools\idf-exe\1.0.3` 提供 `idf.py`）。**全文不读 `%1`** ⇒ 带不带参数结果一样
  （"别带参数，否则 `%1` 会盖掉 `IDF_TOOLS_PATH`"讲的是上游靠 idf-env 查表的那版，对本机不成立）。
- `idf_build.bat`：**切工程 = 改第 5 行 `set PROJECT_PATH=`**。脚本头注释里的"或作为参数传入"没有实现
  —— `flash/monitor` 的 `%~2` 是**串口号**，整张表里只有 `set-target` 吃 `%~2`。
  默认 `COM20`、烧写 2000000、监视 115200；命令集 build / reconfigure / flash / app_flash / monitor /
  flash_monitor / app_flash_monitor / menuconfig / clean / fullclean / size / size-components / size-files /
  partition-table / set-target。
- 工具链目录：`D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5`（`python_env/idf5.5_py3.11_env`、
  `tools/cmake/3.30.2/bin`、`tools/ninja/1.12.1`、`tools/riscv32-esp-elf/esp-14.2.0_20260121/.../bin`、
  `tools/idf-exe/1.0.3`、`tools/ccache/4.12.1/...`、`tools/esp-rom-elfs/20241011`）。
  `D:\Espressif` 在本机不存在（`esp_idf.json`/`idf-env.json` 里还写着它），但那对脚本不查 idf-env，**不影响**。
- VS Code 走 `.vscode/tasks.json` 也通：它在 **IDF 根**，18 个 task 都是 `cwd=${workspaceFolder}` + 裸写 bat 名。
  能成立的前提是默认终端 = cmd（IDF 根 `.vscode/settings.json:117` = `Command Prompt`，只有 cmd 搜索当前目录）；
  换成 PowerShell / Git Bash 就会 "not recognized"。
- **不要在工程目录里复制一套 bat**（2026-10-10 明确要求；我在 `examples/mipi_dsi/` 下建的那两个已删）。

## 2. 判成败：只能看日志标记

该 bat 每个函数都以 `exit /b 0` 结尾 ⇒ **退出码恒 0**，`$?` / `%errorlevel%` 与 `LASTEXITCODE` 都不可信，
**VS Code 的 build 任务因此会假绿**（`"group":"build"` 的后续 flash 也照跑）。判据用日志标记：

| 阶段 | 必须有 | 失败样本 |
| --- | --- | --- |
| build | `Project build complete` | `error:`、`ninja: build stopped`、`CMake Error` |
| flash | `Hash of data verified`（每段一次）+ `Hard resetting` | `Could not open COM20, the port is busy` |
| 采集前 | 目标 `.bin` 的 mtime 比源文件新 | 只烧进上一版固件 ⇒ 整轮结论作废 |

同类陷阱两条：`idf.py build flash 2>&1 | tail -3` 里管道把失败吞成 0；
自己写的 bat 里 `(...) & exit /b %errorlevel%` 的 `%errorlevel%` 在括号块解析时就提前展开 ⇒ 恒 0
（正解 `setlocal EnableDelayedExpansion` + `endlocal & exit /b !errorlevel!`）。

## 3. 从 Git Bash（MSYS）进去时多一步：清 MSYSTEM

`idf.py`/`idf_tools.py` 见到 `MSYSTEM` 就拒跑（`ERROR: MSys/Mingw is not supported`；判据是
`idf_tools.py:3613` 的 `if 'MSYSTEM' in os.environ`，**与用的是哪个 shell 无关**，cmd/PowerShell 里清掉照样能跑）。
`export.bat:2-4` 的守卫是**先 `echo This .bat file is for Windows CMD.EXE shell only.` 再 `goto :eof`**（不是静默）。

```
cmd.exe //c "set MSYSTEM=&& call D:\esp32_8266_files\esp-idf-v5.5.5_ol\idf_cmd_init.bat && call D:\esp32_8266_files\esp-idf-v5.5.5_ol\idf_build.bat build"
```

四条实测细节：
1. `cmd.exe /c` 的 `/c` 会被 MSYS 当路径转换吃掉 ⇒ cmd 进交互模式、bat 一条没跑、而 `$?` 仍是 0（症状：日志只有 189 字节 banner）⇒ 写 `//c`。
2. `set MSYSTEM=` 与 `&&` 之间**不能有空格**：带空格实测 `if defined MSYSTEM` 仍为真（空格成了值）；`set MSYSTEM=&&` 才删掉。
   （bat **文件里**逐行 `set MSYSTEM=` 行尾无空格，本来就成立。）
3. bash 侧 `MSYSTEM= cmd.exe ...` **不够**（传过去的是"存在且为空"，Python 判 `'MSYSTEM' in os.environ` 仍为真）。
4. `env -u MSYSTEM cmd.exe ...` 在本机是坏的（cmd 起来但零输出），别用。
5. 自建环境（不走 `export.bat`）才需要补 `ESP_ROM_ELF_DIR`，否则末尾报 `Error while generating esp_rom gdbinit` → ninja exit 1。

## 4. 配置：`sdkconfig` 与 `sdkconfig.defaults`

- **`sdkconfig.defaults` 只在 `sdkconfig` 不存在时生效** ⇒ 往它追加行而 `sdkconfig` 已存在 = **静默无效**（构建照样"成功"，配置没变）。要生效必须直接改 `sdkconfig`，或删掉 `sdkconfig` 让它重建 ⇒ **两个文件一起改**。
- 判"生效没有"只有一个合法判据：回读 `build/config/sdkconfig.h`（grep `sdkconfig*` 只能证明"文件里写了什么"）。
- kconfig 会**静默丢弃**越界或不满足依赖的符号（`CONFIG_LV_DRAW_THREAD_PRIO` 是 `range 0 4`；`CONFIG_LV_USE_PPA` 缺对齐依赖时整个消失）。
- `**/sdkconfig` 在 `.gitignore` 里 ⇒ 它不进版本库、一次 reconfigure 行号整体位移 ⇒ **文档里引配置只引符号名**，行号只配"当次回读"。
- `sdkconfig` 是 CRLF；工具脚本按行匹配时注意。

## 5. 串口取数（帧率/日志自证）

`idf.py monitor` 是交互式的，脚本侧要读数用 venv python + pyserial（打开口后 RTS 脉冲复位进运行态，按行解析）。
本机现成工具（都在 `C:\Users\Administrator\.qoder-cn\tmp\`，不属于任何工程）：

| 工具 | 用法 | 作用 |
| --- | --- | --- |
| `run_round.sh <工程目录> <标签> <秒>` | 一轮=一条命令 | 先校验 `idf_build.bat` 的 `PROJECT_PATH` 是不是这个工程（不一致就**拒绝**，防烧错工程）→ 走第 1 节那对根脚本 build+flash → 校验三个日志标记 + 新 `.bin` → 回读 `build/config/sdkconfig.h` 打印生效配置 → 才采集 |
| `cap_serial.py <秒> <日志文件>` | 单独采串口 | pyserial + RTS 复位，输出 min/max/mean/p10 与达标帧占比 |
| `idf.ps1` | PowerShell 直调 idf.py | 绕过 bat 拿**真退出码**时用 |
| `kill_stray_capture.ps1` | 列/清采集进程 | 只清我自己留的进程 |

COM20 长期被用户自己的 `idf.py monitor` 占着（`could not open port 'COM20': PermissionError(13)`）⇒ **先问再动**，不要擅自 Stop-Process 他的进程。

## 变更记录

- 2026-10-11：从 esp32 子库 §21 拆出成独立文件；顺手修掉三处旧错——"官方 `idf_cmd_init.bat` 在本机是断的"
  （**错**，它不查 idf-env）、`export.bat` "静默拒绝"（**打印后才退出**）、"`idf_cmd_init.bat` 别带参数否则盖掉
  `IDF_TOOLS_PATH`"（本机全文不读 `%1`）。"证明两核在并行渲染"的测法不属于构建，挪到 esp32 子库 §23。
