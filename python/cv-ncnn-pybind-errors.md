# Python / OpenCV / pybind / ncnn / YOLO 常见错误合集

> 适用：Linux（Ubuntu18/20 实测）+ Python2/3 混合环境 + OpenCV + ncnn + pybind + YOLO 推理
> 来源：《问题解决和汇总 v1.2》"python库的常见错误 / 深度学习"章节（27 条，已合并重复 3 处）
> 目标：一眼对号入座的错误速查表；按"错误 → 根因 → 修法"组织。

## 结论先行

三条元经验：① **多线程里 OpenCV imshow/waitKey 必须放同一线程（优先主线程）**，这是视频窗口卡死/不刷新的万能答案；② **百度搜不到的符号错误去 github issues 搜**（pybind `undefined symbol: __cpu_model` 案例）；③ 大量"突然报错"是**版本组合**问题（Pillow/protobuf/gcc），先怀疑最近动过的包。

## 1. OpenCV / 多线程显示

| 错误 | 根因 | 修法 |
|---|---|---|
| 两个视频窗口卡住 / imshow 失效、不显示、不刷新、卡死（3 处重复案例合并） | 多线程各自调 imshow/waitKey | **所有 imshow/waitKey 收拢到一个线程**（优先主线程）；两个窗口代码间加等待延时；实测 py3.8 + cv3.45 组合下"显示放主线程"稳定 |
| `cv::Exception ... The function is not implemented. Rebuild the library with GTK` | 编译的 opencv 缺 GUI 后端 | `sudo apt-get install build-essential libgtk2.0-dev pkg-config` 后重装；**建议直接 apt 源安装 opencv**，cmake find_package 也能找到 |
| `cv2.error ... window.cpp:665` | 同上（安装不兼容） | 同上，重装/换源 |
| `VIDIOC_DQBUF: Resource temporarily unavailable` | 摄像头兼容性 | 设置 USB 兼容性为 3.0 |
| `TypeError: 'tuple' object is not callable`（cvwin） | 命名/逻辑错误：窗口对象名与函数/变量冲突，`namedWindow` 被当元组调用 | 检查命名冲突，删除错误赋值（文档中两处重复记录，此处已合并） |

## 2. Python 语言 / 环境类

- `TypeError: super() argument 1 must be type, not classobj`：Python2 旧式类导致——类必须继承 `object`（新式类）；Python3 无此问题。
- `UnboundLocalError: local variable 'aiarm' referenced before assignment`：类名与实例名重名引起，命名错开。
- `ValueError: too many values to unpack` 两个检查点：① 遍历字典要用 `dict.items()`；② 函数返回值个数与接收变量数对齐（多返回值要全接，不用也要写）。
- 线程 target 传函数**不要带括号**（`Thread(target=func)`），否则主线程逻辑被抢跑。
- `is not JSON serializable`：图像等二进制数据先转 UTF-8/编码后再序列化。
- `/usr/bin/env: "python\r": 没有那个文件或目录`、`/bin/bash^M: 解释器错误`：Windows 换行符污染，`dos2unix` 处理对应脚本。
- `ModuleNotFoundError: No module named 'sklearn'`：装 scikit-learn。
- `RuntimeError: dictionary changed size during iteration`：迭代中改字典，先拷贝 keys。
- 指定系统默认 python3：处理 `/usr/bin/python` 软链接（改名 .bk 备份、删软链重建、还原同理）。

## 3. 版本组合类（先怀疑最近动过的包）

| 错误 | 修法 |
|---|---|
| `AttributeError: 'ImageDraw' object has no attribute 'textsize'` | Pillow 10 移除了 textsize → 降级 Pillow |
| `TypeError: Descriptors cannot be created directly.` | protobuf 版本太高 → 降版本 |
| `declarative() got an unexpected keyword argument 'full_graph'` | PaddleDetection 2.6 trainer 代码与 paddle 版本不匹配，按仓库 issue 对齐版本 |
| `undefined symbol: __powf_finite` | gcc/glibc 版本组合，重编依赖 |

## 4. pybind / ncnn / so 库

- **`undefined symbol: __cpu_model`（#516）**：gcc 版本低导致；CMakeLists 指定对应参数后重编。排查手法：`ld` 查看 so 的未定义引用；**百度无解就去 github issues**（本项目实战命中）。
- **`ImportError: ... undefined symbol: _ZN14Ncnn_DetectionD1Ev`**：so 与头文件/编译单元不一致，统一重编。
- **`fatal error: Python.h: 没有那个文件或目录`**：CMake 里没指对 Python include 路径。
- **`libjsoncpp.a: 无法添加符号: 错误的值`**：静态库没加 `-fPIC`——在 jsoncpp 的 CMakeLists 加上后重编替换 .a。
- **ncnn 报 `network graph not ready`**：必须**先 load param 再 load model**，顺序不能反。
- **普通 ELF 重定位错误**：ncnn 静态库版本不一致，换成目标平台可用的 ncnn 包。

## 5. 数据/训练类（YOLO/VOC）

- `yolov5 train: ... 624 found, 0 missing, 624 empty`：转换出的 label 全空——**文件名大小写写错**（大写开头→小写）。
- `voc2yolo.py ZeroDivisionError: float division by zero`：个别标注文件 size 字段异常；在脚本里加打印把坏文件揪出来（案例为 new-207）后修正。
- `rospy.init_node ValueError: Unknown level: 'DEBUG'`：先 import 了重模型驱动（RKNN）导致 ros 日志初始化异常——**先 ros 初始化，再 import 模型驱动**。

## 6. Ubuntu18.04 安装 opencv 完整顺序（避坑版）

1. `apt install python3-pip` → 2. `apt install cmake` → 3. pip 指定国内镜像（推荐阿里/清华，http 源要加 `--trusted-host`）→ 4. `ModuleNotFoundError: No module named 'skbuild'` → `pip3 install scikit-build` → 5. `Running setup.py bdist_wheel for opencv-python` 卡住 → `pip3 install --upgrade pip` → 6. `pip3 install opencv-python / opencv-contrib-python`。

## 7. 其他

- **flask 与 ROS 节点共存**：主程序头部加相应初始化代码后，ros 层节点通讯与函数接口可同时使用（详见原文档截图）。
- **`os.system('bash start_pick.sh')` 后代码不继续执行**：脚本末尾用 `&` 连接一个 echo，让命令立即返回。
- **rviz tf 报错（noetic）**：① 启动了多个 joint_state/robot_state 节点，只留一个；② 用 move_planer，别用运动学控制插件。
