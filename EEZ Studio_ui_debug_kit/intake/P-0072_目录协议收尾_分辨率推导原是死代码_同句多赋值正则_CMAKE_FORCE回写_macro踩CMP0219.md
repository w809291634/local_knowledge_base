# P-0072 目录协议收尾：分辨率"自动推导"原来一直是死代码

日期：2026-10-02   状态：fixed（配套 P-0069 瘦身 / P-0071 目录协议）

## 一、起因：瘦身完发现 diff 又涨回去了

用户抱怨过 `PC_SIM` 根 CMakeLists 改动太大（适配版 +139/−30）。
走完"瘦身 + 注释精简 + 目录协议"后实测 **+157/−28**，比被抱怨的那版还大 ——
等于**瘦身的收益被协议块一口吃回去**。于是回头把协议块本身再压一轮：

| 阶段 | diff | 文件行数 |
|---|---|---|
| 用户抱怨的那版 | +139/−30 | 349 |
| 瘦身（只留最小补丁） | +32/−11 | 271 |
| 加目录协议（未压） | +157/−28 | 369 ❌ |
| **协议块再压（本轮）** | **+133/−28** | **345** ✅ |

压法：① 内核探测删掉 5 个写死版本号候选，只留 `common/APL/apl_lvgl*` 通配
② 协议三段 `UPWARD while` 换成 `foreach` + 等长双列表 ③ 底部 6 行 `[sim]` 自证
message 折成 3 行 ④ 协议文档头从 14 行压到 11 行。**净结果：功能变多（多出自动推导），
文件反而比用户抱怨时更小。**

## 二、压完一验证，连抓四个真 bug（全是"压之前看不出来的"）

### ② `apl_lvgl` 不在工程下面，在往上第 2 层
想省掉 up-walk，改成一次性 `file(GLOB "${TARGET_PROJ_DIR}/common/APL/apl_lvgl*")` →
**直接 FATAL 找不到**。实际布局是：

```
 …/idf_v555_my_exps/            ← apl_lvgl_v9_4 在这一层的 common/APL/
   common/APL/apl_lvgl_v9_4/
   p4_touch_lcd4_3_exp/lvgl_demo_ai/eez-test/   ← TARGET_PROJ_DIR（往下 2 层）
```

`common/APL` 是**工程之上的那层目录**，所以 up-walk 不能省，只能把"5 个写死版本号
候选"压成 `apl_lvgl*` 通配 + 逐级上探。**教训：简化前先量一遍真实布局，别照着
"应该长这样"写。**

### ④ 分辨率推导**从来就没生效过**（最要命的一条）
原来那版：`优先 sim_cmake/lv_conf.h 的 LV_HOR_RES`，读不到再回退
`build_ui.py 的 SCREEN_W`。实测两条都不成立：

- `design/sim_cmake/lv_conf.h`（sim.py 生成）里**根本没有** `LV_HOR_RES/VER_RES`；
- `design/build_ui.py:63` 写的是 **`SCREEN_W, SCREEN_H = 800, 480`**（同句多赋值），
  而正则写的是 `SCREEN_W[ \t]*=[ \t]*([0-9]+)`（要求等号紧跟）→ **永远匹配不上**。

所以 **800×480 一直来自 `set(SIM_H_RES 800 CACHE STRING ...)` 的硬编码默认值**，
所谓"分辨率单一真值源"是假象。**辨别方法：把默认值删掉/改成明显错的，
重新 configure 看 CACHE 里会不会变 —— 不变就是死代码。**

### ④ 修正正则要吃同句多赋值
```cmake
# 匹配 `SCREEN_W, SCREEN_H = 800, 480`，也兼容分开两行写的 `SCREEN_W = 800`
string(REGEX MATCH "SCREEN_W[ \t]*,[ \t]*[A-Za-z_][A-Za-z0-9_]*[ \t]*=[ \t]*([0-9]+)[ \t]*,[ \t]*([0-9]+)" _m "${_t}")
string(REGEX REPLACE ".*=[ \t]*([0-9]+)[ \t]*,[ \t]*([0-9]+)" "\\1" _x "${_m}")   # 800
string(REGEX REPLACE ".*=[ \t]*([0-9]+)[ \t]*,[ \t]*([0-9]+)" "\\2" _y "${_m}")   # 480
```
注意 `SCREEN_H` 不能用"等号后第一个数"取 —— 同句里它后面跟的是 `800`
（`SCREEN_H = 800, 480`），必须用**第 2 个捕获组**，否则宽高会反/撞车。

### ④ 推导值必须 `CACHE ... FORCE` 写回
```cmake
set(SIM_H_RES "${_x}" CACHE STRING "..." FORCE)   # 对，FORCE 必需
set(SIM_H_RES "${_x}")                            # 错：只是同名普通变量，
#                                                   CACHE 里仍是空，编译宏拿到空值
```
`target_compile_definitions(main PRIVATE SIM_H_RES=${SIM_H_RES})` 读的是 CACHE 值，
普通同名变量它看不见。这条和 P-0066（apl_lvgl 子作用域只读得到 CACHE）是同一类问题。

### _tmp：`macro()` 抠数字 → CMP0219 + 语法错
压行数时试过用 `macro(_grab _txt _k _out)` 复用 4 段重复正则，结果两个问题：
- `CMake Warning (policy) CMP0219`：macro 调用会保留参数里的反斜杠（宏体里的 `"\\1"`），
  老 policy 下报警告；
- 更要命：宏体里 `"${_txt}"` 展开时被**当成源文件内容塞进字符串字面量**，
  CMake 报 `Syntax error ... when parsing string` 并吐出整篇 `build_ui.py`。

**结论：CMake 里别为了少写几行把正则逻辑塞进 macro，就地展开 + 注释说明才是可维护的。**
（"少写几行"换了 2 个 policy/语法坑，不划算）

## 三、验证清单（本轮）

1. 单独 configure（`cmake -C <sim_init.cmake>`）→ EXIT=0，三条 `[sim] ...` 自证齐全；
   `CMakeCache` 里 `APL_LVGL_DIR` 自动命中 `apl_lvgl_v9_4`、
   `SIM_H_RES/SIM_V_RES` 由 build_ui.py 推出（不再是默认值）；
2. 删 `build/` + `bin/main.exe` 造全新环境 → `sim.py --walk=pwd` 全量编译 EXIT=0；
3. `sim.py --walk=wifi_ok` 回归；
4. `design/_device_syntax_check.py` 绿（本轮没动真机源码）。

## 四、可复用检查表

- **任何"自动推导"写完，先删掉默认值再 configure 一次**，看 CACHE 会不会变
  —— 不变就是死代码（本次就靠这招抓出来）。
- **动 CMake 前先量真实布局**（`find/ls` 看目录到底在哪），别按"应该长这样"写。
- **瘦身目标要量化**：`git diff --stat` 每次改完都量一遍，别让新功能悄悄吃掉收益。
- CMake CACHE 相关一律 `set(X "${X}" CACHE ...)`；**推导出来的值要覆盖已有 CACHE 必须 FORCE**。
