# P-0143 · LVGL 目标 label textType:'expression' 被 codegen 编成空串（构建仍 0 错 0 警）——变量文本必须走 flow labelSetText 动作

- **工程**：watch (Design Watch)
- **日期**：2026-10-18
- **工具**：Qoder
- **状态**：fixed
- **标签**：label,textType,expression,codegen,静默丢内容,labelSetText,asar,时间显示
- **关联提示词**：PR-0239

## 现象（看到什么）

§38 首版把页头时间 label 改 `textType:'expression'`（值=格式化表达式），构建 0 错 0 警；
但生成代码 screens.c 里 35 个该 label 全部编成 `lv_label_set_text(obj, "")`——
文本被**静默丢弃**（与 P-0063 "控件无 lv_image_set_src 行"同族：编辑器不报、产物为空）。

## 根因（真正的原因）

EEZ Studio 1.22 LVGL 目标的 widget 定义级表达式文本没有 codegen 支持路径
（screens.c 全文 0 处 evalString；dataId 绑定表也不存在——ui.c grep 'dataId' 零命中）。
运行时面实证文本更新的正道是 **flow 动作**：
- asar 注册表 `registerAction({id:29, name:'labelSetText', group:'Label',
  properties:[object(widget:Label), text(string)]})`；编辑器把"设置属性"序列化为
  `{action:'labelSetText', object, text, textType}`（asar 内 JSON 转换代码可见
  `case"label": e.action="labelSetText", e.text=e.value, e.textType=e.valueType`）。
- 运行时 `ACTION_START(labelSetText)`（eez-flow.cpp:3891）：STR_PROP(text) 支持
  expression 求值 → `lv_label_set_text(obj, text)`。

## 修复（做了什么）

生成器回退 expr 参数；header() 时间 label 保持字面占位 '00:11' 并打 `_htime` 标记，
build() 统一编 ident（`htime_<page小写>`，35 个）并给每页挂 1s 心跳 clock_flow
（Start→Loop→Delay(1000)→labelSetText，值=TIME_EXPR 表达式）。
Dial 页指针链同结构写 transform_rotation。重建 0 错 0 警，screens.h 35 成员在位。

## 证据（数字 / 命令输出）

第一轮（expr 方案）：screens.c `lv_label_set_text(obj, "")` ×35、evalString=0；
第四轮（labelSetText 方案）：`No error and no warning detected`（/tmp/eez_build_38d.log:14）、
nav_audit PASS（pages=37 edges=72 back_btns=35）、ui.c native_vars 登记
{INTEGER, get_var_time_min, set_var_time_min}、vars.h 双声明。

## 沉淀（新增断言 / 案例 / 文档）

skills §11.42 修正（文本表达式作废，labelSetText 配方）；报告 §38；PR-0239。
判据提醒：**widget 定义级"能不能绑表达式"要看 codegen 产物有没有 eval 调用**，
编辑器 0 警不作为通过的证据（门禁得往产物层再压一层）。
