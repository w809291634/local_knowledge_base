# P-0017 · compare.py 在本机无 PIL 导致 G5 无法运行（受管 venv 未装 Pillow）

- **工程**：小艺 · 智能屏 8
- **日期**：2026-09-27
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：G5,依赖,PIL,venv
- **关联提示词**：PR-0031

## 现象（看到什么）

跑 design/compare.py 直接 ModuleNotFoundError: No module named 'PIL'；受管 Python 3.13 与系统 Python 3.10 都未装 Pillow，G5 闸门长期处于「没跑过」状态

## 复现（怎么稳定重现）

C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe design/compare.py → ImportError

## 根因（真正的原因）

compare.py 依赖 Pillow 做 2 倍降采样与逐像素差；受管环境刻意保持最小化，未预装 Pillow；且 compare.py 无「缺依赖」友好提示，直接崩在 import

## 修复（做了什么）

在受管 venv（/binaries/python/envs/default）里 pip install Pillow 12.3.0，并用该 venv 的 python.exe 跑 compare.py；venv 路径已写进 ui_debug_kit.config.json 的 binaries.python

## 证据（数字 / 命令输出）

compare.py 输出：11 屏全部对照，平均明显差异 8.14%（阈值 25%），无缺屏，退出码 0；run_gate.py 三级 G1/G4/G5 全 PASS

## 沉淀（新增断言 / 案例 / 文档）

配置 binaries.python 已指向带 PIL 的 venv；PLAYBOOK 出图链路可复用
