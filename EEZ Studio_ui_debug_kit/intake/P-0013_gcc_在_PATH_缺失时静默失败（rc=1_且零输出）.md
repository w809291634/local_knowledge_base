# P-0013 · gcc 在 PATH 缺失时静默失败（rc=1 且零输出）

- **工程**：（待补）
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：toolchain,path
- **关联提示词**：（无）

## 现象（看到什么）

仿真器增量编译失败，但 make/gcc 的日志里一条编译错误都没有；手动跑 gcc -c 也 rc=1 且无输出

## 复现（怎么稳定重现）

PATH 里没有 D://Program_Files//mingw64//bin 时执行 gcc -c bad.c -o bad.o（bad.c 内容为非法代码）

## 根因（真正的原因）

gcc 找不到自己的子程序/依赖 DLL（cc1 等），驱动直接退出；Windows 下这类失败不打印任何信息，极易误判成『编译器坏了』

## 修复（做了什么）

编译前把 mingw64\bin 加进 PATH（sim.py 的 env_with_tools 已做；排查时也要记得）

## 证据（数字 / 命令输出）

PATH 含 mingw64\bin：同一文件立刻报出 'bad.c:1:1: error: expected ...'；不含：rc=1 零输出

## 沉淀（新增断言 / 案例 / 文档）

（待补）
