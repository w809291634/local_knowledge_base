# P-0155 · EEZ 最小模板资源账单：A/B 宏 + 逐对象 diff（含字体/数学库归因）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_template
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,资源消耗,flash,RAM,A/B宏,esp_idf_size,字体归因,数学库,flow引擎,最小工程
- **关联提示词**：PR-0259

## 现象（看到什么）

在新适配的最小 EEZ 模板（lvgl_demo_template：ui 仅 1 屏 1 label，flowSupport=true 但 UI 无 flow 逻辑）上需要量化 EEZ 净消耗，并核实此前 lvgl_demo_ai 口径（P-0154）能否直接套用

## 复现（怎么稳定重现）

main.c 顶部 #define APP_ENABLE_EEZ_UI 1/0 各构建一次（0 组换成裸 LVGL 同界面 1 label）；对两次 map 跑 python -m esp_idf_size --files --format json，逐对象求差

## 根因（真正的原因）

EEZ 代价不是一个数：总差 flash +422714B / RAM +14449B，但其中只有 222006B 归引擎。screens.c 的 字体名 到 指针 表引用了 sdkconfig 启用的全部字号（Montserrat 12~26），0 组无引用被 --gc-sections 丢弃，差值被误算进 EEZ；表达式求值器还连带 libm pow/log 系约 18.5KB、esp_timer system_time 7336B

## 修复（做了什么）

无（对照测量）。口径修正：EEZ 引擎净耗 = eez-flow.cpp.obj 222006B flash + 13921B RAM（含 .eh_frame 31144B）；其余约 200KB 主要是字体资产 163955B 加数学库/时基连带，可通过 sdkconfig 关掉不用字号、或编译切 -Os 压缩

## 证据（数字 / 命令输出）

总 flash 1142430 vs 720244，差 422714；归因：eez-flow.cpp 222006(+13921RAM)、Montserrat 12~26 共 163955、libm pow-log 系约 18500、esp_timer system_time 7336、main.c 2240、杂项约 2500。与 P-0154 的 bss 25.7KB 差异解释：那里 flow 有变量/结构状态，本模板无 flow 逻辑故 13.9KB

## 沉淀（新增断言 / 案例 / 文档）

新增可复用测量法：A/B 编译宏 + esp_idf_size --files JSON 双构建 diff（比 parse_map.py 更直接）；续 P-0154 线程；模板脚手架见 reference/11_minimal_eez_project_scaffold.md

## ★ 口径更正（2026-10-19，见 P-0158）：字体不是 EEZ

原"合计（A/B 总差）+422,714B"把 **Montserrat 字体** 也算进了 EEZ，属口径不严。重做 A/B（同配置）并剥离字体后：

- **EEZ 自身**（引擎 eez-flow.cpp + 生成的 screens/ui + 引擎连带 libm/esp_timer）：
  **131,184B flash + 3,985B RAM**（优化后；优化前约 264KB / 14.8KB）
- **字体**（Montserrat 26/24/22/20/18/16/12）：**164,138B** —— LVGL 资产，**非 EEZ**；
  只因 sdkconfig 开了这 7 档、加上 EEZ 的 `fonts[]` 名字表按名引用，才被拉进固件。原生 LVGL 用同样字号也要付这笔。
- 整机 991,024B = 裸底座 695,712B + EEZ 131,184B + 字体 164,138B。

⇒ 引用本条数字时请注明是否含字体。详见 `P-0158_*.md`。