# P-0022 · tabName 不进字形收集：tab 标签中文字形缺失（设了字体仍豆腐）

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio 0.29
- **状态**：fixed
- **标签**：json2eez,字体,字形收集,tabview,tabName
- **关联提示词**：PR-0035

## 现象（看到什么）

即使给 tab 按钮指定中文字体，标签仍豆腐块；13px 烘焙字体缺「待机对话语音记录正在播放曲库通用网络显示唤醒」

## 复现（怎么稳定重现）

tabName 含中文 + gen_fonts 后 13px 字体 C 文件搜不到对应字形即可复现（TEXT_BY_FONT 未收 tabName 时必现）。

## 根因（真正的原因）

json2eez.py TEXT_BY_FONT 只收集 label 节点的 text/glyphs；tab 标题存在 LVGLTabWidget.tabName，不是 label，收集不到

## 修复（做了什么）

json2eez.py 的 tab 分支把 title 并入 TEXT_BY_FONT[TAB_LABEL_FONT]（初版 13px；后演进为 15px 主 + 13px 兜底，rail tabName 写「图标字符+换行+中文」两行，图标与文字字形一并收集——见 json2eez.py:380-389）。机制在后续 tabSize=0 隐藏原生栏后仍保留（tabName 不再渲染但字形收集无害，且首子容器口子如复用仍需要）。

## 证据（数字 / 命令输出）

gen_fonts 输出：13px text=字形数修复前不含 tab 标题字；修复后 13px 覆盖全部 14 个 tab 标题字

## 沉淀（新增断言 / 案例 / 文档）

skills.md §11.6 第 3 条（tabName 字形兜底）、§11.7 第 5 条（主/兜底字体都要收 tabName 字形）；凡新增「非 label 载体文本」必须同步进 TEXT_BY_FONT 收集
