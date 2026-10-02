# P-0073 PC_SIM 根 CMakeLists 极简转发：构建逻辑全搬工程侧，祖传包袱全删

日期：2026-10-02   状态：fixed（配套 P-0069 瘦身 / P-0071 目录协议 / P-0072 协议收尾）

## 一、起因：适配层已经不用改了，但文件还是 345 行，用户看着心慌

用户原话两层意思：

1. 「后期按照统一的工程目录结构的话，是不是不用改了，只需要改工程目录即可」
   → **是**：P-0071 的目录协议落地并验证后，换工程只改
   `design/sim_cmake/sim_init.cmake` 里那一行 `TARGET_PROJ_DIR`
   （那行还是 `sim.py` 自动生成的），`PC_SIM/.../CMakeLists.txt` 一次都不用再碰。
2. 「感觉这个文件现在改的太多了，有点复杂」
   → 通读 371 行后拆类：真正干活的只有约 200 行（目录协议块 + GLOB +
   `add_subdirectory(apl_lvgl)` + ThorVG 屏蔽 + `add_executable` + 链接），
   另外约 170 行是**仿真器自带的祖传包袱**，我们一次都没用过。

## 二、祖传包袱清单（全部可删，实测无影响）

| 块 | 行号 | 为什么能删 |
|---|---|---|
| FreeRTOS 整条分支（`FREERTOS_PORT` / `option(USE_FREERTOS)` / `add_subdirectory(FreeRTOS)` / 三个 `if(USE_FREETOS)` 的 add_executable 与 link 分支） | L152-184、254-264、288-291 | 非 FreeRTOS 分支早就改用工程侧 main.c 了，FreeRTOS 源文件根本不进构建 |
| SDL2_image / libpng / libjpeg-turbo / FFmpeg / FreeType 五个可选库 | L189-194、L296-328 | 五个 option 默认全 OFF，对应的 `find_package` 分支一次没进 |
| Debug 警告墙（-pedantic-errors -Wshadow … 22 条）+ ASAN 分支 | L330-371 | `sim.py` 恒定传 `-DCMAKE_BUILD_TYPE=Release`，从不进 Debug |
| ccache 探测 | L205-216 | 本机没装 ccache，纯 message 噪音 |
| `include_directories(${PROJECT_SOURCE_DIR}/main/inc)` | L187 | `main/inc` 目录**根本不存在** |
| `set(WORKING_DIRECTORY ...)` | L203 | 无意义的空设置 |

依赖核对（动手前先查，别凭印象删）：
- `main/src/mouse_cursor_icon.c` 只 `#include "lvgl.h"`，不依赖 `main/inc`；
- `lv_interface_sim` / `LV_INTERFACE_SIM` 在仿真器侧**无人引用**，但工程侧 `io_pc`
  可能用，所以 `option(LV_INTERFACE_SIM)` + `add_compile_definitions` **保留**（2 行）。

## 三、修法：极简转发（forwarding include）

**PC_SIM 根 CMakeLists.txt 从 371 行 → 29 行**，只剩三件事：

```cmake
cmake_minimum_required(VERSION 3.10)
project(lvgl C CXX)                      # 必须留：apl_lvgl 作 subdirectory 引用时靠它跳过自己的 project()
if(NOT TARGET_PROJ_DIR) message(FATAL_ERROR ...) endif()
get_filename_component(TARGET_PROJ_DIR "${TARGET_PROJ_DIR}" ABSOLUTE)
include("${TARGET_PROJ_DIR}/design/sim_cmake/sim_build.cmake")
```

**全部构建逻辑搬到工程侧** `<TARGET_PROJ_DIR>/design/sim_cmake/sim_build.cmake`，
由 `design/sim.py` 的 `write_simbuild()` 生成（**181 行**，与 sim.cmake 目录里
main.c / lv_conf.h / sim_init.cmake 合称「接入点四件套」）。

这么做相对「就地瘦身」的三个额外好处：

1. **PC_SIM 那个文件从此彻底封版**：换工程只动工程侧，
   仿真器目录被覆盖/升级/换版本都不影响我们（原来还要担心适配层被冲掉）。
2. **逻辑跟着工程走**：目录协议本来就要求"工程结构统一"，构建逻辑落在工程侧，
   新工程 clone 下来自带，不用先去仿真器目录抄一段 CMake。
3. **职责彻底单一**：PC_SIM 只负责"起个壳"，看不懂的部分都在工程侧文件里。

配套：完整历史版备份 `design/sim_cmake/CMakeLists.v2_371lines.bak`（想回退直接拷回）。

## 四、证据

| 项 | 前 | 后 |
|---|---|---|
| PC_SIM 根 CMakeLists | 371 行（自定义 +133/−28） | **29 行**（转发壳，其中 20 行是目录协议速查注释） |
| sim_build.cmake | 无 | 181 行（工程侧，sim.py 生成） |
| 祖传包袱引用 | FreeRTOS ×3 分支 / 5 个可选库 / Debug+ASAN / ccache | 全 0（grep 无残留） |

**验证（按 P-0070 的假绿教训，先造全新构建环境再验）**：

1. `mv bin/main.exe /tmp` + `mv build /tmp` —— 挪走 exe 防 `exe_stale()` 跳过编译
   （P-0070 坑），挪走 build 模拟换工程后的**首次全新 configure**；
2. `python design/sim.py`（prepare 生成新接入点四件套 → cmake -C 全新配 → 真编译
   → 11 屏出图）：**EXIT=0，2m38s 全量真编译**，冒烟测试全绿
   （tab 切换 / 音乐播放进度 / 通知过滤 / 键盘绑定 / 滑动 tab 全部 expect 命中），
   出图 `截图 14/11`；
3. `sim.py --walk=pwd` → 2 图（`07_list` / `11_pwd`，密码面板排版完整，键盘齐全）；
   `--walk=wifi_ok` → 3 图（`07_list` / `10_connecting` / `12_ok`，
   `HomeNet-5G · WPA2 PSK · 已保存` + 「已连接」+ IP 正确）；
4. 目检 `11_pwd.png` / `12_ok.png` 两张关键屏 OK；
5. `design/_device_syntax_check.py` → 4 文件 0 错 0 警（本轮零设备侧改动）。

## 五、沉淀

- **"不用改了"和"改得太多"是两个问题**：协议让文件免改，但不等于文件该保持臃肿。
  判断依据 = **通读后按"是否真在构建中生效"分类**，死代码一律删（本轮删 170 行）。
- **改别人目录里的文件时，优先问"能不能搬出来"而不是"怎么改得更少"**：
  搬出后对方目录零改动、我们侧全掌控，比就地精简更彻底。
- **删依赖前先查**（`grep -rl` + 看 include），本轮靠这条保住了 `LV_INTERFACE_SIM`；
  判断"某块死代码不用了"要落到**文件级证据**（如 `main/inc` 目录不存在），不能靠记忆。
- **验证仿真器改动必须先造全新构建环境**：只挪 exe 不够（P-0070），
  连 `build/` 一起挪走才能证明"新 CMakeLists 真的被 configure 过"。
