# P-0003 · json2eez 备份文件未被忽略，累积 308MB 污染 git

- **工程**：spilcd_spiopt_eez_lv_port_pc_tem_atks3
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：工件卫生,git,备份
- **关联提示词**：（无）

## 现象（看到什么）

git status 出现 ?? test.eez-project.bak-<时间戳>；工程内累积 15 个备份共 308.4MB

## 复现（怎么稳定重现）

运行一次 design/json2eez.py 就生成一个约 20MB 的 test.eez-project.bak-<时间戳>

## 根因（真正的原因）

json2eez.py 每次自动备份工程，但仓库（根 .gitignore）未忽略该模式，且无工程级 .gitignore

## 修复（做了什么）

在 main/test/ 新建 .gitignore，忽略 *.bak-* 与 __pycache__/*.pyc

## 证据（数字 / 命令输出）

备份 15 个、合计 308.4MB；加 .gitignore 后 git status 不再出现备份项

## 沉淀（新增断言 / 案例 / 文档）

无需断言（属工件卫生）
