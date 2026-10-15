# embedded/ — 嵌入式经验库索引

> 本目录是**自建中文经验库**的一半（另一半在仓库根的 `yjt/`），两边各有分区索引：
> 本文件 与 `yjt/README.md`；入口规则见仓库根 `AGENTS.md`。
> 仓库根 `README.md` 里有三个自建章节（`### Embedded`、`### UI Debug Kit`、`### YJT`），
> 已按当前结构收录（2026-10-15 校验：链接全部可解析）。
>
> 本索引最后更新：2026-10-15（`esp32/` 与 `EEZ Studio_ui_debug_kit/` 从仓库根并入；
> 原平铺在本目录根的 6 篇笔记已按主题归入专门文件夹）。

---

## 1. 子库（自带方法论 + 记录区，体量较大）

| 子库 | 讲什么 | 什么时候查 |
|---|---|---|
| `embedded/esp32/` | ESP32-P4/C6 实战四篇：Windows 下 IDF 构建通路、LVGL 9 触摸 LCD 调试与优化主文档、帧率调优手册（playbook）、P4+C6 远程 WiFi（esp_hosted） | 碰 ESP-IDF 构建、LVGL 帧率/撕裂/旋转、托管组件还原、双核与 PPA 取舍 |
| `embedded/EEZ Studio_ui_debug_kit/` | **可移植的 UI 调试与验收工具箱**（ui_debug_kit）：整个文件夹拷进任意 UI 工程 + 填一份配置，即得"出效果图 → 对照定位 → 修复验收"能力。内核在 `PLAYBOOK.md`/`CONFIG.md`/`tools/`/`cases/`，记录区在 `skills.md`/`intake/`/`prompts/` | 任何"用组件树描述界面 + 由它生成代码"的 UI 方案（EEZ Studio、LVGL、Web/桌面/移动前端）要做像素级对照与回归门禁 |

进 `EEZ Studio_ui_debug_kit/` 先读它的 `README.md`（30 秒上手），再读 `PLAYBOOK.md`。

## 2. 主题文件夹（一主题一目录，2026-10-15 归置完成）

| 文件夹 | 内容 | 一句话 | 什么时候查 |
|---|---|---|---|
| `embedded/debug-methodology/` | `debug-methodology.md` | 四种通用排查打法：参考示例入手 / 对比法 / 问题点法 / github issues 搜索法 | **没头绪时先读这篇**，它是本目录其余各篇的上一层方法 |
| `embedded/debugger/` | `debugger-jlink-stlink-wchlink.md` | J-Link V8 刷固件救砖、WCH-Link 双接口双驱动、ST-LINK | 调试器连不上 / 报 defective / 变砖 |
| `embedded/ide/` | `iar-keil-ide-issues.md` | IAR、Keil MDK、RT-Thread Studio 的 IDE 层坑（跳转失效、优化导致变量不可见、编码与路径） | 编译能过但调试行为诡异 |
| `embedded/rt-thread/` | `rt-thread-pitfalls.md` | RT-Thread hard fault 定位、线程栈溢出的统一根因、定时器回调上下文限制 | RT-Thread 上 assertion failed / 随机死机 |
| `embedded/stm32/` | `stm32-hal-pitfalls.md` | STM32/HAL 经典坑：时钟先使能、printf 重定向三件套、JTAG 引脚复用前必须释放 | 配置看不出问题但外设就是不工作 |

新增同主题经验请**往对应文件夹里加文件**，不要退回本目录根平铺。
新芯片/新主题 → 新建一个文件夹，并在本表加一行。

## 3. Keil C51 那篇为什么不在这里

`keil-c51-pdata-overlay.md`（L18 pdata 跨页 / L15 Overlay 重入）已移到 **`yjt/STC8H_8G/`**，
理由是它只在 8051 + Keil C51 上成立，且那一目录已有同族两篇（`keil-c51-language-pitfalls.md` 语言层坑、
`keil-c51-overlay-function-pointer.md` 函数指针使 Overlay 失效）。三篇分工：语言层 / 链接器 Overlay 机制 / 内存模型警告。
C51 相关经验今后统一进 `yjt/STC8H_8G/`。

## 4. 新笔记落在哪：`embedded/` 还是 `yjt/`

- **只在一款芯片 / 一个工程上成立** → `yjt/<芯片或项目名>/`（现有：`ch571/`、`STC8H_8G/`、`MultiParam/`、`PEMS/`，索引见 `yjt/README.md`）。
- **跨项目、跨芯片可复用的方法论与工具** → `embedded/<主题>/`，一个主题一个文件夹。
- 判据模糊时问一句"换一颗芯片这条还成立吗"：成立进 `embedded/`，不成立进 `yjt/`。
- 已知灰色地带：RT-Thread 与 STM32 两篇都带平台属性，但结论主要是该 RTOS/该 HAL 的通用坑，故留 `embedded/`。

## 5. 引用与路径写法（2026-10-15 起统一）

- 文档里引用本库其他文件，**一律写仓库根相对路径**：`embedded/esp32/esp-idf-windows-build.md`，
  不要写 `esp32/...`（那是 2026-10-15 之前的旧位置；`skills.md`、`reference/09`、`intake/P-0120` 里的旧写法已分别就地更正或追加勘误）。
- **移动文件要同时处理两类断链**：文字里的路径标签、Markdown 链接里的 `../` 深度。
  本轮已处理：`embedded/debug-methodology/debug-methodology.md` 指向 `../../python/cv-ncnn-pybind-errors.md`（下沉一层后已从 `../` 改 `../../`）；
  `embedded/stm32/stm32-hal-pitfalls.md` 里对 rt-thread 篇的裸文件名指代已补全路径；
  `embedded/esp32/esp-idf-windows-build.md` 里的 `../EEZ Studio_ui_debug_kit/...` 是同层兄弟引用，仍有效。
- 「`esp32` 子库」「ui_debug_kit」这类**称呼**保持稳定，变的只是路径。

## 6. 机器相关路径：统一规矩（适用于本库所有文件）

库里若干文件写着 `C:\Users\Administrator\...`、`D:\esp32_8266_files\...`、`~/.qoder-cn/tmp\...`。
2026-10-15 在本机（用户 `yjt54`）逐条到文件系统实测过，**结论不是"全都失效"，而是分三类**：

| 文档里的写法 | 本机实测 |
|---|---|
| `D:\esp32_8266_files\esp-idf-v5.5.5_ol`（IDF 根） | ✅ 存在 |
| IDF 根 `idf_cmd_init.bat` + `idf_build.bat`（构建通路唯一入口） | ✅ 两个都在 |
| `{ROOT}` = `...\examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_ai\eez-test` | ✅ 存在（`design/`、`src/`、`test.eez-project`、`ui_debug_kit.config.json` 齐） |
| `C:\Users\Administrator\.workbuddy\...\envs\default\Scripts\python.exe`（`{PY}`，唯一装了 PIL 的解释器） | ✅ 本机等价物存在，只是用户名换成 `yjt54` 后同布局命中 |
| `C:\Users\Administrator\AppData\Local\Programs\eezstudio\EEZ Studio.exe` | ✅ 同上，换用户名即命中 |
| `...\AppData\Local\Espressif\ComponentManager\Cache\`（托管组件干净副本） | ✅ 本机 `%LOCALAPPDATA%` 下存在 |
| `.workbuddy\binaries\node\versions\22.22.2-3\node.exe` | ⚠️ 版本号不同：本机是 `22.22.2-6` |
| `D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5`（工具链目录） | ❌ 不存在。本机只有 `esp-idf-tools_for_idf_v5_5_1` 与默认 `C:\Users\yjt54\.espressif\tools` |
| `...\idf_v555_my_exps\common\PC_SIM\lv_port_pc_vscode_v9.5`（PC 仿真器根） | ❌ 不存在（`common/` 下只有 `APL`、`DRV`） |
| `...\common\APL\apl_lvgl_v9_4`（LVGL 内核） | ❌ 不存在（`APL` 下只有 apl_atomic / apl_console* / apl_utility） |
| `{IDF_ROOT}\build` | ❌ 不存在（本机尚未构建过） |
| `C:\Users\Administrator\.qoder-cn\tmp\` 里的 `run_round.sh` / `cap_serial.py` / `idf.ps1` | ❌ 不存在。本机 `.qoder-cn\tmp` 是会话临时目录，只有 session 子目录 |
| `C:\Users\yjt54\eez-projects\examples\eez_lvgl_demo`（官方参照工程） | ❌ 不存在（本机 `eez-projects` 下只有 `eez-test`） |

规矩：

1. 表里标 ✅ 且只是用户名不同的，直接把 `Administrator` 换成当前用户名即可，不必再猜；
2. 标 ⚠️ / ❌ 的**不得当事实使用**：确认不了就问用户，禁止扫盘猜（`EEZ Studio_ui_debug_kit/config.template.json` 的 `sim` 段已写明同一条）；
3. 本机实测到新真值就回来更新本表并标日期；表里没有的路径按第 1 条流程先测再记。
4. **工程侧文件不在本库范围内**：`D:\...\eez-test\ui_debug_kit.config.json` 的 `binaries.python` / `python_venv` / `node` /
   `runtime.exe` 四条目前仍写 `Administrator`，在本机跑 kit 会被 `config_check.py` ERROR 阻断（这正是它的设计）。
   改那 4 行属于**改工程配置**，需用户确认后再动，本库只做记录。
5. 已加顶注/行内标注的 4 份文件：`embedded/esp32/esp-idf-windows-build.md`、
   `embedded/esp32/esp32-p4-lvgl9-touch-lcd-debug-optimization.md`、
   `embedded/EEZ Studio_ui_debug_kit/reference/09_build_flash_debug_lvgl_demo_ai.md`、
   `embedded/EEZ Studio_ui_debug_kit/CONFIG.md`（§4.1 行内）。顶注只指路到本表，不再各自重复结论。
6. `intake/`、`prompts/` 里出现的历史路径属于**证据记录**，按第 7 节规矩只追加、不改写
   （已知：`P-0017`、`P-0043`、`P-0065`、`P-0101`、`PROMPT_LOG` 数条）。

## 7. 记录区纪律（`embedded/EEZ Studio_ui_debug_kit/intake/`、`prompts/`）

编号只增不改；结论被推翻时**追加**一个新段（如 `P-0120` 的「★ 追加更正」「★ 追加 5」），前文原文保留。
这条是那些文件里 `esp32/...` 旧路径不被就地改写的唯一原因。
