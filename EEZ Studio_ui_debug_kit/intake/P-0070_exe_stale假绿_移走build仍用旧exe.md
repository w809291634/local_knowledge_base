# P-0070 · 瘦身验证的「假绿」：`exe_stale()` 跳过编译，跑的还是瘦身前那份旧 exe

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真器 lv_port_pc_vscode_v9.5
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：仿真验证,增量编译,exe_stale,假绿,旧副本,验证纪律
- **关联提示词**：（未对应，该轮提示词未进 PROMPT_LOG）

> 补档说明（2026-10-03）：正文按 `index.md` 的 P-0070 行 +
> 工程日志 `.workbuddy/memory/2026-10-02.md`「第 84 轮｜PC_SIM 根 CMakeLists 瘦身」
> 的「验证（新增纪律）」段回填（该段第 304-305 行明确写「intake 新增 … P-0070」）。

## 现象（看到什么）

给 PC_SIM 根 `CMakeLists.txt` 做完瘦身（`git diff` 从 **+139/−30（240→349 行）** 降到
**+32/−11（271 行）**）之后跑验证，**3 秒就"跑通"了** —— 看着像"改完没坏"。
实际上那次跑的是**瘦身前那份旧 exe**，瘦身后的 CMakeLists **一次都没被编译验证过**。
同一轮还出现：首次 `make -j12` 在 **4%** 报 `Error 2` 且**零错误行**（子进程被掐）。

## 复现（怎么稳定重现）

1. 改 PC_SIM 根 `CMakeLists.txt`（这类改动不碰 `src/native`、也不碰 `sim_cmake/main.c`）；
2. 把 `build/` 目录移走（本轮临时改名 `build_prev_slim`）；
3. 跑 `python design/sim.py --walk=...` —— `exe_stale()` 判「工程源码不比 exe 新」
   → **直接跳过编译** → 走路用的是旧 exe，3 秒返回"成功"。

## 根因（真正的原因）

`exe_stale()` 的判定输入只有**工程侧源码的 mtime**（第 82 轮定的口径：比 `src/native`
与 `design/sim_cmake/main.c` 的新旧），**`build/` 目录不在它的输入里** → 移走 build 不会
让 exe 失效；而「换 CMakeLists / 换构建配置」本来就不改那两个文件的 mtime。
于是"增量判据"和"真正决定构建产物的东西"不是同一批输入 —— 假绿。
**为什么以前没发现**：同一个病灶在 P-0057 已经爆过一次（快捷入口只判 exe 是否存在 →
排查被旧日志骗），那次修的是"副本没同步"，这次是"增量判据没覆盖构建配置"，
**换了个触发方式复发**（本轮日志原话：「P-0057 同类坑换个触发方式」）。

## 修复（做了什么）

验证仿真器/构建改动的**强制纪律**（不再依赖 `exe_stale()` 的自动判断）：

1. 先 `rm` / `mv bin/main.exe` **强制重编**，再跑走路/冒烟；
2. 或者显式看 configure 期的 `[sim] LVGL 配置来源 = ...` **自证行**，确认新配置真被读到；
3. 「编译过没过」以看到 `[100%] Built target main` 为准，不以"没报错 / 退出得快"为准。

## 证据（数字 / 命令输出）

- 假绿本体：3 秒"跑通" vs 全量编译实际耗时 **3m54s（EXIT=0）** —— 时间差就是证据。
- 同轮记录的两处偶发：首次 `make -j12` 在 **4%** 报 `Error 2`、**零错误行**（子进程被掐），
  重跑 `EXIT=0` ⇒ 判为偶发，但据此立了「看到 `[100%] Built target main` 才算真过」的规矩。
- 同轮真正过了一次的自证：`build/CMakeCache.txt` **8 项注入全部命中**
  （UI/NATIVE/SIM_MAIN_DIR、apl_lvgl_v9_4、800×480、LV_BUILD_CONF_PATH=LV_CONF_PATH→工程
  lv_conf、LV_BUILD_CONF_DIR 空）+ `--walk=pwd` 2 图 / `--walk=wifi_ok` 3 图 +
  `_device_syntax_check.py` 四文件 0 错 0 警。
- 噪音排除：走路日志里的 `can't open file for write !` 在 exe 与 LVGL 源码里都 grep 不到
  （SDL 运行库），与本轮无关，未深挖。
- 遗留物：旧 `build/` 改名 `build_prev_slim` **留着未删**（构建产物，等用户处置）。

## 沉淀（新增断言 / 案例 / 文档）

- ★ **验证仿真器改动 = 先 `mv bin/main.exe` 再 `mv build`**（已上升为长期约定，
  见 MEMORY.md「仿真 / 验收」段），CACHE 默认值只在首次 configure 落盘，更要全新构建树。
- ★ **"跑得快"是假绿的头号信号**：增量判据的输入集必须覆盖"能改变产物的所有东西"
  （CMakeLists / 缓存 / 配置注入），否则就手动破环。
- 同型链条：P-0057（旧副本假绿）→ P-0061（`build()` 每次全量 re-configure）→
  **P-0070（本条）**。日志第 86 轮（P-0073）验证段原话「照 P-0070 教训先造全新环境」、
  第 87 轮（P-0074）验证段原话「P-0057/0070 防假绿：先 mv bin/main.exe 再 mv build」。
- 可加断言（本次未加）：`sim.py` 里把"根 CMakeLists 与 CACHE 内容指纹"纳入 stale 判定。
