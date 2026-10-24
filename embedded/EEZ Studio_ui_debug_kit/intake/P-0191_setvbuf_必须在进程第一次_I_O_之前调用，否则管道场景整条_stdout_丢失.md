# P-0191 · setvbuf 必须在进程第一次 I/O 之前调用，否则管道场景整条 stdout 丢失

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：无头验证,stdout,缓冲,子进程,排查
- **关联提示词**：PR-0361

## 现象（看到什么）

仿真 exe 用 subprocess 以管道捕获 stdout 时只拿到 lv_init 的几行告警，后面所有 [NAV]/[IO] 断言行全丢，rc=0；同一 exe 重定向到文件却正常。

## 复现（怎么稳定重现）

main.c 里 setvbuf(stdout, NULL, _IONBF, 0) 放在 lv_init() 之后即可复现。

## 根因（真正的原因）

LVGL 在 lv_init() 里已经写过 stdout；对已使用过的流再 setvbuf 是 C 未定义行为，MinGW/UCRT 下表现为流被打断——写文件缓冲路径侥幸没事，写管道就整条丢。

## 修复（做了什么）

把 setvbuf 提到 main() 的第一条语句（lv_init 之前），并在注释里写明「必须是本进程第一次 I/O」，防止后人为了整理顺序再挪回去。

## 证据（数字 / 命令输出）

挪前：同一命令 stdout 从 1.6KB（只剩告警）恢复为完整 18 条 [NAV] 行；连跑 5 次 rc 全 0、RESULT 全 17/0。

## 沉淀（新增断言 / 案例 / 文档）

本工程 EEZ_WORKFLOW §5.4 夹具坑清单（第 5 条）
