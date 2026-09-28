# P-0022 · tabName 不进字形收集：tab 标签中文字形缺失（设了字体仍豆腐）

- **工程**：（待补）
- **日期**：2026-09-28
- **工具**：未知工具
- **状态**：open
- **标签**：（无）
- **关联提示词**：（无）

## 现象（看到什么）

即使给 tab 按钮指定中文字体，标签仍豆腐块；13px 烘焙字体缺「待机对话语音记录正在播放曲库通用网络显示唤醒」

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

json2eez.py TEXT_BY_FONT 只收集 label 节点的 text/glyphs；tab 标题存在 LVGLTabWidget.tabName，不是 label，收集不到

## 修复（做了什么）

json2eez.py 的 tab 分支把 title 并入 TEXT_BY_FONT[TAB_LABEL_FONT]（YaHei_Consolas_Hybrid_13，与 fix_tabview.py 的按钮字体常量对应）

## 证据（数字 / 命令输出）

gen_fonts 输出：13px text=字形数修复前不含 tab 标题字；修复后 13px 覆盖全部 14 个 tab 标题字

## 沉淀（新增断言 / 案例 / 文档）

（待补）
