# P-0020 · 固件链接报 undefined reference to get_var_*（native 没注册成组件，且 ui 与 native 无依赖导致库顺序错）

- **工程**：小艺 · 智能屏 8（ESP32-P4 / ESP-IDF v5.5.5 / LVGL 9.4）
- **日期**：2026-09-27
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：ESP-IDF,链接,native,组件,CMake,库顺序,EEZ
- **关联提示词**：无

## 现象（看到什么）

`idf.py build` 在链接期失败，20 条同类报错：

```
esp-idf/ui/libui.a(ui.c.obj):(.data.native_vars+0x10): undefined reference to `get_var_wifi_state'
...
esp-idf/ui/libui.a(ui.c.obj):(.data.native_vars+0x80): undefined reference to `set_var_brightness'
collect2.exe: error: ld returned 1 exit status
```

## 复现（怎么稳定重现）

在 `lvgl_demo_ai/` 下 `idf.py build`（EEZ 导出过 UI 后必然复现）。

## 根因（真正的原因）

两层原因叠在一起，只修第一层不会好：

1. **`src/native/CMakeLists.txt` 不是一个真正的 ESP-IDF 组件**——它只有
   `set(NATIVE_SRCS ... PARENT_SCOPE)`，没有 `idf_component_register`。
   工程顶层虽然把 `./eez-test/src` 加进了 `EXTRA_COMPONENT_DIRS`，但 `native`
   因为没有注册而被跳过，`native_vars.cpp` **从未被编译**。
   又踩一个认知误区：EEZ **只生成 `src/ui/vars.h`（extern 声明），从不生成
   `vars.cpp`**，这 20 个函数的唯一定义就在 `native_vars.cpp` 里，所以不存在
   "重复符号"这种顾虑——不编译进固件就是 undefined。
   （同时 `main/CMakeLists.txt` 的 REQUIRES 整段被注释掉了。）

2. **补上组件注册后仍然失败**。用 `nm` 查证：符号其实在
   `libnative.a` 里（`T get_var_wifi_state` 等 22 个，覆盖 ui 需要的全部 20 个）。
   真正的原因是 **ui 与 native 之间没有依赖关系**，CMake 排出来的库列表是：

   ```
   104: esp-idf/ui/libui.a
   105: esp-idf/native/libnative.a
   106: esp-idf/main/libmain.a
   ...
   122: esp-idf/native/libnative.a
   123: esp-idf/ui/libui.a
   ```

   `ui.c.obj` 是因为 `main` 引用 `ui_init` 才被拉进来的，而 `main` 排在 ui **后面**，
   所以 ld 第一次扫到 `libui.a`(104) 时并没有提取 `ui.c.obj`；等它在 123 位第二次
   扫到 `libui.a` 才真正提取，此时 `libnative.a`(122) **已经扫过去了**。
   → 光看"ui 在 native 前面"会误判顺序没问题，必须看**最后一次出现**的相对次序。

## 修复（做了什么）

1. `eez-test/src/native/CMakeLists.txt` 改写成真正的组件：
   `idf_component_register(SRCS ${NATIVE_SRCS} INCLUDE_DIRS "." "platform"
   "${CMAKE_CURRENT_LIST_DIR}/../ui" REQUIRES driver lvgl)`。
   - 刻意 **不用 `REQUIRES ui`**（那会形成 ui ↔ native 循环依赖，让排序更不可控），
     ui 的头文件改用 `INCLUDE_DIRS ../ui` 表达（只是头文件，不是链接依赖）。
2. `main/CMakeLists.txt` 显式列全依赖。注意 **main 是 IDF 的特例组件**：不写
   REQUIRES 时默认依赖全部组件，一旦显式写就被覆盖——只写 `ui native` 会让
   `bsp/esp-bsp.h`、`board.h`、`lv_demos.h` 全部找不到（第二轮编译就撞上了）。
   最终列为：`esp32_p4_wifi6_touch_lcd_4_3 board_config lvgl apl_console ui native`。
3. 工程顶层 `CMakeLists.txt` 在 `project()` 之后建立 **ui → native** 的链接依赖：
   ```cmake
   cmake_policy(SET CMP0079 NEW)   # 跨目录给 target 加链接库必须开这个
   idf_component_get_property(ui_lib ui COMPONENT_LIB)
   idf_component_get_property(native_lib native COMPONENT_LIB)
   target_link_libraries(${ui_lib} PUBLIC ${native_lib})
   ```
   （不能写在 `ui/CMakeLists.txt`——EEZ 每次导出都会重写该文件；也不能写在
   `native/CMakeLists.txt`——那是反方向。）

## 证据（数字 / 命令输出）

- `nm -u libui.a | grep var_` → ui 需要 20 个 var 符号；
  `nm -g libnative.a | grep var_` → native 提供 22 个，差集为空。
- 修复前 `EXIT=2`（20 条 undefined）；修复后 **`EXIT=0`**，
  `build/lvgl_demo_v9.bin` 1669472 字节（分区余量 80%）。
- `nm build/lvgl_demo_v9.elf | grep -c get_var_/set_var_` → **20 个全部就位**；
  `click_trace_init` / `click_trace_tick` / `app_get_input_i` 也都在 elf 里
  （说明单击打印钩子一并进了固件）。

## 沉淀（新增断言 / 案例 / 文档）

- skills.md §7 新增「固件链接」条目：EEZ 不生成 vars.cpp；native 必须是真组件；
  ui→native 依赖要在工程顶层建；main 显式 REQUIRES 会丢掉"默认依赖全部"的特例。
- `native/CMakeLists.txt` / 工程 `CMakeLists.txt` 内已写明原因注释。
- 排查手法：链接报 undefined 时，先 `nm` 双向比对（谁需要 / 谁提供）确认符号真的存在，
  再去 `build/CMakeFiles/<elf>.rsp` 看**最后一次出现**的库相对顺序，别只看第一次。
