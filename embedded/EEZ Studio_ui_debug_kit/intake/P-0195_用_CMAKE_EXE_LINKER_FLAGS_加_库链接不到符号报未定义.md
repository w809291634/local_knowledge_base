# P-0195 · 用 CMAKE_EXE_LINKER_FLAGS 加 -l 库链接不到，符号报未定义

- **工程**：app-wifi-scan-conn-no-flow（PC 仿真接 wlanapi）
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：构建,CMake,MinGW,链接顺序,共享脚本不改
- **关联提示词**：PR-0365

## 现象（看到什么）

PC 仿真要调 Windows `wlanapi`（真扫描/真连接）。共享的 `PC_SIM/.../CMakeLists.txt` 里没有
加库的入口，而工程约定是"PC_SIM 与 LVGL 内核源码保持不变"。
第一反应是在工程自己的 `run_sim.bat` 里传 `-DCMAKE_EXE_LINKER_FLAGS=-lwlanapi`——
配置能过，链接期 `undefined reference to WlanOpenHandle/WlanConnect/...`。

## 复现（怎么稳定重现）

`cmake ... -DCMAKE_EXE_LINKER_FLAGS=-lwlanapi` 后构建即复现；
换成 `-DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi` 就链接通过。

## 根因（真正的原因）

CMake 链接命令模板是
`<CMAKE_EXE_LINKER_FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES> <CMAKE_XX_STANDARD_LIBRARIES>`：
`CMAKE_EXE_LINKER_FLAGS` 落在**目标文件之前**，而 GNU ld 从左往右解析、只在此时还没被满足的符号上
才去拉库，所以放在对象前面的 `-l` 等于没放。`*_STANDARD_LIBRARIES` 是专门设计成追加在最后的。

## 修复（做了什么）

`design/sim_cmake/run_sim.bat`（每个示例各有一份，不属于共享件）配置行改成
`-DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi`，并在上方注释写明为什么不能用 `CMAKE_EXE_LINKER_FLAGS`。
共享的 `PC_SIM` CMakeLists 一行未改。

## 证据（数字 / 命令输出）

`[3/3] Linking CXX executable bin\main.exe` + `[run_sim] build succeeded.`；
真接口跑通：`[WIN] WlanConnect 已下发：YJT-1号楼办公`，
系统侧 `netsh wlan show interfaces` 独立回读 `状态: 已连接 / SSID: YJT-1号楼办公 / 通道 36`。

## 沉淀（新增断言 / 案例 / 文档）

工程侧落档：`EEZ_WORKFLOW.md` §5.8、`README.md`「让仿真器走真 WiFi」。
判据：以后给仿真加系统库，只允许动 `run_sim.bat` 的 `*_STANDARD_LIBRARIES`，
判据是"链接行里库名出现在对象文件之后"（`ninja -v` 可反查）。
