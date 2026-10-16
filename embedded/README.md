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
| `embedded/jieli_soundbox_sdk/` | **杰理（Jieli）Soundbox SDK 经验**，按"跨型号通用 / 型号绑定"分两层：`common/`（编译烧录链、配置三层开关、任务状态机、按键事件流、VM/syscfg/SDFILE、外设驱动速查、led7 与 UI 框架、音频链路与在线调音、日志与异常定位、功耗、OTA 双备份、协议接入、配置工具量产）+ `ac695n_br23/`（芯片资源表、19 个板级映射、版本史） | 碰杰理 AC695N/AC696N/BR23 系蓝牙音频 SoC；先读 `jieli_soundbox_sdk/README.md` |

进 `EEZ Studio_ui_debug_kit/` 先读它的 `README.md`（30 秒上手），再读 `PLAYBOOK.md`。

## 2. 主题文件夹（一主题一目录，2026-10-15 归置完成）

| 文件夹 | 内容 | 一句话 | 什么时候查 |
|---|---|---|---|
| `embedded/debug-methodology/` | `debug-methodology.md`、`hardfault-crash-forensics.md` | 四种通用排查打法 + **死机/异常取证**（callstack、栈溢出判据、memset 越界、断言两种行为、寄存器读法） | **没头绪时先读前者**；崩了就查后者 |
| `embedded/debugger/` | `debugger-jlink-stlink-wchlink.md`、`stlink-jlink-remote-oscilloscope.md` | 调试器固件与驱动救砖 + **ST-Link 自制固件版本、J-Link 远程调试、示波器操作、SWD 引脚占用** | 调试器连不上 / 要远程调 / 要量波形 |
| `embedded/ide/` | `iar-keil-ide-issues.md` | IAR、Keil MDK、RT-Thread Studio 的 IDE 层坑 | 编译能过但调试行为诡异 |
| `embedded/mcu-peripherals/` | **6 主题篇 + 5 代码配方 + ERRATA 档 + COVERAGE 档**：UART/485/CAN/MODBUS、I2C/SPI 与器件驱动、SD/DCMI/FSMC、I2S/WAV、定时器/ADC/DMA、时钟/GPIO/NVIC/EXTI | 单片机**外设原理与用法**（跨芯片通用为主） | 配任何外设前；**引用那份 docx 前先查 ERRATA**；**想知道库里有没有某条内容先查 COVERAGE** |
| `embedded/mcu-chip-families/` | 7 篇：各家与 STM32 差异总表、GD32、AT32、PY32/Holtek、STC+沁恒 CH、CC2530/2538/2640、Z-Stack OSAL | **换芯片/换家时的"哪一点会咬人"清单** | 移植到 GD32/AT32/PY32/STC/CH/TI 时 |
| `embedded/mcu-toolchain-boot-flash/` | `README.md` | 启动链与堆栈、Keil/MicroLIB/scatter/map、BOOT 模式与串口 ISP 烧录、Flash 扇区与选项字节、IAP 跳转 | 改时钟、加烧录、做 IAP、看 map |
| `embedded/rt-thread/` | `rt-thread-pitfalls.md` | RT-Thread hard fault 定位、线程栈溢出的统一根因、定时器回调上下文限制 | RT-Thread 上 assertion failed / 随机死机 |
| `embedded/stm32/` | `stm32-hal-pitfalls.md` | STM32/HAL 经典坑：时钟先使能、printf 重定向三件套、JTAG 引脚复用前必须释放 | 配置看不出问题但外设就是不工作 |

**注意与本次新增的三目录的分工**：`stm32/`、`debug-methodology/`、`debugger/` 里的老篇来自
《问题解决和汇总 v1.2》；`mcu-peripherals/`、`mcu-chip-families/`、`mcu-toolchain-boot-flash/` 来自
《单片机外设和调试基础知识.docx》（2026-10-16 精读）。**同一主题两边都有时，以 `⚠校核` 标注和 ERRATA 为准。**

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

## 6. 机器相关路径：A/B 两类，处置方式完全不同

本库多篇文件写着 `C:\Users\Administrator\...`、`D:\esp32_8266_files\...`、`~/.qoder-cn/tmp\...`。
判别的唯一标准是：**这条路径是"用户名不同、布局相同"，还是"每台电脑都按个人习惯乱放"。**

**A 类 · 只与用户名绑定** —— 目录布局本身通用，把 `Administrator` 换成当前用户名即可用。
允许"推断 + 实测确认"，不必每次问用户。

**B 类 · 每机都不同的变量** —— 位置与目录名随各人的存放习惯变化，**经验库里不得存成事实**。
文档中一律按 `{占位符}` 看待，写死的那串字符只是**来源机器的样本**；
**用之前必须让用户指定这台电脑上的真值**，禁止扫盘猜，也禁止拿样本值直接跑。

**不算待办的一类**：IDF 工具包与 Python 环境（`esp-idf-tools_for_idf_v5_5_5`、`IDF_TOOLS_PATH`、`IDF_PYTHON_ENV_PATH`）
由本机 IDF 安装和用户自己的环境配置解决，**已经配好了**；经验库里出现的那串目录名只说明当时装在哪，
不需要每机核对，也不要拿它当"缺失项"提醒用户。

| 文档里的写法 | 类别 | 2026-10-15 在 `yjt54` 机器的抽样 |
|---|---|---|
| `D:\esp32_8266_files\esp-idf-v5.5.5_ol`（IDF 根） | A | 存在 |
| IDF 根 `idf_cmd_init.bat` + `idf_build.bat`（构建通路唯一入口） | A | 两个都在 |
| `{ROOT}` = `...\examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_ai\eez-test` | A | 存在（`design/`、`src/`、`test.eez-project`、`ui_debug_kit.config.json` 齐） |
| `C:\Users\Administrator\.workbuddy\...\envs\default\Scripts\python.exe`（`{PY}`，装了 PIL 的解释器） | A | 等价物存在，换用户名即命中 |
| `...\AppData\Local\Programs\eezstudio\EEZ Studio.exe`（`{EXE}` 的宿主） | A | 同上 |
| `...\AppData\Local\Espressif\ComponentManager\Cache\`（托管组件干净副本） | A | `%LOCALAPPDATA%` 下存在 |
| `.workbuddy\binaries\node\versions\22.22.2-3\node.exe` | A（版本号是变量） | 本机实际为 `22.22.2-6`，取目录里在的版本 |
| `...\idf_v555_my_exps\common\PC_SIM\lv_port_pc_vscode_v9.5`（PC 仿真器根） | **B** | 未命中（本机 `common/` 下只有 `APL`、`DRV`） |
| `...\common\APL\apl_lvgl_v9_4`（LVGL 内核源码目录） | **B** | 未命中（本机 `APL` 下只有 apl_atomic / apl_console* / apl_utility） |
| `.qoder-cn\tmp` 里的 `run_round.sh` / `cap_serial.py` / `idf.ps1` | **B** | 未命中；本机 `.qoder-cn\tmp` 是会话临时目录，只放 session 子目录 |
| `eez-projects\examples\eez_lvgl_demo`（官方参照工程） | **B** | 未命中（本机 `eez-projects` 下只有 `eez-test`） |
| `{IDF_ROOT}\build` | 派生物 | 未命中（本机尚未构建过；跑一次构建即出现，不是要找的路径） |

怎么用这张表：

1. 读经验碰到 **A 类** → 直接换用户名，实测存在就照用；
2. 碰到 **B 类** → **先问用户要这一台机器上的真值**，拿到再执行。真值写进**工程侧配置**
   （kit 的 `ui_debug_kit.config.json`、或作业卡里标"本机"的那一段），
   **不要回填进经验正文**——正文只留占位符、做法和判据。`config.template.json` 的 `sim` 段注释就是这个设计；
3. 本表"抽样"那一列只用于**判类别**，不构成长期事实；换一台机器重新看一遍即可，无需逐条改正文。

补充：`D:\...\eez-test\ui_debug_kit.config.json` 的 `binaries.python` / `python_venv` / `node` / `runtime.exe` 四条目前仍写 `Administrator`，
在本机跑 kit 会被 `config_check.py` ERROR 阻断（这正是它的设计）。改那 4 行属于**改工程配置**，需用户确认后再动，本库只做记录。

已加顶注 / 行内标注的 4 份文件：`embedded/esp32/esp-idf-windows-build.md`、
`embedded/esp32/esp32-p4-lvgl9-touch-lcd-debug-optimization.md`、
`embedded/EEZ Studio_ui_debug_kit/reference/09_build_flash_debug_lvgl_demo_ai.md`、
`embedded/EEZ Studio_ui_debug_kit/CONFIG.md`（§4.1 行内）。它们的顶注只指路到本节，不各自重复结论。

`intake/`、`prompts/` 里出现的历史路径属于**证据记录**，按第 7 节规矩只追加、不改写
（已知：`P-0017`、`P-0043`、`P-0065`、`P-0101`、`PROMPT_LOG` 数条）。

## 7. 记录区纪律（`embedded/EEZ Studio_ui_debug_kit/intake/`、`prompts/`）

编号只增不改；结论被推翻时**追加**一个新段（如 `P-0120` 的「★ 追加更正」「★ 追加 5」），前文原文保留。
这条是那些文件里 `esp32/...` 旧路径不被就地改写的唯一原因。
