# P-0067 · SDL 的 `main` 改名：clang(lld-link) 与 mingw(GNU ld) 需求相反，要两边都补

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真器 lv_port_pc_vscode_v9.5
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：链接,SDL2,SDL_main,SDL_MAIN_HANDLED,clang,mingw,双工具链
- **关联提示词**：无

## 现象（看到什么）

同一份入口 `main.c`，换编译器就换一种链接错误：

- **clang + lld-link（MSVC 式，本机 `C:/Program Files/LLVM/bin/clang.exe -nostartfiles -nostdlib -Wl,--undefined=WinMain -fuse-ld=lld`）**：
  `lld-link: undefined symbol: main`（P-0064）——`libSDL2main.a` 拉不进来。
- **mingw gcc 13.1（GNU ld，`find_package(SDL2)` 把 `libSDL2main.a` 一起链进来）**：
  ```
  .../x86_64-w64-mingw32/bin/ld.exe: .../libSDL2main.a(SDL_windows_main.o): in function `main_getcmdline':
  .../SDL2-2.32.4/src/main/windows/SDL_windows_main.c:80: undefined reference to `SDL_main'
  collect2.exe: error: ld returned 1 exit status
  ```
  原因是上一轮 clang 那条路加的 `#define SDL_MAIN_HANDLED` 让入口保持真 `main`，
  却没人提供 mingw 端 `SDL_windows_main.o` 要的 `SDL_main` 符号。

## 复现（怎么稳定重现）

```bash
cmake -S <PC_SIM>/lv_port_pc_vscode_v9.5 -B <空目录> -G "MinGW Makefiles"   # 会落到 mingw gcc
mingw32-make -C <空目录> -j12 main
```

（若 build 目录已有 clang 的 CMakeCache，则走另一条：`python design/sim.py --walk=pwd`。）

## 根因（真正的原因）

`SDL_main.h` 有两个互斥开关：

- **不定义 `SDL_MAIN_HANDLED`**：`main` → 改名成 `SDL_main`，SDL 自己提供 WinMain 去调它。
  适用于 mingw（libSDL2main.a 在，且 SDL 想接管入口）。
- **定义 `SDL_MAIN_HANDLED`**：`main` 保持 `main`，入口归用户/CRT。
  适用于 clang + lld-link + `-nostartfiles`（拉不进 libSDL2main.a）。

P-0064 只解决了前半段（clang），把这一行**无条件写进 main.c**，等到换成 mingw 构建就变成反向的缺符号。
即：这是**按前端而异**的开关，不该写死在源码里。

## 修复（做了什么）

文件：工程侧仿真入口 `design/sim_cmake/main.c`（由 `sim.py` 的 `write_main()` 生成，模板同一处）

保留原有的 `#define SDL_MAIN_HANDLED`（clang 那条路不变），在**真 `main()` 定义之后**补一层转调：

```c
/* 上面定义了 SDL_MAIN_HANDLED，main 不会被改名，入口保持 int main()。
   mingw/GNU 下 find_package(SDL2) 会链进 libSDL2main.a，其中的
   SDL_windows_main.o 会去调 `SDL_main` —— 只有 GNU 前端才需要这个符号。 */
#undef main                       /* ★ 先摘掉宏，否则下面的 main(...) 被二次改名造成自递归 */
int SDL_main(int argc, char **argv) {
    return main(argc, argv);
}
```

- clang/lld 那边不引用 `SDL_main`，这层转调是死代码，无害；
- mingw 那边它正好补上 `SDL_windows_main.o` 的引用；
- `#undef main` 是关键细节：不摘宏时函数体里的 `main` 会变成 `SDL_main`，自己调自己 → 栈溢出。

## 证据（数字 / 命令输出）

| 构建 | 修复前 | 修复后 |
|---|---|---|
| mingw gcc 13.1（临时构建树完整编译） | `undefined reference to SDL_main` + `collect2.exe: ld returned 1`，`BUILD_EXIT=2` | `BUILD_EXIT=0`，产物 `bin/main.exe` 3.98 MB，10:01 |
| clang + lld-link（主构建树） | OK | OK（exe 3.20 MB，10:02，走路 2 张图） |

两条路的 `--walk=pwd` 都出图：密码面板「输入密码 / TP-LINK_8890 / 键盘 4 行按键齐全」目检正常。

## 沉淀（新增断言 / 案例 / 文档）

- 经验：同一份模拟器入口要同时得过 **clang(lld-link)** 与 **mingw(GNU ld)** 两种前端，
  凡是"SDL 接管入口 / 用户接管入口"这类互斥开关，一律**两端都给**（缺哪个补哪个），
  不要写成无条件宏。
- 经验：加这类兜底函数时先 `#undef` 同名宏，否则自递归。
- 未加断言（属链接期，不在 UI 断言范围）。
