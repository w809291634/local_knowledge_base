# UI 自动设计 + 对照查验 + 仿真验证 技能

> 一份把「写 UI」变成「可验证的工程流程」的操作手册。
> 目标：**不靠肉眼巡检，也能稳定产出可用的 UI**。
> 来源：EEZ Studio v3 + LVGL 9.4 + ESP32-S3（320×240 SPI 屏）项目实战，
> 其中每一条规则都对应一个**真实出过并复现过**的缺陷。

---

## 0. 这个技能解决什么

UI 开发最容易陷入的循环是：改一版 → 烧录 → 发现点不动/跳错 → 再改 → 再烧。
一次烧录几分钟，一天只能试十几次，而且「点了没反应」这类问题在真机上几乎无法定位。

本技能把它拆成三件事：

| 阶段 | 做什么 | 耗时 | 拦住什么 |
|---|---|---|---|
| **A 自动设计** | 一个 Python 脚本产出全部界面（DSL），效果图和固件代码同源 | 一次 | 「效果图好看、上机不一样」 |
| **B 对照查验** | 秒级静态体检，把踩过的坑变成断言 | 秒 | 坐标偏移、字体回退、点击被遮挡、真机编译失败 |
| **C 仿真验证** | PC 模拟器跑真 LVGL + 真生成代码，程序注入真鼠标事件 | 分 | 「点了跳错页」「点了没反应」 |

**核心原则：唯一设计源。** 界面只在一处定义（DSL 构建脚本），效果图、EEZ 工程、
固件 C 代码全部由它派生。绝不手写第二套实现。

---

## 1. 开工前：确认 4 件事

### 1.1 必须向用户询问的两项

> **⚠️ 执行本技能时，如果下面两项未知，必须先问用户，不要猜。**

1. **仿真器（PC Simulator）工程路径**
   —— 阶段 C 要用它编译出可执行程序。不同机器位置不同，**运行时询问**：

   > 「仿真器工程在哪个目录？（就是带 `CMakeLists.txt` + `lv_sdl_window_create` 的那个
   > LVGL PC 模拟器工程，例如 `.../common/PC_SIM/lv_port_pc_vscode_v9.5`）」

   拿到后确认三件事存在：
   - `<仿真器>/CMakeLists.txt` 里有 `lv_sdl_window_create` / SDL2 依赖
   - `<仿真器>/lv_conf.h` 里 `LV_USE_SDL 1`
   - 构建工具链（见 1.2）

2. **UI 工程路径**（EEZ 工程所在目录），本例为
   `.../Template/spilcd_spiopt_eez_lv_port_pc_tem_atks3/main/test`

### 1.2 环境自检（本机不需要联网安装）

```
LVGL 源码   从固件的 build/compile_commands.json 里 grep lv_obj.c 挖出真实路径
编译器      mingw64 gcc/g++（问用户：通常在 D:\Program_Files\mingw64）
CMake       cmake -G "MinGW Makefiles"
SDL2        <仿真器>/setup_env.bat 里记录了路径
```

### 1.3 版本必须对齐（最容易踩的坑）

**模拟器默认的 LVGL 版本 ≠ UI 生成时的版本**时，会出现一堆莫名的编译错误。
先确认：EEZ 是按哪个 LVGL 版本生成代码的（`src/ui/screens.c` 里用的 API），
然后把 `CMakeLists.txt` 的 LVGL 目录指向**同版本**源码。

### 1.4 不要污染用户仓库

编译产物**不要**放在工程目录内（会让 git 一片红）。拷到桌面或临时目录再编译，
并把 CMakeLists 里的相对路径（`${PROJECT_SOURCE_DIR}/../../...`）改成绝对路径。

---

## 2. 四层门禁总览

```
DSL 构建脚本  ──►  ui_voice.json  ──►  EEZ 工程  ──►  screens.c  ──►  固件
                        │                  │              │
        L1 静态体检 ◄────┘                  │              │
        L2 真点击（仿真器）◄────────────────────────────────┘
        L3 真机烧录
```

| 层 | 命令 | 拦什么 | 何时跑 |
|---|---|---|---|
| **L1** | `python ui_debug_kit/tools/run_gate.py` | 静态可查的一切 | 每次改完设计源 |
| **L2** | 见 §5 | 真点击行为 | 提 PR 前 / 发版前 |
| **L3** | `idf.py build flash` | 硬件相关 | 发版 |

---

## 3. 阶段 A：UI 自动设计

### 3.1 结构约定

```
<工程>/main/test/
  design/
    build_voice_ui.py    ★ 唯一设计源（所有页面的构造函数）
    ui_voice.json          中间产物：人类可读 DSL
    json2eez.py            DSL -> EEZ 工程
    eez_build.py           EEZ headless 构建 -> src/ui/screens.c
    gen_fonts.py           重新生成字体 C（EEZ 构建会删掉它们）
    dsl2png.py             效果图
    check_nav.py           跳转体检（由配置挂到门禁 G2）
  ui_debug_kit/            可移植调试工具箱（本文件所在目录）
    INTAKE.md              记录规约（新问题 / 提示词怎么留痕）
    intake/                问题流水（P-####_*.md + index.md）
    prompts/               提示词日志（PROMPT_LOG.md，PR-####）
    tools/
      log_entry.py         ★ 记录写入器（新问题 / 提示词，任何 AI 工具可调）
      run_gate.py          ★ 一键门禁
      audit_ui.py          回归断言集 A1~A10
      gen_clicks.py        自动生成真点击用例
      tree_check.py        通用静态体检
  ui_debug_kit.config.json 工程侧配置（唯一需要填工程信息的地方）
  src/ui/                  EEZ 生成的 C 代码（编译进固件）
```

### 3.2 全链路（顺序不能乱）

```bash
python design/build_voice_ui.py          # 1. 生成 DSL
python design/json2eez.py --dsl ui_voice.json   # 2. 编译进 EEZ 工程
python design/eez_build.py               # 3. 生成 screens.c（headless CLI 不烘焙字体，
                                         #    还会把上次清单里的 ui_font_*.c 当 orphan 删）
python design/gen_fonts.py               # 4. 补生成字体 C（必须紧跟第 3 步）
python ui_debug_kit/tools/run_gate.py    # 5. 门禁
```

### 3.3 写设计源时的硬规则

**坐标**：DSL 写绝对坐标，但 EEZ 子控件是相对父对象的，转换脚本必须做
`to_relative()` 换算。漏了的话，嵌套容器里的子控件会二次偏移跑出屏幕。

换算的**精确式子**（对照本机 LVGL 9.4 的 `src/core/lv_obj_pos.c::lv_obj_move_to`）：

```
子绝对 = 父->coords.x1  +  子声明坐标  −  父->scroll_x
```

两个容易搞错的点：

- `coords.x1` 是父的**边框盒**左上角 —— **border 与 padding 都不参与**，
  换算就是单纯的 `子绝对 − 父绝对`，不用再去减内边距；
- **父的滚动量会叠加**：容器默认带 `SCROLLABLE`，子控件一旦溢出就会把父撑出
  滚动区，滚动量把所有子控件一起带偏。所以配套要做两件事：
  ① 容器/按钮去掉 `SCROLLABLE`；② 保证子控件不超出父范围。

**子控件超出父范围会被裁掉**（画了但看不见），所以生成端要有一条
「子控件必须在父的矩形内」的校验：相对坐标为负、右/下边缘越界都直接报错。
实测这条校验一次就抓出 4 类真实问题（电池电极在主体之外、气泡头像超出、
滑块的圆点比轨道高被削平、分区指示条贴在栏外）。

**取舍：平铺 vs 分层。** 也有一种走法是**彻底不做换算**：把全部后代提升成
页根的直接子节点（平铺），式子退化成 `渲染坐标 = 声明坐标`。
它确实能消掉偏移，但代价是**父子语义、相对布局、成组移动全部丢失**
（组件树退化成几百个平级节点，编辑器里没法把一张卡片整体挪走）。
**两者都能跑通，推荐分层 + 换算**：语义正确、可维护，且换算规则已经明确到
一个式子；只有在框架不支持嵌套、或排障对比时才用平铺。

**Button 必须清零内边距**：LVGL 默认主题给 Button 加内边距，子控件整体偏移
**(+14, +9)**；Container 没有这个问题。凡是 `type="button"`，样式里必须显式写
`pad_top/pad_bottom/pad_left/pad_right = "0"`。

**字体**：
- 中文与图标各一份，`text_font` 必须与 `fonts[].name` **完全一致**（对不上会静默回退 14px）
- 中文码位进 `lvglRanges`；FontAwesome 私有区（U+E000..F8FF）进 `lvglSymbols`
- 扩展字体前先 `ensure_extra_fonts`，再 `extend_font_ranges`
- 布局宽度按**真实渲染字号**算（`content` 宽），不要拍脑袋

**不要用「固定宽 + text_align」做居中/右对齐**：EEZ 保存工程时会按它自己的字宽
重算 `left`，会算出负数，文字跑出画布。一律用 `content` 宽度 + 按真实文本宽度算出的 x。

**装饰元素关闭点击**：叠在按钮之上的纯装饰容器（圆环、圆底、分隔线）必须
`clickable=False`，否则它会把自己覆盖区域内的点击全部吃掉。

**Tab 栏当前页不生成按钮**：`active` 只表示「高亮哪个图标」，不等于「当前是哪一屏」。
必须显式传当前页名，按页名判断——否则二级页（带 Tab 栏但当前页不是那个 Tab）的
正常跳转会被误删，或者点当前 Tab 触发 changeScreen 到自己造成闪屏。

---

## 4. 阶段 B：对照查验

### 4.1 一键门禁

```bash
python ui_debug_kit/tools/run_gate.py            # 全跑
python ui_debug_kit/tools/run_gate.py --quick    # 只跑 G1 + 配置里标 quick 的项
```

| 组 | 脚本 | 查什么 |
|---|---|---|
| G1 | `ui_debug_kit/tools/audit_ui.py` | 回归断言 A1~A10（见 §6.2） |
| G2 | `design/check_nav.py`（配置挂载） | 跳转三要素、死链、跳自己、可达性、死胡同（**本工程未挂载：脚本未写、config.gates 无此条，当前跳转仅由 A8+G4 覆盖**） |
| G4 | `ui_debug_kit/tools/tree_check.py` | 几何越界、文本折行、字体缺失、墨迹异常 |
| G5 | `design/compare.py`（配置挂载） | 设计稿 vs 实机逐屏对照：缺屏或平均差异超阈值即阻断 |

G2/G5 是**本工程专属**脚本，留在 `design/`，由 `ui_debug_kit.config.json` 的
`checks.gates` 挂进门禁 —— 工具箱本身保持零工程痕迹。脚本不存在会被 SKIP 而非报错。

退出码非 0 即为阻断，可直接挂到 git pre-commit。

### 4.2 数量对账法（改完必做）

跳转数在三层必须一致：

```
DSL 里的 goto 数 == EEZ 的 connectionLines 数 == screens.c 的 lv_obj_add_event_cb 数
```

**变化时必须对得上账**。例：52 − 5（Tab 跳自己）− 1（错误 goto）= 46，
实测 46 说明没误删有效跳转；对不上就是改坏了。这项已固化成断言 A8。

### 4.3 出图对照

```bash
python design/dsl2png.py                  # 设计源直出效果图
node design/eez_pages.js <输出目录> <页面>  # 抓 EEZ 原生渲染图（真 LVGL 渲染）
```

后者需要带调试端口启动 EEZ Studio：
`--remote-debugging-port=9222 --no-sandbox --disable-gpu --enable-unsafe-swiftshader
--disable-dev-shm-usage`（不能加 `--disable-software-rasterizer`）。
**注意：EEZ 编辑器画布不能用来做点击测试**（见 §7.1），它只适合出图对照。

---

## 5. 阶段 C：仿真器真点击

### 5.1 为什么必须有这一层

L1 是「算」出来的，能抓几何与结构问题，但抓不到**真实运行时行为**。
真点击用的是**真 LVGL 运行时 + 真生成的 C 代码 + 真 SDL 鼠标事件**，
与真机的差别只有没有物理屏和触摸芯片。

### 5.2 搭建步骤

1. **拷仿真器工程到桌面/临时目录**（不要拷进用户仓库）
2. 拷 EEZ 生成的 UI 源码到 `<仿真器>/eesrc/`：`src/ui/*.c *.cpp *.h`
3. 改 `CMakeLists.txt`：
   - LVGL 目录指向**与 UI 同版本**的源码（绝对路径）
   - UI 源文件 glob 改为 `eesrc/*.c` 和 `eesrc/*.cpp`（`eez-flow.cpp` 必须编进去）
   - include 目录指向 `eesrc`
4. 改 `main.c`：分辨率改成实际屏（320×240）、入口换成 EEZ 的 `ui_init()`、
   主循环**必须同时**调 `lv_timer_handler()` 和 `ui_tick()`
5. 编译

### 5.3 三个必踩的编译坑

| 现象 | 原因 | 处理 |
|---|---|---|
| ThorVG 报缺 `config.h` | LVGL 的 CMake 是给 ESP-IDF 写的 | 关掉：`-DCONFIG_LV_USE_THORVG_INTERNAL=0 -DCONFIG_LV_BUILD_EXAMPLES=0 -DCONFIG_LV_BUILD_DEMOS=0`，同时关 `LV_USE_LOTTIE` |
| 报 `lv_font_montserrat_8/10 undeclared` | `lv_conf.h` 没开对应字体 | 开成 1；**同时检查工程侧的 `lv_conf.h`**，否则真机也会炸（断言 A6 就是查这个） |
| Permission denied / 锁文件 | 之前 kill 掉的进程留了锁 | 换一个干净的构建目录（`-B build2`） |

### 5.4 跑测试

```bash
python ui_debug_kit/tools/gen_clicks.py -o <仿真器>/clicks.txt    # 生成全量用例
<仿真器>/bin/main.exe <仿真器>/clicks.txt               # 执行
```

用例格式：每行 `x y 期望页面名`，输出 `click(x,y) 前 -> 后 expect=xx OK/FAIL`。

`gen_clicks.py` 会从设计源推导**每一个可达按钮**（含导航路径），并列出不可达的屏——
那些屏说明还没配入口，需要回到设计源补 `goto`。

### 5.5 main.c 的两个关键点

- **不能 `#include "ui.h"`**（会引入 C++ 头 `eez-flow.h` 导致编译失败），
  用 `extern void ui_init(void); extern void ui_tick(void);` 显式声明
- **判断当前在哪一屏**：对比 `lv_screen_active()` 与 `screens.h` 里 `objects`
  结构体的各页指针（`screens.h` 是 C 安全的，可以直接 include）

---

### 5.6 零点击出图：逐屏快照（把 L2 做成可自动跑的截图流水线）

真点击用来验「点下去会怎样」；**出图**只需要「每屏长什么样」。
后者可以完全不用鼠标：在仿真器里逐屏 `load → 跑几帧 → 快照 → 写裸帧`。

```
main.exe <输出目录>          # 出图模式；不带参数则开窗口交互
  for 每一屏:
      lv_screen_load(obj)
      for i in 1..25: lv_timer_handler(); ui_tick(); usleep(4ms)
      db = lv_snapshot_take(lv_screen_active(), LV_COLOR_FORMAT_ARGB8888)
      写 "<w> <h> <stride> <cf>\n" + db->data 到 <name>.raw
  _exit(0)                   # 关键：SDL 收尾有时不返回，不退出会挂死脚本
```

四个必踩点（详见 `cases/B8`）：

| 点 | 处理 |
|---|---|
| 快照字节序 | ARGB8888 在小端下内存序是 **B,G,R,A**，读取端要按 `c2,c1,c0` 重排成 RGB |
| 快照内存 | `w×h×4` 要一整块连续内存；内置静态堆常只有 1MB → 仿真器换 CRT 堆 |
| 进程不退 | 出图模式结尾 `_exit(0)`；调用端以「产物文件齐全」判定成功，别等退出码 |
| 配置不生效 | 构建系统读的配置路径可能 ≠ 命令行传的变量，两份都要写，并在日志里确认生效 |

配套：**UI 源码与渲染引擎分开增量编译**（引擎全量几十分钟，UI 增量几十秒）；
仿真器工程**拷到临时目录**再改，不污染用户仓库。

产物用同一个对照脚本与设计稿逐屏比（切块差异 + 三联图：设计 / 实机 / 差异热力图），
差异稳定的残留项就是"框架画不出来的东西"（渐变角度、阴影、发光、自绘图标），
写进工程侧的「已知差异」清单，而不是每次重新排查。

---

## 6. UI 测试条例

> 按这套条例执行，即可稳定产出可用 UI。分三段：
> **D = 设计期**（写代码时遵守），**G = 门禁**（改完必跑），**R = 发布前**（真机）。

### 6.1 D 段：设计期条例（写设计源时遵守）

| 编号 | 条例 | 违反后果 |
|---|---|---|
| D1 | 界面只在构建脚本里定义，效果图/EEZ/固件代码全部由它派生 | 两套实现必然漂移 |
| D2 | 子控件坐标必须做「绝对 → 相对父对象」换算 | 嵌套容器子控件二次偏移跑出屏 |
| D3 | `type="button"` 必须显式 `pad_*=0` | 子控件整体偏移 (+14,+9) |
| D4 | `text_font` 必须与 `fonts[].name` 完全一致 | 静默回退 14px，大标题变小 |
| D5 | 中文进 `lvglRanges`，FontAwesome 进 `lvglSymbols` | 缺字/豆腐块 |
| D6 | 禁止「固定宽 + text_align 居中/右对齐」，用 `content` 宽 + 算 x | EEZ 保存后 left 变负数，文字跑出画布 |
| D7 | 叠在按钮上的装饰容器必须 `clickable=False` | 按钮中心点不动 |
| D8 | Tab 栏当前页不生成跳转按钮（按页名判断，不要用 index） | 点当前 Tab 闪屏；二级页的正常跳转被误删 |
| D9 | 元素不得压进 Tab 栏区域（y ≥ 204） | 点列表行实际命中 Tab，莫名跳错页 |
| D10 | 每个二级页都要有返回/出口，每个入口卡片都要配 `goto` | 死胡同 / 页面永远点不到 |
| D11 | **每个控件都要有唯一且短的 identifier**（格式 `<页缩写>_<自身 token>`，不拼父链） | codegen 一律叫 `obj38` —— 出问题没法指名道姓；名字还不能与**页面名**（EEZ 里页面也占一个 `objects.<页名>`）重名 |

### 6.2 G 段：门禁条例（改完必跑，任一 FAIL 不得提交）

```bash
python ui_debug_kit/tools/run_gate.py
```

| 编号 | 断言 | 检查内容 | 判定 |
|---|---|---|---|
| G1-A1 | 字体名一致性 | DSL 字体名 ⊆ EEZ `fonts[]` ∪ 内置字体 | 无未知字体 |
| G1-A2 | 字体基线 | EEZ `ascent` == 字体 C 的 `line_height - base_line` | 一致（不一致只 WARN，仅影响预览） |
| G1-A3 | 主题内边距 | 会吃主题偏移的类型（`theme_defaults` 里 dx/dy 非 0 的）4 个 `pad_*` 均为 `"0"` | 全部为 0 |
| G1-A4 | 文本对齐 | 无「固定宽 + text_align=CENTER/RIGHT」的 label | 0 处 |
| G1-A5 | 底栏侵占 | 带底栏的页无非底栏元素压进底栏区（本工程 y ≥ 204） | 0 处重叠 |
| G1-A6 | 字体开关 | `screens.c` 引用的 `lv_font_*` 在 `lv_conf.h` 中均为 1 | 0 种未开启 |
| G1-A7 | 当前页标记 | `tabbar(active, cur=X)` 的 X 等于所在页页名 | 全部一致 |
| G1-A8 | 链路忠实性 | DSL goto 数 == EEZ 连线数 == `screens.c` 回调数 | 三者相等 |
| G1-A9 | 部件开关 | `screens.c` 里 `lv_*_create()` 用到的部件，在 `lv_conf.h` 中开关均为 1 | 0 种被关闭 |
| G1-A10 | 样式值语法 | 颜色类样式值必须形如 `0xRRGGBB`（`checks.color_props` / `color_node_keys` 可配） | 0 处不合法 |
| G2 | 跳转体检 | 三要素完整 / 无死链 / 无跳自己 / 可达性 / 死胡同（**本工程未挂载**，暂由 A8+G4 覆盖） | 无 ERROR |
| G4 | 通用体检 | 几何越界 / 文本折行 / 字体缺失 / 墨迹异常 | 全部通过 |

### 6.3 R 段：发布前条例（真机）

| 编号 | 条例 | 说明 |
|---|---|---|
| R1 | 全量真点击通过 | L2 跑出的报告 0 FAIL |
| R2 | 真机编译通过 | 特别注意 A6 那类「本地能跑、上机炸」的字体开关 |
| R3 | 固件周期调用 `ui_tick()` | 不调的话 EEZ flow 动作只入队不执行，**表现为按钮点了没反应** |
| R4 | 启动页加载正确 | `ui_init()` → `create_screens()` → `lv_screen_load(objects.main)` |

---

## 7. 已知陷阱（血泪清单）

### 7.1 EEZ Studio 编辑器里点不了，别浪费时间

实测结论：EEZ 画布**一个事件监听器都没有**（`DOMDebugger.getEventListeners` 返回空，
inline `on*` 也是空）。挡住它的是 EEZ 给每个组件套的透明外壳
`div.EezStudio_ComponentEnclosure`，点击被拿去做「选中组件」。
CDP 鼠标事件、直接派发 PointerEvent、窗口置顶——三种注入方式全部无效。
**画布只是渲染预览，真点击只能靠仿真器或真机。**

### 7.2 「点了画面来回跳」的三类成因

1. 元素压进 Tab 栏 → 点它实际命中 Tab 按钮（D9 / A5）
2. Tab 当前页会 changeScreen 到自己 → 整屏 MOVE_LEFT 重载（D8 / A7）
3. 一个 source 挂了多条连线 → 一次点击触发多个切屏

### 7.3 「点了没反应」的三类成因

1. 装饰容器盖在按钮上且可点击（D7）
2. label 带了 `clickableFlag`，抢走按钮的点击目标
3. 固件没周期调 `ui_tick()`（R3）

### 7.4 「本地能跑、上机炸」

`lv_conf.h` 有两份：仿真器一份、工程一份。仿真器补开的字体开关**不会**同步到工程侧。
断言 A6 专查这一项。

### 7.5 出图与渲染不一致

EEZ 编辑器按自己的 `ascent` 画字，与固件里烘焙字体的真实基线可能差 2px。
用实测值（`line_height - base_line`）做基准，配置里的值不要盲信。

### 7.6 固件链接报 `undefined reference to get_var_*`（见 intake/P-0020）

三层坑，缺一层都过不去：

1. **EEZ 只生成 `src/ui/vars.h`（extern 声明），从不生成 `vars.cpp`。**
   那 20 个 `get_var_*/set_var_*` 的唯一定义在 `native/native_vars.cpp` 里，
   不存在"和 EEZ 生成的重复"。所以这个 **必须** 编进固件。
2. **`src/native/CMakeLists.txt` 必须是真正的 IDF 组件**（有 `idf_component_register`）。
   只 `set(NATIVE_SRCS ... PARENT_SCOPE)` 等别人 include 是不够的——目录虽在
   `EXTRA_COMPONENT_DIRS` 里，没注册的组件会被直接跳过，一个 .cpp 都不会编。
3. **必须显式建立 ui → native 的链接依赖**，否则 CMake 的库顺序会出问题：
   `ui.c.obj` 是被 `main` 拉进来的，而 `main` 排在 ui 后面，ld 到**第二次**出现
   `libui.a` 时才提取 `ui.c.obj`，此时 `libnative.a` 已经扫过去了。
   ```cmake
   # 工程顶层 CMakeLists.txt，project() 之后
   cmake_policy(SET CMP0079 NEW)    # 跨目录改别人的 target 必须开
   idf_component_get_property(ui_lib ui COMPONENT_LIB)
   idf_component_get_property(native_lib native COMPONENT_LIB)
   target_link_libraries(${ui_lib} PUBLIC ${native_lib})
   ```
   不能写在 `ui/CMakeLists.txt`（EEZ 每次导出会重写），也不能写在
   `native/CMakeLists.txt`（那是反方向，会造成 ui ↔ native 循环）。
   native 需要 ui 的头文件时，用 `INCLUDE_DIRS ../ui`，别用 `REQUIRES ui`。

**另一个连带坑：`main` 组件一旦显式写 `REQUIRES/PRIV_REQUIRES`，就丢掉了
"默认依赖全部组件"的 IDF 特例。** 只写 `ui native` 会让 `bsp/esp-bsp.h`、
`board.h`、`lv_demos.h` 全部找不到，必须把 main.c 用到的组件列全。

**排查手法**：链接报 undefined 时先双向 `nm` 比对确认符号真的存在
（`nm -u libui.a` vs `nm -g libnative.a`），再去
`build/CMakeFiles/<elf>.rsp` 看**最后一次出现**的库相对顺序——只看第一次会误判。

### 7.7 静态库链接顺序：通用解法（get_var_* 与 lv_mem_psram 同一坑）
> **现象**：`undefined reference to <符号>`（链接期）。
> **什么情况**：符号定义在组件 B（.cpp/.c），被组件 A 引用；但 `libb.a` 排在 `liba.a`
> 被抽取**之前**，ld 单遍扫描时把 B 里那个 .o 整段跳过。
> **怎么写**：让 A 显式依赖 B，拓扑排序把 `libb.a` 排到 `liba.a` 之后，实现即被抽到。

```cmake
cmake_policy(SET CMP0079 NEW)            # 跨目录改别人 target 必须开
idf_component_get_property(a_lib <A>   COMPONENT_LIB)
idf_component_get_property(b_lib <B>   COMPONENT_LIB)
target_link_libraries(${a_lib} PUBLIC ${b_lib})
```
- **写哪里**：工程顶层 `CMakeLists.txt`、`project()` 之后。不能写进被 EEZ 重写的
  `ui/CMakeLists.txt`，也不能写反方向（会造成循环依赖）。
- **实例 1 — `ui → native`**：见 §7.6。EEZ 只生成 `vars.h` 声明，`get/set_var_*` 唯一定义在 `native/native_vars.cpp`。
- **实例 2 — `lvgl → lv_mem_psram`**：`lv_mem_psram` 提供 LVGL 内存 core 的 PSRAM 实现
  （`lv_malloc_core`/`lv_mem_init` 等），LVGL 默认内置实现未编入。**`lvgl` 是托管组件，
  注册名 `lvgl__lvgl`**（库目标 `__idf_lvgl__lvgl`），写 `lvgl` 会报 `Failed to resolve component 'lvgl'`。
- **备选**：`--undefined=<符号>` 强抽（顺序无关）也行，但要背符号名；本项目两处统一用上面的排序法。

---

## 8. 命令速查

```bash
# 改完设计源后的标准动作（本工程的“一条命令”版本在 design/all.py）
python design/build_voice_ui.py
python design/json2eez.py --dsl ui_voice.json
python design/eez_build.py
python design/gen_fonts.py
python ui_debug_kit/tools/run_gate.py

# 只在工程侧 design/ 里的一条龙（含仿真器出图与对照）
python design/all.py            # DSL -> 工程 -> C 代码 -> 字体
python design/all.py --shots    # 再：仿真器增量重编 + 11 屏出图 + 对照报告
python design/sim.py --ui-only  # 只换 UI 源码增量重编（引擎已编好）

# 单独跑某项
python ui_debug_kit/tools/audit_ui.py            # 回归断言（可加 A3 A6 只跑指定项）
python ui_debug_kit/tools/audit_ui.py A10        # 只看样式值语法
python design/check_nav.py                       # 跳转体检（**本工程暂缺此脚本**，run_gate 会 SKIP；G2 仍缺）

# 真点击
python ui_debug_kit/tools/gen_clicks.py -o <仿真器>/clicks.txt
<仿真器>/bin/main.exe <仿真器>/clicks.txt

# 留痕（每轮都做，见 §10 / INTAKE.md）
python ui_debug_kit/tools/log_entry.py prompt "用户原始提示词" --tool <AI名>
python ui_debug_kit/tools/log_entry.py problem --title "<标题>" --symptom "…" --root "…" --fix "…"
python ui_debug_kit/tools/log_entry.py list
```

---

## 9. 迁移到新项目

这份技能里**与具体项目无关的**部分是 §0、§2、§5、§6、§7——可以直接复用。
需要按新项目改的只有**一份配置文件** `ui_debug_kit.config.json`（模板在
`ui_debug_kit/config.template.json`，字段说明见 `CONFIG.md`）：

1. `project.*` / `paths.*`：设计源、目标工程、生成代码、运行时字体配置的位置
2. `tree_schema`：字段名与类型取值映射（换框架只改这里）
3. `checks.tab_bar`：底栏识别规则（有底栏才需要；各项对应页名会自动推导）
4. `checks.gates`：把新项目自己的检查脚本挂进门禁
5. 新增断言：把新项目踩到的坑按 A1~A10 的格式加进 `audit_ui.py` 的 `CHECKS` 字典

三个脚本（`audit_ui.py` / `gen_clicks.py` / `run_gate.py`）**内部不含任何工程信息**，
迁移时不用改它们。缺哪份输入，对应断言就自动跳过并打印"跳过"。

**记录区随项目累积**：`intake/`（问题流水）、`prompts/`（提示词日志）、`skills.md`（本手册）
在换新工程时**保留**，靠每条记录里的 `工程` 字段区分。

**每踩一个新坑，就加一条断言**——这是这套体系唯一但最重要的维护动作。

---

## 10. 记录：把新问题与提示词写回技能（必做）

> **完整规约在 `INTAKE.md`**。任何 AI 工具（WorkBuddy / Cursor / ChatGPT / 人）都应遵守。
> 目的是：以后再用这套技能开发时，**新问题能沉淀进来、用户原话能留痕**，方便日后追查。

| 发生什么 | 写到哪 | 编号 |
|---|---|---|
| 遇到**新问题**（报错 / 表现异常 / 踩坑） | `intake/P-####_*.md` + `intake/index.md` 一行 | `P-0001`… |
| 用户给出**一条提示词**（每次输入） | `prompts/PROMPT_LOG.md` 追加一段 | `PR-0001`… |

```bash
python ui_debug_kit/tools/log_entry.py prompt "用户原始提示词" --tool <AI名> --link P-0001
python ui_debug_kit/tools/log_entry.py problem --title "<标题>" \
    --symptom "…" --root "…" --fix "…" --evidence "…"
python ui_debug_kit/tools/log_entry.py list
```

三条纪律：

1. **只追加，不改历史**；判断被推翻时补写"为什么当初误判"，不要删旧条目。
2. **提示词逐字抄**，不改写 / 不润色 —— 用户原话是**不可再生**的信息。
3. 问题必须带**可复现证据**（坐标 / 命令 / 前后对比数字），不要写"报错了、修好了"。

闭环：`intake/`（原始流水）→ 搞懂且可推广后按 `cases/README.md` 提炼进 `cases/` →
若本可被断言拦住，就加进 `tools/audit_ui.py` 的 `CHECKS`。
三步叠加，技能才会**越用越强**。

---

## 11. 实测补充（2026-09，EEZ Studio 1.22.10 / 800×480 / LVGL 9.4）

> 一次「按设计稿生成 11 屏」的实战里新踩出来的坑，都带可复现证据，
> 流水见 `intake/P-0005` ~ `P-0010`；已提炼成案例：
> [`B5 子控件二次偏移`](cases/B5_子控件二次偏移（嵌套容器）.md)、
> [`B6 样式值写错语法被静默吞掉`](cases/B6_样式值写错语法被静默吞掉.md)、
> [`B7 构建成功却零产出`](cases/B7_构建成功却零产出.md)、
> [`B8 仿真器出图的四个坑`](cases/B8_仿真器出图的四个坑.md)。

### 11.1 EEZ CLI build 的四个坑

| 现象 | 根因 | 处理 |
|---|---|---|
| 报「No error and no warning detected / Build successfully finished」但**零产出** | `settings.build.files` 是 12 个产出文件（screens.c/ui.c/fonts.h…）的模板表，被删掉了 | 该字段**不能动**；恢复后日志会多出 `Configuration: Default` 与 12 行 `File "…/screens.c" built` |
| build 结束后**进程不退出**，脚本挂到超时 | 只有收到 `on-build-project-message(undefined)` 才 `app.quit()` | 用 `Popen` + 轮询日志里的 `Build successfully finished`，拿到后 `terminate()` + `taskkill /F /IM` |
| `bad option: --build-project` | 环境里 `ELECTRON_RUN_AS_NODE=1`，Electron 退化成 Node | `env.pop("ELECTRON_RUN_AS_NODE")` |
| GPU 进程反复崩 | headless 起不来 GPU | `--no-sandbox --disable-gpu --enable-unsafe-swiftshader`（**不要**加 `--disable-software-rasterizer`） |

### 11.2 布局：平铺 > 相对换算

`D2` 说的是「子控件坐标要做绝对→相对换算」。更省事的做法是**干脆不嵌套**：
在转换脚本里把全部后代提升成 screen 的直接子节点（先序 = 原绘制顺序），
既不用换算，也不受父容器 padding/border 影响。配合给**所有容器显式 `pad_*=0`**
（LVGL 子控件坐标是相对父对象内容区，默认主题的容器内边距会让所有子控件整体偏移）。

实测：同一份 DSL，保留嵌套时卡片里只剩一条滚动条、文字全部跑到卡片外；
平铺后与设计稿结构一致。

### 11.3 样式细节

- **颜色值必须是 `"0xRRGGBB"` 字符串**。`bg = 0x2a3044`（少写引号）在 Python 里是
  `int 2764868`，序列化后变成 `"2764868"` —— EEZ 打开工程时在树上报 **invalid color**
  （`ColorFormat.parse` 认不出 → `formatType=UNKNOWN` → `isValid()=false`），
  但**CLI build 依然报 "No error and no warning detected"**，只有 GUI 里看得见。
  → `json2eez.check_colors()` 在生成阶段直接抛错拦住（已内置）。
- **`text_font` 必须能在工程 `fonts[]` 或内置字体里找到**：找不到 EEZ 不报错，
  codegen 静默回退（表现是「大标题突然变小」）→ `json2eez.check_fonts()` 拦住。
- **开关**要同时写 `DEFAULT` 与 `CHECKED` 两个状态：默认主题对 CHECKED 单独定义了
  各 part 的样式，只写 DEFAULT 会被盖住 —— 表现是「开关暗的，只有白圆点在右边」。
- **图标宽度必须用图标字体量**：`Pillow` 拿主 TTF 量 FontAwesome 私有区码位会退回
  `.notdef`（宽度恒定 10px，与字号无关），算出来的胶囊宽度全错、右侧内容被挤出画面。
  正确做法：`ImageFont.truetype(FA_WOFF, size)`。
- EEZ 样式表**没有 `border_side`**，画不出「只描右边」的边框 —— 分隔线用 1px 装饰容器代替。
- 容器默认 `SCROLLABLE`，`flagScrollbarMode` 建议写 `"OFF"`。
- 拼装顺序即绘制顺序（z 序）：父/底先、子/上后；装饰容器一律 `clickable=False`。

### 11.3.1 判定「构建真的失败了吗」

CLI 日志里会混进 Chromium 自己的噪音：
`[27612:0923/185626.983:ERROR:net\disk_cache\cache_util_win.cc:25] Unable to move the cache`。
按 `^\[\d+:\d{4}/\d+:\d+:\d+\.\d+:(ERROR|WARNING|INFO):` 过滤掉再统计，
否则会把「9 条 error」当成构建失败（实际项目零错误）。

### 11.4 仿真器出图（把 L2 变成可自动跑的截图流水线）

- 拷一份仿真器到临时目录改，**不污染仓库**；改 `CMakeLists.txt` 的 `UI_DIR`、
  `APL_LVGL_DIR`（版本必须与工程 `lvglVersion` 一致）、`SIM_H_RES/V_RES`；
  链接行里的 `lvgl::thorvg` 要摘掉（配合 `-DCONFIG_LV_USE_THORVG_INTERNAL=0`）。
- `os_desktop.cmake` 读的是 `${CMAKE_SOURCE_DIR}/lv_conf.h`，**不是** CMakeLists 里的
  `LV_CONF_PATH` —— 两份都要写，否则改的那份被静默忽略。
- 快照 800×480×4 = 1.5MB 连续内存，LVGL 自带 `LV_MEM_SIZE` 常只有 1MB，会报
  `lv_draw_buf_create_ex: No memory` → 仿真器把 `LV_USE_STDLIB_MALLOC` 换成 `LV_STDLIB_CLIB`。
- 快照 `LV_COLOR_FORMAT_ARGB8888` 在**内存里是 B,G,R,A**（小端 `lv_color32_t`）：
  Python 侧 `frombytes("RGBA").split()` 后要按 `(c2, c1, c0)` 重排才是真 RGB。
- 出图模式：`main.exe <输出目录>` → 逐屏 `lv_screen_load` + 跑几帧 + `lv_snapshot_take`
  写裸帧；**结尾用 `_exit(0)`**，SDL 收尾有时不返回，会让脚本挂死。
- 增量：UI 源码变了但 LVGL 没变时，只重新拷贝 `lv_ui/` 再 `make`（几十秒），
  不要重头编 LVGL（约 8 分钟）。
- Windows 上 `subprocess` 用**父进程** PATH 找 exe，`mingw32-make` 之类不在 PATH 时要给绝对路径。
- **mingw64 的 bin 必须在 PATH 里**：缺了它 `gcc` 会**静默失败**（rc=1 且一条输出都没有，
  连 `bad.c` 这种明显错误都不报），极易误判成「编译器坏了」。
  排查编译问题第一步：`export PATH="/d/Program_Files/mingw64/bin:$PATH"` 再跑（`intake/P-0013`）。

### 11.5 按 id 收集/匹配必须用 prefix_ids 之后的最终 id

`build_ui.prefix_ids(nodes, prefix)` 会给 DSL 里所有**显式 id** 加分区前缀
（如 `"tab_ai"` → ui.json 里的 `"m_tab_ai"`）。任何「按 id 收集字形 / 匹配控件」的
字典（如 json2eez 的 `RAIL_TAB_IDS`）如果键写的是 build_ui 里的原始 id，
**永不命中且无任何报错**——表现是 FA 图标字形从未进烘焙集合、整排缺字形方框，
而个别恰好也在原有符号集里的码位（如 F001）正常渲染，极具迷惑性
（会误判成 FA woff 缺字形，实测 cmap 四码位齐全）。
规则：**写死 id 之前先 grep ui.json 拿实际 id**；排查时按
「eez-project fonts[].lvglSymbols 是否含目标码位 → FA woff cmap 是否覆盖 → 烘焙产物 .c 是否含码位」
三段逐级定位（`intake/P-0024`）。

### 11.6 EEZ 原生主题三件套（fix_tabview 类运行时补丁的替代，`intake/P-0025`）

用户纪律：**UI 一律 EEZ 原生定义，禁止往生成代码里注入 C 补丁**。EEZ 1.22.10 原生能力实测
（反编译 `resources/app.asar` 生成器模板，`lv_theme_default_init(dispp` 全包唯一命中）：

1. **深色主题**：生成器发
   `lv_theme_default_init(dispp, lv_palette_main(LV_PALETTE_BLUE), lv_palette_main(LV_PALETTE_RED), <dark>, LV_FONT_DEFAULT)`，
   `<dark>` 取自工程 **`settings.general.darkTheme`**（布尔字段，json2eez 直接写 `true`）。
   主/次色**硬编码** BLUE/RED，工程改不了（选中高亮即 LVGL 调色板蓝 #2196F3）。
2. **默认字体**：`LV_FONT_DEFAULT` 在 lv_conf.h（平台配置，EEZ 不管）。要指向自定义烘焙字体，
   用 LVGL 官方口子（lv_font.h 在 `lv_font_t` 定义之后展开）：
   `#define LV_FONT_CUSTOM_DECLARE extern const lv_font_t ui_font_xxx;` +
   `#define LV_FONT_DEFAULT &ui_font_xxx`。
   **ESP-IDF 真机例外**：Kconfig（`CONFIG_LV_FONT_DEFAULT_*`）选不了自定义字体，需固件 main
   在 `ui_init()` 之后补一次 `lv_theme_default_init(..., true, &ui_font_xxx)`（平台接线，非 UI 代码）。
3. **tab 图标/中文标签**：EEZ 的 `tabName` 原样落到 tab 按钮 label 文本 —— 直接写 FA 私有区
   字符即可（`json2eez` 对 rail tab 生成 `tabName=chr(0xF4AD)` 等），中文标题照常；
   字形都必须烘进 `LV_FONT_DEFAULT` 指向的那份字体。

**EEZ 画布预览 ≠ 运行时效果**：预览按工程 JSON 静态渲染，不执行 LVGL 运行时——
darkTheme、LV_FONT_DEFAULT、tabview 内部主题样式在预览里统统看不到（预览发白 ≠ 工程坏了）。
验收以 PC 仿真图（真 LVGL + 真 SDL 快照）为准；EEZ 预览只用来摆控件位置。

### 11.7 EEZ tab 栏原生定制口子 + LVGL tabview 按钮填满机制（`intake/P-0026`）

> **⚠ 状态（2026-09-28 第五轮后）**：本条的 inject_tabbar_styling 路线**已停用**
> （json2eez.py 里函数保留、main() 调用已注释）——现行方案是 §11.8 的
> 「tabSize=0 隐藏原生栏 + 设计稿 rail 容器 + tabviewSetActiveTab 动作」。
> 但本条机制本身仍然成立：首子容器样式口子、按钮填满机制、可继承样式在
> 「tabSize>0 的原生 tab 栏」场景（或口子复用）时依然有效，留档备用。

1. **tab 栏定制口子（asar 实证）**：EEZ 的 `LVGLContainerWidget.toLVGLCode` 有专门分支——
   容器若是 tabview 的**第一个子对象**，生成器不为它建对象，而是把它的 localStyles 发射到
   `lv_tabview_get_tab_bar()`（V9；V8 是 get_tab_btns）；**第二个子对象** → `lv_tabview_get_content()`。
   即：给 tabview 前插一个空 container 承载 localStyles（text_font/text_align/pad_*/bg_color...），
   就能纯 EEZ 原生控制 tab 栏字体、内边距、背景，无需任何 C 补丁。
2. **LVGL 9.4 tab 按钮永远填满按钮栏**（lv_tabview.c 实证）：按钮是 `lv_button` 且
   `lv_obj_set_size(button, lv_pct(100), lv_pct(100))` + `flex_grow(1)`——按钮栏多高按钮就
   均分多高（446px ÷ 4 = ~111px 整格大块的根因）。收紧凑行的唯一原生手段 = 在按钮栏上垫
   `pad_top/pad_row/pad_bottom`（pad_row 即 column flex 间距），把内容区压到顶部。
3. **tab 按钮 label 的字体与对齐靠继承**：label 自身不设字体，沿「label → button → 按钮栏」
   继承 `text_font`；`text_align` 是**可继承属性**（lv_style.c:126 实证），设在按钮栏上即可让
   按钮文本居中。因此 tab 栏一个 text_font 就能同时改图标与文字大小。
4. **混合字体的妙用**：本工程字体同含中文+FA 图标字形，rail 的 `tabName` 写
   「图标字符+`\n`+中文」两行即可原生实现设计稿「图标在上、文字在下」的形态——
   一个 label 只能一个字号，图标与文字同字号是此路线的已知取舍。
5. **字体兜底**：tab 栏主字体（如 15/17px）与 `LV_FONT_DEFAULT` 兜底字体（13px）都要收齐
   tabName 字形——首子容器机制万一失效，tab 栏退回默认字体也不出 tofu。
6. **坑**：注入的样式容器 x/y 必须写父 tabview 的绝对坐标（to_relative 按「子绝对−父绝对」
   换算，写 (0,0) 会变负相对坐标被 check_bounds 拦下）；工程门禁要求容器必须有 identifier。

### 11.8 隐藏原生 tab 栏 + 自定义导航 + tabviewSetActiveTab 动作（`intake/P-0027`）

1. **tabSize=0 是隐藏原生 tab 栏的实测标准手段**：tabview 属性 `tabSize`（tabviewSize）
   设 0 → 生成 `lv_tabview_set_tab_bar_size(obj, 0)`，tab 栏不占位，content 原点即 tabview
   原点（tab 锚点坐标按父原点写）。§11.7 的首子容器样式口子在此配置下自然失效（栏没了）。
2. **自定义导航 = 普通 container/button 容器 + `tabviewSetActiveTab` 动作**。asar 逐字实锤
   （registerAction）：`id:60, name:"tabviewSetActiveTab", group:"Tabview", properties:
   [{object, widget:Tabview}, {tab, integer, 0-based}, {animated, boolean}], defaults:{animated:true}`。
   运行时 eez-flow.cpp `actions[]` 函数表（表长 65）index 60 = `&tabviewSetActiveTab`，
   经 `executeLVGLApiComponent` 调度，LVGL 9 生成 `lv_tabview_set_active(obj, tab, anim)`。
   json2eez 侧与 goto/changeScreen 同机制：`LVGLActionComponent` + connectionLine
   （source=按钮 objID, output=CLICKED, target=动作 objID, input=@seqin）。
3. **核心坑（16 errors 根因）——动作里引用控件禁止手写 id 字符串**：EEZ identifiers 表
   在 finalizeObjectAccessibleFromSourceCodeTable 里只 push「第一遍扫描中被
   markObjectAccessibleFromSourceCode 标记的对象」（即生成器会输出 `objects.xxx` 引用的
   widget）；且 **identifier 名就是工程 JSON 里 identifier 字段的原值**（UnderscoreLowerCase
   规范化）。而本工程的前缀重写发生在 **build_ui.py 的 assign_ids/prefix_ids**（不是
   json2eez——json2eez 只是消费 ui.json），显式 id 被加页别名前缀（`main_nav` → `m_main_nav`，
   PAGE_ALIAS["Main"]="m"）。动作 object 字段写重写前的名字 → 第二遍扫描
   getWidgetObjectIndexByName 里 `identifiers.indexOf(t)` 落空 → EEZ build 报
   `Widget index not found for "xxx"`（每个动作组件一条，共 N 条），并伴随
   `TypeError: Cannot read properties of undefined (reading 'selectTab')`。
   注意 getWidgetObjectIndexByName 第一遍直接 return 0，报错只出现在第二遍——
   报错数=动作组件数，别误当成更多处引用。
   **修法（结构级）**：DSL 里 switchTab 写 `{"tv_ref": <tabview DSL 节点引用>, "tab": N}`，
   build_ui `main()` 在 json.dump 前递归 `_resolve_switchtabs()` 把 tv_ref 换成 `tv_ref["id"]`
   ——assign_ids 是原地改写节点 id，且在导航容器挂进 screen 之后调用，此刻解析拿到的
   必是最终 id。与 §11.5（按 id 收集必须用最终 id）同源，这次上升到机制层：
   **凡跨节点引用控件，一律「节点引用 + assign_ids 后统一解析」**。
4. **选中态高亮（2026-09-28 起统一为 CHECKED 动作链方案，见 §11.9）**：
   - **旧案已废除**：设置左栏 rail_cats 曾在每个子 tab 首位挂副本（4 份）——副本在
     tabview 内容区里，点击切 tab 时左栏跟着页面一起滑动（用户实测指出），违反
     「tab 固定、页滑动」规则；主 rail 高亮静态钉死「对话」不跟随，也是已知偏差。
   - **现案（单实例 + 两态 + 动作链）**：rail 与 rail_cats 都只挂一份（外置固定，
     rail 挂 screen 级、rail_cats 挂 set_nav 的兄弟位），每项 DEFAULT/CHECKED 两态样式，
     初始高亮用 checkedState，点击走 objClearState→objAddState→tabviewSetActiveTab
     动作链。详细机制与 asar 实证见 §11.9。
5. **设计稿形态还原**：AI/音乐等页设计稿本无顶部 tab 栏——此前凭空加的 30px 原生栏
   是差异大头。tabSize=0 + 设计稿 rail 容器后，G5 17.10% → 8.84%（11/11 屏全过）。
6. **验证清单**：screens.c 每个 tabview 一处 `lv_tabview_set_tab_bar_size(obj, 0)`；
   EEZ build 0 error（动作 identifier 全解析）；仿真图确认 rail 形态与设计稿一致；
   **跨主 tab 的屏要单独放大看 rail 高亮**（如 05 音乐页），平均差异分会掩盖
   60×55 高亮块的错位。

### 11.9 tab pager 通用规则：导航外置固定 + CHECKED 高亮跟随（`intake/P-0028`）

用户 2026-09-28 实测确立的通用规则：**以后所有 tab pager 类型，tab 键固定、只有页滑动**。
任何导航（rail / rail_cats / 未来的分段条）都不许挂进 tabview 内容区，否则点击切 tab 时
导航跟着页面横滑（P-0028 的根因：rail_cats 4 份副本挂在各 set 子 tab 首位）。

1. **结构**：导航单实例，挂 tabview 的**兄弟位**（rail 挂 screen 级、rail_cats 挂
   `sett["children"] = [sett_nav, rail_cats(...)]`，z 序压在 tabview 上）。高亮跟随不再
   靠副本，靠状态样式 + 动作链。
2. **两态样式**：每个导航项 DEFAULT/CHECKED 两态都写全（默认主题给 CHECKED 定义过样式，
   只写 DEFAULT 会被主题盖住——与 switch 同坑）。工程 JSON 样式 definition 的 state 键是
   **字符串**（asar LVGL_STYLE_STATES：DEFAULT/CHECKED/PRESSED/…），LVGL 9 数值 CHECKED=4
   （lvglStates_V9_5_0 表；LVGL 8 是 1，别混）。
3. **文字/图标色跟随 = LVGL text_color 父链继承**：按钮样式里写
   `text_color`（DEFAULT 灰 / CHECKED 亮），内部 icon/label **不写 color**（DSL color=None
   时不落 text_color 样式键）。text_color 是继承属性，label 沿父链取最近定义、状态位按
   `(state & sel)==sel` 匹配且高位优先 → CHECKED 自动压过 DEFAULT。不要给子 label 单独
   add/clear state（动作数会翻倍）；**例外**：继承链上没有状态样式兜底的静态项（如
   rail_cats 不可点行）必须写死颜色，否则一路继承到 screen 主题白。
4. **初始高亮 = checkedState（LVGLWidget 基类属性）**：所有 widget（含 button/container）
   工程 JSON 都可写 `"checkedState": true, "checkedStateType": "literal"` → codegen 生成
   `lv_obj_add_state(obj, LV_STATE_CHECKED)`（asar classInfo
   `makeLvglExpressionProperty("checkedState","boolean")` 实证）。不需要 screen LOAD 事件。
5. **点击动作链（单 LVGLActionComponent 多 actions）**：`executeLVGLApiComponent`
   （eez-flow.cpp:4191）对 `component->actions[]` **逐条顺序执行** → 一个动作组件装下：
   `objClearState(其余项, CHECKED)` ×N → `objAddState(自己, CHECKED)` →
   `tabviewSetActiveTab(tv, idx)`。asar 实证：`id:20 objAddState` / `id:21 objClearState`
   （properties: object(widget) + state(enum:LV_STATE)，字面量写 `"state":"CHECKED"`）；
   另有 id:15/16 objAddFlag/objClearFlag（flag enum，默认 "HIDDEN"）、id:18
   objSetStateChecked（object+boolean）。json2eez：switchTab =
   `{"tv_ref":<节点引用>, "tab":N, "add":[<节点引用>...], "clear":[<节点引用>...]}`，
   `_resolve_switchtabs` 统一解析成最终 id（铁律同 §11.8.3）。
6. **仿真截图必须走真实点击**：sim.py 原来直调 `lv_tabview_set_active` 绕过动作链 →
   高亮不跟随、G5 虚高（9.09%）。改为 `lv_obj_send_event(导航按钮, LV_EVENT_CLICKED, NULL)`
   优先（无导航按钮的层才直调），截图行为 = 真机点击行为，G5 回落 8.54%。
   顺带补了 `lv_tick_inc` 驱动 + shoot 时间片加长到 400ms（tabviewSetActiveTab 默认
   animated:true，动画 180ms 要走完再截屏，否则截到切换中间态）。
7. **验收结果（2026-09-28）**：EEZ build 0 error；G5 平均 8.54%（11/11 屏过，上轮 8.84%）；
   10_display/05_now_playing 目检：rail 高亮跟随 + cats 高亮跟随 + 其余项灰字，全对。
   已知边界：AI/音乐子 tab 当前无导航 UI（设计稿无顶部 tab 栏，仅初始 actTab 定页）——
   后续若要可切换需按本节规则补顶部导航条。
8. **快速修改清单（下次同类需求直接按单改，2026-09-28 沉淀）**。改动点索引（本工程）：

   | 需求 | design/build_ui.py | design/json2eez.py | design/sim.py |
   |---|---|---|---|
   | 导航项定义 / 两态样式 | `rail()` / `rail_cats()`（button 的 `checked_style` 参数；label `color=None` 走继承） | — | — |
   | 挂载位置（兄弟位） | `s_home()`：`sett["children"] = [sett_nav, rail_cats(...)]`；rail 挂 screen 级 | — | — |
   | 点击动作链 | switchTab 节点 `{"tv_ref","tab","add":[],"clear":[]}` | `build_widget` 尾部（checkedState 通用生成）+ `build_page` 动作链段（单 LVGLActionComponent 多 actions） | — |
   | 节点引用 → 最终 id | `_resolve_switchtabs()`（assign_ids 之后跑） | — | — |
   | 截图点击驱动 | — | — | `nav_btn_for()`（layer0=主 rail / layer3=set cats）+ `set_tv_layer()` + shoot 时间片 |

   常见需求 → 最小改动：
   - **加一个导航项**：rail/rail_cats 里加两态按钮（switchTab 引用一律写节点引用，
     铁律 §11.8.3）→ **所有既有项的 `clear` 列表补上新项引用、新项 `clear` 补既有项、
     `add` 补自己**（动作链是全名单式，漏一项 = 高亮叠两块）→ 确认初始 `checked:true`
     该挪到哪一项。动作数基线：rail 9 动作/项、cats 4 动作/项。
   - **改高亮样式**：只改 CHECKED 态（bg/bgOpa/text_color），子 icon/label 保持不写色。
   - **加指示条**：nav_marker 两态显隐（DEFAULT bg_opa 0 / CHECKED 255），
     marker 引用必须进**每一项**动作链的 add/clear 名单。
   - **新页面要 tab pager**：整页按本节 1~7 条实施，导航挂 tabview 兄弟位；
     动手前先走 PLAYBOOK 场景 E 第 0 步确认清单。
   改完自检链：`build/verify_center.py` → EEZ build 0 error（动作 id 全解析）→
   `python design/all.py --sim` 全量 → G5 门禁 → **逐屏目检高亮跟随**
   （平均差异分会掩盖高亮块错位，§11.8.6）。
9. **交互约定（用户 2026-09-28 确立）**：下次遇到 tab pager / 导航类界面，**动手前先询问
   用户要实现什么效果**（哪个固定/哪个滑动、高亮怎么跟随、有无指示条、挂载位置、要不要
   动画），确认后再按本节实施。确认清单见 PLAYBOOK §0 第 8 条 / 场景 E 第 0 步。

### 11.10 按钮→写变量：SetVariableActionComponent（onClick 机制，2026-09-28 按钮全适配）

功能按钮（非导航）要"点了有反应"，EEZ LVGL 项目的正路是 **EEZ 原生 SetVariable 组件**，
不是手写 C 回调（产物只读铁律，PLAYBOOK §0.9）。全套机制（EEZ Studio 1.22.10 实证）：

1. **DSL**：按钮节点配 `"onClick": {"setVar": "<输出变量名>", "value": <常量/表达式>}`。
   与 switchTab 并列；同一个节点别同时配 goto（会被 place() 的 strip_goto 剥掉，
   且 goto/switchTab/onClick 共用 eventHandlers 字段，覆盖关系脆弱——配新动作时
   显式 `pop("goto")`）。
2. **json2eez 编译**：收集 (path, onClick) → 生成组件
   `{"type": "SetVariableActionComponent", "entries": [{"variable": <名>, "value": <表达式字符串>}]}`
   + connectionLine(source=控件 oid, output=CLICKED, input=@seqin)。
   variable 必须是 **ui.json variables[] 里声明过的 native 输出变量**（声明同步链见
   工程侧约定：variables[] → 工程 globalVariables → vars.h extern → native_vars.cpp 定义）。
3. **运行时（关键认知）**：LVGL 项目的 flow 是「**组件数据打包进 ui.c assets 数组 +
   eez-flow.cpp 运行时解释**」——生成产物里**没有** `set_var_xxx(1);` 这样的 C 直调
   （那是 EEZ GUI 项目的编译期路线，别被 asar 里的 genFlowCode 误导）。组件类型
   `COMPONENT_TYPE_SET_VARIABLE_ACTION=1007`（eez-flow.h:271），运行时函数表已注册
   （eez-flow.cpp executeSetVariableComponent），变量赋值走 ui.c native 注册表的
   set 函数指针。**EEZ build 0 error + grep 不到直调 = 正常**，链路要靠运行时冒烟验证。
4. **验收（必做）**：仿真 main 里 `lv_obj_send_event(控件, LV_EVENT_CLICKED, NULL)`
   真实点击 → 跑时间片（排空命令队列）→ 看 io 层回显打印；tab 跳转类断言用
   `lv_tabview_get_tab_active`（**LVGL 9.4 没有 lv_tabview_get_active**，链接会炸）。
5. **新增输出变量的同步清单（六处，漏一处就链接期炸）**：ui.json variables[] →
   native_vars.cpp get/set → app_model.h APP_OUT 枚举 → app_model.cpp 排空 switch →
   io_iface.h 声明 → io_pc.cpp/io_esp.cpp 实现。
6. **盘点工具**：只读扫描 ui.json，按 type∈{button,slider,switch,...} 分「已配
   （goto/switchTab/onClick）/未配」两列（工程 design/_audit_buttons.py 可直接抄）。
   「未配」按钮点起来静默无反应——新界面交付前必须跑一遍盘点，未配数为 0 才算完。

### 11.11 用户事件：EEZ 官方 User Action（native 实现，2026-09-29 语音页光球 voice_stop 实战）

官方依据（用户要求细读官方手册）：Reference Guide PDF（GitHub eez-open/studio
`docs/reference guide/`，784 页）P7.3「Working with Actions」：LVGL 工程也有
Actions 调色板（Fig.78），底部列 User Actions；A34.2.16「Event handlers」：控件
事件 Handler type = **Flow | Action**，Action 需填 User action 名。源码交叉验证：
`features/action/action.tsx`（Action{implementationType:"flow"|"native"}）、
`lvgl/build.ts::buildActionsDecl/buildActionsArrayDef`、`lvgl/widgets/Base.tsx`
（native action 生成直调）、asar 内 findAsset（`maps.name` 按 **名字** 索引）。

1. **生成产物三件套**（EEZ build 对 native User Action）：
   `actions.h`（`extern "C" void action_<name>(lv_event_t * e);`，下划线小写）、
   `ui.c`（`ActionExecFunc actions[] = { action_<name>, ... };` 传给 eez_flow_init）、
   `screens.c`（控件 `event_handler_cb_<页>_<控件>` 里 `action_<name>(e);` **直调**
   ——不经 flow 解释器、不经变量；ui.c 里空表 `{ 0 }` = 工程无 User Action）。
2. **DSL 约定**：顶层 `"actions": [{"name","implementationType":"native","userProperties":[]}]`
   （json2eez `sync_actions` 同步进 project["actions"]，objID 用 oid("actions/"+名)）；
   控件 `"onAction": "<动作名>"`（与 goto/switchTab/onClick 互斥）。编译成
   `eventHandlers:[{eventName:"CLICKED", handlerType:"action", action:"<名>", userData:0}]`。
3. **两个静默坑**：① 装饰性 `circle()` 默认 clickable=False——交互体必须显式
   `clickable=True`，否则生成 `lv_obj_remove_flag(CLICKABLE)`，点击永远落空；
   ② eventHandler.action 存 **动作名**，存 objID 会生成**空 CLICKED 分支**（findAsset
   按 maps.name 查不到），EEZ build 0 error 不报错，必须看产物核对回调体非空。
4. **固件接入**：`src/native/native_actions.cpp` 实现 `action_<name>(lv_event_t*)`
   （include 生成的 actions.h，extern "C" 对齐）→ `app_set_output(APP_OUT_*)` 入
   输出命令队列 → user_io_tick 排空 → io_*。与 setVar 路线分工：setVar=声明式
   状态写入（开关/翻转）；User Action=命令式回调（拿得到 lv_event_t，无需声明变量）。
   真机 `src/native/CMakeLists.txt` 的 NATIVE_SRCS 必须补 native_actions.cpp
   （actions.h 只有声明，唯一定义在此；漏了链接期炸，P-0020 同款）。
5. **与 executeLvglActionHook 的关系**：eez-flow.cpp `executeActionFunction(actionId)`
   → `executeLvglActionHook(actionId - 1)` 是 flow 内 CallAction/ACTION 组件的运行时
   兜底；控件事件绑 native action 走的是更直接的生成期直调（screens.c），**不需要**
   设钩子。别把两条路线混为一谈。
6. **★「按钮触发外部逻辑」官方有三条合法路径，别只讲 User Action（2026-09-29 补）**：
   官方手册**没有任何「推荐用哪个」的表述**（检索 recommended / should be used 全是
   不相关命中），native 变量专章在手册里还是 "explained in Chapter XX" **占位符**
   （官方未写完）——所以选型只能按**工程特性**，不要冒充官方口径。三条路：
   · **① 事件 Handler type = Action（native）** → 生成期直调 `action_x(lv_event_t*)`，
     不经 flow 解释器，**能拿到事件上下文**（区分来源控件/事件码），开销最小；
   · **② 事件 Handler type = Flow → 内置 SetVariable 组件**（P8.1 明列三个变量组件：
     Evaluate / Watch / SetVariable）→ 运行时解释执行，调 `set_var_x(v)`，
     **拿不到事件上下文**，但变量值可用 `get_var_x()` 回读、可回显到 UI；
   · **③ Watch 组件（A91，P.329）**：「monitors the change in the value... every value
     change is sent」= **变量变化驱动后续逻辑，官方一等公民**，不是什么野路子。
   **选型判据**：需状态回显（开关/亮度/时钟/电量/信号）→ native 变量；
   一次性命令或需要 lv_event_t → User Action；**若计划关闭 Flow 支持，
   SetVariable 组件会消失而 native Action 依然工作**（架构级差异，影响选型）。
   ⚠ **两个已被证伪的错判，别再写进任何总结**：
   (a) 「用变量触发外部逻辑属于官方语义之外」——错，②③都是官方明列机制；
   (b) 「变量 setter 会被固件回写触发、塞命令易自激」——**至少 EEZ-test 工程不成立**：
       输入变量（wifi_state/rssi/battery/clock/wifi_icon/bars）的 `set_var_*` 全是
       **空实现**（native_vars.cpp `/* input: UI must not write */`），固件更新走自己的
       g_in_*、UI 用 `get_var_*` 拉，根本不经过 setter；输出变量固件只排空不回写。
       **一般化论断必须先回本工程源码验证，别把「理论上可能」当成事实。**
7. **★ 迁移动作时 `sync_variables` 会把已删变量「复活」（2026-09-29 实测）**：
   变量同步若写成「保留工程里多出来的变量」（`kept = [g for g in old
   if g.name not in decls]`），本意是保护 EEZ GUI 里手工加的变量，但它**无法区分
   「手工加的」和「DSL 里已删掉的」**——从 ui.json 删掉一个变量后，它会被当成
   手工变量永久残留：vars.h 仍生成 `extern` 声明，而 native_vars.cpp 里的实现已删
   → **链接期 undefined reference**（EEZ build 本身 0 error，看不出来）。
   **修法**：变量同步与动作同步保持一致，都以 DSL 为准**整体重建**
   （单向管线，ui.json 是唯一真值源），并打印被移除的变量名以便核对。
   **验收动作**：迁移后必查 `vars.h` 里已删变量残留数为 0，
   且 `actions.h` 声明与固件实现的符号名**逐一 diff 一致**。

### 11.12 EEZ 字体烘焙：GUI 会，headless CLI 不会（2026-09-29 实测，**推翻旧结论**）

旧笔记写的「EEZ 根本不生成字体 / 烘焙只在 GUI 里做」是**错的二分法**，正确事实分三层：

1. **EEZ 有烘焙能力（源码级证据）**：app.asar 里 `getName("ui_font_", this.params.name,
   UnderscoreLowerCase)` + lv_font_conv 全套参数（size / bpp / no_compress / lcd /
   lv_fallback / opts_string），交给 `new Worker(path.join(__dirname,"lvgl-worker.js"))`
   执行。工程侧 `settings.general.embedFonts=True`、`renderingEngine='LVGL'`、
   fonts[] 的 TTF 路径有效、`fonts.h` 里的声明也是 EEZ 写的。
   **用户在 GUI 里 Check and Build 确实会产出 `ui_font_*.c`。**
2. **headless CLI `--build-project` 不烘焙（3 次实测一致）**：把 11 个 `ui_font_*.c`
   连同 `src/ui/.eez-project-build` 一起删光再跑 build → 产出 **0 个字体文件、
   0 报错、耗时 2.2s**，日志里连 `Extracting font "..."` 都没有。
3. **★ orphan 清理会把字体删掉（最坑的一条）**：EEZ 构建收尾会 unlink
   「**上一次清单里有、本次没重写**」的文件（asar 源码：
   `const r=new Set(i), s=t.filter(e=>!r.has(e)); ... \`Deleted orphaned file: ${t}\``，
   unlink 失败被 `catch` 吞掉）。推论：
   · GUI 构建过 → 清单含 11 个字体 → **紧接着跑 CLI build 会打 10 条
     `Deleted orphaned file:` 把字体全删**（缺的那个 unlink 抛错被吞，所以是 10 不是 11）；
   · CLI 构建过 → 清单不含字体 → 再跑 CLI **不删**（此时字体是 gen_fonts.py 补的，安全）。
   **所以 `eez_build.py` 之后必须紧跟 `gen_fonts.py`**（`design/all.py` 已是这个顺序）。

4. **★ 根因 + 正解（2026-09-29 反编译 asar，已落实到脚本）**：
   源码 `project-editor/store/fonts-cache.js`：
   ```js
   getFontsCacheFilePath(){ return this.projectStore.filePath + "-fonts-cache" }
   async load(){ if (this.projectStore.project.settings.general.cacheFonts) { ...读缓存... } }
   ```
   **`cacheFonts=False` → EEZ 不加载任何字体缓存**，每次都得现场跑 Worker 烘焙；
   而现场烘焙这条链在 headless CLI 下不产出 → 永远 0 个字体文件。
   （当时本工程正是 `cacheFonts:False` 且 `test.eez-project-fonts-cache` 不存在。）
   **修法**：`json2eez.py` 的 `ensure_build_settings` 里置 `settings.general.cacheFonts=True`
   → 由 **EEZ Studio GUI 烘焙一次**写入缓存 → 之后 CLI build 直接取官方结果输出
   `ui_font_*.c`。**字体数据始终由官方软件烘焙，脚本不代劳。**
   排查同类问题记住先验三项：`embedFonts` / `cacheFonts` / 缓存文件是否存在。

5. **用户原则（2026-09-29 确立）**：**字体必须由 EEZ Studio 官方生成，禁止脚本自己烘焙。**
   三条路的定性（都已实测过）：
   · A 脚本自己调 lv_font_conv **—— 违反原则，已废**
   · B 后台拉起 EEZ Studio GUI 按 Ctrl+B —— 能用，但要开 GUI、依赖窗口焦点，已废
   · **C 解包调 EEZ 自带引擎 —— 当前方案**（第 6 点），纯后台且产出即官方产物
   `gen_fonts.py` 已删除 lv_font_conv 调用，改为「校验 ui_font_*.c 齐全 + 回写实测度量」，
   缺字体 → 报错并引导跑 `eez_font_engine.py --force`（不代劳、不兜底生成）。
   `eez_check_build.py`（CMake 编译前钩子）缺字体会直接中断编译。

6. **★★ 正解：解包调 EEZ 自带引擎（2026-09-29 定稿，`design/eez_font_engine.py`）**：
   `cacheFonts` 那条路（第 4 点）**没能**让 CLI 烘焙（实测仍是 0 个字体），
   后台拉 GUI 按 Ctrl+B（旧第 6 点）能用但**要开窗口、依赖焦点**，脆弱。
   最终方案 C：**把 app.asar 里的官方引擎整个解出来，在 Node 里以 Worker 语义直接调用** ——
   纯后台、不开 GUI、不弹窗，**产出与 GUI 点 Build 逐字节一致（11/11 IDENTICAL 实测）**。
   组件（都在 `.../eezstudio/resources/app.asar` 内）：
   ```
   build/project-editor/features/font/font-extract/lvgl-worker.js   ← 引擎入口（EEZ 原文件）
   node_modules/lv_font_conv/lib/freetype/build/ft_render.js        ← freetype（wasm 内嵌 base64，自包含）
   node_modules/{opentype.js, make-error, bit-buffer}               ← 运行时依赖
   ```
   调用方式：`global.self = ctx`（worker 里 `const ctx=self; ctx.onmessage=...`），
   然后 `require(引擎)` 拿到 `ctx.onmessage`，用 `{data:{args, output}}` 触发，`ctx.postMessage` 收结果。
   **一个 Node 进程可连续烘 11 个字体（约 2 秒）**，`collect_font_data` 结尾的
   `ft_render.destroy()` 不影响下一个。

   ★★ **要让产出逐字节一致，有 8 个必须踩准的点（全部实测，错一个就对不上）**：
   1. asar 头部：前 16 字节是 4 个 uint32，**第 4 个**才是 header JSON 长度；
      `BASE = 16 + header_size`，叶子节点 offset 相对 BASE。
      （用 `data.find(b'{"files"')` 找起点 + `data[4:8]` 当长度是错的。）
   2. **C 源码没有被 base64 编码**：worker 里两个返回值都写 `.toString("base64")`，
      但 `String.prototype.toString(enc)` **忽略参数原样返回**；只有 bin 是 Buffer、才是真 base64。
      按首字符是否是 `/` 区分，否则解出二进制乱码。
   3. **主字体的 symbols 取顶层 `lvglSymbols`**（本工程为空）。`lvglGlyphs.symbols`
      是 UI 展示用的合集，**含 FontAwesome**，拿去烘会报
      `Font "..." doesn't have any characters included in "..."` —— FA 属于附加源。
   4. 附加源工程字段名是 `{filePath, lvglRanges, lvglSymbols}`，**不是** `encodings/symbols`。
   5. `lv_include` 取自 **`settings.build.lvglInclude`**（不是字体条目上的字段）。
   6. `opts_string` 顺序：`--symbols` 在 `--range` **之前**，附加源追加在 `--format lvgl` **之后**
      （见 `features/font/font.js` 的 `_lvglExtractFontParams`）。
   7. **落盘后处理**：连续 3+ 换行折叠成 2 个 + 去掉末尾所有空白
      （官方产物末尾**不带换行**）。不做这两步会差 8 个空行 + 末尾换行。
   8. **（P-0035）opts_string 的 `--font` 用工程 filePath 的原文**（font.js 实证：
      `--font ${this.source.filePath}` / `--font ${e.filePath}`，无任何相对化）——
      所以工程里 filePath **必须存相对工程根**（GUI 保存的工程就是相对的），
      内核读文件以**工程目录**为基准（等价 getAbsoluteFilePath，不依赖 cwd）。
      连带：`ensure_engine` 缓存命中也必须校验 bake.js 内容（驱动代码 ≠ 引擎，
      内核更新后旧 bake.js 还在跑 = 改动静默失效）。

   脚本默认「字体定义没变就跳过」（key 存 `design/.font_bake_state.json`），`--force` 强制重烘，
   `--clean` 清引擎缓存。引擎缓存放 `%LOCALAPPDATA%/eez-font-engine/<asar size-mtime hash>`，
   不污染工程、EEZ 升级会自动重建。找不到 asar 可用 `EEZ_STUDIO_ASAR` 环境变量指定。

   **★ 代码分两层：内核进工具箱，胶水留工程（2026-09-29 用户问「脚本要不要入库」后的定案）**。
   这套东西里只有「解包 + 烘焙」是**工程无关**的，其余（写哪个目录、要不要增量、
   孤儿清理、接不接 `all.py`）全是**工程专属**的。混在一起就会拷不动、改不动。
   ```
   tools/eez_font_bake.py      内核：find_asar/find_node/extract_engine/bake/kernel_hash
                               只写 out_dir + manifest.json，不碰任何工程目录
   design/eez_font_engine.py   胶水：调内核 → 搬到 src/ui → 增量状态 → 孤儿清理
   ```
   工具箱 README 「五、栈专属工具放哪里」已把胶水脚本明确列为工程侧该放的东西。
   **防分叉**：工程侧别复制 `BAKE_JS`，而是 import 内核，并校验
   `eez_font_bake.kernel_hash()`（= `BAKE_JS` 的 sha256）——
   改了烘焙行为指纹就变，能立刻发现"工具箱升级了、工程里那份还在跑旧逻辑"。

   （旧方案「后台拉 GUI 按 Ctrl+B」保留要点备用：只发 Ctrl+B 不要先发 Ctrl+K ——
    Check 会弹结果框挡按键；启动前 `env.pop("ELECTRON_RUN_AS_NODE")`；
    单纯打开工程不会烘焙。已被本方案取代，`eez_gui_build.py` 已删除。）

⚠ **方法论教训（这条比结论本身更值钱）**：当时我从「删掉一个字体文件后跑了一次
CLI build，它没回来」直接推出「EEZ 不生成字体」——这是**单次观察否定能力**的谬误。
「这一次没发生」只能证明这条路径这次没触发，不能证明 EEZ 没有该能力、更不能覆盖
GUI 路径。**正确顺序**：先查配置开关（`embedFonts` / `renderingEngine`）和产物清单
（`.eez-project-build`），再对 GUI / CLI **分别**下结论；下结论前先问「我的观察覆盖了
几条路径、几次」。

---

### 11.13 ★ 怎么证明「后台产物 == 官方产物」（2026-09-29 定稿，配套 `tools/font_verify.py`）

上一节讲的是**怎么让产物对得上**；这一节讲的是**怎么证明它对得上**。
结论会过期、参数会变，但验证方法不过期 —— 换 EEZ 版本、换字体、换机器后
**第一件事就是重跑这一节**，而不是相信「上次是对的」。

#### 一、先立真值：黄金样本只能来自 GUI

    python tools/font_verify.py snapshot --src src/ui --golden <dir> \
           --note "EEZ Studio 1.22.10 GUI Check and Build 产物"

★ **黄金样本的唯一合法来源是 EEZ Studio GUI 点 Build**，不能是任何脚本产物。
自己烘一份当真值 = 自己给自己当裁判，一致也证明不了任何事。
`_manifest.json` 会记下时间/来源标注/每个文件的 sha256 —— 下次比对时打印出来，
一眼能看出样本是不是被脚本产物覆盖过。

#### 二、逐字节比对（必要，但不充分）

    python tools/font_verify.py check --src src/ui --golden <dir> --metrics

`--metrics` 顺带比对 `line_height / base_line`。**这一项必须零漂移** ——
字节层面差两个空行不影响显示，但度量一变整屏文字就画高，而它恰恰最容易静默变化。

⚠ 为什么比对**不充分**：万一 `src/ui` 里的字体根本没被覆盖（增量跳过、路径写错、
写入失败被吞），比对照样全绿。**所以必须做第三步。**

#### 三、清空重建实验（最硬的一条）

    rm src/ui/ui_font_*.c           # 连增量状态一起删，逼它真的重烘
    rm design/.font_bake_state.json
    python design/eez_font_engine.py --force
    python tools/font_verify.py check --src src/ui --golden <dir> --metrics

    # 再跑完整链路后复校 —— 这一步验证「管线顺序」也是对的
    python design/all.py
    python tools/font_verify.py check --src src/ui --golden <dir> --metrics

**两轮都全 IDENTICAL + 度量零漂移**，才能下「后台产物 == 官方产物」的结论。
第二轮不是冗余：CLI build 有可能把字体当 orphan 删掉、再由后一步补烘，
只有跑完整链路才知道「顺序」对不对。

#### 四、不一致时怎么定位（工具已自动化，这里是原理）

按**从具体到泛化**的顺序排，先命中先报：

| 症状 | 成因 | 修法 |
|---|---|---|
| 产物是可打印字符 < 90% 的乱码 | C 源码被当 base64 解了（`String.prototype.toString(enc)` 忽略参数） | 按首字符是不是 `/` 区分，别解码 |
| 只有 `#include` 那行不同 | `lv_include` 没取到 | 读 `settings.build.lvglInclude` |
| 去掉空行后两边相同 | 漏做空行折叠 | `replace(/\n{3,}/g,'\n\n')` |
| 只差文件末尾 | 漏做去末尾空白 | `replace(/\s+$/,'')` |
| 头部 `Opts:` 行不同 | 参数拼错 | `--symbols` 在 `--range` 前；附加源在 `--format lvgl` 后 |
| `/* U+` 计数不同 | 字形集合变了 | 主字体 symbols 取顶层 `lvglSymbols`；附加源字段是 `lvglSymbols` |
| 换行符不同（CRLF vs LF） | Python 默认 newline 转换 | `newline='\n'`；EEZ 产物是 LF |
| 以上都不是 | 人工二分 | 先看头部注释（参数层），再看首处不同行落在 BITMAPS / GLYPH / KERNING 哪一段 |

**★ CRLF 是诊断杀手**：一旦换行符不同，首处不同必落在第 0 行的 `\r` 上，
真正的差异全被淹没。所以工具里**先归一化换行符再诊断**，把它单独列为一个症状。

#### 五、三条容易忘的原则

1. **别信单一观察**（上一节末尾那条教训的推论）。「删掉一个文件跑一次 CLI build
   它没回来」只能推出「这条路径这次没触发」。下结论前先问：我覆盖了几条路径
   （GUI / CLI / 后台引擎）、跑了几次。
2. **失败要能复现才算数**。烘焙报错时先确认是「参数错」还是「环境错」——
   附加源路径不存在、asar 找不到、node 版本不对，都会伪装成参数问题。
3. **差异分类要写回工具**。这次踩的 7 个坑全部编码进了 `font_verify.py` 的成因表，
   下次同类问题直接出结论，不用重新推理一遍。**经验只有变成可执行检查才不会丢。**

#### 六、代码本身怎么保证不退化（内核 / 胶水分层）

验证对的是**产物**，但产物对了不代表**代码**不会悄悄跑偏 —— 复制一份脚本到工程里、
过几周改一点，两条链就分叉了。所以：

- 烘焙逻辑**只有一份**，在 `tools/eez_font_bake.py`；工程侧 `import` 而不是复制。
- `eez_font_bake.kernel_hash()` = `BAKE_JS` 的 sha256，**任何改动都会变指纹**。
  工程侧胶水在调用前比对一次硬编码的期望值，不一致就报错停机，
  逼着人重跑本节的验证，而不是"好像能跑就继续"。
- 判定基准同样只有一份：真值在 `.golden_fonts/`，判据在 `font_verify.py`。

一句话：**产物有真值比对，代码有指纹比对**，两头都锁住，"和 GUI 一致"才是个
可长期依赖的结论，而不是某一次跑出来的运气。

### 11.14 ★ 回调/变量框架：四层隔离 + 命令/变量双通道 + 代码归属标记（2026-09-29，实战复盘）

> 用户问「UI 里按钮触发回调和变量，有没有软件设计框架图」「框架里要标明哪些是用户添加的
> 代码」「这个框架好不好」。下面把可复用的骨架与方法论提炼出来（工程专属的信号清单见
> 工程侧 `design/architecture/framework.md`，本库只沉淀骨架与纪律）。

#### 一、核心原则：生成代码与用户代码只通过一份契约对话

EEZ 生成的 UI（**不可手改，铁律见 §0.9**）和你的业务代码（可写）**互相看不见**，
只通过一份头文件 `app_model.h` 对话。这份头是**唯一**被两边 `#include` 的文件——
UI 侧调 `app_set_output` / `app_get_input_*`，硬件侧实现 `io_*`，中间状态全在
`app_model` 里。任何把逻辑塞进生成代码、或让生成代码直接调业务函数的做法都违反此原则。

#### 二、四层结构（含「代码归属」标记约定）

用户要求「框架里必须标明哪些是自己加的代码」。落地约定：

> **标记规则**：凡画框架图，用**颜色**区分归属 ——
> 紫色带 = EEZ 生成（标注「不可手改」），绿色带 = 用户添加的代码（标注「只做转发/薄层」）。
> 配套一张**归属速查表**，逐层逐文件写明「EEZ 生成 / 用户添加 / 能否手改」。

```
┌──── ① 生成层  src/ui/                  【EEZ Studio 生成，紫色，不可手改】 ────┐
│  screens.c / actions.h / ui.c / vars.h / ui_font_*.c                    │
└──────┬─────────────────────────── get_/set_var_* · action_* ────┬──────┘
┌──────▼ ② 适配层  src/native/native_actions.cpp · native_vars.cpp ┐【用户添加，绿色】│
│  薄转发：action_* → app_set_output；get/set_var_* ↔ app_get/set_* │
└──────┬────────────────────────────── app_set_*/app_get_* ─────┬─┘
┌──────▼ ③ 契约层  src/native/app_model.h · app_model.cpp ───────┐【用户添加，绿色】│
│  唯一被两边 include 的头：状态数组 + 输出命令环形队列 + 主循环两函数 │
└──────┬────────────────────────── io_sample_inputs / io_* ────┬─┘
┌──────▼ ④ 平台层  src/native/platform/io_iface.h · io_pc.cpp · io_esp.cpp ┐【用户添加，绿色】│
│  唯一因环境而不同的层：io_pc=仿真假数据；io_esp=真机驱动              │
└─────────────────────────────────────────────────────────────────┘
```

**归属速查（铁律级）**：
- EEZ **只**生成 `src/ui/*`（含 `ui_font_*.c`）。**绝不**生成 `app_model.*` /
  `native_*.cpp` / `io_*.cpp` —— 这些全是用户代码，加信号时缺一不可。
- 漏了任何一处用户侧定义 → **链接期** `undefined reference to action_* / get_var_*`
  （P-0020 同款坑）。

#### 三、两条命令通道 + 一条输入通道（A/B/C，命令 vs 变量的边界纪律）

这是框架最容易用错的地方，用户特别强调要理清「触发 user action 和 native 变量」的区别：

| 通道 | 语义 | 路径 | 是否声明变量 |
|---|---|---|---|
| **A · User Action**（按钮 = 一次性命令） | 发送/扫描/翻转开关/停止聆听 | `action_*(e)` 直调 → `app_set_output` → 队列 → `io_*` | **不声明**；EEZ `implementationType:"native"` |
| **B · native 变量（输出）** | 会回写的真状态（如背光 `brightness`） | `set_var_*` → `app_set_output` → 队列 → `io_*` | 声明一个 native 输出变量 |
| **C · native 变量（输入）** | 硬件状态回显到 Label（时间/电量/wifi 图标） | `io_sample_inputs` → `app_set_input_*` → `get_var_*` → 表达式绑定 | 声明一个 native 输入变量 |

**选型判据（人肉纪律，机器不强制）**：
- 命令类（`APP_OUT_*`，值恒 1，收到即执行/翻转）→ 走 **A**；
- 真状态（会被 UI 显示、外部改变量要推回控件）→ 走 **B/C**。
- **别把「点击下发命令」做成变量**：变量 getter 若是 `app_get_output_last` 回声，
  设备端执行失败时 UI 仍显示「已执行」（命令与状态挤在同一变量的后遗症）。
- 官方有三条合法触发路径（§11.11 第 6 条）：native Action 直调 / Flow→SetVariable /
  Watch 组件，**官方无「推荐用哪个」明文**，按工程特性选。

**实战教训（PR-0049）**：本工程曾把 7 个命令型变量（`chat_send` / `wifi_command` /
`mic_toggle` / `dnd_toggle` / `auto_brightness_toggle` / `wake_toggle` / `wake_dnd_toggle`）
做成 native 输出变量，结果它们的 getter 全是回声、无 UI 绑定、不反映真状态 ——
全部迁回 A 通道（onClick→onAction），变量从 16 删到 9（只留真状态）。**这是框架
走向成熟的关键一步**：方向对，但「命令 vs 变量」的边界靠人守，不是机器拦。

#### 四、仿真 / 硬件：靠编译期切换，运行时零分支

上三层（生成/适配/契约）两边**字节级一致**，唯一不同的就是平台层：
`io_pc.cpp`（仿真，假数据 + `printf("[io_pc] ...")`）vs `io_esp.cpp`（真机，读真
GPIO/ADC/WiFi/RTC）。由 `EEZ_SIM` 在 CMake 期选定（`native/CMakeLists.txt`
`if(EEZ_SIM)` 选 pc，否则选 esp；`sim.py` 生成的 CMake 跳过 `io_esp.cpp`）。
**因此加新信号时，`io_iface.h` 加了声明，`io_pc.cpp` 和 `io_esp.cpp` 两边都必须补本体。**

#### 五、扩展信号的标准做法（防链接期炸的同步清单）

加一个信号（动作或变量）必须同步 **4 处**，漏一处即 `undefined reference`：
1. `ui.json` / EEZ 工程（声明动作或变量，`native:true`）；
2. `native_actions.cpp` / `native_vars.cpp`（函数本体，**唯一定义处**）；
3. `app_model.h`（`app_output_id_t` / `app_input_id_t` 枚举）；
4. `io_iface.h` + **两个后端** `io_pc.cpp` / `io_esp.cpp`（实现）。

**缓解工程（建议）**：把这套同步清单固化成 `design/all.py` 的校验——
① `vars.h` 里已删变量**残留数 = 0**（防 `sync_variables` 复活旧变量，PR-0049 第 7 条）；
② `actions.h` 声明与 `native_actions.cpp` 实现符号**逐一 diff 一致**；
③ `screens.c` 里回调体**非空**（防 `eventHandler.action` 写成 objID 生成空 CLICKED 分支，§11.11 第 2 条）。

#### 六、框架评价（用户问「好不好」的诚实回答）

**优点**：隔离干净（唯一契约 `app_model.h`）、仿真/硬件可互换（编译期切换、运行时零
`#ifdef`）、A/B/C 通道语义清晰互不污染、派生输入归 UI 侧现算保持契约最小。
**缺点**：① 输出变量 getter 是「回声」非「真状态」，脆弱（见 §三判据）；② 扩展要改
4 处、漏则链接期炸；③ 无运行时类型安全（`app_value_t` 联合体 + 整型枚举）；④ 两套管接
命名（`"integer"` vs `NATIVE_VAR_TYPE_INTEGER`）易漂移；⑤ 「生成声明 + 手写定义」天然
有裂缝，需长期断言守。
**结论**：方向对、工程化收益明确，但「命令 vs 变量」边界是人肉纪律非机器强制——把
「加信号向导 + 残留符号断言」固化进构建脚本、输出变量 getter 改成「回声 + 真值回采(走 C)
分离」，是优先级最高的两个加固项。

### 11.15 滑动高亮跟随 + 程序切页 animated:false 铁律 + 下拉浮层（2026-09-29/30，实战复盘）

用户原始诉求（eez-test）：①「上下滑动时候，左边的tab没有跟着变动，设置界面也是一样」
②「点击无线网络时候，可以产生一个下拉窗口，而不是屏幕往下滑（推挤其他选项）」③要自查。

#### 一、滑动/程序切页高亮跟随（§11.9 的缺口补全）

§11.9 的高亮跟随只覆盖**点击动作链**；手势滑动切 tab 时没人改 CHECKED。补法（EEZ 原生）：

1. **tabview VALUE_CHANGED → native User Action**：LVGL 9.4 tabview 在
   `button_clicked_event_cb`（lv_tabview.c:330，点自带 tab 栏按钮）和
   `cont_scroll_end_event_cb`（:376，**手势滑动松手落定**）都发
   `lv_obj_send_event(tv, LV_EVENT_VALUE_CHANGED)`，target 就是 tabview 本体。
   本工程 tab 栏 tabSize=0 不可能点，滑动路径就是唯一入口。
2. **DSL**：tabview 节点 `"onTabChange": "sync_rail_main"`（json2eez 新增 handlerType:"action"
   的 VALUE_CHANGED handler，与 onAction 同款直调）；顶层 actions[] 声明 native 动作。
3. **native 实现**（src/native/native_actions.cpp）：`lv_tabview_get_tab_active(tv)`
   读 idx（LVGL 9.4 没有 _get_active，§11.10.4），按索引表
   `rail_set_checked()`：main 0..3 ↔ m_nav_chat/music/bell/tune（含 navmk）；
   sett 0=通用(无) 1=wifi 2=sun 3=mic。**rail 索引表必须与 add_tab 顺序一致**。
4. **★ animated:false 铁律（本轮最大的坑，P-0029）**：程序切页
   （EEZ 链 tabviewSetActiveTab / sim 的 lv_tabview_set_active）**必须 animated:false**。
   `true` 时 lv_tabview_set_active 起 180ms 滚动动画，动画未完又来下一次切换/事件时，
   tabview 的 SCROLL_END 处理器拿 `lv_obj_get_scroll_end`（**旧动画目标位**）算出
   **旧 tab**，`set_active(旧值)` 把页面拉回去、再发 **VALUE_CHANGED(旧值)**——
   表现为「高亮/页面整体慢一拍」（sync 收到 idx=2 而刚切到 1，off-by-one；
   冒烟实测 `rail@tab1: bell=1 music=0`）。改成 false 后：程序切换即时完成、
   SCROLL_END 恒有 t==tab_cur → 不再发事件；**手势滑动仍由 LVGL 滚动自然跟手动画**，
   松手 SCROLL_END 拿新鲜 t 发 VALUE_CHANGED → sync 正确跟随。
   行业惯例亦然：点导航即时切，滑动才动画。**别用「加长等待时间」掩盖竞态**。
5. **验收必须加运行时断言**（sim.py click_smoke_test 扩展）：
   `set_tv_layer()` 切页后 dump 四项 `lv_obj_has_state(obj, LV_STATE_CHECKED)`，
   断言恰好一项为 1（0100/0010…）。G5 截图对照会掩盖单项错位（§11.8.6 同理）。

#### 二、下拉浮层（dropdown / popup）通用模式

诉求②的「点无线网络弹下拉，不推挤其他行」。EEZ 原生做法（json2eez 新增
onShow/onHide → 内置动作 id:16 objClearFlag / id:15 objAddFlag，flag=HIDDEN）：

1. **结构**：浮层 = 两兄弟节点挂内容区容器末尾（z 序天然最高）——
   `pop_bg` 半透明遮罩（盖内容区，点击=收起）+ `pop` 卡片（标题/关闭/列表/扫描）。
   **不进任何会随滚动/推挤的流式布局**，绝对定位，出现时零位移。
2. **DSL**：触发体 `"onShow": [pop引用, pop_bg引用]`（显示=clear HIDDEN）；
   每个收起入口（关闭按钮/遮罩/选中的网络行）`"onHide": [pop, pop_bg]`（隐藏=add HIDDEN）；
   浮层两节点 `hidden: true`（codegen `lv_obj_add_flag(HIDDEN)` 初始收起）；
   json2eez 把每处编译成「CLICKED connectionLine + 单 LVGLActionComponent 多 actions」。
   **onShow/onHide 与 onAction/goto/switchTab/onClick 互斥**（json2eez 有守卫）。
3. **可点击性**：json2eez `default_clickable = wtype not in ("label","arc")`——
   **container 默认可点**，遮罩 box 不用显式 clickable；行/关闭用 button() 天然可点。
4. **★ 验证认知（别再被 grep 坑）**：flag 动作和 SetVariable 一样走
   「组件数据 + eez-flow.cpp 运行时解释」，**不会**在 screens.c 出现
   `lv_obj_add_flag(HIDDEN)` 字面量（grep HIDDEN screens.c=0 是正常的）；
   真值在 test.eez-project 里（grep `"flag": "HIDDEN"` 应 = onShow 目标数 + onHide 入口数×2，
   本工程 2+12=14）。**最终以仿真运行时断言为准**（has_flag(HIDDEN) 翻转）。
5. **验收断言**（sim.py）：点行 → `has_flag(pop,HIDDEN)==0 && bg==0`；
   点关闭/遮罩 → 都回 1。实测三连全过。

#### 三、自查方法论（用户③「希望有些问题你自己检查」的落法）

- **先读生成物再下结论**：本轮一开始就误信了「screens.c 无 HIDDEN = 动作没生成」，
  实际是表示层不同；反例教训同 §11.10.3。
- **编译 ≠ 行为**：native C 编译链接通过（sim build 0 error）只说明引用合法；
  高亮 off-by-one 是运行时竞态，**只有运行时断言能抓到**。
- **调试闭环**：native 动作里临时 printf(idx/指针) + 冒烟 dump 全部四项状态
  （只断言两项时恰好漏看 bell=1，差点误判）→ 一次复跑定位根因 → 修上游
  （json2eez animated:false）→ 复跑全绿 → 移除临时 printf。

### 11.16 switch 两态样式：OFF 态也要分化（2026-09-30）

**症状**：开关打开是蓝色（对），关闭还是蓝（应灰）。
**根因**：DSL 里 INDICATOR 的 DEFAULT 与 CHECKED 都写了 on 色。LVGL 开关
OFF 时画的是 INDICATOR 的 **DEFAULT** 样式 —— 两态同色 = 关闭态看不出变化。
**修法**：MAIN / INDICATOR 都按状态写：DEFAULT=off 色、CHECKED=on 色；
KNOB 恒白即可。只写 DEFAULT 会被主题 CHECKED 盖住（§428 track 同坑），
所以**两态都必须显式写**。
**验证坑**：静态稿若所有开关都是同一状态，截图无法验证另一态 —— 临时把
一个开关置反跑 `--shots` 截图确认后还原。同屏放一开一关对照最直观。

### 11.17 换页高亮同步纯 EEZ flow 化：user action 退役 + asar 序列化四要点（2026-09-30，实战复盘）

P-0029 用 native User Action 实现的滑动高亮跟随，被用户铁律推翻、重做为纯 EEZ flow。
本节是重做的完整配方（intake P-0030 / PR-0057）。

#### 一、★ 选型铁律（用户 2026-09-30 定稿，原话存档）

> 「后期要求优先输出用EEZ里面控制UI，包括各个控件的联动，仅仅控制外部硬件的允许使用
> 用户代码，如果实在没有办法的话，需要通知我」

落成选型判据：
- **UI 控制 + 控件联动**（高亮/显隐/样式/切页/联动）→ **EEZ 优先**：flow 链、
  LVGL 内置动作、状态样式（DEFAULT/CHECKED…）。
- **外部硬件控制**（发命令给 wifi/音频/RTC/传感器）→ 用户代码（A 通道 user action /
  B/C 变量，见 §11.14）。
- **EEZ 实在表达不了** → **先通知用户**，不要默默走 native。

判例：高亮同步 = 控件联动 → EEZ；`mic_toggle` 命令 = 硬件 → user action。
「EEZ 能不能表达」拿不准时先做 asar 取证（下）再选型，别凭直觉走捷径。

#### 二、纯 EEZ flow 同步链结构（替代 §11.15 的 native sync_rail）

```
tabview VALUE_CHANGED (handlerType:"flow", userData:0)
  → LVGLActionComponent ①: objClearState(CHECKED)×N + tabviewGetActiveTab(result=页面局部变量)
      ── @seqout（① 全部 actions 执行完才传播）──→
  → CompareActionComponent(局部变量, i, "=")   ×每个非空页码 i
      ── True → LVGLActionComponent ②: objAddState(CHECKED)×第 i 组
```

要点：
- 连线：tabview → ① 用 output `VALUE_CHANGED` / input `@seqin`；① → Compare 用
  `@seqout`；Compare → ② 用 `True`（boolean 序列输出的连线名就叫 True）。
- 空组（如 sett 索引 0=通用左栏无对应行）跳过，不建 Compare/AddState 组件。
- 局部变量写 `page.localVariables`：`{name, type:"integer", defaultValue:"0"}`；
  表达式里裸名即按局部变量解析。
- 本工程产物：Main 页 LVGLActionComponent×28 + CompareActionComponent×7，
  连线 CLICKED 19 / VALUE_CHANGED 2 / @seqout 7 / True 7。

#### 三、asar 序列化四要点（写 DSL 编译器的硬依据）

1. **assignable 参数没有 Type 后缀**：LVGL 动作类工厂
   `e.isAssignable || (o[e.name+"Type"]="literal")` —— 只有非 assignable 参数才写
   `<nameType>:"literal"`；`tabviewGetActiveTab` 的 `result` 就是裸表达式字符串，
   误加 `resultType` 会破坏序列化。
2. **CompareActionComponent**（flowComponentId 1009）：A/B/C 是 makeExpressionProperty
   裸串；operator 用枚举字符串 `"="`；输出 @seqout / True / False。
3. **@seqout 传播时机**：eez-flow.cpp `executeLVGLApiComponent`（4188–4196）末尾才
   `propagateValueThroughSeqout` —— 同组件全部 actions 执行完才向后传播，
   下游 Compare 读到的变量一定已写好，无需手工排序。
4. **局部变量**：`page.localVariables`（Flow.typeClass=Variable）。

取证方法：解包 EEZ Studio 的 asar，看动作类定义（`isAssignable`）与
CompareActionComponent 定义 + 运行时 eez-flow.cpp 对应分支；用 Studio 手搭一条
最小链保存后对照 JSON。**先取证再写编译器 —— 取证充分则零试错。**

#### 四、DSL 与代码归属变化

- `onTabChange` 从字符串动作名升级为结构化：
  `{"tv_ref":…, "var":"main_page_idx", "clear":[…全部要熄的控件…],
    "add":[[第0页组],[第1页组],…]}`（与 onAction 互斥，json2eez 有守卫）。
- `build_ui.py` 里 clear/add 都写**解析后的最终 id 串**（`_resolve_switchtabs`
  统一处理，注意 prefix_ids 前缀坑 → P-0027）。
- **native 退役要删干净**：DSL actions[] 声明、native_actions.cpp 函数、
  （自动再生成覆盖）三处同步删，留墓碑注释指路 json2eez 的 onTabChange 注释。
- screens.c 的 VALUE_CHANGED 分支正确形态是
  `flowPropagateValueLVGLEvent(flowState, <componentIndex>, 0, e)`；
  再见到 `action_*` 直调就是还有残留。

#### 五、验收（沿用 P-0029 建立的运行时断言，一个不改）

6 条 [swipe] 断言（确定性滑动 `lv_obj_scroll_to_y + SCROLL_END + pump(60)`）：
main tile 跳转 0/1000→1/0100→0/1000；sett 上滑 1/100、下滑 0/000。
外加 11 屏视觉对照（本轮 8.59% < 25% 阈值）。**重构不改行为时断言一字不动，
本身就是「重构等价」最硬的证明。**

#### 六、方法论：为什么当初走了 native、以后怎么避免

- 当初「不确定 EEZ 能不能表达」就直接走 native —— 正确顺序是**先取证（asar 序列化
  / Studio 手搭对照）再选型**；拿不准就通知用户，别默默扩大用户代码面。
- 铁律的本质：**EEZ 工程要能脱离开发者自解释**（打开 Studio 能看到全部 UI 逻辑），
  用户代码只留机器边界（外部硬件）。这条比「少写代码」更重要。

### 11.18 ★ 声明式显隐 hiddenExpr：状态机 UI 的正解（2026-09-30，网络页实战）

§11.17 的选型铁律往前推了一步：**「状态 → 界面」切换根本不需要 flow 链，也不需要
user action，EEZ 自己就有声明式开关 —— hiddenFlag 表达式（`hiddenExpr`）。**

#### 一、机制（asar / 生成代码实证）

DSL 节点加 `hiddenExpr="<表达式>"` → 工程 JSON 写
`hiddenFlagType:"expression"` + `hiddenFlag:"<表达式>"`。EEZ Studio build 在
`tick_screen_<page>()` 生成：

```c
bool new_val = evalBooleanProperty(flowState, 464, 3, "Failed to evaluate Hidden flag");
bool cur_val = lv_obj_has_flag(obj, LV_OBJ_FLAG_HIDDEN);
if (new_val != cur_val) lv_obj_add_flag(obj, LV_OBJ_FLAG_HIDDEN);   /* 或 remove */
```

**每帧求值 + 自动 add/remove HIDDEN。** 硬件侧只改 native 输入变量，界面自己切画面，
**UI 逻辑零用户代码** —— 铁律下「控件联动」的最优解，优先于 flow 链（更声明式、
工程里一眼看得见、不用建 Watch/Compare 组件）。网络页一次落了 54 处。

- 表达式引用的变量**必须在 `ui.json` 的 `variables[]` 声明**，否则 build 找不到变量。
- 引擎支持 `== != < > <= >= && ||`（`eez-flow.cpp` 表驱动 `do_OPERATION_TYPE_*`）。
- 改 hiddenExpr 后**必须重跑 `all.py` 全链路**（只有 build 才会把表达式编进
  `evalBooleanProperty`），只改 ui.json 不 build 是没用的。

#### 二、★ 四个坑（都实测踩过，症状 → 原因 → 规则）

| # | 症状 | 原因 | 规则 |
|---|---|---|---|
| 1 | 两个**本该互斥**的控件同时显示、叠字 | 表达式写成 `"A \|\| (%s)" % cond`（给子条件顺手加括号），落盘被再包一层成 `"A \|\| !(!(B && C))"` → 判定恒真/恒假 | **禁止嵌套括号**：只写扁平 `&&`/`\|\|` 串；分组结果**预先展开**成 `!X && !Y && !Z`；`!` 直接贴比较式写 |
| 2 | 文字骑在 pill 上（如「连接超时」压在「重试」上） | `pill()` 返回的 `w` 是**给 `x=0` 锚点**算的；先 `shift` 再用 `fw` 反推邻居位置 = 算进 pill 内部 | 顺序固定：**先 `pill(0,0)` 拿 w → 用 w 反推 `pill_x = rx - w` → 最后才 `shift`**；邻居用 `pill_x` 定位 |
| 3 | 右对齐的文字右边缘飘 1~2px | `label_right(rx,…)` 内部按 Pillow 量宽反推 x，与实渲有差（`…` 更明显） | 严格右对齐用 `label(rx - tw(text, px), …)`，别用 `label_right` |
| 4 | 一次点击发了**两条**命令 | 行容器绑 `action`，行内失败态「重试」pill 也绑同一 `action` → 事件冒泡触发两遍 | 行容器**纯展示不绑动作**；另加一层 `bgOpa=0` 的**透明热区按钮**铺满整行负责点击，与行内按钮的 hiddenExpr **互补**（失败态让位给 pill） |

#### 三、状态机页配方（网络页模板，其他硬件页照抄）

```
状态：wifi_state 0 列表 / 1 扫描中 / 2 连接中 / 3 已连接 / 4 失败
      wifi_conn_slot 当前槽位     wifi_slot{i}_ssid/_sub/_rssi/_lock  ← 5 个固定槽
```

- **EEZ 生不出不定长列表** → 结果列表**必须预置固定槽位**；空槽 = `ssid == ""`，
  UI 用 `wifi_slot{i}_ssid == ''` 自动藏掉那行 + 那条分隔线。
  **槽位数在 DSL（`NET_SLOTS`）和 native（`APP_WIFI_SLOTS`）两处，必须同步改。**
- 归属分层（对齐 §11.14 双通道）：
  - 状态切换 / 显隐 / 样式 → **hiddenExpr**（EEZ，零用户代码）
  - 真扫描 / 真连接 / 断开 → **User Action**（函数体只有一行 `app_set_output`）
  - 结果回显 → **native 输入变量**（`app_set_input_*`，UI 只读）
- native 侧省事写法：槽位变量函数对**用宏生成**（`WIFI_SLOT_ALL(i)`）；
  `pick` 用**一个**输出枚举 `APP_OUT_WIFI_PICK` + 槽位号，**不要 5 个枚举**；
  `app_model.cpp` 的字符串输入缓冲按 **id 直接索引**（`g_in_str[APP_IN_COUNT][64]`），
  **不要靠 `id - 基准值` 算下标** —— 加字段必然串位（旧代码只认 2 个串）。
- 运行时才填入的字符串必须**预先用 `glyphs=` 收字形**（网络页 `NET_GLYPHS`，
  含中文错误原因 + `·` 分隔符），漏了就是豆腐块。
- **中间态截图**：仿真的 `shoot()` 每屏只拍一张，扫完/连完就回列表态，**拍不到
  扫描中/连接中/失败**。做法：`platform/io_pc.cpp` 认环境变量
  `EEZ_SIM_STATE=<n>[,slot]` **钉住**状态（`s_pinned` 让时间推进不再改状态）。
  - Windows 下 `getenv` 读不到 shell 设的环境变量，**先 `_putenv("")` 刷新 CRT 环境**。
  - 手动跑 exe 需把 `SDL2.dll` + `libstdc++-6.dll` + `libgcc_s_seh-1.dll` +
    `libwinpthread-1.dll` 拷到 exe 同目录，否则 missing shared libraries。
  - 出图目录参数必须是 Windows 风格路径（`C:/…`）；`/foo` 会被当根路径解析而静默失败。

#### 四、验收

`all.py --shots` 全绿（EEZ build **No error and no warning**、11 屏出图、
6 条 swipe 断言全过）+ 四态截图核对（列表+已连接 / 扫描中 / 连接中 / 失败+重试）。
**状态机的正确性靠「四态出图逐张看」，不是靠断言** —— 断言只覆盖点击链是否闭环。

### 11.19 设置页布局铁律：外置左栏让位 `RAIL_W+206` + 对照门禁的均值盲区（2026-09-30，P-0032）

#### 一、几何契约（不可变）

- 设置左栏 `rail_cats()` 是**外置单实例**（§11.9 tab pager 规则），固定盖内容区左侧
  `[CONTENT_X, CONTENT_X+206]`（= 76..282）。
- 设置三子页（通用 / 显示 / 唤醒）的 pane 一律
  `place(pane_xxx(SW, CONTENT_H), RAIL_W+206, SB_H)`，`SW = CONTENT_W-206`（=518），
  内容占 282..800。
- 为什么容易踩：撤掉某个子页时「没有子页了 → 内容占满内容区」的直觉是**错的** ——
  左栏是外置的、不在 tabview 里，它永远占着左侧 206px，跟 tabview 有几页无关。

#### 二、症状

内容 76..594，左半压在 rail_cats 分类列表上（两组文字叠字），右缘 594..800 空一截。
07 / 08 / 09（背景）/ 10 四屏同病（同一条链路生成的三张设置子页 + 以它为背景的浮层）。

#### 三、两层门禁为什么都没拦住（重要方法论）

1. `check_bounds`（json2eez）只查「**子超出父**」，不查「**兄弟重叠**」——
   「内容压左栏」对它是合法结构。
2. `compare.py` 对照门禁只看 **11 屏平均**明显差异（阈值 25%）：单屏结构性错位
   只把 07 拉到 12.90%，均值 10.05% 照样绿。
3. **结论：数字绿 ≠ 画面对。出图必须分区放大目检**（浮层 / 遮罩压暗的背景也要看，
   不能只看主角控件）。修复后回归：07 12.90→6.54%、08 →7.65%、10 →6.47%，
   平均 10.05→8.62%。

#### 四、修复形态

```python
SET_X = RAIL_W + 206   # 外置 rail_cats 盖住左侧 76..282，内容让位
set_gen["children"]  = place(pane_settings(...), SET_X, SB_H, "set_")
set_disp["children"] = place(pane_display(...),  SET_X, SB_H, "disp_")
set_wake["children"] = place(pane_wake(...),     SET_X, SB_H, "wake_")
```

同构的隐藏钉态页 / 截图页要**一起改**（x 同步 +206、w 收成 SW），否则
`check_bounds` 会拦「282+724=1006>800」。

#### 五、点亮组完备性（2026-09-30 深夜补充，P-0034）

滑动同步链是「clear 全部 → 按页分组 add」——**每个 tab 的点亮组都不能留空**，
否则滑到那页就全灭：

- **无子页的入口行（pop，tab=None）必须显式归入它语义上归属的页**。
  本工程「网络与连接」行 = 通用页（tab 0）的点亮项（设计稿初始 `checked` 也是它）。
  曾以为「没有子页就不参与高亮」→ 滑回通用页左栏全灭（用户报
  「wifi 页 tab 有时候没有高亮」：首次进设置亮、滑一圈回来灭）。
- **pop 行点击不动高亮**：它是浮层入口不是页面入口，switchTab 不挂 clear/add
  （json2eez 按 `or []` 生成空动作链，只剩 onShow）——在显示/唤醒页点它开浮层，
  左栏不跳蓝，高亮始终跟随页面。
- **断言期望值来自设计推导，不能把现状打印出来抄**：sim.py 曾把
  `(expect 0 / 000)` 写进 swipe 断言并注释「wifi 不参与高亮」——
  等于把 bug 固化成验收标准，冒烟永远绿。修复后 down 期望 `100`。

### 11.20 DSL 结构不变量：tab 只能是 tabview 的直接子对象（2026-09-30，P-0033）

#### 一、规则与取证

- EEZ 规定 `LVGLTabWidget` 必须挂在 `LVGLTabviewWidget` 下。Screen 直下挂 tab，
  GUI 打开工程报
  **`Invalid position of Tab widget inside Widgets Structure`**。
- **headless CLI build 不做这层结构校验**：编过、仿真正常、对照全绿 ——
  「**headless build 过 ≠ 结构合法**」。DSL 生成端（build_ui / json2eez）要
  自己保证结构不变量，不能指望 EEZ headless 帮你查。

#### 二、案例：四张「钉态」隐藏页的始末

- 当初为给仿真脚本提供「干净背景出图」，往 Screen 直下挂了 4 张隐藏 tab
  （显示/唤醒/通知/浮层 · 钉态）。
- 复盘发现 `m_shot_*` 在 sim.py / 冒烟脚本里**零引用**：四态图实际走 §11.18 配方
  （真实页 + `EEZ_SIM_STATE` 钉态钩子）—— 钉态页是废弃中间方案 + 死代码
  （ui.json / 生成 C 白多约两千行），且正是它们触发 GUI 结构报错。**整体删除**。
- **以后再要「干净背景截图页」**：包进一个**隐藏 tabview**（tabSize=0、页填满内容区）
  或改普通 container，不能裸挂 Screen。

#### 三、校验手法

遍历工程 JSON，断言每个 `type:"LVGLTabWidget"` 的 parent type 是
`LVGLTabviewWidget`（本次手工执行：13 tab / 4 tabview / 违例 0）。
**遗留建议**：把该断言做进 `json2eez.py` 的 check_bounds 邻位，成为常驻门禁。


### 11.21 ★ 绑变量的滑杆：`get_var` 与 `set_var` 必须指向同一块内存（2026-10-03 真机确认，`intake/P-0110`）

EEZ 对"值绑了变量"的滑杆，生成的代码**每次刷新**都执行回写（实测 `src/ui/screens.c:9494-9501`）：

```c
int32_t new_val = evalIntegerProperty(...);          // 走 get_var_xxx()
int32_t cur_val = lv_slider_get_value(objects.m_np_vol);
if (new_val != cur_val) {                            // 只要不等就写回控件
    tick_value_change_obj = objects.m_np_vol;        // 反环标记：这次写入不再触发 set_var
    lv_slider_set_value(objects.m_np_vol, new_val, LV_ANIM_OFF);
}
```

⇒ 用户手点到 25 之后，只要 `get_var` 读到的还是旧值，**下一帧绑定就把滑杆打回 42**；
命令通道随后把值改成 25，控件再跳回来 —— 现象就是"跳到目标 → 弹回旧值 → 再跳到目标"的闪烁。

**铁律**：`set_var_X()` 写哪儿，`get_var_X()` 就必须读哪儿。
两边读写的若不是同一块内存，任何"事件写 A、刷新读 B"的错位都会被这行回写放大成可见闪烁。
本工程的落法 = 两边都走统一设置表 `g_set`（`src/native/app_settings.h`）：

```c
void    set_var_volume_pct(int32_t v) { g_set.volume = v; app_set_output(APP_OUT_VOLUME_SET, ...); }
int32_t get_var_volume_pct(void)      { return g_set.volume; }   // ★ 不是 app_get_input_i(APP_IN_*)
```

三条附带教训：
1. **只补一半会看起来"没修好"**：第一轮只改了 `set_var` 写表（以为旧值不会再被发布），
   真机仍闪 —— 因为漏了"绑定读的是模型槽"这条独立路径。控件回写型 UI 要**两条路径一起改**。
2. **PC 仿真复现不出来 ≠ 没问题**：走路器 `getval`（`lv_slider_get_value`，本工程 LVGL 9.x
   **没有** `lv_obj_get_value` 符号）每 20ms 采样，修复前后都是"一路 25"。
   绑定 vs 事件是**亚帧竞态**，仿真的刷新顺序与真机不同 ⇒ 这类只能真机判定。
3. **`APP_IN_*` 槽不必删**：改成读表后，io 侧照旧发布（待机页等别的消费者还在用），
   只是不再当控件的真值源 —— 单一真值源指的是**读路径**，不是"只能有一份拷贝"。


### 11.22 ★ 借 `compile_commands.json` 做"真编译"取证的硬规矩（四条，2026-10-04，`intake/P-0113`）

背景：本机跑不了 `idf.py reconfigure/build`（`export.ps1` 在这台 PowerShell 上 `BadExpression` 直接失败），
但**每个源文件的真实编译命令**都在 `compile_commands.json` 里，借它做**单文件真编译**（保留 `-c` 与 `-O2`，
输出指向 scratch obj），比肉眼 review 强得多 —— 前提是别把"没编译"当成"编译通过"。四条：

1. **能 `reconfigure` 就先 `reconfigure`**（本机入口见下条 0），新文件才会进 `compile_commands.json`，后面全是官方命令，不必借。
   没有构建入口时才用「借命令」，此时**先确认它在不在清单里**（这条最容易翻车）：`compile_commands.json` 是 **cmake 生成物**，
   没 reconfigure 就不会收录新建的 `.cpp`；按文件名匹配不到时脚本会**静默跳过**，于是"0 错 0 警"是假的。
   **0. 本机 cmd 侧构建入口（用户给的 tasks.json 复刻，2026-10-04 实测跑通）**：
   `cmd.exe //C "design\\_idf_build.bat <reconfigure|build|size|flash|monitor>"`，包装里必须
   `set MSYSTEM=`（Git Bash 继承来的，`export.bat` 第 2 行见到就 `goto :eof` 静默拒绝）＋
   显式 `IDF_PYTHON_ENV_PATH=...\python_env\idf5.5_py3.11_env`（不指会按 PATH 猜成 py3.10 报 env not found）＋
   `set IDF_TOOLS_PATH=...` ＋ `set IDF_PATH=<idf 根>` 再 `call export.bat`，最后 `cd` 到 **IDF 工程根**（不是子工程目录）。
   两条禁忌：`idf_cmd_init.bat` **别带参数**（`%1` 以 `esp-idf` 开头会把 `IDF_TOOLS_PATH` 盖成参数值，报天书级「命令语法不正确」）；
   `.bat` 内**只写 ASCII**（UTF-8 中文注释被 GBK 切碎成垃圾命令，实测报 `'sks.json' 不是内部或外部命令`）。
   ```bash
   python -c "import io;t=io.open('<上级>/build/compile_commands.json',encoding='utf-8').read();print(t.count('io_weather'))"
   # 0 ⇒ 该文件对逐文件真编译完全隐形，必须借命令
   ```
   ⚠ 路径坑：IDF 的构建树在**工程上级**（`lvgl_demo_ai/build/`），子目录里的 `build/` 常是仿真产物，别找错。
2. **命令写进 `.sh` 再 `bash xx.sh`，绝不用 `bash -c "$CMD"`**。清单里的命令含 `\"` 转义引号
   （如 `-DIDF_VER=\"v5.5\"`、`@"...cxxflags"`），经 Python→CreateProcess→MSYS bash 二次转义后
   源文件参数会被吃掉，gcc 只报 `fatal error: no input files` —— 报的是"没有输入"，不是"找不到文件"，
   极易误判成路径写错。改造只动两处：`-o <原 obj>` 换成 scratch obj（**保留 `-c`，别换 `-fsyntax-only`**，
   见 `intake/P-0052`：`-fsyntax-only` 不跑 tree 优化器，抓不到 `-Wstringop-truncation` 这类警告）、
   结尾 `-c <src>` 换成目标文件；最后整体把 `\` 换成 `/`（`-DIDF_VER=\"x\"` 被顺手改成 `/"x"/` 无副作用）。
3. **补的 `-I` 要做反证**。兄弟文件的 include 集只覆盖它自己用到的组件，新头文件（如 `esp_http_client.h`）
   常缺目录；补完后**去掉补的 -I 再跑一次应当报错**（`fatal error: xxx.h: No such file or directory`），
   这才证明补齐是必要的、而不是碰巧过了。
4. **★ 新建「设备专属」文件后，必须再跑一次 PC 门禁**（本轮就是它抓到回归）。PC 仿真收 `src/native` 的方式是
   `file(GLOB_RECURSE)` + **按名字排除**（`common/PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt:27-30`，
   正则 `(io_esp|test_native)\.(c|cpp)$`）⇒ 新文件不在名单里就被仿真构建**捞去编译**，炸在
   `freertos/FreeRTOS.h: No such file or directory`。这与 `intake/P-0045` 是**同一对盲区的双向**：
   老坑 = io_esp 在 PC 根本不编（改动潜伏）；新坑 = 新加的设备文件在 PC **会**被编（你以为不会）。
   修法优先在**工程内自证身份**，别改那个多工程共用、又不在本工程 git 里的构建壳：
   ESP-IDF 必给 `-DESP_PLATFORM`、PC 仿真没有 ⇒ 文件体整体包 `#if defined(ESP_PLATFORM)`，PC 侧编成空翻译单元。

借来的命令只验到**编译这一层**（头文件 + 代码生成期警告）：**链接、体积、`REQUIRES` 齐不齐**要真机 `idf.py build`，
**两边构建是否都通**要 PC 门禁 `design/all.py --shots` —— 三者缺一不可，别拿其中一个盖另外两个。
留档脚本范式见工程侧 `eez-test/design/_verify_weather.py`（一次跑 6 个文件；有官方条目用官方条目、
没有才借 io_esp 的命令，含"去掉补的 -I 应当报错"的反证开关 `VW_NOEXTRA`）。
⚠ 借命令时**反斜杠归一化必须跳过 `\"`**：`re.sub(r'\\\\(?!")', '/', cmd)`。一把梭 `cmd.replace("\\","/")`
会把 `-DMBEDTLS_CONFIG_FILE=\"x\"` 改成 `/"x"/`，于是 mbedTLS 配置头加载不到，
报 `esp_crt_bundle.h: 'mbedtls_x509_crt' does not name a type` —— 看着像缺 `-I`，其实是**缺 define**。
（实测：借来的命令编 `io_weather.cpp` 就中过这一枪，官方条目 + 安全归一化后才 0 错 0 警。）


### 11.23 ★ 轮播/翻转态不进设置表也不进 NVS；断言要"比变化"不要"比值"（2026-10-04，`intake/P-0114`）

待机页天气卡收藏多城后要 8 秒自动翻一城、手动 ‹ › 即重置计时。两条口径值得单列，因为它们和
"统一设置表 + 周期比对变更"（`§11.21` / P-0108）看起来一致、其实相反：

1. **`view`（当前翻到第几个）是显示态，不是设置**：它每 8 秒变一次 ⇒ 塞进 `g_set` 就等于
   每 8 秒写一次 NVS（Flash 实打实的磨损），而且 `app_settings_tick` 的 `memcmp` 去抖
   对"周期性必然变化"完全失效（每次都判定"变了"）。⇒ 它是数据源模块的私有 static，
   表里只留真正跨重启要保留的 `wx_mask`。**判据：只有"用户会去调 + 要跨重启"的项才进统一表。**
2. **走路断言优先"比变化"而不是"比具体值"**：这条链上自动翻转随时会插进来（走路本身耗掉十几秒），
   认死"第 3 城 = 上海"必然假失败。写成 `A → 点 › → B≠A → 点 ‹ → 回到 A → 静置 8.6s → 又变`，
   三向都成立才算手动/自动/重置各自生效。
3. 附带：翻转/熄屏这类计时一律 `lv_tick_get()` + **有符号回绕比较**
   （`if ((int32_t)(now - due) < 0) return;`），别用墙上时间（P-0097 对时一跳就乱）。


### 11.24 ★ 外部 API 的响应形状必须当场抓一次；短动效用样式值断言，别用截图（2026-10-04，`intake/P-0114`）

天气"后来不再获取数据了"的根因不是网络，是我照记忆写的解析：以为 Open-Meteo 多地点返回
`{"current":[{...},{...}]}`，**实测**（直接抓一次那个 URL）顶层其实是**数组**、每个元素各自带一个
`current` **对象** ⇒ `cJSON_GetObjectItem(root, "current")` 在数组上返回 NULL ⇒ 勾 ≥2 城永远解析失败。
三条：

1. **能当场取证就别用记忆**：一次 HTTP 抓取就能定形状，成本远低于"上线后用户报障"。
   凡"我以为接口是这样"（对象还是数组、字段在顶层还是嵌一层、顺序是否等于请求顺序）都先抓一次。
2. **退避游标要记"尝试"，不是记"成功"**。写成"只在成功时更新游标"会让
   `changed = (want != 上次成功)` 在失败后恒真 ⇒ 60 秒退避被绕成**每 5 秒一次 TLS 握手**，
   还顺带撞限流。这两个 bug 是叠在一起才显得"完全不上数据"。
3. **几百毫秒的动效不要靠截图断言** —— 走路器 `shot` 之前还会再泵几帧，动画早播完了，
   图上看着就是"没效果"。加一条读样式的走路命令才是硬证据：
   `getrot <obj>` 打 `lv_obj_get_style_transform_rotation / transform_scale_x / opa_layered`，
   换城后 80ms 采到 `rot=-50 scale=219 opa=179`、播完采到 `0/255/255` ⇒ 既证明在跑，也证明能归零。
   顺带一条 LVGL 9 事实：**transform 是"对象 + 整棵子树"画进中间层再整体变换**
   （`src/core/lv_refr.c`：`lv_obj_redraw(new_layer, obj)` → `lv_draw_layer(..., rotation/scale/skew)`），
   所以给容器加 transform 会带着子控件一起动，不用逐个对象刷；
   但那张中间层是 ARGB 的（本工程天气卡 290×128 ≈ 148KB/帧）⇒ **短时可用、别常驻**，
   嫌重就降时长/降角度（本工程两个宏：`WX_ANIM_MS` / `WX_TILT_DEG`）。


### 11.25 ★ 定任务栈之前，先算它每个函数的最大局部对象（2026-10-04 真机崩溃，`intake/P-0115`）

`xTaskCreate(fn, "ui_sd_scan", 6144, ...)` 配一句 `sd_snap_t s;`（`char names[64][96]` = 6152B）
= 局部变量比整个栈还大 ⇒ 真机 Core0 **Stack protection fault**，崩点还落在被调函数里
（`bsp_sdcard_mount`），看起来像"别人的锅"。三条：

1. **小任务（<8KB）里出现 >1KB 的局部对象就是定时炸弹**：一律改 `static`（单线程用）或 heap。
   编译器不警告、静态检查不报、**PC 仿真根本不编这段代码** ⇒ 只有真机会炸。
2. **手算一遍再定栈**：把调用链上每个函数的最大局部量加起来（FatFS 挂载 + `opendir` 还要几百到上千字节），
   别照抄"看起来差不多"的数（本工程 io_weather 用 8192 是因为里面有 TLS）。
3. **留一条真实用量**：一次性任务收尾打
   `ESP_LOGI(TAG, "stack min free = %u bytes", uxTaskGetStackHighWaterMark(NULL) * sizeof(StackType_t))`，
   下次烧完直接看数字，不用再来回猜。
4. 解码崩溃的固定动作：`Stack bounds` 相减 = 实际栈大小，和 `xTaskCreate` 的数一比，
   再和函数里最大的那个局部量一比 —— 三个数字对上，根因就出来了（这次 6136 vs 6152）。


**补一条同型判据（真机 Store access fault 定位法）**：崩在 `memcpy` 且 `A0/MTVAL` 是个小常数
（如 `0xc`）时，先怀疑 `NULL + 结构体字段偏移` —— 去查那个偏移等不等于某个 header/struct 的
`sizeof`（本次 `esp_payload_header` packed = 12 ⇒ `copy_buff == NULL`）。
再查该缓冲来自哪块内存：esp_hosted 的 `MEM_ALLOC` 带 `MALLOC_CAP_INTERNAL|MALLOC_CAP_DMA`，
**PSRAM 再大也不相干**；所以"加功能后偶发网络崩溃"要先算自己往内部 RAM 里塞了多少静态数组/任务栈。
另外：release 下 `assert()` 会被编掉，驱动里 `assert(p); *p = ...` 这种写法等于把 panic 留给你。

