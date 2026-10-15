# P-0103 · 走路器：内层 tabview 的页要两段 tab 命令；无 id 圆钮只能 mousef 图标

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：sim.py,走路器,双层tabview,mousef,截图错位,目检
- **关联提示词**：PR-0136

## 现象（看到什么）

chataudit 第一次跑：audit m_ai_chat_scroll 出来的消息行 vis=0、坐标 @(887,-188) 在屏外；mousef m_ic_send 点完没有任何新消息。

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

对话页不在主 nav 的第 1 页 —— 它在 AI 主页（tab main 0）的**内层** tabview 里，必须再下一条 tab ai 1；只写内层那条，截的全是待机页（与设置页 tab main 3 + tab set 0 同一个坑，第二次踩）。另外 pane_chat 的发送圆钮 button() 没传 id => 不在 objects 表里，只能对里面的图标 m_ic_send 用 mousef（按对象中心发真 press/release，LVGL 会把点击送给可点击祖先）。

## 修复（做了什么）

走路脚本写死两段式：tab main 0 + tab ai 1 再断言；给这类无 id 控件统一用 mousef <子图标>。以后凡是内层 tabview 的页，先加两段 tab 再怀疑对象名。

## 证据（数字 / 命令输出）

修好后 chataudit：待机页 m_txt_6=19:39、m_txt_7 带…，「该有文字却没文字且可见」=0。

## 沉淀（新增断言 / 案例 / 文档）

MEMORY.md 走路器段补一句：双层 tabview 必须两段 tab
