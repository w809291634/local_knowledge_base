# CHANGELOG —— 工具箱迭代记录

> 约定：只往前追加。方法论被推翻时不要删旧条目 —— 在同一版里写清"改了什么、为什么改"。
>
> 注意：本文件描述的是**工具箱自身**的演进。工程专属的构建流水线、屏名、字体等
> 不属于工具箱，请写在工程侧的文档里。

---

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

> 注：具体换算实现（`to_relative()` / `check_bounds()`）属工程侧，
> 不进工具箱；工具箱沉淀的是**规则与判据**。

---

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

> 注：`design/` 那套生成脚本（DSL 构建 / 转换 / 仿真器适配 / 对照）属于**工程侧**，
> 不进工具箱；工具箱只沉淀**通用断言与案例**。

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

> 注：具体部件类型（switch 等）与其开关映射属于**工程侧**的设计源/生成器，
> 不进工具箱；工具箱只提供这条通用断言。

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
