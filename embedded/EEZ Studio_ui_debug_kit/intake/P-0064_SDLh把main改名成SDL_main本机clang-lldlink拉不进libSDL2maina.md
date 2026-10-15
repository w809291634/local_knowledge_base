# P-0064 · SDL.h 把 main 改名成 SDL_main，本机 clang + lld-link 拉不进 libSDL2main.a

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：链接,SDL2,main符号,SDL_MAIN_HANDLED,lld-link,入口
- **关联提示词**：无

## 现象（看到什么）

解决掉 m.lib/pthread.lib 之后：

```
lld-link: warning: ignoring unknown argument '--undefined=WinMain'
lld-link: error: undefined symbol: main
>>> referenced by msvcrt.lib(exe_main.obj):(int __cdecl invoke_main(void))
clang++: error: linker command failed with exit code 1
```

`main.c` 明明写着 `int main(int argc, char **argv)`，却说找不到 `main`。

## 复现（怎么稳定重现）

仿真入口 `#include "SDL2/SDL.h"` 之后定义 `int main(...)`，且本机是 clang + MSVC 兼容模式 +
`-nostartfiles -nostdlib -fuse-ld=lld`（CMakeCache 实测的链接行）。

## 根因（真正的原因）

`SDL.h` 会 `#define main SDL_main`（SDL2 为 Windows 准备的入口约定）：真正的入口交给
`SDL2main.lib` 的 `WinMain`，它转调 `SDL_main`。
**纯 mingw/gcc 下这套成立**（libSDL2main.a 被正常拉进来，`WinMain` 有引用者）。

本机 clang 走 MSVC 兼容模式 + `-nostartfiles -nostdlib`：启动文件不参与链接、
`--undefined=WinMain` 又被 lld-link 当未知参数忽略（还带 warning），
`libSDL2main.a` 里的 `WinMain` 没人引用 → 拉不进来 → `SDL_main` 落空；
同时 `--dependent-lib=msvcrt` 引进来的 `msvcrt.lib(exe_main.obj)` 需要 `main`
—— 于是报的是 "undefined symbol: main"，而不是 "undefined symbol: SDL_main"
（因为是 `main` 这个符号名字对不上，而不是 `SDL_main` 对不上）。

取证：`llvm-nm CMakeFiles/main.dir/.../main.c.obj` 里只有 `T SDL_main`，**没有** `T main`
（220 个符号里搜 `main` 只搜到字符串常量的 `??_C@_04GHJNJNPO@main?$AA@`）。
`nm` 不在 PATH 上，用 `C:/Program Files/LLVM/bin/llvm-nm.exe`。

## 修复（做了什么）

在仿真入口（sim.py 的 `MAIN_C` 模板）里，include SDL.h **之前**声明 `SDL_MAIN_HANDLED`：

```c
#include "lvgl.h"
/* ★ 必须在 SDL.h 之前定义：SDL.h 会用 #define main SDL_main 把入口改名，
   指望 SDL2main.lib 的 WinMain 转调 SDL_main —— 这在纯 mingw/gcc 下成立，
   本机 clang 走 MSVC/lld-link + -nostartfiles 时 libSDL2main.a 根本拉不进来，
   链接期直接 undefined symbol: main。
   声明 SDL_MAIN_HANDLED 后 SDL.h 不再改 main，入口保持 int main()，CRT 直接找到它。 */
#define SDL_MAIN_HANDLED
#include "SDL2/SDL.h"
```

注意：仿真器自带那份 `main/src/main.c` 也没写 `SDL_MAIN_HANDLED`（它靠 SDL2main 转调），
因为是"引用不改"的源文件，我们没有改它；改的是工程侧入口 `sim_cmake/main.c`。

## 证据（数字 / 命令输出）

- 修复前：`llvm-nm main.c.obj | grep -w main` → 只有 `R ??_C@...main?$AA@`（字符串），无 `T main`；
- 修复后：链接通过，`bin/main.exe` 生成，走路器四条链路全跑通并出图。

## 沉淀（新增断言 / 案例 / 文档）

- 判据（下次再遇到 "undefined symbol: main 但明明定义了"）：先用 `llvm-nm` 看目标文件里
  到底叫 `main` 还是 `SDL_main`（或 `__mainCRTStartup` 之类被宏改名），比读报错快。
- 通用结论：`#define SDL_MAIN_HANDLED` 是自建 SDL 入口（尤其要自己接管 stdin/退出码/
  走路器 `exit`）时的标准做法。
