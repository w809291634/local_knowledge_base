# P-0062 · 别对 src/ui 整体 set_source_files_properties(LANGUAGE CXX)

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：CMake,语言标准,C与C++差异,enum隐式转换,EEZ生成代码
- **关联提示词**：无

## 现象（看到什么）

刚把仿真器改成「引用工程源码」后，`screens.c` 编译炸出满屏：

```
src/ui/screens.c:981:29: error: no matching function for call to 'lv_obj_remove_flag'
  981 |  lv_obj_remove_flag(obj, LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE);
apl_lvgl_v9_4/src/core/lv_obj.h:207:6: note: candidate function not viable:
        no known conversion from 'int' to 'lv_obj_flag_t' for 2nd argument
void lv_obj_remove_flag(lv_obj_t * obj, lv_obj_flag_t f);
（… 还带 "fatal error: too many errors emitted"）
```

## 复现（怎么稳定重现）

在根 CMakeLists 里加一行
`set_source_files_properties(${UI_SOURCES} PROPERTIES LANGUAGE CXX)` 就必现
（`UI_SOURCES` 由 `file(GLOB_RECURSE UI_DIR/*.c *.cpp *.h)` 收来，把 .c 全变 C++）。

## 根因（真正的原因）

EEZ 生成的 `screens.c` 里到处是位或拼接的 flag 字面量
（`LV_OBJ_FLAG_CLICKABLE|LV_OBJ_FLAG_SCROLLABLE` 这整项是 **int**），
而内核签名 `lv_obj_flag_t f` 是 **enum**。

- **C** 规则：int → enum 允许隐式转换（enum 的兼容类型是 int/unsigned），编译过；
- **C++** 规则：int → enum 必须显式 `static_cast`，编译不过。

也就是说：真机（C 编译）本来好好的，仿真（强改 C++）才炸。这类"只在另一条语言规则下炸"
的问题最容易误导排查方向（会先去怀疑内核版本/头文件）。

当初加这行的理由是「eez-flow.h 是 C++ 头」——但 `.cpp` 靠**扩展名**本来就是 C++，
不需要动 `.c`，更不需要对含 `.h` 的 GLOB 结果整体设 LANGUAGE（给头文件设 LANGUAGE
本身还可能报 "Cannot set LANGUAGE property for files of type HEADER_FILE"）。

## 修复（做了什么）

删掉那行，改成让扩展名说话，并在 CMakeLists 里写死注释防止再犯：

```cmake
add_executable(main
    ${SIM_MAIN_DIR}/main.c
    ${PROJECT_SOURCE_DIR}/main/src/mouse_cursor_icon.c
    ${UI_SOURCES}
    ${NATIVE_SOURCES})
# ★ src/ui 里 .c / .cpp 一律按**扩展名**决定语言，不要整体改 LANGUAGE CXX：
#   screens.c 里传 int 给 lv_obj_flag_t —— C 允许隐式转换、C++ 不允许。
#   .cpp(eez-flow.cpp) 靠扩展名本来就是 C++，C 头由 eez-flow.h 自己包 extern "C"。
```

（`LANGUAGE CXX` 那条如果只是想让 `.cpp` 参与，其实 `add_executable` 默认就按扩展名处理。）

## 证据（数字 / 命令输出）

删掉那一行后，`screens.c / styles.c / images.c / ui.c / ui_font_*.c` 全部按 C 通过编译，
只剩 MSVC 的 `strtok` deprecation 警告（无害），随后顺利进入链接阶段。

## 沉淀（新增断言 / 案例 / 文档）

- 判据：CEEZ 生成物（`screens.c` 等）在**真机就是 C 编译**，仿真必须保持同语言，
  否则「仿真绿、真机绿」但两端语言规则不一致会造出仿真特有的假红/假绿。
- 同理：仿真入口 `sim_cmake/main.c` 也是 C，别顺手改成 C++。
