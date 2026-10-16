# P-0127 · watch 工程就绪缺口四项：design_src 非 JSON 崩溃 / node 裸命令 / A8 设计侧口径 / check_project.py 悬空

- **工程**：Design Watch（watch UI 工程）
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：kit,配置,就绪,A8,check_nav,node,直出型工程
- **关联提示词**：PR-0214

## 现象（看到什么）

config_check.py 在 design_src=build_watch_ui.py(非JSON) 时 json.load 崩溃；binaries.node 写裸命令 'node' 被判不存在(ERROR)；run_gate A8 报设计侧=0(节点级 goto 遍历不适用直出型工程)；config 注释引用的 design/check_project.py 从未存在。

## 复现（怎么稳定重现）

cd 工程根跑 kit.py/config_check.py/run_gate.py

## 根因（真正的原因）

直出型工程（无中间 DSL，design_src==project_file）与 kit 假设不匹配：工具预期可解析 JSON 设计源 + 节点级 goto 字段。

## 修复（做了什么）

① design_src 指向 watch.eez-project（检查类工具以 EEZ 工程 JSON 为可解析设计源）；② node 改绝对路径；③ kit 加 checks.a8_design_equals_project 开关(默认false) + 新建 design/check_nav.py 作为 G2 门禁（链路计数/死链/死胡同，基线 15）；④ 注释更新、check_project.py 记为待补。

## 证据（数字 / 命令输出）

修复后：config_check OK29/WARN0/ERROR0『完全适配』；run_gate 三组全绿 G1+G2+G4（修复前 A8 报 design0/project15/code15）

## 沉淀（新增断言 / 案例 / 文档）

kit CHANGELOG v0.9.5
