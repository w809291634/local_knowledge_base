# P-0128 · kit 工具在 Windows GBK 控制台因 ✓/✗ 字符 UnicodeEncodeError 崩溃

- **工程**：通用（本机）
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：kit,编码,GBK,控制台,PYTHONIOENCODING
- **关联提示词**：PR-0214

## 现象（看到什么）

config_check.py / tree_check.py 检查全部跑完后在打印结论行（含 ✓/✗）时崩溃：'gbk' codec can't encode character '\u2713'。

## 复现（怎么稳定重现）

Windows 控制台默认 GBK 码页 + PYTHONIOENCODING 未设时运行 kit 工具。

## 根因（真正的原因）

工具结论行用 ✓/✗ 等非 GBK 字符打印 stdout。

## 修复（做了什么）

运行前 export PYTHONIOENCODING=utf-8（不改工具本体）。

## 证据（数字 / 命令输出）

设 UTF-8 后同两工具完整输出、无崩溃。

## 沉淀（新增断言 / 案例 / 文档）

（待补）
