# P-0157 · EEZ 引擎三处体积优化实测：执行队列、ui 组件 -Os、关 CXX 异常（flash -152KB / RAM -10.9KB）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_template
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,engine,-Os,CXX异常,RTTI,eh_frame,queue,EEZ_FLOW_QUEUE_SIZE,flash,RAM,体积优化,实测
- **关联提示词**：PR-0264

## 现象（看到什么）

flowSupport 必须保留时如何压缩 eez-flow.cpp 引擎的 flash/RAM。手册 P13.2 明说只有 3 个 Build 选项影响内存（Compress flow definition / Execution queue size / Expression evaluator stack size），需确认它们够不够，并另找编译级手段。

## 复现（怎么稳定重现）

A/B 逐对象 diff：python -m esp_idf_size --files --format json 双构建对差。三项独立叠加：①.eez-project executionQueueSize 1000→128 ②顶层 CMake target_compile_options(ui PRIVATE -Os) ③sdkconfig 关 COMPILER_CXX_EXCEPTIONS/CXX_RTTI（改 defaults 并删旧 sdkconfig 重建）。

## 根因（真正的原因）

①引擎 g_queue[1000] 是 static 数组（EXTRAM_DATA 定义为空 ⇒ 落在内部 RAM 的 bss），每项 12B ≈ 12KB，正好是引擎 bss 的全部；1000 是默认值、多数 UI 用不到。②-Os 对模板很重的 C++ 引擎收益远超预期（text -40%）。③关异常不只删 .eh_frame（29732→0），还连带删掉 libgcc unwind-dw2(+fde) 与 12+ 个 libstdc++ EH/typeinfo 对象（stdexcept/functexcept/eh_throw/class_type_info 等）共 72KB，远超仅数 eh_frame 的直觉；且引擎自带 flow 级错误传播（throwError → findCatchErrorComponent，eez-flow.cpp:9572）根本不用 C++ 异常，故关闭安全。

## 修复（做了什么）

已落地三项：.eez-project executionQueueSize=128 且 eez-flow.h EEZ_FLOW_QUEUE_SIZE=128；顶层 CMake target_compile_options(ui PRIVATE -Os)，LVGL 保持全局 -O2 护帧率；sdkconfig.defaults 注释掉 CXX_EXCEPTIONS/RTTI。

## 证据（数字 / 命令输出）

①queue 1000→128：整机 bss 20973→10509（-10464），引擎 RAM 13921→3457，flash -122。②-Os：引擎 221884→142037（-79847，其中 .flash.text -71498 / -40.1%），整机 flash -79873，RAM ±0。③关异常：整机 flash 1062435→990092（-72343），.eh_frame 29732→0，34 个对象消失（unwind-dw2 -11508、unwind-dw2-fde -2874、eh_personality -1978、eh_alloc -1616、si_class_type_info -795、stdexcept -476 等），RAM -393。累计 flash 1142430→990092（-152338 ≈ -148.8KB / -13.3%），RAM 202224→191367（-10857 ≈ -10.6KB）。完整性核对：删 sdkconfig 重建后与备份逐行比对，仅差这 5 行 CXX 设置，无其他配置漂移。

## 沉淀（新增断言 / 案例 / 文档）

更新 reference/11_minimal_eez_project_scaffold.md §3（补三项实测表）；本批再次验证 A/B 逐对象 diff 法有效。
