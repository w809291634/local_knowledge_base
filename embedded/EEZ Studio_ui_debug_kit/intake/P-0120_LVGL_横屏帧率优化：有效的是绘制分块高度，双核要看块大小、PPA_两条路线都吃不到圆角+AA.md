# P-0120 · LVGL 横屏帧率优化：有效的是绘制分块高度，双核要看块大小、PPA 两条路线都吃不到圆角+AA 文字

- **工程**：08_lvgl_demo_v9_opt (p4_touch_lcd4_3_exp)
- **日期**：2026-10-10
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,帧率,ESP32-P4,esp_lvgl_adapter,buffer_height,PPA,双核,内部RAM,假绿,取证,串口COM20
- **关联提示词**：PR-0195, PR-0196

## 现象（看到什么）

800x480 横屏跑 lv_demo_widgets，串口/屏上只有 3fps，且每帧周期恒为 300ms；按清单依次打开双核、PPA 都看不出任何差别。

## 复现（怎么稳定重现）

examples/08_lvgl_demo_v9_opt：bsp_display_start_with_config(ROTATE_90, TRIPLE_PARTIAL)，main 里 lv_demo_widgets() + lv_demo_widgets_start_slideshow() 造持续动画；CONFIG_ESP_LVGL_ADAPTER_ENABLE_FPS_STATS=y 后 esp_lv_adapter_get_fps() 每秒打串口；再用 LV_EVENT_FLUSH_START/FINISH(lv_refr.c:1415/1423) 夹 esp_timer 把送屏与绘制拆开。一次只改一项，45s 采样一轮。

## 根因（真正的原因）

四层：(1) 3fps 是空载假象——静止画面唯一重绘源是性能表，周期 LV_SYSMON_REFR_PERIOD_DEF=300ms；(2) adapter 在旋转下算错分块行数：TRIPLE_PARTIAL 的绘制缓冲 = 面板hor_res(480) x buffer_height（display_manager.c:868-872），而 ROTATE_90 后 LVGL 宽 800 ⇒ 每块只有 0.6 x buffer_height 行，bh=50 实际 30 行/块 = 一帧 16 块，块边界同步把帧率压死；(3) 双核收益依赖块大小：14 块时两个 draw unit 在同一块缓冲上同步反而更慢，4 块才转正(+5%)；(4) PPA 帮不上：原生 PPA draw unit 只认领 radius==0 且 opa==MAX 的 FILL 和不缩放不旋转的 RGB565/888 IMAGE（lv_draw_ppa.c:111-160），adapter 的 blend handler 把所有带 mask 的圆角/描边/字形 AA 退回软渲染（lvgl_ppa_accel_v9.c:321-336），根因是 P4 PPA BLEND 只有 bg/fg+固定 alpha，没有 per-pixel mask 输入 ⇒ 逐像素混合卸不出去；瓶颈是逐像素软件混合，不是核数也不是送屏。

## 修复（做了什么）

BSP profile .buffer_height 50→200（4 块/帧，192KB 内部 RAM）+ CONFIG_LV_DRAW_SW_DRAW_UNIT_CNT=2 ⇒ 均值 23.4→37.0fps、最低 15→26、峰值 47；TRIPLE_FULL、LV_USE_PPA(路线②)、LV_DEF_REFR_PERIOD 10ms、L2 cache line 64B 全部实测无收益已回退；bh=267 与 L2 512KB 会直接起不来（内部 RAM 被抢光），不要再往那个方向调。

## 证据（数字 / 命令输出）

同负载：800x480 横屏(ROTATE_90) + TRIPLE_PARTIAL + lv_demo_widgets + start_slideshow，重绘面积 84%，45s 采样，路线①(enable_ppa_accel)保持 false：
  A bh=50(14块/帧) 单核      均23.4 最低15 峰34  送屏5.4ms 绘制45ms
  B bh=50(14块/帧) 双核      均19.9 最低12 峰32  送屏5.5ms 绘制57ms  ← 双核在碎块下是负收益
  C bh=128(6块/帧) 单核      均29.9 最低21 峰37  送屏6.7ms
  D bh=128(6块/帧) 双核      均29.3 最低20 峰39               ← 与单核同分
  E TRIPLE_FULL 整屏渲染     均25.7 最低21 峰29  送屏7.8ms     ← 每帧100%重绘，更差
  F bh=200(4块/帧) 单核      均35.2 最低25 峰43  送屏4.8ms 绘制18.5~35ms
  G bh=200(4块/帧) 双核      均37.0 最低26 峰47  送屏4.8ms 绘制16~33ms  ← 最佳
  H = G + 路线② LV_USE_PPA(+IMG，指纹确认 lv_ppa=1 生效)  均35.8 最低26 峰48 ← 无收益
  I = G + LV_DEF_REFR_PERIOD 15→10ms                      均36.0 最低26 峰47 ← 无收益
  J bh=267(想做到3块/帧) 起不来：E esp_lvgl:disp alloc primary buffer 256320 bytes failed
    → assert esp32_p4_wifi6_touch_lcd_4_3.c:690 → 复位循环；内部 RAM 上限就卡在 bh=200~267 之间
  K L2 cache 512KB 起不来：Could not reserve internal/DMA pool (0x101)
    → abort @ freertos/app_startup.c:179 reclaim_startup_stack_memory_for_heap
  空载读数：出厂示例静止画面恒 3fps/300ms 每帧，那是性能表周期(lv_sysmon.c:24-25,120)，不是瓶颈

## 沉淀（新增断言 / 案例 / 文档）

skills.md §11.31（帧率先确认在不在动、再确认一块多大；双核收益随块大小变号；PPA 覆盖面要看它认领的 task type）+ §11.32（每轮从设备日志回读生效配置，管道会吞掉构建失败）；reference/08_lvgl_esp32p4_frame_rate.md 第4节「没测过基线」由实测表取代；与 esp32/esp32-p4-lvgl9-touch-lcd-debug-optimization.md §19（+6fps、NON_BLOCKING 拖影、队列深8无效）和 §4/§16（大 buffer_height 分配失败、路线①崩溃）互相印证。

## ★ 追加（同日）自证帧率：不靠眼睛，靠串口两个指标

用户要求「你自己验证」。加进固件的两件事（`main/main.c`）：

1. **面板帧缓冲抽样哈希**：`esp_lcd_dpi_panel_get_frame_buffer(bsp_display_get_panel_handle(), 3, &fb0,&fb1,&fb2)`
   拿到 DSI 正在扫描的三块 PSRAM（本板每块 768000 B），每秒各取 700 个 RGB565 像素做 FNV-1a。
   实测 83 秒里 `changed=3/3` 每秒、`distinct fb hashes=83` ⇒ 扫出的那份内存**确实在逐秒改写**，
   排除「计数器在跑但画面冻结」（esp32 子库 §5 记过的 TRIPLE_PARTIAL+ROTATE_90 冻结形态）。
   注意这是 CPU 读 PSRAM；本次没出现常数哈希，所以缓存陈旧掩盖变化的情况没有发生，
   若要更硬可以 msync(INVALIDATE/M2C) 后再采样。
2. **帧周期直方图**（累计，不是平均）：`<25ms / <33ms / <50ms / >=50ms` 四桶 + `ge40=达标帧/总帧`。
   3146 帧：`<25ms=1302(41.4%) 25-33ms=1289(41%) 33-50ms=554(17.6%) >=50ms=1`。
   ⇒ 平均 36.4fps、峰值 47fps、**达到 40fps 的帧只占 41%**，"最低 40fps" 这个口径直接量化成不达标。
   坑：`inst_min` 会被**开机第一帧**（实测 416ms）拉成一个假极小值，`>=50ms` 那 1 帧就是它，
   报瞬时最低帧率时要先把首帧剔掉。

## ★ 追加（同日）烧写后的触摸假象

`idf.py flash` 只拉 RTS 复位，GT911 不在复位域里（它的 RST 与 LCD RST 共用，
`esp32_p4_wifi6_touch_lcd_4_3.c` 的 `tp_cfg.rst_gpio_num = BSP_LCD_RST`），于是烧完头一两次开机会：
`GT911: touch_gt911_read_cfg(419): GT911 read error!` → `Error (0x103)` → BSP 里
`bsp_display_indev_init` 的 `ESP_ERROR_CHECK` 直接 abort → `rst:0xc SW_CPU_RESET` 再来一遍，
第三次才 `Touch input device registered`（本次日志：0x5d 失败、0x14 也失败、第三次成功）。
⇒ **不要把它当成帧率改动引起的回归**：断电重上电/按复位键就正常；真要治是把触摸失败降级成
`ESP_LOGW` 容错（esp32 子库也提过这个口子），那是 BSP 健壮性决定，归用户。


## ★ 追加 3（2026-10-10 晚）：稳定模式约束落地后的数

用户否决两件事：**不许用局部绘制**（必须全屏滚动），**不许改画面效果**（所以 `LV_DRAW_SW_COMPLEX=n` 换的 43fps 作废），
并指出 **TRIPLE_PARTIAL 会因 PPA 卡死**——与 `esp32/esp32-p4-lvgl9-touch-lcd-debug-optimization.md` §5
「TRIPLE_FULL 稳定 / TRIPLE_PARTIAL 冻结」一致。于是回到 TRIPLE_FULL 重测（外观不变、双核、缓存 16/8、60s）：

| 轮 | 配置 | 均值 | 每秒最低 | 峰值 | 帧周期分布 |
|---|---|---|---|---|---|
| R26 | TRIPLE_FULL，屏上性能表**关** | 29.0 | 24 | 33 | <20ms 0 / <25 2 / <33 814 / >=33 789 |
| R27 | TRIPLE_FULL，性能表**开**（用户要求保留指示器） | 29.0 | 24 | 33 | 同上（0/2/829/807） |

三条新结论：

1. **在 TRIPLE_FULL 下屏上性能表是免费的**（29.0 vs 29.0）——因为整屏重绘时 overlay 那块面积可忽略；
   之前 PARTIAL 下它值 2.6% 是另一条链路的账。**用户要指示器就直接给，不用拿帧率换。**
2. **PARTIAL 37.7 与 FULL 29.0 的差（约 -23%）就是稳定税**：FULL 每帧 100% 面积 + 未重绘区不复制；
   PARTIAL 靠分块把面积压到 84% 但那条增量刷新路径在本 adapter 版本上会冻结。
3. **卡死的根因找到了**：`managed_components/espressif__esp_lvgl_adapter/0001-bugfix-lcd-Fixed-PPA-freeze.patch`
   是给 **ESP-IDF 本体** `components/esp_driver_ppa/src/ppa_srm.c` 加的 2 行
   `PPA.sr_byte_order.sr_macro_bk_ro_bypass = 1;`，而本机 IDF 源码里**没有这 2 行**（grep 无命中）
   ⇒ 补丁从未生效，PPA SRM 冻结风险一直存在。横屏每帧 SRM 次数：PARTIAL 4~16 次 / FULL 1 次
   —— 这解释了为什么 FULL 稳定、PARTIAL 容易死。
   ⇒ 处置：要么给 IDF 打这 2 行（影响所有工程，须用户同意），要么保持 FULL（每帧只 1 次 SRM）。
4. **50fps 在这个约束下的距离**：实测绘制 ~31ms/帧（与缓冲位置无关，PARTIAL 的绘制也是 26~33ms），
   送屏 ~8ms。§20 的异步旋转只能隐藏送屏 ⇒ 约 32~37fps，仍不到 50。
   样式不许改又要全屏滚动的唯一可达路径是**减少每帧像素**：LVGL 按 640x400 渲染、由 PPA SRM 在同一次
   事务里 scale+rotate 到 480x800（像素量 0.4x，圆角/渐变/阴影/字号全保留，代价是清晰度），
   需要改 adapter 的 LVGL 分辨率、缓冲尺寸、SRM scale 与触摸坐标反缩放四处 ⇒ 属组件内改动，先请示。


## ★ 追加更正（2026-10-10 晚）本条目里被证据推翻或降级的结论（逐条点名）

纪律：编号只增不改；本段是**追加**的更正，前面原文保留。

| # | 原结论 | 现状 | 依据 |
|---|---|---|---|
| 1 | 「路线② `CONFIG_LV_USE_PPA` 无收益」的首次读数 | 首次那两次是**旧固件**（构建失败被管道吞掉）；后来带指纹 `lv_ppa=1` 的 R14c 实测 35.8 vs 37.0，结论成立但只算一次 | 追加 2、§11.32 |
| 2 | 「L2 cache line 64B 无收益」 | **撤回，等于未测**：那一轮同样是旧固件，至今没有有效对照 | 本轮复核 |
| 3 | 「绘制线程优先级往上调会倒退（写 6 时 37.6 vs 43.0）」 | **撤回**：`LV_DRAW_THREAD_PRIO` 在 LVGL Kconfig 是 `range 0 4`（`managed_components/lvgl__lvgl/Kconfig:212-215`，与 esp32 子库 §19.7 同一个坑），6 属非法值被静默改写 ⇒ 测的不是那个假设；合法值 4 的对照因构建进程残留（`ninja: failed recompaction: Permission denied`）中断，仍未测 | 本轮实测 |
| 4 | 「buffer_height=200 就是内部 RAM 上限」 | **降精度**：只证明 200 可用（192KB）、267 不可用（256320B 分配失败 → assert 复位循环），墙在两者之间 | 追加 2 的 J 行 |
| 5 | 「烧完头两次开机 GT911 失败是 RTS 复位时序造成」 | **降级为假设**：现象可复现（`GT911 read error → Error(0x103) → ESP_ERROR_CHECK abort → rst:0xc`，第三次成功），但没做断电重上电对照 | 追加 2 |
| 6 | 「`export.ps1` 走不通是因为 idf_tools.py 认为工具未安装」 | **归因错误**：真实原因是继承了 `MSYSTEM` 让 `idf_tools.py` 直接拒跑（输出为空 → `BadExpression`）；清掉 `MSYSTEM` 后 `export.ps1` 能不能用**未测**。后来确认**根本不需要自建环境**：IDF 根那对脚本可用（见 `esp32/esp-idf-windows-build.md` §1） | cmd 复测 |
| 7 | 单次采样、差值 <5% 的项（`LV_DEF_REFR_PERIOD 15→10` 36.0 vs 37.0；阴影/圆形缓存 36.4 vs 36.4） | **标注低置信**：同配置重复采样噪声约 ±0.5fps，<5% 不足以下结论 | 追加 2/3 |
| 8 | **追加 3 的结论 1「TRIPLE_FULL 下屏上性能表是免费的（R26 关表 29.0 vs R27 开表 29.0）」** | **作废（2026-10-11）**：R27 那轮固件里**也没有表**——`CONFIG_LV_USE_PERF_MONITOR=y` 只写进了 `sdkconfig.defaults`，而 `sdkconfig` 已存在 ⇒ defaults 静默不生效（`build/config/sdkconfig.h` 零命中）。⇒ R26/R27 是同一配置测两次，不是"表的代价"；真开表后的读数**尚未重测** | 回读 `build/config/sdkconfig.h` |
| 9 | 「`sdkconfig` 的行号（`:3272/:3337/:3616`）可以长期引用」 | **改规矩**：`**/sdkconfig` 在 `.gitignore` 里，一次 reconfigure 行号整体位移 ⇒ 只引**符号名** | 本轮复核 |

还有一条比上面都重要的**取证纪律失效案例**：`cmd.exe /c "..."` 在 Git Bash 下会被 MSYS 把 `/c` 当路径转换吃掉
⇒ cmd 进交互模式、bat 一条都没执行，而 `$?` 仍是 0；我据此一度以为"bat 跑了但没输出"。
判据是**日志字节数 + 预期标记**（那次只有 189 字节的 Windows banner，正常构建是几十 KB 且必含 `Hash of data verified`），
cmd 开关要写成 `//c`。

---

## ★ 追加 4（2026-10-11）：对照工程 `examples/mipi_dsi` 结案 + 构建通路收敛

1. **横屏"全黑但软件一切正常"结案 = 背光极性**（本板背光栅极低有效；BSP 在
   `esp32_p4_wifi6_touch_lcd_4_3.c:380-395` 用 `ledc flags.output_invert = 1`，我那份漏了它 ⇒ 引脚恒高、LED 串全灭）。
   用户回报"LVGL 可以运行了"即结案证据。**可复用规矩**：自拼显示管线先照抄 BSP 的 `output_invert`，再怀疑数据通路；
   开机先打纯色是最快的分水岭。详录 `esp32` 子库 §22 末段。
2. **构建通路收敛为一条**：在 **IDF 根**开 cmd 终端 `idf_cmd_init.bat && idf_build.bat <cmd>`；切工程 = 改 `idf_build.bat:5` 的 `PROJECT_PATH`。
   两个必知的坑：该 bat 每个函数都 `exit /b 0` ⇒ **退出码恒 0、VS Code 会假绿**；`%~2` 是串口号不是工程路径。
   唯一真源 = `esp32` 子库 `esp-idf-windows-build.md`；`reference/09 §4.2`、`skills.md:1529-1539` 已按此就地更正，工程内复制的 bat 已删。
3. **还欠的数**：mipi_dsi 的 `flush=`（改 NON_BLOCKING+提交即 `flush_ready`+整帧旋进 FB 后应接近 0）、`stalls=`、
   `core free loops/s: cpu0=/cpu1=`（P4 无 SMP 内核 ⇒ 用空闲钩子计数，不用 `xCoreID`）、真开表后 29.0 是否变化。
   判据：**`flush≈0` 而 `render` 仍 26~28ms ⇒ 上限 ~35fps**，再往上只剩"降渲染分辨率 + 同次 SRM 放大"。

