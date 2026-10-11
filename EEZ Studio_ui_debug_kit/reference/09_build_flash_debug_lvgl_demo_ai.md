# 本工程（lvgl_demo_ai / eez-test）编译 · 烧写 · 调试作业卡

> 2026-10-06 整理。用途：把 `PLAYBOOK.md` §1.1 那套 `{占位符}` 填成**这台机器上的真实值**，
> 并把"一条命令走到底"的顺序钉死。所有条目都是本项目实际用过的，不是抄官网。
> 相关：帧率与 PPA 见 `reference/08_lvgl_esp32p4_frame_rate.md`；通用方法论见 `PLAYBOOK.md`。

---

## 0. 路径与占位符对照

| 占位符 | 实际值 | 备注 |
|---|---|---|
| `{ROOT}` | `D:\esp32_8266_files\esp-idf-v5.5.5_ol\examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_ai\eez-test` | UI/native 工程根 |
| `{IDF_ROOT}` | `{ROOT}\..` = `...\lvgl_demo_ai` | ★ **build 目录在这里**，不在 eez-test |
| `{DESIGN_DIR}` | `{ROOT}\design` | DSL、工具、门禁、走路器全在这 |
| `{PY}` | `C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe` | ★ **只有它装了 PIL**；系统 python 跑门禁必 `ModuleNotFoundError: PIL` |
| 仿真器根 | `...\idf_v555_my_exps\common\PC_SIM\lv_port_pc_vscode_v9.5` | 目录内**零改动**，靠引用工程源码编译 |
| `{EXE}` | 仿真器根 `\bin\main.exe` | |
| LVGL 内核 | `...\common\APL\apl_lvgl_v9_4` | 读源码定 API 时来这里（`lv_obj_event.c` / `lv_indev.c` 等） |
| IDF | `D:\esp32_8266_files\esp-idf-v5.5.5_ol`，工具链 `esp-idf-tools_for_idf_v5_5_5`，py env `idf5.5_py3.11_env` | |
| 小智 | `{IDF_ROOT}\xiaozhi-esp32`（vendored，**不改**）；板级胶水 `{IDF_ROOT}\main\board_p4_audio.cc`（改这里） | |

---

## 1. 铁规矩：验收顺序不能颠倒

```
① UI/DSL 改动   → python design/all.py --sim          （pipeline + 出图 + 对照门禁）
② 交互/状态改动 → python design/sim.py --walk=<name>   （走路录像 + 断言日志）
③ 设备侧改动    → python design/_verify_weather.py     （官方逐文件真编译）
④               → cmd.exe //C "design\_idf_build.bat build"   （链接 + 尺寸）
⑤ 才给用户烧写清单（idf.py flash monitor）
```
每一层能证明什么、不能证明什么，**报告里要写清**：
- ①②证明的是**通路**，不是真值（PC 的音量/电量/进度都是假的）；
- ③④证明能编能链接，**不证明**运行时行为；
- 被 `#if defined(ESP_PLATFORM)` 关空的代码，仿真层**完全编不到**（例：`io_music_player.cpp`）
  ⇒ 这类改动只能靠"代码读证 + 真机日志"，别拿仿真绿当行为对。

---

## 2. UI 生成流水线（`src/ui/` 是只读产物）

```
design/build_ui.py（DSL） → design/ui.json → design/json2eez.py → test.eez-project
   → design/eez_build.py（EEZ CLI） → src/ui/**（生成代码）
```
- **排查一律回上游改 DSL**，手改 `src/ui` 会被下次生成覆盖。
- 自证没手改：`ls -la --time-style=+%H:%M:%S src/ui/*`（产物时间戳应同秒）。
- 字体：`gen_fonts.py` / `eez_font_engine.py`；缺字检查 `_glyph_lint.py`
  ⚠ 它只扫 DSL 里的**静态**文字，运行期灌进去的文本（曲名、歌词、聊天、AP 名）要自己保证字库覆盖
  ⇒ 13px 档有 GB2312 一二级全量（~6770 字），16px 档只有演示曲名。
- 门禁：`compare.py`，判据 = 平均明显差异 ≤ 25%（阈值在 `compare.py:140`）；
  本工程当前基线 **9.88% ~ 9.95%**。纯管道改动后数字不变 = 正确的证据，要这么写。
- 运行期文本要能在仿真里断言 ⇒ 给控件**显式 id**（自动名会随增删控件漂移）：
  例 `m_np_prog_time` / `m_np_title` / `m_np_lyr0..4`。

---

## 3. PC 仿真（`design/sim.py`）

| 用法 | 说明 |
|---|---|
| `--walk=<name>` | 跑走路脚本，出图 + 断言日志到 `build/sim_shots/walk_<name>/` |
| `--walk=list` | 列出可用走路脚本 |
| `--states` / `--gui` / `--ui-only` / `--no-build` | 钉态拼版 / 开窗口 / 只换 UI 重编 / 用现成 exe |

- 走路器命令（够覆盖本项目全部断言手法）：
  `tap <obj>` `tapxy <x> <y>` `mouse <x> <y>`（真 SDL 链路）`mousef`（真人手速）`tab <页> <序号>`
  `gettext`（含 vis）`getrot`（样式 rot/scale/opa + image 的 imgrot）`rect`（真实矩形自证）
  `state` `tree` `audit` `key` `scan` `disc` `ai <0..3|off>`（钉假 AI 态）`voice open_music|list|play <名>`
  `wait <ms>` `shot <名>`
- ⚠ `walk_capture()` 每次都会重写 `sim_cmake/main.c` ⇒ mtime 变 ⇒ **必重编**（几十秒），别按"改没改源码"猜。
- ⚠ 命中/坐标类断言必须让工具**自证**（tapxy 会打印命中对象名 + 真实矩形 + CLICKABLE）；
  打偏了不报的工具会把人带去追一整轮假 bug（2026-10-06 踩过，见 §11.27）。
- 钉态环境变量（`io_pc.cpp`）：`EEZ_SIM_STATE`（Wi-Fi 各态）、`EEZ_SIM_AI=0..3`、
  `EEZ_SIM_AI_VOLUME`、`EEZ_SIM_SD=nocard|nodir|empty|fail`、`EEZ_SIM_LRC=none`。
- ⚠ **OS 真实光标会顶掉 indev**：窗口在屏上时人的鼠标一动，走路里 `mouse` 的读数就会对不上，
  甚至冒出看着像"代码回声"的假命令（本项目真发生过，别急着改代码）。
- ⚠ 子进程输出必须 `encoding="utf-8"`（Windows 默认按 GBK 解 → 中文乱码 + print 时 UnicodeEncodeError）。

---

## 4. 真机编译 / 烧写 / 调试

### 4.1 用户侧权威入口（VS Code `tasks.json`，2026-10-06 用户逐字给出）
`workspaceFolder` = IDF 工程根 `...\p4_touch_lcd4_3_exp\lvgl_demo_ai`；
除 menuconfig 外每条都是 `idf_cmd_init.bat && idf_build.bat <子命令>`。

| task 标签 | 什么时候用 |
|---|---|
| `reconfigure` | ★ 新建/删除源文件、改 `CMakeLists.txt`、改分区表后**必须先跑** —— 否则新文件不进 `compile_commands.json`，逐文件真编译会"看不见它却报 ALL CLEAN"（假绿，P-0113） |
| `idf_build`（build） | 日常编译（含链接与体积检查） |
| `flash` | **全量烧**：bootloader + 分区表 + ota_data + app + `generated_assets.bin` |
| `app_flash` | ★ **只烧 app**，日常最快。但改了三样就不能只用它：① `partitions.csv`/分区相关 sdkconfig；② **字体烘焙产物**（走 assets 分区 `0x1020000`，见 §2 的字库话题）；③ bootloader 本身 |
| `monitor` | 看串口 |
| `flash_monitor` / `app_flash_monitor` | 烧完接着看 —— 交付给用户时推荐这个组合（少一次手动） |
| `menuconfig` | 交互改配置（`start cmd.exe /K call idf_cmd_init.bat && call idf_build.bat menuconfig`）。★ 改完的关键项要**同步进 `sdkconfig.defaults`**，否则 `fullclean` 后丢 |
| `size` / `size-components` / `size-files` | 量化体积。例：「给 16px 也补 GB2312 全量字库约 +700~900KB」这种判断，就得靠它出数，别拍脑袋 |
| `partition-table` | 分区改动后单独重算 |
| `fullclean` | `clean` 在 tasks 里是**注释掉的** ⇒ 要清只有 fullclean；★ 它连 `build/compile_commands.json` 一起带走，之后必须 `reconfigure` |
| `set-target esp32p4` / `esp32s3` | 切目标芯片（本工程 esp32p4；`esp32` 那条被注释） |

★ **表里的 `app_flash` / `flash_monitor` / `app_flash_monitor` 是用户 `idf_build.bat` 的参数名，不是 `idf.py` 的子命令。**
`idf.py --help` 实测只有连字符形式：`app-flash`、`bootloader-flash`、`partition-table-flash`，
而"烧完接着看"在 idf.py 侧是**两个子命令** `flash monitor`（没有 `flash_monitor` 这个名字）。
⇒ 抄任务名到别的入口前先对齐命名，别以为 `idf.py app_flash` 能过（argparse 不认下划线）。

### 4.2 AI 侧等价入口（这台机器实测能过）
```
cmd.exe //C "design\_idf_build.bat <t>"     t ∈ reconfigure|build|app-flash|flash|monitor|size|fullclean|...
```
★ 我们这份包装是 `idf.py %*` **直传**，所以只能用 idf.py 的真名：`app-flash`（连字符）、
`flash monitor`（两个词一次传：`..._idf_build.bat flash monitor`）。
★ 用户的 `idf_cmd_init.bat` / `idf_build.bat` **在 IDF 根** `D:\esp32_8266_files\esp-idf-v5.5.5_ol\`，
`tasks.json` 的 `cwd=${workspaceFolder}` 指的也是 IDF 根（2026-10-11 更正：从前记的"在 workspaceFolder 里、本侧搜不到"
是我在**工程目录**里搜 ⇒ 误判；**不要再往工程目录复制 bat**，切工程只改 `idf_build.bat:5` 的 `PROJECT_PATH`）。
构建通路唯一真源 = `esp32` 子库 `esp-idf-windows-build.md`（含"该 bat 每个函数都 `exit /b 0` ⇒ 退出码恒 0、判成败只看日志"这条）。
三个必须（缺一件就失败）：① `set MSYSTEM=`（Git Bash 起 cmd 时它有值，`export.bat:2-4` 见到会先打印
"This .bat file is for Windows CMD.EXE shell only." 再 `goto :eof`）；
② 显式 `IDF_TOOLS_PATH` / `IDF_PYTHON_ENV_PATH` / `IDF_PATH`；③ **`.bat` 内容必须 ASCII-only**
（UTF-8 中文注释在 GBK 代码页下会被解析成垃圾命令，报"'sks.json' 不是内部或外部命令"这类莫名错）。
★ 另：`idf_cmd_init.bat` 带参数会把 `IDF_TOOLS_PATH` 盖成参数值 —— **这是上游 idf-env 查表版的行为**；
本机那份 `:11-13` 已把路径写死、全文不读 `%1`，带不带参数结果一样（见 `esp32/esp-idf-windows-build.md` §1）。

### 4.3 产物与分区
`{IDF_ROOT}\build\lvgl_demo_v9.bin`（当前 `0x4efae0`；app 分区 `0x800000`，38% free）；
assets 在 `0x1020000` ⇒ **改字库要全量 flash，`app_flash` 烧不到它**。

### 4.4 三个必踩坑
1. 新建 `.cpp` 后**必须先 `reconfigure`**（见 4.1 第一行）。
2. `src/native/CMakeLists.txt` 的 `NATIVE_SRCS` 是**显式列表不是 GLOB** ⇒ 新文件要手加进去，
   否则真机链接期 `undefined reference`（P-0020 同款）。
3. 调试开关（perf monitor / heap poisoning / log level）要**同时写进 `sdkconfig.defaults`**，
   只改 `sdkconfig` 下次重配就丢；改完用 effective config 复核（build 后的 `build/config/sdkconfig.h`）。

---

## 5. 逐文件真编译（比整项目 build 快，且能单独验一个文件）

```
python design/_verify_weather.py          # 全部目标；TARGETS 里加你要验的文件
VW_NOEXTRA=1 python design/_verify_weather.py   # 反证：去掉补的 -I，应当报错（证明检查有效）
```
- 命令来源两级：该文件**自己的** `compile_commands` 条目（首选）→ 借兄弟文件的命令 + 手补 include。
- ★ 必须真 `-c -O2` 编译，**不能用 `-fsyntax-only`**（语法检查不跑树优化器 = 假绿，P-0052）。
- 借来的命令连 define 也是借的：重配后借 `io_esp.cpp` 编别人会报
  `esp_crt_bundle.h: 'mbedtls_x509_crt' does not name a type` —— 那是缺 `MBEDTLS_*` 宏，不是缺 `-I`。
- 反斜杠归一化必须跳过 `\"` 转义（`re.sub(r'\\(?!")', "/", cmd)`）。
- 命令一律写进 `.sh` 再 `bash file.sh`：**别用 `bash -c "<命令>"`**，二次转义会把源文件名吃掉
  （报 "no input files"）。

---

## 6. 崩溃与日志解码（真机）

- `addr2line`：`D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5\tools\riscv32-esp-elf\...\bin\riscv32-esp-elf-addr2line`
  ★ **先核 ELF sha256 前缀**（boot log 里那句 `ELF file SHA256: xxxxxxxxx`）与 `build/*.elf` 一致，
  再信任何地址解析结果 —— 烧错版本时地址解出来是"看着很像"的错函数。
- 栈溢出三数字法：`Stack bounds` 相减 = 实际栈大小 → 和 `xTaskCreate` 的数比 → 和函数里最大的那个
  局部对象比（本项目 6136 vs 6152 那次就是这么定的，§11.25）。
- `Store access fault` 且 `A0/MTVAL` 是个小常数 ⇒ 怀疑 `NULL + 结构体字段偏移`：
  去查该偏移等不等于某个 header 的 `sizeof`（本项目 `0xc == sizeof(esp_payload_header)` ⇒ `copy_buff==NULL`）。
- release 下 `assert()` 被编掉 ⇒ 驱动里 `assert(p); *p = ...` 等于把 panic 留给你。
- 帧率/CPU：`CONFIG_LV_USE_PERF_MONITOR=y` 时屏上右下角就是读数（正式版本记得关）。
- 归因纪律：**先画"通道对照表"**（谁通谁不通）再改码，别拿"改配置试探"当排查（§2.8）。

---

## 7. 环境雷区速查（每一条都真踩过）

| 现象 | 真因 | 规矩 |
|---|---|---|
| `ModuleNotFoundError: PIL` | 用了系统 python | 一律用 `{PY}`（.workbuddy 那个） |
| 中文参数变乱码 | Git Bash 传参编码 | 写 python driver，`subprocess` 用 **list 参数** + `PYTHONIOENCODING=utf-8` |
| 构建失败却"成功" | `cmd \| tail` 的退出码是 tail 的 | 判成败看 `rc=` 或日志里的 `error:`，别看管道尾 |
| grep 扫出 0 命中 | 相对路径在跨双树工程里扫空 | 扫描根一律绝对路径 |
| 走路日志半途 UnicodeEncodeError | 子进程管道按 GBK 解 | `subprocess(..., encoding="utf-8")` |
| `bash -c` 报 no input files | 二次转义吃掉文件名 | 命令写进 `.sh` 再跑 |
| 改了源码仿真没变 | exe 没重编 | `walk_capture` 已无条件重生成 main.c ⇒ 必重编；别手动 `-n` |
| sdkconfig 改动没生效 | 只改了 `sdkconfig` | 同步 `sdkconfig.defaults` + 复核 effective config；注意它是 CRLF |
| **反过来**：只改了 `sdkconfig.defaults` | `sdkconfig` 已存在时 defaults **完全不参与**（只有删掉 `sdkconfig` 才生效）⇒ 构建照样"成功"，配置没变 | 两个文件都要写；判据只认 `build/config/sdkconfig.h` 回读 |
| 真机方框但仿真正常 | 两端 `LV_FONT_DEFAULT` 不是一个东西 | 运行期建的控件必须自己 `set_style_text_font`（P-0118） |

---

## 8. 交付节奏（这个项目的用户偏好，别自作主张跳过）

1. **先方案后动手**：给 2-3 个机制 + 推荐 + 各自代价，等点头再改代码。
2. **一次一个改动、一炉一验证**：混着改就没法归因。
3. 用户会提前烧 ⇒ 要给明确的"可以烧了"信号 + **真机检查清单**（看哪几行日志、哪几个现象）。
4. 每轮收尾三步（做完才算完）：① 修错（结论被推翻就**公开撤回**并在库里追加更正段）
   ② 补新知识（`skills.md` 通则 / `intake/P-####` 问题 / `reference/` 主题）
   ③ 逐字补录提示词 `prompts/PROMPT_LOG.md`（PR-####）+ 工程侧 `.workbuddy/memory/<日期>.md`。
5. 写状态/行为类结论前先问一句：**这条仿真真能验到吗？** 验不到就写"只能真机验"，不要顺手算已验证。
