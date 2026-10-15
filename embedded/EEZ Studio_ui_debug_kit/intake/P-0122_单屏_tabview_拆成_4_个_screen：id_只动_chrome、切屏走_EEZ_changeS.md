# P-0122 · 单屏 tabview 拆成 4 个 screen：id 只动 chrome、切屏走 EEZ changeScreen、高亮退回 DSL 画死

- **工程**：lvgl_demo_ai/eez-test · **日期**：2026-10-14 · **工具**：Qoder · **状态**：fixed（仿真器已验；真机待烧）
- **标签**：EEZ,多screen,tabview,identifier全局唯一,changeScreen,push栈,fadeMode,assign_ids,仿真门禁,走路nav命令
- **关联提示词**：PR-0202
- **关联**：P-0116/P-0119（都还按单屏 tabview 写）、esp32 子库 §10

## 诉求
用户：「eez 中就创建了一个 screen，我想使用 4 个，避免所有事件 flow 都在一个 screen」；随后**主动放弃滑屏**：
「这几页不需要滑屏，使用点击按钮切换」。⇒ 外层四个分区（对话/音乐/通知/设置）从 1 个 tabview 的 4 个 tab
变成 4 个 screen；**子页（待机·对话 / 正在播放·曲库 / 通用·显示·唤醒）仍是 tabview**，一行没动。

## 落地时省掉大麻烦的三个决定
1. **四个 screen 共用同一个 alias "m"**（`PAGE_ALIAS`），内容控件 id 因此**逐字不变**
   （565 个里 534 个原样保留）⇒ native/sim 里成百个 `objects.m_xxx` 引用一个都不用改。
   只有重复画出来的 chrome（状态栏 + rail，约 22 个/屏）需要新名字。
2. chrome 用 **`_cid(base, tag)` 把页标签加在末尾**（`nav_item_music_mus` → 短名替换照常命中 →
   `m_nav_music_mus`）。加在开头会让 `EXPLICIT_SHORT` 的前缀替换失效，名字变长且不可读。
3. 切屏**不写 native 导航器**，直接用 EEZ 的 `goto`→`changeScreen`（CLICKED）；
   rail 高亮**退回 DSL 里 `checked:True` 画死** —— 每屏一份 rail，本屏那项天然就是亮的，
   于是 `switchTab(clear/add)` 与 `onTabChange(VALUE_CHANGED→GetActiveTab→Compare→add)` 两条
   动作链在外层**整体退役**（少一套运行期同步 = 少一个第二真值源）。

## 踩到的（都不是猜的）
- **EEZ identifier 是全工程唯一**，而且 `assign_ids` 的去重表原来是**每页独立**的 ⇒
  没写显式 id 的节点会得到 `m_box` / `m_t` / `m_txt`，四屏各自从 2 开始编号 → 跨页必撞
  （`json2eez.check_identifiers` 当场 ValueError）。改法：去重表改成**模块级共享** `_ID_USED`。
- 另一个撞名点不在 DSL 而在 **json2eez 自己生成的 Comment**：`m_title_tabsync%d` / `m_title_col%d`
  是裸 `m_` 前缀 + **每页重新计数** ⇒ 多页必撞。改成 `m_title_%s_tabsync%d % (name,k)`。
- `place()` 会**无条件抹掉 goto**（单屏时代遗留）⇒ 待机页 4 张 tile 要跨屏，必须加 `keep_goto=True`，
  否则切屏动作被静默吃掉。
- **`changeScreen` 这版引擎只有 push**（`eez-flow.cpp:3176-3182`：`specific->screen != -1` 就
  `eez_flow_push_screen`），json2eez 写的 `useStack` 字段**运行时根本不读** ⇒ 以为设了 replace 其实没有。
  实测无害：栈是 `int16 g_screenStack[10]`，满了**挤掉最老的**，不崩不漏；native 主动跳（语音命令）
  用 `eez_flow_set_screen()`，它会把 `g_screenStackPosition` 归零 = 真 replace。
- sim 模板是 **C**，不能 include `eez-flow.h`（C++ 头）⇒ `eez_flow_set_screen/get_current_screen`
  就地补 `extern` 声明（引擎里这两个本来就是 `extern "C"`）。
- rail 变成**每屏一份**后，走路器原来 `wmap_add("nav_music", objects.m_nav_music)` 那种固定指针全废
  ⇒ 新增 `nav <chat|music|bell|tune>` 命令，按**当前屏**取按钮（`rail_btn_cur`），16 行 `tap nav_X` 机械替换。

## 验收（仿真器，全部实跑）
- `all.py --sim` **rc=0**，门禁 **9 屏平均明显差异 9.84%**（拆分前基线 9.88~9.95%，等于没画歪）。
- 冒烟：待机页点「播放音乐」tile → `main_nav tab=1 (expect 1)`；点通知 tile → `2` ⇒ goto 动作通。
- rail 真点击：`[rail] base: scr=0 rail=1000` → `click music: scr=1 rail=0100` → `back to ai: scr=0 rail=1000`
  ⇒ 切屏 + 目标屏高亮**只有 DSL 一份真值**也对得上。
- 设置内层（仍是 tabview + cats 左栏）`[swipe] sett up: tab=1 cats=010` 不受影响。
- 设备端 `idf.py build` rc=0，bin `0x4e8110 → 0x4ee060`（+24KB，flow 字节码变长）。

## 已知遗留（下次别当成已做完）
- 切屏动画目前是 EEZ 默认 **FADE_IN**（json2eez 写死 `"fadeMode": node.get("gotoFade","FADE_IN")`）；
  用户如果要"推入"观感，改 DSL 里加 `gotoFade="MOVE_LEFT"` 并**先看 EEZ 接不接受这个字面量**（未验）。
- 每屏一份 chrome ⇒ LVGL 对象数 +3×22 个（启动即建，不随切屏销毁）；真机内存待看开机那行 `mem:`。
- 语音命令/点歌的切屏目标已改 `eez_flow_set_screen(SCREEN_ID_MUSIC,...)`，但**真机未验**（任务 #22/#26）。


## 追加（同日）：切屏时左侧导航跟着淡 → 物理结论 + EEZ 内的正确解

用户：「左侧按钮能做到顶层吗，避免点击后按钮也呈现淡入淡出效果，要求 EEZ 中修改」。

**为什么"顶层"在 EEZ 里做不到（查证，不是印象）**：`lv_scr_load_anim()` 的动效作用在
**整个 screen 对象**上，它的子孙一起被动效覆盖 ⇒ 导航栏画在 screen 里就必然跟着淡/跟着滑。
EEZ 只有 `createAtStart` / `deleteOnScreenUnload` / `screensLifetimeSupport` 三个屏生命周期开关，
控件父节点只能是别的控件或屏，**没有 `lv_layer_top` 这一档**：
在 EEZ Studio 本体（`resources/app.asar`，116MB）里 `lv_layer_top` / `lv_obj_set_parent` 的出现全是
**LVGL WASM 预览的导出桩**（`Module['_lv_layer_top'] = makeInvalidEarlyAccess(...)`），
`topLayer` 全是 Floating-UI 的 DOM 代码 —— 都不是工程模型里的能力。
⇒ 想要真·常驻顶层，只能 native 一行 `lv_obj_set_parent(rail, lv_layer_top())` + 删掉其余 3 份 rail
   + **把刚退役的 CHECKED 运行期同步请回来**（顶层那份不再"每屏一份"，高亮必须有人刷）。

**EEZ 内的正确解（已落地）**：屏间过渡一律 `NONE`。
`build_ui.py` 单点常量 `SCREEN_GOTO_FADE="NONE"` / `SCREEN_GOTO_SPEED=0`，rail 按钮与待机页 tile
的 goto 都读它 ⇒ 导航栏与内容同时瞬切，没有任何淡入淡出。
native 侧语音切屏同步改成 `eez_flow_set_screen(SCREEN_ID_MUSIC, LV_SCR_LOAD_ANIM_NONE, 0, 0)`
（两条切屏路径必须同一口径，否则语音和手点是两种观感）。
- EEZ **认 "NONE"**：`eez_build.py` 报 `No error and no warning detected`；工程里 16 条 changeScreen
  的 fadeMode 全 = NONE、speed 全 = 0（数出来对得上：4 屏 ×3 个 rail + 4 张 tile）。
- `all.py --sim` rc=0，门禁 **9.85%**，`[rail] click music: scr=1 rail=0100` 照旧过。
- 设备 `build` rc=0（bin 0x4ee050）。

**还想要"内容有动效、导航不动"**：只能走 `NONE + EEZ playAnimation 给每屏内容容器做入场动画`，
但"屏加载时"这个触发事件 EEZ 有没有暴露**未查**（`eez-flow.cpp` 只见 `LV_EVENT_SCREEN_UNLOADED` 被用来销毁屏）。
要推入式（MOVE_LEFT）则导航栏必然跟着滑 —— 这一点先讲清再选，别等烧完才发现不是想要的。
