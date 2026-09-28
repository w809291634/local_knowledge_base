# Linux / ROS 环境与 shell 问题合集（ssh / desktop 自启 / 信号处理 / 依赖）

> 适用：Ubuntu 18.04/20.04（ROS melodic/noetic）开发机与板卡
> 来源：《问题解决和汇总 v1.2》"linux系统 ROS"章节（12 条）+ 相关 C 编程条目
> 目标：环境差异类问题（登录 shell、桌面自启、退出信号、依赖）的处置清单。

## 结论先行

- ssh 登录后命令找不到（roslaunch 等）→ 默认 shell 不是 bash 或 profile 没加载 `.bashrc`。
- 桌面 `.desktop` 启动的脚本**环境变量与终端不一致**，缺的变量在 `Exec=` 里用 `env` 前缀补。
- ROS 下别用 ctrl+c 当"正常退出"，服务调用会 `Errno 4 Interrupted system call`——收尾逻辑放 `rospy shutdown` 回调。

## 1. ssh 登录后 .bashrc 不执行（roslaunch 找不到命令）

1. **查默认 shell**：`echo $SHELL`，不是 `/bin/bash`（常见 `/bin/sh`）就改：`chsh` 后输入 `/bin/bash`，重新登录；
2. 仍是 bash 还不行 → **profile 文件缺加载**：把加载 `.bashrc` 的段落补进 `/etc/profile` 或用户 profile（Ubuntu 实测有效）。

## 2. 桌面 .desktop 运行 .sh 环境变量不一致

桌面启动的脚本不继承终端环境。修法：`Exec=` 行固定用 `env` 前缀跟环境变量再跟命令（**注意空格**）：

```
Exec=env LD_LIBRARY_PATH=/xxx/lib bash '/home/tianbot/arm_server_desktop.sh'
```

典型场景：程序在终端能跑、desktop 启动报"找不到 so"——把 so 路径用 env 加进 LD_LIBRARY_PATH。

## 3. ctrl+c 与 ROS 服务收尾（Errno 4）

- 现象：ctrl+c 触发 `ServiceException: transport error ... [Errno 4] Interrupted system call`——SIGINT 杀程序导致服务器连接中断；
- 错误做法：靠 ctrl+c"顺便"完成回退动作；
- 正确做法：**注册 rospy shutdown 回调**，shutdown 之后仍执行机械臂回退等服务；ctrl+c 只作异常退出兜底。

## 4. Gazebo / RViz 联动

| 问题 | 修法 |
|---|---|
| universal_robot 的 gazebo launch 无法与 rviz 联动（缺控制器报错） | `sudo apt install ros-melodic-joint-trajectory-controller` |
| `No p gain specified for pid` 刷屏 | 可忽略 |
| gazebo 图片不显示 | 关闭层（不显示立方体）排查墙纸视角；demo 显示异常 `echo "export SVGA_VGPU10=0" >> ~/.bashrc` |

## 5. ROS 杂项

- **python 找不到自定义 srv**（`from moveit_simple_grasps.srv import ...` 失败）：删 src 里残留 CMakeLists 缓存，在对应包 package.xml 补依赖。
- **catkin 编译报错**：先看内存——RAM 占满也会编译报错。
- **rviz tf 转换错误（noetic）**：多个 joint_state/robot_state 节点只留一个；用 move_planer 替代运动学控制插件（详见 python 篇第 7 节）。

## 6. 系统依赖与挂载

- **apt 依赖地狱**：装 `aptitude`（`apt-get install -y aptitude`），用它装目标包，交互提示保持版本不变选 `n`，后续选 `y`（root 权限下操作，忘密码先重置）。
- **挂载 exfat 报 `unknown filesystem type 'exfat'`**：`sudo apt-get install exfat-fuse exfat-utils`。
- **apt update 源**：该机器网络环境下用官方源，不用清华源（设置 main server）。

## 7. Linux C 编程：线程里 popen 段错误

现象：`pthread_create` 的线程中调 `popen` 段错误（`_IO_fgets`）。
根因：编译时有 `warning: implicit declaration of function 'popen'`——头文件里没有该函数声明，按 2 字节返回处理导致栈错位。
修法二选一：① 编译选项改 `-std=gnu99`；② 手动声明函数原型（参考 vnode 工程 ros-sensor.c 的做法）。

## 8. 未解决留档

- c++ 动态库/静态库的使用与第三方包安装（待系统化成篇）。
