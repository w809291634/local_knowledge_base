# P-0164 · EEZ+LVGL 应用级示例 15 连坑复盘（wifi 全流程）：每坑一个机器检查，防再犯

- **工程**：EEz_stidio_examples/app-wifi-connect
- **日期**：2026-10-20
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：防再犯,自检清单,check_project,hiddenFlag,字体条目,cmap过滤,GB2312,flow检查错误,extern C,注释闭合,孤儿清理,exit守卫,textarea,mingw,wlanapi
- **关联提示词**：P-0163

## ★ 正解速查（先看这里——本条目 20 个坑的最终答案）

### 文字居中（按钮/标签）——一分钟正解

> **用 EEZ 新建一个按钮，照抄它的默认结构，只改文字。完。**

原生默认结构（EEZ Studio 0.29 / LVGL 9.4 实测）：
```json
{ "type": "LVGLButtonWidget", ..., "children": [{
    "type": "LVGLLabelWidget",
    "left": 0, "top": 0,
    "width": 80, "height": 32,
    "widthUnit": "content", "heightUnit": "content",   ← 自适应文字
    "text": "连  接", "textType": "literal",
    "localStyles": { "definition": { "MAIN": { "DEFAULT": {
        "align": "CENTER",            ← widget 对齐（画布原生渲染）
        "text_color": "0xFFFFFF", "text_font": "cn14" } } } }
}]}
```
生成码 = `set_size(LV_SIZE_CONTENT, LV_SIZE_CONTENT)` + `set_style_align(LV_ALIGN_CENTER)`。

**三条铁律**（每条都是一天工期换来的）：
1. **不要自创结构**：子 label 铺满 + `text_align` 样式——真机/画布都能居中
   （★勘误：EEZ 画布与 Run 用真实 LVGL wasm 渲染，text_align 有效；此前
   "画布不居中"实为字体缺字形导致的宽度异常，非对齐不支持——原文
   "画布不渲染 text_align"是错误推断，eez-test 零使用≠不支持）；
2. **不要用 widget align 配显式定位**：`align:CENTER` 与 top/left **互斥**
   （LVGL align 覆盖 x/y 语义）；且 label **无 width 字段时 EEZ 发
   set_size(0,h)**（0 宽+WRAP=文字叠成竖条）——必须显式
   `widthUnit:"content"`；
3. **测量先验证坐标系**：`lv_obj_get_x` 返回**父容器相对偏移**，当屏幕坐标
   用会得出"+40px 假偏移"（作者连踩两次，见坑 16/20）。

### 耗时复盘：为什么简单问题弄了一天

| 失误 | 代价 |
|---|---|
| 没有第一时间照抄 EEZ 原生按钮结构，自创 text_align 铺满方案 | 源头错误，画布/真机表现分裂 |
| 像素测量坐标系搞混（父相对当屏幕） | 把"居中"误判为"偏移 40px"，误启动修复 |
| 凭单次可疑测量就连改两次布局（手工居中→widget align） | 每次修复引入新问题（+40 偏移→竖条→位置错乱） |
| 修复前没测基线、修复后没用同一方法复测 | 无法及早发现"修复"本身是错的 |

**正确节奏**：测量基线（验证坐标系）→ 定位根因 → 最小改动 → 同一方法复测。

### 对照实验定论（font-test 工程，三实现并排+像素测量）

| 实现 | 构建产物 | EEZ 画布 |
|---|---|---|
| A text_align 铺满 | 偏差 0 ✓ | 偏差 0 ✓（★勘误：wasm 渲染，text_align 有效） |
| B align:CENTER + content | **label 飘出按钮** ✗（EEZ/LVGL 组合定位锚定异常） | 画布原生渲染 ✓ |
| **C 收窄+坐标（推荐）** | 偏差 0 ✓ | 所见即所得 ✓ |

（本工程按钮最终采用 **EEZ 原生形态**＝画布/真机双正确；C 为通用兜底。）

---

## 现象（看到什么）

wifi 全流程示例开发过程中连续踩 15 个坑（字体豆腐×3、面板盖屏、程序自退、链接错误×3、GUI extraction failed、演示抖动等），同类问题反复出现

## 复现（怎么稳定重现）

开发全程记录，每坑见 P-0163 及本条目清单

## 根因（真正的原因）

共性根因三类：①EEZ JSON 契约键名/形态与直觉不符（hiddenFlag、字体条目四要点、flow 检查错误非致命）且**静默失败**（错误延迟到 GUI/运行期才暴露）；②动态数据硬套固定变量集；③补丁链碎片化修改同一函数（误删代码块）

## 修复（做了什么）

三层防线：①**机器自检 design/check_project.py**（7 项静态检查：表达式引用标识符审计/字符集⊆字体cmap/字体条目形态/extern C/注释提前闭合/无守卫exit——每项对应一次真实事故，交付前必跑，FAIL 退出码 1）；②**流程定稿**：build_example→cli_build(含flow错误守卫)→audit_chars→gen_font(必须在cli后)→sim build；③**KB 知识**：本条目 15 坑清单+P-0123/0125/0140/0152/0163 关联条目

## 证据（数字 / 命令输出）

check_project.py 对当前工程跑通 OK；audit_chars/截图自证（lv_snapshot）闭环验证；15 坑逐条有复现与修复记录（P-0163 全程 + 本条目清单）

## 沉淀（新增断言 / 案例 / 文档）

app-wifi-connect/design/check_project.py、README、KB 10号§12、模板说明.md、workspace memory

## 15 坑清单（按根因分类；★ = 已有机器检查或流程门槛拦截）

### A 类：EEZ JSON 契约与直觉不符 / 静默失败
| # | 坑 | 症状 | 正解 | 拦截 |
|---|---|---|---|---|
| 1 | 隐藏表达式 JSON 键名是 `hiddenFlag`（写 hiddenExpr 静默无效） | 面板盖住全屏吸收点击，行点击全失效 | 键名 hiddenFlag + hiddenFlagType:"expression"；语义 true=隐藏 | ★ check 1（引用审计）+ 静态读取验证 |
| 2 | 字体条目四要点缺一不可（renderingEngine/lvglRanges/lvglGlyphs/glyphs[]） | 画布中文永远豆腐 + Fonts 面板崩 | P-0125 定论格式 | ★ check 3 |
| 3 | 字符集含字体没有的字 | GUI 提取报 doesn't have any characters in range | fontTools 读 cmap 交集过滤 | ★ check 4 |
| 4 | 字符集漏 ASCII | GUI 画布拉丁/数字全豆腐（PC_SIM 正常——烘焙有 -r） | GB2312/自定义集必须并 0x20-0x7E | ★ check 4（字符集含 ASCII 断言） |
| 5 | flow 检查错误**非致命**（引用错变量照样 Build successfully finished） | 坏表达式静默进产物，运行期 label 永错 | cli_build.py 守卫：正则抓 N errors，N>0 判 FLOW_ERRORS | ★ check 1 + cli 守卫 |
| 6 | Textarea 的 text 是 input 单向（绑变量覆盖打字） | 键盘打字被 tick 清掉 | 密码在动作里 lv_textarea_get_text(objects.pwd_ta) 读 | 流程：动作里读控件 |

### B 类：构建链与工具时序
| # | 坑 | 症状 | 正解 | 拦截 |
|---|---|---|---|---|
| 7 | CLI 不烘字体（孤儿清理还会删已烘的） | undefined reference to ui_font_xxx | gen_font 在 **cli_build 之后**跑 | ★ 流程定稿（模板说明四步） |
| 8 | 改名/新建文件后 GLOB 不重扫 | lv_conf not found / 新文件没编 | 删 build_rel（及 _rw）重配 | 流程定稿 |
| 9 | EEZ 残留进程单实例锁 | 后续构建 TIMEOUT | taskkill EEZ Studio.exe 再构建 | 流程定稿 |

### C 类：native 层 C 代码
| # | 坑 | 症状 | 正解 | 拦截 |
|---|---|---|---|---|
| 10 | native 头注释里写 `xxx_*/yyy_*`（`*/` 提前闭合注释） | extended character 。 is not valid in an identifier 一串错 | 注释里避免 `*/` 序列 | ★ check 6 |
| 11 | native_vars.h 漏 extern "C" | C 侧链接 undefined reference to get_var_xxx | 头文件包 extern "C" | ★ check 5 |
| 12 | io 平台层依赖 LVGL（lv_tick_get） | 平台不可移植 | 计时用 clock() | 代码评审 |

### D 类：行为/演示
| # | 坑 | 症状 | 正解 | 拦截 |
|---|---|---|---|---|
| 13 | 调试 exit(0) 残留 | "一点就退出" | 自动退出必须 getenv("WIFI_AUTOEXIT") 守卫 | ★ check 7 |
| 14 | 多轮碎片 replace 改同一函数 | 误删代码块（假模式自动扫描丢失） | 整段读-改-写，禁止叠碎片 patch | 流程纪律 |
| 15 | mingw wlanapi 四件（链接位置/缺宏/枚举名/字段名） | undefined reference / error 87 | 见 P-0163 mingw 节 | 照抄 io_win.cpp |

## 三层防线（落地）

1. **机器自检**：`design/check_project.py`（managed python 跑，7 项检查对应
   上表 ★）——交付前必跑，FAIL 退出码 1。
2. **流程定稿**（模板说明.md）：
   `build_example → cli_build(含 flow 守卫) → audit_chars → check_project → gen_font → sim build`
   ——顺序敏感（gen_font 必须在 cli 后；新文件删 build_rel）。
3. **知识**：本条目 15 坑清单 + 关联条目（P-0123/0125/0140/0152/0163/10 号架构）。

## ★ 坑 16（追加）：键盘位置三重坑——构造期对齐残留 + 坐标空间混淆

- **现象**：密码面板的键盘贴底/偏右，怎么设 pos 都不对。
- **根因（三层叠加）**：
  ① LVGL 键盘**构造函数自带 `lv_obj_align(obj, LV_ALIGN_BOTTOM_MID, 0, 0)`**
     （lv_keyboard.c:451）——EEZ 的 `lv_obj_set_pos` 只设 x/y style，**不清 align**，
     最终位置 = BOTTOM_MID 基准 + set_pos 偏移 → 键盘贴父容器底部；
  ② 修复时用 `lv_obj_get_x` 当屏幕坐标校验——**它返回的是父容器相对偏移**，
     "x=70" 被误读成屏幕 70，实际屏幕位置 = 面板原点 + 70 = 110（右移 34 的真相）；
  ③ 正解：`lv_obj_align(TOP_LEFT,0,0)` 清残留 + `lv_obj_set_pos(父相对设计位)`
     （本例面板内 30,100）——像素实测键盘中心 240 = 设计 240。
- **正解代码**（main.c，ui_init 之后）：
  `lv_obj_align(objects.kb_main, LV_ALIGN_TOP_LEFT, 0, 0);`
  `lv_obj_set_pos(objects.kb_main, 30, 100);  /* 父容器相对设计位 */`
- **方法论**：UI 位置争议不要目测缩放图——**lv_snapshot 截图 + 叠设计参考线
  （PIL ImageDraw）+ 像素测量**三件套，一次定位。lv_obj_get_x/y 返回父相对值，
  当屏幕坐标用必被坑（本题 34px 偏差的全部来源）。

## ★ 补充：忘记网络 + 保存/不保存双路径（真 WiFi 全闭环）

- 新增坑 17：EEZ actions 数组加了动作但 **native_actions.cpp 忘了实现** →
  链接 undefined reference to action_xxx（对账手段：check_project 已比对
  actions 数组与……未覆盖 C 实现——后续可加"生成 actions.h 声明逐一 grep
  实现"检查）。
- 双路径连接：记住=是 → WlanSetProfile + mode=profile（持久化=NVS 保存）；
  记住=否 → wlan_connection_mode_temporary_profile（不保存）。mingw 旧头
  WLAN_CONNECTION_PARAMETERS 无 strProfileXml 字段——temporary 模式下
  strProfile 即 XML。
- forget：WlanDeleteProfile + 若正连着先 WlanDisconnect（P-0085 语义）。
- 三按钮布局：连接/忘记/取消 各 120 宽等缝对称（面板 400 宽 → x=0/140/280）。

## ★ 补充：按钮文字居中实测 = 精确居中（-1px 渲染舍入）；测量工具 measure_ui.py

- 用户报"按钮文字不居中"。像素测量（三按钮，屏幕坐标系）实测：文字中心与
  按钮中心偏差 **-1px**（渲染舍入）= 精确居中；叠设计框线截图直观确认。
- ★ 复盘：第一轮测量报"偏移 +40px"是**测量者自己踩了坑 16 的坐标空间混淆**
  （测量窗口用了面板相对坐标，按钮实际在面板原点+EEZ 坐标）——坑 16 的
  普遍性连作者都会再踩，故把"坐标系换算"写进 measure_ui.py 文档头。
- 用户在 EEZ 画布/Run 看到的不居中 = GUI 渲染差异（同键盘 Run 差异）；
  **权威验收 = PC_SIM 截图 + measure_ui.py 像素测量**。
- 新工具 `design/measure_ui.py`：对 shot_fake.bmp 测量键盘中心/三按钮文字
  中心/状态行中心（阈值按文字颜色特征：白字 vs 浅蓝字），±4px 内 OK。
  彩蛋：键盘 -3px 来自 LVGL 键盘按键布局的非对称（1# 键窄），属正常。

## ★ 坑 18 定稿：居中的正确姿势与两次错误修复的教训

- **错误修复 1**：把"画布文字不居中"归因于 text_align 画布不渲染 → 改手工
  坐标居中 → 实际把构建后居中的按钮搞偏 +40px（测量坐标系错误导致的误判，
  见坑 16）。
- **错误修复 2**：改用 widget align=CENTER + 无宽 label（EEZ 原生按钮形态）
  → EEZ CLI 对无宽 label 发 set_size(0,h)，w=0+WRAP=逐字换行竖条；且
  **widget align=CENTER 与 top/left 显式定位互斥**（LVGL align 语义覆盖
  x/y）→ 整行 label 位置错乱。
- **最终正解**：定宽整行 label + `text_align:"CENTER"` 样式（LVGL 真机
  渲染正确，像素实测居中）；**不用 widget align**（与显式定位互斥）。
  ★勘误：EEZ 画布/Run 用真实 LVGL wasm 渲染（Studio 自带 2MB wasm），
  text_align 画布有效——此前画布"不居中"是字体缺字形（宽度异常）所致，
  字库修复后画布同样居中。
- **方法论教训（本轮最大）**：连续两次"修复"都引入新问题，因为每次都凭
  单一证据下结论就动手。正确节奏：**测量基线 → 定位根因 → 最小改动 →
  同一方法复测**；测量本身要先验证坐标系（坑 16 重演了两次）。

## ★ 坑 19（追加）：垂直居中——LVGL label 文字从盒顶绘制

- **现象**：定高 label（h=22~30 > 文字 14px）里文字贴顶，"上下不居中"。
- **根因**：LVGL label 的文字永远从盒子内容区**顶部**绘制；`text_align`
  只管水平。定高 > 文字高 → 下方留空 = 视觉偏上。
- **正解**：**label 高度收缩到文字高（14px）+ y 定位到所在行的垂直中心**
  （y = 行y + (行h-14)/2）。按钮内 label 同理（y=(按钮h-14)/2=5）。
  水平仍由 text_align:CENTER 承担。
- 像素验证：按钮内文字 y 中心 285 vs 按钮中心 284（±1 ✓）。
- ★ 规矩：**EEZ 里文字垂直居中不要靠"调高 label 再指望文字自己居中"——
  直接把 label 高做成 14、y 给到行的中心**（与坑 18 的水平方案合用：
  定宽 + text_align 水平居中 + 收缩高 + y 垂直居中 = 双轴精确）。

## ★ 坑 20（对照实验定稿）：EEZ 原生 align:CENTER + content 组合 label 飘出父容器

- 用户提示"新建一个按钮对照"→ 建 font-test 工程，三实现并排 + 像素测量：
  A text_align 铺满 = 偏差 0 ✓；B widthUnit:content + align:CENTER =
  **label 脱离按钮**（定位锚定异常，按钮内空、文字跑到屏幕下方）✗；
  C 手工坐标 = 偏差 0 ✓。
- **定论**：按钮文字居中正解 = **C 方案（label 收窄到文字宽 + x 居中，
  零对齐属性依赖，画布/真机双端一致）**；A 方案真机正确、画布观感差异；
  **B（EEZ 原生 align+content）在 EEZ v3 + LVGL 9.4 组合不可用**。
- 工具沉淀：font-test 工程（对照实验模板）、text_w() 宽度估算、
  measure_ui.py 像素校验。

## ★ 坑 20 正解落地：按钮子 label 改 EEZ 原生形态（content 单位 + align CENTER）

- 按用户指示"新建按钮只改文字"：button() 的子 label 改为与官方 defaultValue
  逐字段一致的形态——`width:80,height:32,widthUnit:"content",heightUnit:"content"`
  （自适应文字）+ localStyles 仅 `align:"CENTER"`+text_color+text_font
  （**不再铺满、不再 text_align、不再 ZERO_PAD**）。
- 生成码 = `set_size(LV_SIZE_CONTENT, LV_SIZE_CONTENT)` + `set_style_align(
  LV_ALIGN_CENTER)` —— 与 EEZ 新建按钮完全同源，画布/真机一致。
- 像素实测：连接/取消文字中心偏差 -1px ✓。注意 EEZ 对"无 width 字段"发
  set_size(0,h)（NaN/0 宽陷阱），**必须显式 widthUnit:"content"**。
- 布局说明：连接/取消按钮相邻无缝是用户还原的坐标（30/200 各 170 宽），
  非缺陷。


---

## ★ 勘误（2026-10-20 晚 · 用户要求核对本地经验）

**本条目原"EEZ 画布不渲染 text_align"为错误结论，已全文勘误**：

- 错误来源：把"EEZ 画布文字不居中"误判为"对齐样式不被渲染"。
- 真相：①EEZ Studio 自带 LVGL wasm（~2MB），LVGL 工程的画布/Run 用
  **真实 LVGL** 渲染，text_align 必然有效；②当时画布文字不居中/豆腐的
  真因是**字体缺字形**（GB2312 未配置 + extraction failed），文字宽度
  异常导致观感错位——字库修复后画布即正常。
- 教训升级（坑 16 的元版本）：**观察异常时先把"环境是否完好"列为第一
  嫌疑（字体/资源/缓存），再怀疑框架能力**——"框架不支持 X"这类结论
  必须有框架源码或官方文档级证据，禁止从单次观感直接推断。
- 影响范围：本条目 TL;DR 铁律 1、对照实验表 A 行、坑 18 定稿；
  reference/02_styles_fonts_vars.md 文字居中节——均已同步勘误。
- 仍然有效的部分：坑 16/20 的坐标空间、content 单位、w=0 陷阱、
  B 方案 label 飘出按钮（实测）——不受本次勘误影响。

## ★ 补充：键盘弹出（LVGL 标准模式）+ 连接失败可见反馈（真 WiFi 诊断闭环）

- **诊断**（假指针自动点行+点连接）：整条链路通（扫描→选中→动作→io 层），
  "点连接无效果"真因 = **键盘不弹出没法输密码 + 守卫拒绝无可见反馈**
  （日志 `[IO:WIN] locked network needs a password` 用户看不到）。
- **修复 1（键盘弹出，LVGL 标准模式）**：`ui_behavior.cpp`（PC/真机共用）——
  键盘初始隐藏；密码框 CLICKED → 移除 HIDDEN；键盘 READY/CANCEL → 加 HIDDEN。
  画布不受影响（JSON 键盘仍在面板内设计位）。
- **修复 2（失败可见反馈）**：wifi_state=3（请输入密码/连接失败）→ footer
  表达式四分支。锁网络空密码守卫拒绝时发布 3；连接超时失败发布 3。
- **教训**：守卫/失败路径必须有 **UI 可见反馈**，只打日志用户看不到
  （"点连接无效果"的一半就是这个）。

## ★★ PC 真 WiFi 连接"无效果"根因链（实测闭环，2026-10-20 18:50）

用户现象：真 WiFi 模式点"连接"无任何反应。假指针自动点行+连接 + netsh
交叉验证，定位五层根因：

1. **mingw 头 `WlanSetProfile` 参数顺序与 MSDN 相反**：
   mingw: (..., bOverwrite, pReserved, pdwReasonCode)
   MSDN : (..., bOverwrite, pdwReasonCode, pReserved)
   按 MSDN 传 → &reason 进了 pReserved（非 NULL）→ ERROR_INVALID_PARAMETER(87)。
   修：`WlanSetProfile(h, guid, 0, xml, NULL, true, NULL, &reason)`
2. **认证方式必须以真实 profile 为准**：该网络为 WPA3SAE + transitionMode，
   硬编码 WPA2PSK 的 profile 无效。正解：加密网络统一 WPA3SAE +
   <transitionMode>true</transitionMode>（兼容 WPA2/3）；SSID 用
   <hex>…</hex><name>…</name> 双写 + xmlns。
3. **高频轮询会卡死连接**：每 4ms 拍调 WlanQueryInterface(250Hz) →
   接口卡 authenticating(state=7)。修：轮询节流 1s。
4. **SetProfile 后立即 Connect 静默无效**（返回 0 但不连）→ 非阻塞延迟
   800ms 再 Connect（pending 标志）。
5. **密码以系统 profile 为准**：用户记录写成 `yjt888...`（含省略号，恰为
   真密码）；先 `netsh wlan export profile key=clear` 核对 keyMaterial。

附带：
- 已保存 profile 存在 → WlanGetProfile 命中 → 直接 WlanConnect（免密码）✓
- remember=否：temporary 不稳 / 连上后删 profile 即断 → Windows 后端
  "不保存"暂不可行（两者均保存，已记录）
- 验证三件套：show interfaces / show profiles / export key=clear（用完即删）
- 测试钩子 WIFI_TEST_SSID/WIFI_TEST_PWD（env 注入，不落盘不打印）+
  按 SSID 找行对象 + scroll_to_view + 实际坐标点击

## ★ 补充：把"构建成功"与"截图对照"变成门槛（P-0165 同期）

- **三假象**（只认 `BUILD RESULT:` 与 `N errors`，其余不算证据）：
  ① `Build successfully finished` 但零产出（`settings.build.files` 被删，P-0005）；
  ② `No error and no warning detected` 但 flow 引用错误非致命（本条目坑 5）；
  ③ 满屏红字其实是 Chromium 噪音（P-0010/P-0016）。
- **preflight 脚本**：按序跑 生成 → CLI → 字符审计 → 静态自检 → 字库，并在 CLI 之后
  **校验产物文件**（screens.c/ui.c/vars.h/actions.h/structs.h 存在且非空）——P-0005 的
  机器化落地；缺脚本时明确 SKIP，不把"没检查"伪装成"通过"（P-0012）。
- **截图对照**：程序内 `lv_snapshot`（系统截图抓不到 GPU 帧、不可复现）→ BMP→PNG；
  颜色反相用 `--swap-rb`（P-0008 通道序）；按设计坐标 spec 画绿框/红线，输出
  "设计 SVG ｜ 截图 ｜ 叠加图" 三栏报告 + 每元素 Δx/Δy，±4px 为 PASS。
- **判读口诀**：整块同向偏 20–40px = 坐标空间错（坑 16）；文字贴顶 = label 定高 >
  文字高（坑 19）；方块字 = 先修字体（A2–A4）；颜色整体反相 = 快照通道（P-0008）。
