# P-0025 · tabview 主题/字体需运行时补丁？实测 EEZ 原生三件套即可：darkTheme 字段 + LV_FONT_CUSTOM_DECLARE + tabName 图标字符

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio 0.29
- **状态**：fixed
- **标签**：EEZ原生,主题,字体,tabview,fix_tabview废除
- **关联提示词**：PR-0038

## 现象（看到什么）

tabview 深色主题、中文/图标 tab 标签、rail 图标此前全靠 fix_tabview.py 在生成后的 screens.c 里注入 C 补丁；用户要求纯 EEZ 路线

## 复现（怎么稳定重现）

反编译 EEZ Studio resources/app.asar 里的生成器模板（唯一命中 lv_theme_default_init(dispp）

## 根因（真正的原因）

EEZ 0.29 生成器：lv_theme_default_init(dispp, LV_PALETTE_BLUE, LV_PALETTE_RED, dark 参数取自工程 settings.general.darkTheme, LV_FONT_DEFAULT) —— dark 可配，主/次色硬编码不可配；字体走 lv_conf 的 LV_FONT_DEFAULT

## 修复（做了什么）

① json2eez 写 settings.general.darkTheme=true（EEZ 原生 dark 主题）；② design/lv_conf.h 用 LVGL 官方口子 LV_FONT_CUSTOM_DECLARE + LV_FONT_DEFAULT 指向烘焙 13px 混合字体（tabName 中文/图标原生可渲染；真机 ESP-IDF Kconfig 无此入口，需固件 main 在 ui_init 后补一次主题 init）；③ json2eez 对 m_tab_* 的 tabName 直接写 FA 图标字符（字形烘进 13px）；④ 删除 fix_tabview.py 并从 all.py 移除。G5 8.74%→24.39%，差值全部来自原生均分整格按钮 vs 设计稿图标块/紧凑行的形态差，属可接受取舍

## 证据（数字 / 命令输出）

screens.c:9372 lv_theme_default_init(..., true, LV_FONT_DEFAULT) 为 EEZ 原生输出；grep fix_tabview 0 残留；拼版 11 屏 rail 图标/中文标签/深色全正常

## 沉淀（新增断言 / 案例 / 文档）

skills.md §11.5 后追加 §11.6：EEZ 原生主题三件套 + EEZ 预览是静态渲染，darkTheme/LV_FONT_DEFAULT 等运行时参数预览里看不到，验收以仿真图为准
