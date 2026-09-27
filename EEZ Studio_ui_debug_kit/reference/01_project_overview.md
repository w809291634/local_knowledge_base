# EEZ Studio 参考指南 — 项目概览与 UI 工程笔记（C1–C5, P1–P7, P13）

> 本文档从 EEZ Studio Reference Guide 纯文本提取稿中整理的“项目（Project）”部分使用笔记，面向**为嵌入式 LVGL 设备（目标 LVGL 9.4）生成 UI 工程**这一核心目标。所有英文标识符、属性名、菜单项均保持原样（verbatim）。
>
> 文档覆盖范围：C1–C5（法律/概览/安装/关键特性/菜单与设置）、P1（首页工程区块）、P2（工程编辑器概览）、P3（工程编辑器模式）、P4（工程编辑器面板）、P5（编辑器/查看器）、P6（EEZ Flow）、P7（工程编辑）、P13（设置）。

---

## C1. 法律信息（Legal information）

### 用途
说明 EEZ Studio 的许可证、免责声明与联系方式。与嵌入式 LVGL 工程导出关系较小，但涉及**许可证合规**，值得记录。

### 关键内容
- **许可证**：EEZ Studio 本身使用 **GPL v3** 许可证（详见 https://www.gnu.org/licenses/gpl-3.0.html）。贡献采用 **C4.1（Collective Code Construction Contract）** 流程。
- **文档许可证**：本文档本身以 GNU **FDL v1.3** 发布，可自由复制、再分发（含修改）。
- **运行时许可证（Runtime License）**：用户可选择 **MIT、BSD 2.0、Public Domain**（见 C4.1）。导出到嵌入式固件时，运行时代码的许可证可由用户选择，对闭源固件集成很重要。
- **开源/安全**：所有 Envox 产品可能存在未识别漏洞；安全漏洞通过 **EEZ Studio issue tracker** 报告。
- **联系信息**：
  - Discord：https://discord.gg/dhYMnCB
  - E-mail：support@envox.eu
  - 网站：www.envox.eu

### 修订历史（与 LVGL 嵌入式相关的重要节点）
- 0.22.0（2025-02-10）：**迁移到 LVGL v9.2.2**，新增 Play Sound 与 FocusWidget Actions。
- 0.23.1（2025-04-06）：**LVGL QR code**。
- 0.13.1（2025-05-16）：LVGL bug fixes。
- 0.14.0–0.14.2：Hybrid table/tree/grid widget；"Scrollbar mode" / "Scroll direction" 属性（LVGL widgets）。
- 0.15.0（2024-08-04）：**Project scrapbook、Copy/paste between projects**。
- 0.24.0 及之后（至 0.26.0，2026-02-04）：各类修复与改进。
- 注意：手册明确说明 GUI 版本迭代快，部分截图可能不反映最新外观（“some of them will not reflect the appearance of the latest version”）——阅读时以文字描述为准。

---

## C2. EEZ Studio 概览（The EEZ Studio overview）

### 用途
介绍 EEZ Studio 的两大组成部分，帮助判断该工具是否适合你的需求。

### 两大模块
1. **Project（工程）**：为选定目标平台**创建、编辑、调试、构建**嵌入式 GUI 工程代码。生成代码可直接导入 IDE/工具链（如 STM32CubeIDE、Arduino IDE）加快构建。原生支持 **LVGL 图形库**；拖放式编辑器 + 流程图式 **EEZ Flow** 编程大幅减少编码量。
2. **Instrument（仪器）**：通过 SCPI 指令访问多台 T&M 仪器，采集测量数据、截图、自动化测试（使用 JavaScript 与 EEZ Flow）。与嵌入式 UI 导出无直接关系。

> 对嵌入式 LVGL 设备：我们只需要 **Project** 模块。

---

## C3. 安装（Installation）

### C3.1 系统要求
- EEZ Studio 是 **64 位应用程序**，需要 64 位操作系统 + 足够 RAM 与磁盘空间。
- 官方下载页：https://github.com/eez-open/studio （建议首次安装获取最新版，之后可用内置更新检查）。

### C3.2 Linux
- 提供 `.deb` / `.rpm` 包，或用对应安装器安装。
- 另有自执行 **.AppImage**：下载后需在文件权限中勾选 **“Allow executing file as program”** 才能运行。
- 若 AppImage 无法运行，使用 `--no-sandbox`：`//EEZ-Studio-[version].AppImage --no-sandbox`

### C3.3 Mac
- 要求 **macOS 10.10 (Yosemite)** 或更新。
- 下载 `eezstudio-mac.zip`，解压后将 `eezstudio.app` 移入 `Applications`。

### C3.4 Windows
- 要求 **Windows 7 (64-bit)** 或更新。
- 下载并运行 `EEZ_Studio_setup.exe`。

### C3.5 Nix 包管理器
- 通过 Nix flake 提供的 derivation 或 overlay 安装。

### C3.6 从源码构建（全平台）
1. 安装 **Node.JS 14.x 或更新**。
2. 安装 **node-gyp**。
3. **Linux only**：`sudo apt-get install build-essential libudev-dev`
4. **Raspbian only**：安装 Node.js 16 与 npm；`sudo apt-get install build-essential libudev-dev libopenjp2-tools ruby-full`；`sudo gem install fpm`
5. **All platforms**：
   ```
   git clone https://github.com/eez-open/studio
   cd studio
   npm install
   npm run build
   npm start          # 启动
   npm run dist       # 生成发行包（Raspbian 除外）
   ```
6. **Raspbian**：`npm run dist-raspbian`
7. **Nix**：`nix build 'github:eez-open/studio'` / `nix run 'github:eez-open/studio'`

### C3.7 USB TMC（访问仪器用，UI 工程一般不需）
- **Windows**：用 Zadig 选设备 → 选 `libusb-win32` → 按 “Replace Driver”。
- **Linux**：需将账户加入 `usbtmc` 组：
  ```
  ls -l /dev/usbtmc*
  sudo groupadd usbtmc
  sudo usermod -a -G usbtmc <username>   # 需重启
  ```

### C3.8 FAQ（与 LVGL 构建相关）
- **数据库文件位置**：
  - Linux：`~/.config/eezstudio/storage.db`
  - Mac：`~/Library/Application\ Support/eezstudio/storage.db`
  - Windows：`%appdata%\eezstudio\storage.db`
  - 默认数据库及位置可在 Settings 中更改。
- **IEXT（Instrument EXTension）存储位置**：同上三个路径下的 `extensions` 目录。
- **Python 设置（重要）**：在 Settings 里可指定默认或自定义 Python 安装位置。手册特别指出：构建 LVGL 时**转换图片（image conversion）用的是 EEZ Studio 实际运行的 Python 版本**，如果用户用终端 pip 装依赖却与 Studio 用的 Python 版本不同，会产生混淆/问题。→ 对 LVGL 工程导出，务必在 Settings 的 **Python** 项确认路径正确。

---

## C4. 关键特性（Key features）

### C4.1 通用
- 基于 Electron 的现代 UI/UX；**Light / Dark 主题**。
- **多标签（Multi-tab）** 支持。
- 跨平台（Linux / Windows / macOS）。
- 基于插件的模块化设计（插件可按需增删）。
- **源码/版本控制集成**（GitHub 与 gitea.io）。
- 免费开源：**EEZ Studio 许可证 GPL 3.0**；**运行时许可证（用户可选）：MIT、BSD 2.0、Public Domain**。

### C4.2 EEZ Studio Project（与嵌入式 LVGL 最相关）
- 模块化可视化开发环境，适用于**资源受限的小型显示屏嵌入式 GUI** 与桌面 GUI。
- **EEZ Flow**：低代码流程图编程，用于快速原型与复杂应用。
- **LVGL（Light and Versatile Graphics Library）支持**。
- **多语言（Multi-language）** 支持。
- 支持**不限数量的 Color Themes（颜色主题）**。
- 支持**不限数量的 Widget styles（控件样式）**。
- 支持**不限数量的用户自定义 Widgets 与 Actions**。
- **Copy/paste between projects**（跨工程复制粘贴）。
- **Project scrapbook**（工程剪贴簿）。
- 通过 **Project extensions** 添加新功能。
- 生成 **C++ 代码** 用于嵌入式 GUI，可直接纳入：
  - **STM32CubeIDE**（EEZ BB3 及其他 STM32 目标平台）
  - **Arduino IDE**（EEZ H24005 及其他 Arduino 兼容目标平台）
- IDF（Instrument Definition File）构建器（SCPI 相关，UI 工程一般不涉及）。
- **Project templates**（基于 gitea.io 仓库）与工程对比。
- 拖放式编辑器用于创建仪器桌面仪表盘（Dashboard）。

### C4.3 EEZ Studio Instrument
（仪器相关，UI 工程导出基本不涉及，略。）

---

## C5. 菜单选项与设置（Menu options and Settings）

### C5.1 首页（Home page）
启动后显示首页，顶部工具栏包含：**Projects、Instruments、Extensions、EEZ Studio settings**。工程相关操作（Open / Create / Examples）在 P 章节详述。

### C5.2 菜单选项

#### C5.2.1 File
| Option | Shortcut | 说明 |
|---|---|---|
| New project... | CTRL + N | 新建工程 |
| Add instrument... | ALT + CTRL + N | 添加可被控制的仪器 |
| New Window | CTRL + SHIFT + N | 打开一个新窗口（**跨工程复制粘贴时必需**，见 P7.1.2） |
| Open... | CTRL + O | 打开已有工程 |
| Open Recent | – | 最近打开工程列表 |
| Reload (Projects only) | – | 重新加载当前工程（有未保存改动会提示） |
| Load Debug Info... (Projects only) | – | 加载调试器状态并切换到 **Debug 模式**（仅限生成该调试状态文件的同一工程） |
| Save Debug Info... (Projects only) | – | 在 Debug 模式保存调试器状态到文件 |
| Import Instrument Definition... | – | 导入 IEXT 文件 |
| Save | CTRL + S | 保存工程文件 |
| Save as (Projects only) | CTRL + SHIFT + S | 另存为 |
| Check (Projects only) | CTRL + K | 打开工程的 Check 面板 |
| Build (Projects only) | CTRL + B | 开始构建并打开 Build 面板 |
| Build Extensions (Projects only) | – | 仅构建 IEXT .zip（工程含 IEXT 定义时） |
| Build and Install Extensions (Projects only) | – | 同上并立即安装 IEXT |
| Exit | – | 退出 |

#### C5.2.2 Edit
| Option | Shortcut | 说明 |
|---|---|---|
| Undo | CTRL + Z | 撤销 |
| Redo | CTRL + Y | 重做 |
| Cut | CTRL + X | 剪切到剪贴板 |
| Copy | CTRL + C | 复制到剪贴板 |
| Paste | CTRL + V | 粘贴 |
| Delete | DEL | 删除选中内容 |
| Select All | CTRL + A | 全选 |

#### C5.2.3 View
| Option | Shortcut | 说明 |
|---|---|---|
| Home | – | 回到 Home 标签 |
| History | – | 打开仪器 History 标签 |
| Shortcuts and Groups | – | 仪器快捷键/组 |
| Notebooks | – | 仪器 Notebooks |
| Extension Manager | – | 仪器扩展管理器 |
| Settings | – | 打开 Settings 标签（含 Databases / Locale / Python / Dark theme 等） |
| Toggle Full Screen | F11 | 全屏切换 |
| Toggle Developer Tools | CTRL + SHIFT + I | 打开开发者工具 |
| Switch to Dark Theme | CTRL + SHIFT + T | 明暗主题切换 |
| Zoom In | CTRL + + | 放大（部分 Linux 需用 CTRL + SHIFT + +） |
| Zoom Out | CTRL + - | 缩小 |
| Reset Zoom | CTRL + 0 | 恢复默认缩放 |

#### C5.2.4 Help
- **About**：版本信息。
- **Check for Updates**：需联网连接 GitHub 检查新版本；**只检查已发布版本，不检查预发布（pre-release）版本**。
- **Home**：打开 Envox 官网。
- **Github**：打开 Envox GitHub 主页。

### C5 的 Settings 标签（重要设置项）
- **Databases**：首次启动创建空数据库，位置可在此查看；可创建新数据库（列表中标 `[ACTIVE]` 的为当前活动库，用 **Set as Active** 切换）；选项 (2) 在磁盘打开所在文件夹，(3) 删除选中库。**更改数据库参数需重启 EEZ Studio**（右下角出现 Restart 按钮）。
- **Locale**：定义日期/时间国家格式；更改需重启。
- **Date format / Time format**：日期/时间显示格式。
- **Python**：选择默认或自定义 Python 安装位置（**LVGL 构建转换图片时用到，见 C3.8 注意事项**）。
- **Dark theme**：明暗主题切换（同 CTRL + SHIFT + T）。

---

## P1. 首页工程区块（Home page project sections）

### P1 概述
首页的 **Projects Open** 区显示可搜索的 **Recent Project List (RPL)**。

| # | Option | 说明 |
|---|---|---|
| 1 | Open project | 打开已有工程（成功加载后加入 RPL） |
| 2 | Search RPL | 按工程名搜索 RPL |
| 3 | RPL sort order | 排序：Show most recent first / Sort alphabetically |
| 4 | Recent Project List (RPL) | 首次运行后所有成功加载工程的列表 |

### P1.1 EEZ Studio 工程类型（重点）
EEZ Studio 支持为不同目标平台/技术创建工程：
- **Dashboard** — 桌面应用；拖放控件 + 导入字体/位图 + 动画编辑器 + 流程图逻辑；自带调试器。
- **EEZ-GUI** — 使用 EEZ-GUI 框架的嵌入式 GUI（EEZ 原生框架，最初为 H24005/BB3 固件开发）。
- **LVGL** — 使用 **LVGL（Light and Versatile Graphics Library）** 框架的嵌入式 GUI。LVGL 是流行的开源项目，支持大量目标平台（https://lvgl.io/）。→ **为嵌入式 LVGL 设备生成 UI，应选此类型。**
- **LVGL with EEZ Flow** — 同 LVGL，但额外加入 **EEZ Flow** 流程图式编程。→ **若需在 UI 中加入交互逻辑/状态机，选此类型（推荐用于 LVGL 9.4 设备）。**
- **BB3 Applet** — 运行于 EEZ BB3 的 GUI，程序逻辑用 EEZ Flow。
- **BB3 MicroPython script** — 运行于 EEZ BB3 的 GUI，程序逻辑用 MicroPython。
- **Templates from gitea repository** — gitea.io 上的模板工程（多基于 EEZ-GUI），可作新建起点。

> **LVGL 嵌入式设备选择建议**：选 **LVGL** 或 **LVGL with EEZ Flow**。后者在 Settings 中自动开启 Flow support，可用 EEZ Flow 以低代码方式编排页面跳转、控件交互、变量与 Action。

### P1.2 新建工程（Create new project）
在首页工具栏选 **Create** 标签进入。

| # | Option | 说明 |
|---|---|---|
| 1 | Search | 按工程名搜索 |
| 2 | Project list | 选中分类下的所有工程，分组于可展开子列表 |
| 3 | Project selector | 当前子组中的工程选择器；浏览时右侧显示工程设置，悬停缩略图可放大 |
| 4 | Platform description | 目标平台说明及外部网站链接（若有） |
| 5 | Project settings | 工程基本参数（见下） |
| 6 | Info | 若工程有 Git 仓库，显示指向仓库主页的链接 |
| 7 | Project details | 基本信息：类型、屏幕尺寸；LVGL 工程还会显示**所用库版本（version of the library used）** |

> 注：表格原文中编号 "3" 出现两次（Project list 与 Project selector 均标 3），属手册编号瑕疵，此处按内容列出。

### P1.3 工程基本设置（Project basic settings）
- **Name** — 新工程名称。
- **Location** — 工程文件存储位置。
- **Create directory** — 若勾选，会在 Location 下创建以工程名命名的子目录。**从 Git 仓库取工程时此选项不可用**（此时总是新建文件夹）。
- **Project file path** — 只读信息框，显示新工程最终路径。
- **Clone Git repository** — 从 Git 仓库示例新建时，`.eez-project` 文件总会复制；勾选此项可同时复制仓库其余文件。
- **Initialize as Git repository** — 是否将模板新建的工程立即初始化为 Git 仓库；不使用 Git 可不选。

### P1.4 创建 EEZ BB3 工程的附加步骤（LVGL 设备不适用，记录备查）
- BB3 Applet 与 MicroPython script 需引用 **EEZ BB3 固件主工程（master project）**，以复用其样式/字体/主题，保证 GUI 兼容。
- 可从 GitHub 下载主工程，或指向本地仓库副本。
- MicroPython script 需定义目标 BB3 的固件版本，构建时生成对应资源文件。

> 新建工程后进入 **Edit 模式**；最小可用工程即可在仿真（Run / Debug 模式）或构建后于目标平台运行。点击 **Settings** 可在新标签查看/编辑基本设置，并看到 **Project features**（已添加且必选的 Remove 禁用、可移除的、尚未添加的三类）。

---

## P2. 工程编辑器概览（Project editor overview）

### P2.1 工程编辑器工作区（workspace）
工程编辑器元素分三大类：
- **Toolbar** — 基本编辑器功能图标，数量随工程类型变化。
- **Panel windows（面板窗口）** — 含工程元素/组件/报告的组，例如 **Pages、Actions、Styles、Fonts、Bitmaps、Variables、Checks、Output（构建结果）、Search、References**。面板可归入一个 tabset（通过标签切换）。
- **Page editors/viewers** — 显示正在编辑的页面（Debug 模式下为 Page viewers，内容不可编辑）。

面板与编辑器可归入一个或多个 **tabset**（可停靠 dockable），可置于工作区（如示例 (3)(4)）或沿边框（如 (5)(6)）。

| # | Section / option | 说明 |
|---|---|---|
| 1 | Main tabs | 多工程/多选项间导航（含 Instruments 等非 Project 内容） |
| 2 | Toolbar | 编辑器主功能与模式（Edit / Run / Debug） |
| 3 | Tabset | 含一个或多个面板的可停靠区块 |
| 4 | Editor tabset | 编辑 Pages 与 Actions 之处；Pages 含 GUI 元素，Actions 仅含 EEZ Flow 程序逻辑 |
| 5 | Right border tabset | 右边框 tabset；默认含 styles、bitmaps、themes、breakpoints 面板 |
| 6 | Bottom border tabset | 底边框 tabset；默认含错误检查、构建、搜索列表 |

### P2.2 编辑器中页面的显示
- 点击某页面 (1) → 出现新编辑器标签，页面名以**斜体**显示 (2)，表示**未锁定**：再选其他页面会替换当前显示。
- 右键 → **Keep Tab Open** (3) 可锁定页面；锁定后名称不再斜体 (4)。

### P2.3 面板移动与停靠（Panel moving and docking）
- 面板与编辑器可在工作区或边框自由定位并归入 tabset。
- **关键区别**：面板**不能关闭/隐藏**；编辑器按需打开/关闭。
- 移动示例：按住 Actions 标签拖动，光标变化且四边出现可停靠指示标记（border tabset 指示）。
- 可停在 Pages 面板**下方**（水平分割，Fig.11）、**右侧**（垂直分割，Fig.12），或成为现有 tabset 中的新标签（两种方式，Fig.13/14）。靠近现有标签边缘会出现较小矩形表示分割。

### P2.4 边框 tabsets（Border tabsets）
- 边框 tabset 的面板：点击标签打开，再点关闭；**同一边框 tabset 内任意时刻只能有一个面板打开**。
- **面板停靠在 Edit 与 Debug 模式均可，但 Debug 模式下不能停靠进边框 tabset**。

---

## P3. 工程编辑器模式（Project editor modes）

### P3 概述
三种模式：**Edit、Run、Debug**。**Mode switcher（模式切换器）** 位于工具栏，仅当工程使用 **EEZ Flow** 时才显示。
- Dashboard 工程默认包含 EEZ Flow；**EEZ-GUI 与 LVGL 工程需显式设置是否使用 EEZ Flow**（用 Settings 中的 **Flow support** 选项，即 P13 的 Flow support，Fig.18）。

### P3.1 工具栏概览（Toolbar overview）
- 工具栏外观随模式变化；部分选项通用，部分取决于模式、所选 Project features 或全局变量状态。
- Edit 模式用编辑器，Run/Debug 模式用查看器（viewer）：有 **Page viewer**（Run 与 Debug 模式）与 **Action viewer**（仅 Debug 模式）。查看器显示同编辑器但不可编辑。
- Run/Debug 模式**不能修改工程**，仅监视执行。
- **全局变量状态**仅在 Run/Debug 模式出现（且工程至少含一个 object 类型全局变量，如 Instrument connection / PostgreSQL connection）：显示图标、连接状态、标题；点击可改参数。

### P3.2 Edit 模式工具栏（Table 1：各模式可用性）
| Function / Group | Edit | Run | Debug |
|---|---|---|---|
| Save | √ | | |
| Undo | √ | | |
| Redo | √ | | |
| Copy | √ | | |
| Paste | √ | | |
| Scrapbook | √ | | |
| Check | √ | | |
| Build | √ | | |
| Run MicroPython Script (EEZ BB3 only) | √ | | |
| Show front face | √ | √ | √ |
| Show back face | √ | √ | √ |
| Show / Hide animation timeline editor | √ | | |
| Show / Hide component descriptions | √ | √ | |
| Language selector | √ | | |
| Features | √ | | |
| Mode switcher | √ | √ | √ |
| Global variables status | √ | √ | √ |

#### 各按钮详解
- **Undo / Redo**：撤销/重做最近编辑器动作。若有未保存改动，工程标签名旁出现 **`*` 号**（Fig.21）。
- **Copy / Paste**：可复制一个或多个工程项（Copy (1) / Paste (2)）。
  - 跨工程复制时会出现提示（Fig.24）。
  - 若粘贴带全部依赖，且目标工程存在同名但不同类型项，弹出**冲突解决对话框**，四个选项：
    | Option | 说明 |
    |---|---|
    | Rename source | 用新名粘贴 |
    | Rename destination | 保留原名，改目标工程中的现有项名 |
    | Replace | 用复制项覆盖目标工程现有项 |
    | Keep | 不覆盖目标工程现有项 |
  - 若对 Fig.24 提示回答否定且目标有同名项，复制时创建带后缀的新项（如 `global_1`）。
- **Scrapbook（剪贴簿）**：
  - 跨工程复制项可存入 Scrapbook，**显式删除前一直保留**（区别于剪贴板，剪贴板仅保留到 EEZ Studio 重启）。
  - 每个 Scrapbook 是磁盘上的独立 **SQLite 文件**（`.eez-scrapbook`），可自由复制/归档。
  - Scrapbook 可含无限项，可复制到其它工程并编辑。
  - 选项清单（Fig.27）：
    | # | Option | 说明 |
    |---|---|---|
    | 1 | List of scrapbook files | Default 与用户创建的 scrapbook 列表 |
    | 2 | Create a new Scrapbook file | 新建 |
    | 3 | Open a Scrapbook file | 从磁盘打开（`.eez-scrapbook`），加入列表 |
    | 4 | Delete Scrapbook file | 从列表移除（不删磁盘文件） |
    | 5 | Show in File Explorer | 打开磁盘所在文件夹 |
    | 6/7 | Undo / Redo | 剪贴簿内撤销/重做 |
    | 8 | Undock into separate window | 浮动窗口（默认） |
    | 9 | Dock to the side | 停靠进编辑器 |
    | 10 | Maximize | 最大化 |
    | 11 | Close | 关闭 |
    | 12 | Create item from Clipboard | 系统剪贴板内容新建项（名称(17)/描述(18)可改） |
    | 13 | Delete this item | 删除选中项 |
    | 14 | Insert into Active Project | 粘贴到选中工程（冲突时弹冲突解决器） |
    | 15 | Open in Project Editor | 作为合法工程打开查看/编辑 |
    | 16 | Paste Clipboard content into item | 系统剪贴板内容追加到现有项 |
    | 17/18 | Name / Description | 项名称/描述 |
    | 19 | Resources in this item | 项含的所有资源列表 |
- **Check**：不构建可执行代码而检查所有工程元素，结果在 Output 面板。
- **Build**：检查所有元素后构建可执行代码，结果在 Output 面板。
- **Run MicroPython Script (EEZ BB3 only)**：仅 MicroPython Script 类型；需项目通用设置启用 MicroPython 特性；构建时生成 `.res` 资源文件，与 `.py` 脚本一同传到 BB3 执行。
- **Show front face**：仅显示 Widgets（不含 Action 组件与连线），便于阅读。需 Flow 启用且页面编辑器聚焦。
- **Show back face**：显示所有组件（Widgets + Actions）与连线。需 Flow 启用且页面编辑器聚焦。
- **Show / Hide animation timeline editor**：EEZ Flow 支持页面内容动画，时间线编辑器显示在页面编辑器下方。需页面编辑器聚焦且通用设置启用 Flow。
- **Show / Hide component descriptions**：显示/隐藏每个组件的 **Description** 属性。仅当页面编辑器聚焦且选中 Show back face 时显示。
- **Language selector**：仅当通用设置选中 **Texts** 特性且至少定义一种语言时出现；文本标签出现在左边框 tabset，含多语言字符串定义、已用语言、翻译统计；页面编辑器按所选语言显示文本。

### P3.3 Feature buttons（特性按钮）
在通用设置中选中的以下工程特性会在工具栏添加图标：**Shortcuts、MicroPython、Readme**；**Settings** 也有其工具栏图标。

---

## P4. 工程编辑器面板（Project editor panels）

### P4.1 Panel items（面板项，Fig.38）
| # | Item | 说明 |
|---|---|---|
| 1 | Panel tabs | 在 tabset 内选择面板 |
| 2 | Items sort order | 三种排序：User（默认，两箭头均不亮，可拖拽改位置）/ Ascending / Descending |
| 3 | List filter | 按搜索词过滤；**User 排序下若输入过滤词，列表拖放被禁用** |
| 4 | Add item | 添加新元素，弹对话框（名称须唯一）。示例为添加新 Page |
| 5 | Delete selected item | 删除选中元素（可用工具栏 Undo 恢复） |
| 6 | Lock All / Unlock All | 锁定/解锁所有面板元素 |
| 7 | Hide All / Show All | 隐藏/显示所有面板元素 |
| 8 | Maximize tabset / Restore | 最大化/还原 |
| 9 | Sub tabs | 某些面板（如 Components Palette、Variables）用子标签组织内容 |

> **IMPORTANT（页面顺序）**：列表中的**第一个页面是工程启动时首个显示的页面**（示例名为 `main`，Fig.39）。
> **IMPORTANT（页面命名）**：**页面名不能包含点号（`.`）**，因为导入时点号用作外部库名与页面名的分隔符。
> 拖动改位置：User 排序下按住项可拖拽，出现新位置指示后释放即生效。

### P4.2 Right-click menu（右键菜单）
通用右键菜单选项（Fig.41；Widgets 的右键菜单更多，见 P7.2.2）：

| Option | 说明 |
|---|---|
| Add | 添加新项 |
| Duplicate | 复制项，名称加数字后缀（如 `main` → `main-1`） |
| Find All references | 查找所有引用，结果显示在 References 面板，点击跳转到使用处 |
| Cut | 剪切到剪贴板 |
| Copy | 复制到剪贴板 |
| Paste | 从剪贴板添加（剪贴板空时隐藏） |
| Delete | 删除（可用工具栏 Undo 恢复） |

### P4.3 Edit 模式面板总览
| Panel | 说明 |
|---|---|
| Pages | 将在 GUI 显示的页面；**列表顶部页面运行时最先显示**；在 tabset 编辑器打开可编辑 |
| Actions | 在 EEZ Flow 中创建的工程 Actions |
| Page structure | 当前选中页面中用到的所有 Widgets 列表 |
| Variables | 全局/局部变量；Structs 与 Enums 类型定义 |
| Properties | 显示/编辑选中项属性 |
| Breakpoints | 所有断点列表，可启用/禁用单个 |
| Components Palette | 可加到页面/Action 的所有 Widgets 与 Actions；**工程类型决定调色板内容** |
| Styles | 所有 GUI 元素样式 |
| Themes | 用于快速切换样式改变外观；新建主题会把当前所有样式加入新主题 |
| Bitmaps | 所有导入位图列表；**若 Bitmaps 特性启用**显示；工程编辑器内不可编辑位图 |
| Fonts | 所有导入字体列表；若 Fonts 特性启用显示；工程编辑器可做基础字体编辑 |
| Texts | 多语言 GUI 本地化文本；若 Texts 特性启用显示；详见 P12 |
| IEXT (EEZ-GUI only) | IEXT 扩展定义；若 IEXT defs 特性启用显示；一个工程可定义多个 |
| SCPI (EEZ-GUI only) | IEXT 中可访问的 SCPI 命令列表；若 SCPI 特性启用显示 |
| Shortcuts (EEZ-GUI only) | IEXT 中可访问的快捷键；若 Shortcuts 特性启用显示 |
| Changes | Git 仓库时所有 commits 列表；若 Changes 特性启用显示 |
| Checks | 后台持续查错（如错误表达式），列出在面板 |
| Output | 构建完成报告与发现的错误 |
| Search | 内容搜索与替换（见 P4.3.1） |
| References | 可查找 Variables/Struct/Enum/Page/Action/Style/Font/Bitmap 在项目中的所有使用处；右键“Find all references”后显示于此 |

> **手册文字瑕疵提醒**：原文对 Fonts / Texts / IEXT / SCPI / Shortcuts / Changes 均写“**will be displayed if the [feature] feature is disabled**”，逻辑上应为“**enabled**”（启用时显示）。本文按实际功能理解为“特性启用则显示该面板”，阅读原手册时需注意此反向措辞。

#### P4.3.1 Search and Replace（搜索与替换）
| # | Item | 说明 |
|---|---|---|
| 1 | Toggle Replace | 显示/隐藏 Replace 字段 |
| 2 | Search | 搜索内容（受 (4)(5) 条件约束） |
| 3 | Replace | 替换新内容 |
| 4 | Match Case | 区分大小写 |
| 5 | Match Whole Word | 全词匹配 |
| 6 | Refresh Search Result | 改条件后刷新 |
| 7 | Next Result | 下一结果 |
| 8 | Previous Result | 上一结果 |
| 9 | Replace Selected | 仅替换选中项 |
| 10 | Replace All | 替换全部 |
| 11 | Original content | 将被替换的原内容标记 |
| 12 | Replaced content | 新添加内容标记 |
| 13 | Selected item | 当前选中项（可用 (10) 替换或 (7)/(8) 移动） |

### P4.4 Debug 模式面板总览
| Panel | 说明 |
|---|---|
| Pages | 所有页面显示（不可编辑） |
| Actions | 所有 Actions 显示（不可编辑） |
| Active Flows | 活动 Flow 列表 |
| Watch | 执行期间所有变量及其当前值 |
| Queue | 排队等待执行的组件列表 |
| Breakpoints | 断点列表 |
| Logs | 执行日志，类型：Fatal、Error、Warning、Info、Debug、SCPI；可按条件过滤 |

---

## P5. 工程编辑器 / 查看器（Project editors/viewers）

### P5.1 Editors（编辑器）
工作区中央是编辑器 tabsets，可编辑一个或多个页面、工程特性（如 Settings）或 Actions。启用 EEZ Flow 时，页面与 Actions 编辑器出现在 Edit 模式。

| 编辑器 | 说明 |
|---|---|
| **Page editor** | 页面有两条辅助线确定左/上边界，起点 (x=0, y=0) 在左上角（Fig.46） |
| **User Actions** | 编辑 User Actions 面板中选中的 Action |
| **User Widgets** | 编辑 User Widgets 面板中选中的 Widget |
| **Font editor** | 显示字体所有字符，可增删字符；需通用设置启用 Fonts 特性 |
| **Shortcuts (EEZ-GUI only)** | 含 IEXT defs 的 EEZ-GUI 工程启用 Shortcuts 特性后，工具栏出现图标进入定义页 |
| **MicroPython (EEZ BB3 only)** | 打开 MicroPython 文本编辑器 |
| **Readme** | 通用设置启用 Readme 特性后存在；可加说明/提醒（如如何为原生平台构建）；支持 `.txt` 与 `.md`；可移除(1)或选文件路径(2)，可显示但不可编辑 |
| **Settings** | 编辑工程全局参数与特性（见 P13） |

### P5.2 Viewers（查看器）
- **Page viewer**：Run 模式仅看当前活动页面；Debug 模式页面/Action 不可编辑，编辑器即为查看器。
- **Action viewer**：Actions 显示且不可编辑；可见当前正执行的 Action 组件；Flow 暂停时可加断点并查看组件输入值。

---

## P6. EEZ Flow（流程图编程）

### P6.1 基本概念（Basic concepts）
EEZ Flow 用流程图给工程添加编程逻辑，是页面定义的一部分（Widgets 可交互、与 Actions/Widgets 通过 Flow 线相连），也可创建不含图形元素的 User Action。基本元素：

- **Widget** — 给页面添加可见图形元素；可与其他 Widget/Action 组合，可定义一或多个输入/输出（显示为左/右半圆）。
- **User Widget** — 把含图形元素的部分分组以便复用；用 **Input/Output Actions** 作连接点（半圆）。可从 User Widgets 面板 Add Item 创建，或从页面编辑器选中部分 → 右键 **Create User Widget**。
- **Action** — 页面上无可见元素，执行时仅完成某功能；通常至少含一个输入/输出连接其他组件。
- **User Action** — 把部分 Flow 分组复用；用 **Start、End、Input、Output** actions 作连接点。
- **Sequence Flow line（序列流线）** — 定义执行流。组件在序列输入收到执行信息（无数据传输，即“null data”）时执行；结束时通过序列输出发送“null data”给下一组件。未选中时显示为 **verdigris（蓝绿色）**。
- **Data Flow line（数据流线）** — 类似序列流线但连接数据输入/输出，沿线路**传输实际数据**（整数/字符串/结构体等）。未选中时为 **灰色**。

> **LVGL 嵌入式提示**：LVGL 工程的 Widgets 只能使用 LVGL 类型（见 P7.2），Flow 线连接方式与 EEZ-GUI 一致。

### P6.2 Flow 执行（Flow execution）
- EEZ Studio 允许同一工程内**多个 Flow 并行执行**；Debug 模式可监视（Fig.56）。
- 执行时保留所有全局变量当前值与活动 Flow 列表；任一时刻可有一个或多个活动 Flow。每个活动 Flow 保存：所有局部变量当前值、所有组件输入值、组件内部状态（如 Loop 记循环次数）。
- 所有活动 Flow **共享同一执行队列（execution queue）**；每次从队首取一个组件执行。
- 组件在 Flow 线收到数据后，若**所有数据输入**与**至少一个序列输入**（若存在）均收到数据，则入队等待执行。若无 Flow 线指向某输入，则该输入不参与此判定。
- 多个序列输入时（如 Loop 的 Start 与 Next），任一收到数据即就绪。
- 执行组件时：所有序列输入被清空（数据值清除），数据输入保留当前值（后续新数据到达仍可再次执行）。部分组件会自行清空某数据输入（其描述会特别说明）。
- **无输入的组件**在初始化时立即入队（如 **Start** 总立即执行）。
- **Catch error** 无输入但不立即执行，仅在 Flow 出错时执行。
- **OnEvent** 无输入，仅当页面事件（如 open page、close page）发生时执行。
- **Widgets 立即执行**（也参与 Flow：可收值/发值）。
- 保留内部状态、执行时间长的组件在调试器有**特殊图标**标记（如 Loop、Delay、SCPI）。这类组件可自我重新入队（如 SCPI 逐条执行命令并保留进度），实现 Flow 并行。

### P6.3 Flow 示例（Examples）
| Case | 行为 |
|---|---|
| #1 action_with_start | 实现 Start action，序列流输入为必选；1 秒 Delay 后显示结果 |
| #3 action_without_start | 序列流输入非必选，行为同 #1 |
| #4 | 序列流输入非必选，User Action 在启动即执行（Constant 传字符串显示） |
| #2 | 必选序列输入未连接 → **编辑器报错**；但**允许运行该 Flow**（便于边连边测） |

> 重要：Case #2 编辑器报错仍允许运行，方便未完全连接时测试已完成部分。

---

## P7. 工程编辑（Project editing）

### P7 概述：拖放添加 Widget
从 **Components Palette** 拖放一个或多个 Widget 到页面即可布局。拖动时光标变化；拖入编辑器区域立即出现**辅助对齐线（snap lines）**协助放置（靠近其它对象时相对它们对齐，或作为首个 Widget 时相对页面居中，Fig.61/62）。
- 若对齐线碍事，按住 **SHIFT** 移动可禁用对齐。
- **EEZ-GUI 与 LVGL 工程：若 Widget 超出页面边界（Fig.63），超出部分不可见。**

### 多选与对齐
- 多选方式：编辑器内 **SHIFT 逐个点选**、**橡皮筋框选（rubber band）**；或在 **Page Structure 面板**中用 SHIFT（连续）或 CTRL（不连续）选择。
- 多选后 Properties 面板显示选中多个；**Position and size** 区出现更多 Align 选项与完整 **Distribute** 子区。
- **Distribute 仅当选中 3 个及以上 Widget 时启用**。

**Align（对齐）**：
| 标题 | 说明 |
|---|---|
| Align left edges | 对齐到最左 Widget 左边缘 |
| Center on vertical axis | 垂直居中到最宽 Widget 中心 |
| Align right edges | 对齐到最右 Widget 右边缘 |
| Align top edges | 对齐到最上 Widget 上边缘 |
| Center on horizontal axis | 水平居中到最高 Widget 中心 |
| Align bottom edges | 对齐到最低 Widget 下边缘 |

**Distribute（分布，3+）**：左边缘/中心/右边缘等距分布；水平/垂直间距相等；顶/底边缘等距分布（详见手册 P.45 表格）。

### 页面缩放与滚动（Fig.66）
| 操作 | 说明 |
|---|---|
| CTRL + 鼠标滚轮 | 缩放页面 |
| SHIFT + 鼠标滚轮 | 水平滚动 |
| 鼠标滚轮 | 垂直滚动 |
| 中键/右键拖动 | 移动页面 |
| 双击 | 重置缩放并居中 |
| 拖放 | 移动选中 Widget |

### P7.1.1 连接 Flow 组件（Connecting Flow components）
- 从一组件输出拖到另一组件输入：放到输出 (1) 背景变色，拖动出现 Flow 线 (2)，到达输入时变绿 (3)，释放即建立连接 (4)；移动组件时线随之移动。
- 也可从输入拖到输出。
- **可连多条 Flow 线到同一输出（输入同理）**。
- 删除：选中 Flow 线（变红）后右键 Delete 或按 **DEL**。
- **移动多条线**：到输出时光标与所有相关线 (1) 变色，按住 **SHIFT** 拖动出现副本，到新输出变绿 (3) 释放即重连。

### P7.1.2 跨工程复制粘贴（Copy & Paste between two projects）
- 用 **File → New Window（CTRL + SHIFT + N）** 打开两个 EEZ Studio 窗口。
- 在源工程选中要复制的区块 → 右键 Copy（或 CTRL + C）。
- 在目标工程右键 Paste（或 CTRL + V）粘贴。

### P7.2 使用 Widgets
- Widget 快速添加图形；位于 Components Palette 的 **Widgets 子标签**，按组归类。
- **EEZ Studio 支持两类不可混用的 Widget**：
  - **EEZ-GUI (Native)** — 为 STM32 系列 MCU 嵌入式 GUI 设计（Fig.70）。
  - **LVGL** — 开源 LVGL 库控件，**只能用于 LVGL 类型工程**（Fig.71）。→ **嵌入式 LVGL 9.4 设备必须且只能使用 LVGL 类型 Widget。**

#### P7.2.1 Widget 组件项（Fig.72, Table 2）
| # | Item | 说明（手册标注为 mandatory，见下方提醒） |
|---|---|---|
| 1 | Selection handlers | 选中时出现，可各方向缩放 |
| 2 | Sequence Output | 序列输出 |
| 3 | Sequence Input | 序列输入 |
| 4 | Data Input | 数据输入 |
| 5 | Data Output | 数据输出 |

> **User Widget 引脚类型（Table 2）**：Sequence input pin、Sequence output pin、Data input pin、Data output pin。
> **手册措辞提醒**：原文将 Sequence Output / Sequence Input / Data Input / Data Output 均标为“must be connected, otherwise it will generate an error”。实际 EEZ Flow 中并非所有引脚都是强制的（Action 区分 mandatory/optional，见 P7.3.1）；Widget 的描述在手册里统一写成强制，但实践中应依据具体 Widget 类型的引脚定义判断。以组件上引脚是否为空心/实心或属性面板说明为准。

#### P7.2.2 创建 User Widget
- **方式一（面板）**：选 User Widgets 面板 (1) → Add (2) → 输入名称对话框 (Fig.73) → 确认 (4) 后出现于列表，选中即开编辑器添加 Widgets/Actions。
- **方式二（右键）**：在页面选中一个或多个组件 (1) → 右键 **Create User Widget** → 同名对话框。
- 默认新建的 User Widget 页面尺寸取自工程通用 Settings（示例 480 x 272），继承默认样式（背景深蓝），起点 (x=0, y=0)。
- 用方式二创建的 User Widget 尺寸等于原选区，首个组件位于起点。
- User Widget 可包含多个 User Widget 与 User Action。

### P7.3 使用 Actions
- 内置 Actions 位于 Components Palette 的 **Actions 子标签**，拖放添加，按组归类；**实现数量取决于工程类型**（Fig.77 Dashboard / Fig.78 LVGL）。
- Action 也可由 EEZ Studio 扩展实现（如 Postgres，属 eez-Flow-ext-postgres 组）。
- 用户可定义 **User Actions**，在 User Actions 编辑器编辑；所有 User Actions 列于 Actions 子标签底部 (1)，可像普通 Action/Widget 一样拖放添加。

#### P7.3.1 Action 组件项（Fig.79, Table 3）
| # | Item | 说明 |
|---|---|---|
| 1 | Icon | 组件图标（不可改） |
| 2 | Name | 组件名（不可改） |
| 3 | Mandatory sequence inputs | 必选序列输入，须连接否则报错 |
| 4 | Mandatory sequence output | 必选序列输出，须连接否则报错 |
| 5 | Optional sequence output | 可选序列输出，不连也能正常执行 |
| 6 | Additional information | 可选显示附加信息 |
| 7 | Description | 属性中定义的组件描述 |
| 8 | Optional sequence input | 可选序列输入，不连也能正常执行 |
| 9 | Mandatory data output | 必选数据输出，须连接否则报错 |

> **Action 引脚类型（Table 3）**：Mandatory sequence input/output、Optional sequence input/output、Mandatory data input/output、Optional data input/output。
> **手册瑕疵提醒**：第 9 项标题写“Mandatory data output”，描述却写“The mandatory data input must be connected...”；按 Table 3 应为数据输出引脚。理解时以引脚类型表为准。

#### P7.3.2 创建 User Action
- 用 User Actions 提升 Flow 可读性与模块化。
- **允许 User Action 添加到自身**，但须注意连接方式避免执行时**无限循环**。
- Fig.82 展示序列/数据流线如何影响组件在 Action 调色板中的外观。

---

## P13. 设置（Settings）

工程 Settings 用于配置工程，参数与特性数量取决于工程类型。

### P13.1 General（通用设置）
| Item | 说明（含 LVGL 相关） |
|---|---|
| **Project type** | 工程类型，**创建时生成、之后不可改**；支持：Dashboard、EEZ-GUI、LVGL、BB3 MicroPython Script、BB3 Applet（描述见 P1.1） |
| Target BB3 firmware (BB3 MP only) | 支持版本：1.7.X or older / 1.8 or newer |
| Master project (BB3 only) | 创建时填入 BB3 固件工程名（modular-psu-firmware.eez-project），可改 |
| **Extensions** | 工程所用扩展列表；可增删、调加载顺序（顺序对代码执行影响不大） |
| Import | 工程使用的外部工程列表 |
| Title (Dashboard only) | 独立应用/仪表盘名称 |
| Icon (Dashboard only) | 图标 |
| **Display width (EEZ-GUI & LVGL only)** | 页面宽度（像素） |
| **Display height (EEZ-GUI & LVGL only)** | 页面高度（像素） |
| **Flow support (EEZ-GUI & LVGL only)** | 启用 EEZ Flow；**LVGL 工程需勾选此项才能用 EEZ Flow 编程**（对应 P3 的模式切换器显示条件） |
| Description / Image / Keywords | Examples 区展示用 |
| Target platform / Target platform link | Examples 区展示 |
| Author / Author link | Examples 区展示 |
| Min. studio version | 运行示例所需最低 Studio 版本；大于当前版本则示例不显示 |
| Resource files | 示例所用外部文件（如 .py、.csv） |
| **Project features** | 特性数量随工程类型变化（EEZ-GUI 见 Fig.144），含 Bitmaps、Fonts、Texts、IEXT defs、SCPI、Shortcuts、Changes、Readme、MicroPython 等 |

> **LVGL 嵌入式设备关键**：创建工程时选 LVGL 或 LVGL with EEZ Flow；在 General 中设置 **Display width/height**（与硬件屏分辨率一致）、按需勾选 **Flow support**；在 **Project features** 中启用所需特性（如 Fonts、Bitmaps、Texts）以显示对应面板。

### P13.2 Build（构建，仅 EEZ-GUI 与 LVGL 工程）
| Item | 说明 |
|---|---|
| **Destination folder** | 构建文件输出文件夹 |
| **LVGL include (LVGL only)** | 指向 `lvgl.h` 头文件路径；通常为 `lvgl/lvgl.h`，若位置不同可在此指定 |
| **Generate source code for EEZ Flow engine (eez-framework)** | 当 LVGL 工程使用 EEZ Flow（General 中勾选 Flow support）且此项勾选时，Studio 在目标文件夹生成在目标平台构建所需全部文件（**无需额外 EEZ 库**）。额外生成文件： |
| | • `eez-flow.h` / `eez-flow.cpp`（基础） |
| | • 勾选 “Compress flow definition” 时额外：`eez-flow-lz4.h` / `eez-flow-lz4.c` |
| | • 工程用到 `Crypto.sha256` 表达式函数时额外：`eez-flow-sha256.h` / `eez-flow-sha256.c` |
| | 由于 `eez-flow.cpp` 是 C++ 源文件，**需启用 C++ 编译**。若不勾选此项，则需手动包含 eez-framework 库。**此项默认勾选**（最简启用 EEZ Flow 方式） |

#### 影响 FLASH/SRAM 的选项
- **Compress flow definition**：勾选则包含 LZ4 库（`eez-flow-lz4.h/.c`）。**关心 FLASH 用量则压缩；关心 SRAM 用量则不勾选**。**新建工程默认不勾选**。
- **Execution queue size**：取决于 Flow 复杂度；**高级选项，通常不改**。默认值够大多数情况；想省 SRAM 可尝试调小；若执行开始报错说明队列过小。
- **Expression evaluator stack size**：取决于表达式中复杂度；**高级选项，通常不改**。默认值够用；想省 SRAM 可尝试调小；若报错说明过小。

> **嵌入式 LVGL 9.4 设备导出要点**：
> 1. Destination folder 设为固件工程可引用的目录。
> 2. LVGL include 指向你设备 SDK 中 `lvgl.h` 的实际路径（默认 `lvgl/lvgl.h`）。
> 3. 用 EEZ Flow 时保持 **Generate source code for EEZ Flow engine** 勾选（默认），并启用 C++ 编译。
> 4. 资源受限设备：FLASH 紧张 → 勾选 Compress flow definition；SRAM 紧张 → 不勾选，并可适当调整 Execution queue size / Expression evaluator stack size（但勿过小以免运行报错）。

### P13.2.1 Configurations（仅 EEZ-GUI）
- 一个工程可定义多个构建配置（如：同一工程既构建硬件板原生固件又构建模拟器，且互不包含对方专属资源）。
- 对 **Page、Action、SCPI command、Shortcut、Variable** 可用 **Used in** 属性（Fig.145）指定所属配置。
- 构建配置参数（Fig.146）：Name、Description、Properties（IEXT 用，JSON 格式指定额外选项）。

### P13.2.2 Files（仅 EEZ-GUI 与 LVGL）
- 列出用于生成源文件的**模板源文件列表**，在工程创建向导中已准备好。

---

## 速查：为嵌入式 LVGL 9.4 设备生成 UI 工程的推荐流程

1. **首页 Create** → 选 **LVGL** 或 **LVGL with EEZ Flow**（需 EEZ Flow 编程逻辑时选后者）。
2. 填 **Name / Location / Create directory**；确认 **Project details** 显示正确的 LVGL 库版本。
3. 进入 Edit 模式 → **Settings（General）**：设 **Display width/height**（匹配硬件屏）、按需勾选 **Flow support**、在 **Project features** 启用 Fonts / Bitmaps / Texts 等。
4. 从 **Components Palette → Widgets（LVGL 类型）** 拖放控件布局；用 **Pages** 面板管理页面（列表首个为启动页，页面名禁含 `.`）。
5. 用 **EEZ Flow** 连接 Widget/Action（序列流线蓝绿、数据流线灰）；用 **User Widget / User Action** 模块化复用。
6. **Settings → Build**：设 **Destination folder**、**LVGL include**；用 EEZ Flow 时确认 **Generate source code for EEZ Flow engine** 勾选（默认），并据此决定是否 **Compress flow definition**（FLASH/SRAM 权衡）。
7. 工具栏 **Check（CTRL+K）** 检查 → **Build（CTRL+B）** 构建；输出到 Destination folder 的 C++ 源文件纳入你的固件工具链（需启用 C++ 编译）。
8. 可选：用 **Run / Debug** 模式在仿真中验证交互；Debug 模式可监视 Active Flows / Watch / Queue / Logs。

### 常见坑（Gotchas）
- 页面名不能含 `.`（导入分隔符冲突）。
- 列表**首个页面**为启动页。
- LVGL 工程只能用 **LVGL 类型 Widget**，不能与 EEZ-GUI Native Widget 混用。
- Widget 超出页面边界部分在 EEZ-GUI/LVGL 下**不可见**。
- Debug 模式**不能停靠进边框 tabset**，也不能修改工程。
- EEZ Flow 中未连接必选序列输入的组件会在编辑器报错，但**仍允许运行**测试。
- 跨工程复制需 **New Window（CTRL+SHIFT+N）** 开两个窗口；Scrapbook 比剪贴板持久（重启不丢），适合在不同工程间搬运资源。
- **Python 设置**影响 LVGL 构建时图片转换所用解释器，需与终端 pip 安装环境一致。
- 手册若干处存在反向/笔误措辞（面板“disabled”实为“enabled”、Widget 引脚全标 mandatory、Action data output 描述误写 input），已在上文逐一标注，以实际功能/引脚类型表为准。
- 运行时许可证可选 MIT/BSD 2.0/Public Domain，便于闭源固件集成；Studio 本体为 GPL v3。
