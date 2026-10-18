# P-0147 · LVGL 9 子件恒被裁到父框，OVERFLOW_VISIBLE 只扩 ext_draw_size——"放大越界变方"必须换载体

- **工程**：watch (Design Watch)
- **日期**：2026-10-18
- **工具**：Qoder
- **状态**：fixed
- **标签**：lvgl,裁切,overflow_visible,transform_scale,结构坑,心跳
- **关联提示词**：PR-0247

## 现象（看到什么）

AppList 心率行心跳搏动到峰值时，红色圆盘四边被切平=圆角正方形（用户截图"放大之后边框
变为正方形"）；静息帧正常。构建 0 错 0 警、Checks 干净、nav_audit PASS——纯视觉静默坑。

## 根因（真正的原因）

盘=76×76 位图（circle_icon 满幅圆底）嵌在 76×76 容器 ib_ 内，flow 给位图写
transform_scale 峰值 275/256=1.074 → 81.6px > 父框。LVGL 9 子件绘制恒 intersect 到
父件 coords(+ext_draw_size)（lv_refr.c:140、lv_obj_pos.c:914 源码实证）；
LV_OBJ_FLAG_OVERFLOW_VISIBLE **只把裁切区扩 ext_draw_size（阴影/边框级几像素）**，
不允许子件真正越界。实测：给 ib_ 挂 OVERFLOW_VISIBLE（EEZ 旗标枚举确有此项、
codegen 出 add_flag）截图复测仍切平。

## 修复（做了什么）

载体重构：盘位图/姿势帧/特效叠层从 ib_ 容器**提为行容器的直接子件**（行高 100px=裁切
上限，盘有效尺寸 ≤92 永不切）；原本由父继承的滚轮曲线缩放并入 ic 自身表达式
（曲线×增量嵌套 → 单写曲线+增量，静息 280/峰 299 逐点等价）；旋转/摆动/位移通道
ib_→ic_ 改指；ib_ 留空承载框兼容 hearttest A1 采样点。hearttest 判据参数化静息基线
（AppList ic 256→280）后 ALL PASS，gesturetest 14 断言 ALL PASS，峰值帧复测正圆。

## 证据（数字 / 命令输出）

hbshot 夹具：修复前 peak ic=275 切方；修复后 peak.png 正圆、ic scale 域 280..299；
hearttest `ALL PASS (fails=0)`；gesturetest `ALL PASS (fails=0)`。报告 §49。

## 沉淀（新增断言 / 案例 / 文档）

skills §11.44（裁切语义+载体重构配方+"逐项对照实拍"纪律——本轮曾把 BPM 穿字误判为
针太长，收短指针后回滚）。夹具 verify/hbshot_main.c 留档（峰值帧截图法）。
