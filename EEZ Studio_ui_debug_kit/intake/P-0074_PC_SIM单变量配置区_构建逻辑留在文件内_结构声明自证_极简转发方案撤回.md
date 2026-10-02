# P-0074 · PC_SIM 单变量配置区（构建逻辑留在文件内）——「极简转发」方案撤回

- 日期：2026-10-03（工程当日记忆 = .workbuddy/memory/2026-10-02.md 第 87 轮）
- 状态：fixed
- 标签：单变量配置区,结构声明,撤回转发,目录协议真值源,防脚本盖用户改值,CMakeLists 自证
- 相关：P-0071（目录协议）/ P-0072（分辨率推导死代码）/ P-0073（极简转发，本次撤回）

## 用户原话（决定方案走向的那句）
> 「我还原了，我要保证最简单的修改，我需要的是，允许这个文件 适配 每个工程只需要
> 配置 cmakelist 中指定工程路径变量即可，需要声明工程的大致结构即可」

拆成三条硬要求：
1. **改动量 = 单点**：换工程只配置 CMakelists 里那个「工程路径变量」；
2. **这个文件自己适配每个工程**（= 构建逻辑留在 PC_SIM 里，不是搬到工程侧）；
3. **声明工程的大致结构即可**（= 文件里要有目录树/推导规则的结构声明，让人自证）。

## 与 P-0073（极简转发）的取舍
| | P-0073 极简转发（已撤） | P-0074 单变量配置区（采用） |
|---|---|---|
| 逻辑位置 | 搬到工程侧 `sim_build.cmake` | **留在 PC_SIM 根 CMakeLists** |
| PC_SIM 文件 | 371→29 行的转发壳 | 371→~200 行的适配层 |
| 换工程改哪 | 改 `sim_init.cmake` 一行 | 改 CMakeLists 顶部配置区一行 |
| 用户视角 | 逻辑不在眼前，要跳两个文件 | 逻辑 + 结构声明都在这一个文件里 |

**教训（可复用）**：用户要的「简单」= **改动单点 + 结构自明**，
不 = 文件行数少。把逻辑搬出他`只许改一行`的目录（PC_SIM），
换来"文件短了"却把认知成本挪到了别处 —— 判定失误，直接撤。

## 落地
- `common/PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt`（唯一被改的仿真器文件）：
  - 顶部 **★配置区**：只有一处 `set(TARGET_PROJ_DIR "<工程根>" CACHE PATH ★...)`；
    下方列破例 `-D` 清单（UI_DIR / NATIVE_DIR / SIM_MAIN_DIR / APL_LVGL_DIR /
    SIM_H_RES / SIM_V_RES），留空即自动推导；
  - 再下 **工程结构声明**：目录树（src/ui · src/native · design/sim_cmake ·
    design/build_ui.py）、内核 `common/APL/apl_lvgl*`、`-D > build_ui.py >
    lv_conf.h` 的优先级、仿真器自带文件仍编译；
  - 逻辑段：三目录推导 → 内核 up-walk → GLOB（排除 io_esp/test_native）→
    LVGL 配置 `_PATH` 注入（`_DIR` 置空）→ 分辨率推导 → 编译/链接。
  - 死代码照样清：FreeRTOS 三分支、五个可选库、Debug 墙+ASAN、ccache、
    `include_directories(main/inc)`（该目录根本不存在）。
    **删前 `grep -rl` 查依赖，`LV_INTERFACE_SIM` 必须留**（仿真器侧无人用，工程 io_pc 用）。
- `design/sim.py`：
  - 删 `write_simbuild()` / `write_siminit()`；新增 `read_target_proj_dir()`；
  - **绝不传 `-DTARGET_PROJ_DIR=`** —— 否则用户手改配置区那一行会被脚本每次盖回去
    （★真值源冲突：脚本"自动指向当前工程" ≠ 用户"手改成别的工程"，必须让手改优先；
    脚本只在那一行缺失或指向不存在的目录时兜底写成本工程）；
  - `build()` 去掉 `-C sim_init.cmake`，接入点回到 **两件套**（main.c + lv_conf.h）。
- 清理：删 `design/sim_cmake/sim_build.cmake`、`sim_init.cmake` 旧产物。
- 备份：`CMakeLists.v2_371lines.bak`（协议版）、`CMakeLists.v0_240lines.pristine.bak`（原版）。

## 验证（按 P-0057/0070 防假绿：先 `mv bin/main.exe` 再 `mv build`）
- 全量 `design/sim.py` EXIT=0：全新 configure + 真编译 + 冒烟全绿 + 截图 14/11；
- `CMakeCache.txt` 自证四项推导命中：`TARGET_PROJ_DIR/UI_DIR/NATIVE_DIR/SIM_MAIN_DIR`
  → 本工程、`APL_LVGL_DIR`→`common/APL/apl_lvgl_v9_4`、`LV_BUILD_CONF_PATH`→工程侧
  `sim_cmake/lv_conf.h`、`SIM_H_RES/SIM_V_RES`=**800/480**（真来自 build_ui.py）；
  `grep -c "sim_init.cmake\|sim_build.cmake" CMakeCache.txt` = **0**（旧链路清干净）；
- `--walk=wifi_ok` 3 图 / `--walk=pwd` 2 图，目检 `12_ok.png`
  （`HomeNet-5G · WPA2 PSK · 已保存` + 已连接 + 192.168.1.23）正常；
- `_device_syntax_check.py` 4 文件 0 错 0 警。

## 下次注意
- 改 PC_SIM 仍是「一个文件、一个变量」，别再发明"转发/搬运"花样；
- 任何"脚本替用户改某个他手改的文件"的设计，都要先问答：会不会盖掉他的正确选择
  （本次就靠 `read_target_proj_dir()` 只在失效时兜底才不犯这个错）；
- 保留自证：configure 期打 `[sim] 工程=/UI=/NATIVE=/内核/窗口=` 三行 message。
