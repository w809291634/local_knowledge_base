#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eez_font_bake.py —— **通用** EEZ Studio 官方字体引擎驱动（工程无关）

把 EEZ Studio 安装目录 app.asar 里的**官方烘焙引擎**解出来，在 Node 里按 Worker
语义调用，**纯后台、不开 GUI、不弹窗**。产出与 EEZ Studio 点 Build **逐字节一致**。

这是**可复用内核**：只做「解包 + 烘焙 + 产出到输出目录」，不关心工程目录结构、
不写 src/ui、不管增量状态 —— 那些是工程侧胶水的事（见 skills.md §11.12）。

为什么不用 headless CLI
----------------------
EEZ 的 `--build-project` 在本机**不烘焙字体**（删光字体再 build → 0 个字体、
0 报错、2.2s、无 `Extracting font` 日志）。GUI 能烘是因为它有 Worker 线程环境。

引擎构成（都在 app.asar 内）
---------------------------
    build/project-editor/features/font/font-extract/lvgl-worker.js   引擎入口（EEZ 原文件）
    node_modules/lv_font_conv/lib/freetype/build/ft_render.js        freetype（wasm 内嵌 base64，自包含）
    node_modules/{opentype.js, make-error, bit-buffer}               运行时依赖

参数构造严格复刻 EEZ 自己的代码：
    font-extract/lvgl.js 的 ExtractFont.start()
    features/font/font.js 的 _lvglExtractFontParams（opts_string 拼接）
    project-editor/project/assets.js 的 getName() + eez-studio-shared/string.js 的 underscore()

用法
----
    python tools/eez_font_bake.py --info                       # 探测 asar / node / 引擎缓存
    python tools/eez_font_bake.py <工程文件> <输出目录>          # 烘全部 LVGL 字体
    python tools/eez_font_bake.py <工程文件> <输出目录> 字体名1 字体名2
    python tools/eez_font_bake.py --clean                       # 清引擎缓存（EEZ 升级后必做）

输出：`<输出目录>/ui_font_*.c` + `manifest.json`（变量名清单，由 EEZ 的 getName 算出）。

API
---
    import eez_font_bake
    names = eez_font_bake.bake(proj_path, out_dir)          # -> ["ui_font_xxx", ...]
    eez_font_bake.kernel_hash()                             # 内核 BAKE_JS 的 sha256（查分叉用）

环境变量：`EEZ_STUDIO_ASAR` 指定 app.asar；`EEZ_NODE` 指定 node 可执行文件。

只依赖标准库（需要系统上有 node）。
"""
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

# ------------------------------------------------------------------ 路径候选 --
ASAR_CANDIDATES = [
    os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs",
                 "eezstudio", "resources", "app.asar"),          # Windows 默认
    r"C:/Program Files/EEZ Studio/resources/app.asar",
    r"C:/Program Files/eezstudio/resources/app.asar",
    "/Applications/EEZ Studio.app/Contents/Resources/app.asar",  # macOS
    "/opt/eezstudio/resources/app.asar",                          # Linux
    os.path.join(os.path.expanduser("~"), ".local", "share",
                 "eezstudio", "resources", "app.asar"),
]

NODE_CANDIDATES = [
    r"C:/Program Files/nodejs/node.exe",
    "/usr/local/bin/node",
    "/usr/bin/node",
    "/opt/homebrew/bin/node",
]

ENGINE_SUBTREES = [
    "/build/project-editor/features/font/font-extract",
    "/node_modules/lv_font_conv",
    "/node_modules/opentype.js",
    "/node_modules/make-error",
    "/node_modules/bit-buffer",
]
ENGINE_EXCLUDE = ("/bin/", "/test", "/example", "/doc/", ".map")


# ================================================================== bake.js ===
# 引擎驱动。改动这里 = 改动烘焙行为，改完必须重跑 font_verify.py 验证。
# （kernel_hash() 就是这段的指纹，工程侧拿它查分叉。）
BAKE_JS = r'''
"use strict";
const fs = require("fs");
const path = require("path");

// -------- 复刻 eez-studio-shared/string.js: underscore() --------
function underscore(input) {
    let e = (input || "").toString().trim();
    if (e.toUpperCase() === e) return e;
    let r = "";
    for (let t = 0; t < e.length; t++) {
        const isUp = c => c >= "A" && c <= "Z";
        if (isUp(e[t]) && t > 0 && isUp(e[t - 1]) &&
            (t === e.length - 1 || isUp(e[t + 1]) ||
             (e[t + 1] >= "0" && e[t + 1] <= "9") ||
             e[t + 1] === " " || e[t + 1] === "." || e[t + 1] === "_")) {
            r += e[t].toLowerCase();
        } else {
            r += e[t];
        }
    }
    return (r = r.replace(/([a-z\d])([A-Z]+)/g, "$1_$2"))
        .replace(/[-\s]+/g, "_").toLowerCase();
}

// -------- 复刻 project-editor/project/assets.js: getName() --------
function getName(prefix, s) {
    let a = s.toString();
    a = a.replace(/\$/g, "");
    a = a.replace(/[^a-zA-Z_0-9]/g, "_");
    a = underscore(a).toLowerCase();
    return prefix + a;
}

// -------- 加载 EEZ 官方引擎（Worker 语义） --------
const WORKER = path.join(__dirname,
    "build/project-editor/features/font/font-extract/lvgl-worker.js");
const ctx = {};
global.self = ctx;                 // lvgl-worker.js 里 `const ctx = self`
require(WORKER);                   // 执行后 ctx.onmessage 已被赋值
const onmessage = ctx.onmessage;
if (typeof onmessage !== "function") throw new Error("failed to load EEZ engine: " + WORKER);

function bake(args, output) {
    return new Promise((resolve, reject) => {
        ctx.postMessage = m => (m && m.error) ? reject(new Error(m.error)) : resolve(m);
        onmessage({ data: { args, output } });
    });
}

// -------- 复刻 font-extract/lvgl.js 的 ExtractFont.start() --------
function buildArgs(font, LVGL_INCLUDE) {
    const abs = path.resolve(font.source.filePath);
    if (!fs.existsSync(abs)) throw new Error("font source not found: " + abs);
    const buf = fs.readFileSync(abs);

    const enc = [];
    const encodings = (font.lvglGlyphs && font.lvglGlyphs.encodings) || [];
    encodings.forEach(t => enc.push(t.from, t.to, t.mapped_from ?? t.from));
    // 主字体的 symbols 取顶层 lvglSymbols；lvglGlyphs.symbols 是含 FontAwesome 的
    // UI 合集，拿去烘会报 “doesn't have any characters included in ...”
    const symbols = font.lvglSymbols || "";

    const fontList = [{
        source_path: abs,
        source_bin_base64: buf.toString("base64"),
        ranges: [{ range: enc, symbols }]
    }];

    for (const s of font.lvglAdditionalSources || []) {
        const sab = path.resolve(s.filePath);
        if (!fs.existsSync(sab)) throw new Error("additional font source not found: " + sab);
        const se = [];
        (s.encodings || []).forEach(t => se.push(t.from, t.to, t.mapped_from ?? t.from));
        fontList.push({
            source_path: sab,
            source_bin_base64: fs.readFileSync(sab).toString("base64"),
            ranges: [{ range: se, symbols: s.lvglSymbols ?? "" }]
        });
    }

    const output = getName("ui_font_", font.name || "");

    // 复刻 font.js 的 _lvglExtractFontParams
    let opts = `--bpp ${font.bpp} --size ${font.source.size} --no-compress --font ${abs}`;
    const symStr = (font.lvglSymbols || "").replace(/\s/g, "");
    if (symStr) opts += ` --symbols ${symStr}`;
    const rngStr = (font.lvglRanges || "").replace(/\s/g, "");
    if (rngStr) opts += ` --range ${rngStr}`;
    if (font.lvglFallbackFont) opts += ` --lv-fallback ${font.lvglFallbackFont}`;
    opts += " --format lvgl";
    for (const e of font.lvglAdditionalSources || []) {
        if (!e.filePath) continue;
        opts += ` --font ${path.resolve(e.filePath)}`;
        const es = (e.lvglSymbols || "").replace(/\s/g, "");
        if (es) opts += ` --symbols ${es}`;
        const er = (e.lvglRanges || "").replace(/\s/g, "");
        if (er) opts += ` --range ${er}`;
    }

    return {
        args: {
            font: fontList,
            size: font.source.size,
            bpp: font.bpp,
            no_compress: true,
            lcd: false,
            lcd_v: false,
            use_color_info: false,
            output,
            lv_include: LVGL_INCLUDE,
            no_kerning: false,
            no_prefilter: false,
            fast_kerning: false,
            opts_string: opts,
            lv_fallback: font.lv_fallback ? font.lv_fallback : undefined
        },
        output
    };
}

(async () => {
    const projPath = process.argv[2];
    const outDir = process.argv[3];
    const proj = JSON.parse(fs.readFileSync(projPath, "utf8"));
    const LVGL_INCLUDE = (((proj.settings || {}).build) || {}).lvglInclude || "lvgl.h";
    const fonts = (proj.fonts || []).filter(f => (f.renderingEngine || "LVGL") === "LVGL");

    fs.mkdirSync(outDir, { recursive: true });
    const manifest = [];
    for (const f of fonts) {
        const t0 = Date.now();
        const { args, output } = buildArgs(f, LVGL_INCLUDE);
        const r = await bake(args, output);
        // C 源码是字符串（没被真 base64 编码）；bin 才是 Buffer
        const rawSrc = r.lvglSourceFile;
        const src = rawSrc.startsWith("/") ? rawSrc
                                          : Buffer.from(rawSrc, "base64").toString("utf8");
        // EEZ 落盘前的统一后处理：折叠多余空行 + 去掉末尾空白
        const norm = src.replace(/\n{3,}/g, "\n\n").replace(/\s+$/, "");
        fs.writeFileSync(path.join(outDir, output + ".c"), norm);
        manifest.push(output);
        console.log(`OK ${output}.c  ${norm.length} bytes  (${Date.now() - t0} ms)`);
    }
    fs.writeFileSync(path.join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2));
})().catch(e => {
    console.error("FAIL:", (e && e.message) || e);
    process.exit(1);
});
'''


# ============================================================== 定位工具链 =====
def kernel_hash():
    """BAKE_JS 的指纹。工程侧拿它比对，防止内核副本悄悄分叉。"""
    return hashlib.sha256(BAKE_JS.encode("utf-8")).hexdigest()


def find_asar():
    env = os.environ.get("EEZ_STUDIO_ASAR")
    if env and os.path.exists(env):
        return env
    for p in ASAR_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def find_node():
    env = os.environ.get("EEZ_NODE")
    if env and os.path.exists(env):
        return env
    for p in NODE_CANDIDATES:
        if os.path.exists(p):
            return p
    return shutil.which("node")


# ================================================================ asar 解包 ====
def _asar_index(data):
    """{包内路径: (offset, size)}，offset 相对文件体起点。

    ★ asar 头部：前 16 字节是 4 个 uint32，**第 4 个**才是 header JSON 长度。
    用 data.find(b'{"files"') 找起点 + data[4:8] 当长度是错的。
    """
    u = struct.unpack("<4I", data[:16])
    header = json.loads(data[16:16 + u[3]].decode("utf-8"))
    base = 16 + u[3]

    acc = {}

    def walk(d, prefix=""):
        for name, info in (d or {}).items():
            p = prefix + "/" + name
            if "files" in info:
                walk(info["files"], p)
            else:
                acc[p] = (int(info.get("offset", 0)), int(info.get("size", 0)))

    walk(header.get("files", {}))
    return acc, base


def extract_engine(asar, cache):
    if os.path.isdir(cache):
        shutil.rmtree(cache)
    os.makedirs(cache, exist_ok=True)
    data = open(asar, "rb").read()
    acc, base = _asar_index(data)
    n = 0
    for p, (off, size) in acc.items():
        if not any(p.startswith(t) for t in ENGINE_SUBTREES):
            continue
        if any(x in p for x in ENGINE_EXCLUDE):
            continue
        dest = os.path.join(cache, p.lstrip("/").replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data[base + off: base + off + size])
        n += 1
    return n


def ensure_engine(clean=False, quiet=False):
    """确保引擎缓存就绪 -> (cache_dir, node_exe)。"""
    asar = find_asar()
    if not asar:
        raise SystemExit(
            "!! 找不到 EEZ Studio 的 app.asar。设环境变量 EEZ_STUDIO_ASAR=<路径>。\n"
            "   找过：\n     " + "\n     ".join(ASAR_CANDIDATES))
    node = find_node()
    if not node:
        raise SystemExit("!! 找不到 node（引擎需要 Node 运行）。设 EEZ_NODE=<路径>。")

    st = os.stat(asar)
    key = hashlib.sha1(("%d-%d" % (st.st_size, int(st.st_mtime))).encode()).hexdigest()[:12]
    root = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    cache = os.path.join(root, "eez-font-engine", key)
    marker = os.path.join(cache, ".engine_ok")

    if clean and os.path.isdir(cache):
        shutil.rmtree(cache)

    if not os.path.exists(marker):
        if not quiet:
            print("引擎缓存: %s" % cache)
            print("从 app.asar 解包 EEZ 官方字体引擎 ...")
        n = extract_engine(asar, cache)
        with open(os.path.join(cache, "bake.js"), "w", encoding="utf-8", newline="\n") as f:
            f.write(BAKE_JS)
        with open(marker, "w", encoding="utf-8") as f:
            f.write("%s\n%d\n%s" % (asar, n, time.strftime("%Y-%m-%d %H:%M:%S")))
        if not quiet:
            print("  解出 %d 个文件" % n)
    elif not quiet:
        print("引擎缓存命中: %s" % cache)
    return cache, node


# ==================================================================== 烘焙 ====
def bake(proj_path, out_dir, names=None, clean=False, quiet=False):
    """烘工程里的 LVGL 字体到 out_dir，返回变量名清单。

    不写任何工程目录 —— 落盘位置由调用方（工程侧胶水）决定。
    """
    cache, node = ensure_engine(clean=clean, quiet=quiet)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    cmd = [node, os.path.join(cache, "bake.js"), os.path.abspath(proj_path),
           os.path.abspath(out_dir)]
    if names:
        cmd += list(names)
    r = subprocess.run(cmd, cwd=cache)
    if r.returncode != 0:
        raise RuntimeError("EEZ 字体引擎烘焙失败（见上面 FAIL 行）")

    mf = os.path.join(out_dir, "manifest.json")
    if not os.path.exists(mf):
        raise RuntimeError("引擎没产出 manifest.json")
    return json.load(open(mf, encoding="utf-8"))


# ==================================================================== CLI ======
def cmd_info():
    asar = find_asar()
    node = find_node()
    print("EEZ Studio app.asar : %s" % (asar or "(未找到)"))
    print("node                : %s" % (node or "(未找到)"))
    print("kernel hash         : %s" % kernel_hash())
    if asar:
        st = os.stat(asar)
        key = hashlib.sha1(("%d-%d" % (st.st_size, int(st.st_mtime))).encode()).hexdigest()[:12]
        root = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        cache = os.path.join(root, "eez-font-engine", key)
        print("引擎缓存            : %s%s" % (
            cache, "（已就绪）" if os.path.exists(os.path.join(cache, ".engine_ok"))
            else "（未解包）"))
    return 0 if (asar and node) else 2


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] in ("--info", "info"):
        return cmd_info()
    if a[0] in ("--clean", "clean"):
        ensure_engine(clean=True)
        print("引擎缓存已清空（下次运行会重新解包）。")
        return 0
    if a[0].startswith("-"):
        print(__doc__)
        return 2

    proj_path = a[0]
    out_dir = a[1] if len(a) > 1 else os.path.join(tempfile.gettempdir(), "eez_font_out")
    names = [x for x in a[2:] if not x.startswith("-")]

    if not os.path.exists(proj_path):
        print("!! 工程文件不存在: %s" % proj_path)
        return 2
    try:
        got = bake(proj_path, out_dir, names or None)
    except (RuntimeError, SystemExit) as e:
        print(e)
        return 1
    print("\n完成：%d 个字体 -> %s" % (len(got), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
