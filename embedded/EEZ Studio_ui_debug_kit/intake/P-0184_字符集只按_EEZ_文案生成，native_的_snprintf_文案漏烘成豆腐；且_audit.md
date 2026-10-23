# P-0184 · 字符集只按 EEZ 文案生成，native 的 snprintf 文案漏烘成豆腐；且 audit_chars 查不出

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：字体,字符集,门禁,gb2312,CP936
- **关联提示词**：PR-0356

## 现象（看到什么）

列表行副文案「WPA2 · -41 dBm · 2.4 GHz」的分隔符在仿真里是两个豆腐方块，但 design/audit_chars.py 报 OK: 每一个文字都在字体字符集内。

## 复现（怎么稳定重现）

跑 design/shot_states.py 出 done.png；或 python design/audit_chars.py 看 rc=0。

## 根因（真正的原因）

两处叠加：① build_example 的字符集来自 python 'gb2312' 编解码器，它把 0xA1A4 解成 U+30FB「・」（simhei 没有，被 cmap 过滤丢弃），而 native 源码里的分隔符是 CP936/GBK 的 U+00B7「·」——字符集里从来没有它；② audit_chars.py 只遍历 .eez-project 的 text/placeholder，native C 源码里的字符串字面量不在审计面内，所以漏字照样全绿。

## 修复（做了什么）

① build_example.py 增设 NATIVE_SYMBOLS（当前含「·」）并入 _RAW_CHARS；② audit_chars.py 追加扫描 src/native/**.{c,cpp,h} 的字符串字面量（先剥 /* */ 与 // 注释，再按 unicode_escape 还原），与 FONT_CHARS 对账。

## 证据（数字 / 命令输出）

非 ASCII 审计字数 30→60（native 文案进入审计面）；反向测试：把 NATIVE_SYMBOLS 置空 → audit rc=1 且点名 U+00B7；复原 rc=0。重烘后 build/sim_shots/done.png 行内分隔符为「·」，无豆腐。

## 沉淀（新增断言 / 案例 / 文档）

cases/B1 同族（字体源分配）+ 本工程 EEZ_WORKFLOW §5.5 + audit_chars 覆盖面
