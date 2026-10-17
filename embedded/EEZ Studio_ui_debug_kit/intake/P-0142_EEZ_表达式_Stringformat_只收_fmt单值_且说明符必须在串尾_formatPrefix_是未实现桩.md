# P-0142 · EEZ 表达式 String.format 只收 (fmt,单值) 且说明符必须在串尾；formatPrefix 是未实现桩——"HH:MM" 类双值格式化必须 padStart+两次 format 拼接

- **工程**：watch (Design Watch)
- **日期**：2026-10-18
- **工具**：Qoder
- **状态**：fixed
- **标签**：表达式引擎,String.format,padStart,formatPrefix,native变量,时间显示,eez-flow
- **关联提示词**：PR-0239

## 现象（看到什么）

§38 时钟变量首版用 `String.format("%02d:%02d", hh, mm)`（照 asar 注册表"有 format 函数"想当然），
EEZ 构建报 **77 errors**：`In function 'String.format' call expected 2 arguments, but got 3`（35 个
表达式标签 ×2 处计数 + 其他）。改拼 `"%d:05"` 这类"中部说明符"设想也被源码否决。

## 根因（真正的原因）

eez-flow.cpp 逐行实证（本 LVGL 工程运行时）：
1. `do_OPERATION_TYPE_STRING_FORMAT`（8427）：pop 两个值——**格式串 + 单一数据值**；
   数据类型由**格式串最后一个字符**当说明符扫描决定（specifier=format[len-1]），
   尾字符不是合法说明符（如 "…05" 的 '5'）直接进 `else → makeError`。
   ⇒ 一次 format 只能注入一个值、且必须落在串尾说明符处；`'%d:05'`（值在串首/中部）不可用。
2. `do_OPERATION_TYPE_STRING_FORMAT_PREFIX`（8515）：**pop 三个值后无条件 push error**——
   注册表里有名字，运行时是空桩。信注册表不信源码就中招（第四次验证"运行时面才算数"）。
3. 拼接可用：`op_add`（6993）任一侧字符串 → concatenateString；`String.padStart(str,len,pad)`
   （8538）真实现。数字转串用 `String.format("%d", x)`（串尾 'd' 合法）。
4. 除法毒化连带坑：`'/'` 产 double 会毒化 %d 实参；分钟→小时用 `(t*2185)>>17` 整型化。

## 修复（做了什么）

`TIME_EXPR = pad(format("%d",H),2,"0") + ":" + pad(format("%d",M),2,"0")`（生成器
build_watch_ui.py 模块常量落码，最终作为 flow labelSetText 动作的 expression 值使用
——载体坑另见 P-0143）；重建后 String.format 类错误清零。
同场抓到陈坑复发：§36 Settings 页动画动作对象写了原始驼峰 `stic_General` 等
→ "Widget index not found" ×7（P-0132 已登记过的规范化坑，落地时漏套 c_ident）；
icon_anim_flow 的 object 参数统一过 c_ident() 修复。

## 证据（数字 / 命令输出）

首轮构建日志 77 errors（`/tmp/eez_build_38.log`，String.format 行刷满）；
二轮 7 errors（全为 stic_* Widget index not found）；三轮（c_ident 修复后）0 错 0 警
（见 `__LAST_BUILD__` 占位，重建完成后回填）。

## 沉淀（新增断言 / 案例 / 文档）

skills §11.42（EEZ 表达式格式化/字符串操作 + native 变量桥配方）；报告 §38；
PR-0239。
