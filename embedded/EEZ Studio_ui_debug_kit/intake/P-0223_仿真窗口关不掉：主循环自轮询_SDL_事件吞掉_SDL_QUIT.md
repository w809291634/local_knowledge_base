# P-0223 · 仿真窗口关不掉：主循环自轮询 SDL 事件，把 SDL_QUIT 吞在鼠标 handler 之前

- **工程**：w78-tabview-smart-home
- **日期**：2026-11-05
- **工具**：Qoder
- **状态**：fixed
- **标签**：仿真,SDL,窗口关闭,LVGL,事件,PC_SIM,过程文件
- **关联提示词**：PR-0502

## 现象（看到什么）

双击 `design/sim_cmake/run_sim.bat` 打开仿真窗口后，点窗口右上角 × 无反应，只能用任务管理器结束。
接着重新构建时报错：`ld.exe: cannot open output file bin\main.exe: Permission denied`
——上一个没关掉的 `main.exe`（PID 44292）还占着 exe。

## 复现（怎么稳定重现）

1. 双击 `run_sim.bat`（不带参数，走窗口模式）；
2. 点窗口关闭按钮 → 窗口不退出；
3. 再跑构建 → 链接 Permission denied。

## 根因（真正的原因）

`design/sim_cmake/main.c` 的主循环自己 `SDL_PollEvent`，并把**每一个**事件都喂给
`lv_sdl_mouse_handler(&e)`：

```c
while (SDL_PollEvent(&e)) lv_sdl_mouse_handler(&e);
```

LVGL 的 SDL 窗口驱动本来会处理关闭：`lv_sdl_window.c` 的刷新回调里判
`SDL_WINDOWEVENT_CLOSE`（删 display）与 `SDL_QUIT`（`SDL_Quit` + `lv_deinit`，
`LV_SDL_DIRECT_EXIT=1` 时直接 `exit(0)`）。但事件已经在我们的循环里被消费，
驱动永远收不到，所以关闭按钮形同虚设；`main.exe` 进程一直活着，锁住 exe。

## 修复（做了什么）

`design/sim_cmake/main.c` 主循环先判关闭事件，再喂鼠标 handler：

```c
while (SDL_PollEvent(&e)) {
    if (e.type == SDL_QUIT ||
            (e.type == SDL_WINDOWEVENT &&
             e.window.event == SDL_WINDOWEVENT_CLOSE)) {
        SDL_Quit();
        return 0;
    }
    lv_sdl_mouse_handler(&e);
}
```

配套：

- `main.c` 新增 `W78_QUIT_TEST=1`：启动后预压一个 `SDL_QUIT`，用来无头自证关闭链路；
- `run_sim.bat` 新增 `quittest` 模式（设 `W78_QUIT_TEST=1` + `SDL_VIDEODRIVER=dummy`）；
- 构建目录从 `design/tmp/sim_build` 改到工程 `tmp/sim_build`（过程件纪律）。

## 证据（数字 / 命令输出）

- `run_sim.bat quittest` → `[QUIT] SDL_QUIT queued` + `QUITTEST PASS`，退出码 0。
- 导航回归 `run_sim.bat test` → `[NAV] 69/69 PASS 全部通过`。
- 修复前构建失败原文：`ld.exe: cannot open output file bin\main.exe: Permission denied`；
  结束 PID 44292 后构建恢复。

## 沉淀（新增断言 / 案例 / 文档）

- NO_FLOW §2.2 的「no-flow 导航接线」段加一条：主循环自轮询 SDL 时必须自己处理
  `SDL_QUIT` / `SDL_WINDOWEVENT_CLOSE`，再喂鼠标 handler。
- CHANGELOG v0.9.97 记录根因与 quittest 入口。
- 只在**手工轮询 SDL** 时踩；不轮询、交给 LVGL 自己的 SDL 定时器那种写法不会出现。
