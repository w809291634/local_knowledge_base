# P-0030 · 滑动同步从 native user action 退役改纯 EEZ flow：不是 bug，是选型被用户铁律推翻

- **工程**：eez-test（EEZ Studio 1.22.10 / LVGL 9.4.0 / 800×480）
- **日期**：2026-09-30
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：EEZ-flow,tabview,VALUE_CHANGED,user-action,asar取证,Compare,localVariables,铁律
- **关联提示词**：PR-0057

## 现象（看到什么）

P-0029 的滑动高亮跟随当时用 native User Action 实现（tabview VALUE_CHANGED →
`action_sync_rail_main/cats`）。功能验收通过后，用户两次加码：

1. 「能够在eez中能实现的动画，不要填写到用户程序中」
2. 定稿：「后期要求优先输出用EEZ里面控制UI，包括各个控件的联动，仅仅控制外部硬件的
   允许使用用户代码，如果实在没有办法的话，需要通知我」

高亮同步是纯 UI 控件联动，落在「必须 EEZ」一侧 —— native 方案需整体退役重做。

## 复现（怎么稳定重现）

grep 双证（重构前）：
- `src/native/native_actions.cpp` 存在 `rail_set_checked` / `action_sync_rail_main` / `action_sync_rail_cats`；
- `src/ui/screens.c` 两处 VALUE_CHANGED 分支是 `action_sync_rail_main(flowState, ...)` 直调。

（重构前功能本身经 P-0029 修复后是正常的 —— 退役原因是选型不合规，不是行为错误。）

## 根因（真正的原因）

不是缺陷，是**选型惯性**：当初不确定「读 tab 序号 → 按序号分组置 CHECKED」能否用
EEZ flow 表达，就顺手走了 native 捷径。事后对 EEZ Studio 的 asar 做序列化取证，
证明这套结构 flow 完全能表达 —— 正确顺序应该是**先取证再选型**。

## 修复（做了什么）

### asar 序列化取证四要点（写 DSL 编译器的硬依据，全部实证、零试错通过）

1. **assignable 参数没有 Type 后缀字段**：LVGL 动作类工厂
   `e.isAssignable || (o[e.name+"Type"]="literal")` —— 只有非 assignable 参数才写
   `<name>Type`；`tabviewGetActiveTab` 的 `result` 就是裸表达式字符串，误加
   `resultType` 会破坏序列化。
2. **CompareActionComponent**（flowComponentId 1009）：`A`/`B`/`C` =
   makeExpressionProperty 裸串；`operator` 枚举（`"="`）；输出口 `@seqout` / `True` /
   `False`（boolean 序列输出的连线 output 名就叫 **"True"**）。
3. **@seqout 传播时机**：运行时 `executeLVGLApiComponent`（eez-flow.cpp 4188–4196）
   末尾才 `propagateValueThroughSeqout` —— 同一 LVGLActionComponent 的全部 actions
   执行完才向后传播，后面的 Compare 读到的一定是写完的变量，无需手工排序。
4. **页面局部变量**：`page.localVariables`（Flow.typeClass=Variable：
   `{name, type, defaultValue}`），表达式裸名按 local-variable 解析；本链用
   `type:"integer"`。

### 代码改动（DSL 两个文件 + native 一个文件，src/ui 由流水线再生成）

- `design/json2eez.py`：`onTabChange` 从字符串动作名改为结构化
  `{tv_ref, var, clear, add}`（add 是「每页码一组」嵌套列表，与 onAction 互斥）；
  tabview 节点生成 `eventHandlers:[{eventName:"VALUE_CHANGED", handlerType:"flow", userData:0}]`；
  每条链 = 1 个 LVGLActionComponent（objClearState(CHECKED)×N +
  tabviewGetActiveTab(result=局部变量)）+ 每非空页码 1 个
  CompareActionComponent(var, i, "=") + 1 个 AddState 组件；
  局部变量汇总写入 `page.localVariables`；`walk_ids` 跳过 `CompareActionComponent`。
- `design/build_ui.py`：s_home / sett_nav 两处改为结构化 onTabChange 赋值；
  顶层 actions[] 删 `sync_rail_main` / `sync_rail_cats` 声明（留注释墓碑）。
- `src/native/native_actions.cpp`：删 `rail_set_checked` + 两个 action 函数（留墓碑注释）。
- **永不手改 `src/ui/*`**（铁律不变），screens.c/ui.c 全部由流水线重新生成。

## 证据（数字 / 命令输出）

- `python design/sim.py` 6 条 [swipe] 断言全绿（断言与 P-0029 版**一字未改**）：
  main tile 跳转 0/1000→1/0100→0/1000；sett 上滑 1/100、下滑 0/000。
- 11 屏视觉对照平均 **8.59%**（阈值 25%），无回归；`all.py --shots` 41 秒完成。
- `src/ui/screens.c` 两处 VALUE_CHANGED 已变为
  `flowPropagateValueLVGLEvent(flowState, 13, 0, e)` / `(flowState, 399, 0, e)`，
  无 action_* 直调；`ui.c` / `actions.h` 0 残留。
- 工程 JSON：actions 8 个；Main 页 `localVariables` 2 条（main_page_idx / set_page_idx）；
  组件 LVGLActionComponent×28 + CompareActionComponent×7（main B=0..3、set B=1..3，
  set 索引 0=通用左栏无对应行 → 不建组件）；连线输出统计 CLICKED 19 /
  VALUE_CHANGED 2 / @seqout 7 / True 7。
- 交互仿真窗口用户实测：「我测试可以的」。

## 沉淀（新增断言 / 案例 / 文档）

- skills.md **§11.17**（选型铁律 + 链结构 + 四要点 + 验收 + 方法论）；CHANGELOG **v0.9.0**；
- UI_BEHAVIOR_CONTRACT.md 新增「UI 控制实现选型铁律」节，§0 / §7 的 sync_rail 引用
  更新为纯 EEZ flow；
- PROMPT_LOG **PR-0057**（铁律原话存档）；
- 铁律同步落三处记忆：项目 `.workbuddy/memory/MEMORY.md`、用户级
  `~/.workbuddy/MEMORY.md`、当日日志。
- 可被哪条断言提前拦住：**选型审查** —— 新增任何 UI 行为前先问「EEZ flow /
  LVGL 动作 / 状态样式能否表达」，native 只留外部硬件控制。6 条 [swipe] 运行时
  断言继续把行为质量关（重构不改行为时断言一字不动，即等价性证明）。
