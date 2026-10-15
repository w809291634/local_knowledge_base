# P-0026 · EEZ tab 栏原生定制：首子容器样式发射到 lv_tabview_get_tab_bar（rail 两行标签 / 设置左栏紧凑行）

- **工程**：eez-test (LVGL 9.4 / 800x480)
- **日期**：2026-09-28
- **工具**：WorkBuddy+EEZ Studio 0.29
- **状态**：fixed
- **标签**：EEZ原生,tabview,样式,tab栏,字体继承,布局
- **关联提示词**：PR-0039

## 现象（看到什么）

P-0025 纯 EEZ 路线落地后仍有三处难看：① rail 图标以 LV_FONT_DEFAULT=13px 渲染明显偏小（设计稿 ~20px）且无文字；② 设置左栏 4 个 tab 按钮被均分成 206×111 实心蓝块（设计稿 44px 紧凑列表行）；③ 顶部导航标签 13px（设计稿 15px）。

## 复现（怎么稳定重现）

反编译 app.asar 的 LVGLContainerWidget.toLVGLCode + 读本机 LVGL 9.4 lv_tabview.c 源码。

## 根因（真正的原因）

两条实锤：① EEZ 的 LVGLContainerWidget 若是 tabview 的**第一个子对象**，生成器不为它创建对象，而是把它的 localStyles 发射到 `lv_tabview_get_tab_bar()` 上（第二个子对象 → `lv_tabview_get_content`）——这是 EEZ 内置的 tab 栏定制口子；② LVGL 9.4 `lv_tabview_add_tab` 建 tab 按钮是 `lv_button` 且 `lv_obj_set_size(button, 100%,100%)` + `flex_grow(1)`——按钮永远填满按钮栏，按钮栏 446px 高就被均分成 ~111px 整格；按钮 label 不设字体，沿「按钮 → 按钮栏」继承 text_font（text_align 亦是可继承属性，lv_style.c:126 实证）。

## 修复（做了什么）

json2eez 新增 `inject_tabbar_styling()`：在 DSL 树上给每个 tabview 前插一个空 container（id=tabbar_*，x/y=父 tabview 绝对坐标，防 check_bounds 负坐标），样式表 `TABBAR_STYLE_BY_ID`：rail(m_main_nav) text_font=17px 混合字体 + text_align=CENTER；ai/mus/set_nav text_font=15px；m_set_nav 另加 pad_top=8/pad_row=10/pad_bottom=210（把 446px 按钮栏收成 ~50px 紧凑行）+ bg_color=0x0A0C11。同时 rail tabName 改「图标字符+\\n+中文」两行（混合字体同含 FA 与中文字形，一个 label 两种字形）。字形同步收进 15/17px 主字体与 13px 兜底字体（LV_FONT_DEFAULT），任何一环失效不出 tofu。顺带修 build_ui Home-5G 副标题被「测得延迟 12ms」胶囊遮挡（文本过长，缩短为「已连接 · IP 192.168.1.24」）。

## 证据（数字 / 命令输出）

screens.c:248/6256 生成 `lv_tabview_get_tab_bar(parent_obj)` + `lv_obj_set_style_text_font(obj, &ui_font_ya_hei_consolas_hybrid_17/15,...)` + `pad_row/pad_bottom/bg_color`，全部 EEZ 原生输出（No error and no warning）。`all.py --sim` 11/11 屏通过，**G5 平均明显差异 24.39% → 17.10%**（设置四屏 13-14%）。3 倍放大裁剪核对：rail 图标+文字两行居中、设置左栏紧凑行、Home-5G 无遮挡。

## 沉淀（新增断言 / 案例 / 文档）

skills.md 新增 §11.7（tab 栏定制口子 + LVGL tabview 按钮填满机制 + 可继承样式清单）
