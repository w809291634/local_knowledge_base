# VMware 虚拟机：Ubuntu 共享文件夹 / 全屏 / ssh 连 NAT / VPN

> 适用：VMware Workstation/Player + Ubuntu 20.04/22.04 客户机
> 来源：《问题解决和汇总 v1.2》"VMware虚拟机相关问题"章节
> 目标：虚拟机与宿主机协作的常用配置一次配好。

## 结论先行

- 共享文件夹用 **open-vm-tools**（别折腾 VMtools 按钮灰色/换 ISO），挂载用 `vmhgfs-fuse`，开机自动挂载写进 fstab/rc.local。
- ssh 连 NAT 模式虚拟机靠 **端口转发**；虚拟机走 VPN 分 NAT 与桥接两种接法。

## 1. Ubuntu 20.04 共享文件夹（VMtools 按钮灰色也能装）

1. 客户机内直接装：`sudo apt-get install open-vm-tools`；
2. 部分情况需关机一次；
3. 关机状态下：虚拟机→设置→选项→共享文件夹→总是启用，选好宿主机路径；
4. 客户机内 `mkdir -p /mnt/hgfs`，挂载：`sudo vmhgfs-fuse .host:/ /mnt/hgfs -o nonempty -o allow_other`；
5. 上述挂载重启失效，把挂载命令写入开机脚本实现自动挂载（`/etc/fstab` 加 `.host:/ /mnt/hgfs fuse.vmhgfs-fuse allow_other 0 0` 或 rc.local）。

## 2. Ubuntu 22.04 无法全屏 / 无法复制文件

- 装增强工具时若报段错误，忽略报错多试几次：`sudo apt install open-vm-tools open-vm-tools-desktop`；
- 装完重启进入全屏、剪贴板互通。

## 3. ssh 连接 NAT 模式虚拟机

NAT 下宿主机无法直接 ssh 到客户机 IP，用 VMware **虚拟网络编辑器配置端口转发**（宿主端口 → 客户机 IP:22）。详细步骤见 ESP32 资料的 matter 章节（原文档标注）。

## 4. 虚拟机连接 VPN

- NAT 方式与**桥接方式**两种接法，各有适用场景；详细步骤见 ESP32 资料的 matter 章节（原文档标注）。
- 桥接时虚拟机与宿主机同网段，注意 VPN 客户端的"虚拟网卡"绑定顺序。

## 5. 其他

- 客户机里 firefox 卡住：同样见 ESP32 matter 章节资料（原文档标注）。
