# CHANGELOG —— 工具箱迭代记录

> 约定：只往前追加。方法论被推翻时不要删旧条目 —— 在同一版里写清"改了什么、为什么改"。

> 版本号：全库**单调递增**，新条目取文件里当前最大号 +1，不再另开第二条序列
> （2026-11-04 发现 v0.9.53~57 曾被两套并行计数撞号，v0.9.61/62 是那次更正）。
>
> 注意：本文件描述的是**工具箱自身**的演进。工程专属的构建流水线、屏名、字体等
> 不属于工具箱，请写在工程侧的文档里。
> 版本号更正：本条与上一条先前误编为 v0.9.57 / 未编号；本 CHANGELOG 有两条并行序列，最高已到 v0.9.60，故顺延为 v0.9.61 / v0.9.62。PR-0444 里写的「v0.9.57」指本条。
> 注：具体换算实现（`to_relative()` / `check_bounds()`）属工程侧，
> 不进工具箱；工具箱沉淀的是**规则与判据**。
> 注：`design/` 那套生成脚本（DSL 构建 / 转换 / 仿真器适配 / 对照）属于**工程侧**，
> 不进工具箱；工具箱只沉淀**通用断言与案例**。
> 注：具体部件类型（switch 等）与其开关映射属于**工程侧**的设计源/生成器，
> 不进工具箱；工具箱只提供这条通用断言。

---

## v0.9.169 — 动态条目区（H5 标出 + 设计原则，PR-0583）

- 设计原则：数量随程序变化的列表（Wi-Fi 扫描结果、设备、通知、动作/定时）设计期
  **只框区域、不画任何对象**；条目不进设计源/EEZ，运行期由应用代码创建。
- H5 模板 `tools/h5_overview_template.py`：`pages.py:DYN_ZONES` 驱动青色虚线框 +
  「动态区 · 运行期由应用代码生成」，右栏清单单列「动态条目区」；生成器 assert 页存在/框不越界。
- w78 落地 5 处：Wi-Fi 网络列表、全部设备、通知中心、场景详情、灯详情定时；固化条目全部删除
  （831→762 控件）。NO_FLOW §2.1、reference/14 同步；四件套 PASS、NAV 64/64、D5 平均 98.70%。

## v0.9.168 — 共用布局自查 tools/layout_check.py（PR-0582）

- 新增 `tools/layout_check.py`：L1 越界/零尺寸、L2 结构控件部分重叠、L3 identifier 重复、L4 D5 相似度门槛。
- w78 `eez_check` 内置 A15；修 `detail_camera` 控件框 460×300→252（原压住下一行 53%）。NO_FLOW §2.2c、P-0262。

## v0.9.167 — 流程写死「改完 EEZ 必须当场编译四件套」（PR-0581）

- 用户令：改了 EEZ 就要编译确认无错误，每次必须执行、不得遗留；并要求写进**经验库流程**（不只 AGENTS）。
- NO_FLOW 新增 §2.2c：`cli_build`（0 错 0 警）→ 字体补烘 → `gcc -fsyntax-only`（screens/ui/styles/images）
  → `eez_check`（A1–A14）四项全绿才算做完；禁止只改不编译、报错绕过、把红色结果留到下一轮；
  汇报必须贴四项结果。FLOW §2 加同口径指针。

## v0.9.166 — 记录 EEZ 滑块/开关的默认样式与旋钮尺寸口径（PR-0580）

- 用户验收 w78 滑块效果后要求把默认样式写进工作流。
- NO_FLOW §2.2 新增口径（依据 LVGL 9.4 `lv_slider.c` / `lv_switch.c` 源码）：
  **旋钮直径 = 控件高度 + KNOB 的 `pad_*`**（`width/height` 样式不参与、EEZ 也不生成）；
  **轨道高度 = 控件高度 − MAIN 的 `pad_top/pad_bottom`**，默认贴顶、上下相等才居中。
- 实测配方：20px 高滑条 + `MAIN pad=7/7` → 6px 轨道居中；`KNOB pad=-2` → 16px 旋钮（便于点击）；
  开关轨道 44×24 + `KNOB pad=-2` → 20px 旋钮，触摸区用透明容器承载。
- 效果：w78 D5 平均 98.57%（灯详情 96.40→98.37，客厅 97.05→97.72），剩余差异为字体。

## v0.9.165 — 新增「控件可改属性总表」并写死字段白名单（PR-0579）

- 用户令：结合 EEZ 手册，逐控件记录「EEZ 前端 UI 能改哪些属性字段」，输出 md 表；经验库后续生成
  EEZ 工程必须按该表取字段，记录要详细。
- 新增 `reference/16_widget_properties.md`（约 32KB）：36 类 LVGL 控件 + Screen，逐类型列出
  **属性名 / UI 显示名 / 类型 / 枚举可选值 / 模板默认值 / 属性面板分组 / 条件显隐**；
  另含通用 27 项、`widgetFlags` 18 个复选框、`states` 复选框、`<属性>Type` 表达式选择器、
  Style 面板口径与 5 条生成器硬约束。
- 三方来源交叉核对：EEZ Studio 5.x `app.asar` 的 `classInfo.properties`（属性面板渲染真值）、
  官方手册 W 章节（`05/06` 提炼版）、`eez-widget-templates/templates` 落盘字段；
  校验脚本确认**模板落盘字段 100% 被表覆盖**（0 缺失）。
- 规则落地：`reference/README.md` 索引、`eez-widget-templates/README.md` 硬规则、
  NO_FLOW §2.2 生成段落、`AGENTS.md` 铁律 8 均写死「可改字段以 16 表为准，表外字段不得写」。
- **复核（用户要求“不得随意捏造”）**：脚本逐行比对 168 行 → 属性名双向 0 差异、枚举值/模板默认值
  逐字一致、臆造字段 0。为守口径去掉了上一版的两处推断：①未在 classInfo 显式命名的属性不再补显示名，
  统一写「—（未命名）」；②数字型 `type` 保留 classInfo 原值，不翻译成中文类型名。
- **§5 未收录清单（5 类，明确原因）**：①humanize 生成的显示名；②`PropertyType` 枚举名；
  ③Style 属性 × 控件/Part 可见性矩阵（只给全量 114 项目录，未逐控件裁剪）；④`eventHandlers`/`timeline`/
  `customInputs`/`customOutputs` 的条目子结构；⑤条件性才出现的字段规则（Keyboard `textarea`、Tab `tabName`、
  `hiddenFlag=true` 等）。均写明“需要时回 EEZ UI 确认后回填”。
- **§6 字段补充流程**：查手册（W 章节）→ 在 EEZ UI 里拖出控件/改出属性并逐项看枚举 → UI 保存 →
  `extract_templates.py` / `validate_templates.py` → 读模板落盘值 → 回填本表并重跑复核 → 用于生成器先过 A14/A10。
  明令禁止脚本拼字段、脚本改 `.eez-project`、按 classInfo 片段猜值。
- **全仓工程回查（2026-11-06）**：扫仓库内 26 个 `.eez-project`、**1821 个控件**，
  逐控件比对字段与 Style 键 → **未知类型 0、表外字段 0、表外样式键 0**（Flow 动作组件不计入控件）；
  结果已写进 16 表 §4。

## v0.9.164 — 工作流写死「EEZ 参数优先 + 不确定先查官方手册」（PR-0578）

- 用户令：用 EEZ 建 UI 时始终优先在 EEZ 里改参数，不得用脚本间接改 EEZ 工程程序；不确定的先查官方手册，
  并要求把"查阅官方手册"写进工作流。
- `EEZ_FIRST_WORKFLOW_NO_FLOW.md` 新增 §2.2b：顺序＝查手册 → EEZ UI 设参数并构建看 `.c` 产物 →
  结论带页码落 intake → 才写进设计源/模板库；给出「可以做 / 禁止」对照与判据（手册位置 + 构建产物取证）。
- `EEZ_FIRST_WORKFLOW_FLOW.md` §2 增加同口径两行指针；`AGENTS.md` 铁律新增第 15 条（入口一行）。
- 反例引用 I4 翻案：手册 P10 Bitmaps 的 Color format 可选 `INDEXED 4 BIT`；`bpp` 是 CF id
  （`CF_INDEXED_4_BIT=43`），不能用脚本把 4/9/10 当位深试后就判"EEZ 不支持"。

## v0.9.154 — 模板工程按 EEZ UI 拖拽重建（PR-0568）

- 旧模板被确认不是“拖拽后保存语法”：它来自保存形态 + classInfo 片段 + 手工 hiddenFlag，
  且校验是模板↔defaults 自洽循环。
- 按用户令在 EEZ UI 新建工程、18 个画布，每页从 Palette 拖一个控件、松开稳定后保存；
  没有用脚本创建/修改 `.eez-project`。
- 只读提取 19 个模板；`validate_templates.py` 逐字段对照 UI 工程 PASS；构建成功。
- 新语法：有 clickableFlag/scroll/group，无 hiddenFlag/checkedState/textarea；
  widgetFlags 不含 CLICKABLE；localStyles 只有 objID。
- w78 仍是旧语法，A14 0/813，待迁移。P-0258。

---

## v0.9.155 — w78 迁移到 EEZ UI 拖拽保存语法（PR-0569）

- 以新模板为字段真值迁移 w78：删 `hiddenFlag`/`checkedState`，补
  `clickableFlag`/`flagScrollDirection`/`scrollSnapX/Y`/`group`，`widgetFlags` 去掉 `CLICKABLE`。
- `no_click()` 改为 `clickableFlag=false`，装饰件/进度条/图表仍不接收点击。
- A14 放行放置期 `identifier`、隐藏遮罩 `hiddenFlag`、Keyboard 绑定 `textarea`。
- 结果：A14 813/813、D5 24 页平均 98.27%（最低 96.40%）、NAV 72/72、D1–D9 PASS。
- 设计源与交互语义未改；设计冻结结论仍以 D5 重跑为准。P-0259。

---

## v0.9.156 — 模板库补齐到 Palette 全部 36 项（PR-0570）

- 原模板库只覆盖 18 类，与面板 36 项差 18 类；本轮在同一个 UI 工程补齐到 36 项。
- 新增 17 画布；`Tab` 不独立成页，拖到 Widgets Structure 的 Tabview 行内保存。
- 35 画布 / 37 模板（36 控件 + Screen）；`validate_templates.py` PASS。
- 实测：画布拖放只落页面层，嵌套必须在结构树目标行下半区落点。
- `Spangroup`→`LVGLSpanWidget`；MessageBox localStyles 带 definition；
  Image/AnimationImage/Canvas/Line 无 clickableFlag。
- 复核发现 w78 工作树回到迁移前 HEAD，A14 0/813，需重跑 P-0259。P-0260。

## v0.9.157 — 修正 reference/07 的 Tabview 落盘字段

- `reference/07_project_json_schema.md` §6 旧稿写 `"tabs": [ … ]` / `"tabSize": 0`；
  这两个键在 `.eez-project` 里不存在（全库 `.eez-project` 搜 `"tabs"`/`"tabSize"` 命中 0）。
- 改为实测字段：Tab 在 `children`（`LVGLTabWidget`，`tabName`/`tabNameType`）；
  栏位置/尺寸/活动页是 `tabviewPosition`/`tabviewSize`/`selectedTab`/`selectedTabType`；
  `tabviewSize: 0` 隐藏原生 tab 栏，对应 json2eez DSL 的 `tabSize`（skills.md §11.8）。

## v0.9.158 — Tab 结构不变量落地为常驻门禁

- Tab 是 Components Palette 里的独立控件（asar：`LVGLTabWidget` 的 `enabledInComponentPalette`），
  但只能作 `LVGLTabviewWidget` 的子对象；挂 Screen 直下时 GUI 报
  `Invalid position of Tab widget`，headless 构建不查这层结构（P-0033）。
- 新增 `tools/tab_parent_check.py`：逐工程断言 Tab 的父级；`--all <root>` 批量扫。
- `tools/audit_ui.py` 加 **A11 Tab 结构**（随 G1 自动跑）；`project_file` 不是 `.eez-project` 时跳过。
- 自证：全库 26 工程 / 11 个 Tab / 违例 0；反向夹具（Tab 挂 Screen）出 `[A11]` 且非 0 退出。
- skills.md §11.20 的「遗留建议」改为已落地；reference/07 静默失败清单第 8 条补门禁指针。

## v0.9.159 — 门禁放行要带值判据；核对跑完的实例与 tmp 残留（PR-0571）

- w78 迁移重放后，A10/A14 最初整键放行 `hiddenFlag`，会放过 811 个残留 `hiddenFlag: false`；
  改为只在值等于 `True`（真隐藏遮罩）时放行。反向夹具验证：注入 `hiddenFlag: false` 与
  `pad_all` 都出 FAIL。
- 教训：字段级门禁的"例外"必须写成**值条件**，不能写成键名豁免；例外键名要同时落到
  A10（样板并集）与 A14（模板字段集），只改一处会一边 PASS 一边 FAIL。
- D5/仿真跑完会留下 EEZ 实例、headless Edge 与 `tmp/` 杂物（`edgeprof`/`eezprof`/
  `d_page.html`/`eez_*.js`/`wifi_*.bmp`），占着文件句柄让 D7 FAIL；收尾按 user-data-dir
  精确匹配关自己起的实例（别动用户浏览器），再删杂物，构建缓存保留。
- Screen 模板没有 `flagScrollbarMode`，迁移后 24 行 `LV_SCROLLBAR_MODE_OFF` 从 screens.c 消失，
  D5 逐页相似度不变（98.27%/96.40%）。P-0259。

## v0.9.160 — Tabview 0/1/2/3 个 Tab 整块入库（PR-0572）

- 用户要求分别建「无 Tab / 1 / 2 / 3 个 Tab」的 Tabview 形态，防止动态添加导致语法不同。
- 在模板源工程真实拖出 `Tabview0/1/2/3` 四页（Tabview 拖画布，Tab 走 Widgets Structure
  行下半区），实测**只差 `children` 数量**：其余 34 个字段、`tabviewSize=32`、
  `selectedTab=0` 与每个 Tab 对象（180×68、`tabName:"Tab"`）完全相同。
- 新增 `templates/variants/LVGLTabviewWidget.tabs{0,1,2,3}.json`；`extract_templates.py`
  加 `VARIANT_PAGES`/`extract_variants()` 与 `manifest._variants`；`validate_templates.py`
  页数 39、变体四重核对（等于变体页 / children 数 / 除 children 外等于基础模板 /
  每个 Tab 归一后等于 Tab 模板）。
- 自证：`[TPL_CHECK] PASS（37 个模板 + 4 个变体）`；反向夹具三条全 FAIL
  （改 `tabviewSize`、删一个 Tab、塞 `identifier`）；EEZ CLI 构建 39 页
  `No error and no warning detected`（13:03:31）。kit 镜像 37+4 逐字节同步。P-0261。

## v0.9.161 — 变体按用户令在 UI 重做；模板工程写死“禁止手搓”（PR-0575）

- 用户令“还原本轮改动，只改 eez-widget-templates；重新建立 Tabview 0/1/2/3，
  必须用 EEZ 拖动新建创建法”：在 UI 里删四页→Add Page→拖 Tabview→把 Tab 拖到
  Widgets Structure 行下半区（0/1/2/3 次）→保存；误删的 Lottie 页同样补拖回来。
- 重新提取后 37 模板 + 4 变体与重做前**逐字节相同**，`[TPL_CHECK] PASS`；
  EEZ 构建 39 页 0 错 0 警（14:03:53）。
- 工程 UUID 换新、页面顺序变化导致 `SCREEN_ID_*` 重排（35~39），属重建副作用。
- `eez-widget-templates/README.md` 新增「硬规则：不得手搓，只能用 UI 拖拽保存语法」：
  唯一 oracle、只读提取产物、只允许改值的白名单、新增形态必须回 UI 拖、Tab 只能拖进
  结构树行下半区。kit 镜像 README 同步。P-0261。

## v0.9.162 — 流程文件写死“新建控件严格按模板库语法”（PR-0576）

- 用户令：把“后续项目严格按模板控件语法新建控件”写进本地经验库流程，避免问题复发。
- `EEZ_FIRST_WORKFLOW_NO_FLOW.md` §2.2 生成方式首段新增强制句：后续所有项目（no flow / flow）
  新建控件一律“克隆模板 → 只改值 → 过 A14”；模板缺类型/形态时回模板工程 UI 拖拽保存后重提取，
  禁止手搓、禁止脚本拼字段。
- `EEZ_FIRST_WORKFLOW_FLOW.md` §2 第②步注记由“克隆 EEZ 默认结构再改”升级为
  “模板库克隆 + A14 字段集 + 缺类型回 UI 拖”，与 no flow 口径一致。
- 未改模板文件与示例工程；w78 复跑 `[A14] 813/813`、`[EEZ_CHECK] PASS`。

## v0.9.163 — 工具索引补齐字段集门禁；独立新工程复核 Tabview 变体（PR-0577）

- `tools/template_field_check.py` 已入库（f719990），本轮补 tools/README 条目与 A11 行：
  任意 `.eez-project` 逐控件字段集必须等于拖拽模板（`identifier` 不计），按类型列
  “多/缺”字段与数量，违例非 0 退出；默认 kit 镜像模板，`--templates` 可指向工程侧模板库。
- 独立复核：EEZ Home→Create 新建 LVGL 9.4 工程，UI 真实拖出 Tabview 0/1/2/3；
  与 `templates/variants/*.json` **字段/值/键序 0 差异**；A11 `6 Tab / 4 Tabview / 违例 0`。
  新建工程仅自带 `Main` 示例 Label 是旧写法（非拖拽控件），F0–F3 四页全干净。
- 用该门禁量仓库外四个 Tabview 示例（w23 / tabview-swipe-switch / perf / watch）：
  **387/387 控件偏差**（旧手搓写法），确认是示例生成器的问题，不是模板库。

## v0.9.153 — 全流程执行 + 测试夹具修复（PR-0560）

- D5 全量树节点 `BLOCKED`：取 rect 前 `row.scrollIntoView({block:'center'})`，24/24 恢复。
- `flowtest` 原是死模式（env 无人处理，无头下无限循环）；实现假世界连接闭环。
- 连接成功判定修正：`pick` 指针 `qsort` 后失效，先拷 SSID；`CONN_STATE=2` 被 logic 消费，
  改为查后端 AP `connected`；`uitest` 由“打印 conn=0 仍 0 退出”改为断言失败非 0。
- 结果：A/D 全 PASS，D5 24 页平均 98.03%、最低 95.89%；NAV 72/72、UI 行为 PASS；
  Wi-Fi 真扫描 8 AP、假连接/UI PASS、关闭 PASS、24 张截图；模板库 PASS/OK。P-0253。

## v0.9.152 — 标准字段集补 hiddenFlag + 智能家居 A14 全绿（PR-0559）

- 用户要求确认 EEZ 所有控件都从标准模板改；初查 w78 有 424/815 控件字段集不标准：
  104 个 Button 子 Label 是精简样板、104+203+1+3+2 个控件多 `hiddenFlag`、
  8 个 Slider 缺 `valueLeft*`、1 个 Bar 缺 `valueStart*`。
- 标准模板补基础字段 `hiddenFlagType: literal` / `hiddenFlag: false`，`_apply_fields()` 持久化；
  w78 Button 子标签改完整 Label 字段集，补 Bar/Slider range 字段，恢复 literal hiddenFlag。
- `eez_check.py` 新增 **A14**：逐控件字段集必须等于标准模板库；w78 现在 `815/815`。
- 生成代码 pos/size 1630 行、style 9149 行、flags 687 行与迁移前逐行一致；视觉/行为不变。
- A/D 门禁、UI 行为、NAV 72/72 全 PASS；P-0252。

## v0.9.151 — 模板双副本核对 + 旧采样引用清理（PR-0557）

- 用户要求同时核对经验库和示例工程的模板；两处 19 个模板、defaults、manifest 逐字节一致，
  两边 `[TPL_CHECK] PASS（19 个模板）`。
- 示例工程 gallery 18 页与模板 0 不符；生成代码 18 种创建函数、尺寸/文本/选项/值/颜色 0 不符；
  Switch 50×25 且无 `remove_flag(CHECKABLE)`；构建成功。
- 清理旧“临时工程新建 / `eez_defaults.py` 采样”引用（AGENTS 8、NO_FLOW §2.2、reference/07、
  tools/README、reference/README、根 README/CODE_WIKI、语法库 README）；P-0249 加更正提示。
- `validate_templates.py` 支持 `--templates/--defaults`，可校验任一副本；补嵌套事件/时间线检查。
- P-0251。

## v0.9.150 — 控件模板复位为标准新建值（PR-0556）

- 用户追问模板是否“新建控件的标准模板”；核对发现字段集真实，但值带源工程定制
  （Switch iOS 配色、Button 蓝底+`cn14`、尺寸/文案/选项/值域都是源工程值）。
- 从 EEZ Studio `classInfo.defaultValue/defaultFlags` 取 19 类标准值，落到 `defaults.json`；
  `build_templates_project.py` 全量复位，Button 按标准 100×50 + 子 Label“Button”。
- `validate_templates.py` 逐项对照标准值；项目/经验库 README、AGENTS 8、NO_FLOW ⑩、reference/07 同步。
- 自证：`[TPL_CHECK] PASS（19 个模板）`、`[BUILD] OK`；P-0250。

## v0.9.149 — EEZ 控件语法库 + 模板采集工程（PR-0555）

- 用户令：根目录新建工程采集 EEZ 控件模板，单个控件模板存经验库，建“新建控件”语法库。
- 新增 `eez-widget-templates/`：从真实工程提取 19 种控件 JSON（objID 占位、事件清空、表达式 literal），
  生成 18 页 gallery 并用 EEZ CLI 无头构建；`validate_templates.py` 校验字段集与 CHECKABLE。
- 新增经验库 `reference/eez_widget_syntax/`（README + templates + manifest）；
  `AGENTS 8`、`NO_FLOW ⑩/⑪`、`reference/07` 明确“新建控件唯一来源”。
- 自证：`[TPL_CHECK] PASS（19 个模板）`、`[BUILD] OK`；P-0249。

## v0.9.148 — Switch 样板缺 CHECKABLE 导致开关不切换（PR-0554）

- 用户指出开关点不动，并判断是样板未按拖拽生成；核对属实。
- `eez_defaults.json` 的 Switch 样板采样自 watch 工程，缺 `CHECKABLE`，生成代码移除该标志；
  LVGL 在 `RELEASED` 时靠它切换。改用 `two-state-styles` 真实拖拽样板（带 CHECKABLE）。
- `eez_check` 新增 **A13**：所有 Switch 必须含 CHECKABLE；临时 native 补丁已删除。
- 自证：`PRESSED → RELEASED` 后 on 1→0、off 0→1；A1–A13 PASS，D5 确认哈希仍有效。
- AGENTS 8、NO_FLOW 生成器⑪、reference/07；P-0248。

## v0.9.147 — 行为覆盖审计：69 个交互件未接（PR-0553）

- 用户发现 UI 很多控件没实现，质疑控件数核对。
- 结论：281=281 只证明存在/类型（A2/A12），不证明行为；问题在 ⑦。
- 新增 `design/behavior_audit.py`：已接导航 72、Wi-Fi 10、滑条数值 5；
  未接交互件 69（开关 28、动作/场景 38、滑条 3）；`--strict` 可供后续门禁。
- P-0247（open）；后续按批次补开关/动作/滑条/硬件与 Wi-Fi 连接。

## v0.9.146 — D5 确认标记改设计源哈希；设计冻结（PR-0552）

- 用户确认 D5 后，D1–D9 里 D5 仍 FAIL：D4 重建刷新 screens.c/.eez-project mtime，被误判过期。
- `proj_sig()` 改哈希设计源（pages/values/simple_control/eez_gen），标记写入 `sig:`；
  旧标记无 sig 时退回 mtime 兼容；修正 sig 前缀切片。
- 结果：D1–D9 PASS（D5 24 页 98.03%，最低 96.07%；D9 442KB）；
  `design/flow_state.json` 记录 design_frozen（2026-11-05 19:50）。
- 后续改设计须回 ① 并重跑 D5；P-0246。

## v0.9.145 — 滑条→数值联动 + 控件一致性审计（PR-0551）

- ⑦ 接线：新增 `src/native/value_bind.c/.h`，亮度/开合/自动锁屏滑条变化时更新对应 in_read 标签；
  色温等需值域映射的留后。无头自证：55% / 开合 42% / 33% | 33%。
- 一致性审计：设计 281 行 = EEZ 281 个标注控件 = H5 281 行，逐页数量一致，类型 0 错配；A1–A12 PASS。
- D5 全量重跑（单实例）：平均 98.03%，最低 96.07%（灯详情），待用户确认。
- 测试脚手架 `W78_VALUE_TEST` 已删，终态只留 value_bind；P-0245。

## v0.9.144 — 沉淀：滑条/进度条旁的数值=内部读（PR-0550）

- 用户令：明显属于进度条/滑条 + 数值显示的组合，直接标内部读，不用逐条说。
- `values.py` 自动识别：滑条/进度条邻近（±20/±10）+ 名称含 %/K → `uivalue`（`in_read`）；
  进度值/特殊项用显式 UI_READ（窗帘 70%、设置 60 秒、配网 70%）。
- w78 命中 9 条 UI 读数（开合 70% ×4、窗帘 70%、80%、3000K、60 秒、配网 70%）；
  控件行 281；A1–A12 PASS、PC 构建通过。
- NO_FLOW §2.1、AGENTS 8、reference/07 写入规则；P-0244。

## v0.9.143 — 开合值归 UI 内部读 in_read（PR-0549）

- 用户纠正：开合随进度条变化，属 UI 自己控制，不能当静态/外部读。
- `values.py` 增加 `uivalue`（UI_READ / UI_READ_SUB），`io_of → in_read`；
  恢复 5 条（客厅/主卧/窗帘详情×2/全部设备），EEZ 仍为真实 Label；1080P 保持静态。
- 控件行 276 → 281；A1–A12 PASS、PC 构建通过；滑条→标签实时更新留给⑦。
- NO_FLOW §2.1、AGENTS 8 补分类口径；P-0243。

## v0.9.142 — 应用 H5 批注：读数改静态文本（PR-0548）

- 输入 `w78_annotations (2).json`：客厅 `1080P · 已加密`、`开合 70%` 删除控件。
- 追加要求：所有 `开合 70%` 同步处理（客厅/主卧/窗帘详情/全部设备）。
- `values.py` 增加 SKIP / SKIP_SUB，按 (页,名称) 与子串排除；设计帧文本保留为静态；
  不生成控件表/H5 标注/EEZ Label。H5 ANN_KEY 升 v2，旧批注不回显。
- 控件行 280 → 276；A1–A12 PASS；PC 仿真构建通过；P-0242。

## v0.9.141 — H5 评审页模板 v2 回灌（PR-0547）

- 用户认可 w78 当前 H5，要求输出经验库并便于后续同类生成。
- `tools/h5_overview_template.py` 整体同步为 v2（三视图、全量标注、读数/整卡 glyph/弹层、
  右键清单/标签批注、效果图页面 pin、localStorage、导出 annotations.json）。
- reference/14 新增 §10 复用步骤 + 数据契约 + 必保交互 + 验证；QUICKSTART 增加 H5 短指令；
  tools/README 条目更新；P-0241。

## v0.9.140 — 「标注」开关改为全局生效（PR-0546）

- 用户问顶部「标注：开」是否还有作用。原来只作用于高清设计图，总览/演练点了没反应。
- 分层总览、跳转演练、停靠栏也改用 `marks:marksOn`；点一次全局隐藏/显示控件框与序号。
- CDP 自证：分层总览控件描边数 637 → 关闭后 344 → 再开 637。
- 批注红框/红 pin 不受此开关影响，始终显示待处理修改。

## v0.9.139 — 底部控件标签也接右键控件菜单（PR-0545）

- 用户反馈：右键页面卡下方控件标签仍是浏览器菜单。
- `pill()`/`tagIo()` 输出 `data-page/data-rn`，`tags(d,p)` 传页面名；
  右键选择器扩到 `.item[data-rn], .pill[data-rn]`。
- CDP 自证：右键 `5. 客厅卡 → 客厅` 标签 → 菜单标题正确，标记删除写入 localStorage。
- NO_FLOW §2.1、AGENTS 6、reference/14 §8 同步；P-0240。

## v0.9.138 — 控件菜单挪到右侧清单，效果图只做页面批注（PR-0544）

- 用户令：控件菜单在右侧控件清单处右键，页面批注在效果图里右键。
- 清单行加 `data-page/data-rn`；右键清单行 → 控件菜单；效果图（分层卡片/跳转大图/停靠栏）
  右键只做页面 pin，不再弹控件菜单。
- CDP 自证：清单 #5 菜单标题正确、删除写入；跳转大图右键标题为“页面”。
- P-0239；NO_FLOW §2.1、AGENTS 6、reference/14 §8 同步。

## v0.9.137 — H5 批注改为右键控件菜单（PR-0543）

- 用户令：不要“批注开关 + 左键面板”，改为在控件标注处右键弹菜单选功能。
- 去掉批注开关/左键采集；右键控件序号/本体 → 标记删除/修改说明/加控件提示/清除；
  右键页面空白 → 加坐标提示；右键已有 pin → 修改/删除；点空白或 Esc 关闭菜单。
- 自证：右键 #2 → 菜单标题正确；标记删除 opacity=.18；页面 (400,192) 加提示并保存。
- NO_FLOW §2.1、AGENTS 6、reference/14 §8 同步为右键口径；P-0238。

## v0.9.136 — H5 批注模式实现（PR-0542）

- 按 v0.9.135 规格在 `overview_pro` 落地：批注开关、控件删/改、页面坐标 pin、
  localStorage、导出 `w78_annotations.json`、底部「导出并返回 ④」。
- 删除只做 H5 预览（控件 opacity .18 + 红框「删」）；工程仍由设计源重生成。
- Edge headless + CDP 自证：控件面板/保存/pin/删除预览四步全通过。
- 批注坐标用 viewBox；弹层态用展开帧。P-0237。

## v0.9.135 — H5 批注回路写入工作流（PR-0541）

- 用户定：H5 支持“点控件删/改、点页面落坐标标签、导出 annotations.json 给 AI 改设计源”，
  改完提示返回 ④ 重新生成 EEZ。
- NO_FLOW §2.1 新增「H5 批注回路」与 JSON 条目格式；AGENTS 6 加一行；reference/14 新增 §8 规格。
- 边界：H5 不直接改工程/不手改生成 HTML，设计源仍是唯一真值；删除先在 H5 本地隐藏预览。
- 状态：规格已落档，H5 批注模式代码待实现。

## v0.9.134 — 沉淀「标注范围（唯一判据）」（PR-0540）

- NO_FLOW §2.1 新增一段判据：会随设备/时间变化的值、用户能操作的元素 = 控件，必须编号；
  固定标题/字段名/说明步骤/按钮文案/空态/装饰不标。
- 明确整卡交互区（整卡 + 卡内开关/滑条本体）、隐藏弹层展开态、纯数字角标都归控件。
- AGENTS 8 加指针；reference/14 同步。

## v0.9.133 — 整卡开关/滑条标注到控件本体（PR-0539）

- 用户指出房间格开关/滑条很显眼，但序号在卡片角落。
- `overview_pro` 为整卡 toggle/slider 计算 glyph box（开关轨道/滑条轨道），标注框与序号画在
  开关/滑条本体上；整卡保留 0.28 透明虚线框表示点击区域；序号放 glyph 左侧不盖控件。
- H5 重新生成（282 条控件，JS 检查通过）；未启动 EEZ。

## v0.9.132 — 日期/时间读数纳入 value 控件（PR-0538）

- 用户令：日期也是从硬件（RTC）获取，应算控件。
- `values.py` 增加日期规则：`YYYY-MM-DD`、`M月D日`、`周一…`、`上午/下午/晚上…好`；
  读数 97 → **100**，控件行 279 → **282**（主控问候日期、关于页两条更新日期）。
- A1–A12 PASS、导航 72/72；AGENTS 8、reference/07 补“日期时间”示例。

## v0.9.131 — 设计图细节复查：读数 97 条 + Wi-Fi 弹层态（PR-0537）

- 用户要求复查设计图里还有哪些控件（细节）没标注。
- `values.py` 扩类：数量（个设备/个房间/条未读）、状态（在线/已接入/正在连接/已开启）、
  时间计划（22:30/今晚/每晚）、版本/网关、色温 K；读数 63 → **97** 条。
- H5：Wi-Fi 基础页只标 base 控件；新增「Wi-Fi 密码半页」「忘记网络」两张展开态卡，
  弹层控件在正确位置带号，去掉基础页上的幽灵框。
- 控件行 245 → 279；A1–A12 PASS、导航 72/72；D5 不再反复跑（最新 98.03%，待确认）。
- 有意不标：字段名/标题/说明/空态/装饰字符/场景动作文案/纯数字角标。

## v0.9.130 — D5 抓错页修复 + 读数补全 + 禁止反复开关 EEZ（PR-0536）

- 用户令：不要老是打开/关闭 EEZ。
- D5 根因：Pages 树与 Widgets Structure 有同名文本（房间卡「客厅」等），点到 label 后抓的是上一页；
  改为只认**同时含 ≥3 个页 ID 的 Pages 树**，`MISS_*` 直接报错不回退；客厅/灯详情重抓确认正确，
  24 页全量 98.03%。
- 读数补全：`开/关` 状态不再按字号排除，改由“落在小开关框内”排除；类型卡图标首字用邻近长文本排除。
  读数 57 → 63 条。
- H5 读数徽标移到数值左侧 16px，避免压住读数。
- AGENTS 11 / NO_FLOW D5：整轮只起一次 EEZ，改动期间不反复跑，合并一次全量；禁止反复开关。

## v0.9.129 — 设备读数作为 value 控件自动标注（PR-0535）

- 用户令：温度这类从设备读取的值也应算控件，必须标注出来。
- 新增 `design/values.py`：从设计帧识别温度/湿度/百分比/功率/电量/在线状态等读数，
  自动补 `value` 行（`out_read`，`hr` 码），生成真实 Label；标题/说明/按钮文案/小号开关状态字排除；
  宽卡片与只读卡里的读数照标。
- w78：新增 57 条读数，控件行 182 → 239，out_read 27 → 84；A1–A12 PASS，导航 72/72，
  D5 98.03%（待重新确认），ESP32 `-O2` 只编译 442KB。
- AGENTS 8、NO_FLOW ②/生成器⑫、reference/07、控件清单说明同步。

## v0.9.128 — 高清设计图默认叠加全部控件标注（PR-0534）

- 用户令：设计图里的所有开关、滑条等控件都要标注出来。
- 根因：控件表 182 条完整，但 H5「高清设计图」写死 `marks:false`，主设计视图看不到序号。
- `overview_pro.py`：`marksOn` 默认真，高清设计图使用 `marks:marksOn`；顶栏加「标注：开/关」。
- 重生成 H5（24 页 / 182 控件，node --check 通过）；AGENTS 6、NO_FLOW §2.0c、reference/14 同步：
  高清设计图默认必须有全部控件号，不得以无标注净图作为唯一视图。
- 说明：房间格“整卡开关/滑条”的序号在整卡左上角，代表整块交互区；真控件是卡内小件（P-0230）。

## v0.9.127 — 标注控件必须真实物化；新增 A12 类型门禁（PR-0533）

- 用户令：设计图标注的所有控件必须在 EEZ 里真实建立，不能是假的。
- 审计 171 行标注：28 开关 + 8 滑条 + 38 动作按钮 + 2 输入 = **76 个只有透明容器**。
- `eez_gen` 新增 `widget_kind()`：toggle→Switch、slider→Slider、动作/跳转→Button、
  输入→Textarea、进度→Bar、图表→Chart；整卡交互区用「容器 + 卡内真控件」（子坐标相对父）。
- 开关初值按设计旋钮位置写 `states:"CHECKED"`；已物化控件框内的设计图形不再重复画装饰。
- `eez_check` 新增 **A12**：逐行核对标注类别 ↔ 实际类型；整卡核对容器内真控件；
  Wi-Fi 页核对 list/textarea/keyboard/button。A2 的“同框存在”不再能掩盖容器冒充。
- D5 确认标记增加时效：工程/`screens.c` 比确认标记新即 FAIL，避免旧 98.53% 掩盖新 UI。
- w78 结果：控件 814，A1–A12 PASS，导航 72/72，D5 当前 97.85%（待用户重新确认），
  ESP32 `-O2` 只编译 442KB（字体 236）。

## v0.9.126 — PC 仿真 build 目录按工程名命名（PR-0532）

- 用户令：每个工程的 PC 仿真 build 单独命名，避免多工程冲突。
- `run_sim.bat` 改为 `<project>\tmp\sim_build_<project name>`（由 `SIM_TARGET_PROJ_DIR` 取工程名），
  `SIM_BIN_DIR` 随之为工程私有；已有缓存目录改名复用，删 `CMakeCache.txt` 重配一次后
  增量构建约 1s。
- `mem_report.py` 按 `sim_build_<工程名>` 找 exe/库（兼容旧 `sim_build`）；
  D7 白名单改为 `sim_build_*/`、`compile_cache/`。
- AGENTS 5、NO_FLOW 目录树/D7/收尾条款同步。

## v0.9.125 — 编译缓存保留，不再每次全量重编（PR-0531）

- 用户令：编译过程文件不要删，避免下次编译耗时。
- `esp32_estimate.py` 与 `mem_report.py` 的 PC 统计改为持久对象缓存
  `tmp/compile_cache/{esp32,pc}/…`，按**单文件内容 + 头文件 + 编译参数签名**失效
  （改一个屏不会连字库重编）；首次约 7s，缓存命中约 0.3s（13 个 .o，约 3.9MB）。
- D7 白名单改为只允许 `sim_build/`、`compile_cache/`；AGENTS 5、NO_FLOW 目录树/D7/收尾条款、
  `run_sim.bat` 注释同步。

## v0.9.124 — 估算逐文件标注精确链接值（PR-0530）

- 用户质疑 `screens.c 239.7KB` 是否真实占用。
- 说明：239.7KB 是 -O2 只编译对象；最终链接 `screens.c` 为 **176.0KB**（gc 掉未绑定回调/合并字符串，
  -26%）。24 屏合计 239.8KB 对象，最大 living 19.3 / master 18.2 / main 16.6KB；
  非屏代码仅 9.3KB（含 `objects_t` bss 3.7KB）。
- `mem_report.py` 在估算逐文件行后追加「精确 X」，避免把未链接值当最终占用。
- 全 UI：估算 476.0KB → 精确 404.9KB；最大项仍是 cn12 汉字档 220.6KB。

## v0.9.123 — 默认优化等级固定 -O2（PR-0529）

- 用户令：默认就用 `-O2`（IDF 当前）参数。
- `design/esp32_toolchain.json` 增加 `default_opt: "-O2"`；`esp32_estimate.py` 默认用该等级
  覆盖编译命令中的优化参数（不再随模板变化），标题/汇总/D9 均显示「优化 -O2，默认」。
- 等级对比表保留 `-O0/-O1/-O2/-O3/-Os`，`-O2` 行标「当前」。
- NO_FLOW ⑤/D9/§2.5、AGENTS 13、QUICKSTART ⑤、reference/07、B23、P-0229 同步。

## v0.9.122 — 资源树标注优化等级 + 等级对比（PR-0528）

- 用户令：说明优化等级是多少，不同等级分别占多少资源。
- `esp32_estimate.py` 从 IDF 编译命令自动识别等级（本模板 `-O2`），新增 `measure_levels()`，
  对 `-O0/-O1/-O2/-O3/-Os` 各编译一遍；对比表按 `ui_hash` 缓存（UI 变了才重算）。
- `mem_report.py` 在 ESP32 标题标注等级、打印对比表，`[MEM-BIN]` 带 `opt=`；D9 文案带等级。
- w78 实测（只编译，字库 236KB 不随等级变）：`-O0` 528.0 / `-O1` 474.5 / `-O2` 476.0 /
  `-O3` 476.0 / `-Os` 475.2KB；RAM 均为 3.8KB。
- NO_FLOW ⑤/D9/§2.5、AGENTS 13、QUICKSTART ⑤、reference/07、B23、P-0229 同步。

## v0.9.121 — 资源账默认改为 IDF 工具链只编译估算（PR-0527）

- 用户令：默认用 IDF 工具链只编译看占用，流程也默认这么写；只有点名才做 IDF 工程编译。
- 新增 `design/esp32_estimate.py`：从测量模板 `compile_commands.json` 取 IDF 原参数，
  用 riscv 工具链编译 UI（不链接），每次实时出逐文件字节；`mem_report.py` 默认展示它，
  PC 编译上限并列；`[MEM-BIN]` 带 `source=toolchain-estimate`，D9 按此核预算。
- 精确最终链接保留为按需：`design/esp32_size.py`，`ui_hash` 缓存，点名才跑。
- NO_FLOW ⑤/D9/§2.5、AGENTS 13、QUICKSTART ⑤、reference/07、B23、P-0229 同步。

## v0.9.120 — 换 IDF 编译器只编译仍不等于 IDF 构建（PR-0525）

- 用户问：用 IDF 编译链直接估算是否与 IDF 一样。
- 结论：只编译仍差 17%（缺 `--gc-sections`、链接脚本、库顺序）；必须用同一套链接参数链接一次才一致。
- NO_FLOW §2.5 措辞补全：换 IDF 编译器也不改变「只编译=估算」的结论；
  同优化参数实测仍 +17%，差异在链接期（gc/脚本/库顺序），不是 -O 等级。

## v0.9.119 — 工具链只编译只能估算，精度实测（PR-0524）

- 用户问：PC 与 ESP32 占用是否一样；能否只用工具链编译、不进 IDF。
- 实测同一份 UI：PC 525KB / 目标工具链只编译 475.9KB / IDF 最终链接 404.9KB；
  只编译比链接高 17.5%（未做 gc），RAM 误差 +2.5%。
- 结论：工具链只编译可当快速估算，不能作 D9/交付判据；精确值链接一次即可，
  仍可复用测量模板临时换 UI，不必把 UI 并进 IDF 工程。
- NO_FLOW §2.5 补这条；P-0229 增加实测表。

## v0.9.118 — 资源占用要求写进工作流步骤（PR-0523）

- 用户令：ESP32 编译占用（有环境时）+ PC 编译占用并列、数据详细准确，必须体现在工作流。
- NO_FLOW ⑤ 步骤与判据补：每次编译/测试打资源树，目标最终链接逐文件字节 + app.bin/分区 +
  整机内部 RAM，PC 上限并列，缓存过期=未测。
- §2.5 新增「展示（每次编译/测试都打）」：两层口径与无 IDF 时的标注要求。
- QUICKSTART 卡⑤、AGENTS 13 同步。

## v0.9.117 — 资源账增加 ESP32 最终链接（PR-0522）

- 用户令：有编译环境时体现 ESP32 编译后占用，同时保留 PC 段，数据要详细准确。
- 新增 `design/esp32_size.py`：本机 P4 模板换 UI → `idf.py build` → `esp_idf_size` 读 map
  → 还原模板；写 `design/esp32_size.json`（逐文件字节 + `ui_hash` + 时间）。
- `mem_report.py` 优先显示 ESP32 最终链接，PC 编译标注为「未链接上限」；`[MEM-BIN]` 带 target，
  D9 以目标值为预算基准，缓存过期自动回退 PC。
- w78 实测：UI 404.9KB/3.7KB（字体 228.9KB；cn32 未被引用 → 0），app.bin 1.09MB/8MB；
  PC 同源 525KB/7KB。
- 踩坑（P-0229）：备份目录放 `eez-test/src` 下会被当组件；拷贝 mtime 旧导致 ninja 不重编。
- NO_FLOW D9/§2.5、AGENTS 13、reference/07、B23 同步。

## v0.9.116 — 资源账只报编译后占用（PR-0521）

- 用户令：只要编译占用结果，不要源码体积，别弄错。
- `mem_report.py` 去掉全部源码 MB 数（字体、screens/styles/images 合计、native 源码行），
  树里只留编译后 Flash / bss / RAM；PC 仿真接口只留 exe、liblvgl.a 与运行期缓冲。
- NO_FLOW D9/§2.5 改为「只报编译后占用：Flash（text+data）+ bss，源码体积不进账」。

## v0.9.115 — 内存账改按编译后 Flash（PR-0520）

- 用户质疑：`screens.c` 源码 1.22MB 是否真占这么多。
- 实测：screens.c 编译后 text 293,664 + data 544 ≈ **287KB Flash**、bss 7,456 ≈ **7KB RAM**；
  字体源码 1.52MB → **237KB Flash**（cn12 221KB / cn24 9KB / cn32 8KB）；
  UI 合计源码 2.74MB → **525KB Flash + 7KB RAM**。
- `mem_report.py` 改为 gcc 编译产物 + `size` 取 text+data/bss，树里写「源码 x → Flash y」；
  输出 ASCII 汇总行 `[MEM-BIN]`；D9 改解析该行并按编译后值对预算。
- 预算改档位制 `mem_budget.json`：tier=1m，fonts 0.5MB / UI 1.0MB。
- NO_FLOW D9/§2.5 补「只认编译后 Flash（text+data）与 bss，源码体积不作判据」。

## v0.9.114 — 字库存储策略 A11 硬门禁（PR-0519）

- 用户令：镜像字号 ≤3 种、只有 1 档可含常用/完整汉字且尽量小；SD 卡不限；严格执行。
- 新增 `design/font_storage.json`（storage=image/sd）；`eez_check` 新增 **A11**：
  镜像 ≤3 档、恰好 1 档带汉字、该汉字档必须是最小字号；SD 模式镜像仍须有 1 档汉字兜底。
- 反向测试四例（4 档 / 两档汉字 / 汉字非最小 / SD 无兜底）均正确 FAIL。
- 当前 w78：3 档（12 汉字 / 24/32 ASCII），A11 PASS。

## v0.9.113 — 控件 JSON 只许来自 EEZ 拖拽样板；新增 A10 字段门禁（PR-0518）

- 用户令：所有控件添加不得随意写代码/捏造对象格式，必须以 EEZ 画布拖入生成的 JSON 为基础调整，严格执行。
- 规则：AGENTS 8 改写为「只克隆拖拽样板」；NO_FLOW 生成器九条 → **十条**，新增⑩；
  reference/07 写明取样流程（拖控件→保存→`eez_defaults.py` 采样→克隆）与允许修改的字段。
- 门禁：`eez_check` 新增 **A10**——逐控件比对字段集与 `eez_defaults` 并集，出现样板外字段即 FAIL。
- 实测：A10 立刻抓到生成器里人为加的 `pad_all`（列表样式），已删除；A10 全工程 PASS。

## v0.9.112 — PC 仿真编译/测试自动打印资源树（PR-0517）

- 用户令：仿真阶段每次编译完成、每次跑测试，都要反馈当前资源占用（UI 层/字库/PC 仿真接口），树状展示。
- `design/mem_report.py` 增加资源树：镜像 UI（逐字体大小 + screens/styles/images + 合计/预算）、
  字库（镜像 12 汉字 + 24/32 ASCII、SD 卡未启用）、PC 仿真接口（main.exe、liblvgl.a、native 源码、
  LV_MEM、帧缓冲 800×480×32bpp≈1.46MB、snapshot 1.5MB 按需）。
- `design/sim_cmake/run_sim.bat`：构建成功后打印完整树；`test` 模式在 AUTOTEST PASS 后再打一行摘要。
- NO_FLOW D9 行同步。

## v0.9.111 — 镜像字库：≤3 档、仅 1 档带汉字并已落地（PR-0516）

- 用户口径：镜像内字号不超过 3 种；**只有 1 个字号允许常用/完整汉字**，且尽量小；其余字号只放
  ASCII/数字；SD 卡字库不占镜像、可不限（保留镜像 1 档兜底）。
- w78 落地：字号 16 档 → **12（汉字）/24（数字）/32（大数字）**；只有 12px 挂 GB2312+设计用字，
  24/32 只含 ASCII/数字/符号；设计源与 EEZ 同一规则。
- 结果：字体条目 16→3，字体 **9.23MB→1.52MB**，生成物 **10.45MB→2.74MB**；D9 预算改 2/3MB。
- 代价：全 UI 中文统一 12px，标题与大数字档减少，视觉层级变平；若需更易读可把单一中文字号换 14/16。
- 复验：导航 72/72；D5 24 页 98.53%；D1–D9 PASS。

## v0.9.110 — 字库按字号共用：12/18 直接挂运行时字符集（PR-0515/0516）

- 用户令：字库能公用一些字号；设计字号 ≤3 种。
- 工程：删除独立 `cn12f`/`cn18f` 条目，12/18 号本身挂 GB2312 运行时字符集、统一 2bpp；
  字体条目 18→16，字体 9.80→**9.23MB**。静态 12/18 文本随之为 2bpp，目检无可见断层。
- 流程：字号 ≤3 档令牌规则已入 NO_FLOW / AGENTS / reference/07；当前 w78 16 档为历史设计，
  版式重整留待下一轮设计修订。

## v0.9.109 — 字号 ≤3 档且全工程共用（PR-0515）

- 用户令：字库要公用字号；设计图/UI 设计阶段字号不超过 3 种。
- NO_FLOW ① 行、生成器第③条、F4、§2.5 同步：设计源先定 ≤3 档令牌（小/正文/大），全工程共用；
  大数字可单独 ASCII 子集例外；新增字号先论证。
- AGENTS 新增规则 14；QUICKSTART 卡①、reference/07 同步。

## v0.9.108 — 第二轮 UI 复核：忘记框豆腐、关于页误导箭头、关闭键方框（PR-0514）

- 忘记对话框标题/SSID/说明是设计字号字体，运行时文案缺字 → 全部挂运行时 `cn12f`，布局微调。
- 关于页三个只读行带 `›` 但无目标页 → 设计源删箭头，不再误导可点。
- Wi-Fi 半页关闭键方框：按钮标签没挂运行时字体、`×`(U+00D7) 未进字符集 → 补字形 + 挂 `cn12f`。
- 复验：24 屏整屏截图 + 忘记框/半页截图；导航 72/72；D5 98.49%；D1–D9 PASS。

## v0.9.107 — UI 预算档位前置到设计阶段确认（PR-0513）

- 用户令：前期设计阶段就确认内存参数并询问用户，而不是预生成后才看。
- NO_FLOW §2 表①行与 §2.5 加：①询问 UI 预算档位（200K/500K/1M/2M/4M 或实际值）并落
  `design/mem_budget.json`；**未确认不进入 ④ 预生成**。
- AGENTS 规则 13、FLOW 总则、QUICKSTART 卡① 同步。

## v0.9.106 — UI 内存改按预算档位控制，不写死上限（PR-0512）

- 用户纠偏：上一版 §2.5 的 64×64/16 帧/256KB 等写得太死；应按项目实际预留空间分级。
- §2.5 重写：先确认档位（200K/500K/1M/2M/4M 或实际值），表给各档字体/图片/动图的**参考**配置；
  分配顺序「可读性优先：字体→静态图→动图」，压缩后必须目检 + D5；D9 对档核账。
- AGENTS 规则 13 与 reference/07 同步为「按档位控制，不压呈现质量」。

## v0.9.105 — 工作流写明「UI 小内存优先（字体/动图）」（PR-0511）

- 用户令：始终以小内存消化完成 UI，主要是字体、动图。
- NO_FLOW 新增 §2.5：字体（必要字号/字符集、运行时 12/18、大字 2bpp）、动图（优先属性动画；
  序列帧 ≤64×64/≤16 帧/1–4bpp/合计 ≤256KB）、图片（按显示尺寸、低 bpp）、缓冲（固件不跑 snapshot）、
  D9 预算门禁。
- AGENTS 规则 13 改写为「UI 小内存优先（字体/动图）」。

## v0.9.104 — 内存优先入流程；字体 11.06→9.80MB + D9 预算门禁（PR-0510）

- 用户令：工作流始终注意内存占用，以减少内存占用优先。
- 规则：AGENTS 13「内存优先」；NO_FLOW D1–D8 → D1–D9（D9 内存账）；
  reference/07 字体节补 bpp/字号/预算口径。
- 工程：运行时时档 24→18（cn18f），与 cn12f 固定两档；运行时档与 ≥30px 设计字体改 2bpp。
  字体 .c 11.06MB→**9.80MB**，生成物 12.29→**11.02MB**；`design/mem_report.py` + `mem_budget.json`（10/12MB）。
- 复验：大字 2bpp 目检无断层；D9 PASS；D1–D8 仍 PASS。

## v0.9.103 — 仿真目检修三处布局缺陷（PR-0509）

- 「全部设备」筛选胶囊只有底色没文字：装饰矩形 over 阈值 2000 太大，把 68×28 胶囊抬到文字上方。
  收窄为 `面积<400 或 min(w,h)≤10`，只让信号条/圆点上浮。
- 「摄像头」视频卡压住「移动侦测」行：卡高 300 伸进 y=364 的行；卡 252、内框 168、码率文字挪进卡内。
- 「主卧」场景格右上空胶囊：`tile()` 给所有格子画「详情」，但场景格只登记「执行」；改为 scene 不画详情。
- 复验：导航 72/72；D5 24 页 98.48%（Wi-Fi 99.48%）；D1–D8 PASS；证据 `sim_ui_contact.png`。

## v0.9.102 — Wi-Fi 连接页参考实现固化进工作流（PR-0508）

- 用户令：Wi-Fi 连接这类页面以后直接按成熟示例做，AI 自动识别，不用再提醒。
- 新增 `reference/15_wifi_list_connect_pattern.md`：触发词、EEZ 单页结构（list_box/overlay_root/dlg_root）、
  native app/navigation/widgets/platform 分层、no-flow 改造点、验证四件套、四个坑。
- 入口：NO_FLOW §0 加一行「Wi-Fi 列表/连接页先移植 reference/15」；AGENTS 新增规则 12；
  `reference/README.md` 索引加一行。

## v0.9.101 — Wi-Fi 连接页完全对齐示例工程结构（PR-0507）

- w78 用户令：Wi-Fi 连接页要完全参考 `app-wifi-scan-conn-no-flow`，样式可调。
- EEZ：删掉「Wi-Fi 密码」「Wi-Fi 连接中」两屏（26→24 页），改成一个 Wi-Fi 页：
  `list_box`（LVGL List，行由 native 动态建）+ `overlay_root`（scrim+sheet+pwd_ta+keyboard）
  + `dlg_root`（忘记确认），对象名与示例一致（list_box/pwd_ta/kb_main/btn_refresh…）。
- native：按示例分层移植 app/{wifi_events,wifi_logic,wifi_view,wifi_model,wifi_text} +
  navigation/{wifi_nav,wifi_bind} + widgets/{wifi_list,wifi_busy,wifi_eye,wifi_skin} + platform；
  删除自研 wifi_ui.cpp。样式改为 w78 深色（行高 56、720 宽、字体 cn12f）。
- 多屏差异两处：① busy 遮罩挂 `lv_layer_top`（示例单屏才挂 objects.main）；
  ② `lv_snapshot` 只拍当前屏、不含 layer_top，遮罩证据要用可见性断言/整窗截图。
- 验证：导航 72/72；假后端 扫描12→开半页→密码→连接→列表把新网络置顶并标已连接；证据 4 张截图。

## v0.9.100 — Wi-Fi 列表接真扫描 + 运行时中文字库档（PR-0506）

- w78 ⑦-2：`src/native/wifi_ui.cpp` 把平台快照写进 Wi-Fi 三屏——列表 5 行（名称/加密·RSSI·频段/锁/状态）、
  扫描/断开命令、行点击选网、密码页运行时 textarea+keyboard、连接三态（连接中/成功/失败）与页间跳转。
  实测真 wlanapi 扫描 12 个 AP，列表与徽标正常；导航回归 82/82。
- 新坑：设计期字体子集覆盖不到运行时中文（SSID），新建控件又默认 Montserrat → 全豆腐。
  修法：同 TTF 再烘 `cn12f`/`cn24f`（GB2312 A1–D7 + ASCII + U+00B7），设计里引用让 EEZ 导出，
  lv_conf 开 `LV_FONT_FMT_TXT_LARGE`；D3 门禁改为「每个字体条目都有 .c」。
- 落点：NO_FLOW §3.2 F7；reference/07 字体节；intake P-0225；证据 `designer_annotated/wifi_ui.png`。

## v0.9.99 — D5 单实例跑完 26 页；页签激活 + 可见画布（PR-0504）

- 用户要求 D5 不要反复开关 EEZ 窗口：改为整轮只启动一次，逐页双击树节点 + 激活页签。
- 单实例早期抓到旧页（92–94% 假数字），根因两条：① 只判"页签文本存在"，没验目标页签自身 selected
 （整页多个 tabset 各有一个 selected）；② `grab.js` 按最大画布取，隐藏页签画布同为 800×480。
- 修复：`CLICK_JS` 校验目标页签自身 selected；`grab.js` 新增 `--visible` 只取视口内画布；
  `d5_pages` 固定 `--canvas --visible`，整轮单实例、单页连续失败才重启兜底；新增 `--pages` 小样本复测。
- 结果：26 页平均相似度 **98.46%**、最低 97.52%（主控）；Wi-Fi 三屏 97.89 / 97.57 / 99.10%；
  导航仿真 82/82 PASS；D1–D4、D6–D8 PASS，D5 待人工确认。
- 落点：reference/14 §7 17–19；NO_FLOW D5 行；intake P-0224。

## v0.9.98 — 流程入口挂上问题索引（PR-0503）

- 用户问"工作流程里有没有问题索引"：此前只有 `intake/index.md` 和 README 提到 intake，流程正文没挂入口。
- NO_FLOW §0「求解顺序」改为先查 `intake/index.md`（一行一个 P-####，按现象/标签检索），并补「新问题修完
  用 `tools/log_entry.py problem` 登记、自动追索引」；FLOW §0 同步一句。
- AGENTS 铁律 4（留痕）补「追 `intake/index.md`，查问题先看这张索引」。

## v0.9.97 — 仿真窗口关不掉：自轮询 SDL 要自己处理 QUIT/CLOSE（PR-0502）

- 根因：主循环把 `SDL_PollEvent` 的每个事件都喂 `lv_sdl_mouse_handler`，
  `SDL_QUIT`/`WINDOWEVENT_CLOSE` 在 LVGL 的 SDL 驱动看到之前就被吞了（`LV_SDL_DIRECT_EXIT` 形同虚设）。
- 修复：轮询时先判 `SDL_QUIT` 与 `SDL_WINDOWEVENT_CLOSE` → `SDL_Quit()` + 退出；其余仍走鼠标 handler。
- 自证：新增 `run_sim.bat quittest`（`W78_QUIT_TEST=1` 预压一个 `SDL_QUIT`），退出码 0；导航回归 69/69。
- 顺带：构建目录改到工程 `tmp/sim_build`（原先落在 `design/tmp`，不符合过程件纪律）。

## v0.9.96 — ⑤ 导航闭环：绑定表 + 仿真真点击 69/69；生成器第⑨条（PR-0501）

- w78 实做：`design/nav_bind_gen.py` 从 nav_map 生成 `src/native/nav_bind_table.h`（62 静态 + 7 返回），
  native 统一挂 `LV_EVENT_CLICKED`；`design/sim_cmake` 起 PC_SIM（800×480），
  `run_sim.bat test` 无头注入真实 SDL 鼠标事件，逐边断言落点屏，**69/69 PASS**。
- 新硬口径（生成器第⑨条）：纯展示/装饰容器必须去掉 `CLICKABLE`（widgetFlags + clickableFlag），
  否则透明底板盖住按钮、画布正常但仿真/真机点不动。
- 自证坑：返回边测试必须先 `loadScreen(源屏)` 再点（否则点在非活动屏上）；indev 采样周期
  要留够（一次点击 ≈ 上下沿各 60–80ms），否则「有时 PASS 有时 FAIL」。
- 落点：NO_FLOW §2.2 生成器九条 + C 层判据改为真实鼠标事件；AGENTS 铁律 8 同步。
- 结果：D1–D4/D6–D8 PASS；D5 23 页平均 98.50%，仍待用户 `--b1-ok`。

## v0.9.95 — 分类码命名落地 + A9 对账；Edge 收尾按根 PID 杀树（PR-0499）

- 用户令：按 v1 名称改 EEZ 变量，查漏并核错。
- 生成器：identifier 改为 `{页ID}_{类别码}{页内该类序号}`（码表在 `pages.IO_CODE`，判定用 `overview_pro.io_of`）；
  按钮子标签 `<id>_lb`，静态文字 `_stNN`，装饰仍 `_decoNN`。
- 门禁：`eez_check` A2/A3 的控件识别改为类别码正则；新增 **A9**（码 ↔ io 类一致、按类连续、无未分类命名）。
- 控件清单加「代号」列，可直接与 identifier、H5 分类三处互查。
- 实测：878 个 identifier 全唯一且全部符合命名式；171 个控件 = 期望 171，
  分类计数 `go 67 / hr 25 / hw 53 / r 3 / w 23`；D1–D4/D6–D8 PASS；主控 D5 仍 97.52%。
- 工具修复：`h5_edge.sh --kill` 先 `taskkill /T` 启动时记录的根 PID，再按 profile 扫；
  修前根进程一死子进程被重挂，留下 9 个锁 profile 的 msedge（实测 16 个整树杀净，残留 0）。

## v0.9.94 — 控件 identifier 按 H5 分类码命名（v1，后续迭代）（PR-0497/0498）

- 用户口径：H5 已给控件分六类，创建的控件名也要带分类码；`w`=写、`hw`=硬件、`r`=读，固定显示用专门前缀。
- 定稿 v1：`{ASCII页ID}_{类别码}{页内该类两位序号}`，码表
  `r` 内部读 / `hr` 外部读 / `w` 内部写 / `hw` 外部写 / `go` 跳转 / `sw` 手势 / `st` 固定显示；
  前缀最长匹配，序号按类独立，装饰仍叫 `deco`。
- 门禁要求：identifier 类别码 ↔ `io_of()` 六类必须一致；码表只在一处映射表定义。
- 落点：NO_FLOW §2.2「生成器七条」→「八条」；`reference/07` identifier 节新增码表与解析规则；
  `reference/14` 分类口径补 identifier 同源说明。
- 说明：v1 仅定名法与门禁口径；生成器改造与旧 `_wNN` 迁移在后续迭代做。

## v0.9.93 — H5 模板与当前源码同步；SVG 强制步骤清残（PR-0495/0496）

- 用户问"是否还留存 SVG 相关步骤""是否参考了本次 H5 源码与效果"。
- 模板：`tools/h5_overview_template.py` 从 w78 `design/overview_pro.py`（22:50 版）整体同步——
  右侧停靠栏、单一 `trail` 栈 + `pushTrail`、直接换页不做动画、`hotBack`、`crumbText`、
  确认门与 `node --check`；旧版的滑动过渡与 `swapBig(dir)` 删除。
- 文档：`reference/14` 抬头/三视图交互/换页动画条目同步；新增 D5 抓画布三条坑
  （多棵树选含根页那棵、点「行∩树视口」交集、差异 >20% 判抓错页）；门禁示例计数更新为 23/171。
- SVG：`reference/README` 改为"H5 为主、SVG 可选"；NO_FLOW §2.1 标注交付改为控件清单 + H5 停靠栏为主，
  单页标注图/树状总览降为可选；§2.0c 删除 `prototype/index.html` 第二载体说法。
- 保留的 SVG：框图（diagrams/01–03）、动效素材单页总览（ANIMATION_ASSETS §7）—— 非设计图步骤。



- 用户口径："现在设计图还是以 H5 为主吗，SVG 可以为辅，或者不生成"；旧"一律交 SVG 总蓝图"条款删除。
- 改动：NO_FLOW §2 表①行、§2.0 整节改写；§2.0c 删掉"SVG 先确认、H5 不替代 SVG"；
  FLOW §1 铁律 1 与"设计图交付形态"同步；README / QUICKSTART 卡 C 同步；reference/13 重写
  （删全览树 / 悬停预览 / prototype 等已被推翻的内容，改为三视图 + 停靠栏现状）。
- 不变：动效数值真值仍是设计源 `ANIM` + 分镜 PNG；H5 通过不替代 ④⑤ 的 EEZ 画布与仿真。

## v0.9.91 — 「系数」一词全部退役：统一叫相似度（PR-0492）

- 用户口径：不要"差异系数"，统一用**相似度百分比**；连产物文件名也不叫系数。
- 改动：`d5_相似度.txt`（原 d5_系数.txt 重命名）；三个脚本内的文件名与措辞同步；
  过时的单页脚本 `design/d5_compare.py` 删除（功能 = `d5_pages.py --page 主控`），门禁提示改指向 d5_pages.py。
- 历史条目（CHANGELOG/PROMPT_LOG 里的"差异系数"）保留不改，属当时事实。

## v0.9.90 — 生成器七条：把三类 UI 真缺陷写成硬口径（PR-0491）

- 本轮用户指出"明显 UI 问题"，逐张看并排图后定位到三类：
  卡片被做成按钮（文字压住设计标签）、行式控件文字居中且与标签重复、`fill=none` 被写成 `0XNONE` 触发 invalid color。
- 固化：NO_FLOW §2.2「生成器七条」；AGENTS 铁律 8 加指针；D5 指标改相似度（前一条）。

## v0.9.89 — D5 指标改为「相似度百分比」；invalid color 已修（PR-0490）

- 用户口径：不用差异系数，用**相似度百分比**（相似度 = 100 − 逐像素差异率）。脚本、汇总、记录文件与流程条款同步改口径。
- 同时修掉 EEZ Checks 报的 4 个 `invalid color`：装饰底板取色时只接受 `#RRGGBB`，`fill="none"` 的手势标注线不再被写成 `0XNONE`；`eez_check` 新增 A8 颜色合法性门禁。
- 复验：构建 12 文件、字体 16 个、`[EEZ_CHECK] PASS`（23 页 / 793 控件）。

## v0.9.88 — D5 全量 23 页出系数（每页重启 EEZ）（PR-0489）

- `design/d5_pages.py` 定为"每页重启 EEZ"：新 profile → 等 15s → 双击页节点（虚拟列表用滚轮定位）→
  等 3s → 抓画布；单页最多 3 次重试取最小系数（编辑器偶发重绘残影会把系数抬高）。
- 基准 = **H5 高清设计图**那张帧（Edge 渲染；cairosvg 缺中文字体会画豆腐块）。
- 结果：23 页全部出数，**平均 4.59% ｜ 最大 7.51%（窗帘详情）**；主控重测 2.48%。
- 边界：>5% 的页保留并排图，其中部分仍含编辑器重绘残影（如能源统计/场景详情抓到了上一页叠影），
  这些数只能当参考，需人工看并排图确认。

## v0.9.87 — D5 逐页跑：单页可靠，逐页受 EEZ 树虚拟化限制（PR-0488）

- 新增 `design/d5_pages.py`：一次启动 EEZ，逐页点树节点 → 抓画布 → 出系数；
  实测能稳定量到 8–13 页（1.26%–2.90%），但**页面树是虚拟列表**，滚轮只能滚到一部分节点，
  其余页点不中；切页后画布偶发未重绘（会抓到上一页或叠影）。
- 设计基准必须声明 `font-family="Microsoft YaHei,…"`，否则 cairosvg 渲出豆腐块（系数虚高）。
- 关键发现：**树节点要双击才真正切页**（单击只选中）；且首屏要等 ~20s（字体提取）再抓。
- 单页可靠通道复测通过：主控 **2.40%**（写法：新 profile 启动 → 等 20s → 双击 main → 抓画布）。
- 结论：D5 自动化只承诺**单页（主控）**；逐页批量受树虚拟化限制，其余页建议人工翻看，
  或改用"每页单独重启 EEZ"（约 23×25s，可靠但慢）。

## v0.9.86 — 23 页全量生成跑通：命名/字号四条规则（PR-0487）

- 生成器由单页扩成通用 `build_page()`，一次出 23 页 / 855 控件 / 1949 KB。
- 撞到的四个必须规则（已写进 NO_FLOW）：① 页名必须 ASCII（中文全消成 `SCREEN_ID___`）；
  ② identifier 全工程唯一（加页前缀，否则 `duplicate member deco_00`）；③ 字号从设计帧收集（写死漏 16/18/20/24/30/38/40）；
  ④ 替换后的字符要进字体子集（`✓→√` 之前漏进子集 → A6 报缺字）。
- 复验：`[EEZ_CHECK] PASS`（23 页 / 855 控件 / 16 字号）；构建 12 文件 + **20 个 C 文件编译通过**；
  主控差异系数 2.18% 不变。

## v0.9.85 — 每次生成 EEZ 都输出"差异系数"（用户令，PR-0486）

- 新增 `design/d5_compare.py`：一条命令完成「设计 SVG 栅格化 → 无头起 EEZ → 点开页节点挂载画布 →
  抓画布 → 逐像素比对」，打印差异系数并存 `designer_annotated/d5_系数.txt` + 并排图。
- 首跑：主控 差异系数 **2.18%**（阈值 30/255，差异集中在文字反锯齿与字重）。
- 顺带修两个顺序/超时坑：`wait_cdp` 把 45 当成绝对时间（永远超时）；构建会清空 `src/ui/fonts`，
  门禁必须先构建、再烘字体、最后统计（F5 已补这条）。
- 条款：NO_FLOW §2.2 的 D5 判据改为"打印差异系数并留证"；AGENTS 铁律 11 同步。

## v0.9.84 — 真编 C：EEZ 生成 ≠ 编译；克隆模板要清表达式属性（PR-0485）

- 用户问"发现编译错误没"——此前 D4 只跑 EEZ 代码生成（12 个文件），从未真编 C。
- 真编后抓到：`screens.c` 调 `get_var_pick_ssid______()` 未声明。根因是所有克隆来的控件模板
  都带 `hiddenFlag: "pick_ssid == ''"`（别的工程的表达式），EEZ 据此生成了变量读取。
- 修：`fresh()` 克隆后把 `hiddenFlagType/checkedStateType/disabledStateType/clickableFlagType`
  复位成 literal；D4 判据加 `gcc -fsyntax-only`（含 9 个字体 .c，共 13 个文件）。
- 复验：`[DELIVERY] D4 PASS ｜ 构建 12 行 built ｜ C 编译 13 个文件 全过`。

## v0.9.83 — 经验库瘦身：铁律一行一条，细节只留一处（用户令，PR-0482）

- 用户令：往经验库加内容时保留重要位置的关键事实，其余简化。
- AGENTS.md 铁律段由 12 条 × 2–3 行压成 **12 行**（一行一条 + 指针），全文 49 行 / 3.8 KB；
  同时在段末立约束：新规则只加两处（这里一行 + 对应文档一节），不在第三处复述。
- 口径修正：H5 已不做过渡动画，铁律 6 由"改 H5 动效"改为"改 H5 交互/实时效果"。


## v0.9.82 — 交付门禁 D1–D8：一条命令跑完，FAIL 不许交付（用户令，PR-0481）

- 用户令：EEZ 设计比对、编译核对及其他核对要进流程，交付严格执行。
- 新增 `design/delivery_gate.py`：D1 结构对账 / D2 文本覆盖 / D3 字体 F1–F6 / D4 无头编译 /
  D5 画布比对（人工确认后 `--b1-ok` 打标记）/ D6 跳转闭环 / D7 过程件清理 / D8 留痕。
- NO_FLOW §2.2 的"交付前四件"升级为 D1–D8 表；FLOW 与 AGENTS 铁律 11 同步。
- 首跑实况：D1–D4、D7、D8 PASS；D5 未做画布比对、D6 卡在"场景详情无权威入边"（A/B 待定）。

## v0.9.81 — 字体问题索引化：F1–F6 唯一清单（用户令，PR-0480）

- 用户令：字体反复出问题，要在流程的注意事项里做索引，避免重复描述与漏项。
- NO_FLOW §3.2 由散 bullets 改为 **F1–F6 表**（三件套 / 条目形态 / 字形覆盖 / 多字号 / 烘字体 / 验收三连），
  每行附"不过会怎样"；reference/07 保留字段级细节并加指针（编号管要不要做，07 管怎么写）。
- AGENTS 铁律 10 指向该清单（每会话自动加载）。

## v0.9.80 — EEZ 工程交付前四件：构建 / 字体 / 文本覆盖 / 画布比对（PR-0479）

- 用户质问"交付 eez 工程时是否做 UI 比对、编译 OK"——当时确实只做了结构断言，构建与视觉比对都没做。
- 补齐三件并固化成流程：无头 `cli_build.py`（此前缺 `settings.build.files` 12 条模板，会"构建成功却零产出"）；
  9 个字号单独烘字体；设计文字 39/39 覆盖对账（含 ‹›−▶◀ 替换表）。
- 仍缺：B1 画布截图 vs 设计图目检（需渲染，见 NO_FLOW §2.2 第四件）。

## v0.9.79 — 中文只在索引里出现：--json 留痕 + texts 索引 + AST 门禁（PR-0476/0477）

- 用户令：中文反复出错，流程里用索引/引用避免重复。
- `log_entry.py` 加 `--json <文件>`：全部字段从 UTF-8 JSON 读，参数里不再出现中文
  （此前两次因 `--out` 里的英文双引号被截断报 unrecognized arguments）。
- 工程侧新增 `design/texts.py`（可见文案按 key 存放）与 `design/lint_text.py`（AST 检查造控件调用里的中文字面量）。
- 条款：PLAYBOOK §2.10「中文只在索引里出现」三条 + AGENTS 铁律 9；tools/README 登记 --json 用法。


---

## v0.9.78 — 默认结构采集器：所有控件都按原生字段改（用户令，PR-0475）

- 用户令：不只按钮，所有控件都用 EEZ 原生默认字段；不知道默认长什么样就临时建工程新增一个控件看。
- 新增 `tools/eez_defaults.py`：扫描全库 48 个 .eez-project，按类型采默认字段结构（含「父+子」组合），
  一次采到 53 种结构（label/button/container/switch/slider/bar/tabview/textarea/keyboard…）。
- 生成器改为"类型模板 → 克隆 → 只改几何/identifier/文本"；主控的卡片改用 Container+居中子标签，
  顶部入口与安防仍用 Button。通道：官方引擎烘焙成功 + [EEZ_CHECK] PASS（控件 30 / 字体覆盖 429 字）。
- 条款同步：NO_FLOW §2.2、FLOW 第④行、AGENTS 铁律 8（改成"所有控件"并写明采样/临时工程两种取法）。

## v0.9.77 — 立为流程条款：EEZ 控件必须克隆默认结构（用户令，PR-0474）

- 用户令：以后一律按 EEZ 默认控件结构来改，写进流程，避免遗忘。
- 落点：NO_FLOW §2.2 开头加「生成方式」三条；FLOW 第④行加同向指针（成对文件）；
  AGENTS.md 铁律 8（每会话自动加载）；字段级对照仍在 `reference/07`。
- 判据不变：按钮恰一子标签、子标签文本非空、按钮自身无 `text`、字体覆盖所有字符。

## v0.9.76 — 控件必须克隆默认结构：按钮文字在子标签（PR-0473）

- 用户当场指出"按钮都没有文字"，要求每个控件先严格按 UI 默认配置、再修改。
- 根因：EEZ 的 `LVGLButtonWidget` **没有 text 字段**，文字是内部唯一的子 `LVGLLabelWidget`
  （`align: CENTER`）。我把 text 写在按钮上 ⇒ 按钮能显示但一个字没有，且不报错。
- 改法：新增 `design/eez_defaults.json`（逐字段取自可打开工程，objID→`__OID__` 占位），
  生成器全部改为"克隆默认 → 只改几何/identifier/文本"；门禁加三条（按钮恰一子标签、子标签文本非空、
  按钮自身不许有 text）。EEZ 检查器 A4 同步改成按子标签判定。
- 复验：官方引擎烘焙成功；[EEZ_CHECK] PASS（页 1 / 控件 30 / 字体覆盖 429 字符）。

## v0.9.75 — 字体条目的真输入是 lvglGlyphs.encodings（PR-0472）

- 现象：脚本生成工程打开无字；用官方引擎单烘报 `-Infinity`。
- 根因：字体条目只写了字符串 `lvglRanges`，缺 `lvglGlyphs.encodings`（结构化 [{from,to}]）——烘焙按后者算范围，空则崩。补齐后官方引擎烘焙成功（435 字形 → ui_font_cn14.c 248 KB）。
- 单变量裁决过程：先怀疑范围串 → 换成 32-126 仍失败；再怀疑子集 TTF → 换原字体仍失败；
  对照同库可打开工程成功 → 逐字段 diff 抓到缺字段。
- 新增 `design/eez_check.py` 七查（页尺寸/控件数/框/文本非空/字体条目/引用/字符覆盖/ID 唯一）。

## v0.9.74 — 脚本生成 EEZ 工程：字体三件套缺一就整屏无字（PR-0471）

- 症状：脚本生成的 .eez-project 打开后没有字。根因是缺字体三件套：`fonts[]` 条目、TTF 文件、
  控件的 `localStyles.text_font` 引用——三样缺一，EEZ 就用默认字体渲染，中文全丢。
- 做法：fontTools 按设计源全量文本裁子集（435 字形 / 87 KB），字体条目照可打开工程抄
  （name/source.filePath/size/bpp 4/threshold/glyphs:[]/lvglRanges 码点串），控件统一引用 cn14。
- 两个必须核的点：① 源字库 cmap 不覆盖的装饰字符（‹ › − ▶ ◀）要先替换成等价 ASCII，否则豆腐块；
  ② 字体条目声明的码点必须 ⊆ TTF 实际 cmap。
- 工程侧新增 `design/eez_check.py`：A 层对账七查（页尺寸/控件数/框/文本非空/字体条目/引用可解析/
  文本字符被字体覆盖/identifier 与 objID 唯一），主控首跑即抓到上述两条。

## v0.9.73 — H5 跳转演练改为直接换页，不做过渡动画（用户定，PR-0468）

- 用户定：界面跳转可以不使用滑动。跳转演练的 swapBig 改为整页直接替换，删掉进出场 CSS 与 keyframes。
- 副作用是好的：那次"换页动画只认最后一层"的层泄漏问题从根上不存在了（实测连跳 8 次 .pg 恒为 1）。
- reference/14 §1 表格与 §4 硬规则同步改写（矛盾直接改旧句，不留修订注）。

## v0.9.72 — 「还是不对」的取证打法 + 动态返回三条硬规则（PR-0467）

- PLAYBOOK §2.8b：连续两轮"还是不对"就停止改码，改为把内部状态印到界面上 + 只索要一个可观测值；
  并自查"同一控件多容器渲染 → 每个容器各验一次"（w78 的返回有四个面，前三轮只验了一个）。
- reference/14 §4：动态返回三条硬规则（单一来路栈 / 返回不打开面板 / 面包屑写出返回目标）。
- UI_BEHAVIOR_CONTRACT 铁律 7 补：多容器各验热区、界面写明返回到哪。

## v0.9.71 — 来路合并为单一栈：房间→详情→返回 回房间（PR-0465）

- 症状：从房间页点「详情」，返回跑回主控。根因：总览用 mapHist、演练用 trail，两套来路互不相通；
  跨视图或在某视图未留痕时，返回只能掉回根页。
- 修：两个视图共用 `trail`，压栈收成 `pushTrail()`（同一页不重复记、上限 10）；总览返回 = 收放大 + 弹栈 + 选回上一页。
- 复验（真实鼠标）：演练 主控→主卧→灯详情→返回=主卧；总览 主控→主卧卡→详情胶囊→返回=主卧（并收起放大）。

## v0.9.70 — 返回不该打开放大图（PR-0464）

- 症状：点详情页的「‹ 返回」反而出现放大图。根因：返回分支里调用了 openDock() 去"复原"那一页。
- 修：返回 = closeDock() + selectCard(上一页)（新原语，不压来路栈）；放大只保留「点卡片本体」一条入口。
- 同时修正 reveal() 的来路压栈（原先压完又弹掉，等于不记）。
- 复验：点主卧卡→点灯详情卡→点帧内退回 = 放大收起、选中回主卧；标签胶囊退回同效；
  开栏后点跳转标签仍滑动且放大图跟随。

## v0.9.69 — 总览里的「‹ 返回」真能点了；生成器加 JS 语法门禁（PR-0463）

- 症状：详情页卡片上的「‹ 返回（来路）」点不动。根因两层：渲染成了不可点的静态胶囊；调用点按 target 分支。
- 修：nav 一律走 pill()，无 target 的返回渲染成真按钮 data-back；跳转演练=轨迹回退，分层总览=回来路栈顶，
  无来路则回主控并在面包屑写明「没有来路，已回主控」。reveal() 选页也压来路栈。
- 修的过程中我打坏过一次括号导致整页全白 ⇒ 生成器收尾加 `node --check` 校验内联 JS，写坏页面直接 FAIL。
- 复验：真实鼠标 A 有来路（灯详情→‹返回→主控）、B 无来路（直接点→回主控+提示）两场景通过。

## v0.9.68 — 共用详情页：来路返回 + 按来路取数；列表页改为数据驱动（PR-0460）

- 通用铁律加 7（共用详情页必须来路返回、数据按进入设备取）与 8（列表条目数由数据决定，超出滚动、零条空态）。
- w78 落地：详情页 6 页的返回统一成「‹ 返回」、行为记 `返回`（目标动态）；页面 22→23（新增空房间状态页）；
  房间设备区按 `room_devices()` 类型分组排序渲染，>6 台纵向滚动+露半行+滚动条，0 台空态。
- 门禁跟着改：nav_audit 认动态返回边（有回退能力即可）、A 检查排除动态目标、计数口径含返回；
  preview_pages 图例与断言接受 `返回`。
- 复验：真鼠标 主卧→床头灯详情→‹返回→主卧；全部设备→行主灯详情→‹返回→全部设备；
  布局单测 6 台不滚 / 7 台滚 / 0 台空态。

## v0.9.67 — H5 换页层泄漏导致「有时回不去」（PR-0459）

- 症状：跳转演练快跳多次后，页面层 `.pg` 越堆越多（实测 30 跳后仍留 28 层且不回收），帧与当前页可能不一致。
- 根因：`swapBig` 把第一层当旧帧，当前帧其实是最后一层 ⇒ 旧层永远没人清。
- 修：以最后一层为当前帧、其余残层就地删，只留「当前帧+退场帧」；路径上限 10 跳；路径条改单行横向滚。
- 复验：30 跳中每采样 `frameIsCur=true`、层数恒 ≤2、静置回到 1；真鼠标 主控→设置→关于→上一页→上一页 全程一致。

## v0.9.66 — 跳转审计七查：把「这页怎么进来的」做成门禁（PR-0457）

- w78 新增 `design/nav_audit.py`：目标存在 / 入边 / 出边 / BFS 可达 / 状态页登记 /
  三处计数逐页对齐 / 跳转表↔控件表双向对账。
- 首跑即抓到真漏洞：`场景详情` 唯一入口（主卧·晚安模式）行为是「下发硬件」却挂了 target，
  被判成卡片残留 ⇒ 权威边入度 0、从根不可达。
- 口径写进 `UI_BEHAVIOR_CONTRACT.md` 通用铁律 3 与 `reference/14` §5。

## v0.9.65 — 通用铁律加两条：覆盖表不许吃掉真值行为；「这页怎么进来的」＝分叉信号（PR-0456）

- 触发：w78 的 `overview_pro.OVERRIDES` 把「设置·关于」判成内部读，导致关于页在 H5 里没有入口（PR-0455 已修）。
- `UI_BEHAVIOR_CONTRACT.md` 通用铁律加第 5、6 条；AGENTS.md 铁律摘要加第 7 条；`reference/14` §5 门禁与坑 9 同步。
- 生成器侧已内建 assert（覆盖使 behav=换页 的控件失去 nav 就报错），w78 重跑 [GATE] nav 64 / in_read 2。

## v0.9.64 — 设计图载体收归 H5；默认不生成「设计图查看器」页（用户定，PR-0451）

- 新增同步铁则：核对通过后再改 H5 的实时效果（跳转/动效/交互），「高清设计图」页签必须同步改，二者同源。
- 默认不再生成 `design_review.html` 这类查看器页；w78 工程里刚建的那份已删。
- 落点：AGENTS.md 铁律 6、NO_FLOW §2.0c 交付方式段、FLOW 同段、`reference/14` §1 与 §4 各一条。

## v0.9.63 — 核对交付方式定档：给 HTML 路径，不做对话内嵌预览（用户定，PR-0450）

- 交付口径改写：AGENTS.md 铁律 6、NO_FLOW §2.0c、FLOW 同段、`reference/14` §1 与坑 7 全部改为
  「给工程内 HTML 绝对路径，用户自己在浏览器打开」；对话内嵌预览不再是核对通道。
- `overview_pro.fragment.html` 保留生成，但定位改成「嵌进自有页面时才用」。
- 工程侧实例：w78 `designer_simple/design_review.html`（设计图查看器，只用 `<img>` 指同目录 SVG，
  不复制内容，避免第二真值）。

## v0.9.62 — H5 评审页顺带出「可内联片段」，对话里直接点（PR-0445）

- 生成器一次出两份同源产物：整页（本地双击核对）+ 片段（`present_visualization` 内联预览）；
  片段由 `fragment()` 从整页剥壳生成，不手搓第二版。
- bootstrap 改 `readyState` 兜底：内嵌时 `DOMContentLoaded` 已过去，不兜底就白屏。
- 实测（无头 Edge 跑片段）：22 卡 / 6 图例 / 停靠栏 745px / 行内滑动 4→163→3214 落定 / 网络失败 0。
- 模板与工程实例正文重新比对仍逐字节一致。

## v0.9.61 — H5 评审页方法定稿：模板 + 无头真实鼠标通道（用户定，PR-0444）


- 新增 `reference/14_h5_review_overview.md`：分层总览 / 跳转演练 / 停靠放大栏三视图口径、
  6 类数据流向标注、排版与交互硬规则（逐条来自本轮改判）、门禁、八个踩坑、边界。
- 新增模板 `tools/h5_overview_template.py`（w78 `design/overview_pro.py` 的实例，用户认可为模板），
  文件头写清「换工程只改这五处」。
- 新增通道 `tools/cdp/h5_edge.sh` + `tools/cdp/h5_probe.js`：无头 Edge 真实视口 +
  CDP `Input.dispatchMouseEvent` 真实鼠标 + 截图 + 网络失败计数 + 按 profile 杀整棵进程树。
- 立此存照的反面教材：`element.dispatchEvent` 绕过命中测试 ⇒「点了能跳」是假通过；
  Desktop 内嵌 Browser 无可见窗口时视口 `0x0` ⇒ 几何断言全量歪。
- 索引同步：`reference/README.md`、`tools/README.md`、顶层 `README.md` 目录树、
  NO_FLOW §2.0c 与 FLOW 同段指针（成对文件）。

## v0.9.60 — 全览"小图看位置、大图看箭头"

- 用户定：缩略可以小，但**每个触发跳转的控件必须有箭头指示**，放大后仍要清晰。
- 节点宽 320 → **240（0.3 倍）**；缩略图上给会跳转的控件打**橙色序号点**（位置=控件框左上角，编号=控件表行号）。
- 悬停浮层 `#peek` 升级为**全尺寸 + 跳转标注**：同一批控件画橙框、序号、**箭头指向「→ 目标页」标签**；
  标注直接由 rows（box+target）生成，与热区同源，不另画。
- 实测：节点宽 240；「通知中心」缩略含 4 个序号点；悬停浮层 4 框 / 4 序号 / 4 箭头，
  目标标签 = → 主控、→ 灯详情、→ 传感详情、→ 能源统计；缩放 0.35（小视口下限）。
- 同步：NO_FLOW §2.0c、`reference/13` §2b。

## v0.9.59 — 全览可读性下限：节点 320 宽 + 悬停 800×480 全尺寸预览

- 用户报"全览的图片太小，每个页面至少能看清楚"。节点宽不再按画布自适应缩小，**固定 320（0.4 倍）**，
  画布按最挤一行放宽（本工程 3168），横向靠滚动。
- 新增**悬停全尺寸预览**：鼠标移到节点即弹该页 800×480 原尺寸帧，缩放夹在 `0.35–1`、越界自动翻边、移出即隐藏。
- 踩坑两条入表：自适应缩略会把节点压到 0.19 倍看不清；用正则回读 `transform` 求缩放会丢符号算出负值——缩放要存变量。
- 实测：节点宽 320、树宽 3168；悬停「空调详情」浮层 cap=「空调详情页 · 800×480 全尺寸」、transform=scale(0.35)
  （小视口下限），移出后 display=none。
- 同步：NO_FLOW §2.0c、`reference/13` §2b 与踩坑表。

## v0.9.58 — 全览树的节点必须内嵌真实设计图

- 用户定：按流程先出设计图，且**全览里要包含设计图**——树上每个节点直接嵌该页 800×480 帧的等比缩略，
  不是文字方块；帧与 H5 单页复用同一段 SVG 字符串，不另画、不用截图。
- 画布固定 1560 宽，节点宽按最挤的一行自适应（`min(168, 可用宽)`），避免右侧节点被裁。
- 实测：22 节点每节含 1 个帧组、树宽 1560；点「安防」进单页热区仍为 0（确认门生效）、
  右侧显示"全览尚未确认"；无入口页仍 1 个红框（离线态）。
- 同步：NO_FLOW §2.0c 全览态条目、`reference/13` §2b。

## v0.9.57 — ②b 加"全览确认门"：确认后才出页面连接 + AI 预估控件图

- 用户定：H5 全览**先出、先确认**；确认之后才同时生成 ① 可点跳转（页面连接）② **AI 预估控件图**
  （逐屏真实帧 + 控件表，标题写明「AI 预估控件图，待你改口径」）。
- 机制：确认状态落在工程 `design/flow_state.json`（`overview_confirmed`）；生成器默认读它，
  `--confirmed` / `--tree-only` 可强制。未确认时前端不建热区、控件表换成"全览尚未确认"提示。
- 顺序定稿：SVG 设计图 → H5 全览 → 用户确认全览 → 页面连接 + AI 预估控件图 → 用户在 SVG 截图上改标注
  → 改设计源重生成（永不手改 HTML）。
- 同步：NO_FLOW §2 表 ②b 行与 §2.0c、`reference/13` §2a。实测：未确认态热区 0/表 1 行提示；
  确认态热区 9、表 13 行、点「通知按钮」落通知中心。

## v0.9.56 — 更正 v0.9.55：观感词要先出四案对照，用户终选纯黑（A 案）

- v0.9.55 把"再浅一点的黑"推论成"提亮盘身 + 加外缘环 + 同心纹"并落地（C 案）；用户看对照图后选 **A：盘身 (56,56,72)、无边缘、无纹路**。
- 结论改写：ANIMATION_ASSETS §6 第 4 条与 cases/B24 §3.1 改为**"太暗"有两条路（加轮廓 / 提主体色），先同尺度出四案让用户点选，别替他推论**；轮廓路线的参数与判据保留为备选口径。
- 工程侧：watch2 `build_music_vinyl.py` 的 `RIM/GROOVES` 退回 None，`BODY=(56,56,72)`；四案出图入口 `design/vinyl_contrast_opts.py` 留着，切方案直接重跑。
- 复验：④-A 323/323、无头仿真 167/0、I4 精灵帧 0.47MB、上屏盘身像素 (56,56,72)。

## v0.9.56 — H5 默认打开即全览，随第①步 SVG 一起产出

- 用户定：设计图的 H5 版本**默认就是全览那张**——第①步出 SVG 时同时生成 `prototype/index.html`，
  打开直接落在全览树（`#work` 才进单页）。SVG 仍照常产出留档，作逐屏像素核对载体。
- ②b 的职责收窄：标注到位后**只给 H5 补热区**（可点态），不再决定 H5 出不出现。
- 推翻 v0.9.55 的"两道入口门、缺一条不出 H5"——那是把全览态和可点态混成一步。
- 同步：NO_FLOW §2 表 ②b 行与 §2.0c、kit README 索引、`reference/13` §2a。

## v0.9.55 — 深色 UI 黑素材的对比度做法（ANIMATION_ASSETS §6 第 4 条 / B24 §3.1）

- 用户口径"黑色好看，再浅一点的黑"⇒ **不靠整盘提灰**，靠外缘高光环 + 同心纹路造轮廓，盘身只比底色亮一档。
- 判据换成**上屏后**的径向亮度剖面：边缘与纹路要各成一个可测峰（本例 r=32→143、r=18~26→98~110、盘身 77、底色 10）。
- 反例：整盘提到 (120,126,140) 时用户判"不是黑色好看"，(56,56,72) 无轮廓时判"还是黑的"。

## v0.9.55 — H5 核验独立成第 ②b 步，并定下"标注→改设计源→重生成 H5"回路

- 用户定：H5 不挂在 ①/② 之下，**独立成步 ②b**；入口是两道门——① SVG 设计图已确认、② 控件标注已收到。
- 标注回路：用户在 **SVG 截图**上标序号/类型/跳向/硬件 → AI 改**设计源**（控件语义表 + `nav_map.py`）
  → 重跑生成器刷新 H5；**不手改 HTML**（否则 H5 成第二真值）。
- 出口判据：用户点验通过 + 全览树无红框（状态页除外）+ 门禁全绿；H5 通过不替代 ④⑤。
- 表述保留"七步主线"编号不动（③–⑦ 被 AGENTS.md 与大量记忆条目按号引用），新步记作 **②b**。
- 同步：NO_FLOW §2 表新增 ②b 行 + §2.0c 改写、FLOW 指针、kit README 索引、`reference/13` 新增 §2a。

## v0.9.54 — 新增 cases/B24：精灵动图"上屏发黑"根因链（占比先于颜色）

- 五轮返工全程复盘：抠黑抠掉盘身 → 自绘盘 + 叠白线 → 上屏仍"黑" → 提亮盘身（治症状）→ 用户拿对照图点出**盘径取错**才是根因。
- 三条根因排序：①主体被抠掉 ②主体占画布比例（并集裁框把飘散弧线算进画布）③判色底色（GIF 白底 vs 页面 #0A0A0F）。
- 量法入档：径向亮度剖面量主体半径、上屏直径 = 2×主体半径/画布×size、圆表放大上限反解 `u²+(d+u)² ≤ (R−8)²`。
- 另记两个工装坑：改外观走参数化生成器（手改 PNG 会被重烘吃掉）；无头截图落在 **exe 工作目录**，量图前先核 mtime。
- 同轮落地：动图原件单一目录 + MANIFEST（§8 / v0.9.52）、盘身回用户原色 (56,56,72)、盘径铺满 r=80/160、精灵 68px。

## v0.9.54 — 纠偏：设计图 v2 的顺序是「先 SVG 确认，再用 H5 核验」

- v0.9.53 写的「SVG 内容并入 H5、`*.svg` 后期只作留档、不再必须逐张交付」**过头**，与 §2.0
  「第①步一律交 SVG 总蓝图并经用户确认」冲突。用户纠偏：工作流仍**先出 SVG 设计图**。
- 正确口径：§2.0 SVG 设计图 = 正式交付与确认载体（未降级）；§2.0c 的 H5 用在**确认之后**，
  只承担「控件布局 + 跳转关系」的呈现与点验，不替代 SVG、不新增第二真值。
- 已同步改：NO_FLOW §2.0c 标题与表①行、kit README 索引行、`reference/13` 定稿说明与 §2b 标题。

## v0.9.53 — 素材上屏"发黑/看不见"三条根因（ANIMATION_ASSETS §6 末）

- **主体占比**：并集裁框会把飘散件（声波/速度线）算进画布，主体被挤小；先做径向亮度剖面量出主体半径，再乘 size/画布得上屏直径，放大上限用表圈安全半径反解。
- **底色判色**：盘身/主体色必须在页面真实底色上判亮度差，GIF 查看器白底判出来的"深灰"落到近黑页面就是黑。
- **改色走生成器**：原件→帧表的脚本参数化（盘身色、半径、阈值），不手改 PNG，避免重烘丢改动。
- 触发：watch2 音乐页黑胶五轮返工（唱片只占画布 49% ⇒ 56px 上屏仅 27px；用户拿 `vinyl_gray_160.gif` 对照点出盘径才是根因）。

## v0.9.53 — 设计图 v2 补全览树，H5 定为统一载体（用户定）

- H5 顶栏加 `全览`：BFS 分层树，顶层=主页；实线标控件名=跳转，青色虚线=返回，
  硬件/只读用方框标签不画线，无入口页标红。`#tree` 可直开。
- 口径变更：**SVG 内容并入 H5，`*.svg` 后期只作留档、不再必须逐张交付**（§2.0c 已改）。
- 新增两条踩坑：`back` 行混进跳转边表会把返回画成实线；场景设备格缺「详情」会让详情页永远进不去
  —— 门禁补"每个非根页至少 1 条入边"。
- 实测：w78 全览 22 节点、1 个红框（离线态=状态页）；点节点跳页、主卧 7 热区含晚安模式→场景详情、
  配网中「下一步」→完成 均通过。

## v0.9.52 — 动图原件归集与留档口径（ANIMATION_ASSETS §2 步9 / 新增 §8）

- 一个工程只留**一个原件目录**：当前设计源引用的每张动图，其站内原始 GIF（未裁框/未染色/未压缩）都收进去。
- 同目录出 `MANIFEST.md`（页面→帧表→原件→作者→许可→直链→SHA256）+ `manifest.json`；收集脚本已存在不重下。
- 换过件的停用帧表与候选帧表**直接删**，留档职责转给原件目录；台账里指向旧目录的行同步改写，不留修订注。
- 触发：watch2 2026-11-03 用户要求"记住当前所有动图原件，放单独文件夹，多余的删掉"。

## v0.9.51 — 设计图 v2：SVG 总览 + H5 可点原型（用户定）

- 第①步交付在 SVG 总蓝图之外**加 `prototype/index.html`**：点界面里的换页控件直接跳目标页，用户亲手核跳转逻辑。
- 硬约束：H5 只内联设计源渲染的帧 + 叠透明热区，**不重画界面**；热区框与标注图共用同一控件框坐标。
- 门禁五条：目标页存在、非根页恰 1 个返回且为换页、每页行数不撑破表格、序号唯一且框有效、屏数下限；
  热区只叠 `nav`/`back` 类控件，开关/滑条/场景不跳页。
- 流程落点：NO_FLOW §2.0c（成对文件 FLOW 加指针）；做法与踩坑 `reference/13_design_v2_h5_prototype.md`。
- 首个落地：w78-tabview-smart-home 22 屏 / 63 个可点控件；浏览器真点三条链通过。

## v0.9.50 — 自检默认无头后台 + 跑完即退

- 用户定：AI 自检 UI 不弹仿真窗口（WATCH_AUTOTEST 自动切 SDL dummy）、结束 exit(0)；
  需要看窗口时由用户点名。dummy 下帧节奏偏快，手势断言 settle frames 提到 120/150；实测 167/0、60~114s。

## v0.9.49 — 定稿默认配置：20 帧/页 + 只播当前页（生成器产出）

- 用户定：每页 20 帧（I4 464KB、app 1.49MB）；"非当前页不动画"为默认配置。
- `emit_watch_anim()` 随生成器每次产出 watch_anim.c（14 精灵/25 屏，SCREEN_LOADED start/delete）。

## v0.9.48 — 精灵性能两条：只播当前页动画；帧名用原始下标

- §6 补：切屏时 `lv_animimg_start` 当前屏、其余 `lv_animimg_delete`（watch2 14 条定时器不再空跑，+2KB）。
- 坑：自烘帧按抽取序号重命名会与生成器引用错位（引用的仍是旧 I8 帧），必须用原始帧下标。

## v0.9.47 — B23 补"精灵帧压缩实测"：I4 + 抽帧 5.65MB→0.45MB

- EEZ bpp 对应表（32/16/8/4 → ARGB8888/RGB565A8/I8/A8）；自烘 I4 布局与管线顺序
  （build_watch_ui → cli_build → font_bake → bake_sprite_i4）；watch2 实测 app.bin 6.69→1.72MB。

## v0.9.46 — 新增 B23：UI 占用实测（P4 模板部署 + ui_size_report）

- 案例：把 UI 拷进 P4 模板（备份原 ui/main.c、补回 CMakeLists、关 demo）→ 用自写 bat 设
  IDF_PATH/IDF_TOOLS_PATH/工具链 PATH 编（export.bat 在 Git Bash 不可用）→ `ui_size_report.py` 出最终链接占用。
- 判读：图片在 flash 是未压缩原始像素（ARGB8888=w×h×4）；`.eez-project` 的 PNG base64 不算占用；
  附 ARGB8565/8bit/4bit/Lottie 压缩对照与 watch2 实测（UI 6.00MB，帧 5.65MB）。
- 前提：模板不在本机时先请用户提供示例工程，不拿源码求和冒充固件占用。

## v0.9.45 — §6 补"精灵清晰度四条"

- 用户报"动图有压缩"后定：帧按显示尺寸 LANCZOS 内嵌（bpp32 不量化）；上屏取安全余量上限（60px）；
  嵌帧必须应用 tint（否则 EEZ 显示原色帧）；判糊必须同尺度对比（设计页 vs 仿真 1:1）。

## v0.9.44 — 总则加"求解顺序"：先查经验库，命中照做

- 用户明令（2026-11-02）：查找问题解决方法时**优先从本地经验库获取**。
- 落点：仓库根 `AGENTS.md` 标题下置顶一条 + 本文件 §0 总则首行；未命中才联网/试验，事后回写。

## v0.9.43 — 精灵动图进 EEZ：AnimationImage（lv_animimg）接入口径

- `ANIMATION_ASSETS.md` §6 补"进 EEZ"：`LVGLAnimationImageWidget`（images/duration/repeatInfinite）+
  帧位图按显示尺寸 bpp32 内嵌；样板 w1-animation-image；CLI 构建后核对 images/fonts 产物。
- watch2 实测 12 个 animimg、383 帧、④-A 321/321、仿真链接通过；记 Flash 预算与 bpp16 压缩方向。

## v0.9.42 — 动图普查提速 8~10 倍：合并解码 + numpy 打分 + 全局 CDN/分数缓存

- `anim_fast.py`：`analyze()` 单次采样出节拍+风格（旧版两遍解码），8 帧×96px、numpy 向量化 ink/色数/细度；
  打分 1.6s→284ms/件（6 线程 ~73ms）；全文抓页/下载/打分并行；扫页不再重编码 GIF。
- 全局 CDN 缓存 + 分数库：同素材跨页/重跑零重复下载/计算；旧账本可硬链接灌缓存。
- 实测 700 件整页：冷跑 277s、全缓存 127s。§7 执行入口改为优先 `sweep_fast`。

## v0.9.41 — §7 补执行入口：脚本三件套 + 复制改 GROUPS 即起跑

- 用户问"下次是否照此方法"：把可执行入口写进 §7——`anim_search.py` 公共函数 + `anim_*_full.py`
  整页普查主线 + `anim_heart_shape.py` 形状筛；新需求复制只改 GROUPS/目录/前缀。
- 附实测规模（消息 830→614 格、睡眠 1300+），选定后串 §2-7 授权 + §6 门禁 + PORTLOG。

## v0.9.40 — §2 步骤7 加 JSON-LD 授权对账法（免人眼对卡片）

- free-animations 页内嵌 JSON-LD：预览 gif 与**紧随其后**的 name/isPartOf.url/creditText 同属一条记录；
  按 contentUrl 定位→取详情页→`<title>` 以 Free 开头即 Free 款。watch2 用心跳红心+跑步小人两件实测核准。

## v0.9.39 — §7 补硬条款：每个动图需求都跑满全量流程，宁多勿少

- 用户重申（原话「搜索每一个动图都要使用这个步骤，尽可能搜索多一些」）：广度是硬要求——
  词表只扩不缩、`?page=N` 翻到空、合格不设上限；禁止「少搜一点先给看看」。§7 首段同步改写。

## v0.9.38 — 素材检索改"全量单页总览"（用户明令，替代一次一种风格）

- `ANIMATION_ASSETS.md` 新增 §7：一句需求 -> 词表扩全（同义/动作/器械/形状 40+ 词 x 2~3 页，`?page=N` 可翻页）
  -> 一次抓完 -> **一张 SVG** 全类型总览（10 列、连续编号、一页滚动）-> 用户一次挑完。
- 判据分层当标签：风格(ink/色数/细度) + 节拍(面积摆幅 ratio+峰值) + 形状(参数轮廓 IoU) + 深底；
  语义最贴用户原话的置顶；首帧空的件改测全帧并集。
- §2 两处旧句就地改写（"一次只做一种"/"一次 6~9 个"），不留修订注；NO_FLOW 素材指向行同步。
- 动机：watch2 心跳件按旧流程返工三轮——单风格判据把"心形+ECG"对口件挡在候选外。

## v0.9.37 — 工作流索引化：NO_FLOW §2.0b 精灵动图交付前自检索引表

- 用户要求"记录到工作流中，工作流使用索引方式"：NO_FLOW 新增 §2.0b——工作流只持 5 行索引表
  （自检项 / 门禁入口 / 规则索引），规则细节留在 `ANIMATION_ASSETS.md` §6、门禁实现留在工程脚本，不复述。
- 表含：底图 skip 精灵（幽灵像素反向测试）、坐标单一真值漂移告警、表圈安全半径、文字零重叠、
  首/中/末三帧 ≥3× 目检；纪律＝用户报"重叠/不一致/骑圈"先跑表出证据再动手。
- FLOW 其余纪律加第 5 条指向该表（原 5 顺延为 6）；kit README 与仓库根 README 索引行同步。
- 动机：watch2 精灵动图修了三轮（骑表圈 → 坐标漂移 → 底图幽灵）才过，三条全部命中表内项。

## v0.9.36 — ANIMATION_ASSETS §6：精灵动图合成三坑 + 两道量化门禁

- `ANIMATION_ASSETS.md` 新增 §6：① 逐帧动图的整页底图必须 skip 精灵控件，否则第 0 帧小人留在背景、
  第 1 帧起两人重叠；② 控件坐标与 SPRITES anchor 单一真值，漂移即"预览图与动图不一致"；
  ③ 门禁量化并反向测试：幽灵像素（skip→0 / 不 skip→460）、表圈安全半径（bbox 四角 ≤ 屏心−8）。
- `EEZ_FIRST_WORKFLOW_NO_FLOW.md` 素材指向行补 §6 指针；intake P-0222、PROMPT_LOG PR-0406 留痕。

## v0.9.35 — 新增 ANIMATION_ASSETS：动效素材从哪找、怎么筛

- 新文件 `ANIMATION_ASSETS.md`：把"给界面找动效"写成可复用的流程。三条能直接抓的渠道
  （lottiefiles 免费区 / OpenGameArt / Wikimedia Commons API）、三家抓不到但能让用户自己下的
  （icons8、iconscout 走 Cloudflare 盾，lordicon 要登录）、两家不能进产品的（Giphy/Tenor、国内素材站）。
- 含可脚本化的 8 步：抓预览 GIF → 抠底（四角同色才键） → 量化风格（ink / 颜色数 / 细度）
  → 染色成单色 → 出统一 200px 格的 SVG 全览（浏览器打开即循环） → 用户按编号点选
  → 回详情页核授权 → 写 PORTLOG（URL/授权/作者/日期/SHA256）。
- 钉死实测判据：线条风 ink<0.10、色≤8、细度>0.30（样本 001.gif：ink 0.04 / 6 色，选中）；
  单色实心细度<0.25；扁平插画 20~70 色。三个坑：站内标题与卡片错位、假透明棋盘格、GIF 丢重复帧不补时长（见 P-0216）。
- LottieFiles 的 slug 只认单词：`running/jogging/workout/fitness/sprint` 有卡片，多词 slug 返回通用页 0 卡片。
- 授权口径按 CC0 < CC-BY < CC-BY-SA 分档，LottieFiles 免费区仍需逐个确认 Free/Premium；医疗/对外产品一律留凭证。
- `README.md` 目录树与仓库根 `README.md` 索引同步；`EEZ_FIRST_WORKFLOW_NO_FLOW.md` §2.0 挂指向。

## v0.9.34 — 交付形态定死：设计图/效果图一律交 SVG 总蓝图（含动效 GIF）

- `EEZ_FIRST_WORKFLOW_NO_FLOW.md` 新增 **§2.0**（并把七步表 ① 行判据指过去）：给用户看的
  是**一张 `designer/_overview.svg` 总蓝图**（页面网格 + 页名 + 跳转清单），不是散页 PNG；
  生成脚本挂在设计图渲染末尾自动刷新，不等用户来要。
- 同节钉死动效口径：**动效格内嵌 `anim/<页>.gif`，浏览器打开总蓝图即循环播放**；截图/转 PNG
  会退回首帧 ⇒ 动效数值真值仍是设计源 `ANIM` + 分镜 PNG。明确**禁止**把界面重画成矢量 SVG 跑
  SMIL（设计图会有两套出处，违反"界面只在设计源里定义一次"）。
- 划清边界：§2.2/§2.3 的核对物（B1/B2 截图、逐屏全分辨率长图）仍是位图，属判读件不受本条约束。
- `README.md` 的七步主链索引同步标注 §2.0。
- 出处：watch2（25 页 / 13 页带动效）与红蓝光治疗仪（12 页）两工程实测；踩过的两个形制坑——
  格宽有限，动效名要按字数截断、period/easing 单独一行（否则文字溢出压隔壁格）；
  跳转曲线叠在缩略图上会糊成一片，改列在底部清单。

## v0.9.33 — 新增 B22：仿真器按键无响应（远程键盘/焦点/事件形态）

- `cases/B22_仿真器按键无响应（远程键盘·焦点·事件形态）.md`：把"回归绿但真人按 A 没反应"
  定位成**输入链路三层**（OS 送达要焦点 → SDL 翻译要认全三种形态 → 程序派发要监听+轮询双保险）；
  附"单键全局导航"落地口径（删所有返回箭头、按屏层级返回、按键只发布事件）与
  可复现验证（`WM_KEYDOWN` 硬件扫描码 0x1E / 回归自灌 `TEXTINPUT` 分支）、
  以及"旧进程占用 exe 导致改动看不到"的环境纪律。
- `cases/README` 索引补 B22，并标注 B20/B22 是仿真器调试的两条腿（滑动 vs 按键）。

## v0.9.32 — 新增 B21：字体按字号裁字形（字体默认按省内存实现）

- `cases/B21_字体按字号裁字形（每档只烘本档用字）.md`：定死"字体总是按省内存方案实现"——
  生成器按**字号**收集字形（不再把全工程码位并集写给每档）、native 运行文案用
  `runtime_text` 按档声明、字体缺码位的符号一律换 ASCII；附烘焙后"字形存在性"校验脚本
  （每档 sparse `range_start` 不同，不能写死）与逐档体积对比（10.8 MB → 1.7 MB，-84%）。
- `cases/README` 索引补 B21，并标注 B17/B21 是字体预算的两面（预防 vs 正面做法）。

## v0.9.31 — 新增 B20：仿真器滑动调试与设计对照

- `cases/B20_仿真器滑动调试与设计对照（逐拍注入＋四方对账）.md`：
  把"在 PC 仿真器里调滑动交互"与"证明设计图/工程/运行图一致"写成可复现工装——
  逐拍注入的测试 indev（每拍必须有位移、可停住截中间帧）、物理量断言（整页对齐/指示点/
  拉窗位移）、四层判据（声明层差异 0 / 画布并排 / 交互回归 / 观感中间帧）、
  以及单一设计源派生四方产物 + `audit_declared` / `eez_b1_shots` 的硬判据操作要点。
- `cases/README` 索引补 B20，并标注 B20 是 B19 的工装手册（B19 定结构，B20 定调法与判据）。

## v0.9.30 — 新增 B19：表盘自环 Tabview

- `cases/B19_表盘自环Tabview（单滚动带循环＋磁吸自愈＋边缘过界手势）.md`：
  把"表盘本身就是第 0 个 tab"的单滚动带形态、磁吸自愈、边缘过界开窗/循环切页、
  指示点同步与点击/滑动分离写成可复用方案（含参数表与跨栈对照）。
- `cases/README` 索引补 B19，并标注 B13/B15/B19 是同一题的三代答案。

## v0.9.29 — 收尾要删过程文件

- 两份流程补同一条纪律（NO_FLOW §2.4 / FLOW §2 收尾纪律）：每步/每条功能收尾时删除过程文件
  （探针与诊断脚本、临时构建目录、一次性补丁、日志、对照中间件）；暂存只放工程 `tmp/` 并收尾清空。
- 起因：工程根残留了一个 `build_alt` 临时构建目录（AI 为绕开被占用的 exe 临时建的），
  既占位又容易被误提交；用户要求"以后在 UI 设计流程里注意删掉过程文件"。

## v0.9.28 — 官方手册使用边界钉死

- `reference/README` 新增两条全局护栏：LVGL 8 手册术语遇 v9.4 时以头文件/生成代码为准；
  WIP 的 custom-code 说明不构成 EEZ-first UI 出 C 授权，必须完成四面对查并获用户同意。

## v0.9.27 — LVGL 9 Image 名称补正

- `reference/05` 的 W30 描述从旧别名 `lv_img` 改为 LVGL 9 正式对象名 `lv_image`；已用
  当前生成 `screens.c` 与 v9.4 `lv_image.h` 交叉核验。

## v0.9.26 — 官方手册版本漂移勘误：LVGL 8 → 9.4 Image API

- `reference/05` / `reference/07` 不再把兼容层 `lv_img_*` 作为主 API；LVGL 9.4 正式名称为
  `lv_image_*`（create/src/pivot/scale/rotation）。
- `reference/02` 标出手册 `LV_IMG_CF_*` 色彩格式表属于 LVGL 8；本库 LVGL 9.4 需使用
  `LV_COLOR_FORMAT_*` 与实际生成位图 `.c` 核验。

## v0.9.25 — 官方手册逐页对照：Widget 目录勘误

- 对照官方 PDF W30–W43：修正 W30 Image 被错标为 W31、W32 Input 的序号错位、W42 List
  被错标为 W43；补回缺失的 W31 Imgbutton（仅 Dashboard / EEZ-GUI）完整属性表。

## v0.9.24 — UI 经验库现行配方审计（第六轮）

- 补足滚动 Container 的适用边界：它适用于固定/有上限行数；LVGL Flow 没有按数组长度创建
  控件的 repeater。动态长度列表在 C 侧例外前必须完成 EEZ-first 四面对查并获得用户同意
  （P-0165）；保留 P-0165 的新增取证内容不改。

## v0.9.23 — UI 经验库现行配方审计（第五轮）

- 勘误 LVGL Checkbox/Switch 的状态说明：`Checked` 是单向表达式状态，不是 assignable
  双向绑定；需要事件写业务变量、再由表达式回显（P-0162）。

## v0.9.22 — UI 经验库现行配方审计（第四轮）

- 删除“EEZ Run 预览永远不产生 GESTURE”的现行绝对断言。P-0149/B13 后续实证表明，预览
  可因 WASM + DOM 事件合并而触发；正确规则是预览结果不能代替 PC_SIM/真机验收。P-0141
  保留原始取证，并追加版本边界更正。

## v0.9.21 — UI 经验库现行配方审计（第三轮）

- 删除 `reference/07` 中“CLI 会把 PNG 直接转换为完整 LVGL 像素 C 数组”的错误说明：CLI
  仅产名表/声明，像素 `.c` 需 GUI Build 或在 CLI 后由工程生成器补齐（P-0151）。

## v0.9.20 — UI 经验库现行配方审计（第二轮）

- 勘误 AnimationImage 的 `Duration`：它是整轮动画时长，不是单帧时长；帧无独立 duration
  （P-0151）。
- 明确 W85 ToggleButton 仅属 EEZ-GUI、无 LVGL codegen；LVGL 使用 CHECKABLE Button。
- 删除 W42 List(LVGL) 的 native 补 UI 建议及 JSON 速查中的同类绕行；List 为 WIP，应用列表
  统一改用滚动 Container + 显式真实行控件（P-0152，EEZ-first）。
- 为 `Flow.makeArrayValue` 补充运行时定长限制，避免将 ArrayValue 当成 `std::vector`
  （P-0165）。

## v0.9.19 — UI 经验库现行配方审计

- 删除 `skills.md` 手势配方中可被直接照抄的错误 `customInput.dataType` 写法，统一为
  已验证的 `type:"any"`；历史 `intake/P-0146` 仍保留原始误判与最小复现证据。
- 勘误 LVGL Label：Studio 1.22 的 widget 定义级 `Text type=Expression` 会被 codegen
  编为空字符串，`reference/05`、`reference/07` 均改为 flow `labelSetText` 路线，并标明
  版本边界，避免误伤其他 Studio/目标组合。
- 清理 eez-test 行为契约中的过时输入栏/发送按钮描述（P-0107 已删除该功能）与“未实现可留死交互”
  许可，使其与导航闭环、语义控件铁律一致。
- 修正 README 案例索引的陈旧范围（B1~B10 → B1~B14）。

## v0.9.18 — Flow 事实核查（P-0165）+ 脚手架文档勘误

- ★ 新增 P-0165：三条实测事实——Flow **已启用**（`ui.c` 调 `eez_flow_init`，`eez-flow.cpp`
  9,923 行生成在 `src/ui`，二进制 501 个 `eez::flow` 符号）；`ArrayValue` 是**定长柔性数组**
  （`values[1]` + `makeArrayRef`，非 `std::vector`，无 push/clear）；`native_var_t` 只支持
  5 种标量，**结构体数组必须走 Flow 全局变量**。附 3 条机器检查。
- ★ reference/11 §6 勘误：删除"EEZ 画布不渲染 `text_align`"（画布是真实 LVGL wasm，
  当时的异常是字体缺字形），替换为实测成立的"手工坐标居中"反例。
- 方法论：判断运行时是否启用看**生成代码 + 二进制符号**；判断容器语义看**结构体定义**；
  判断跨层类型能力看**枚举定义**。

## v0.9.17 — 每页动画"至少核对一个周期"属性值域采样法（watch §51b，PR-0250）

- ★ skills §11.47：动画周期核对正道=直读 flow 写入的样式属性取值域（30ms×52 拍 ≥ 最长
  周期，spin=3510/swing/pulse/bob 各有换算式），不靠加密像素截图（仍可能混叠+阈值盲区）；
  静止页反向断言 range==0；时钟类用 set_var 步进折算；期望值必须从通道 amp 表达式推导
  （§51b 首跑 4 FAIL 全是夹具判据错，修夹具不改工程）。

## v0.9.16 — 视频取证管线（转场 30fps 边界 + 双侧动画判定，watch §51，PR-0249）

- ★ skills §11.46：手持视频复原的三面取证法——切段用 HSV 卡方距离（非逐帧分类）、
  转场判定必须 30fps 边界胶片（10fps 会跳过 50-100ms 交叉淡化误判直切）、
  双侧同度量动画判定（ECC 对齐 + 皮肤色掩膜剔手指 + 中值参考帧差 + 团块坐标）；
  采样混叠坑（帧间隔 < 动画周期半）、blob 阈值过粗误报静止、属性采样兜底裁决；
  changeScreen fadeMode 枚举查 asar registerAction（默认 FADE_IN/speed200）。

## v0.9.15 — 参考视频复原方法论（watch §50，PR-0248）

- ★ skills §11.45：证据矩阵先行（逐帧归类三档+无证据页禁脑补+静帧资产核对身份）；
  四层一致性（语义/结构/观感/动效由硬到软）；逐页 REF|SIM 并排拼图一轮看完再改；
  "假 N 行"=行距脑补把末行挤出屏外的判据式；图标形态放大取证；PIL 弧角坑。

## v0.9.14 — LVGL 裁切语义与载体重构（watch §49，P-0147，PR-0247）

- ★ skills §11.44：LVGL 9 子件恒裁到父框，OVERFLOW_VISIBLE 只扩 ext_draw_size（源码
  lv_refr.c:140/lv_obj_pos.c:914 实证）——子件 transform_scale>1 越界=静默切平（圆变方，
  0 错 0 警）；修复正道=把放大内容提为足够大的祖先直接子件，并把原父承载的动画量并入
  自身表达式（嵌套相乘→单写求和，逐点等价）；判据用"峰值帧截图"（hbshot 夹具法）。
- ★ P-0147 登记；连带纪律：观感修正逐项对照实拍裁决，别顺手扩大改动面
  （§49 曾把 BPM 穿字误判为针太长，收短指针后回滚）。

## v0.9.13 — Checks 双判据与字段对账法（watch §48/§48b 归档，P-0146 终版，PR-0246）

- ★ skills §11.43：手写工程 JSON 字段名必须对照手册/asar classInfo 核实（customInput 类型
  字段=`type` 非 `dataType`；未知字段静默丢弃零告警）；Switch 每个 outputName 必须有连线、
  无 default 合法；**CLI 0错0警≠编辑器 Checks 干净**，交付判据=徽标零错误截图+静态门禁
  规则E 双保险；"转圈（不收敛）"与"红错（收敛后报错）"是检查器两种状态；最小复现工程
  （单变量 repro_ok/repro_bad + 像素差分判转停）为平台行为裁决的标准姿势。
- ★ P-0146 补 §48b 案并回改标题/标签/索引行：初判"EEZ bug"作废，终版=字段名笔误；
  补 type 后收敛并亮 37× `Output "NONE" is not connected`（§35 起即存在，此前无机会报），
  删悬空 NONE test 修复；方向判定手势与 Checks 干净兼得。
- ⚠ §11.41 第 2 条的 `dataType:'any'` 配方写法作废，以第 7 条/§11.43 为准（只增不改，
  作废声明写在 §11.43 开头）。
- ★ PLAYBOOK §2.9「回归定位三步法」：git 还原定坏提交（量化判据）→ diff 变化点圈因 →
  独立简约工程单变量裁决；第 4 步修复落上游+判据固化为门禁并双向回测。附本案四个翻车点
  （先读手册设计语义、对照实验在真实路径跑、用户反例=数据、假象链条留痕标注"待裁决"）。
  ——用户 2026-10-18 明令将此打法固化为默认流程。

## v0.9.12 — 新增 reference/10：硬件 ⇄ UI 分离模板（第一步是目录结构）

- ★ 用户问「硬件和 UI 怎么分离的、整理进库了吗」，并明确要求：**「这个分离中，需要第一步解释文件目录的结构」**。
  第一版从"不变式"开讲被打回（用户整份还原），重做时把 **§0 文件目录结构**放到最前，其余条款整体后移。
- `reference/10_hw_ui_separation.md`（跨项目模板，正文不含具体工程路径）：
  - **§0 文件目录结构**：0.1 四角色目录树（设计源 / 生成产物 / 业务层含 `platform/` / 应用入口）·
    0.2 每个目录怎么自证身份（判据表）· 0.3 依赖方向图（**交汇点只允许一个 = 契约头**）·
    0.4 一条信号跨目录的完整流向（把地图和机制接起来）· 0.5 陌生工程 5 分钟认路三步法。
  - §1 四条不变式 · §2 四层归属 · §3 A/B/C 三通道与选型判据 · §4 变量桥三条硬规矩 ·
    §5 ★平台分界三种机制（CMake 白名单 / GLOB 全收+正则排除 / 文件内 `#ifdef`）的选择判据 ·
    §6 线程模型配方（worker 低于 UI、快照+代数、有界锁、SPSC 每拍一条、独占屏是唯一批准的例外）·
    §7 仿真镜像纪律与"三处不许假装镜像" · §8 加信号核对清单 · §9 九条反模式 ·
    §10 机器检查清单 · §11 实例索引。
  - 教训：**讲架构先给地图，再讲规则**。读者第一问永远是"文件在哪、谁能动谁"，不是"有哪几条不变式"。
- `reference/README.md` 索引补齐：原来只列到 `07`，`08`/`09`/`10` 都没进表；顺手改掉
  "本目录的 6 个 `.md`" 这句过期描述，新增"工程实践类（非手册提炼）"表。
- ⚠ 核查出的落差（未修）：`framework.md §7.2` 声称"声明/定义对账已部分做进校验"，实测
  `design/all.py` 与 `design/_audit_*.py` 里**没有** `vars.h`/`actions.h` 声明集合 ↔ 适配层定义集合的
  diff 断言（grep 零命中）。本文 §10 那条"必须为 0"目前是**要求**，不是现状。

---

## v0.9.11 — 时钟变量桥 + 表达式格式化两面坑（watch §38，PR-0239）

- ★ skills §11.42：EEZ native 外部变量桥（native:true → vars.h get/set_var_x 声明 +
  ui.c native_vars[] 登记；表达式经 VALUE_TYPE_NATIVE_VARIABLE 惰性现读，固件写完即生效）；
  String.format (fmt,单值)+尾说明符限定、formatPrefix 空桩、padStart/'+' 拼接可用面；
  "HH:MM"=padStart+两次 format 配方。
- ★ P-0143：LVGL 目标 label textType:'expression' 被 codegen 编成空串且 0 错 0 警——
  变量文本正道是 flow `labelSetText` 动作（asar id:29）；"0 警≠产物正确"再加一条判据。
- ⚠ P-0132 陈坑复发案例：§36 图标链 object 未过 c_ident → stic_* 驼峰 7 错；
  规则落码要全表过规范化，别只对已知样本调试。

---

## v0.9.10 — UI 通用铁律：导航闭环 + 语义控件（PR-0234）

- ★ `UI_BEHAVIOR_CONTRACT.md` 追加**通用铁律节**（适用所有 UI 工程）：每屏能进能回（真返回按钮）、
  按钮/开关必须原生控件、禁止图片冒充；规则按硬度四层落位（文档→生成器 assert→静态门禁→Run 回归），
  "不得用图片掩盖控件"只有变成"构建不通过"才算钉住。
- ★ skills §11.40（沉淀方法论：能判定化的规则别留在口头）；watch 侧新增 `design/nav_audit.py`
  三查门禁（可达性/返回边/假按钮），29 屏 PASS。

---

## v0.9.9 — B12 升 v7 参数通道动画 + PLAYBOOK 传参/截图两条新坑

- ★ **B12 手册新增 §31.7 参数通道动画节**：高帧率动画的正确形态=flow 每拍直写
  角度/缩放/位移/透明度（33fps 连续量），只有"必须换画面"的步态才烘焙帧；
  相位变量（p/q/h/osc/rot/f4）单点定义、各通道只引用——改周期/幅度各只动一处。
  v6"烘焙帧+65ms 节拍"被判丢帧的教训：**流畅度上限=写入节拍，不是帧数**。
- ★ **PLAYBOOK §3.2 补两条实测坑**：① 路径含空格禁用 PowerShell Start-Process
  -ArgumentList（argv 碎裂 → "Failed to load file!" 假象，症状酷似会话损坏但清
  Storage 无效——先查 argv）；② Run 预览画布坐标会漂移，连拍/截图必须每帧前
  自量最大 canvas 的 rect，写死 clip 会截到编辑器画布产生"平移+假静止"双伪影
  （本轮曾因此误判"整列右移 63px"与"动画冻结"各一轮）。
- ★ **观感判别方法**：蓝底白环被高阈值检测漏判成"叠层不渲染"——先放大裁剪图
  目检，再让检测阈值贴背景亮度；受控二分（借已知可渲染位图）证明控件正常后
  才承认是测量问题。
- ★ **skills 新增 §11.38**（高帧率动画=参数通道：相位变量层 p/q/h/osc/rot/f4 单点定义、
  通道只是门控组合；流畅度正证=轨迹连续而非"有差分"）与 **§11.39**（CDP 驱动 Electron
  四条纪律：bash 引号、禁 F5、自量 rect、"不渲染"三道判别）。
- ★ **intake 登记 P-0138**（PowerShell 拆 argv → Failed to load file! 假象）、
  **P-0139**（canvas 漂移 → 平移+假静止双伪影）；B12 索引行与 EEZ_FIRST_WORKFLOW §3.1 同步。

---

## v0.9.8 — 案例 B12：圆柱滚轮"弧度"= translate_x 弧线（观感词三轮歧义教训）

- ★ **新增案例 `cases/B12`**（七段式）：B11 轮询链只做了缩放（cos 分量），"弧度"实为
  横移（sin 分量）——`translate_x=((352−k)²·181)>>18` 每行盘+文字，88 动作/帧。
  四条误判在案：①拿实拍照片硬拟合设计参数（手指遮挡+相机透视，不可裁决）；②把"弧度"
  做成整行旋转（5°→8°→12° 全错方向）；③ **LVGL 9 `transform_pivot` 样式默认=(0,0)
  不是中心**（12° 把表推离屏心 43px；8° 时已被容差掩盖——角度类改动后必须复测既有不变量）；
  ④ 检测器给圆盘加了 (cosθ+sinθ) bbox 修正——**圆旋转 bbox 不变**，矩形才变。
- **选型三约束**（写进案例"修法"）：横移效果反馈安全（A1 只读 Y）；translate 写子控件
  不写行容器（命中/滚动范围不变）；文字控件须显式 `ident` 才能被动作寻址。
- **EEZ flow 组件描述名 = `description` 字段**（GENERAL → Description，编辑器里渲染成
  组件块下方黄色说明条）；`name` 键被 loader 静默保留但不显示。
- **需求沟通纪律**：观感词（弧度/倾斜/反了/弹性）两轮问答对不齐就**主动要标注图**——
  用户一条红线 = 三轮测量+两次返工。
- 工程侧配套：L4 检测器升级旋转/弧线感知（`measure(tilt_deg=)`、横心断言=弧线模型、
  盘 blob 窗口放宽防裁瓣）。

---

## v0.9.7 — 案例 B11 + 「公用函数」查档入库 + 单读中继配方

- ★ **新增案例 `cases/B11`**（七段式）：滚动动效被误判"EEZ 表达不了"→ 四面对查推翻 →
  native 退役 → 动作面板"公式墙"以「单读+中继」消除。三次误判（只查事件面/CHECKED 双写必须/
  公式该做成公用函数）全部记录在案；含跨栈对照（≈ rAF 轮询 + getBoundingClientRect + CSS 变量）。
- **「公用函数」查档入库（P-0136）**：`reference/07 §4` 补——User Action 的 `implementationType`
  含 `"flow"`（流实现的公用函数，输入/输出=userProperties+Input/Output 动作）；
  调用=**Call Action 组件**（属性 `{action, userPropertyValues:{values:{<propId>:<表达式>}}}`
  ——输入走 expression、输出走 assignable，asar 实证）；⚠ **flow 表达式不能内联调用用户函数**。
  单点复用场景保持内联（升级触发条件=第二处复用；采用前须最小原型验 Call Action 出参）。
- **skills §11.37 三·追加「单读+短中继」配方（P-0137）**：同容器刚性子项 ⇒ 读一个基准项推全表；
  SetVariable 组件（`entries:[{variable,value}]`，均表达式串）做中继——编辑器每行 ≤40 字符、
  帧执行与逐行版持平。案例与配方互链。

## v0.9.6 — A8 支持「只统计事件源连线」+ ★ 常驻轮询链入库（当前）

- 背景（P-0131，watch 工程纯 EEZ flow 滚轮）：工程连线里出现了**流程内部连线**
  （Start→Loop→Delay→动作组、Loop@next 回连，output 为 `@seqout`/`done` 等），
  它们不产生 screens.c 事件回调 → A8 代码侧只数得到 CLICKED 回调，工程侧却数全部连线，
  三层计数假红（19 vs 19 vs 15）。
- 新增 `checks.links_event_outputs`（可选，默认不过滤、不影响存量工程）：列出"事件源
  output"白名单（watch 工程配 `["CLICKED"]`），工程侧只统计这些连线，与代码侧
  事件回调语义对齐。
- 排查记录：流程内部连线的计数真值由工程侧 **G2（design/check_nav.py）** 的
  「连线数（其中导航 N）」一行给出；G2 同步改为只对 CLICKED 线计入导航基线，
  非事件线仍做 source/target 存在性校验。
- ★ **新增 skills §11.37：滚动联动不必"事件驱动"——常驻轮询链**（纯 EEZ flow 滚轮复盘，
  P-0131/0132/0133）：四面对查纪律（事件面/动作面/调度语义/运行时源码）；
  骨架 `Start → Loop(To=大数) → Delay(30ms) → LVGLAction(读坐标→写样式) → 回连 next`；
  三硬约束（整数表达式/规范化标识符/双态写入）。
- ★ §11.37 硬约束 3 细化（同日追加）：**双态双写仅当控件存在静态 CHECKED 样式**；
  更优路径 = 生成端删静态样式、源头消冲突 → flow 单写 DEFAULT（帧动作 −40%、表达式副本 −50%，
  watch 实测零视觉差异，报告 §19）。
- ★ **更正 v0.8.6 与 P-0043 的「`%` 也永远返回 double」**（P-0131 受控实验+源码双证）：
  本 runtime `op_mod` int×int 返回 int32；`/` 才是恒产 double 的头号雷。
  reference/07 §10 陷阱 1 已改写；P-0043 已追加更正块。
- reference/07 §7/§8.1a/§8.4 补充：动作 `object` 参数须写**规范化源码标识符**
  （`row_sport_mode`，P-0132）；objGetDisplayY/objStyleSetProperty 序列化与整数约束；
  Loop `"version":1` 缺失会被 beforeLoadHook 改写 `to`（P-0131 期间实证）。
- PLAYBOOK §3.2 补启动小注：CDP 启动 EEZ Studio 时**工程路径必须放 argv 最后**
  （主进程取 argv[last] 为待打开工程）、旧实例先 taskkill（P-0133）。

## v0.9.5 — A8 适配「生成器直出」工程：设计侧计数同源开关（当前）

- 背景（P-0127，watch 工程就绪核查）：A8 把设计侧跳转数硬编码为「节点级 goto 字段遍历」，
  而生成器直出 EEZ JSON 的工程没有中间 DSL（design_src == project_file），链路表达为
  **页级 connectionLines** → 设计侧恒为 0，门禁假红。
- 新增 `checks.a8_design_equals_project`（默认 false，不影响存量工程）：置 true 时
  A8 设计侧计数与工程侧同源（显式声明「本工程 design≡project」）。
- 配套在工程侧建立 **G2 跳转体检**（`design/check_nav.py`：链路计数/死链/死胡同清单，
  基线数写在脚本内，补导航时同步改）——直出型工程的跳转真值全部取 page 级连线。
- ⚙ 运维注：Windows GBK 控制台跑本工具套件会因 ✓/✗ 字符 UnicodeEncodeError 崩溃，
  跑前 `export PYTHONIOENCODING=utf-8`（P-0128）。

## v0.9.4 — 新增 reference/07：.eez-project 工程 JSON 序列化语法速查（当前）

- 背景（PR-0069，用户问「有没有总结 eez 工程 json 语法，参考手册总结到经验文档」）：
  官方手册只讲 UI 概念与操作，**从不写 .eez-project 文件的 JSON 落盘格式**——
  这层语法全靠逆向 asar + 真实工程试错积累，散落在 json2eez.py 注释、skills.md
  各节与日志里，AI 每次改工程 JSON 都要重新踩一遍。
- 新增 `reference/07_project_json_schema.md`（~330 行）：文件顶层结构、
  settings.general/build、globalVariables、User Actions、页面结构
  （components/connectionLines/localVariables/componentGroups）、控件骨架与
  hidden 三形态、eventHandlers 三形态、**flow 组件逐个序列化**
  （LVGL/SET_PROPERTY 高层形式+降级映射/SetVariable/Compare/Loop/Delay/IsTrue/
  Comment/Start）、连线端口语义表（@seqin/@seqout/True/False/start/next/done）、
  表达式引擎能力与陷阱（`/`、`%` 返回 double）、动画能力矩阵、8 条静默失败清单。
  每条标注验证等级（实测 ✅ / 手册 📖 / asar 🔍）。
- 同日实证的 flow 动画三坑随文档入库：Loop 输入 start/next（非 @seqin）、
  帧表达式纯整数（`/`、`%` 产 double → 位型垃圾坐标）、停止检查须帧级。
- 「Run 模式预览执行 flow」结论修正（PR-0068 用户实证 eez_lvgl_demo）：
  预览执行 flow 并实时刷新画布，但不模拟真实 LVGL 交互事件/native 变量。

- 追加（PR-0083）：**工具字段不限工具**——INTAKE.md/README/TEMPLATE 的示例清单
  补全（WorkBuddy/Trae/Claude Code/Codex/Cursor/ChatGPT/人），显式声明本库
  不绑定任何工具、允许不同工具接力记录；历史条目工具名保持事实不改。

## v0.9.3 — 字体 Opts 对齐 + flow 卫生（孤岛/组/布局）+ 变量审计（当前）

- **P-0035 / PR-0061**：字体 Opts 行路径对齐 GUI——EEZ 用工程 filePath 原文拼
  opts_string（asar font.js 取证），工程改存相对路径；内核读文件基准改工程目录；
  §11.12 必踩点扩到 **8 条**。GUI 黄金样本终验 **11/11 逐字节一致**。
- **P-0036 / PR-0062**：孤岛动作组件清理（空 switchTab 链不建组件）+ 17 处
  `animated:true` 违反 LV_ANIM_OFF 铁律修正；§11.19/§11.20 新增。
- **P-0034 / PR-0060**：滑动点亮组完备性（pop 行归通用页组）；**断言期望值来自
  设计推导，不能把现状抄进 expect**。
- **P-0032 / PR-0059**：设置页内容起点 `RAIL_W+206` 铁律 + **对照门禁均值盲区**
  （出图必分区放大目检）。
- **P-0037/38/39 / PR-0063~0065**：动作画布按导航分区（名字制 `_bucket`，空分区
  不占位）+ ComponentGroup 自动归组（4 组 37/37）+ Comment 标题条 + 行距随
  actions 数动态（渲染高度=声明值最小值）；**布局键用语义名不用数字序号**。
- **P-0040 / PR-0066**：变量死活审计三态合并（结构化绑定/表达式裸引用/native
  读写），删除唯一死变量 battery_pct（33→32）。
- **PR-0067**：知识库损坏检查与修复——系统自动重启致 3 文件尾部 NUL +
  P-0038 丢失，已全部修复重建；后续遇系统级事件必须 NUL 扫描 + 交叉对账。

## v0.9.2 — 设置页布局铁律 + tab 结构不变量（当前）

- 背景（PR-0059 / intake P-0032、P-0033）：用户指出「界面发生重叠，你自己截图
  没看出来有问题吗」，随后又贴出 EEZ GUI 四条
  `Invalid position of Tab widget inside Widgets Structure` 报错。
  两问分别撕开两块盲区：对照门禁的均值盲区、headless 构建的结构校验盲区。
- 新增 `skills.md` **§11.19 设置页布局铁律**：外置左栏 `rail_cats` 固定盖 76..282，
  设置三子页 pane 起点必须 `RAIL_W+206`（撤子页 ≠ 内容可以占满内容区）；
  `check_bounds` 只查「子超出父」不查「兄弟重叠」；**对照门禁只看 11 屏平均，
  单屏结构错位（07 才 12.90%）静默通过 → 出图必须分区放大目检，数字绿 ≠ 画面对**。
- 新增 `skills.md` **§11.20 DSL 结构不变量**：tab 只能是 tabview 的直接子对象；
  **headless build 过 ≠ 结构合法**（GUI 校验更严）。Screen 直下挂 tab 的四张
  「钉态」隐藏页已删（零引用死代码，四态图走 §11.18 配方 + `--states`）；
  再要干净背景截图页须包进隐藏 tabview 或改 container。遗留：把
  「tab 必须在 tabview 内」做进 json2eez 常驻断言。
- 新增 intake **P-0032 / P-0033** + index 两行 + **PR-0059**（用户原话逐字）。
- 追加（PR-0060 / intake **P-0034**）：用户报「wifi 页 tab 有时候没有高亮」——
  §11.19 补「**点亮组完备性**」：每个 tab 的点亮组都不能留空，无子页的入口行
  （pop）显式归入其语义归属页；pop 行点击不动高亮（浮层入口≠页面入口）；
  **断言期望值来自设计推导，不能把现状抄进 expect**（`expect 0/000` 曾把
  bug 固化成规格）。

## v0.9.1 — 声明式显隐 hiddenExpr：状态机 UI 的正解

- 背景（PR-0058 / intake P-0031）：用户要求 Wi-Fi 扫描/连接 UI 按行业标准重做，
  并明确「先按照行业标准做法来做，你先执行」——不要停在方案阶段。
  这是 PR-0057 选型铁律落地后的第一个完整页级实战。
- 新增 `skills.md` **§11.18 声明式显隐 hiddenExpr**，沉淀机制 + 四个坑 + 状态机页配方：
  - **机制（取证充分，非推测）**：DSL 节点 `hiddenExpr="<表达式>"` → `json2eez.py` 写
    `hiddenFlagType:"expression"` + `hiddenFlag:"<表达式>"` → EEZ build 在
    `tick_screen_<page>()` 生成 `evalBooleanProperty(flowState, N, 3, "Failed to evaluate
    Hidden flag")` 并与 `lv_obj_has_flag(obj, LV_OBJ_FLAG_HIDDEN)` 比对，不同就
    add/remove。**每帧求值、自动翻转 HIDDEN** —— hardware 侧改输入变量 UI 自动切换，
    UI 逻辑零用户代码。表达式引擎支持 `== != < > <= >= && ||`（`eez-flow.cpp` 表驱动
    `do_OPERATION_TYPE_*`）；表达式引用的变量必须在 `ui.json` 的 `variables[]` 声明。
  - **状态机页配方**：一个 `wifi_state` 整数 + 各态专属容器，容器 hiddenExpr 互斥
    （如 `net_cur_on` → `wifi_state != 3`、`net_cur_off` → `wifi_state == 3`）；
    列表用**固定槽位**预置（EEZ 静态 UI 无法动态生成不定长列表），空槽用
    `wifi_slot{i}_ssid == ''` 自隐藏。
  - **归属分层**（与 §11.14 一致）：状态切换/显隐/样式 = EEZ 声明式；真扫描/连接/断开
    = A 通道 User Action；结果回显 = C 通道输入变量。
- **四个坑（对照表形式写进 §11.18）**：① 表达式**禁嵌套括号**（嵌套括号落盘后判定失真，
  表现为互斥控件叠字）→ 展开成独立条件用 `&&` 串；② **pill 宽度必须 x=0 锚点**：
  先取宽再 shift，邻居按 `pill_x` 定位，不能用 `fw` 反推（会算进 pill 内部）；
  ③ 行容器与行内按钮禁绑同一 action（冒泡双命令）→ 行纯展示 + 独立透明热区按钮；
  ④ 右对齐别用 `label_right`（飘 1~2px），用 `label(rx - tw(text, px), ...)`。
- **仿真侧配套**：中间态截图钩子 `EEZ_SIM_STATE=<n>[,slot]`（Windows 需先
  `_putenv("")` 刷新 CRT 环境，`getenv` 才读得到），配 `s_pinned` 阻止时间推进覆盖
  —— 状态机的中间态（扫描中/连接中）靠时间推进才能截到，必须有钉态手段。
- 验收：`design/all.py --shots` 全绿 + 四态拼版图逐态人工核对（叠字类问题
  像素 diff 阈值抓不到，必须看图）。

## v0.9.0 — 选型铁律：UI 控制一律 EEZ 优先，user action 只留外部硬件

- 背景（PR-0057 / intake P-0030）：用户在 P-0029 native 方案验收后两次加码，最终定稿
  「后期要求优先输出用EEZ里面控制UI，包括各个控件的联动，仅仅控制外部硬件的允许使用
  用户代码，如果实在没有办法的话，需要通知我」。
- **§11.15 的 native `sync_rail_*` 方案被推翻退役**（按约定保留旧条目，写明改动）：
  高亮同步属纯 UI 控件联动，重做为**纯 EEZ flow 链** —— VALUE_CHANGED →
  objClearState×N + tabviewGetActiveTab(result=页面局部变量) → @seqout →
  CompareActionComponent(var,i,"=").True → objAddState(第 i 组)。
  新增 `skills.md` **§11.17** 完整配方，含 **asar 序列化四要点**：
  ① assignable 参数无 Type 后缀（tabviewGetActiveTab 的 result 是裸表达式串）；
  ② CompareActionComponent：A/B/C 裸串、operator "="、输出口 True/False；
  ③ @seqout 在组件全部 actions 执行完才传播（eez-flow.cpp:4188–4196）；
  ④ 页面局部变量 page.localVariables。
- DSL：`onTabChange` 从字符串动作名升级为结构化 `{tv_ref, var, clear, add}`；
  native 退役删干净（actions[] 声明 + native_actions.cpp 函数 + screens.c 再生成）。
- 方法论：**先取证再选型** —— 「EEZ 能不能表达」不靠直觉，解包 asar 看动作类定义 +
  Studio 手搭最小链对照 JSON，取证充分则零试错；拿不准先通知用户，不默默走 native。
- 铁律落盘：UI_BEHAVIOR_CONTRACT.md 新增选型铁律节（§0/§7 的 sync_rail 引用同步更新）；
  项目/用户级 MEMORY.md 同步。
- 验收基线不变：6 条 [swipe] 运行时断言原样通过 + 11 屏对照 8.59% < 25% ——
  重构不改行为时断言一个字不动，即等价性证明。

## v0.8 — 修正坐标系结论：分层 + 相对换算（拍平降级为排障模式）

**背景**：v0.7 的 `cases/B5` 把「拍平」作为子控件二次偏移的修法。实战反馈指出
这样会**丢掉父子关系与相对布局**（组件树变成几百个平级节点，编辑器里无法成组移动）。
于是把坐标规则查到源码级并改回分层，`B5` 补写「后续实战修正」而不是删旧结论。

变更：

- `cases/B5` 追加「补充」：给出 LVGL 9.4 `lv_obj_move_to` 的精确式子
  `子绝对 = 父->coords.x1 + 子声明坐标 − 父->scroll_x`，纠正"要减父 padding/border"
  的猜测（实测**不用减**），并补上"父滚动量会叠加""子控件越界会被裁掉"两条；
  附两种修法的对比表与实测数据（拍平 8.30% → 分层 8.14%）。
- `PLAYBOOK §4.10` 与 `skills.md §3.3` 同步改写：**默认分层 + 相对换算**，
  拍平只作排障/对比模式。
- 新增一条工程侧必做校验（写在生成脚本里，工具箱未收录为断言）：
  **子控件必须在父的矩形内**（相对坐标为负 / 右·下边缘越界即报错）。
  实测这条校验一次抓出 4 类真实问题：电极在电池主体之外、气泡头像超出父卡、
  滑块圆点比轨道高被削平、分区指示条贴在栏外。


---

## v0.8.8 — 滑动高亮跟随 + 程序切页 animated:false 铁律 + 下拉浮层模式

- 背景（PR-0056 / intake P-0029）：用户反馈 ①「上下滑动时左侧 tab 高亮不跟随
  （设置页同理）」②「点无线网络要弹下拉窗，不要整屏下滑推挤其他选项」③要求自查。
- 新增 `skills.md` **§11.15**，沉淀三块：
  ① **滑动高亮跟随**：tabview VALUE_CHANGED（手势滑动 SCROLL_END 落定发出，
     lv_tabview.c:330/376）→ native User Action `sync_rail_*` 按
     `lv_tabview_get_tab_active` 重排 CHECKED——补上 §11.9 只覆盖点击动作链的缺口；
  ② **★ 程序切页 animated:false 铁律（P-0029 根因）**：`tabviewSetActiveTab(animated:true)`
     的 180ms 滚动动画未完成时再来事件，tabview 的 SCROLL_END 处理器会按
     **旧动画目标位**算出旧 tab，`set_active(旧值)` 拉回页面并发
     **VALUE_CHANGED(旧值)** → 高亮/页面 off-by-one（运行时冒烟实测抓到，
     G5 截图对照掩盖不了也发现不了）。程序切换一律即时，滑动动画留给真实手势；
     「加长等待」是掩盖不是修复；
  ③ **下拉浮层模式**：onShow/onHide → 内置 objClearFlag/objAddFlag(HIDDEN)，
     pop_bg 遮罩 + pop 卡片挂内容区末尾绝对定位（零推挤），隐藏入口多点（关闭/
     遮罩/选中行）；flag 动作同 SetVariable 走 eez-flow.cpp 运行时解释，
     **screens.c grep 不到 HIDDEN 是正常的**，真值在工程 JSON + 运行时断言。
- 验收基线升级：sim.py `click_smoke_test` 从「io 回显 + tab 序号」扩到
  **rail 四项 CHECKED 恰一为真** + **浮层 has_flag(HIDDEN) 翻转**运行时断言
  （高亮竞态、显隐链路只有运行时断言能抓）。
- 方法论：编译/链接通过 ≠ 行为正确；临时 printf + 全量状态 dump 一次定位竞态，
  修上游（json2eez）而非等待/重试，修完移除临时代码。

## v0.8.7 — 回调/变量框架：四层隔离 + 命令/变量双通道 + 代码归属标记

- 背景（PR-0055）：用户要「UI 按钮回调和 native 变量的软件设计框架图」，
  并明确要求**框架里标明哪些是用户添加的代码** + 问「这个框架好不好」。
  本轮把可复用的骨架与方法论进库（工程专属信号清单留在工程侧
  `design/architecture/framework.md` + `callback_var_framework.svg`）。
- 新增 `skills.md` **§11.14** 回调/变量框架，沉淀六节：
  ① 核心原则（生成代码与用户代码只通过唯一契约 `app_model.h` 对话）；
  ② **四层结构 + 代码归属标记约定**（紫色=EEZ 生成不可手改 / 绿色=用户添加；
     附归属速查表：EEZ 只生成 `src/ui/*`，`src/native/*` 全是用户代码）；
  ③ 两条命令通道 + 一条输入通道（A/B/C）+ **命令 vs 变量边界纪律**
     （命令恒走 A、真状态走 B/C，别把「点击下发命令」做成回声变量；引用 §11.11 第 6 条
     + PR-0049 实战把 7 个命令型变量迁回 A 通道）；
  ④ 仿真/硬件靠编译期 `EEZ_SIM` 切换、运行时零分支；
  ⑤ 扩展信号要同步 4 处的防炸清单 + 建议固化的三条断言（vars.h 残留=0 /
     actions 声明与实现 diff 一致 / screens.c 回调体非空）；
  ⑥ 框架诚实评价（优点：隔离干净·仿真硬件可互换·通道语义清晰；缺点：输出变量 getter
     回声脆弱·扩展改 4 处·无运行时类型安全·双套管接命名易漂移·生成声明+手写定义有裂缝）。
- 工程侧交付（不进库，记此备查）：`design/architecture/framework.md`（四层 + A/B/C
  数据流 + 每文件函数清单 + 仿真硬件矩阵 + 字库进工程 + 第 7 节评价）与
  `callback_var_framework.svg`（四条带用颜色区分 EEZ 生成 vs 用户添加，并加图例）。
- 验收：框架图与文档完整覆盖「用户 action 与 native 变量区别 / 仿真硬件如何区分 /
  每文件实现什么函数 / 哪些代码是用户添加」四项诉求；评价章节列出 5 条可复用改进项。

---

## v0.8.6 — 官方字体烘焙内核 `eez_font_bake.py` 入库 + 内核/胶水分层（当前）

- 背景（PR-0054）：用户问「刚生成的这些脚本是不是也要保留到本地知识经验库」。
  按工具箱自身规矩（"工程专属的不属于工具箱"）不能整份拷进来，但
  **「解包 + 调用 EEZ 官方引擎烘焙」这件事本身是工程无关的** —— 于是拆两层。
- 新增 `tools/eez_font_bake.py`（只依赖标准库 + 系统 node）：
  - 通用路径候选：`ASAR_CANDIDATES`（Win/macOS/Linux + Program Files）、
    `NODE_CANDIDATES`，可用 `EEZ_STUDIO_ASAR` / `EEZ_NODE` 覆盖。
  - API：`kernel_hash()` / `find_asar()` / `find_node()` / `extract_engine()` /
    `ensure_engine()` / `bake(proj, out_dir, names)`。
  - `bake()` **只写 out_dir + manifest.json，不碰任何工程目录** ——
    落盘位置、增量状态、孤儿清理全交给工程侧胶水。
  - CLI：`--info` / `--clean` / `<工程> <输出目录> [字体名...]`。
- **防分叉机制**：`kernel_hash()` = 内核 `BAKE_JS` 的 sha256，改烘焙行为指纹就变。
  工程侧胶水应 `import` 内核 + 比对期望指纹，而不是复制一份 `BAKE_JS`。
  本轮实测指纹 `242c651b143060ef89b6c8f08c8d79dc6354a5a744e7e7f5d0ce9b55f88c50af`。
- 文档：
  - `tools/README.md` 新增 **「三、构建类（工程无关内核）」**，`eez_font_bake.py` 条目
    （含作为库调用的示例 + 内核/胶水分工说明），原三/四节顺延为四/五节。
  - `skills.md §11.12` 第 6 点补「代码分两层」小节（内核 vs 胶水、`kernel_hash` 防分叉）；
    §11.13 新增 **第六节「代码本身怎么保证不退化」** ——
    产物有真值比对（`font_verify.py`），代码有指纹比对（`kernel_hash()`），两头锁住。
- 验收：`--info` 正确定位本机 asar/node；独立烘焙 11 个字体全部 OK
  （44546 … 446836 B，单字体 100–180 ms）。

---

## v0.8.5 — 字体一致性判据：`font_verify.py` + 验证方法论

- 背景（PR-0053）：工程侧新增 `design/eez_font_engine.py`（解包 EEZ 自带引擎后台烘焙）。
  结论进库了，但**「怎么证明产物和官方一致」这一层没进库** —— 用户指出后补齐。
- 新增 `tools/font_verify.py`（只依赖标准库）：
  - `snapshot` 存黄金样本（记时间/来源标注/sha256 清单到 `_manifest.json`）
  - `check` 逐字节比对 + **自动定位并猜成因** + `--metrics` 比 line_height/base_line
  - `metrics` 只打印度量
  - 退出码 0/1/2，可直接挂 CI
- 成因表把本轮踩的坑编码成可执行检查（见 `skills.md §11.13` 第四节）：
  base64 误解码 / `lv_include` / 空行折叠 / 末尾空白 / `Opts` 参数 / 字形集合 / CRLF /
  人工二分。★ CRLF 会淹没真实差异（首处不同落在第 0 行的 `\r` 上），
  工具先归一化换行符再诊断，并把它单列为一个症状。
- 文档：
  - `skills.md` 新增 **§11.13 怎么证明「后台产物 == 官方产物」**（立真值 / 逐字节比对 /
    清空重建实验 / 定位表 / 三条原则）。核心是**逐字节比对不充分**——
    文件没被覆盖时也全绿，必须再做清空重建 + 全链路复校两轮。
  - `tools/README.md` 对照类新增 `font_verify.py` 条目。
- 自测：真实场景 11/11 IDENTICAL、度量零漂移；注入 3 种故障（lv_include / 末尾空白 /
  连续空行）全部被正确识别。

---

## v0.8.4 — 全 AI 兼容声明 + 机器相关路径「必问用户」机制（当前）

- 用户要求（PR-0045）：① 经验库不绑定 WorkBuddy，所有 AI 都要兼容；② 仿真器等
  **机器相关路径**必须提示用户指定——本机明确 ≠ 换机有效，配置缺失或失效时
  AI 必须停下来问，禁止扫盘猜。
- 全 AI 兼容：README/INTAKE/skills 主体本就是「任何 AI 工具」口径；`INTAKE.md`
  示例 `--tool WorkBuddy` 改为 `<AI 工具名>` 占位；`prompts/PROMPT_LOG.md` 头部
  补「不限工具、标题照实写工具名」约定（历史条目不动）。
- 路径必问机制：
  - `config.template.json` 新增 **`sim` 段**（template_dir/lvgl_src 必填，
    mingw/cmake/sdl2_bin 可选），注释写明「必须向用户询问，禁止猜」。
  - `tools/config_check.py` 新增 **"F 仿真器"** 强校验：sim 段缺失 / 还是占位符 /
    路径在本机不存在 → **ERROR 阻断**，提示向用户询问新路径。
  - 文档同步：`CONFIG.md`（§1 sim 字段说明 + §2 迁移清单 + §3 常见错误表）、
    `PLAYBOOK.md`（§1.3 采集清单 + §1.4 环境雷区）、`README.md`（30 秒上手）。
- 工程侧配套：`design/sim.py` 硬编码的 SIM_SRC/APL_LVGL/MINGW/CMAKE/SDL2 全部
  改为从 `ui_debug_kit.config.json` 的 sim 段读取，缺失或失效硬停并打印
  「请向用户确认新路径」；本机路径经用户确认后写入工程配置。
- `prompts/PROMPT_LOG.md`：PR-0045。

## v0.8.3 — tab pager 经验固化为快速修改 SOP + 「先问后做」交互约定

- 用户要求（PR-0044）：经验总结以"方便后续快速修改"为导向，且**下次遇到这类界面
  先主动询问用户要实现什么效果再动手**。
- `PLAYBOOK.md`：§0 新增第 8 条（tab pager / 导航类界面先问后做）；§5 新增
  **场景 E**——第 0 步确认清单（固定/滑动、高亮跟随、指示条、挂载位置、子元素
  颜色、动画）+ 通用规则四条（导航单实例外置兄弟位、两态样式+继承+动作链、
  验收走真实点击并等动画结束、快速修改三处同步）。规则来自 P-0028，写成
  跨框架通用形态，工程专属改动点索引放工程侧。
- `skills.md`：§11.9 新增第 8 条「快速修改清单」（改动点索引表 + 常见需求最小
  改动 + 自检链）与第 9 条交互约定。
- `prompts/PROMPT_LOG.md`：PR-0044。

## v0.8.2 — tab pager 通用规则：导航外置固定 + CHECKED 高亮跟随

- 用户 EEZ 实测确立通用规则：**所有 tab pager 类型，tab 键固定、只有页滑动**。
  导航挂进 tabview 内容区 = 结构性错误（P-0028：rail_cats 4 副本随页滑）。
- `skills.md`：§11.8.4 重写（副本案废除标注）+ 新增 **§11.9**——单实例外置挂载、
  DEFAULT/CHECKED 两态样式（state 键为字符串、LVGL9 CHECKED=4）、text_color 父链
  继承做子元素颜色跟随、checkedState（LVGLWidget 基类属性）做初始高亮、单
  LVGLActionComponent 多 actions 动作链（objClearState→objAddState→tabviewSetActiveTab，
  executeLVGLApiComponent 顺序执行实证）、仿真截图必须走真实点击。
- `intake/P-0027`：遗留段补「已由 P-0028 解决」闭环标注；`intake/P-0028` 新建、
  `intake/index.md` 同步。
- `prompts/PROMPT_LOG.md`：PR-0043。

## v0.8.1 — 记录区全库体检：状态同步 + 失效锚点修复

- `intake/P-0021/0022/0023`：状态 open→fixed（修复早已落地，登记未同步），补全
  工程/复现/沉淀/标签/关联提示词；P-0021 注明终版修复=P-0025 原生路线（初版
  fix_tabview.py 补丁已在第三轮废除）。
- `cases/README.md`：B5/B6 挤在同一表格行（多余竖线）拆开；B8/B9 引 PLAYBOOK
  §5.6/§5.7 失效锚点改为实际存在节（skills §5.6 / §4.5）。
- `PLAYBOOK.md`：场景 C 步骤 6 自引 §5.6 失效 → 改指 skills.md §5.6 / cases/B8。
- `skills.md`：§11.7 加「已停用（现行=§11.8 tabSize=0 路线，机制留档）」标注；
  §4.1/§6.2/§8 的 G2/check_nav 相关行加「本工程未挂载」注记。
- `README.md`：目录树 cases 补「B1~B10」累积说明。
- 体检方法：全部结论先取证再落笔（工程源码 grep / asar 反编译 / 截图放大），
  历史条目中的当时事实（fix_tabview/click_trace/sim_nav）按「只追加不改历史」保留。

## v0.7 — 新增 A10 断言 + 4 个案例 + 修掉 A6 假阳性

**背景**：一次「按设计稿生成 11 屏、并用 PC 仿真器真渲染验收」的实战里，
暴露出三类此前没被覆盖的问题：**静默失效的样式值**、**嵌套坐标系的二次偏移**、
**构建说成功却没产物**；同时发现 **A6 一直在误报**。

变更：

- `audit_ui.py` 新增 **A10 样式值语法**：颜色类样式值必须形如 `0xRRGGBB`。
  踩的坑：设计源里 `bg = 0x2a3044`（忘加引号）是 int，序列化后写成十进制串 `"2764868"`，
  目标工具只在 **GUI** 报 invalid color，**CLI 构建照样说"零错误"**。
  新配置项：`checks.color_props` / `color_node_keys` / `color_value_patterns`
  （后两者用于"颜色直接写在节点上"的 DSL）。报错会直接点破"少写了引号"。
- **修 A6 假阳性**：生成器给内置字体查表加了 `#if LV_FONT_X ... #endif` 守护，
  开关为 0 时那些引用根本不会编译进去；改为**先剥守护块再统计**
  （`checks.font_guard_aware`，默认开）。另加 `checks.font_switch_ignore`，
  把"工程自烘焙字体"（不走 `LV_FONT_*` 开关）排除，其存在性由 A2/A8 覆盖。
- **A7 改进**：生成器里完全没有匹配的调用时，从"OK"改为打印 **跳过** 并说明原因 ——
  不适用被伪装成通过，比失败更危险。
- 新增 4 个案例：`B5 子控件二次偏移（嵌套容器）`、`B6 样式值写错语法被静默吞掉`、
  `B7 构建成功却零产出`、`B8 仿真器出图的四个坑`。
- `skills.md`：§6.2 门禁表加 `G1-A10`；新增 **§5.6 零点击出图（逐屏快照）**，
  把 L3 从"只能真点击"扩成"也可批量截图"；§8 命令速查补一键链路；
  §11 指向上述案例。
- 文档同步：`tools/README.md` 断言表加 A10 并写明 A6 的两个细节；
  各处「A1~A9」字样更新为「A1~A10」（历史 CHANGELOG 条目保持原样）。


---

## v0.6 — 新增 A9 断言：部件开关

**背景**：实战中发现「界面里的开关点了没反应」。排查后确认：开关被画成了**装饰容器**（`box() + box()` 拼的胶囊 + 圆点），而 EEZ 其实有原生 `LVGLSwitchWidget`。
顺带暴露出一类此前没有断言覆盖的坑 —— **生成代码用了某 LVGL 部件，但运行时配置
把该部件的开关关成 0**（与 A6「字体开关」同源，只是对象从字体换成了部件）。

变更：

- `audit_ui.py` 新增 **A9 部件开关**：扫生成代码里的 `lv_<name>_create()`，
  逐个查 `lv_conf.h` 的 `LV_USE_<NAME>`；**只对「配置里存在但为 0」报 ERROR**
  （配置里根本没有的 —— 如 `lv_obj_create` —— 跳过，避免假阳性）。
- 文档同步：`tools/README.md` 断言表加 A9、`skills.md §6.2` 加 `G1-A9` 行，
  各处「A1~A8」字样更新为「A1~A9」（历史 CHANGELOG 条目保持原样）。


---

## v0.5 — 记录区：新问题登记 + 提示词留痕

**背景**：使用者要求 —— 以后用本技能开发时，遇到的新问题要能"输出进技能里"，
并且**把用户与 AI 的提示词记录下来**以便追查；且**不依赖具体 AI 工具**。

变更：

- 新增 **`INTAKE.md`**：记录规约（何时记 / 记什么 / 怎么记 / 与 `cases/` 的分工 / 给 AI 的常驻指令）
- 新增 **`intake/`**：问题流水。`TEMPLATE.md`（六段式：现象/复现/根因/修复/证据/沉淀）
  + `index.md` 总表 + 每条一个 `P-####_*.md`
- 新增 **`prompts/`**：提示词日志 `PROMPT_LOG.md`（`PR-####`，**逐字抄**用户原话，只追加）
- 新增 **`tools/log_entry.py`**：记录写入器（只用标准库、与工程解耦，**任何 AI 工具都能调**）
  - `prompt` 追加提示词 / `problem` 建问题文件并更新索引 / `list` 汇总 / `next-id` 取号
- **回填**历史对话提示词（`PR-0001`~`PR-0020`），并登记本轮审计发现的 2 个问题
  （`P-0001` 缺 Pillow 裸崩、`P-0002` tab_bar 模板陷阱）
- 文档同步：`README.md` 增「记录区」章节与结构条目（"零痕迹"表述改为
  "内核可移植 + 记录可累积"）、`PLAYBOOK.md` 执行约定增第 7 条、`tools/README.md` 登记 `log_entry.py`

**设计要点**：`intake/` 是"原始流水"（允许粗糙、允许未定论），`cases/` 是"提炼后的案例"（可推广）。
两者靠编号互引（`PR-####` ↔ `P-####`），即可还原「**用户原话 → AI 定位 → 修复 → 沉淀断言**」的完整链条。

---

## v0.4 — 门禁三件套进工具箱

**背景**：`audit_ui.py`（回归断言 A1~A8）/ `gen_clicks.py`（生成真点击用例）/
`run_gate.py`（一键门禁）原先写在工程目录里，脚本内硬编码了工程路径、屏名、
Tab 栏坐标与字体文件名 —— 换个项目就得改代码，违背了"工具箱零工程痕迹"的原则。

变更：

- **三个脚本迁入 `tools/`**，全部改为从配置读取，脚本内不再出现任何工程信息：
  - `audit_ui.py`：路径取 `project.*` / `paths.*`；底栏取 `checks.tab_bar`；
    A3 只在 `theme_defaults` 里该类型 dx/dy 非 0 时才查（框架没这坑就自动跳过）；
    缺输入时打印"跳过"而不是报错
  - `gen_clicks.py`：入口页取 `checks.entry_page`；底栏各项对应页名**自动推导**
    （以按钮中心 x 为键，跨页互相补齐 —— 不能用 children 下标，因为"当前页那一项"
    通常不生成按钮，下标会整体错位）
  - `run_gate.py`：内置 `G1 audit_ui` + `G4 tree_check`；工程专属检查由
    `checks.gates` 挂载（脚本留在工程里，不存在则 SKIP 不阻断）
- **`kit.py`**：Pillow 改为**按需依赖**（纯逻辑工具没装 Pillow 也能跑）；
  字体判定函数 `declared_fonts` / `is_builtin_font` 上移到 kit，`tree_check` 不再各写一份
- **`gen_clicks.py` 新增一类回归**：**底栏空槽位点击不应跳转** ——
  专抓"内容压占底栏 → 点列表行却跳去别的页"（原来那条"点当前项应不动"
  在"当前页不生成按钮"的修法下已退化）
- **配置新增字段**：`project.builder`、`paths.screens_c` / `lv_conf` / `font_c`、
  `checks.gates` / `tab_bar` / `tab_pages`、`tree_schema.type_values` / `nav_types` /
  `style_key` / `main_part` / `default_state` / `width_unit_key` / `content_unit_value`
  （模板与 `CONFIG.md` 同步更新）

---

## v0.4.1 — 修复「缺 Pillow」时的崩溃

**背景**：审计"工具箱拷到新工程能否直接用"时发现：`kit.py` 声称"Pillow 按需依赖、
缺了给安装提示而不是崩"，但只有 `open_gray()`（即 `ink_check.py`）这条路径真的做了检查。

变更：

- `kit.TextMeasurer._font / _icon_font`：加 `require_pil()` —— 之前缺 Pillow 时
  `tree_check.py` / `text_measure.py` 会抛
  `AttributeError: 'NoneType' object has no attribute 'truetype'`，与"明确安装提示"的承诺不符
- `kit.diff_report()`：加 `require_pil()` —— `diff_report.py` 缺 Pillow 时同样裸崩
- `tree_check.py`：缺 Pillow 时**优雅降级**（打印提示并跳过文本度量 / 按墨迹的越界检查，
  仍做字体名 / 跳转 / 入口页 / 纯几何框检查），而不是整体失败

实测：用**不含 Pillow** 的解释器跑 `tree_check.py` → 提示后正常完成（rc=0）；
用含 Pillow 的 venv 跑 `run_gate.py` → G4 PASS 不受影响。

**文档同步**：`README.md` / `PLAYBOOK.md` 的工具与文件清单补上 `skills.md` 与
`run_gate.py` / `audit_ui.py` / `gen_clicks.py`；`README.md` 的"零工程痕迹"表述
限定为"除 `skills.md` 外"。

---

## v0.3 — 与工程彻底解耦

**目标**：工具箱拷到任何 UI 工程都能直接跑，**目录里不留任何工程信息**。

变更：

- **配置外置**：删除工具箱内已填好的配置，改为
  - `config.template.json`（纯占位符模板，随工具箱走）
  - 工程侧配置文件（默认名 `ui_debug_kit.config.json`，放工程里）
  - 查找顺序：环境变量 `UI_DEBUG_KIT_CONFIG` → 从 cwd 向上找 `ui_debug_kit.config.json`
    → 向上找 `config.json` → 工具箱内 `config.json`；找不到时给出带指引的报错
- **移出栈专属内容**：特定技术栈的流水线脚本、抓图脚本、设计源示例全部移出工具箱
  （这些属于工程侧工具，放在工程里）。`tools/` 只保留与框架无关的通用工具。
- **删掉栈专属章节**：`PLAYBOOK` 移除"某栈专项"整章与"实例配置"附录；
  正文只保留通用方法论与跨栈对照。
- **占位符化**：手册与代码模板统一用 `{ROOT}` `{EXE}` `{SCREEN_W}` 等占位符，
  不再出现任何具体路径、字体名、屏名或数值。
- **屏幕尺寸默认值去除**：`kit.screen_size()` 不再硬编码默认分辨率；
  未配置时返回 `(0,0)`，几何类检查自动跳过并提示。
- **内置字体判定配置化**：`fonts.builtin_patterns` 通配列表（默认含常见内置字体命名），
  不再把某一种命名写死。
- **补回 `tools/cdp/grab.js`**（通用抓图器）与 `tools/cdp/launch.sh`（通用启动器）。

---

## v0.2 — 升级为可移植工具箱

**目标**：从"贴着某个工程写的手册"升级为"拷进工程就能用的工具箱"。

- 拆分为"方法论（`PLAYBOOK`）/ 配置 / 工具 / 案例"四层
- 新增可执行工具：`kit.py`（公共库+自检）、`tree_check.py`（静态体检）、
  `diff_report.py`（差异量化）、`ink_check.py`（墨迹检测）、`text_measure.py`（文本度量）
- 新增 CDP 抓图脚本（启动器 + 抓图器）
- 新增案例库（七段式模板）
- 附录补"迁移到新工程"清单

### v0.2 自测修复（工具必须真能跑，跑不过就改）

交付前逐个执行了所有工具，发现并修掉 5 个真问题：

| # | 问题 | 修法 |
|---|---|---|
| 1 | 配置里说明性字段（含 `/`）被误当路径解析 | 加非路径键白名单 |
| 2 | 内置字体被误报"未声明"（大量假阳性） | 新增 `fonts.builtin_patterns` 通配列表 |
| 3 | 字形墨迹偏移算错（`getbbox` 已相对行框顶，却又减了一次 ascent → 偏移为负） | 直接用 `bbox` 值 |
| 4 | 元组被当格式化参数展开导致崩溃 | 显式 `str()` |
| 5 | `diff_report --overlay` 未创建输出目录就写文件 | `os.makedirs(exist_ok=True)` |

**自测结果**：配置自检通过（关键路径全 OK）· 静态体检查**全部通过** ·
墨迹检测批量**无触边** · 差异量化批量**全部 0.0000%** ·
所有 JS 脚本与 shell 脚本语法检查通过。

---

## v0.1 — 初版（经验沉淀）

**来源**：一次跨框架的 UI 调试实战（组件树式 UI + 代码生成流水线）。

内容：

- 三种"效果图"的分工与可信度（设计预览图 / 交叉验证图 / 原生渲染图）
- 对照修复闭环 + 差异量化四步法 + 基准标定法
- 六类自动体检清单
- 组件树类 UI 的通用坑
- SOP、十条红线、案例

**遗留问题**（v0.2/v0.3 解决）：

- 正文里混入了具体工程的路径与数值 → 无法迁移
- 检查代码是"贴进对话的片段" → 不能直接执行
- 案例是手册的一节 → 不易持续追加；且带着具体工程的痕迹

---

## 待办 / 想法

- [ ] `tree_check.py` 增加"配色/对比度"检查（低对比度文本在真机上几乎看不见）
- [ ] `diff_report.py` 增加"按元素区域分区比对"（而不是整图热点）
- [ ] `grab.js` 支持 `--script` 传入自定义注入脚本（适配非文本命名的视图切换）
- [ ] 增加 `run_all.py`：一条命令跑完六类体检并输出汇总报告
- [ ] 案例库补一条"配置值 ≠ 生效值"的独立案例（目前散在 `PLAYBOOK §4.3`）
- [ ] 提供 `config.schema.json`，让配置文件能被编辑器校验
