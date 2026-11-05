# P-0225 · Wi-Fi 列表动态中文全是豆腐块：设计期字体子集盖不到运行时 SSID

- **工程**：w78-tabview-smart-home
- **日期**：2026-11-05
- **工具**：Qoder
- **状态**：fixed
- **标签**：字体,子集,GB2312,运行时文本,Wi-Fi,SSID,LVGL,豆腐块
- **关联提示词**：PR-0506

## 现象（看到什么）

⑦-2 把真实扫描结果写进 Wi-Fi 列表后，中文 SSID（`YJT-1号楼办公`、`1号楼6层WiFi`）显示为方框；
运行时新建的「已连接 / 已保存」胶囊也是方框；副标题里的 `·` 也是方框。

## 复现（怎么稳定重现）

`design\sim_cmake\run_sim.bat uitest`：真 wlanapi 扫描 → 写 5 行 →
`designer_annotated/wifi_ui.png` 里中文 SSID 与徽标全是 ▯。

## 根因（真正的原因）

1. 字体是按**设计帧文本**裁的子集（`charset()`），SSID 属于运行时数据，字符不在子集里；
2. native 用 `lv_label_create` 新建的徽标标签没设字体，走默认 Montserrat（无 CJK）；
3. 把 24px 做成 GB2312 全字库后，C 数组索引超过 1,048,575，触发
   `#error "Too large font ... Enable LV_FONT_FMT_TXT_LARGE"`。

## 修复（做了什么）

- `design/eez_gen.py`：新增运行时字库档 `cn12f`（行文本）与 `cn24f`（标题）：
  同一 TTF 再烘 GB2312 A1–D7 区 + ASCII + **U+00B7**（GB2312 A1A4 是 U+30FB，不是中点）；
  TTF 烘成「设计字符 ∪ 运行时字符」。
- 设计源里让 Wi-Fi 行/标题标签**引用** `cn12f`/`cn24f`（否则 EEZ 不导出这两个 `.c`）；
  native 新建的徽标、错误行、密码输入框显式 `lv_obj_set_style_text_font`。
- `design/sim_cmake/lv_conf.h` 与 `design/lv_conf.h` 均置 `LV_FONT_FMT_TXT_LARGE=1`。
- 门禁 D3 从「条目数==字号数」改为「每个字体条目都有 `ui_font_*.c`」（同字号允许多档）。

## 证据（数字 / 命令输出）

- 真网卡扫描 12 个 AP，5 行全部中文正常，徽标「已连接/已保存」正常；
  截图 `designer_annotated/wifi_ui.png`（`[WIFI_UI] count=12`）。
- 字体 18 条 / 16 个字号；`ui_font_cn12f.c` 2.1MB、`ui_font_cn24f.c` 6.3MB；
  D3 PASS，D4 语法检查 22 个文件全过，D1–D8 全 PASS。

## 沉淀（新增断言 / 案例 / 文档）

- NO_FLOW §3.2 新增 **F7**（运行时中文单独字库档 + LARGE），D3 行同步；
  `reference/07` 字体节补做法与坑。
- 代价记账：cn12f+cn24f 源码约 8.4MB，固件需按实际可用字符再裁（等级/白名单）。
