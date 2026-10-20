# P-0154 · EEZ 资源消耗实测：同构 tabview 下原生 LVGL vs EEZ（RAM/Flash 数据）

- **工程**：EEz_stidio_examples/perf-tabview-native-vs-eez
- **日期**：2026-10-19
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：EEZ,资源消耗,lv_mem_monitor,flash,flow引擎,性能对照,内存
- **关联提示词**：PR-0260

## 现象（看到什么）

需要回答'用 EEZ 比原生 LVGL 多消耗多少资源'，此前无数据

## 复现（怎么稳定重现）

两个独立工程根直连同一 PC_SIM + 同一 lv_conf.h（1MB 内建堆）：native/ 纯 C 建 tabview（tab 栏隐藏+2 Tab×图标块+2 标签），eez/ 用 EEZ 工程生成完全同构 UI；lv_mem_monitor 打点（UI 建成后+3s），size 工具测链接段

## 根因（真正的原因）

EEZ 侧开销构成：flow 引擎代码+assets+screens 胶水（flash text）、flow 运行时状态（堆）

## 修复（做了什么）

无（对照实验）。实测结论：RAM 堆 EEZ 多 ~1.4KB（17840 vs 16416，+9%，frag 双 0）可忽略；flash text 多 ~1.33MB（2787300 vs 1395580）——MCU 主要代价；bss 多 ~20KB；控件越多 EEZ 胶水占比越低且 flow 动态绑定收益越大

## 证据（数字 / 命令输出）

perf-tabview-native-vs-eez/README.md 实测表（size 段数据 + lv_mem_monitor 打点 main_eez.exe/main_native.exe 留存）

## 沉淀（新增断言 / 案例 / 文档）

perf-tabview-native-vs-eez/README.md、根 README 索引、workspace memory 2026-10-19

## ★ MCU 实测更正（2026-10-19，用户 idf 编译 lvgl_demo_ai 后 map 拆分）

PC 推算的"EEZ 多 1.33MB flash"是**误读**：把字体/资源内容算进了框架。真机 map
（lvgl_demo_v9.map，按组件/成员分桶，parse_map.py）实测：

- **EEZ 框架底价 = eez-flow.cpp 本体 205,771B flash（≈206KB）+ 25,705B RAM-bss**
  （bss 全在 flow 引擎，PC 堆测的 1.4KB 只是运行时增量）。
- EEZ ui 组件合计 2.02MB flash，但其中 **1.34MB 是 13px 中文字体（GB2312 全量）**、
  ~0.21MB 其余字体档——**字体才是 flash 大头，与 EEZ/原生无关**；
  screens.c（几十屏 UI 代码）139KB、ui.c 54KB。
- LVGL 内核（managed lvgl__lvgl，-Os）仅 402KB；整机 flash 5.0MB（含 xiaozhi），
  16MB 板余量充足；RAM bss 合计 48KB（P4 768KB SRAM 无压力）。
- 工具：perf-tabview-native-vs-eez/parse_map.py（map 按组件/成员分桶，可复用）。
- 教训：**评框架资源必须按 map 成员拆分**，字体/位图等"内容"别算到框架头上。

## ★★ 二次更正：EEZ 核心"独有"空间的公平账单（section 级，2026-10-19）

用户指出：**屏幕 UI 创建代码原生方案同样要写**，screens.c（139KB）不该算 EEZ 头上。
按 section 级拆分（lvgl_demo_v9.map）重新记账——**只列原生不需要、纯因 EEZ 而存在**：

| EEZ 独有项 | flash | RAM |
|---|---|---|
| flow 引擎代码（eez-flow.cpp .flash.text） | 186,108 | — |
| flow 引擎常量（.flash.rodata） | 18,419 | — |
| assets 二进制+常量表（ui.c .flash.rodata 主体） | ≈52,376 | — |
| flow 引擎静态表（.dram0.bss） | — | 25,701 |
| .data 初值（两文件） | ≈2,456 | ≈2,456 |
| **EEZ 核心独有合计** | **≈259KB** | **≈28KB** |

中性项（原生同样要付）：screens.c 139KB（原生=手写等价创建代码）、字体 7 档 ~1.55MB、
位图 25KB。**最终口径：EEZ 核心代价 ≈259KB flash + 28KB RAM**（P4 可忽略；
1MB flash MCU 要掂量，512KB 以下排除）。教学意义：评框架资源必须
"section 级拆分 + 区分框架独有 vs 内容 vs 两方案共有"三层。

## ★ 三重交叉验证（回应"确定吗"质疑，2026-10-19）

1. map 分桶（组件/成员/section 三层）——本账单数字来源；
2. `.rodata.assets` 符号实测 **0xcc98=52,376B**，与账单 assets 归因精确一致
   （ui.c 的 rodata ≈100% 是 assets 数组）；
3. `size` 直接量 eez-flow.cpp.obj = **284,344B text** > 最终链接 206KB——差值是
   IDF 链接 `--gc-sections` 裁掉的未引用引擎部件；**obj 是上限，map（最终链接）
   才是固件真实占用**。
4. 当前 sdkconfig 为 CONFIG_COMPILER_OPTIMIZATION_PERF(-O2)；切 SIZE(-Os)
   flow 引擎可再缩 15~30%（要压 flash 的开关）。
结论维持：**EEZ 核心独有 ≈259KB flash + ≈28KB RAM**（当前 -O2 配置的实测值）。

## 补充：EEZ 侧滑动运行时验证（假指针 indev 法，2026-10-20）

用户报告"perf 对照的 EEZ 窗口没有动画效果"。用**假指针 indev**（lv_indev_create
+ set_read_cb 脚本化按下/移动/抬起——走真实输入管线，不动真鼠标）无头验证：
EEZ 侧 tabview 拖动**完全正常**（scroll_x=480 翻页、39 次 SCROLL、frag 0）。
P-0150 的 SNAPPABLE 修复运行时有效。窗口"静止"是因为两侧 tab 栏都隐藏
（perf 同构要求），页间切换唯一方式是拖动，无自动轮播。
方法沉淀：**无头输入注入 = 假 indev + lv_indev_set_read_cb 脚本化状态机**，
比 SendInput 干净（不抢鼠标、可自动化、可断言），已在 perf-eez main.c 落地。
