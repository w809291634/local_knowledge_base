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

### §3.1 压缩引擎的三项实测（2026-10-19，A/B 逐对象 diff）

保留 `flowSupport` 时，能真正压引擎的手段与实测（基线：queue 1000 / -O2 / 引擎 222KB）：

| 手段 | 怎么改 | 实测收益 | 代价/风险 |
|---|---|---|---|
| **执行队列 1000→128** | `.eez-project` 的 `executionQueueSize`（改生成头 `EEZ_FLOW_QUEUE_SIZE` 等价） | **内部 RAM −10,464 B**（12B/项，与理论精确吻合）；flash −122 | 队列满会报错；按 UI 复杂度调，勿过小 |
| **ui 组件 `-Os`** | 顶层 `target_compile_options(ui PRIVATE -Os)`，LVGL 保 `-O2` | **flash −79,873 B**（引擎自身 −36%，其中 text −40%） | 只慢 flow 求值/UI 创建，渲染热路径不受影响 |
| **关 CXX 异常/RTTI** | `sdkconfig.defaults` 去掉 `CONFIG_COMPILER_CXX_EXCEPTIONS` / `CXX_RTTI`（删旧 sdkconfig 重建） | **flash −72,343 B**（`.eh_frame` 29732→0，另有 34 个 unwind/typeinfo 对象消失）；RAM −393 | 需确认不依赖 C++ 异常——EEZ 引擎用自带 flow 级错误传播（`throwError`/`findCatchErrorComponent`，eez-flow.cpp:9572），**不用** C++ 异常，故安全 |

**累计**（相对最初 EEZ-on 基线）：flash `1,142,430 → 990,092`（**−148.8 KB / −13.3%**）；RAM `202,224 → 191,367`（**−10.6 KB**）。
⇒ 优化后「EEZ 相对裸 LVGL 的净代价」从 §3 表的 422,714B / 14,449B 降到 **约 270,376B flash / 3,592B RAM**。

> 注意：这三项**都不减那 222KB「引擎代码」的固有能力**，而是分别压 SRAM、压代码密度、去掉用不到的 EH 运行时。
> 手册 Build 面板那 3 项里，**只有 `Execution queue size` 对本模板有效**；`Compress flow definition` 在最小 flow（`assets[332]`）下会**净增** flash（贴进 LZ4 库）。
> 详见 `../intake/P-0157_*.md`。

> **口径更正（2026-10-19）**：§3 表里的「A/B 总差」把 **字体** 也算进了 EEZ，那是不严的。剥离字体后：
> **EEZ 自身 ≈ 131,184B flash + 3,985B RAM**（引擎 94,668 + 生成 screens/ui 740 + 引擎连带 35,776）；
> **字体 164,138B** 是 LVGL 资产（因 sdkconfig 开了 7 档 + EEZ 字体名表按名引用才被拉入），**非 EEZ**。
> 整机 991,024B = 裸底座 695,712 + EEZ 131,184 + 字体 164,138。
>
> ★ **别用 `.a`/`.o` 的文件大小估固件占用**：`libui.a` 磁盘 5.73MB，其中约 98% 是 `.debug_*` 与符号表；
> `strip --strip-debug` 后仍有 2.14MB（含未被 `--gc-sections` 丢弃的未引用代码/字符串），
> 而真正进固件只有 **95,408B flash + 3,553B RAM**（用 `idf.py size-files` 或 map 才作数）。
> 详见 `../intake/P-0158_*.md`。
**未优化 vs 优化后（分组级实测）**

| 项 | 未优化 | 优化后 | 差值 |
|---|---:|---:|---:|
| 固件 bin（烧写） | 1.09 MB | **967.8 KB** | **−148.9 KB** |
| 链接后合计 | 1.09 MB | 966.9 KB | −152.3 KB |
| 内部 RAM (bss+data) | 197.5 KB | 186.9 KB | −10.6 KB |
| EEZ 引擎 (eez-flow.cpp) | 216.8 KB | **92.4 KB** | **−124.4 KB** |
| EEZ 生成 UI | 0.73 KB | 0.72 KB | — |
| 字体资源 (Montserrat) | 174.9 KB | 174.9 KB | 0（属 LVGL 资产，省不掉） |
| 字体渲染/加载 | 2.9 KB | 2.9 KB | 0 |
| LVGL 内核 | 296.6 KB | 296.6 KB | 0 |
| 显示/触摸/适配 | 35.1 KB | 35.1 KB | 0 |
| 本项目组件 | 12.3 KB | 12.3 KB | 0 |
| C/C++ 运行时 | 29.6 KB | 5.9 KB | −23.7 KB（异常运行时消失） |
| IDF 内核 | 206.4 KB | 205.8 KB | −0.6 KB |
| 其它 | 140.3 KB | 140.3 KB | 0 |
| `.eh_frame` | 36.1 KB | 0 | −36.1 KB |

> 未优化 = 队列 1000 + ui 无 `-Os` + CXX 异常/RTTI 开；优化后 = 队列 128 + ui `-Os` + 异常/RTTI 关。
> 收益约 84% 来自「EEZ 引擎本体 + 异常运行时」；字体/LVGL/驱动等与这三项无关，两版完全不变。
> 数据由 `../tools/ui_size_report.py` 出（同工程两配置各构建一次）；精确字节与逐文件明细见 `../intake/P-0159_*.md`。
**递进阶梯（每步只叠加一项，各构建一次）**

| 步骤 | 配置 | 固件 bin | 链接后 | 内部 RAM | EEZ 引擎 | C/C++ 运行时 | `.eh_frame` | 本步增量 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | 未优化（队列1000 / -O2 / 异常开） | 1.09 MB | 1,142,430 | 197.5 KB | 216.8 KB | 29.6 KB | 36.1 KB | — |
| 1 | + ui `-Os` | 1.01 MB | 1,062,465 | 197.5 KB | 138.7 KB | 29.6 KB | 29.0 KB | flash **−79.9 KB** |
| 2 | + 队列 128 | 1.01 MB | 1,062,435 | 187.3 KB | 138.7 KB | 29.6 KB | 29.0 KB | RAM **−10.5 KB** |
| 3 | + 关 CXX 异常/RTTI | **967.8 KB** | 990,092 | **186.9 KB** | **92.4 KB** | **5.9 KB** | **0** | flash **−72.4 KB** |

> 边际：`-Os` 主要压引擎代码（顺带把 `.eh_frame` 36.9→29.7 KB）；队列只动静态 bss（每项 12B）；
> 关异常删掉整套 EH 运行时（`.eh_frame`→0 + libgcc unwind + libstdc++ EH/typeinfo）。
> 三者作用点不重叠 ⇒ **可加、且顺序不影响总量**。
> 四步完整脚本 log 见 `../intake/P-0160_*.md`。
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
- `../tools/ui_size_report.py` — 固件 flash/RAM 占用报告工具（自包含，可直接拷进工程根目录跑）
- `09_build_flash_debug_lvgl_demo_ai.md` — ai 工程的编译·烧写·调试作业卡
- `10_hw_ui_separation.md` — 硬件 ⇄ UI 分离（跨项目模板）

---

## §6 ★ 铁律：控件结构必须照抄 EEZ 原生形态，禁止自创（P-0164 坑 20）

**用 EEZ GUI 新建一个控件（如按钮），它的默认 JSON 结构就是唯一正确模板——
照抄默认形态，只改 text/坐标/样式值。禁止自己发明控件内部结构。**

### 反例（自创结构的三种翻车，全部实测）

| 自创写法 | 后果 |
|---|---|
| 手工坐标居中（label 收窄 + x 手算） | 字宽估算一错就偏；改字号/文案即失效（实测偏 +40px） |
| ~~按钮子 label 铺满 + `text_align`~~ | ~~画布不渲染~~ **已勘误**：画布是真实 LVGL wasm，`text_align` 有效；当时的画布异常是字体缺字形（见 P-0164 勘误节） |
| 子 label `align:"CENTER"` + `widthUnit:"content"`（EEZ 原生属性却在自创组合里用） | **label 飘出父容器**（定位锚定异常，EEZ v3 + LVGL 9.4 组合 bug） |
| label **缺 width 字段** | EEZ 发 `set_size(0,h)` / `NaN` → 0 宽 + WRAP = 文字叠成竖条；C 侧 `NaN` 直接编译错 |

### 正解流程（一分钟）

1. **EEZ GUI 新建该控件**（如拖一个按钮）；
2. **看它的默认 JSON**（另存 .eez-project 后读，或查 asar 内 `defaultValue`）；
3. **照抄默认结构，只改 text / left / top / 样式值**；
4. 交付前跑静态自检（`check_project.py`：引用审计/字体条目/字符集 ⊆ cmap）。

### 正确示例：按钮文字居中（EEZ 原生默认形态，只改文字）

```json
{ "type": "LVGLButtonWidget", ..., "children": [{
    "type": "LVGLLabelWidget",
    "left": 0, "top": 0,
    "width": 80, "height": 32,
    "widthUnit": "content", "heightUnit": "content",   ← 自适应文字（必填！）
    "text": "连  接", "textType": "literal",
    "localStyles": { "definition": { "MAIN": { "DEFAULT": {
        "align": "CENTER",                              ← widget 对齐，画布原生渲染
        "text_color": "0xFFFFFF", "text_font": "cn14" } } } }
}]}
```
生成码 = `set_size(LV_SIZE_CONTENT, LV_SIZE_CONTENT)` +
`set_style_align(LV_ALIGN_CENTER)`——画布/真机同源渲染。

### 相关陷阱速查

- **widget `align` 与显式 left/top 定位互斥**（LVGL align 覆盖 x/y 语义）——
  定宽铺满的整行 label 用 `text_align:"CENTER"` 做水平居中，**不要加
  widget align**；
- **`lv_obj_get_x` 返回父容器相对偏移**，当屏幕坐标用会得出假偏移；
- label 文字**从盒顶绘制**——垂直居中 = label 高收缩到文字高（14px）+
  y 定位到行中心；
- 完整复盘（15+5 坑、对照实验）见 `intake/P-0163`、`P-0164`。
