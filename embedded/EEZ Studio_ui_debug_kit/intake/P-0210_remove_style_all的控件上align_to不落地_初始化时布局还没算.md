# P-0210 · remove_style_all 的控件上 align_to 不落地；初始化时布局还没算

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-25
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,布局,align_to,remove_style_all,初始化时序
- **关联提示词**：PR-0384

## 现象（看到什么）

给密码框右端加「眼睛」按钮，`lv_obj_align_to(eye, pwd_ta, LV_ALIGN_RIGHT_MID, -6, 0)` 之后，
眼睛画在了输入框中间偏左（图标中心 x≈315，期望 353），`lv_obj_get_x(eye)` 还打印 0。

## 复现（怎么稳定重现）

在 `user_io_init()`（EEZ 刚建完屏、还没跑过布局）里建一个 `lv_obj_remove_style_all` 的控件，
再用 `align_to` 对齐到同级的 `objects.pwd_ta`：位置不对或停在 0,0。

## 根因（真正的原因）

两条叠加：
1. `lv_obj_align_to` 写入的是**对齐样式**，要等下一次布局才生效，而 `get_x` 读的是布局缓存 →
   初始化阶段读到的还是 0；同一帧里再算位置就只能拿错值；
2. 控件被 `remove_style_all` 之后没有样式承载，实测对齐结果不落地（同一父子树下也一样）。

## 修复（做了什么）

先 `lv_obj_update_layout(objects.sheet)`，再按输入框的实测矩形显式 `set_pos`：
`x = get_x(ta) + get_w(ta) - EYE_W - 6`，`y = get_y(ta) + (get_h(ta) - EYE_H)/2`。

## 证据（数字 / 命令输出）

修前图标像素 x=308..323；修后 x=345..360（输入框边框 12..367）；`[NAV] 64/0`、`PREFLIGHT PASS`。

## 沉淀（新增断言 / 案例 / 文档）

**"跟随某个控件定位"的运行时控件，别依赖 align_to 的时序**：先 `lv_obj_update_layout`，
再拿对方的实测矩形自己算；并且把"位置对不对"写成断言（本例断言眼睛落在输入框右半），
否则它画歪了也没人发现。
