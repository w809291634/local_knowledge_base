# P-0063 · Windows 端 clang + lld-link 的三个 POSIX 假设：unistd.h / m / pthread

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：链接,clang,MinGW,unistd,libm,libpthread,移植
- **关联提示词**：无

## 现象（看到什么）

按顺序连着报三条（每条都看着跟上一条无关）：

```
design/sim_cmake/main.c:6:10: fatal error: 'unistd.h' file not found
lld-link: error: could not open 'm.lib': no such file or directory
lld-link: error: could not open 'pthread.lib': no such file or directory
```

## 复现（怎么稳定重现）

本机工具链（CMakeCache 实测）：`CMAKE_C_COMPILER=C:/Program Files/LLVM/bin/clang.exe`、
`CMAKE_CXX_COMPILER=.../clang++.exe`，生成器 MinGW Makefiles、链接器 lld-link ——
即 **clang 在 MSVC 兼容模式下**跑（编译期吃的是 MSVC 的 vcruntime.h/ucrt 头，
链接期吃 msvcrt.lib + lld）。`mingw32-make` 只当 make 用。

只要哪儿写了 POSIX 假设就现形。

## 根因（真正的原因）

三条都是"在 mingw/gcc 下成立、在 clang+MSVC 运行时下不成立"的写法：

1. `#include <unistd.h>`：MinGW/MinGW-w64 就算有 unistd.h，本机 clang 的 include 路径
   又排在 MSVC SDK 前面时未必找得到；入口实际只用到一个 `usleep`。
2. `target_link_libraries(main ... m pthread)`：`m` / `pthread` 会被翻译成
   `m.lib` / `pthread.lib` 传给 lld-link，Windows 上根本不存在这两个库。

## 修复（做了什么）

1. 仿真入口（sim.py 的 `MAIN_C` 模板）加兜底，不要 include unistd.h：

```c
/* MinGW/Windows 没有 unistd.h；入口只用得到 usleep，用 Sleep 兜底 */
#ifdef _WIN32
#include <windows.h>
#define usleep(us) Sleep((DWORD)(((us) + 999) / 1000))
#else
#include <unistd.h>
#endif
```

2. 链接库按平台拆开：

```cmake
if(WIN32)
    target_link_libraries(main lvgl ${SDL2_LIBRARIES})
else()
    target_link_libraries(main lvgl ${SDL2_LIBRARIES} m pthread)
endif()
```

## 证据（数字 / 命令输出）

- 改完 unisth 那处，编译期 0 error（只剩 deprecation 警告）；
- 改完链接库处，`could not open 'm.lib'/'pthread.lib'` 消失，进入下一阶段；
- 最终 `bin/main.exe` 生成，四条走路链路（pwd / wifi / wifi_ok / wifi_retry）全跑通。

## 沉淀（新增断言 / 案例 / 文档）

- 以后往仿真入口塞新的 POSIX 调用前先问一句：Windows 上有 equivalents 吗？
  （sleep/usleep → Sleep；fork/pipe → 别用；pthread → std::thread）
- 排查顺序：链接期报 "could not open X.lib" = 有人在 CMakeLists 或源码里写了 Unix 库名。
