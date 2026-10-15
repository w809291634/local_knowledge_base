# P-0075 · 仿真配置项改为「手动指定」，删掉分辨率的两段正则查找

- 日期：2026-10-03（记忆记 2026-10-02 夜）
- 状态：fixed
- 领域：PC 仿真 / CMake 适配层 / 可维护性

## 用户诉求（原话）

> `set(SIM_H_RES "" ...)` `set(SIM_V_RES "" ...)` 这里 SIM_H_RES SIM_V_RES 也可以通过
> 配置，不需要自动查找，太麻烦了，你看看还有其他的，可以一样我们手动指定

**要点**：用户不要"留空 → 回去 build_ui.py / lv_conf.h 里正则找"这种魔法；要**配置区
一眼能看见、手改就生效**。并授权我把同类项一并收进配置区。

## 改前：4 处在「自动查找」

| 项 | 位置 | 自动行为 | 行数 |
|---|---|---|---|
| 三目录 UI_DIR/NATIVE_DIR/SIM_MAIN_DIR | ① | 留空则 `<TARGET_PROJ_DIR>/<sub>` 拼路径 + FATAL 校验 | ~20 |
| 内核 APL_LVGL_DIR | ② | 留空则逐级 up-walk 找 `common/APL/apl_lvgl*` | ~25 |
| lv_conf.h | ④ | `SIM_MAIN_DIR/lv_conf.h` 优先，`UI_DIR/lv_conf.h` 兜底 | ~10 |
| **分辨率** | ⑤ | 先正则读 `build_ui.py` 的 `SCREEN_W, SCREEN_H = 800, 480`，再正则读 lv_conf.h 的 `LV_HOR_RES/LV_VER_RES` | **~36** |

## 改后：配置区 = 一张显式表（各项都给默认值，不留空去猜）

```cmake
set(TARGET_PROJ_DIR "..." CACHE PATH "★目标工程根（换工程只改这一行）")
set(SIM_H_RES "800" CACHE STRING "★仿真窗口宽（换工程/换屏改这里）")
set(SIM_V_RES "480" CACHE STRING "★仿真窗口高（换工程/换屏改这里）")
set(LVGL_CONF_FILE "${TARGET_PROJ_DIR}/design/sim_cmake/lv_conf.h" CACHE FILEPATH "...")
```

- **⑤ 整段 36 行删光**，⑤ 只剩一行注释 + 一行 `# ====`；三目录仍按 `<proj>/<sub>`
  拼（本来就短），内核 up-walk 保留但已在配置区标注"留空才自动找"。
- 结构声明注释同步：分辨率真值源从 `build_ui.py` 改成"配置区手动指定"。
- 行数 **219 → 192**。

## 验证（防假绿 + 手填真生效）

1. `mv bin/main.exe` + `mv build` 造全新环境 → 全量 sim.py，exe 12:44:21 生成，
   截图 11 屏齐全（含 walk_* 目录）→ `mingw32-make -C build -j8` 增量重跑 grep
   `error:` **0 命中**（首次那次 Error 2 是**并发偶发**，不是本改动引入，重跑即过）。
2. `CMakeCache.txt` 自证：`SIM_H_RES=800` `SIM_V_RES=480` `LVGL_CONF_FILE=<工程>/design/sim_cmake/lv_conf.h`，
   且 `[sim] ... 窗口=800x480` 自证行正常。
3. **手填覆盖验证**（本次重点）：临时构建树
   `cmake -S PC_SIM -B /tmp/reschk -DSIM_H_RES=1024 -DSIM_V_RES=600`，
   自证行打出 `窗口=1024x600`，CACHE 实际 = 1024/600 → 手动指定确实优先于文件默认值。
4. `--walk=wifi_ok` 3 图（07_list / 10_connecting / 12_ok），目检 12_ok.png 排版正常
   （`HomeNet-5G · WPA2 PSK · 已保存` + 已连接 + 192.168.1.23）。
5. `_device_syntax_check.py` 4 文件 0 错 0 警。

## 教训 / 沉淀

- **CACHE 默认值只在首次 configure 落盘**：文件里 `set(X "800" CACHE ...)` 改默认值
  不会覆盖已存在的 CACHE 项。所以"验证新默认值生效"必须 **mv build 全新 configure**；
  反过来这是好事——用户手填的值不会被下次 configure 冲掉（同 P-0074"防脚本盖用户改值"）。
- **"自动查找"要按代价分级**：分辨率（36 行正则 + 踩过 P-0072 同句多赋值坑）必须手填；
  三目录（一行 `if` 拼路径）留着无所谓；内核 up-walk（25 行、手填一长串跨树路径易错）
  保留兜底。不要一刀切删，也别留最痛的那个。
- 删掉正则后 P-0072 那类"同句多赋值匹配不上 / 取错捕获组"的坑**结构性消失**，
  代码面直接变小。
- 与 P-0074 一致：用户要的"简单"= **显式 > 隐式、手填 > 魔法**。
