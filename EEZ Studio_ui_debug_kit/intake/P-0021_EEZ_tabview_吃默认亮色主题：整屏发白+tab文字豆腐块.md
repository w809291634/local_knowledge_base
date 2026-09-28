# P-0021 · EEZ tabview 吃默认亮色主题：整屏发白+tab文字豆腐块

- **工程**：（待补）
- **日期**：2026-09-28
- **工具**：未知工具
- **状态**：open
- **标签**：（无）
- **关联提示词**：（无）

## 现象（看到什么）

单屏嵌套 Tabview 重构后，仿真 11 屏背景全部浅白（设计稿深色 #0A0C11），顶/左 tab 栏纯白底，标签文字全是豆腐块；G5 对照平均差异 60.21%（语音/正在播放 90%+）

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

lv_theme_default.c:740-800：tabview 主对象挂 styles.scr(浅色)、tab 栏容器挂 bg_color_white(纯白)、按钮 CHECKED 挂 primary_muted(浅蓝)、文字用 Montserrat 无中文字形。这些是 EEZ 生成的内部对象，不在 DSL 控件树里，json2eez 的 localStyles 摸不到

## 修复（做了什么）

新建 design/fix_tabview.py 生成后处理：用 lv_tabview_get_tab_bar/get_content/get_tab_count/get_tab_button 公开 API，对 4 个 tabview 逐部件压回深色（主对象/栏容器 bg=0x0A0C11，按钮 DEFAULT 透明底+13px 中文字体+灰字，CHECKED 0x1B2233+白字，PRESSED 微亮，outline/shadow 清零），all.py 在 gen_fonts 后挂载；幂等标记 [fix_tabview]

## 证据（数字 / 命令输出）

build/sim_shots/对照/*.png 三联图：修复前热力图整屏红，修复后残留在 tab 按钮块形态与文字基线

## 沉淀（新增断言 / 案例 / 文档）

（待补）
