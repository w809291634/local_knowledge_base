# P-0024 · RAIL_TAB_IDS 用 build_ui 原始 id，被 prefix_ids 加前缀后永不命中，rail FA 图标全部烘焙缺失

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio
- **状态**：fixed
- **标签**：json2eez,字体,FA图标,prefix_ids,id前缀
- **关联提示词**：PR-0036,PR-0037

## 现象（看到什么）

rail 4 个 FA 图标只有 F001（恰在原有 17px 符号集）正常渲染，F4AD/F0F3/F1DE 全是缺字形方框；gen_fonts 报告 17px 图标=6 全是原有码位，13px 图标=2；eez-project fonts[] 的 lvglSymbols 里查无 rail 4 码位

## 复现（怎么稳定重现）

python design/all.py --shots 后读 build/sim_shots 仿真图 rail 区放大裁剪

## 根因（真正的原因）

json2eez.py 的 RAIL_TAB_IDS 键用 s_home 里定义的原始 id（tab_ai 等），但 build_ui.prefix_ids 会给显式 id 加 m_ 分区前缀，ui.json 实际 id 是 m_tab_ai/m_tab_mus/m_tab_notif/m_tab_sett —— dict key 永不匹配，RAIL_ICON_CHARS 从未并入 TEXT_BY_FONT

## 修复（做了什么）

RAIL_TAB_IDS 键改为加前缀后的最终 id（m_tab_*），并以 ui.json 实际 id 为准写进注释；修复后 17px 图标 6->9、13px 2->6，4 个 rail 图标全部正常渲染

## 证据（数字 / 命令输出）

test.eez-project fonts[].lvglAdditionalSources 17px 仅含 F001/F017/F019/F028/F130/F73D；FA woff cmap 实测 4 码位齐全（排除字体缺字形）；ui.json grep 实际 id 为 m_tab_*

## 沉淀（新增断言 / 案例 / 文档）

verify 增补：检查 rail 图标字形是否进 fonts[]（对照 RAIL_TAB_IDS 与 ui.json 实际 id）；skills.md §11 加一条「任何按 id 收集/匹配的字典必须用 prefix_ids 处理后的最终 id」
