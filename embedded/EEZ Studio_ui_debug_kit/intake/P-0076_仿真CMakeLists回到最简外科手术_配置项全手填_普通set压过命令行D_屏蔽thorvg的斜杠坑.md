# P-0076 · 仿真 CMakeLists 走「最简外科手术」：配置全手填 + 普通 set 压过 -D + ThorVG 屏蔽的斜杠坑

## 用户诉求（原话）
> 「改动太复杂了，`cmake -DSIM_H_RES=1024 -DSIM_V_RES=600 -B build` 不用这样，直接在 cmake
> 文件中修改即可，现在文件改动太大了，我要保证最简修改」
> 「APL_LVGL_DIR 这个自动查找也改成手动指定，不需要自动查找」

三条硬要求：
1. **不要命令行 `-D`** —— 所有配置写死在 CMakeLists 里，命令行压不动。
2. **diff 最小** —— 原版（240 行）骨架绝大部分内容**原样保留**（祖传死代码一律不删），
   只在原版上插入一个配置区 + 改必要几处。
3. **不留自动查找** —— 内核目录 `APL_LVGL_DIR` 也改成手填全路径。

## 做法：从「重写」退回「外科手术」
之前几版（371 行协议版 / 192 行极简转发版）都是**重写**：diff 记的是「被重写的行」而不是
净变化，视觉上吓人（240→192 只有 -21 行净变化，diff 却是 删199/增178）。
本版从 `CMakeLists.v0_240lines.pristine.bak` 复原原版，只做 6 处手术：

| # | 位置 | 手术内容 |
|---|---|---|
| ① | 顶部 L7 | 旧硬编码 `set(UI_DIR "${PROJECT_SOURCE_DIR}/../../../Template/.../main/ui")` → **配置区**（8 行普通 set + 结构声明注释） |
| ② | L18 | GLOB 从 `lv_ui/*.c + lv_interface/*.c` → EEZ 平铺 `${UI_DIR}/*.c｜*.cpp`，另收 NATIVE_SOURCES |
| ③ | L28 | `LV_CONF_PATH` → `LV_BUILD_CONF_PATH` + `LV_BUILD_CONF_DIR ""`（**必须 CACHE**，见下） |
| ④ | L31 | `APL_LVGL_DIR` 写死全路径（删掉 17 行 `while` 上探），配 `EXISTS .../CMakeLists.txt` 防呆 |
| ⑤ | L124/L141/L150 | 入口换 `${SIM_MAIN_DIR}/main.c` + NATIVE_SOURCES；链接加 WIN32 分支；include 补 NATIVE/SIM_MAIN |
| ⑥ | L157 | 加回 ThorVG 屏蔽（**正则必须吃两种斜杠**，见下） |

**结果**：293 行（原版 240），`diff = -30 / +83`（其中 36 行是注释）。对比重写版
（`-199 / +178`）温和得多；原版全部祖传内容保留（`USE_FREERTOS` 7 处、`SDL2_image` 4、
`libpng` 4、`jpeg` 7、`ffmpeg` 4、`freetype` 6、`ccache` 8、`LV_USE_DRAW_SDL` 4 全在）。

## ★ 三个真 bug（都是"静默失败"，取证才抓到）

### 1. ThorVG 屏蔽正则在 Windows 上永远匹配不上
内核 `os_desktop.cmake` L62：`file(GLOB_RECURSE SOURCES ${LVGL_ROOT_DIR}/src/*.c *.cpp *.S)`
→ **thorvg 源码直接进了 `lvgl` target**（不是 `CONFIG_LV_USE_THORVG_INTERNAL` 建的
`lvgl_thorvg` 库，那条只影响 install/链接）。
屏蔽代码 `_s MATCHES "libs/thorvg"` 用正斜杠，而 **Windows 的 SOURCES 是反斜杠路径**
→ 静默不匹配 → `config.h: No such file or directory` 满屏炸。
修：`if(_s MATCHES "libs[\\/]thorvg" OR _s MATCHES "vg_lite_tvg")`，并加自证
`message(STATUS "[sim] 屏蔽 ThorVG/vg_lite 源码 ${_blk} 个")` —— **实测从 0 → 49 个**，
这个数字就是"屏蔽到底有没有生效"的判据，以后再改一眼能看出（P-0076 核心教训）。

### 2. `LV_BUILD_CONF_PATH` 用普通变量传不进 `apl_lvgl` 子作用域
`apl_lvgl/env_support/cmake/os_desktop.cmake` L86：`if(LV_BUILD_CONF_PATH)` 读的是
**CACHE**。父作用域普通变量传不进去 → 静默 `Using lv_conf.h from the top-level
project directory` → 内核按自己那份（ThorVG=1/FS_STDIO=1）走 → 又见坑①。
必须 `set(LV_BUILD_CONF_PATH "${LVGL_CONF_FILE}" CACHE PATH ...)` + `LV_BUILD_CONF_DIR ""`
（两条非空内核会 FATAL）。修后自证变成 `Using configuration: <工程>/design/sim_cmake/lv_conf.h`。

### 3. 残留的旧 `set(SIM_H_RES 320 CACHE ...)` 是第二真值源
原版 L36-37 那两行没被第一刀删干净，`set(SIM_H_RES 800)`（普通）在 L23、
`set(SIM_H_RES 320 CACHE ...)` 在 L77 —— 自证输出直接打 `窗口=320x240`（**CACHE set 会
把同名普通变量干掉**）。清掉后恢复 800x480。
→ **同变量只允许出现一处**，多一处就会静默打脸；加 `grep -n "SIM_H_RES" CMakeLists.txt`
自查即可。

## 「不要命令行 -D」怎么保证
全部配置写成**普通 set（不带 CACHE）**。CMake 里普通变量遮蔽 CACHE 变量，命令行 `-D`
写进 CACHE 也压不过文件里的普通 set。
**实测**：`cmake -S PC_SIM -B /tmp/dchkt -DSIM_H_RES=999 -DSIM_V_RES=777` → 自证仍打
`窗口=800x480`，CACHE 里也翻不出 999 ✅ 真值源唯一。
配套改 `sim.py:read_target_proj_dir()` 的兜底模板：从「两行带 CACHE」改成
**单行普通 set**（`set(TARGET_PROJ_DIR "...")`，与文件里同一形态）。

## 验证（P-0057/0070 防假绿：`mv bin/main.exe` + `mv build`）
- 全量 `sim.py`：全新编译 **1m58s 通过** + onClick 冒烟全绿 + 截图 14/11。
- configure 自证四连：`屏蔽 ThorVG 49 个` / `工程=…` / `窗口=800x480` / `UI=…src/ui`，
  外加 `Using configuration:` 指向工程侧 lv_conf.h。
- `-D` 压不过文件值（见上）。
- `--walk=wifi_ok` 3 图，目检 `12_ok.png`（`HomeNet-5G · WPA2 PSK · 已保存` + 已连接 +
  192.168.1.23，排版正常）。
- `design/_device_syntax_check.py`：4 文件 0 错 0 警。设备侧零改动。

## 教训（可复用）
1. **"改动大"要按 diff 量算，不按行数净变化算** —— 重写能让行数变少（240→192）但 diff
   反而翻倍。用户看的是 diff 那两个数。
2. **最小 diff = 从原版骨架上手切，别重写**；拿不准就把原版备份先 cp 回来再 Edit。
3. **凡是屏蔽/排除，必须留一个自证数字**（`屏蔽 N 个`）或自证行 —— 否则正则写错会
   静默不匹配、症状是"编不过"，让人以为是别的原因（我这次就绕了三圈）。
4. **改完立刻 `grep -n <变量名> <文件>` 查第二真值源**，双真值源必有一个会静默赢。
