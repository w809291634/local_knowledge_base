# P-0178 · 工程路径含中文，mingw 汇编器写不出 obj；仿真必须镜像到 ASCII 路径

- **工程**：AI临时回话\watch
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：中文路径,mingw,GBK,obj,仿真镜像,退出码假绿

## 现象（看到什么）

`run_sim.bat build`（工程在 `C:\Users\yjt54\Desktop\AI临时回话\watch`）编译到最后字体 .c 时报
`Assembler messages: Fatal error: can't create CMakeFiles/main.dir/.../ui_font_cn76.c.obj: No such file or directory`，
错误行里的中文已变乱码（`AI??ʱ?ػ?`）。configure/LVGL 编译一路正常，栽在含中文的**源文件绝对路径**上。
另：`cmd | tail` 让后台任务显示 rc=0，实际日志末行是 `[run_sim] build FAILED`——判成败只看日志。

## 根因

mingw/as 以 GBK 代码页处理含非 ASCII 的输出 obj 路径（obj 目录名由源绝对路径派生），
路径转码后目录不存在 → 写不出 obj。与 kit 老坑"Git Bash 传参中文乱码"同族，但这次是**编译器自身**。

## 修复

按 NO_FLOW §1.3"仿真拷贝到临时目录、不污染原件"的既有纪律做**ASCII 镜像**：
`design/sim.py` 把 `src/`+`design/sim_cmake/{main.c,lv_conf.h}` 单向同步到
`C:\Users\yjt54\watch_sim\watch`，`SIM_TARGET_PROJ_DIR` 指镜像根再 cmake/ninja 构建；
exe 仍在 PC_SIM\bin。真源永远在中文路径工程内，镜像可随手重建。

## 证据

镜像构建后 `[run_sim] build succeeded`；AUTOTEST 出 `[NAV]` 断言与 shot_*.bmp（见工程 tmp/b2）。

## 防再犯

1. 任何 mingw/CMake 工程的**绝对路径必须 ASCII**；工程放中文目录时，仿真/编译一律走镜像。
2. 判构建成败只看日志里的 succeeded/FAILED 行，管道退出码不作数（老坑复现）。

> **更新 2026-10-23**：本工程已迁到纯 ASCII 路径，镜像层撤销改就地构建，见 P-0180；本条规则仍有效（工程根含中文时必须镜像）。
