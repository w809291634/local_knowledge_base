#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""font_verify.py —— 「后台烘焙的字体 == EEZ Studio GUI 产物吗」的可执行判据

为什么需要它
------------
自己搭了一套后台烘焙（解包 EEZ 自带引擎 / 任何旁路生成）之后，**最大的风险不是
跑不起来，而是「跑起来了但和官方产物不一样」** —— 差几个空行、差一个 include、
差几个字形，编译照样过、上屏才豆腐。肉眼根本看不出来。

本工具把这条判据固化成三条命令：

    snapshot   把「官方真值」存成黄金样本
    check      拿当前产物和黄金样本**逐字节**比对，不一致就定位 + 猜成因
    metrics    比对字号度量（line_height / base_line），看布局会不会漂移

只依赖标准库。

★ 黄金样本的唯一合法来源
------------------------
**必须是 EEZ Studio GUI 点 Build 的产物**，不能是任何脚本产物 —— 否则就是
「自己给自己当裁判」，一致也证明不了任何事。
snapshot 会把来源、时间、每个文件的 sha256 记进 `_manifest.json`，
下次 check 时如果发现样本本身被脚本产物覆盖过，会有迹可循。

用法
----
    # 1) 在 EEZ Studio 里 Check and Build 之后，立刻存真值
    python tools/font_verify.py snapshot --src src/ui --golden .golden_fonts

    # 2) 换成后台烘焙的产物，再比对
    python tools/font_verify.py check --src src/ui --golden .golden_fonts

    # 3) 顺带看度量有没有漂移
    python tools/font_verify.py check --src src/ui --golden .golden_fonts --metrics

    # 完整对照实验（最硬的那一条）：见本文件末尾 EXPERIMENT 注释

退出码：0 = 全部一致；1 = 有不一致；2 = 用法/环境错误。
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

FONT_RE = re.compile(r"^ui_font_.+\.c$")

# ------------------------------------------------------------------ 差异成因表 --
#  symptom 判定函数 -> (结论, 该去查什么)
#  顺序敏感：先判最具体的（二进制乱码 / include），再判泛化的（空行 / 末尾）
def _diagnose(gold, mine):
    """比对两份字节，返回 [(结论, 排查方向)]。"""
    tips = []

    # 坑：C 源码被当成 base64 误解码 -> 出一堆非 ASCII 控制字符
    def printable_ratio(b):
        if not b:
            return 1.0
        ok = sum(1 for c in b if 32 <= c < 127 or c in (9, 10, 13))
        return ok / len(b)

    if printable_ratio(mine) < 0.9 and printable_ratio(gold) > 0.9:
        tips.append((
            "产物是二进制乱码 —— 你把 C 源码当 base64 解了",
            "EEZ worker 对两个返回值都写 .toString(\"base64\")，但 C 源码是**字符串**：\n"
            "         String.prototype.toString(enc) 会忽略编码参数原样返回，所以它根本没被编码。\n"
            "         只有 bin 是 Buffer、才是真 base64。按首字符是不是 '/' 区分。"))
        return tips

    # 换行符差异会**淹没真正的差异**（首处不同会落在第 0 行的 \r 上），
    # 所以先单独报出来，再把两边归一化成 LF 继续诊断。
    crlf_g, crlf_m = b"\r\n" in gold, b"\r\n" in mine
    if crlf_g != crlf_m:
        tips.append((
            "换行符不同：黄金 %s / 你的 %s" % ("CRLF" if crlf_g else "LF",
                                            "CRLF" if crlf_m else "LF"),
            "EEZ 产物是 **LF**。Python 写文件时默认 newline 转换会把 \\n 变成 \\r\\n，\n"
            "         用 open(p,'w',encoding='utf-8',newline='\\n')；Node 的 writeFileSync 默认就是 LF。"))
    gold = gold.replace(b"\r\n", b"\n")
    mine = mine.replace(b"\r\n", b"\n")

    try:
        g = gold.decode("utf-8")
        m = mine.decode("utf-8")
    except UnicodeDecodeError:
        tips.append(("两边编码不一致（有一边不是 UTF-8）", "检查写入时用的 encoding"))
        return tips

    gl, ml = g.split("\n"), m.split("\n")

    # 坑：lv_include 取错
    inc_g = [l for l in gl if "#include" in l and "lvgl" in l]
    inc_m = [l for l in ml if "#include" in l and "lvgl" in l]
    if inc_g != inc_m:
        tips.append((
            "lv_include 不一致：黄金 %r vs 你的 %r" % (inc_g, inc_m),
            "lv_include 取自 **settings.build.lvglInclude**（工程设置 → Build → LVGL include），\n"
            "         不是字体条目上的字段。默认成 'lvgl/lvgl.h' 就说明没读到这个设置。"))

    # 坑：落盘后处理（折叠多余空行）
    def collapse(s):
        return re.sub(r"\n{3,}", "\n\n", s)

    if g != m and collapse(g) == collapse(m):
        tips.append((
            "只差在**连续空行**上",
            "EEZ 落盘前会折叠连续空行：连续 3+ 个换行 -> 2 个。\n"
            "         补一句 src.replace(/\\n{3,}/g,'\\n\\n') 即可。"))
    elif g.rstrip() == m.rstrip():
        tips.append((
            "正文一致，**只差文件末尾空白**",
            "EEZ 产物末尾**不带换行**。补一句 .replace(/\\s+$/,'') 去掉末尾空白。"))
    elif collapse(g).rstrip() == collapse(m).rstrip():
        tips.append((
            "只差在**空行 + 末尾空白**上（两处后处理都没做）",
            "同时补：折叠连续 3+ 换行为 2 个 + 去掉末尾所有空白。"))

    # 坑：range / symbols 取错（字形集合变了 -> 体积和行数都差很多）
    def opts_of(s):
        mm = re.search(r"\*\s*Opts:\s*(.*)", s)
        return mm.group(1).strip() if mm else ""

    og, om = opts_of(g), opts_of(m)
    if og and om and og != om:
        tips.append((
            "头部 Opts 行不一致（参数不同）",
            "黄金: %s\n         你的: %s\n"
            "         逐段比对：--symbols 必须在 --range **之前**；附加源 --font 追加在\n"
            "         --format lvgl **之后**（见 features/font/font.js 的 _lvglExtractFontParams）。"
            % (og, om)))

    def n_glyph(s):
        return len(re.findall(r"/\* U\+", s))

    ng, nm = n_glyph(g), n_glyph(m)
    if ng != nm:
        tips.append((
            "字形数量不同：黄金 %d 个 vs 你的 %d 个" % (ng, nm),
            "① 主字体的 symbols 要取**顶层 lvglSymbols**；lvglGlyphs.symbols 是含\n"
            "         FontAwesome 的 UI 合集，拿去烘会报 'doesn't have any characters included'。\n"
            "         ② 附加源在工程里的字段是 {filePath, lvglRanges, lvglSymbols}，不是 encodings/symbols。"))

    if not tips:
        tips.append((
            "找不到已知成因，需要人工二分",
            "按下面的顺序定位：\n"
            "         1) 先 diff 头部注释（Size / Bpp / Opts）—— 参数层面的差异一眼可见\n"
            "         2) 再找**首处不同的行**，看它落在 BITMAPS / GLYPH DESCRIPTION / KERNING 哪一段\n"
            "         3) 落在 BITMAPS -> 栅格化参数（bpp / size / 字体源文件）\n"
            "         4) 落在 KERNING -> no_kerning / 附加源没喂进去"))
    return tips


def _first_diff(gold, mine):
    gold = gold.replace(b"\r\n", b"\n")
    mine = mine.replace(b"\r\n", b"\n")
    gl = gold.split(b"\n")
    ml = mine.split(b"\n")
    for i, (a, b) in enumerate(zip(gl, ml)):
        if a != b:
            return i, a[:90], b[:90]
    if len(gl) != len(ml):
        return min(len(gl), len(ml)), b"<end of shorter file>", b"<line count differs>"
    return None, None, None


# ------------------------------------------------------------------ 命令实现 ----
def list_fonts(d):
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if FONT_RE.match(f))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_snapshot(src, golden, note=""):
    fonts = list_fonts(src)
    if not fonts:
        print("!! %s 下没有 ui_font_*.c" % src)
        return 2
    os.makedirs(golden, exist_ok=True)
    man = {
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "note": note or "(未注明来源 —— 强烈建议写明是 EEZ Studio GUI Build 的产物)",
        "src": os.path.abspath(src),
        "files": {},
    }
    for f in fonts:
        s = os.path.join(src, f)
        d = os.path.join(golden, f)
        with open(s, "rb") as a, open(d, "wb") as b:
            b.write(a.read())
        man["files"][f] = {"sha256": sha256(d), "size": os.path.getsize(d)}
    with open(os.path.join(golden, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
    print("黄金样本已存 %d 个 -> %s" % (len(fonts), golden))
    print("  来源标注：%s" % man["note"])
    print("  !! 确认这是 **EEZ Studio GUI Build** 的产物 —— 否则一致也证明不了任何事")
    return 0


def cmd_check(src, golden, with_metrics=False):
    man_path = os.path.join(golden, "_manifest.json")
    if not os.path.exists(man_path):
        print("!! %s 里没有 _manifest.json，先跑 snapshot" % golden)
        return 2
    man = json.load(open(man_path, encoding="utf-8"))
    print("黄金样本：%s（%s）\n  来源：%s\n" % (golden, man.get("created"), man.get("note")))

    golds = list_fonts(golden)
    if not golds:
        print("!! 黄金样本目录为空")
        return 2

    ok, bad = [], []
    for f in golds:
        gp = os.path.join(golden, f)
        mp = os.path.join(src, f)
        if not os.path.exists(mp):
            bad.append((f, "缺失", None))
            print("MISSING  %-44s 你的产物里没有这个文件" % f)
            continue
        g = open(gp, "rb").read()
        m = open(mp, "rb").read()
        if g == m:
            ok.append(f)
            print("IDENTICAL %-44s %8d bytes" % (f, len(g)))
        else:
            bad.append((f, "内容不同", (g, m)))
            print("DIFFER    %-44s 黄金 %d / 你的 %d bytes" % (f, len(g), len(m)))

    print("\n结果：一致 %d 个，不同 %d 个" % (len(ok), len(bad)))

    if bad:
        print("\n" + "=" * 70)
        print("差异诊断")
        print("=" * 70)
        for f, why, pair in bad:
            if pair is None:
                continue
            g, m = pair
            print("\n--- %s" % f)
            ln, ga, ma = _first_diff(g, m)
            if ln is not None:
                print("    首处不同 第 %d 行：" % ln)
                print("      黄金: %r" % ga)
                print("      你的: %r" % ma)
            print("    行数 黄金 %d / 你的 %d；空行 黄金 %d / 你的 %d" % (
                g.count(b"\n"), m.count(b"\n"),
                sum(1 for l in g.split(b"\n") if not l.strip()),
                sum(1 for l in m.split(b"\n") if not l.strip())))
            print("    末尾 黄金 %r / 你的 %r" % (g[-24:], m[-24:]))
            for concl, hint in _diagnose(g, m):
                print("    → %s" % concl)
                for line in hint.split("\n"):
                    print("        %s" % line.strip())

    if with_metrics:
        print("\n" + "=" * 70)
        print("字号度量（决定布局，必须完全一致）")
        print("=" * 70)
        print("  %-44s %-12s %-12s" % ("文件", "golden", "mine"))
        drifted = 0
        for f in golds:
            gp, mp = os.path.join(golden, f), os.path.join(src, f)
            if not os.path.exists(mp):
                continue
            gm, mm = metrics_of(gp), metrics_of(mp)
            same = gm == mm
            if not same:
                drifted += 1
            print("  %-44s %-12s %-12s %s" % (
                f, fmt_metrics(gm), fmt_metrics(mm), "" if same else "  ← 漂移!"))
        print("\n  度量漂移 %d 个（>0 说明布局会变，必须查）" % drifted)
        if drifted:
            return 1

    return 1 if bad else 0


def metrics_of(path):
    try:
        t = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    lh = re.search(r"line_height\s*=\s*(-?\d+)", t)
    bl = re.search(r"base_line\s*=\s*(-?\d+)", t)
    if not lh or not bl:
        return None
    return (int(lh.group(1)), int(bl.group(1)))


def fmt_metrics(m):
    return "-" if m is None else "h%d/b%d" % m


def cmd_metrics(src):
    fonts = list_fonts(src)
    if not fonts:
        print("!! %s 下没有 ui_font_*.c" % src)
        return 2
    for f in fonts:
        m = metrics_of(os.path.join(src, f))
        print("  %-44s %s" % (f, fmt_metrics(m)))
    return 0


def main():
    ap = argparse.ArgumentParser(description="后台烘焙字体 vs EEZ Studio GUI 产物 的一致性判据")
    ap.add_argument("cmd", choices=["snapshot", "check", "metrics"])
    ap.add_argument("--src", required=True, help="当前产物目录（一般是 src/ui）")
    ap.add_argument("--golden", help="黄金样本目录")
    ap.add_argument("--note", default="", help="snapshot 时标注来源")
    ap.add_argument("--metrics", action="store_true", help="check 时顺带比度量")
    a = ap.parse_args()

    if a.cmd == "snapshot":
        if not a.golden:
            print("!! snapshot 需要 --golden")
            return 2
        return cmd_snapshot(a.src, a.golden, a.note)
    if a.cmd == "check":
        if not a.golden:
            print("!! check 需要 --golden")
            return 2
        return cmd_check(a.src, a.golden, a.metrics)
    return cmd_metrics(a.src)


# ==============================================================================
# EXPERIMENT —— 最硬的那条验证（光比对还不够，要能「从零重建出一样的东西」）
# ==============================================================================
# 逐字节比对只能证明「这次的产物和上次一样」，证明不了「我的生成链路是对的」。
#   —— 万一 src/ui 里的字体是上次后台烘的、根本没被覆盖，比对照样 IDENTICAL。
# 所以要做**清空重建实验**：
#
#   1) snapshot：EEZ Studio GUI Build 之后存黄金样本
#        python tools/font_verify.py snapshot --src src/ui --golden /tmp/golden \
#               --note "EEZ Studio 1.22.10 GUI Check and Build 产物"
#   2) 清空：rm src/ui/ui_font_*.c   （连增量状态一起删，逼它真的重烘）
#   3) 重烘：python design/eez_font_engine.py --force
#   4) 比对：python tools/font_verify.py check --src src/ui --golden /tmp/golden --metrics
#   5) 再跑一遍**完整链路**后复校（CLI build 可能把字体当 orphan 删掉再补烘，
#      这一步能验证「管线顺序」也是对的）：
#        python design/all.py
#        python tools/font_verify.py check --src src/ui --golden /tmp/golden --metrics
#
# 两轮都 IDENTICAL、且度量零漂移，才能下「后台产物 == 官方产物」的结论。
#
# ★ 别信单一观察：曾经从「删掉一个字体后跑 CLI build 它没回来」直接推出
#   「EEZ 不生成字体」，这是错的 —— 单次观察只能否定「这次发生了」。
#   下结论前先问：我的观察覆盖了几条路径（GUI / CLI / 后台引擎）、跑了几次。
# ==============================================================================

if __name__ == "__main__":
    sys.exit(main())
