# P-0168 · lv_list_add_button 的 label 默认 SCROLL_CIRCULAR：新建时 coords=0，跑马灯动画当场启动且停不下来

- **工程**：app-wifi-connect2（v3 List 方案）
- **日期**：2026-10-21
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：lv_list,add_button,SCROLL_CIRCULAR,跑马灯,label,long_mode,coords,动画,截图动检
- **关联提示词**：无

## 现象（看到什么）

Wi-Fi 扫描列表里，**每行的 SSID 名称在横向自动滚动**（像电视新闻跑马灯），
停不下来；副行（类型·dBm·频段）与状态文字（已连接/已保存）都正常不动。
列表的垂直滚动是正常的，名称是在自己行内左右移动。

## 复现（怎么稳定重现）

app-wifi-connect2 v3，仿真器 autoscan 出列表后观察任意一行名称。
无头实锤（连拍 diff 法）：scan done 后拍 shot_a，~1s 后拍 shot_b，
PIL `ImageChops.difference` 对比——SSID 文字带（x≥60，y≈74-85/116-129/
161-173/206-218/251-263/296-306，即每行 TXT_X 之后的区域）像素持续变化，
修复前 diff bbox=(60,74,151,306)，72 行有变化；修复后 0 像素变化。

## 根因（真正的原因）

三个事实叠出一个必踩坑：

1. `lv_list_add_button()`（apl_lvgl_v9_4/src/widgets/list/lv_list.c）给自带的
   文字 label 设了 **`LV_LABEL_LONG_MODE_SCROLL_CIRCULAR`**（跑马灯）。
2. `lv_label_refr_text()` 用 **当前 coords** 与文字宽比较来决定是否启动画：
   ```c
   lv_obj_get_content_coords(obj, &txt_coords);
   ...
   if(size.x > lv_area_get_width(&txt_coords)) { /* 启动无限重复动画 */ }
   ```
   而**新建对象当拍 coords 还是 0**——`lv_obj_set_size()` 不同步 coords，
   coords 要等下一轮 layout（渲染期 `lv_obj_update_layout`）才生效。
   于是 `add_button` 内部 `lv_label_set_text()` 触发的 refr_text 看到
   "文字宽 84 > 盒宽 0" → **当场启动无限滚动动画**。
3. 之后 `build_row` 再 `set_size(230)`、首帧布局刷新把 coords 补成 230，
   **都不会重跑 refr_text**（布局驱动的 coords 变更不发 SIZE_CHANGED）→
   CIRCULAR 分支里"文字放得下就 lv_anim_delete"的自止逻辑没机会执行 →
   **动画永远转**。

同类陷阱推广：**任何在新建当拍依赖"当前宽度"的求值都会拿到 0**——
DOTS 模式会按 0 宽把文字截成"…"（文字被写坏），SCROLL* 会误启动画。

## 修复（做了什么）

`src/native/wifi_ui_sync.cpp` `build_row()`：复用 add_button 的 label 后，
显式改 long mode（一行 + 注释）：

```c
lv_obj_set_pos(ssid, TXT_X, 6);
lv_obj_set_size(ssid, 230, 16);
lv_label_set_long_mode(ssid, LV_LABEL_LONG_MODE_CLIP);  /* 杀掉默认跑马灯 */
```

为什么是 CLIP 而不是 DOTS：

- `lv_label_set_long_mode()`（lv_label.c:231-234）**内部先
  `lv_anim_delete(set_ofs_x_anim/set_ofs_y_anim)` 并把 offset 归零**——
  换 mode 这个动作本身就会停掉旧动画；
- refr_text 的 CLIP/WRAP 分支是**空操作**（`/*Do nothing*/`）：纯绘制期
  按 coords 裁剪，永不起动画、永不改文字缓冲区，超长名字在 230px 盒边裁掉；
- **DOTS 在 9.4 只管垂直溢出**（`size.y > height && size.y > line_height`），
  单行超宽不截断也不加"…"，绘制期也不做横向裁剪 → 不可用。

## 证据（数字 / 命令输出）

- 修复前（默认 SCROLL_CIRCULAR）：`WIFI_AUTOSCAN=1 WIFI_SHOT2=1` 连拍 diff，
  bbox=(60,74,151,306)，72 行像素变化；
- 修复后：同法 diff，`total changed pixels: 0`，`changed bbox: None` → PASS；
- 截图目视：12 行名称完整、静止、位置正常（x=44 起，未被裁）。

## 沉淀（新增断言 / 案例 / 文档）

- 新机器检查建议：自绘/生成代码里凡**复用 `lv_list_add_button` 的 label**，
  必须显式 `lv_label_set_long_mode`（默认值是雷）；
- 新检测法：**截图动检**——间隔 1s 连拍两张 diff，任何"静止 UI"都可用来抓
  潜伏动画（本次靠它实锤，比单张截图可靠）；
- 关联：P-0166（List 方案三坑）同属 add_button 家族，本条补第四坑；
  P-0164 坑 16 坐标空间的推论在这条面前 again 不成立——coords 不是设了就生效。
