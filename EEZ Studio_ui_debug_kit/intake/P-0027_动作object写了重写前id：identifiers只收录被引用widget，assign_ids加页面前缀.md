# P-0027 · 动作引用控件写了重写前的 id：EEZ identifiers 只收录被引用 widget，assign_ids 会加页面前缀

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio 0.29
- **状态**：fixed
- **标签**：EEZ原生,tabview,动作,identifier,命名重写,tabviewSetActiveTab
- **关联提示词**：PR-0040

## 现象（看到什么）

按 P-0026 路线把四个 tabview 全部 `tabSize=0` 隐藏原生 tab 栏、用设计稿 rail 容器重建导航后，EEZ headless build 报 **16 个 `Widget index not found for "main_nav"`**（每个动作组件一条），并伴随 `Unhandled error: TypeError: Cannot read properties of undefined (reading 'selectTab')`，构建失败。

## 复现（怎么稳定重现）

json2eez 生成的 switchTab 动作（tabviewSetActiveTab）object 字段直接写 build_ui 里的原始 id 字符串 `"main_nav"`，跑 `eez_build.py` 即稳定复现。

## 根因（真正的原因）

两条机制层实锤（asar 反编译）：① `getWidgetObjectIndexByName` 在 `getPageIdentifiers(e).identifiers` 里 `indexOf(t)` 查找，而 **identifiers 表在 finalizeObjectAccessibleFromSourceCodeTable 里只 push「第一遍扫描中被 markObjectAccessibleFromSourceCode 标记的对象」**（即生成器会输出 `objects.xxx` 引用的 widget）；且 identifier 名就是工程 JSON 里 identifier 字段原值（UnderscoreLowerCase 规范化）。② 本工程的前缀重写发生在 **build_ui.py 的 assign_ids（PAGE_ALIAS["Main"]="m"，另有 prefix_ids）**——不是 json2eez（json2eez 只消费 ui.json），显式 id 被加页别名前缀（`main_nav` → `m_main_nav`，screens.c object_names 实锤）。动作里写字符串 `"main_nav"` 在 identifiers 表 indexOf 落空 → 每个动作组件报一条 not found，EEZ 内部随后在 undefined 上取 `selectTab` 崩溃。注意 getWidgetObjectIndexByName 第一遍扫描直接 return 0（不查表不报错），报错只出现在第二遍——报错条数=动作组件数。

## 修复（做了什么）

结构级修法，禁止跨节点手写 id 字符串：switchTab 数据结构改为 `{"tv_ref": <tabview DSL 节点引用>, "tab": N}`，build_ui `main()` 在 json.dump 前调 `_resolve_switchtabs()` 递归把 tv_ref 换成 `tv_ref["id"]`——assign_ids 是原地改写节点 id，且在导航容器挂进 screen **之后**调用，此刻解析必得最终 id。json2eez 侧把解析后的 `tv` 写进 `tabviewSetActiveTab` 动作（actions-catalog id 60，properties object/tab/animated），以 `LVGLActionComponent` + connectionLine（与 goto/changeScreen 同机制）生成 16 条动作连线（主导航 4 + 设置分类 12）。

## 证据（数字 / 命令输出）

EEZ build **No error and no warning**（16 errors 与 selectTab TypeError 全部消失）；screens.c 四处 `lv_tabview_set_tab_bar_size(obj, 0)`；eez-flow.cpp `actions[]` 表（表长 65）index 60 = `&tabviewSetActiveTab`（LVGL 9 → `lv_tabview_set_active`）；asar @100450441 `registerAction({id:60, name:"tabviewSetActiveTab", properties:[{object,widget:Tabview},{tab,integer,0-based},{animated,boolean}], defaults:{animated:true}})`。`all.py --sim` 11/11 屏，**G5 平均 17.10% → 8.84%**（01 待机 10.49 / 07 设置 6.96），对照三联图确认 rail 形态与设计稿一致。

## 遗留（核对后确认，未修）

主 rail 高亮**静态固定「对话」**：rail() 全屏只挂一份实例（screen 级，z 序在 main_nav 之上），切到音乐/通知/设置 tab 后高亮不跟随（05 音乐页放大实证：高亮仍在对话项，与设计稿不符）。设置左栏 rail_cats 则是每个子 tab 首位挂一份副本（4 份：wifi/wifi/sun/mic），子 tab 内静态高亮成立。主 rail 高亮跟随需 selectedTab 绑变量/样式表达式或每主 tab 一份副本——尚未实现；G5 平均分掩盖该偏差（60×55 高亮块错位仅占全屏 ~0.9%），验收时必须跨主 tab 单独放大看 rail。

## 沉淀（新增断言 / 案例 / 文档）

skills.md 新增 §11.8（tabSize=0 隐藏原生 tab 栏 + tabviewSetActiveTab 动作路线 + 「凡跨节点引用控件一律节点引用 + assign_ids 后统一解析」原则，与 §11.5/P-0024 同源上升机制层）
