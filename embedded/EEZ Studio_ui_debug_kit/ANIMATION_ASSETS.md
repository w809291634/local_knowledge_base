# 动效素材：渠道与筛选流程（2026-10-30 定，watch2 实测）

用来回答两个问题：**去哪里找 UI 动效**、**怎么把一堆候选筛到能用的那一两个**。
本文件只讲"素材获取与筛选"；落地播放方式见 NO_FLOW §2.0 与各工程 `SPRITES`/`ANIM` 口径。

## 1. 渠道清单（按实测可用性分三档）

### A. 可直接抓（不用登录、不经 Cloudflare）★ 首选

| 站 | 拿什么 | 抓法 | 授权 |
| --- | --- | --- | --- |
| **lottiefiles.com** | Lottie 动画的 GIF 预览 | `GET https://lottiefiles.com/free-animations/<单词>` 的 HTML 里直接有 `assets-v2.lottiefiles.com/**.gif`，一页约 50 个 | Lottie Simple License；**选中后必须回动画页确认是 Free 还是 Premium** |
| **opengameart.org** | 精灵表 / 逐帧 | `GET /content/<slug>`，页面里 `/sites/default/files/*.png|gif`；授权写在 `License(s):` 后 | CC0 / CC-BY / CC-BY-SA / GPL，逐条看 |
| **commons.wikimedia.org** | 体育/生活类 GIF | API：`action=query&list=search&srsearch=filemime:image/gif <词>&srnamespace=6`，再 `prop=imageinfo&iiprop=url|size|mime|extmetadata` | 多为 CC BY-SA / CC0 / PD，`extmetadata.LicenseShortName` 直接读 |

**LottieFiles 的 slug 只认单词**：`running` `jogging` `workout` `fitness` `sprint` 都能出卡片；
`running-line` 这种多词 slug 返回的是一张没有卡片的通用页（实测 0 个 GIF）。想要另一种风格就换单词，别再拼短语。

### B. 站点能开但抓不到文件（别浪费时间爬）

- **icons8.com / iconscout.com**：curl 直接吃 `Just a moment...`（Cloudflare 5 秒盾），HTML 里没有任何动画资源地址。
- **lordicon.com**：页面 200 可读，但下载/JSON 要走账号。
- 结论：这几家**只适合让用户自己登录下载**，AI 侧不要试图抓。

### C. 不能进产品（只能当参考）

- Giphy / Tenor / soogif：网友上传，版权不明。
- 千图/包图/千库/摄图/站酷海洛：要会员，授权书要单独下载存档；能用于产品但必须留凭证。

## 2. 筛选流程（一步步）

**给用户看的一步步（用户自己也能照着做）**

1. 先说清风格轴：线条 / 扁平插画 / 单色实心 / 像素 / 真人抠图。**一次只做一种**，混着给等于没给。
2. 打开 `lottiefiles.com/free-animations/running`（或 jogging/workout/fitness/sprint），搜索框里换词可以继续扩。
3. 鼠标划过卡片就能看到"在动"，先按风格挑 5~8 个，记下画面特征（"线描小人""扁平跑步女"这种），别记标题——**站内标题和卡片经常错位**。
4. 挑中后进它的动画详情页，看右上角是 **Free** 还是 **Premium**，记下作者名。
5. 需要单色效果时告诉 AI"要线条/要染成强调色"，AI 会把整条动画染成单色再出预览。

**给 AI 的一步步（可脚本化）**

1. 抓候选：`GET https://lottiefiles.com/free-animations/<单词>`，正则取 `https://assets-v2\.lottiefiles\.com/[^"']+?\.gif`，去重后每页 ≈50 个。
2. 批量下载预览 GIF（每个 30~2500 KB），得到"候选池"。
3. **抠底**：取像素四角，若四角同色（白/灰/绿底都常见），把 |RGB−角点色| ≤18 的像素置透明；四角不同色视为真透明，跳过。
4. **量化筛风格**（见 §3 判据）：算 ink（可见像素占比）、颜色数（RGB//40 量化后去重）、细度（`边界像素/可见像素`）。
5. **染色**：取 alpha 通道 + 目标色填充（`纯白` 或 `STYLE["accent"]`），得到可直接上深色界面的版本。
6. **出全览**：统一 200×200 格、保留各自原速，写成一张 SVG（`<image href="x.gif">`），浏览器打开即循环；一次 6~9 个，编号给用户点选。
7. 用户选定后：回原动画页核准标题/作者/授权 → 拉 Lottie JSON 或帧序列 → 写 `PORTLOG.md`（URL、授权条款、作者、下载日期、每帧/每文件 SHA256）。
8. 播放方式三选一，第④步按实测定：`lv_gif` 直播 GIF（最省事）/ 转帧序列（可控） / ThorVG 播 Lottie JSON（体积最小，P4 无 GPU 要量每帧耗时）。

## 3. 判据（watch2 实测数字）

| 风格 | ink（可见占比） | 颜色数 | 细度 | 实测样本 |
| --- | --- | --- | --- | --- |
| 线描 | < 0.10 | ≤ 8 | > 0.30 | `001.gif` ink=0.04、6 色 → 线描跑步小人（选中） |
| 单色实心 | < 0.10 | ≤ 8 | < 0.25 | `008.gif` ink=0.05、8 色 |
| 扁平插画 | 0.05~0.20 | 20~70 | — | `004/030` 跑步女（20~40 色） |
| 像素/游戏精灵 | 视尺寸 | 多 | — | OpenGameArt 50×50 精灵表 |

**三个坑（都踩过）**

1. **标题错位**：从 DOM 上下文抓的标题与卡片不一一对应（抓出"跑步舞"其实是咖啡杯）。命名以画面为准，授权以详情页为准。
2. **假透明**：有些 GIF 用棋盘格画"透明"，角点键色会把棋盘留下；这类直接剔除。
3. **抠底后帧被合并**：PIL 保存 GIF 会丢掉与上一帧完全相同的帧，**但不补时长**；循环会变短，必须自己合并重复帧并累加时长（详见 intake P-0216）。

## 4. 授权口径（医疗/对外产品一律照此）

- **CC0**：可商用、免署名，最省事；账里记来源即可。
- **CC-BY**：可商用，**必须在说明书/致谢署名作者**。
- **CC-BY-SA**：署名 + **改动后的图要同样开源**；改过色/裁过尺寸就算改动，慎用。
- **LottieFiles 免费区**：Lottie Simple License，可商用；**每个动画仍要单独确认 Free/Premium**。
- 所有素材入库都要在工程 `PORTLOG.md` 记：URL、授权条款原文、作者、下载日期、SHA256；注册资料要能追溯。

## 5. 已落地示例

watch2 运动页跑步小人：LottieFiles 线描款，染色成 `#FF6B35`/纯白，出对比 SVG
`watch2/tmp/oga/_anim_line.svg`（8 格：原黑/染白/染强调色/彩色线条/剪影速度线/单色实心/扁平女/正面走跑）。
