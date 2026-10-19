# 11 · 最小 EEZ 工程脚手架（ESP32-P4 / LVGL 9.4 / ESP-IDF 5.5.5）

> 工程实践类（非手册提炼）。适用两种场景：
> ① 已有一个跑通的 LVGL 显示工程，要从零接入 EEZ Studio UI；
> ② 从零建一个**可编译的最小 EEZ 模板**（先跑通"显示 + 触摸 + 控制台"，再往上堆 UI）。
>
> 实例来源：`p4_touch_lcd4_3_exp/lvgl_demo_template`（参考 `lvgl_demo_ai` 精简而来）。
> 机器路径约定见 `../AGENTS.md` 第 4 节：IDF 根与工程根属 A 类，可直接用。

---

## §0 目录结构（四块，各司其职）

| 目录 | 角色 | 要点 |
|---|---|---|
| `main/` | **入口** | 只做：`hw_board_init()` → `dsi_display_start()` → `dsi_display_lock()` → `ui_init()` → 建 5ms `ui_tick` 定时器 → `dsi_display_unlock()` → `dsi_display_run()`。渲染必须等 `dsi_display_run()`；对象树没建好就让 LVGL 任务跑会崩（空/NULL 屏渲染） |
| `eez-test/src/ui/` | **EEZ 导出区** | EEZ Studio 整目录覆盖写入。**不要手改**；入口固定为 `ui_init()` / `ui_tick()`，所以覆盖后 `main.c` 不用动 |
| `eez-test/src/native/` | **用户实现层** | 真 IDF 组件。EEZ 只生成**声明**（`vars.h` / `actions.h`），`get_var_*` / `set_var_*` / `action_*` 的**唯一定义**必须在这里，否则链接报 `undefined reference` |
| `components/` | **板级与显示** | `board`（控制台/CPU 监控）、`board_config`（引脚/任务）、`dsi_display`（DSI + PPA 旋转 + LVGL 任务）、`lv_mem_psram`（LVGL 内存走 PSRAM） |

---

## §1 三条硬规矩

1. **native 只定义、不 `REQUIRES ui`。**
   `native/CMakeLists.txt` 里 `INCLUDE_DIRS "." "../ui"`，`REQUIRES lvgl`。
   若写 `REQUIRES ui` 会形成 `ui <-> native` 循环依赖；真正的链接方向（`ui` 需要 `native`）在顶层用 CMP0079 补（见 §2）。

2. **`ui` 组件用 `file(GLOB)` 收源，EEZ 导出新增文件后必须 reconfigure。**
   `file(GLOB)` 只在 **CMake 配置期**求值一次。EEZ Studio 首次导出会新增 `eez-flow.cpp` / `eez-flow.h` 等，
   这些文件出现在配置期之后，**不会进编译**，链接时报
   `undefined reference to eez_flow_init / eez_flow_tick / getFlowState / g_currentScreen`。
   修复：`touch eez-test/src/ui/CMakeLists.txt` 或删 `build/` 触发一次 reconfigure。
   （详见 `../intake/P-0156_*.md`）

3. **native 不要写死 EEZ 生成对象的句柄。**
   别在 native 里直接引用 `obj_label_status` 这类手写/生成对象名——EEZ 每次导出会重写 `screens.h`，
   手写句柄消失就编译断。native 回写 UI 的正道是**声明一个 Flow 变量，用生成的 `set_var_xxx()`**。

---

## §2 三大链接机制（顶层 `CMakeLists.txt`，`project()` 之后）

静态库抽取顺序坑的三种解法，缺一不可：

```cmake
# ① ui 依赖 native：否则 libnative.a 排在 ui.c.obj 之后，
#    action_* / get_var_* 全部 undefined reference。CMP0079 允许跨目录改 target。
#    不能写进 ui/CMakeLists（EEZ 每次导出重写它）。
cmake_policy(SET CMP0079 NEW)
idf_component_get_property(ui_lib ui COMPONENT_LIB)
idf_component_get_property(native_lib native COMPONENT_LIB)
target_link_libraries(${ui_lib} PUBLIC ${native_lib})

# ② LVGL 依赖 lv_mem_psram：提供 LVGL core malloc 的 PSRAM 实现
#    （CONFIG_LV_USE_CUSTOM_MALLOC=y）。注意 lvgl 是托管组件，注册名是 lvgl__lvgl（不是 lvgl）。
idf_component_get_property(lvgl_lib lvgl__lvgl COMPONENT_LIB)
idf_component_get_property(lv_mem_psram_lib lv_mem_psram COMPONENT_LIB)
target_link_libraries(${lvgl_lib} PUBLIC ${lv_mem_psram_lib})

# ③ 强抽 lv_os_pinned.c.obj：只有 liblvgl__lvgl.a 引用 OS 抽象层，
#    不给 --undefined 就不会被抽进来，绘制线程会丢掉核绑定（仍能跑，但 DRAW_UNIT_CNT=2 白配）。
target_link_options(${PROJECT_NAME}.elf PRIVATE "-Wl,--undefined=lv_thread_init")
```

另外两条工程级设置：
- `set(PROJECT_VER "1.0.0")`：git-describe 回退值（如 `ee0dbd3-dirty`）不是合法 `esp_app_desc` 版本号。
- `idf_build_set_property(MINIMAL_BUILD ON)` + `main` 显式短 `PRIV_REQUIRES`：
  `main` 被 IDF 特判（`REQUIRES`/`PRIV_REQUIRES` 都空时自动依赖**所有**组件），
  会让编译命令行逼近 Windows `CreateProcess` 32767 字符上限。

---

## §3 开关与 A/B 测量法（用宏，不用 Kconfig）

在 `main.c` 顶部放一行宏做 A/B 对照，**不要开 Kconfig**（改宏即重建，省去 menuconfig 往返）：

```c
/* 1 = 跑 EEZ UI（ui_init/ui_tick）；0 = 裸 LVGL 同界面，链接器按对象丢弃 ui 组件 */
#define APP_ENABLE_EEZ_UI  1
```

- `0` 组建一个"视觉等价"的裸 LVGL 屏（`bare_ui_create()`），`ui` 组件照常编译但无引用符号，
  被 `--gc-sections` **逐对象丢弃** → 两版之差就是 EEZ（及其连带）的真实代价。
- 取数命令（**必须用 JSON**，表格输出在非 tty 下会渲染错乱）：

```powershell
idf.py build
python -m esp_idf_size --files --format json build\lvgl_demo_template.map > build\size_on.json
# 切换宏为 0，再 build、再导出 size_off.json，然后逐对象求差
```

实测数字（最小模板：1 屏 1 label，`flowSupport=true` 但 UI 无 flow 逻辑；明细见 `../intake/P-0155_*.md`）：

| 项 | flash | RAM | 性质 |
|---|---|---|---|
| `eez-flow.cpp` 引擎本体 | 222,006 | 13,921 | **EEZ 真正净耗**（含 `.eh_frame` 31,144） |
| Montserrat 12~26 字体 | 163,955 | — | **内容**，非引擎——`screens.c` 字体表引用了 sdkconfig 启用的**全部**字号，关掉不用的即可省 |
| libm `pow`/`log` 系 | ~18,500 | — | 表达式求值器连带 |
| esp_timer `system_time` | 7,336 | — | flow 的 `millis()` 时基 |
| 合计（A/B 总差） | **+422,714** | **+14,449** | |

---

## §4 与 P-0154（lvgl_demo_ai 全量）的关系

| | 工程 | UI 规模 | EEZ 核心口径 |
|---|---|---|---|
| `../intake/P-0154_*.md` | lvgl_demo_ai | 11 屏 + 13px 中文字体 + flow 变量 | ≈259KB flash + ≈28KB RAM |
| 本篇 / `../intake/P-0155_*.md` | lvgl_demo_template | 1 屏 1 label，无 flow 逻辑 | 222KB flash + 13.9KB RAM |

差异解释：P-0154 的 setup 含 assets 常量（≈52KB rodata）与 flow 运行时状态（bss 25.7KB）；
最小模板无 assets、无 flow 逻辑，故 bss 只有 13.9KB。**两者一致的方法论结论**：

> 评框架资源必须做**三层拆分**——① 框架独有（引擎代码/静态表）；② 内容（字体/位图）；③ 两方案共有（屏幕 UI 创建代码）。
> 把②③算到框架头上，就会得到"EEZ 多耗 1.33MB"这类被 P-0154 两次更正过的错误口径。

---

## §5 相关

- `../intake/P-0155_*.md` — 最小模板资源账单（A/B 宏 + 逐对象 diff）
- `../intake/P-0156_*.md` — EEZ 导出后 GLOB 不刷新 → undefined reference
- `../intake/P-0154_*.md` — lvgl_demo_ai 资源实测（含两次更正与三重交叉验证）
- `09_build_flash_debug_lvgl_demo_ai.md` — ai 工程的编译·烧写·调试作业卡
- `10_hw_ui_separation.md` — 硬件 ⇄ UI 分离（跨项目模板）
