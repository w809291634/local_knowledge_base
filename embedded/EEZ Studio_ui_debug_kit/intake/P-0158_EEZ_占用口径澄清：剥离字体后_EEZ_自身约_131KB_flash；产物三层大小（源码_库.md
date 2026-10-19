# P-0158 · EEZ 占用口径澄清：剥离字体后 EEZ 自身约 131KB flash；产物三层大小（源码/库/固件）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_template
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,占用口径,字体非EEZ,libui.a,调试信息,size-files,flash,RAM,产物大小
- **关联提示词**：PR-0272

## 现象（看到什么）

关于 EEZ 到底占多少出现口径分歧：早前 A/B 总差 +422714B 把 Montserrat 字体也算进了 EEZ；用户指出字体与 EEZ 无关。另需给出 src/ui 各文件占用与生成库 libui.a 的大小。

## 复现（怎么稳定重现）

在当前优化后配置下只切 main.c 的 APP_ENABLE_EEZ_UI 1/0 做 A/B，用 esp_idf_size --files JSON 逐对象 diff；再用 ar tv 看 libui.a 成员、riscv32-esp-elf-strip --strip-debug 看调试信息占比。

## 根因（真正的原因）

A/B 总差里混了三类：① EEZ 独有代码（引擎 + 生成的 screens/ui）② 引擎连带（libm pow/log 约21KB、esp_timer system_time 7.3KB、被 flow 拉入的 LVGL 组件）③ 字体（LVGL 资源，因 sdkconfig 开了 7 档 + EEZ 的 fonts[] 名表按名引用才被拉进来）。字体属内容/资产、不是框架，原生 LVGL 用同样字号也要付。另：.a/.o 磁盘大小远大于固件占用——含 .debug_*（约 98%）、符号表，以及 --gc-sections 会丢弃的未引用函数与数据，故不能用 .a 大小估固件。

## 修复（做了什么）

无（口径澄清 + 度量）。结论：EEZ 自身（剥离字体）= 131184B flash + 3985B RAM；字体 = 164138B（非 EEZ）；裸底座 = 695712B。

## 证据（数字 / 命令输出）

三层大小：① 源码：eez-flow.cpp 369589 + eez-flow.h 160059 + 其余小文件，约 535KB；② 库 libui.a 6007552B（5.73MB），strip-debug 后 2135684B，其中 eez-flow.cpp.obj 5437192→1943972；③ 进固件 libui.a 合计 95408B flash + 3553B RAM（eez-flow 94668/3457、ui.c 396/16、screens.c 336/80、images.c 8/0、styles.c 0）。EEZ-on vs OFF（同配置）总差 flash +295322 / RAM +3985，拆为：字体 +164138、引擎 +94668、ui 其它 +740、引擎连带 +35776。整机 991024B = 底座 695712 + EEZ 131184 + 字体 164138。

## 沉淀（新增断言 / 案例 / 文档）

追加更正段到 P-0155（原文保留）；reference/11_minimal_eez_project_scaffold.md §3.1 补剥离字体口径与库大小不等于固件占用提醒。
