# P-0151 · EEZ 手册 W1 AnimationImage 落地：CLI 构建不产图片 .c，帧位图=data-URI 内嵌

- **工程**：EEz_stidio_examples/w1-animation-image
- **日期**：2026-10-19
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：AnimationImage,animimg,位图,data-URI,CLI不烘图片,lv_image_dsc_t,ARGB8888,gen_images
- **关联提示词**：PR-0257

## 现象（看到什么）

纯 CLI 构建的 AnimationImage 工程链接报 undefined reference to img_anim_frame_N：images.c 只有 {名,&符号} 名表、images.h 只有声明，帧数据 .c 全缺失

## 复现（怎么稳定重现）

EEZ v3 工程 + LVGLAnimationImageWidget（images=8 帧位图名、duration=800、repeatInfinite=true）+ settings.build.separateFolderForImagesAndFonts=true，只跑 CLI 构建

## 根因（真正的原因）

EEZ CLI 构建（P-0140 的图片版）只发名表与声明，图片数据 .c 由 GUI Build 的 lvgl-worker 提取；手册（help/en-US/components/widgets/AnimationImage.md，官方目录即 W1 节 + docs.lvgl.io/master/widgets/animimg.html，EXAMPLES 节为空）明确属性三件套：Images 按序逐帧/Duration 整轮 ms/Repeat infinite|count——帧条目无独立时长

## 修复（做了什么）

与 gen_fonts.py 同款自愈：design/gen_images.py 复算帧像素，按 EEZ v9 格式落 src/ui/images/img_anim_frame_N.c——lv_image_dsc_t{magic=LV_IMAGE_HEADER_MAGIC, cf=LV_COLOR_FORMAT_ARGB8888, w,h,stride=4w}，像素内存字节序 B,G,R,A；工作流=CLI 构建→gen_images.py→编译。位图条目本身用内嵌 data:image/png;base64（bpp32 支持透明），无需外部图片文件

## 证据（数字 / 命令输出）

修复前链接 8 个 undefined reference（frame_6/7 在尾）；gen_images.py 后 PC_SIM 9/9 编译链接 0 错；生成代码与手册语义一一对应（set_src(8帧)→set_duration(800)→set_repeat_count(LV_ANIM_REPEAT_INFINITE)→start）

## 沉淀（新增断言 / 案例 / 文档）

w1-animation-image/README.md、根 README 索引第 8 行、workspace memory 2026-10-19、skills.md 可后续并入 §11.48 图片扩展

## 补充（同日）
- GUI 手动添加 AnimationImage 的完整操作文档已落在示例工程：
  `EEz_stidio_examples/w1-animation-image/GUI-操作指南.md`
  （导入帧图→拖控件→Images 批量添加含 No. of images 连填→Duration/Repeat→Build，
  末尾附常见问题对照表；P-0150 的"flags 别乱裁"已写进注意事项）。
