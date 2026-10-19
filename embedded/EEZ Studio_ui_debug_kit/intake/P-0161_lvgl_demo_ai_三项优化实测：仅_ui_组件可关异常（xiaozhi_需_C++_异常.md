# P-0161 · lvgl_demo_ai 三项优化实测：仅 ui 组件可关异常（xiaozhi 需 C++ 异常）；固件 -130.9KB / 内部RAM -20.4KB

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_ai
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,体积优化,-Os,-fno-exceptions,-fno-rtti,执行队列,ui_font 中文字体,分组账单,ui_size_report,xiaozhi
- **关联提示词**：PR-0277

## 现象（看到什么）

把在最小模板上验证过的三项优化（ui -Os / 执行队列 / 关 CXX 异常）套用到 lvgl_demo_ai（大工程，含 xiaozhi），看效果并输出脚本报告。

## 复现（怎么稳定重现）

① ui 组件 target_compile_options(-Os 加 CXX 限定的 -fno-exceptions -fno-rtti)；② executionQueueSize 2000→256（.eez-project 与生成的 eez-flow.h 同步）；③ idf.py build 后跑 tools/ui_size_report.py --project <ai 目录>。

## 根因（真正的原因）

关键约束：本工程不能在 sdkconfig 里全工程关异常 —— xiaozhi 的 C++ 大量使用 throw/try/catch/dynamic_cast（mcp_server.cc 与 .h、lvgl_image.cc、assets.cc），全关会编译失败。故异常只按 target 关在 ui 组件（EEZ 引擎自身无 try/catch）。后果：引擎自己的 .eh_frame 与 EH 相关代码被删掉，但工程级 EH 运行时（libgcc unwind + libstdc++）仍被 xiaozhi 需要，所以 C/C++ 运行时那一组不减 —— 省不到模板上那份额外的 -23.7KB。

## 修复（做了什么）

已落地三项（异常为 ui 作用域）。实测：app bin 5,239,712→5,105,696（-134,016B / -2.6%）；链接后 5,237,213→5,103,134；内部 RAM 335,423→314,495（-20,928B，= 队列(2000-256)×12B，精确吻合）；EEZ 引擎 225.1KB→94.8KB（-130.3KB）。

## 证据（数字 / 命令输出）

分组（优化前→优化后）：EEZ 引擎 225.1→94.8KB；EEZ 生成 UI 202.9→202.4KB；字体资源 1.70MB→1.70MB（不变）；C/C++ 运行时 232.2→232.2KB（不变，全工程异常仍开）；EEZ 独有 428.0→297.2KB。.flash.text 2.38MB→2.29MB(-91.9KB)；.eh_frame 144.4→113.3KB(-31.1KB)；app 分区占用 62.5%→60.9%。引擎 94.8KB 与最小模板的 94.7KB 几乎相同 ⇒ 引擎成本由框架决定、与 UI 内容量无关。UI 逐文件（后）：ui_font_ya_hei_13 1.28MB、screens.c 125.0KB/RAM4.9KB、eez-flow 94.8KB/RAM5.9KB、ui.c 52.5KB、54 档 72.5KB、15 档 28.2KB、26 档 26.6KB。

## 沉淀（新增断言 / 案例 / 文档）

新增 P-0161（附前/后两份完整脚本 log）；修正 ui_size_report.py 分组规则（字体规则前置，避免把 libui.a 里 1.28MB 中文字体误算进 EEZ 框架）并同步到 tools/。
---

## ★ 附：ui_size_report.py 完整输出（原样 log，未做摘要）

> 均为 `python ui_size_report.py --project <lvgl_demo_ai>` 的逐字输出。
> 优化 = ui 组件加 -Os + CXX 限定 -fno-exceptions/-fno-rtti；执行队列 2000→256。

### A) 优化前（构建 2026-10-17，bin 5,239,712）

```text
==============================================================================
 固件资源占用报告  [lvgl_demo_v9]     ui_size_report v2 (size tool only; no map guessing)
==============================================================================

[1] 固件总体 (app .bin)
    app .bin (烧写大小) : 5.00 MB (5,239,712 B)
    app 分区            : 8.00 MB (8,388,608 B)  已用 62.5%, 余 37.5%
    链接后进固件合计    : 4.99 MB (5,237,213 B)
    内部 RAM (bss+data) : 327.6 KB (335,423 B)

[2] flash 按分组            (单位: KB, 1 KB = 1024 B)
    分组                                             flash    占比
    --------------------------------------------------------------
    EEZ 引擎 (eez-flow.cpp)                       225.1 KB    4.4%
    EEZ 生成 UI (screens/ui/styles/images)        202.9 KB    4.0%
    字体资源 (Montserrat)                          1.70 MB   33.9%
    字体渲染/加载 (LVGL font engine)                2.9 KB    0.1%
    LVGL 内核                                     298.7 KB    5.8%
    显示/触摸/适配 (ST7701/GT911/adapter)         106.5 KB    2.1%
    本项目组件 (main/board/dsi/native/console)    334.1 KB    6.5%
    C/C++ 运行时 (libm/libc/libstdc++)            232.2 KB    4.5%
    IDF 内核 (FreeRTOS/heap/log/...)              404.9 KB    7.9%
    其它 (其它 IDF 组件 / managed 库)              1.53 MB   30.7%
    --------------------------------------------------------------
    合计                                           4.99 MB  100.0%

[2b] 重点两项（区分「EEZ 框架」与「字体资源」，别混算）
    EEZ 独有代码 (引擎 + 生成 UI)   : 428.0 KB (438,281 B)
    字体相关 (资源 + 渲染引擎)      : 1.70 MB (1,780,430 B)   <- 字体资源不属于 EEZ；原生 LVGL 同样要付

[3] EEZ UI 组件逐文件 (eez-test/src/ui)     (单位: KB)
    文件                             flash       RAM
    ------------------------------------------------
    ui_font_ya_hei_consolas_hybrid_13.c.obj   1.28 MB       0 B
    eez-flow.cpp.obj              225.1 KB   26.3 KB
    screens.c.obj                 125.6 KB    4.9 KB
    ui_font_ya_hei_consolas_hybrid_54.c.obj   72.5 KB       0 B
    ui.c.obj                       52.5 KB    1.3 KB
    ui_font_ya_hei_consolas_hybrid_15.c.obj   28.2 KB       0 B
    ui_font_ya_hei_consolas_hybrid_26.c.obj   26.6 KB       0 B
    ui_font_ya_hei_consolas_hybrid_11.c.obj   24.9 KB       0 B
    ui_image_np_disc.c.obj         24.8 KB       0 B
    ui_font_ya_hei_consolas_hybrid_16.c.obj   19.4 KB       0 B
    ui_font_ya_hei_consolas_hybrid_22.c.obj   18.1 KB       0 B
    ui_font_ya_hei_consolas_hybrid_19.c.obj   17.8 KB       0 B
    ui_font_ya_hei_consolas_hybrid_17.c.obj   17.7 KB       0 B
    ui_font_ya_hei_consolas_hybrid_12.c.obj   14.2 KB       0 B
    ui_font_ya_hei_consolas_hybrid_10.c.obj    8.5 KB       0 B
    images.c.obj                       8 B       0 B
    ------------------------------------------------
    合计                           1.94 MB

[4] 字体明细            (单位: KB)
    lv_font_montserrat_26.c.obj                33.4 KB
    lv_font_montserrat_24.c.obj                29.3 KB
    lv_font_montserrat_22.c.obj                26.1 KB
    lv_font_montserrat_20.c.obj                22.5 KB
    lv_font_montserrat_18.c.obj                19.8 KB
    lv_font_montserrat_16.c.obj                16.8 KB
    lv_font_montserrat_14.c.obj                14.6 KB
    lv_font_montserrat_12.c.obj                12.5 KB
    lv_font_fmt_txt.c.obj                       2.9 KB
    --------------------------------------------------
    合计                                      177.8 KB
    只有 UI 真正用到的字号才需要保留；未用到的可在 sdkconfig 关闭
    (EEZ 的 screens.c 字体表带 #if LV_FONT_MONTSERRAT_xx 保护，关闭不会编译错)

[5] 内部 RAM (DIRAM)
    .dram0.bss  : 50.5 KB (51,753 B)
    .dram0.data : 33.6 KB (34,366 B)
    bss 占用最大的对象:
        25.1 KB  libui.a:eez-flow.cpp.obj
         3.6 KB  libstdc++.a:locale_init.o
         3.1 KB  libfreertos.a:port.c.obj
         2.3 KB  libui.a:screens.c.obj
         1.3 KB  libnative.a:io_esp.cpp.obj
         1.3 KB  liblwip.a:dns.c.obj
          932 B  liblwip.a:nd6.c.obj
          908 B  liblvgl__lvgl.a:lv_init.c.obj

[6] 常驻 flash 的段 (PSRAM XIP 执行/读取)
    .flash.text   (代码)      : 2.38 MB (2,491,570 B)
    .flash.rodata (常量/字体) : 2.27 MB (2,385,445 B)
    .eh_frame     (异常表)    : 144.4 KB (147,876 B)

==============================================================================
 提示: build/.../libui.a 的文件大小(数 MB)含调试信息与符号表，不代表固件占用。
==============================================================================
```

### B) 优化后（三项已落地，bin 5,105,696）

```text
==============================================================================
 固件资源占用报告  [lvgl_demo_v9]     ui_size_report v2 (size tool only; no map guessing)
==============================================================================

[1] 固件总体 (app .bin)
    app .bin (烧写大小) : 4.87 MB (5,105,696 B)
    app 分区            : 8.00 MB (8,388,608 B)  已用 60.9%, 余 39.1%
    链接后进固件合计    : 4.87 MB (5,103,134 B)
    内部 RAM (bss+data) : 307.1 KB (314,495 B)

[2] flash 按分组            (单位: KB, 1 KB = 1024 B)
    分组                                             flash    占比
    --------------------------------------------------------------
    EEZ 引擎 (eez-flow.cpp)                        94.8 KB    1.9%
    EEZ 生成 UI (screens/ui/styles/images)        202.4 KB    4.1%
    字体资源 (Montserrat)                          1.70 MB   34.8%
    字体渲染/加载 (LVGL font engine)                2.9 KB    0.1%
    LVGL 内核                                     298.7 KB    6.0%
    显示/触摸/适配 (ST7701/GT911/adapter)         106.5 KB    2.1%
    本项目组件 (main/board/dsi/native/console)    334.1 KB    6.7%
    C/C++ 运行时 (libm/libc/libstdc++)            232.2 KB    4.7%
    IDF 内核 (FreeRTOS/heap/log/...)              404.9 KB    8.1%
    其它 (其它 IDF 组件 / managed 库)              1.53 MB   31.5%
    --------------------------------------------------------------
    合计                                           4.87 MB  100.0%

[2b] 重点两项（区分「EEZ 框架」与「字体资源」，别混算）
    EEZ 独有代码 (引擎 + 生成 UI)   : 297.2 KB (304,314 B)
    字体相关 (资源 + 渲染引擎)      : 1.70 MB (1,780,430 B)   <- 字体资源不属于 EEZ；原生 LVGL 同样要付

[3] EEZ UI 组件逐文件 (eez-test/src/ui)     (单位: KB)
    文件                             flash       RAM
    ------------------------------------------------
    ui_font_ya_hei_consolas_hybrid_13.c.obj   1.28 MB       0 B
    screens.c.obj                 125.0 KB    4.9 KB
    eez-flow.cpp.obj               94.8 KB    5.9 KB
    ui_font_ya_hei_consolas_hybrid_54.c.obj   72.5 KB       0 B
    ui.c.obj                       52.5 KB    1.3 KB
    ui_font_ya_hei_consolas_hybrid_15.c.obj   28.2 KB       0 B
    ui_font_ya_hei_consolas_hybrid_26.c.obj   26.6 KB       0 B
    ui_font_ya_hei_consolas_hybrid_11.c.obj   24.9 KB       0 B
    ui_image_np_disc.c.obj         24.8 KB       0 B
    ui_font_ya_hei_consolas_hybrid_16.c.obj   19.4 KB       0 B
    ui_font_ya_hei_consolas_hybrid_22.c.obj   18.1 KB       0 B
    ui_font_ya_hei_consolas_hybrid_19.c.obj   17.8 KB       0 B
    ui_font_ya_hei_consolas_hybrid_17.c.obj   17.7 KB       0 B
    ui_font_ya_hei_consolas_hybrid_12.c.obj   14.2 KB       0 B
    ui_font_ya_hei_consolas_hybrid_10.c.obj    8.5 KB       0 B
    images.c.obj                       8 B       0 B
    ------------------------------------------------
    合计                           1.81 MB

[4] 字体明细            (单位: KB)
    lv_font_montserrat_26.c.obj                33.4 KB
    lv_font_montserrat_24.c.obj                29.3 KB
    lv_font_montserrat_22.c.obj                26.1 KB
    lv_font_montserrat_20.c.obj                22.5 KB
    lv_font_montserrat_18.c.obj                19.8 KB
    lv_font_montserrat_16.c.obj                16.8 KB
    lv_font_montserrat_14.c.obj                14.6 KB
    lv_font_montserrat_12.c.obj                12.5 KB
    lv_font_fmt_txt.c.obj                       2.9 KB
    --------------------------------------------------
    合计                                      177.8 KB
    只有 UI 真正用到的字号才需要保留；未用到的可在 sdkconfig 关闭
    (EEZ 的 screens.c 字体表带 #if LV_FONT_MONTSERRAT_xx 保护，关闭不会编译错)

[5] 内部 RAM (DIRAM)
    .dram0.bss  : 30.1 KB (30,825 B)
    .dram0.data : 33.6 KB (34,366 B)
    bss 占用最大的对象:
         4.7 KB  libui.a:eez-flow.cpp.obj
         3.6 KB  libstdc++.a:locale_init.o
         3.1 KB  libfreertos.a:port.c.obj
         2.3 KB  libui.a:screens.c.obj
         1.3 KB  libnative.a:io_esp.cpp.obj
         1.3 KB  liblwip.a:dns.c.obj
          932 B  liblwip.a:nd6.c.obj
          908 B  liblvgl__lvgl.a:lv_init.c.obj

[6] 常驻 flash 的段 (PSRAM XIP 执行/读取)
    .flash.text   (代码)      : 2.29 MB (2,399,706 B)
    .flash.rodata (常量/字体) : 2.27 MB (2,375,046 B)
    .eh_frame     (异常表)    : 113.3 KB (116,060 B)

==============================================================================
 提示: build/.../libui.a 的文件大小(数 MB)含调试信息与符号表，不代表固件占用。
==============================================================================
```
