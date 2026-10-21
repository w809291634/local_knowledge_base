# P-0167 · EEZ 结构体/数组变量：native 直接读写的 C++ 容器

> 2026-10-21 · app-wifi-connect2 实测（EEZ Studio 0.29 + LVGL 9.4）
> 场景：WiFi 扫描结果要"动态、行数不限、native 可写、UI 可读"——
> 用 **Struct + 数组全局变量**（Flow 变量），native 侧直接操作。

## 1. 事实核查（纠正 P-0165 的两处不准确）

| P-0165 原说法 | 实测修正 |
|---|---|
| "ArrayValue 是定长柔性数组，无 push/clear" | ✓ 对（`struct ArrayValue{uint32_t arraySize; uint32_t arrayType; Value values[1];}`） |
| "结构体字段写入方式待确认" | **已确认：结构体在 eez-flow 里就是"一个数组 Value"**——`Value` 的 union 里没有 structValue 成员；EEZ 生成的 `ap_infoValue` 封装内部是 `Value::makeArrayRef(NUM_FIELDS, FLOW_STRUCTURE_X, 0)`，字段**按下标**存 |
| "数组必须走 Flow 全局变量" | ✓ 对（`NativeVarType` 只有 INTEGER/BOOLEAN/FLOAT/DOUBLE/STRING） |

## 2. EEZ 工程 JSON 写法（.eez-project / 生成器）

类型表示法（EEZ 源码确认）：`integer` / `string` / `boolean`；结构体 `struct:<name>`；
结构体数组 `array:struct:<name>`。

```json
"variables": {
  "structures": [
    {"name": "ap_info", "fields": [
      {"name": "ssid", "type": "string"},
      {"name": "rssi", "type": "integer"},
      {"name": "lock", "type": "boolean"}
    ]}
  ],
  "globalVariables": [
    {"name": "scan_state", "type": "integer", "defaultValue": "0",
     "persistent": false, "native": true},
    {"name": "aps", "type": "array:struct:ap_info", "size": 0,
     "defaultValue": "[]", "defaultValueList": [],
     "persistent": false, "native": false},
    {"name": "ap_len", "type": "integer", "defaultValue": "0",
     "persistent": false, "native": false}
  ]
}
```

`Structure = {name, fields[]}`、`StructureField = {name, type}`、
`Variable = {id, name, description, type, size, defaultValue, defaultValueList, usedIn, persistent, native}`。

**cli_build 自动生成**（src/ui/）：
- `structs.h`：`enum FlowStructures{FLOW_STRUCTURE_AP_INFO=16384}`、
  `enum FlowArrayOfStructures{FLOW_ARRAY_OF_STRUCTURE_AP_INFO=81920}`、
  `enum ap_infoFlowStructureFields{..._FIELD_SSID=0, ..., ..._NUM_FIELDS}`、
  `struct ap_infoValue{ getter/setter }`、`typedef ArrayOf<ap_infoValue,...>`
- `vars.h`：`enum FlowGlobalVariables{FLOW_GLOBAL_VARIABLE_APS=0, ...}`
  ——**index = 非 native 变量在 globalVariables 里的顺序，native 变量不占位**

## 3. native 读写（ap_store.cpp 模式）

```cpp
using namespace eez;
using namespace eez::flow;      // ★ get/setGlobalVariable 在 eez::flow

void ap_store_publish(const wifi_ap_t *aps, int n)
{
    Value arr = Value::makeArrayRef(n, FLOW_ARRAY_OF_STRUCTURE_AP_INFO, 0);
    for (int i = 0; i < n; i++) {
        ArrayValue *raw = arr.getArray();
        // ★★ 坑 1：每个元素必须先变成结构体数组，再填字段
        raw->values[i] = Value::makeArrayRef(FLOW_STRUCTURE_AP_INFO_NUM_FIELDS,
                                             FLOW_STRUCTURE_AP_INFO, 0);
        ap_infoValue ap(raw->values[i]);
        ap.ssid(aps[i].ssid);   // ★ 坑 2：StringValue 存指针，数据源须静态存储期
        ap.rssi(aps[i].rssi);
    }
    setGlobalVariable(FLOW_GLOBAL_VARIABLE_APS, arr);
    setGlobalVariable(FLOW_GLOBAL_VARIABLE_AP_LEN, Value(n));
}
```

读取：`getGlobalVariable(FLOW_GLOBAL_VARIABLE_AP_LEN).getInt()` 取长度；
`getGlobalVariable(FLOW_GLOBAL_VARIABLE_APS).getArray()->values[i]` 取元素，
包一层 `ap_infoValue` 用 getter。

## 4. 三个坑（全部实测段错误/构建错）

1. **`makeArrayRef` 后元素不能直接当结构体用**：其 placement new 循环
   **从 i=1 开始**（`for (int i = 1; i < arraySize; i++)`），`values[0]` 未初始化；
   且每个元素初始是"普通 Value"不是结构体数组。**必须先给每个元素
   `makeArrayRef(NUM_FIELDS, FLOW_STRUCTURE_X, 0)`**，否则 `getArray()` 解
   未初始化值 → 段错误（n=0 不崩、n>0 必崩——定位特征）。eez 内部同款用法
   见 `eez-flow.cpp:4491`。
2. **`StringValue(const char*)` 存指针不拷贝**：数据源必须是 static/长生命周期
   缓冲区（io 层的 `static s_aps[]` 满足）；传栈上临时缓冲 = 悬空。
3. **数组变量 `defaultValue` 是 Flow 表达式**：空串会被当表达式解析，报
   `SyntaxError: ... end of input found`（flow 检查 2 errors）——必须给 `"[]"`。

## 5. 配套坑（C 侧）

- `get_var_*`/`set_var_*` 定义在 .cpp 里：**native_vars.h 必须同步声明**
  （`extern "C"` 块内），否则新函数被 C++ name mangling → 链接
  `undefined reference to get_var_xxx`（旧名残留也会静默踩中）。
- `setGlobalVariable` 在 `eez::flow` 命名空间（`Value`/`makeArrayRef` 在 `eez`）。

## 6. 机器检查

- `grep "lv_list_add_button\|makeArrayRef" src/native/ap_store.cpp`；
- `grep "FLOW_STRUCTURE_AP_INFO_NUM_FIELDS" src/ui/structs.h`（生成物在位）；
- 无头运行：`[UI] list rebuilt: N rows from aps[]`。

## 7. 仍然不成立的事（别被"容器"误导）

**UI 不会按数组长度自动生成控件。** LVGL 工程里 Flow 只提供表达式/动作，
没有 create-object API（`eez-flow.h` 里 `lv_obj_create` 命中 0）；
`flow_defs_v3.h` 的 `COMPONENT_TYPE_LIST_WIDGET/DISPLAY_DATA_WIDGET` 是
**EEZ-GUI（Dashboard）渲染体系**的组件，与 LVGL 控件树不兼容。
所以：**数据可以全动态（数组变量），渲染仍要一个 C 函数把数组映射到控件**
（本工程 = `lv_list_add_button` 循环，见 P-0166）。两者结合 =
"数据模型在 EEZ、渲染逻辑在 native"的分层。

## 关联

- P-0165（Flow 运行时形态）：本文补全结构体/数组的正确用法，修正其"待确认"项；
- P-0166（滚动三坑）：数组变量 → lv_list 渲染的正解搭档。
