# P-0057 · PC 仿真只判断「exe 是否存在」→ 改了 `io_pc.cpp` 跑的还是旧副本

- **日期**：2026-10-02（PR-0107）
- **工具**：WorkBuddy + `design/sim.py`（`walk_capture` / `states_capture`）
- **症状**：失败态点「重试」没反应，查了半天日志——日志里那行 `[io_pc] UI picked
  slot 1 (TP-LINK_8890) -> 加密未保存` 是**旧代码**打的（新加的 `wifi retry` 分支
  压根没跑）。查 exe 与副本时间戳才发现：副本 `io_pc.cpp` 停在 08:50，源文件改于
  09:01。
- **根因**：旧写法是
  `if not os.path.isfile(exe): copy_ui(); copy_native(); write_main(); build()`
  —— exe 一旦存在就**永远不同步源码**。`walk_capture` / `states_capture` 都踩。
  这类坑最阴：仿真"验证通过"其实验的是上一次运行的二进制，等于什么都没验。
- **规则**：
  1. 仿真快捷入口（走路 / 钉态截图）**每次都 `copy_native()`**（很便宜）；
  2. 再按「用户代码 / `WORK/main.c` 是否比 exe 新」决定要不要增量编译
     （`sim.py: exe_stale()`）；
  3. 日志里看到行为与代码不符时，**先看副本与 exe 的时间戳**（`ls -la --time-style`），
     这比读代码快。
- **状态**：fixed（两条路径都改成「每次 copy_native + stale 才 build」）
