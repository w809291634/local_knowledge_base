# P-0134 · 旧经验「`%` 也永远返回 double」是错的——int×int 的 % 保整数（源码+受控实验双证）

- **工程**：EEZ Studio_ui_debug_kit（跨工程方法论）
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：表达式引擎,op_mod,整数类型,getUInt32,位型毒化,受控实验,P-0043更正
- **关联提示词**：PR-0218,PR-0219,P-0131

## 现象（看到什么）

库内三处（P-0043 坑2、reference/07 §10 陷阱1、CHANGELOG v0.8.6）声称『/ 与 % 永远返回 double』；新会话若信  也被逼用三目阶梯绕行，浪费且可能写出更复杂的帧表达式

## 复现（怎么稳定重现）

读 watch 工程 src/ui/eez-flow.cpp（eez-framework commit 10f714f9）op_mod：int32 分支 return Value((int)(a.int32Value % b.int32Value), VALUE_TYPE_INT32)；double 分支仅当任一边 isDouble/isFloat/isInt64

## 根因（真正的原因）

P-0043 当年的『MOD 实证 double』应来自已含 double 操作数的表达式（如前面带 ），把个例概括成了语言规则

## 修复（做了什么）

① 受控实验：滚轮表达式临时加恒等项 N % 2147483647（N≤153M）→ 全链重建 → 盘径 192/212/243/219/195 与基线逐位一致（若 % 产 double，>> 对非整数报错、行会保持静态值，非实测）；② reference/07 §10 陷阱1 改写为：/ 恒产 double（头号雷）、% 等 int×int 保整数、统一纪律=喂整数动作的值必须整数型；③ P-0043 追加更正块；④ CHANGELOG v0.9.6 记录更正；⑤ 实验后已还原生成器并重建全部产物（回归 PASS、门禁全绿）

## 证据（数字 / 命令输出）

受控实验盘径（实验态 vs 基线 vs 最终态）：57/48/72/65/58 三轮完全一致；eez_build 'No error and no warning detected'；G1/G2/G4 PASS

## 沉淀（新增断言 / 案例 / 文档）

skills §11.37 二·① 已写更正后的纪律
