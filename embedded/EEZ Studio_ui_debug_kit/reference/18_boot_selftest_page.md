# 开机自检页（自检 → 真实 MP4 → 主界面）

> 2026-11-07 用户定稿。适用：需要开机自检/开机动画的 LVGL 9.4 + EEZ no-flow 工程。
>
> **默认规则（2026-11-07 用户定）**：以后所有工程的设计图（PNG）与 H5 评审页**默认包含「开机初始化」页**，
> 不因工程暂无开机动画/自检需求而省略；只有用户明确说“不要”才可省。新工程直接复用本页版式。
>
> **创建方式（2026-11-07 用户定）**：自检页**默认不通过 EEZ 创建**，由运行期覆盖层
> （`boot_selftest`）实现；EEZ 只保留业务页。只有用户明确要求时才改成 EEZ 真页。
> 参考实现：`w78-tabview-smart-home`
> - `src/native/app/boot_selftest.c/.h`（运行期覆盖层）
> - `src/native/platform/pc/sim_video.c/.h`（PC 真实 MP4）
> - `design/boot_init_design.py`、`design/simple_control.py#boot_init_frame`
> - H5-only 页「开机自检」：`design/overview_pro.py`

## 1. 流程（唯一口径）

```
上电 → 自检页 0→100%（可选约 2s）→ 删除覆盖层 → 播放真实 MP4 → 主界面
```

- 自检页是**运行期 LVGL 顶层覆盖层**（`lv_layer_top()`），不是 EEZ 页。
- **不进 EEZ**（2026-11-07 用户定）：它简单且只存在一瞬，EEZ 只保留业务页；
  强行做成 EEZ 真页会引入 arc/line 控件、不可达屏、导航豁免和一整套门禁适配。
- 设计可见性由两处承担：H5 评审页（H5-only 页，排首位）+ 设计图 PNG。
- 真机没有 MP4 解码时：自检页结束后直接进主界面（`sim_video` 在 `ESP_PLATFORM` 下是空实现）。

## 2. 版面规则

| 元素 | 几何（800×480） | 说明 |
| --- | --- | --- |
| 品牌 H 标 | 30×30 @ (40,34)，圆角 9 | 辅色底 + 深色字 |
| HAVEN HOME / 系统自检 | (82,37) / (82,62) | 英文用 montserrat_20，中文用 `ui_font_cn12` |
| 版本号 | 右上 (700,40) 右对齐 | |
| 中央徽标 | 112×112 @ (344,72)，圆角 28，边框 1px | 房子 = 白色墙体 + 深色门 + 两条白色折线屋顶 |
| 环形进度 | 176×176 @ (312,40)，环宽 3 | **环半径必须大于徽标对角半径**（88 > 79.2），否则环切过徽标角；`lv_arc_set_rotation(270)` 从正上方起画 |
| 标题 / 副标题 | y=222 / y=254，居中 | **中文只能用 `ui_font_cn12`** |
| 进度条 / 百分比 | 520×8 @ (140,300)；右对齐 @ (560,282) | |
| 动态字条 | 圆点 8×8 @ (300,334)；文字 x=316 | **只有一条字条**，随检测项切换 |
| 页脚 | 分隔线 y=432；文字 y=444 | 左「请勿断电」/ 右「HAVEN HOME」 |

**禁止**：`1、2、3、` 编号列表；多项堆叠或换行；用 `ui_font_cn24/cn32` 写中文
（这两档只有 Latin/数字，写中文全是豆腐块）。

## 3. 运行期驱动

```c
static const char *status_text(int p)
{
    if (p < 20) return "正在检查内存…";
    if (p < 45) return "正在检查显示…";
    if (p < 70) return "正在检查 Wi-Fi 模块…";
    if (p < 90) return "正在检查存储…";
    return "自检完成，正在进入…";
}
```

- `lv_timer` 20ms 一步，100 步 ≈ 2s；每步更新 bar / arc / 百分比 / 字条。
- 到 100%：删定时器 → 删覆盖层 →（PC）`sim_video_play_boot()`。
- 覆盖层删除后主界面自然露出（`ui_init()` 已加载主控）。
- 在定时器回调里删自己的定时器是安全的：LVGL 9 用 `timer_deleted` 标记并在本轮结束后重建遍历。

## 4. 真实 MP4（PC 仿真）

- `sim_video` 用 `_popen` 启动 ffmpeg，直接解码 `assets/boot.mp4` → 800×480 BGRA → LVGL canvas。
- **禁止**把 MP4 预转成帧序列/动图冒充「播放视频」；帧序列只能是真机资源包。
- ffmpeg 路径由 `run_sim.bat` 写入 `FFMPEG_EXE`（`imageio_ffmpeg.get_ffmpeg_exe()`）。
- Windows `_popen` 两个坑：
  1. exe 路径含空格时用引号包住，否则 cmd 拆参数；
  2. 临时 `_chdir(工程根)` 后用相对路径 `assets\boot.mp4`，避免带引号 exe + 多参数被拆坏。
- 解码到 30 帧后取一张截图做目检；`boottest` 打印 `[VIDEO] playing ...` 与解码帧数。

## 5. 自证

```bat
run_sim.bat boottest
```

判据：`[BOOT] selftest=100 video=N active=0`（N>0）+ 两张截图
（`tmp/boot_selftest.bmp`、`tmp/boot_video.bmp`）目检无豆腐块/无重叠。

## 6. 踩坑

| 现象 | 原因 | 处置 |
| --- | --- | --- |
| 标题中文是豆腐块 | 误用 `ui_font_cn24` | 中文一律 `ui_font_cn12` + `letter_space` 撑开 |
| 环形切过徽标角 | 环半径小于徽标对角半径 | 环 r=88，徽标 112（对角半径 79.2） |
| 视频截图没生成 | 固定帧号时视频已播完 | 用 `sim_video_frames() >= 30` + 去重标志 |
| `[VIDEO] 文件名、目录名或卷标语法不正确` | `_popen` 引号被 cmd 拆坏 | 见 §4 两条 |
| 视频播完窗口还在 | 覆盖层未删 | EOF 时删定时器 + 删 canvas 覆盖层 |
