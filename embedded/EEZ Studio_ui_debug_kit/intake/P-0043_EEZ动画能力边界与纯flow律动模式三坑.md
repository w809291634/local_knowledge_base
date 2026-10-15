# P-0043 EEZ 动画能力边界与纯 flow 律动模式（Loop+Delay+SET_PROPERTY 三坑）

- **状态**：fixed
- **发现日期**：2026-10-01
- **提示词**：PR-0071~PR-0077（用户看官方 eez_lvgl_demo 实证「Run 模式预览有动画」）
- **标签**：EEZ-flow, 动画, Loop, Delay, SET_PROPERTY, 预览, Run模式, double陷阱, LVGL

---

## 一、能力边界（先查手册 + asar + 用户实证，三方闭环）

| 途径 | 循环 | 可停 | Run 预览可见 | F7 全仿真器 | 真机 |
|---|---|---|---|---|---|
| PLAY_ANIMATION（Anim Y/Width/Height/Opacity/ImageZoom/ImageAngle） | ✗ 一次性 | ✗ 无停止动作组件 | 静态画布 ✗ | ✓（需 Docker） | ✓ |
| **Loop+Delay+SET_PROPERTY 循环链**（官方 eez_lvgl_demo 同款） | ✓ | ✓（帧级 IsTrue） | **✓ Run 模式真实执行** | ✓ | ✓ |
| Animation timeline + A2 Animate | Dashboard 专用，LVGL codegen 不消费（运行时只发调试消息） |

- 手册 A43（P.215–221）Anim\* 只有 Start/End/Delay/Time/Relative/Instant/Path——无 repeat、无停止。
- **Run 模式预览会执行 flow 并实时刷新画布**（旧结论「预览不执行运行时」作废；
  准确说法：预览执行 flow，但不模拟真实 LVGL 交互事件——滑动 SCROLL_END/
  VALUE_CHANGED 链在预览不发生、native 变量不反映）。
- F7 全仿真器（Settings→Build→UseDockerDesktop 勾选后出现）：Docker+Emscripten
  编真 LVGL 成 WASM；**只拷 uiDir（生成代码目录），不含 src/native**。

## 二、纯 flow 律动链结构（可直接照抄）

```
CLICKED → SetVariable(np_playing = 1 - np_playing)
  → IsTrue(np_playing)
     True  → Loop i0(0..1e9, step1)            # ≈无限外层
               body: Loop kg(0..27, step1)      # 扩散相
                 body: FRAME(SET_PROPERTY×11) → Delay 30
                       → IsTrue(np_playing) True→kg next / False→RESET   ★帧级可停
               → Loop ks(27..0, step-1)         # 回缩相（step 负数原生支持）
                 body: FRAME_S → Delay → IsTrue …
               → ks done → i0 next
     False → RESET（暂停点击立即复位）
```

- 两圈半相位错位不用并行链：ring2 的位移表达式传 `(27 - kg)`（三角波取反）。

## 三、三个必踩坑（全实测）

1. **Loop 输入端口是 `start`(0)/`next`(1)，没有 `@seqin`**；`done→start` 自环 =
   无限循环；停止 = 帧级 IsTrue 走 False 分支后不再回 next（链自然熄灭）。
2. **`/` 和 `%` 永远返回 double**（eez-flow.cpp MOD 实证返回
   VALUE_TYPE_DOUBLE）——位型塞进 objSetY 等整数动作 = 垃圾坐标
   （实测 disc_y=0x66666666）。**帧表达式必须纯整数**；阶梯波用嵌套三目
   （CONDITIONAL 是整数安全运算）。
3. **停止检查（IsTrue）必须放内圈帧级**——放外层循环一次要等 1.68s 才发现
   暂停；且 disc 类「每帧一条」的动作别塞进会被调用两次的 helper（两条
   SET_PROPERTY 互相覆盖，末条生效）。

## 四、证据

eez-test 唱片律动：all.py --shots EXIT=0；[np] playing orbit_w=104/disc_y=55、
stopped 96/58 精确复位；11 屏对照 8.65% 无回归；Studio Run 模式预览由用户验收。
官方参照工程：`C:\Users\Administrator\eez-projects\examples\eez_lvgl_demo`
（其动画 = Start → Loop(0→3600,70) → SET_PROPERTY(IMAGE_ANGLE) → Delay 50）。
