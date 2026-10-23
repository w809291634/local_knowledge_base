# P-0179 · lv_snapshot_take 恒 NULL：静态内存池装不下大屏快照；另 C 入口调 C++ 导航层要 extern "C"

- **工程**：AI临时回话\watch（PC_SIM ⑤站 B2）
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：snapshot,LV_MEM_SIZE,静态池,extern-C,静默NULL

## 现象
AUTOTEST 逐屏 `lv_snapshot_take()` 全部返回 NULL；分步探针确认死在
`lv_snapshot_create_draw_buf`（屏 466x466 尺寸正常），即 `lv_draw_buf_create` 分配失败。
另：sim main.c(C) 调 watch_nav.cpp(C++) 链接报 `undefined reference to watch_nav_init`。

## 根因
1. lv_conf `LV_MEM_SIZE=1MB` 静态池：466×466×4=869KB 快照缓冲 + 显示缓冲/对象池超池。
   通用模板示例(368x448=660KB)侥幸装得下，**屏越大越会踩**；LV_LOG 的 "No memory" 默认不可见，
   表现为 snapshot 静默 NULL。
2. native 层是 C++，头文件无 `extern "C"` 守卫 ⇒ C 编译单元按 C 符号找 ⇒ mangle 失配。

## 修复
- 仿真 lv_conf：`LV_MEM_SIZE` 1MB→8MB（工程侧偏离模板，注释注明原因）；
- watch_nav.h 加 `#ifdef __cplusplus extern "C"` 守卫；
- 字体补烘写进 sim.py 链路（cli_build 覆盖 src/ui 会删 ui_font_*.c，§3.4 老坑的新受害者形态：
  链接期 undefined ui_font_*）。

## 证据
`[NAV] RESULT: PASS=44 FAIL=0 (rc=0)`；B2 截图 23 张无空屏（tmp/b2/_b2_compare.png）。

## 防再犯
1. 新工程仿真 lv_conf 的 LV_MEM_SIZE 按 `屏宽×屏高×4×2(双缓冲+快照)+对象池` 起算，别抄模板默认。
2. C 入口 + C++ native ⇒ 头文件必带 extern "C" 守卫（新建即加）。
3. sim.py 链路=补烘字体→同步镜像→构建，三段缺一必翻车（已在 design/sim.py 固化）。
