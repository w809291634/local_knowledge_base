# -*- coding: utf-8 -*-
"""
fig_tools —— Word 文档插图（框图/流程图/拓扑图）通用绘制原语
================================================================
目标：让「绘图」这件事像写文档一样可复用、可自检，避免手工凑坐标导致
      文字压框、箭头指错、元素重叠。

三条硬规则（对应历史上踩过的坑）：
  1) **1 数据单位 = 1 英寸**：figsize=(W,H) + axes 占满 figure + xlim/ylim=(0,W)/(0,H)，
     字号 pt 可直接换算成图内尺寸，排版可预估。
  2) **方框一律用 Rectangle**（不用 FancyBboxPatch）：边界严格等于 (x,y,w,h)，
     这样箭头端点才能由 box_edge() 精确算出，不会指到框里或框外。
  3) **图内不写图名**：图名交给 Word 图题（居中加粗），否则与图题重复。

用法（典型）：
    from fig_tools import canvas, box, arr, edge, txt, save, flow, warn_report
    fig, ax = canvas(14, 9)
    mcu = box(ax, 5.3, 3.7, 3.4, 1.9, 'STC8H1K16\\n(8051 内核)', fs=9.5)
    u1  = box(ax, 0.7, 7.4, 3.2, 1.0, 'UART1 调试串口\\nP3.0/P3.1', fs=8.5)
    arr(ax, edge(u1, 'bottom'), edge(mcu, 'top', 0.2))     # 端点自动落框边
    save(fig, 'fig1.png')
    print(warn_report())        # 文本宽度溢出预警，应为空
"""
import matplotlib
matplotlib.use('Agg')                      # 无显示环境（headless）
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch

plt.rcParams['font.family'] = 'SimHei'     # 中文字体；缺字可换 SimSun/Microsoft YaHei
plt.rcParams['axes.unicode_minus'] = False

# 统一配色（可按项目覆盖）
C_EDGE = '#3D85C6'
C_TXT = '#1A1A1A'
C_LAYER = ['#D6E4F0', '#D9EAD3', '#FFF2CC', '#F4CCCC']   # 分层底色
C_WARN = '#FFCDD2'
C_NOTE = '#555555'

_WARNINGS = []


def canvas(w, h):
    """创建画布：W/H 单位英寸，1 数据单位 = 1 英寸。"""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1])        # axes 占满，保证比例==数据比例
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig, ax


def rect(ax, x, y, w, h, fc='white', ec=C_EDGE, lw=1.2):
    """矩形框（边界 == (x,y,w,h)），返回 box 元组供 edge() 使用。"""
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw))
    return (x, y, w, h)


def txt(ax, x, y, s, fs=9, color=C_TXT, weight='normal',
        ha='center', va='center'):
    ax.text(x, y, s, fontsize=fs, color=color, weight=weight,
            ha=ha, va=va, linespacing=1.35)


def est_w(s, fs):
    """粗略估算文本宽度（英寸）：中文≈1.0em，西文≈0.55em。"""
    return sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in s) * fs / 72.0


def box(ax, x, y, w, h, s='', fc='white', ec=C_EDGE, fs=9, lw=1.2,
        weight='normal', tag='', pad=0.14):
    """矩形框 + 居中文本；文本超框宽时记入预警（不发散、不静默）。"""
    rect(ax, x, y, w, h, fc=fc, ec=ec, lw=lw)
    if s:
        need = max(est_w(ln, fs) for ln in s.split('\n'))
        if need > w - pad:
            _WARNINGS.append('[宽度预警] %s: 需≈%.2f in > 框宽 %.2f in -> %s'
                             % (tag or s[:8], need, w, s.replace('\n', '/')[:36]))
        txt(ax, x + w / 2, y + h / 2, s, fs=fs, weight=weight)
    return (x, y, w, h)


def edge(b, side, t=0.5):
    """取框 b 某条边上的点；t 为沿边比例(0~1)。箭头端点一律用它算。"""
    x, y, w, h = b
    return {'top': (x + w * t, y + h), 'bottom': (x + w * t, y),
            'left': (x, y + h * t), 'right': (x + w, y + h * t)}[side]


def arr(ax, p1, p2, color=C_EDGE, lw=1.5, style='-|>'):
    """箭头：p1/p2 一般由 edge() 给出，保证首尾都贴在框边界上。"""
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, color=color,
                                 lw=lw, mutation_scale=12, shrinkA=0, shrinkB=0))


def circle(ax, cx, cy, r, fc='#FFD54F', ec='#F57F17', lw=1.3):
    ax.add_patch(Circle((cx, cy), r, fc=fc, ec=ec, lw=lw))


def flow(ax, steps, bx, top, bw=5.0, bh=0.9, bg=0.55, fs=10, notes=None,
         note_dx=0.3):
    """竖向流程图：steps=[(文本, 底色), ...]；notes={序号: 右侧注释}。

    返回画布所需总高（供 canvas 计算 H）。首节点绿框、末节点红框。
    """
    n = len(steps)
    for i, (s, fc) in enumerate(steps):
        y = top - bh - i * (bh + bg)
        ec = '#2E7D32' if i == 0 else ('#C62828' if i == n - 1 else C_EDGE)
        box(ax, bx, y, bw, bh, s, fc=fc, ec=ec, lw=1.6, fs=fs, weight='bold', tag=s[:10])
        if i < n - 1:
            arr(ax, (bx + bw / 2, y), (bx + bw / 2, y - bg), lw=1.8)
        if notes and i in notes:
            txt(ax, bx + bw + note_dx, y + bh / 2, notes[i], fs=8.5,
                va='center', ha='left', color=C_NOTE)
    return n * bh + (n - 1) * bg


def save(fig, name, out_dir='.', dpi=200):
    import os
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=dpi, facecolor='white')
    plt.close(fig)
    return path


def warn_report():
    """返回宽度预警文本（空字符串表示无预警）。生成后应打印它自检。"""
    return '\n'.join(_WARNINGS)


def reset_warnings():
    _WARNINGS.clear()
