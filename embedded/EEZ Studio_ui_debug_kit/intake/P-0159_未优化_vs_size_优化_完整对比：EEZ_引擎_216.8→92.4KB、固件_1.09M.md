# P-0159 · 未优化 vs size 优化 完整对比：EEZ 引擎 216.8→92.4KB、固件 1.09MB→967KB（分组级实测）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_template
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,体积对比,未优化,优化,-Os,执行队列,CXX异常,eh_frame,flash,RAM,分组账单,ui_size_report
- **关联提示词**：PR-0274

## 现象（看到什么）

需要一份「未优化 vs 优化后」的完整对比账（分组级），回答「这几项优化到底省了多少、省在哪」。

## 复现（怎么稳定重现）

同一工程两种配置各构建一次，用 tools/ui_size_report.py 出报告：①未优化 = executionQueueSize 1000 + ui 组件无 -Os + CXX 异常/RTTI 开；②优化后 = queue 128 + ui 组件 -Os + CXX 异常/RTTI 关。

## 根因（真正的原因）

三项优化作用点不同：执行队列 → 引擎静态 bss（每项 12B）；-Os → 引擎代码密度；关 CXX 异常 → 整套 EH 运行时（.eh_frame + libgcc unwind-dw2 + libstdc++ EH/typeinfo 一族）。字体 / LVGL 内核 / 显示驱动 / 本项目组件与这三项无关，故两版完全不变。

## 修复（做了什么）

无（对比记录）。结论：优化后固件 -148.9KB（-13.0%）、内部 RAM -10.6KB；收益 84% 来自 EEZ 引擎本体+异常运行时。

## 证据（数字 / 命令输出）

单位 KB(1KB=1024B)。固件 bin 1,143,488→991,024（-148,464B）；链接后合计 1,142,430→990,092（-152,338B / -13.3%）；内部 RAM(bss+data) 202,224→191,367（-10,857B）。分组 flash（未优化 → 优化后）：EEZ 引擎 216.8→92.4（-124.4KB）；EEZ 生成 UI 0.73→0.72；字体资源 174.9→174.9（不变）；字体渲染 2.9→2.9（不变）；LVGL 内核 296.6→296.6（不变）；显示/触摸 35.1→35.1（不变）；本项目组件 12.3→12.3（不变）；C/C++ 运行时 29.6→5.9（-23.7KB，异常运行时消失）；IDF 内核 206.4→205.8；其它 140.3→140.3（不变）。逐文件：eez-flow.cpp 216.8KB/13.6KB RAM → 92.4KB/3.4KB RAM。段：.flash.text 641.5→540.9；.flash.rodata 260.6→248.7；.eh_frame 36.1→0。bss 20.5→10.1（其中 eez-flow 12.4→2.2）。精确字节：引擎 222,006→94,668；合计 1,142,430→990,092；eh_frame 36,916→0；bss 20,973→10,340。

## 沉淀（新增断言 / 案例 / 文档）

reference/11_minimal_eez_project_scaffold.md §3.1 追加「未优化 vs 优化后」两栏对比表；测量工具 tools/ui_size_report.py。
---

## ★ 附：ui_size_report.py 完整输出（两版 · 原样 log，未做摘要）

> 采集方式：同工程两种配置各构建一次，脚本逐字输出。
> 未优化 = executionQueueSize 1000 + ui 组件无 -Os + CXX 异常/RTTI 开；
> 优化后 = executionQueueSize 128 + ui 组件 -Os + CXX 异常/RTTI 关。

### A) 未优化（当前配置）

```text
==============================================================================
 固件资源占用报告  [lvgl_demo_template]     ui_size_report v2 (size tool only; no map guessing)
==============================================================================

[1] 固件总体 (app .bin)
    app .bin (烧写大小) : 1.09 MB (1,143,488 B)
    app 分区            : 8.00 MB (8,388,608 B)  已用 13.6%, 余 86.4%
    链接后进固件合计    : 1.09 MB (1,142,430 B)
    内部 RAM (bss+data) : 197.5 KB (202,224 B)

[2] flash 按分组            (单位: KB, 1 KB = 1024 B)
    分组                                             flash    占比
    --------------------------------------------------------------
    EEZ 引擎 (eez-flow.cpp)                       216.8 KB   19.4%
    EEZ 生成 UI (screens/ui/styles/images)           746 B    0.1%
    字体资源 (Montserrat)                         174.9 KB   15.7%
    字体渲染/加载 (LVGL font engine)                2.9 KB    0.3%
    LVGL 内核                                     296.6 KB   26.6%
    显示/触摸/适配 (ST7701/GT911/adapter)          35.1 KB    3.1%
    本项目组件 (main/board/dsi/native/console)     12.3 KB    1.1%
    C/C++ 运行时 (libm/libc/libstdc++)             29.6 KB    2.7%
    IDF 内核 (FreeRTOS/heap/log/...)              206.4 KB   18.5%
    其它 (其它 IDF 组件 / managed 库)             140.3 KB   12.6%
    --------------------------------------------------------------
    合计                                           1.09 MB  100.0%

[2b] 重点两项（区分「EEZ 框架」与「字体资源」，别混算）
    EEZ 独有代码 (引擎 + 生成 UI)   : 217.5 KB (222,752 B)
    字体相关 (资源 + 渲染引擎)      : 177.8 KB (182,043 B)   <- 字体资源不属于 EEZ；原生 LVGL 同样要付

[3] EEZ UI 组件逐文件 (eez-test/src/ui)     (单位: KB)
    文件                             flash       RAM
    ------------------------------------------------
    eez-flow.cpp.obj              216.8 KB   13.6 KB
    ui.c.obj                         396 B      16 B
    screens.c.obj                    342 B      80 B
    images.c.obj                       8 B       0 B
    ------------------------------------------------
    合计                          217.5 KB

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
    .dram0.bss  : 20.5 KB (20,973 B)
    .dram0.data : 12.6 KB (12,929 B)
    bss 占用最大的对象:
        12.4 KB  libui.a:eez-flow.cpp.obj
         3.1 KB  libfreertos.a:port.c.obj
          908 B  liblvgl__lvgl.a:lv_init.c.obj
          720 B  libfreertos.a:tasks.c.obj
          512 B  libriscv.a:interrupt.c.obj
          316 B  libc_nano.a:libc_a-findfp.o
          312 B  libfreertos.a:timers.c.obj
          264 B  libc_nano.a:libc_a-on_exit_args.o

[6] 常驻 flash 的段 (PSRAM XIP 执行/读取)
    .flash.text   (代码)      : 641.5 KB (656,864 B)
    .flash.rodata (常量/字体) : 260.6 KB (266,891 B)
    .eh_frame     (异常表)    : 36.1 KB (36,916 B)

==============================================================================
 提示: build/.../libui.a 的文件大小(数 MB)含调试信息与符号表，不代表固件占用。
==============================================================================
```

### B) 优化后（queue 128 + -Os + 关异常）

```text
==============================================================================
 固件资源占用报告  [lvgl_demo_template]     ui_size_report v2 (size tool only; no map guessing)
==============================================================================

[1] 固件总体 (app .bin)
    app .bin (烧写大小) : 967.8 KB (991,024 B)
    app 分区            : 8.00 MB (8,388,608 B)  已用 11.8%, 余 88.2%
    链接后进固件合计    : 966.9 KB (990,092 B)
    内部 RAM (bss+data) : 186.9 KB (191,367 B)

[2] flash 按分组            (单位: KB, 1 KB = 1024 B)
    分组                                             flash    占比
    --------------------------------------------------------------
    EEZ 引擎 (eez-flow.cpp)                        92.4 KB    9.6%
    EEZ 生成 UI (screens/ui/styles/images)           740 B    0.1%
    字体资源 (Montserrat)                         174.9 KB   18.1%
    字体渲染/加载 (LVGL font engine)                2.9 KB    0.3%
    LVGL 内核                                     296.6 KB   30.7%
    显示/触摸/适配 (ST7701/GT911/adapter)          35.1 KB    3.6%
    本项目组件 (main/board/dsi/native/console)     12.3 KB    1.3%
    C/C++ 运行时 (libm/libc/libstdc++)              5.9 KB    0.6%
    IDF 内核 (FreeRTOS/heap/log/...)              205.8 KB   21.3%
    其它 (其它 IDF 组件 / managed 库)             140.3 KB   14.5%
    --------------------------------------------------------------
    合计                                          966.9 KB  100.0%

[2b] 重点两项（区分「EEZ 框架」与「字体资源」，别混算）
    EEZ 独有代码 (引擎 + 生成 UI)   : 93.2 KB (95,408 B)
    字体相关 (资源 + 渲染引擎)      : 177.8 KB (182,043 B)   <- 字体资源不属于 EEZ；原生 LVGL 同样要付

[3] EEZ UI 组件逐文件 (eez-test/src/ui)     (单位: KB)
    文件                             flash       RAM
    ------------------------------------------------
    eez-flow.cpp.obj               92.4 KB    3.4 KB
    ui.c.obj                         396 B      16 B
    screens.c.obj                    336 B      80 B
    images.c.obj                       8 B       0 B
    ------------------------------------------------
    合计                           93.2 KB

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
    合计                                        177.8 KB
    只有 UI 真正用到的字号才需要保留；未用到的可在 sdkconfig 关闭
    (EEZ 的 screens.c 字体表带 #if LV_FONT_MONTSERRAT_xx 保护，关闭不会编译错)

[5] 内部 RAM (DIRAM)
    .dram0.bss  : 10.1 KB (10,340 B)
    .dram0.data : 12.6 KB (12,893 B)
    bss 占用最大的对象:
         3.1 KB  libfreertos.a:port.c.obj
         2.2 KB  libui.a:eez-flow.cpp.obj
          908 B  liblvgl__lvgl.a:lv_init.c.obj
          720 B  libfreertos.a:tasks.c.obj
          512 B  libriscv.a:interrupt.c.obj
          316 B  libc_nano.a:libc_a-findfp.o
          312 B  libfreertos.a:timers.c.obj
          264 B  libc_nano.a:libc_a-on_exit_args.o

[6] 常驻 flash 的段 (PSRAM XIP 执行/读取)
    .flash.text   (代码)      : 540.9 KB (553,908 B)
    .flash.rodata (常量/字体) : 248.7 KB (254,657 B)
    .eh_frame     (异常表)    : 0 B
       -> CXX 异常已关闭 (CONFIG_COMPILER_CXX_EXCEPTIONS=n)，异常表为 0

==============================================================================
 提示: build/.../libui.a 的文件大小(数 MB)含调试信息与符号表，不代表固件占用。
==============================================================================
```
