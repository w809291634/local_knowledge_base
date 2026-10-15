# P-0077 配置区归位：需要配置的在顶上，非配置项下移到用点，注释缩到行尾

- 日期：2026-10-02
- 对象：PC_SIM 根 CMakeLists.txt（仿真器唯一对外适配文件）
- 上游：P-0076（最简外科手术 240 行骨架 + 6 处手术）

## 1. 用户在意什么

> 「应该改正这样，需要配置的放在上面，不需要配置的放在下面，同时注释简短一点」

P-0076 定案后的配置区是：3 行头注释 + 8 项 set 混在
5 行「配置项说明」+ 7 行「目标工程目录树」注释中间 —— **注释比代码还长**，
要换工程的人第 1 眼找不到那行 `set(TARGET_PROJ_DIR ...)`。

目标形态（用户点名的顺序，逐字落地）：

```
set(TARGET_PROJ_DIR "D:/.../p4_touch_lcd4_3_exp/lvgl_demo_ai/eez-test")            # 目标工程根，其余路径都跟它拼
set(APL_LVGL_DIR     "D:/.../common/APL/apl_lvgl_v9_4")                             # LVGL 内核全路径（手填，不做自动查找）
set(LVGL_CONF_FILE   "${TARGET_PROJ_DIR}/design/sim_cmake/lv_conf.h")               # 仿真专用 lv_conf.h
set(SIM_H_RES 800)                                                                   # 仿真窗口宽 = 实际 LCD 宽
set(SIM_V_RES 480)                                                                   # 仿真窗口高 = 实际 LCD 高
set(UI_DIR       "${TARGET_PROJ_DIR}/src/ui")                                        # EEZ 生成代码（平铺 .c/.cpp）
set(NATIVE_DIR   "${TARGET_PROJ_DIR}/src/native")                                    # 用户逻辑（排除 io_esp / test_native）
set(SIM_MAIN_DIR "${TARGET_PROJ_DIR}/design/sim_cmake")                              # 仿真入口 main.c + lv_conf.h
```

## 2. 改法：配置区只留 8 项，其余下移到「自己的用点旁」

| 下移的东西 | 挪到哪 | 理由压成几行 |
|---|---|---|
| `LV_BUILD_CONF_DIR ""` / `LV_BUILD_CONF_PATH` / `LV_CONF_PATH` | `set(APL_LVGL_DIR ... CACHE)` 之后、**`add_subdirectory(${APL_LVGL_DIR})` 之前** | apl_lvgl 是子作用域，普通变量传不进去 → 必须 CACHE，否则回落自带 lv_conf（ThorVG=1，PC 编不过）；`_DIR` 置空否则 FATAL（P-0066） |
| `set(CONFIG_LV_USE_THORVG_INTERNAL OFF CACHE BOOL ...)` | ThorVG 源文件屏蔽块前 | 内核里它是 `option()` 默认 **ON**，与 lv_conf.h 里的 `0` 无关（P-0076） |

293 → **273 行**；配置区 21 行 → **12 行**（3 行头注释 + 8 项 + 收尾分隔）。

## 3. ★ 坑：纯「整理」也能改坏语义 —— 赋值时机

第一版我把 `CONFIG_LV_USE_THORVG_INTERNAL OFF` 放在 **屏蔽块**，而屏蔽块在
`add_subdirectory(${APL_LVGL_DIR})` **之后**（屏蔽的是 `lvgl` target 的 SOURCES）。
此时内核的 `option()` 早已执行完 → 开关对内核**没用**。已挪回 `add_subdirectory` 之前。

**铁律**：凡是要**影响 add_subdirectory 里那个内核**的赋值（option / CACHE 布尔 /
任何 `set` 给内核读的开关），**必须写在 `add_subdirectory(...)` 语句之前**；
整理代码顺序时，把这类赋值「往下挪到用点旁」是安全的，挪到内核引用点之后就失效，
而且**不会报错、只是静默失效**。

自检手法（本次用上）：挪完立刻重跑 configure 看自证四连 + CACHE 值：

```
-- Using configuration: <工程>/design/sim_cmake/lv_conf.h
-- [sim] 屏蔽 ThorVG/vg_lite 源码 49 个
-- [sim]   窗口=800x480  内核=.../apl_lvgl_v9_4
CACHE: CONFIG_LV_USE_THORVG_INTERNAL:BOOL=0
```
（`SIM_H_RES`/`SIM_V_RES`/`TARGET_PROJ_DIR` **不在 CACHE** 才对 —— 它们是普通 set，
命令行 `-D` 压不动，这是 P-0076 要的效果。）

## 4. 配套检查：脚本兜底写回不会吃掉行尾注释

`sim.py:read_target_proj_dir()` 用正则
`'set\s*\(\s*TARGET_PROJ_DIR\s+"([^"]*)"'` 定位后**只替换 `m.start()..m.end()`**，
闭引号之后的行尾注释原样保留 → 新形态（行尾带中文注释）安全，脚本不用改。

## 5. 附：一条既有小瑕疵的取证手法（别误判成新引入）

现象：出图末尾 `can't open file for write !`，且
`07b_wifi_popup_open.raw` / `09_network.raw` **没有对应 .png**。
取证：`ls -l` 看字节数 → 1536016 vs 800×480×4 = 1536000，**多 16 字节 = PNG 文件头**，
说明 C 侧这两张走了 stb-image-write 的 PNG 写盘、fopen 失败只落了 16B 头残片。

→ **判据升级**：验证出图别只数 `.png` 个数，要核 `.raw` 字节数是否等于
`W*H*4`；`.raw` 比预期多 16B 就是「写成了 PNG 但没写全」。

## 6. 验证

- 全新环境（先 `mv bin/main.exe` 再 `mv build`）：全量编译 **1m58s 通过**（与改动前同耗时）
- onClick 冒烟全绿；出图 15/11；`--walk=wifi_ok` 3 图，目检 `12_ok.png` 排版正常
- configure 自证四连齐、CACHE 取值符合预期
- 设备侧零改动，`_device_syntax_check.py` 无需重跑（未碰 src/）

## 7. 方法论

1. **注释挂行尾、配置排最顶** —— 「看代码的人第一眼要落到哪一行」比信息完整度更重要；
   长理由压成 1–2 行 + 关联上一轮编号（P-00xx），要查再查。
2. **挪位置 ≠ 无风险**：凡是「给 add_subdirectory 里的子项目读的赋值」，挪动会静默失效；
   整理后必跑一次自证（带数字的 `message` / CACHE 取值），别靠"看着没变"。
3. 行数会变（293→273），但 diff 相对原版骨架仍是小幅（外科手术口径，P-0076）。
