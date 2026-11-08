# P-0266 · F3 未核源字库 cmap：•/‹ 在 simhei.ttf 无字形，EEZ 官方字体烘焙直接 FAIL

- **工程**：redblue_p4
- **日期**：2026-11-08
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：字体,cmap,F3,D3,字形
- **关联提示词**：PR-0614

## 现象（看到什么）

生成器把设计源全部文本码位写进 fonts[].lvglRanges 后跑 eez_font_bake.py，报 FAIL: Font simhei.ttf doesn't have any characters included in range 0x2022-0x2022。

## 复现（怎么稳定重现）

设计图用微软雅黑绘制 ••••••• 与 ‹ 返回；EEZ 侧 device_ttf 用 simhei.ttf，两字库 cmap 不同；生成字体前不核 cmap。

## 根因（真正的原因）

NO_FLOW §3.2 F3 明写「先核源字库 cmap，‹ › − ▶ ◀ 先替换再写 encodings」；本轮只按文本取码位，漏了这一步。PIL 设计图字体与 EEZ 烘焙字体不是同一套，不能假定字符集相同。

## 修复（做了什么）

用 fontTools 读 simhei.ttf cmap 列出全部缺失字符（仅 U+2022 • 与 U+2039 ‹），按 F3 建替换表 •→*、‹→< 并全局同步 design_view.py / controls.py / export_design_source.py / overview_pro.py；在 build_ui.py 加 assert_cmap() 前置硬门禁，缺字形当场 FAIL 并列出码位。

## 证据（数字 / 命令输出）

重建后 cmap 28522 码位 F3 PASS；EEZ 官方引擎烘出 cn16/cn20/cn64 三档（253146/359574/2896275 bytes）；gcc -fsyntax-only 7/7 PASS。

## 沉淀（新增断言 / 案例 / 文档）

固化断言：生成 fonts[] 之前必须核 device_ttf 的 cmap；替换表落设计源，禁止只在生成器里静默剔除。
