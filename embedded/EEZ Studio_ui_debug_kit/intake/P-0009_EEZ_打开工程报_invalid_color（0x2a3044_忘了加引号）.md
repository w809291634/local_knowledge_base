# P-0009 · EEZ 打开工程报 invalid color（0x2a3044 忘了加引号）

- **工程**：（待补）
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：eez,color,gate
- **关联提示词**：（无）

## 现象（看到什么）

EEZ Studio 里 AiChat / Screen / Children / Container 与 History 两处 Container 报 invalid color；CLI build 却报 'No error and no warning detected'

## 复现（怎么稳定重现）

build_ui.py 里 av_bg = 0x2a3044 if who=='me' else PRIMARY（少了引号）

## 根因（真正的原因）

Python 里 0x2a3044 是 int 2764868，json2eez 用 str() 序列化后写成 "2764868"，不是 0xRRGGBB 形式；EEZ 的 ColorFormat.parse 认不出 -> formatType=UNKNOWN -> isValid()=false。报错对象正是三处「我」的气泡头像（AiChat 1 条 me 消息、History 2 条）

## 修复（做了什么）

改成 SW_OFF 常量（'0x2a3044'）；并在 json2eez 增加 check_colors() 门禁：颜色类属性必须是 0xRRGGBB/#RRGGBB，否则生成阶段直接抛错

## 证据（数字 / 命令输出）

扫描工程得到 3 处 bg_color='2764868'；修复 + 门禁后扫描 0 处；单元测试：注入 '2764868' 被 ValueError 拦住

## 沉淀（新增断言 / 案例 / 文档）

json2eez.check_colors()（已内置门禁）；ui_debug_kit/skills.md §11.3
