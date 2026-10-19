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
