# P-0165 · 生成产物里 Flow 的真实形态：已启用、数组定长、native var 只能标量

- **工程**：app-wifi-connect2（EEZ Studio 0.29 / LVGL 9.4 / 480×320）
- **日期**：2026-10-20
- **工具**：WorkBuddy
- **状态**：verified（结论经源码与二进制双重核对）
- **标签**：eez,flow,array,native-var,codegen,架构
- **关联**：P-0156（首次导出 eez-flow.cpp 报 undefined reference）、P-0020（native_vars 链接）、reference/10（硬 UI 分离）

## 现象（为什么要查）

规划 WiFi 列表时出现三个互相矛盾的判断，必须钉死：

1. 「本工程生成的是 `create_screens()`，没在 Flow 运行时里，要迁移」；
2. 「`ArrayValue` 内部是 `std::vector<Value>`，可以 push，能装任意多个 AP」；
3. 「用 native var 把 `ap_t[]` 数组传给 UI」。

三条全错。错在任何一条，架构都会走偏（迁移成本 / 越界 / 链接失败）。

## 核实（三条命令，任何人可复现）

```bash
# 1) 运行时是否已启用
grep -n "eez_flow_init\|eez_flow_tick" src/ui/ui.c
#   ui_init() → eez_flow_init(assets, sizeof(assets), ...)
#   ui_tick() → eez_flow_tick(); tick_screen(g_currentScreen);

# 2) 运行时是否真的编进固件（不是只生成没链接）
nm -C bin/main.exe | grep -c "eez::flow"      # 实测 501

# 3) 数组到底是什么
grep -n -A5 "struct ArrayValue {" src/ui/eez-flow.h
#   struct ArrayValue { uint32_t arraySize; uint32_t arrayType; Value values[1]; };
```

## 根因（三条事实）

### 事实 1：Flow 已启用，不是"待迁移"

| 证据 | 值 |
|---|---|
| `src/ui/eez-flow.h` 第 17 行 | `#define EEZ_FOR_LVGL 1`（自带，不用外部定义） |
| `src/ui/eez-flow.cpp` | **9,923 行**，由 EEZ 直接生成进工程，不是外部库 |
| `src/ui/ui.c:48` | `eez_flow_init(assets, sizeof(assets), (lv_obj_t **)&objects, ...)` |
| `ui_tick()` | `eez_flow_tick(); tick_screen(g_currentScreen);` |
| 编译产物 | `eez::flow` 符号 **501** 个 |

→ 结构体/数组**本来就能用**；缺的不是运行时，而是 assets 里的结构体定义与变量内容。

### 事实 2：`ArrayValue` 是定长柔性数组，不是 `std::vector`

```c
struct ArrayValue { uint32_t arraySize; uint32_t arrayType; Value values[1]; };
Value Value::makeArrayRef(int arraySize, int arrayType, uint32_t id);
ArrayValue *Value::getArray();          // 可写：getArray()->values[i] = ...
```

- **没有** `push_back` / `clear` / `resize`；长度在 `makeArrayRef(size, ...)` 时定死；
- `Value` 带 `refCounter`：`operator=` 先 `freeRef()`（计数减到 0 释放）再对新值 `++`，
  所以"每轮扫描重建数组"**不会泄漏**，但会有分配抖动 → 建议一次建好 N 条、之后只改字段。

### 事实 3：native var 只能标量，带不了数组

```c
typedef enum { NATIVE_VAR_TYPE_NONE, NATIVE_VAR_TYPE_INTEGER, NATIVE_VAR_TYPE_BOOLEAN,
               NATIVE_VAR_TYPE_FLOAT, NATIVE_VAR_TYPE_DOUBLE, NATIVE_VAR_TYPE_STRING } NativeVarType;
typedef struct { NativeVarType type; void *get; void *set; } native_var_t;
```

→ 槽位式标量（`ssid_1`/`rssi_1`…）可以走 `native_vars[]`；
**结构体数组必须走 Flow 全局变量**：`makeArrayRef` → `getArray()->values[i]` → `setGlobalVariable(idx, arr)`。

## 修复 / 正解（代码形状）

```cpp
// 一次建好（5 条），之后只改字段；索引用 vars.h 的枚举，不写死数字
Value arr = Value::makeArrayRef(5, FLOW_ARRAY_OF_STRUCTURE_AP, 0);
for (int i = 0; i < 5; i++) {
    Value e = arr.getArray()->values[i];
    e.getArray()->values[FLOW_STRUCTURE_AP_FIELD_SSID] = Value::makeStringRef(ssid, len, 0);
    e.getArray()->values[FLOW_STRUCTURE_AP_FIELD_RSSI] = Value(rssi);
}
setGlobalVariable(FLOW_GLOBAL_VARIABLE_APS, arr);
```

反例（会直接崩/静默失效）：

| 写法 | 后果 |
|---|---|
| `arr.values.push_back(...)` | 编译错（不是 vector） |
| `makeArrayRef(16,…)` 却写第 17 条 | 越界写堆 |
| 把 `ap_t[]` 塞进 `native_var_t.set` | 类型不支持（只有 5 种标量） |
| 用字面量 `setGlobalVariable(3, …)` | 变量增删后错位 → 用枚举 |

## 证据

- `eez-flow.h:1278-1282`（ArrayValue 定义）、`:1228`（makeArrayRef）、`:1016-1055`（refCounter/operator=）、`:2220-2223`（全局变量读写）、`:2568-2578`（NativeVarType）；
- `ui.c:48`、`ui_tick()`；`structs.h` 生成样例（`testValue` 即"结构体=字段数组"的封装）；
- `nm -C main.exe | grep -c "eez::flow"` → 501。

## 沉淀（机器检查建议并入 check_project）

```python
# A. ui.c 必须调 eez_flow_init / eez_flow_tick；缺 = 生成的 UI 不生效
assert "eez_flow_init" in ui_c and "eez_flow_tick" in ui_c

# B. 出现 "values.push" / "values.clear" = 把定长数组当 vector 用
assert not re.search(r"values\.(push|clear|resize)", src)

# C. setGlobalVariable 第一个参数必须是枚举名，不是数字
assert not re.search(r"setGlobalVariable\(\s*\d", src)

# D. native_vars 里不允许出现结构体/数组类型
```

## 教训（元层面）

- 判断"运行时有没有启用"看**生成代码 + 二进制符号**，不看文档、不看 `flowSupport` 开关；
- 判断容器语义看**结构体定义**，不看名字（`ArrayValue` 听起来像 vector，实际是柔性数组）；
- 跨层传数据的类型能力看**枚举定义**（NativeVarType 只有 5 种标量），不看字段名 `void *`。

## 追加核实：能不能"按数组长度生成 UI 行"（手册原文）

**结论：EEZ-GUI（Dashboard）有，LVGL 没有。**

| 手册章节 | 原文要点 | 适用项目 |
|---|---|---|
| **W40 List**（p.529） | "Use this Widget when you want to display the same Widget multiple times… the number of times it will be displayed depends on the **Data** property"；Data 为数组时"the number of elements in the list is equal to the number of elements in that array"；子控件用系统变量 **`$index`** 取数组项（例：`country_cities[$index].country`）；配合 `struct:$ScrollbarState` 可滚动 | **EEZ-GUI / Dashboard** |
| **W42 List (LVGL)**（p.538） | "This widget is **work in progress**… Studio will generate all the code for its creation, but for anything more than that you should do it in your **custom code**, for example after `ui_init()`" | LVGL（本项目） |

配套证据：`eez-flow.h` 里 `lv_obj_create/lv_label_create` 命中 0 次（Flow 运行时没有创建控件的 API）；
asar 里 `repeater` 命中 0 次。

→ LVGL 工程里，**数组长度不会驱动行数**；要做"数量不定 + 滚动"，只有两条路：
① 容器 + C 侧 `lv_obj_create` 循环建行（本工程采用，上一代 88 行已验证）；
② 整个工程切 EEZ-GUI 运行时（放弃 LVGL codegen，设备端换渲染器，字体/性能/移植全变）。
