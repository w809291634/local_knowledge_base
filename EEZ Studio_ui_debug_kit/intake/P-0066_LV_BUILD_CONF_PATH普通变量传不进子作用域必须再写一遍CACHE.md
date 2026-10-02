# P-0066 · `LV_BUILD_CONF_PATH` 只写普通变量传不进 `add_subdirectory` 子作用域，必须再写一遍 CACHE

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真器 lv_port_pc_vscode_v9.5 + 共享内核 apl_lvgl_v9_4
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：CMake,作用域,子目录,lv_conf,静默回落,假绿,仿真
- **关联提示词**：无

## 现象（看到什么）

仿真器根 `CMakeLists.txt` 明明已经写了（在 `add_subdirectory(apl_lvgl)` 之前）：

```cmake
set(LV_BUILD_CONF_PATH "${SIM_MAIN_DIR}/lv_conf.h")   # 普通变量，父作用域
```

但内核 CMake 打印的却是回退分支：

```
-- Using lv_conf.h from the top-level project directory
-- Enabling the building of ThorVG internal
-- Enabling the building of examples
-- Enabling the building of demos
```

即：**编译期用的不是工程侧那份仿真 lv_conf**，而是 PC 仿真器根目录那份原始 `lv_conf.h`
（THORVG=1 / FS_STDIO=1）。这就是上一轮 P-0061 想根治、但没根治干净的病灶——
代价是 ThorVG 源文件被拖回编译、FS_STDIO 要 `dirent.h`，clang 下直接挂。

父作用域里 `message()` 打出来是有值的（证明 set 生效）：

```
-- [sim] DBG before add_subdir LV_BUILD_CONF_PATH=[D:/.../eez-test/design/sim_cmake/lv_conf.h]
```

而内核里 `message(STATUS ${LV_BUILD_CONF_PATH})`（os_desktop.cmake:78）打出来是**空字符串**——
同一个变量，进子作用域就空了。

## 复现（怎么稳定重现）

```bash
cmake -S <PC_SIM>/lv_port_pc_vscode_v9.5 -B <空目录> -G "MinGW Makefiles" | grep -n "lv_conf"
```

看是 `Using configuration: <sim 那份路径>` 还是 `Using lv_conf.h from the top-level project directory`。

## 根因（真正的原因）

`apl_lvgl_v9_4/CMakeLists.txt:26` 是 `include(env_support/cmake/os_desktop.cmake)`，
而它是被咱们 `add_subdirectory(${APL_LVGL_DIR} ...)` 拉进来的**子作用域**。
实测：父作用域设的**普通变量**在子作用域里读不到（这里表现为空串），
而 `os_desktop.cmake` 第 5 行 `set(LV_BUILD_CONF_PATH "" CACHE PATH ...)` 只在 cache 里建了个空项，
于是 `if(LV_BUILD_CONF_PATH)` 落假、走 `else()` 分支 —— **不报错、纯静默**，最坏的一类假绿。

上一轮（P-0061）的结论"必须用普通变量不能用 CACHE"是**过度修正**：
怕的是历史 cache 被钉成空，正确解法是"普通变量 + 同一行再写一份 CACHE"两条路都堵上，
而不是二选一。

## 修复（做了什么）

文件：仿真器根 `CMakeLists.txt`（适配层）

```cmake
set(LV_BUILD_CONF_DIR "")
set(LV_BUILD_CONF_PATH "${SIM_MAIN_DIR}/lv_conf.h")
set(LV_BUILD_CONF_PATH "${SIM_MAIN_DIR}/lv_conf.h" CACHE PATH "Sim lv_conf.h (full path)")   # ★ 这一行是关键
set(LV_CONF_PATH "${SIM_MAIN_DIR}/lv_conf.h" CACHE PATH "Shared LVGL config header")
```

- CACHE 变量一定被子作用域读到（`LV_BUILD_CONF_DIR ""` 同样用普通变量置空压掉历史值，避免两者同时非空触发 FATAL）。
- 普通变量保留兜底（同一份值，读谁都对）。
- 末尾加 `message(STATUS "[sim] LVGL 配置来源 = ${LV_BUILD_CONF_PATH}")`，**每次 configure 都自证配置注入落到了哪份 lv_conf**。

## 证据（数字 / 命令输出）

改之前：

```
-- Using lv_conf.h from the top-level project directory
-- Enabling the building of ThorVG internal
```

改之后（裸 configure、不带任何 `-D`）：

```
-- [sim] DBG before add_subdir LV_BUILD_CONF_PATH=[D:/.../eez-test/design/sim_cmake/lv_conf.h]
-- Using configuration: D:/.../eez-test/design/sim_cmake/lv_conf.h
-- Enabling the building of ThorVG internal      ← ThorVG/examples/demos 这两条在 sim.py 里靠
-- Enabling the building of examples             ← -DCONFIG_LV_USE_THORVG_INTERNAL=0 等关掉，
-- Enabling the building of demos                ← 与新注入的 lv_conf 无关，属同一问题的另一处开关
```

关键差异：从 `Using lv_conf.h from the top-level project directory` 变成
`Using configuration: <sim 那份 lv_conf>`。

## 沉淀（新增断言 / 案例 / 文档）

- 经验：跨 `add_subdirectory` 传值，父作用域**普通变量**不保证在子作用域可见；
  要"父→子"必传的值（尤其内核/库的开关类变量），**普通变量 + CACHE 各写一遍**，
  并在下游加一条 `message()` 自证，别靠推理。
- 经验：库 CMake 里那种"变量空了就静默回落默认配置"的分支，是最容易吃假绿的坑；
  一旦看到 `top-level project directory` / 默认配置类 message，就是没喂进去。
- 未加断言（CMake configure 期，不在 UI 断言范围）。
