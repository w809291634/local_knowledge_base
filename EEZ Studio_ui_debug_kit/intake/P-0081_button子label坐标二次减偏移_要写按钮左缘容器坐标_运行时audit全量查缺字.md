# P-0081　button 子 label 的 DSL 坐标会被「二次减偏移」——要写按钮左缘的容器坐标，不是相对按钮的 (0,y)

- **日期**：2026-10-02
- **现象**：真机（仿真同样）密码面板「取消 / 连接」两个按钮**没有文字**。
  用户先报「键盘中按钮没有文字」，实际是确认/取消按钮。
- **误判过程**：
  1. 先猜 15px 字体缺「取/连」字形 → 写 `_font_cov.py` 全量比对静态文本 vs
     烘焙字体 `--range`/`--symbols` → **OK 全覆盖**（EEZ 把 label 静态文本也烘进
     `--symbols`）。推翻字形假设。
     ★ `_font_cov.py` 的 `--range` 正则要在第一个 `--` 处截断（`--symbols` 段里的
     字面字符如 `38899--` 不能收进码点集），否则假绿。
  2. 走路器 `tree m_btn_6` 报「没有对象」→ 改 `tree pwd_panel 2` 从面板往下看，
     拿到按钮子 label 相对坐标：`rel(-18,-110)` → 生成代码
     `lv_obj_set_pos(label, -18, -110)`，label 画到屏幕外。
- **根因**：EEZ 生成的 button 子 label，最终
  `lv_obj_set_pos(label) = DSL label pos − parent button pos`。
  即 **DSL 里 label 坐标被按「相对按钮的父容器」解释**。写 `label_mid(0,0,...)`
  （以为相对按钮居中）→ 被再减一次按钮自身 pos → 负坐标飞出屏幕 → 看起来没文字。
  生成代码证据：修复前 `m_t_139 → lv_obj_set_pos(obj, -18, -110)`。
- **修法**：label 坐标传**按钮自己的左缘 x + 居中补偿**（容器基准坐标），减完正好
  相对按钮居中。两个按钮左缘不同，不能共用同一个 x（写死第一个按钮的 x 会让
  右边按钮的文字整体左偏）：
  ```python
  def btn_cx(base_x, txt):
      return base_x + (bw - tw(txt, 14)) / 2.0   # base_x = 该按钮自己的左缘
  cancel = button(cancel_x, btn_y, bw, bh, None,
                  [label_mid(btn_cx(cancel_x, "取消"), btn_y, bh, "取消", 14, TEXT2)], ...)
  ```
- **验证**：修复后生成 `lv_obj_set_pos(118, 13)` / `(119, 13)`；walk 截图放大
  「取消 / 连接」文字都在；`all.py --sim` 9.30% PASS。
- **全量排查（用户要求「检查所有的」）**：
  - 字形覆盖：`design/_font_cov.py` → 3688 字符全 OK，**无缺字**。
  - 位置越界：静态 DSL 累加坐标脚本（`_label_bounds.py`）**254 条全是假阳性**
    （tabview 非活动页/滚动区/浮层位置还原不了），已删除，**别再用静态法判越界**。
  - ★ 可信法 = **运行时 audit**：走路器新增 `audit [obj]` 命令（sim.py），从屏幕根
    DFS，用 `lv_obj_get_coords`（真实渲染矩形，tabview/滚动下也准）+
    `lv_obj_is_visible` 过滤隐藏对象，列出所有 text/空label/空按钮，可见的空文字
    对象计数。走路脚本 `audit_all`：逐 rail 页（nav_chat/nav_music/nav_bell/
    nav_tune）→ WiFi 列表 → 密码面板，每态 `audit` + `shot`。
    解析：`design/_audit_report.py build/walk_audit.log`。
  - 结果：6 态 339 个可见文字对象，唯一 `vis=1` 的空 label 是 **textarea 内部
    placeholder label**（LVGL 自建、不在 objects_t，空密码时本来就该空），
    其余空 label 全 `vis=0`（绑变量、未赋值、隐藏）→ **除已修的取消/连接外无缺字**。
- **走路器连带坑**：
  - `objects_t` 正则要写 `typedef struct\s*\w*\s*\{` —— EEZ 生成的是
    `typedef struct _objects_t {`（带 tag 名），漏了会静默走「跳过自动对象表」。
  - write_main() 现在把 screens.h 的 ~650 个对象名**全部自动登记**进 wmap
    （`__WMAP_AUTO__` 占位符替换），audit/tap/tree 报的都是 EEZ 真名。
  - 切页必须 `tap nav_chat / nav_music / nav_bell / nav_tune`（layer0 rail 按钮），
    `tab ai/set` 落在隐藏的 tabview 容器上切不过去。
