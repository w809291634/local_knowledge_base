# P-0028 · 设置左栏随页滑动：tab pager 导航必须外置固定，高亮走 CHECKED 动作链跟随

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio 0.29
- **状态**：fixed
- **标签**：EEZ原生,tabview,动作,objAddState,checkedState,样式状态,导航固定
- **关联提示词**：PR-0043

## 现象（看到什么）

用户在 EEZ 中启动实测：设置界面点击左栏小 tab（分类行）时**整个页面（含 tab 栏本身）都在滑动**。用户确立通用规则：**以后所有 tab pager 类型，tab 键固定、只有页滑动**。

## 复现（怎么稳定重现）

设置页点击任一可点分类行（网络与连接/显示与音量/语音唤醒）。根因在生成结构：rail_cats 的 4 份副本挂在各 set 子 tab 的 children 首位（build_ui.py s_home）——**导航在 tabview 内容区里**，点击触发 tabviewSetActiveTab 后内容横滑，左栏副本作为内容一部分跟着滑。主 rail 虽挂 screen 级不滑，但高亮静态钉死「对话」（P-0027 遗留），切 tab 不跟随。

## 根因（真正的原因）

导航挂载位置错误 + 高亮机制缺失：① rail_cats 副本挂进 tabview 内容区 = tab pager 结构性错误；② 单实例导航要高亮跟随，需要「对象状态（LV_STATE_CHECKED）+ 两态样式 + 点击时批量切换状态」的机制链，此前未打通。

## 修复（做了什么）

1. **结构**：rail_cats 改单实例，挂 `sett["children"] = [sett_nav, rail_cats(...)]`（tabview 兄弟位，z 序在上）；4 份副本删除。rail 维持 screen 级。
2. **两态样式**：导航项 DEFAULT/CHECKED 都写全（asar `LVGL_STYLE_STATES` 实证 state 键为字符串；LVGL9 数值 CHECKED=4，lvglStates_V9_5_0 表）。文字/图标**不写色**走 LVGL text_color 父链继承（build_ui label() 支持 color=None 不落样式键）——按钮两态 text_color（TEXT3 灰 / TEXT 白或 0xc6d1ff 亮蓝）自动作用到子 label；继承链无状态样式兜底的静态项（rail_cats 不可点行）写死 TEXT3。
3. **初始高亮**：DSL `checked:true` → json2eez 输出 `checkedState:true/literal`（asar 实证 checkedState 是 **LVGLWidget 基类属性**，所有 widget 可用；codegen literal 时生成 `lv_obj_add_state(obj, LV_STATE_CHECKED)`）。
4. **点击动作链**：switchTab 扩展 `{"tv_ref":<节点引用>, "tab":N, "add":[<引用>...], "clear":[<引用>...]}`；`_resolve_switchtabs` 统一解析成最终 id（P-0027 铁律）。json2eez 生成**单个 LVGLActionComponent 多 actions**（eez-flow.cpp:4191 `executeLVGLApiComponent` 对 actions[] 逐条顺序执行）：`objClearState(其余项,CHECKED)` → `objAddState(自己,CHECKED)` → `tabviewSetActiveTab`。asar 实证 id:20 objAddState / id:21 objClearState（object(widget)+state(enum:LV_STATE)，字面量 `"state":"CHECKED"`）。
5. **仿真点击驱动**：sim.py 直调 lv_tabview_set_active 会绕过动作链（高亮不跟随、G5 虚高），改为优先 `lv_obj_send_event(导航按钮, LV_EVENT_CLICKED, NULL)`；补 `lv_tick_inc` 驱动 + shoot 时间片 25→100 轮（400ms，animated:true 切页动画 180ms 要走完再截屏）。

## 证据（数字 / 命令输出）

EEZ build **No error and no warning**；screens.c：m_nav_chat/m_cats_wifi/m_navmk_chat 各有 `lv_obj_add_state(obj, LV_STATE_CHECKED)` + 两态样式（DEFAULT 0x6b7488 / CHECKED 0x5b7cfa opa 36 + 亮字）；工程 JSON：7 个动作组件（cats 链 4 动作、rail 链 9 动作，clear→add→setTab 顺序正确）、checkedState=true 恰 3 个新对象（m_cats_wifi/m_nav_chat/m_navmk_chat）、identifier 633 个无重名。**G5 平均 8.84% → 8.54%**（11/11 屏过；08 语音唤醒 9.45→7.60、10 显示 8.26→6.42——点击驱动后 cats 高亮与设计稿对齐）。目检 10_display：rail「设置」高亮（含左缘指示条）+ cats「显示与音量」高亮 + 其余灰字；05_now_playing：rail「音乐」高亮——P-0027 遗留的「主 rail 高亮不跟随」同步解决。

## 遗留（核对后确认，未修）

AI/音乐子 tab 当前**无导航 UI**（设计稿这几页没有顶部 tab 栏，仅初始 actTab 定页）——用户未要求，暂不动；若后续要可切换，按本节规则补顶部导航条（外置固定 + 同款动作链）。

## 沉淀（新增断言 / 案例 / 文档）

skills.md §11.8.4 重写（副本案废除标注）+ 新增 §11.9（tab pager 通用规则全机制：结构/两态样式/状态继承/checkedState/多动作链/仿真点击驱动）；CHANGELOG v0.8.2。
