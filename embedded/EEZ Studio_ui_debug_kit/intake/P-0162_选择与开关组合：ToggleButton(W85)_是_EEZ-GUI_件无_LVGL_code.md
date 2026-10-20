# P-0162 · 选择与开关组合：ToggleButton(W85) 是 EEZ-GUI 件无 LVGL codegen；Dropdown/Roller selected 可双向绑定做联动；Switch/Checkbox 无绑定属性

- **工程**：EEz_stidio_examples/w23-w59-w73-w16-select-switch
- **日期**：2026-10-20
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：Dropdown,Roller,Switch,Checkbox,ToggleButton,Tabview,联动,assignable,per-tab bisect,EEZ-GUI件,lvglBuild
- **关联提示词**：PR-0262

## 现象（看到什么）

组合初版含 ToggleButton：EEZ CLI 构建报 TypeError: t.lvglBuild is not a function + Cannot read properties of undefined (reading 'selectTab')；且 Switch/Checkbox 拖入后无可绑定属性，联动无从下手

## 复现（怎么稳定重现）

LVGL 9.4 工程：type="LVGLToggleButtonWidget"（猜的名）+ Tabview(tabviewSize=30 可见) 挂 4 个 Tab（Dropdown/Roller/Switch/Checkbox 各一页，Dropdown/Roller 的 selected 同绑 g_sel）

## 根因（真正的原因）

①ToggleButton 的 EEZ 类=ToggleButtonWidget（无 LVGL 前缀，继承 EEZ-GUI Widget 基类，必填 data/text1/text2，toLVGLCode 不存在）→ 在 LVGL 工程必报 lvglBuild 错误；②EEZ 的 Dropdown/Roller 有 selected assignable（双向）而 Switch/Checkbox 没有（defaultValue 仅几何+checkedState）——联动只能选有 assignable 的件；③构建失败时 EEZ Studio 进程残留（单实例锁）会让后续构建 TIMEOUT，需先 taskkill

## 修复（做了什么）

剔除 ToggleButton（LVGL 等价物=CHECKABLE Button）；联动改用 Dropdown+Roller selected 同绑 g_sel（两控件跨页互相同步，零 flow 图）；排障用 per-tab bisect（每页单独成工程构建定位）+ cli_build.py 支持 argv 指定工程文件 + 构建前 taskkill 残留进程；改名/换目录后删 build_rel

## 证据（数字 / 命令输出）

per-tab bisect：drop/roll/sw/chk 单页各自构建 ok（证明控件无罪）；完整 4 页工程构建 ok（0 错 0 警）；screens.c 命中 10 处（dropdown/roller/switch×2/checkbox×2/tabview/add_tab×3+g_sel 绑定）；PC_SIM 编译链接 0 错

## 沉淀（新增断言 / 案例 / 文档）

w23-w59-w73-w16-select-switch/README.md、根 README 索引、模板说明.md（bisect 方法）、workspace memory 2026-10-20
