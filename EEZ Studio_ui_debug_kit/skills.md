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
| **B 对照查验** | 秒级静态体检 + 命中仿真，把踩过的坑变成断言 | 秒 | 坐标偏移、字体回退、点击被遮挡、真机编译失败 |
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
        L2 命中仿真 ◄──────────────────────┘              │
        L3 真点击（仿真器）◄────────────────────────────────┘
        L4 真机烧录
```

| 层 | 命令 | 拦什么 | 何时跑 |
|---|---|---|---|
| **L1** | `python ui_debug_kit/tools/run_gate.py` | 静态可查的一切 | 每次改完设计源 |
| **L2** | 含在 L1 的 G1/G2/G3 | 见 §6 | 每次改完设计源 |
| **L3** | 见 §5 | 真点击行为 | 提 PR 前 / 发版前 |
| **L4** | `idf.py build flash` | 硬件相关 | 发版 |

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
    sim_nav.py             命中仿真（由配置挂到门禁 G3）
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
python design/eez_build.py               # 3. 生成 screens.c（会删掉 ui_font_*.c）
python design/gen_fonts.py               # 4. 重新生成字体 C
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
| G2 | `design/check_nav.py`（配置挂载） | 跳转三要素、死链、跳自己、可达性、死胡同 |
| G3 | `design/sim_nav.py`（配置挂载） | 按 LVGL 命中规则，逐按钮验证「点下去命中的是谁」 |
| G4 | `ui_debug_kit/tools/tree_check.py` | 几何越界、文本折行、字体缺失、墨迹异常 |
| G5 | `design/compare.py`（配置挂载） | 设计稿 vs 实机逐屏对照：缺屏或平均差异超阈值即阻断 |

G2/G3 是**本工程专属**脚本，留在 `design/`，由 `ui_debug_kit.config.json` 的
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

L1/L2 都是「算」出来的，能抓几何与结构问题，但抓不到**真实运行时行为**。
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

### 5.6 零点击出图：逐屏快照（把 L3 做成可自动跑的截图流水线）

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
| G2 | 跳转体检 | 三要素完整 / 无死链 / 无跳自己 / 可达性 / 死胡同 | 无 ERROR |
| G3 | 命中仿真 | 每个跳转按钮中心点下去命中的是它自己 | 0 遮挡 0 落空 |
| G4 | 通用体检 | 几何越界 / 文本折行 / 字体缺失 / 墨迹异常 | 全部通过 |

### 6.3 R 段：发布前条例（真机）

| 编号 | 条例 | 说明 |
|---|---|---|
| R1 | 全量真点击通过 | L3 跑出的报告 0 FAIL |
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
python design/check_nav.py                       # 跳转体检
python design/sim_nav.py Main                    # 某屏命中仿真

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

## 11. 实测补充（2026-09，EEZ Studio 0.29 / 800×480 / LVGL 9.4）

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

### 11.4 仿真器出图（把 L3 变成可自动跑的截图流水线）

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
