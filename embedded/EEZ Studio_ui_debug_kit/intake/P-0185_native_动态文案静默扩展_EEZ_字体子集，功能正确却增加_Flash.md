# P-0185 · native 动态文案静默扩展 EEZ 字体子集，功能正确却增加 Flash

- **工程**：watch（EEZ no-flow + LVGL 9.4）
- **日期**：2026-10-23
- **工具**：Codex
- **状态**：fixed
- **标签**：字体,字形子集,Flash,动态文案,EEZ,LVGL,内存预算
- **关联提示词**：PR-0357

## 现象（看到什么）

为运行时状态增加中文提示与罗马数字后，design/build_watch_ui.py 将它们加入 RUNTIME_TEXTS，EEZ 字体字形从 302 扩到 310；所有 11 个 ui_font_cn*.c 均变大。

## 复现（怎么稳定重现）

在生成器的 collect_texts() 额外加入动态字符串，重生 watch.eez-project 后运行 eez_font_bake.py，比较 src/ui/fonts/ui_font_cn*.c 与基线哈希。

## 根因（真正的原因）

EEZ 按项目 lvglGlyphs 为每个字号烘焙子集；为了避免豆腐字而无差别添加动态中文，会使每个相关字号的字体 C 源增长。运行时逻辑只需要状态表达，不一定需要新中文字符。

## 修复（做了什么）

移除 RUNTIME_TEXTS；动态状态复用设计中已有的中文（例如 测量/开始/暂停）或 ASCII（BLE OFF、BLE ON、...、||）。重新生成工程并使用官方 eez_font_bake.py 重烘字体。

## 证据（数字 / 命令输出）

生成器输出码位从 310 回到 302；11 个 ui_font_cn*.c 与 HEAD 的 Git blob 哈希逐一相等；PC_SIM 完整编译成功，功能与导航回归 61 PASS / 0 FAIL。

## 沉淀（新增断言 / 案例 / 文档）

已写 P-0185；提炼 B16：动态文案先做字形预算，新增字形必须按字号、Flash 增量和必要性审批。
