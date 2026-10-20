# B14 腕表图标动画（GIF 存文件系统路线）：小人动画六轮被否后定稿「开源动画 + 官方渲染帧 + 位图后处理」链路

## 现象

AppList 图标需要动起来：`sport_mode`（运动模式）图标 = lime 圆底 + 跑步小人，
要求 **外圆静止、只有小人动**，观感对标 Apple Watch 跑者动图（用户给了截图基准：
lime 圆 + 白色粗壮剪影、身体前倾）。图标 76×76，最终产物进 LVGL 播放
（GIF 存文件系统路线，`watch/fs/anim/`）。

## 证据

最终定稿的量化验证（`design/_tmp_final_render.py` 内置强制断言，交付前自动执行）：

- 帧序列一致性：读回 GIF 逐帧 `tobytes()` 与期望序列**逐字节相等**
- 时长守恒：读回各帧 duration 求和 = 360ms = 写入值（GIF 帧延迟粒度 10ms，取值 40ms 无取整误差）
- 唯一帧数：9/9（无重复帧被去重）
- 居中度量：逐帧白色像素质心相对圆心 (38,38) 偏移 -2.0~+1.1 px（残差为步态自身摆动）
- 外圆零位移：色键包围盒逐帧检测（早期版本即已建立的方法）

## 曾经的误判（六轮被否 + 三个技术坑，全部有实证）

**内容方向被否（观感层）：**

1. **程序化骨骼小人**（PIL 画双段腿+屈膝公式）：线宽细像火柴、粗了四肢粘连成"黑坨"——
   76px 上程序化人形的笔宽/缝隙没有同时满足的窗口。
2. **AI 生成 sprite sheet 切帧**：姿态是专业的，但 4 帧循环卡顿感明显，且 AI 风格与
   图标体系不统一。
3. **icons.py 既有 RUNNER_POSES 三帧 ping-pong**：姿态还原视频但帧少。
4. **Emoji 跑者 🏃**（Segoe UI Emoji 渲染）：彩色小人与剪影系图标风格冲突。
5. **抽象动效**（速度线/同心弧 spinner）：被否，用户要"人"。
6. **静态图标 + 整体 wiggle/bounce**：观感是"图标活了"不是"人在跑"——四肢本身不动
   （单体 SVG 无关节），被否。

**技术路线被否（渲染层，本案例最值钱的部分）：**

7. **python-lottie 的 SVG/cairo 导出器丢失旋转插值**：
   源动画 60fps/37 帧，渲染出 36 帧里**只有 3 个唯一画面**（肢体旋转全丢，
   只剩位置类关键帧）。更糟的是交付时没验帧数，"36 帧动画"实为 3 帧幻灯片
   → 用户"你自己核对一下，明显就是不行的"。
8. **rlottie 引擎（rlottie-python）渲染该动画产生纯黑残影层**：帧 12 起肢体旁出现
   与主剪影同灰度的重影，阈值法（240→150 两轮收紧）无效——残影是纯黑级别。
9. **Pillow 12.3 GIF 保存会对相邻内容相同帧去重**：`_getbbox(previous_im, im_frame)`
   判定相同则丢弃后帧、duration 累加到前一帧（源码
   `GifImagePlugin._write_multiple_frames` 实证）。36 帧写出去只剩 3 帧。

## 真因

三层独立问题叠加，任何一层不解决都出不了可交付动画：

1. **内容层**：76px 下"像人跑步"的姿态无法靠参数化公式达到专业水准——姿态质量
   只能来自**设计师调好的动画数据**（开源动画库），程序生成只适合抽象图形。
2. **渲染层**：Lottie→帧 的第三方 Python 绑定都不完全可靠（python-lottie 丢插值、
   rlottie 加残影）；**作者上传的官方渲染 GIF 才是唯一干净的帧源**。
3. **编码层**：Pillow 会静默去重 GIF 相邻同内容帧 + GIF 帧延迟只有 10ms 粒度——
   不做预合并与读回校验，产物帧数/节奏会静默失真。

## 修法

定稿链路（`design/_tmp_final_render.py`，全部位图后处理，零矢量渲染依赖）：

```
官方渲染 GIF（LottieFiles 下载，作者 Larry double「Stickman running」，
             Lottie Simple License 免费商用）
  → 逐帧 RGB，深色阈值掩码取剪影（r+g+b < 380）
  → 全帧联合 bbox 裁剪（统一框防抖动）
  → MaxFilter(7) 轻膨胀（+3px 粗壮感；≤13 会把手臂贴脸的帧粘成块）
  → 染白 RGBA（putalpha 回写掩码）
  → 全帧联合质心计算 → 质心钉在圆心 (38,38)（bbox 居中 ≠ 视觉居中）
  → 前倾 8°：rotate(-8, expand=True) + 画布中心补偿贴图
  → lime 圆垫底 + 黑底 RGB
  → 9 唯一帧 × 40ms（GIF 粒度 10ms 的整数倍，零取整误差）
  → 保存后强制读回校验（帧序列逐字节 / 总时长 / 唯一帧数三断言）
```

关键防回归点：
- **相邻重复帧预合并**（`tobytes()` 对 `merged_b[-1]` 比较——注意 `bytes == Image`
  永远 False 的低级坑，必须缓存 bytes 比较）；
- **保存后读回断言**：`assert got == expect`（期望序列须用量化后帧生成，
  用未量化 RGB 对比必失败）+ 总时长守恒 + 唯一帧数下限。

## 验证

```powershell
python design\_tmp_final_render.py          # 内置三断言，失败即退出非零
# 人工核对：out_gif/_final_9frames.png 9 帧放大表（无重影/粘连/出圆）
```

产物：`out_gif/sport_mode_final.gif`（9 帧 @40ms = 360ms 快跑周期，13.4KB，
白色剪影 + lime 圆静止 + 8° 前倾）。用户确认定稿后复制到 `watch/fs/anim/`
按 `step_walk.gif` 同款桥接（`lv_gif_create` 挂图标位）。

## 通用化

| 本案例 | 跨栈对照 |
|---|---|
| python-lottie 丢旋转插值 | 任何"矢量动画→帧"转换器：交付前必须**唯一帧数校验**（`set(tobytes)` 计数），帧数骤减 = 插值丢失 |
| rlottie 纯黑残影 | 渲染器 buffer 复用/blend 语义差异；同动画多渲染器结果不同，**官方预览产物优先于本地重渲染** |
| Pillow GIF 相邻同帧去重 | Pillow ≥12 的静默行为；预合并相邻重复帧（缓存 bytes 比较）+ 读回断言。B4（异步旧帧）同族：**产物必须读回验证** |
| GIF 10ms 帧延迟粒度 | 60fps 动画进 GIF 必有取整误差；取粒度整数倍（20/30/40ms）并整批校验总时长 |
| bbox 居中 ≠ 视觉居中 | 前倾/不对称剪影的外接框中心偏移；用**前景像素质心**对齐目标点。B9/B10（居中三兄弟）：B9 手摆 vs 声明、B10 尾随间隔、B14 外接框 vs 质心 |
| MaxFilter 膨胀粘连 | 形态学膨胀会填平 ≤kernel/2 的缝隙；肢体间距小的图形先看最小缝隙宽度再选 kernel |
| 开源动画素材渠道 | Iconify 公共 API（`api.iconify.design/<集>/<名>.svg`，免 key，200+ 开源集）；LottieFiles 免费 API（`/api/v1/animation/<id>?format=json` 元数据含官方 GIF/JSON 直链）；许可证认准 Lottie Simple License / CC-BY / Apache-2.0 |

检索别名：图标动画 / GIF 生成 / 跑者动画 / Lottie 渲染 / Pillow 去重 / 帧数校验 /
质心居中 / 形态学膨胀 / 开源图库 / Iconify / LottieFiles
