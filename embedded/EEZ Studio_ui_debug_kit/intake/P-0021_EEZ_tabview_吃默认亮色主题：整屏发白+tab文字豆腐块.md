# P-0021 · EEZ tabview 吃默认亮色主题：整屏发白+tab文字豆腐块

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio 0.29
- **状态**：fixed（终版修复走 P-0025 原生路线；本条初版 fix_tabview.py 补丁已在第三轮废除删除）
- **标签**：EEZ,主题,tabview,字体,深色
- **关联提示词**：PR-0035

## 现象（看到什么）

单屏嵌套 Tabview 重构后，仿真 11 屏背景全部浅白（设计稿深色 #0A0C11），顶/左 tab 栏纯白底，标签文字全是豆腐块；G5 对照平均差异 60.21%（语音/正在播放 90%+）

## 复现（怎么稳定重现）

EEZ headless build 后跑 sim.py 出图即可稳定复现（工程 settings.general 无 darkTheme 字段时，EEZ 生成 lv_theme_default_init(..., false, ...)）。

## 根因（真正的原因）

lv_theme_default.c:740-800：tabview 主对象挂 styles.scr(浅色)、tab 栏容器挂 bg_color_white(纯白)、按钮 CHECKED 挂 primary_muted(浅蓝)、文字用 Montserrat 无中文字形。这些是 EEZ 生成的内部对象，不在 DSL 控件树里，json2eez 的 localStyles 摸不到

## 修复（做了什么）

初版：design/fix_tabview.py 生成后处理（lv_tabview_get_tab_bar/get_content 公开 API 压回深色，幂等 [fix_tabview] 标记），G5 60.21%→8.99%。
**终版（P-0025）**：废除补丁，EEZ 原生三件套——json2eez 写 settings.general.darkTheme=true + lv_conf.h LV_FONT_DEFAULT 指向烘焙 13px + tabName 直接写 FA 图标字符。fix_tabview.py 已删除，all.py 已摘除该步。

## 证据（数字 / 命令输出）

初版：三联图修复前热力图整屏红，修复后 8.99%。终版：screens.c `lv_theme_default_init(dispp, BLUE, RED, true, LV_FONT_DEFAULT)`，G5 见 P-0025/P-0027 演进链（最终 8.84%）

## 沉淀（新增断言 / 案例 / 文档）

skills.md §11.6（EEZ 原生主题三件套）、§11.7/§11.8（tab 栏形态后续演进）；index.md 状态同步 fixed
