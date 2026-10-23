# P-0180 · 工程从中文目录迁到 ASCII 路径：撤销仿真镜像层改就地构建，搬迁同时打断硬编码路径与旧 CMakeCache

- **工程**：D:\temp_d\AI_Temporary_Reply\watch（原 C:\Users\yjt54\Desktop\AI临时回话\watch）
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：目录搬迁,ASCII路径,就地构建,镜像撤销,硬编码路径,CMakeCache失效,P-0178翻案

## 现象（看到什么）

工程从 `Desktop\AI临时回话` 整体搬到 `D:\temp_d\AI_Temporary_Reply`（纯 ASCII）后，
上一轮为绕 P-0178 建的 ASCII 镜像链（`design/sim.py` 同步到 `C:\Users\yjt54\watch_sim` 再构建）
前提不再成立；而 `run_sim.bat` 里 `set "PROJ_DIR=...AI临时回话\watch"` 是硬编码旧路径，
用户双击必然"找不到 sim.py"。工程内还残留上一轮就地构建失败的 `design/sim_cmake/build_rel/`
（6.1MB，CMakeCache 里全是已消失的旧绝对路径），一旦被复用就重现 "can't create ...obj" 假故障。

## 根因

1. P-0178 的镜像只是**中文路径的条件补丁**，不是仿真构建的固有形态；PC_SIM 的 CMakeLists 只认
   `SIM_TARGET_PROJ_DIR`，指哪都能编。
2. 搬迁同时打断三样：脚本内硬编码绝对路径、CMake 缓存里的路径、工作区级索引文件
   （旧根 `AGENTS.md` 未随工程走，七步口径只剩 NO_FLOW.md 一份真值）。与 P-0177 同族。

## 修复

- `design/sim.py`：删掉 `MIRROR`/`sync()`，改为 `SIM_TARGET_PROJ_DIR=工程根` + 构建目录
  `design/sim_cmake/build_rel/`（gitignore）；`do_build.bat` 生成物挪进工程 `tmp/`；
  新增两道守卫——`check_ascii_path()`（工程根含非 ASCII 直接退出并指回 P-0178）与
  `wipe_stale_cache()`（缓存的 CMAKE_CACHEFILE_DIR 与当前构建目录不符就整删重建）。
- `run_sim.bat`：`PROJ_DIR` 重指新路径，头注释与 echo 横幅按就地链路口径改写（pause 分支不变）。
- 删掉工程内失效的旧 `build_rel/`，全量重编。
- NO_FLOW §1.3 仿真条改为"默认就地构建，仅非 ASCII 根才镜像"。

## 证据

就地构建 `[100%] Built target main`，`tmp/sim_build.log` 链接行为
`Linking CXX executable ...PC_SIM\lv_port_pc_vscode_v9.5\bin\main.exe`（10:42，4.8MB）；
`sim_run.py` 复跑 `[NAV] RESULT: PASS=44 / FAIL=0`（45 条断言 0 FAIL），B2 截图 23 张无空屏；
双击壳 `run_sim.bat build` rc=0 且日志同上。构建目录 36MB 全在工程内并被 gitignore 覆盖。

## 防再犯

1. 工程内一切脚本用 `ROOT` 相对定位；出现绝对工程根（`PROJ_DIR` 这类）必须与 `sim.py` 同目录口径，
   搬迁后先 `grep` 旧路径扫全库。
2. 镜像/沙箱只是**路径条件的补丁**；条件消失要主动撤销，别把绕路当常态留着。
3. 构建目录搬迁后先清 CMakeCache（或写守卫自动清），别信" configure 过了就没事"。
4. 工作区级 AGENTS.md/README 索引跟着工程走；搬完核对一遍索引是否还在。

## 附：本轮顺带抓到的静默丢档风险（字体）

`tools/eez_font_bake.py::bake()` 每次调用**先 `shutil.rmtree(out_dir)` 再重写**（第 362 行），且 `manifest.json` 是最后一个落盘件。
后果：烘焙进行中去读字体目录，看到的就是"少一档 + 没 manifest"的半成品（本轮就这样误报过一次 `git status` 显示 `ui_font_cn76.c` 被删）；
若烘焙进程中途死掉，工程字体池直接残缺。已在 `design/sim.py` 加门禁：打印的 OK 档位数必须等于盘上 `ui_font_*.c` 个数，不等即退。
打桩反向测试：11/11 放行、11/10 拦截、10/10 放行均符；注意"**伪造一个多余 .c 再跑**"这种测法无效——它会被 rmtree 先清掉。
