# 15 Wi-Fi 列表/连接页：直接移植成熟参考实现

> 触发词：Wi-Fi 扫描、Wi-Fi 连接、密码页、忘记网络、连接中、配网列表。
> 遇到这些需求**先读本篇并移植**，不要从零设计交互，也不要拆成「列表页 + 密码页 + 连接中页」三屏。

## 参考实现

`<EEz_stidio_examples 仓库根>/app-wifi-scan-conn-no-flow`

本机仓库根因机器而异，用前按实际路径定位；找不到就先问用户要路径。
它是 PC 真 wlanapi + 真机双后端的完整样板，结构与交互都验证过。

## EEZ 页面结构（一页）

| 对象 | 类型 | 作用 |
|---|---|---|
| `lbl_status` | label | 状态文案（已发现 N 个 / 正在连接 X… / 已连接 X） |
| `btn_refresh` | button | 发起扫描；扫描中禁用 |
| `list_box` | LVGL List | **空列表**，行全部由 native 动态建（可滚动） |
| `overlay_root` | container（默认隐藏） | 密码半页：`scrim` + `sheet`（`lbl_pwd_ssid`、`btn_pwd_close`、`pwd_ta`、`btn_connect`、`kb_main`） |
| `dlg_root` | container（默认隐藏） | 忘记确认：`dlg_scrim` + `dlg_card` + 忘记/断开/取消 |

半页与对话框都挂**屏幕根**，不要塞进列表容器（会被裁剪、坐标二次偏移）。

## native 分层（照抄目录）

```
app/        wifi_events（动作→命令）wifi_logic（每拍排空/平台推进）wifi_view（状态文案/密码读取）
navigation/ wifi_nav（半页/对话框显隐与动画）wifi_bind（no-flow 的按钮回调）
widgets/    wifi_list（动态行）wifi_busy（连接中遮罩+转圈）wifi_eye（按住看密码）wifi_skin.h（配色）
platform/   wifi_platform.h + pc（wlanapi/假世界）+ device
```

- 行：信号条 + SSID + 「加密 · dBm · 频段」 + 状态；排序 **已连接 → 已保存 → RSSI 降序**，组间插分隔线。
- 手势：点行——已保存/开放直连，有锁未保存开半页；长按已保存行开忘记框。
- 连接：收半页 → 全屏 busy（挡住一切）→ 结果写标题栏；密码 8–64 位，空密码就地提示不发起。

## no-flow 改造点

1. 示例用 EEZ action 挂回调；no-flow 不生成 action，统一在 `navigation/wifi_bind.cpp` 用
   `lv_obj_add_event_cb` 挂（按钮/遮罩/对话框）。
2. 多屏工程：busy 遮罩必须挂 `lv_layer_top()`（示例单屏才挂 `objects.main`）。
3. `lv_snapshot` 只拍当前 screen、不含 layer_top：busy 证据用可见性断言或整窗截图。
4. 动态中文（SSID/状态）要 GB2312 运行时字库档（`cn12f`/`cn24f`）+ `LV_FONT_FMT_TXT_LARGE`。

## 验证四件套

1. 假后端流程：`WIFI_PC_FAKE=1` 扫描→开半页→密码→连接→列表置顶标已连接（不改真实网络）。
2. 真接口扫描：`run_sim.bat wifitest` 打印真实 AP 列表（SSID/加密/RSSI/频段/保存态）。
3. 导航：`run_sim.bat test` 逐边真点击，全 PASS。
4. 样式：D5 画布相似度；Wi-Fi 页默认态是**空列表**，行内容由仿真截图另行取证。

## 坑（都踩过）

- 行容器必须带 `SCROLL_CHAIN_VER`，否则列表滚不动。
- LVGL keyboard 构造函数强制 `BOTTOM_MID`，必须先改 `TOP_LEFT` 再设坐标。
- textarea `oneLineMode` 会把高度改成内容高，靠上下 pad 撑设计高度。
- 长按抬手后普通按钮还会补发一次 `CLICKED`，要吞掉否则"先开对话框再直连"。
