# P-0164 · EEZ+LVGL 应用级示例 15 连坑复盘（wifi 全流程）：每坑一个机器检查，防再犯

- **工程**：EEz_stidio_examples/app-wifi-connect
- **日期**：2026-10-20
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：防再犯,自检清单,check_project,hiddenFlag,字体条目,cmap过滤,GB2312,flow检查错误,extern C,注释闭合,孤儿清理,exit守卫,textarea,mingw,wlanapi
- **关联提示词**：P-0163

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
