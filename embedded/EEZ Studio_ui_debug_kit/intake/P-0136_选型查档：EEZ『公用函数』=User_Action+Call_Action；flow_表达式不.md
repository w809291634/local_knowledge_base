# P-0136 · 选型查档：EEZ『公用函数』=User Action+Call Action；flow 表达式不能内联调函数——单点复用保持内联更优

- **工程**：watch (Design Watch)
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：user-action,call-action,公用函数,表达式边界,选型对比,objGetDisplayY同族
- **关联提示词**：PR-0221,P-0131

## 现象（看到什么）

用户问『公式能否变成公用函数』——需要知道 EEZ 官方的函数化机制及适用代价

## 复现（怎么稳定重现）

手册 P7.3.2/A32/A54 + asar CallActionActionComponent 注册；表达式函数目录 P8.3 无用户函数

## 根因（真正的原因）

EEZ 的复用机制是流程级的(User Action 组件)，不是表达式级的；把每行标量计算函式化会引入 22 组件/帧调用/22 流态分配——单点使用代价大于收益；真正收益点是多处复用

## 修复（做了什么）

决定=保持内联（设计源 WHEEL_EXPR 已是单常量）；三形态对比与升级路径记档（报告 §20 + reference/07 §4 + skills §11.37 交叉引用）；若将来第二处复用/曲线需 EEZ 内可调再启用 User Action（采用前须最小原型验 Call Action 出参）

## 证据（数字 / 命令输出）

对比表：现状 66 执行/帧最省；A=88+22 流态/帧；B=88；D=66+1 流态。手册 P7.3.2 原文 + asar 类定义（userPropertyValues/getAdditionalFlowProperties）

## 沉淀（新增断言 / 案例 / 文档）

reference/07 §4 补 flow 实现与表达式限制；报告 §20
