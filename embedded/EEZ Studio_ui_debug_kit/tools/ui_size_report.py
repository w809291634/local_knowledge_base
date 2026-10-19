#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui_size_report.py -- report where the firmware flash/RAM actually goes.

Run it directly from the project directory (or anywhere; the project root is
located from this script's own path):

    python ui_size_report.py

It answers three questions at once:
  1. How big is the app .bin, and how much of the app partition is used.
  2. Which *groups* eat the flash (EEZ engine / generated UI / LVGL core /
     fonts / display+drivers / project components / C runtime / IDF / rest).
  3. Per-file breakdown of the EEZ UI component (eez-test/src/ui), the fonts
     detail, and the internal-RAM (DIRAM bss/data) detail.

Accuracy: the numbers come from the IDF size tool
(`python -m esp_idf_size --files --format json <map>`), which reports the
FINAL LINKED per-object contribution (after --gc-sections / -Os). The
interpreter that hosts that tool is auto-detected, in this order:
  1. build/CMakeCache.txt  (the project's own record of the IDF python -- works
     in a plain terminal with no IDF environment variables set)
  2. $IDF_PYTHON_ENV_PATH
  3. $IDF_TOOLS_PATH/python_env/*/
  4. this interpreter, then python/python3/py on PATH
Override with --idf-python <path> if detection fails.

IMPORTANT: the size of build/.../libui.a on disk (several MB) is NOT the
firmware cost -- it is dominated by .debug_* and symbol tables. Only the
numbers below are the real footprint.
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):
    try:
        # Keep the console code page but never crash on an unrepresentable char.
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

PROJECT_NAME_DEFAULT = "lvgl_demo_template"
APP_PARTITION_SIZE = 0x800000  # 8 MB, see partitions.csv
SCRIPT_VERSION = "2 (size tool only; no map guessing)"


# ---------------------------------------------------------------------------
# Locating the project and the build artifacts
# ---------------------------------------------------------------------------

def find_map_and_bin(project_root, project_name):
    build = os.path.join(project_root, "build")
    return (
        os.path.join(build, project_name + ".map"),
        os.path.join(build, project_name + ".bin"),
        build,
    )


def detect_project_name(build_dir):
    """Pick the app name from build/: the .map that has a matching .bin.

    This is what makes the tool portable -- copy it into any IDF project and
    run it, with no need to pass --name.
    """
    best = None
    for m in glob.glob(os.path.join(build_dir, "*.map")):
        base = os.path.basename(m)[:-4]
        if os.path.exists(os.path.join(build_dir, base + ".bin")):
            return base
        if best is None:
            best = base
    return best


# ---------------------------------------------------------------------------
# Finding an interpreter that can `import esp_idf_size`
# ---------------------------------------------------------------------------

def python_from_cmake_cache(build_dir):
    """The project's build cache records the exact IDF python. No env needed."""
    cache = os.path.join(build_dir, "CMakeCache.txt")
    if not os.path.exists(cache):
        return None
    wanted = ("PYTHON", "_Python3_EXECUTABLE")
    with open(cache, "r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            m = re.match(r"^([A-Za-z0-9_]+)(?::[A-Za-z0-9_]+)?=(.+)$", line)
            if not m or m.group(1) not in wanted:
                continue
            path = m.group(2).strip().replace("/", os.sep)
            if os.path.exists(path):
                return path
    return None


def python_candidates(build_dir):
    p = python_from_cmake_cache(build_dir)
    if p:
        yield p

    env_path = os.environ.get("IDF_PYTHON_ENV_PATH")
    if env_path:
        yield os.path.join(env_path, "Scripts", "python.exe")
        yield os.path.join(env_path, "bin", "python")

    tools_path = os.environ.get("IDF_TOOLS_PATH")
    if tools_path:
        for sub in ("Scripts/python.exe", "bin/python"):
            for hit in glob.glob(os.path.join(tools_path, "python_env", "*", sub)):
                yield hit

    yield sys.executable
    for name in ("python", "python3", "py"):
        hit = shutil.which(name)
        if hit:
            yield hit


def find_idf_python(build_dir, explicit=None):
    """Return an interpreter that can import esp_idf_size, or None."""
    if explicit:
        return explicit if os.path.exists(explicit) else None
    seen = set()
    for py in python_candidates(build_dir):
        if not py or py in seen or not os.path.exists(py):
            continue
        seen.add(py)
        try:
            r = subprocess.run([py, "-c", "import esp_idf_size"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return None


def load_per_file(py, map_file, project_root):
    out = subprocess.run(
        [py, "-m", "esp_idf_size", "--files", "--format", "json", map_file],
        cwd=project_root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=300,
    )
    if out.returncode != 0 or not out.stdout.strip():
        raise RuntimeError("esp_idf_size returned no data (rc=%s)" % out.returncode)
    return json.loads(out.stdout.decode("utf-8-sig", errors="replace"))


# ---------------------------------------------------------------------------
# Grouping rules
# ---------------------------------------------------------------------------

PROJECT_ARCHIVES = (
    "libmain.a", "libboard.a", "libboard_config.a", "libdsi_display.a",
    "libnative.a", "liblv_mem_psram.a", "libapl_console.a",
    "libapl_console_cmd_nvs.a", "libapl_console_cmd_system.a",
    "libapl_console_cmd_wifi.a", "libapl_utility.a",
)
RUNTIME_RE = re.compile(r"^lib(m|gcc|c|c\+\+|c\+\+abi|stdc\+\+|cxx|newlib|pthread)\.")
KERNEL_RE = re.compile(
    r"^lib(freertos|esp_system|esp_timer|heap|log|esp_hw_support|esp_common|soc|hal|esp_rom"
    r"|efuse|esp_psram|spi_flash|esp_partition|esp_mm|esp_security|esp_pm|esp_event)\."
)
DRIVER_RE = re.compile(
    r"st7701|touch|lvgl_adapter|esp_lcd|esp_lv_decoder|esp_lv_fs|mmap_assets"
    r"|esp_new_jpeg|libpng|zlib|freetype|button"
)

G_ENGINE = "EEZ 引擎 (eez-flow.cpp)"
G_UIGEN = "EEZ 生成 UI (screens/ui/styles/images)"
G_FONTDATA = "字体资源 (Montserrat)"
G_FONTENG = "字体渲染/加载 (LVGL font engine)"
G_LVGL = "LVGL 内核"
G_DRIVER = "显示/触摸/适配 (ST7701/GT911/adapter)"
G_PROJECT = "本项目组件 (main/board/dsi/native/console)"
G_RUNTIME = "C/C++ 运行时 (libm/libc/libstdc++)"
G_KERNEL = "IDF 内核 (FreeRTOS/heap/log/...)"
G_OTHER = "其它 (其它 IDF 组件 / managed 库)"

GROUP_ORDER = [G_ENGINE, G_UIGEN, G_FONTDATA, G_FONTENG, G_LVGL,
               G_DRIVER, G_PROJECT, G_RUNTIME, G_KERNEL, G_OTHER]


def classify(key):
    archive, _, member = key.partition(":")
    if member.startswith("eez-flow.cpp"):
        return G_ENGINE
    if archive == "libui.a":
        return G_UIGEN
    if member.startswith("lv_font_montserrat"):
        return G_FONTDATA
    if member.startswith("lv_font_"):
        return G_FONTENG
    if archive.startswith("liblvgl"):
        return G_LVGL
    if DRIVER_RE.search(archive):
        return G_DRIVER
    if archive in PROJECT_ARCHIVES:
        return G_PROJECT
    if RUNTIME_RE.match(archive):
        return G_RUNTIME
    if KERNEL_RE.match(archive):
        return G_KERNEL
    return G_OTHER


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def kb(n):
    """Size in the unit people actually compare: KB / MB (1024-based)."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 / 1024:.2f} MB"


def human(n):
    """KB/MB first (what users compare), exact bytes in parentheses."""
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB ({n:,} B)"
    return f"{n / 1024 / 1024:.2f} MB ({n:,} B)"


def sec(entry, *names):
    return sum(entry.get(n, 0) for n in names)


def _disp_width(s):
    """Display columns of s: East-Asian wide/fullwidth chars occupy 2."""
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def col(s, width, align="l"):
    """Pad s to `width` DISPLAY columns so CJK labels line up with each other."""
    fill = max(0, width - _disp_width(s))
    return (" " * fill + s) if align == "r" else (s + " " * fill)


def print_overall(bin_file):
    """Bin size + partition usage -- works even without the IDF size tool."""
    bin_size = os.path.getsize(bin_file) if os.path.exists(bin_file) else 0
    print("\n[1] 固件总体 (app .bin)")
    if not bin_size:
        print("    (未找到 build/<name>.bin，请先构建)")
        return 0
    pct = bin_size * 100.0 / APP_PARTITION_SIZE
    print(f"    app .bin (烧写大小) : {human(bin_size)}")
    print(f"    app 分区            : {human(APP_PARTITION_SIZE)}  已用 {pct:.1f}%, 余 {100 - pct:.1f}%")
    return bin_size


def print_report(project_name, per_file, bin_file):
    flash_total = sum(v.get("flash_total", 0) for v in per_file.values())
    ram_total = sum(v.get("ram_st_total", 0) for v in per_file.values())

    print("=" * 78)
    print(f" 固件资源占用报告  [{project_name}]     ui_size_report v{SCRIPT_VERSION}")
    print("=" * 78)

    print_overall(bin_file)
    print(f"    链接后进固件合计    : {human(flash_total)}")
    print(f"    内部 RAM (bss+data) : {human(ram_total)}")

    # --- flash by group ---------------------------------------------------
    groups = {g: {"flash": 0, "ram": 0} for g in GROUP_ORDER}
    for k, v in per_file.items():
        g = classify(k)
        groups[g]["flash"] += v.get("flash_total", 0)
        groups[g]["ram"] += v.get("ram_st_total", 0)

    print("\n[2] flash 按分组            (单位: KB, 1 KB = 1024 B)")
    print("    " + col("分组", 42) + col("flash", 12, "r") + col("占比", 8, "r"))
    print("    " + "-" * 62)
    for g in GROUP_ORDER:
        f = groups[g]["flash"]
        if not f:
            continue
        pct = f * 100.0 / flash_total if flash_total else 0
        print("    " + col(g, 42) + col(kb(f), 12, "r") + col(f"{pct:.1f}%", 8, "r"))
    print("    " + "-" * 62)
    print("    " + col("合计", 42) + col(kb(flash_total), 12, "r") + col("100.0%", 8, "r"))

    eez = groups[G_ENGINE]["flash"] + groups[G_UIGEN]["flash"]
    fonts = groups[G_FONTDATA]["flash"] + groups[G_FONTENG]["flash"]
    print("\n[2b] 重点两项（区分「EEZ 框架」与「字体资源」，别混算）")
    print("    " + col("EEZ 独有代码 (引擎 + 生成 UI)", 32) + ": " + human(eez))
    print("    " + col("字体相关 (资源 + 渲染引擎)", 32) + ": " + human(fonts)
          + "   <- 字体资源不属于 EEZ；原生 LVGL 同样要付")

    # --- UI component per file -------------------------------------------
    ui_keys = sorted((k for k in per_file if k.startswith("libui.a")),
                     key=lambda k: -per_file[k].get("flash_total", 0))
    print("\n[3] EEZ UI 组件逐文件 (eez-test/src/ui)     (单位: KB)")
    if ui_keys:
        print("    " + col("文件", 28) + col("flash", 10, "r") + col("RAM", 10, "r"))
        print("    " + "-" * 48)
        f_sum = 0
        for k in ui_keys:
            v = per_file[k]
            f_sum += v.get("flash_total", 0)
            print("    " + col(k.split(":", 1)[1], 28)
                  + col(kb(v.get("flash_total", 0)), 10, "r")
                  + col(kb(v.get("ram_st_total", 0)), 10, "r"))
        print("    " + "-" * 48)
        print("    " + col("合计", 28) + col(kb(f_sum), 10, "r"))
    else:
        print("    (本构建未引用 ui 组件 -- 可能关闭了 APP_ENABLE_EEZ_UI)")

    # --- fonts detail -----------------------------------------------------
    font_keys = sorted((k for k in per_file if "lv_font_" in k),
                       key=lambda k: -per_file[k].get("flash_total", 0))
    print("\n[4] 字体明细            (单位: KB)")
    if font_keys:
        for k in font_keys:
            print("    " + col(k.split(":", 1)[1], 38)
                  + col(kb(per_file[k].get("flash_total", 0)), 12, "r"))
        print("    " + "-" * 50)
        print("    " + col("合计", 38)
              + col(kb(sum(per_file[k].get("flash_total", 0) for k in font_keys)), 12, "r"))
        print("    只有 UI 真正用到的字号才需要保留；未用到的可在 sdkconfig 关闭")
        print("    (EEZ 的 screens.c 字体表带 #if LV_FONT_MONTSERRAT_xx 保护，关闭不会编译错)")
    else:
        print("    (无字体对象)")

    # --- internal RAM -----------------------------------------------------
    bss = sum(v.get(".dram0.bss", 0) for v in per_file.values())
    data = sum(v.get(".dram0.data", 0) for v in per_file.values())
    print("\n[5] 内部 RAM (DIRAM)")
    print(f"    .dram0.bss  : {human(bss)}")
    print(f"    .dram0.data : {human(data)}")
    top = sorted(per_file.items(), key=lambda x: -x[1].get(".dram0.bss", 0))
    print("    bss 占用最大的对象:")
    printed = 0
    for k, v in top:
        b = v.get(".dram0.bss", 0)
        if b:
            print("      " + col(kb(b), 9, "r") + "  " + k)
            printed += 1
            if printed >= 8:
                break
    if not printed:
        print("      (无)")

    # --- flash-resident sections -----------------------------------------
    ftext = sum(v.get(".flash.text", 0) for v in per_file.values())
    frodata = sum(v.get(".flash.rodata", 0) for v in per_file.values())
    ehf = sum(v.get(".eh_frame", 0) for v in per_file.values())
    print("\n[6] 常驻 flash 的段 (PSRAM XIP 执行/读取)")
    print(f"    .flash.text   (代码)      : {human(ftext)}")
    print(f"    .flash.rodata (常量/字体) : {human(frodata)}")
    print(f"    .eh_frame     (异常表)    : {human(ehf)}")
    if ehf == 0:
        print("       -> CXX 异常已关闭 (CONFIG_COMPILER_CXX_EXCEPTIONS=n)，异常表为 0")

    print("\n" + "=" * 78)
    print(" 提示: build/.../libui.a 的文件大小(数 MB)含调试信息与符号表，不代表固件占用。")
    print("=" * 78)


def main():
    ap = argparse.ArgumentParser(description="Report firmware flash/RAM usage by group and by file.")
    ap.add_argument("--project", default=None, help="project root (default: this script's directory)")
    ap.add_argument("--name", default=None,
                    help="project/binary base name (default: auto-detect from build/*.map)")
    ap.add_argument("--idf-python", default=None, help="python that can import esp_idf_size")
    args = ap.parse_args()

    root = os.path.abspath(args.project) if args.project else \
        os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(root, "build")
    name = args.name or detect_project_name(build_dir)
    if not name:
        print(f"在 {build_dir} 里找不到 .map 文件。")
        print("请先在本工程构建一次:  idf.py build")
        return 2
    map_file, bin_file, _ = find_map_and_bin(root, name)

    if not os.path.exists(map_file):
        print(f"找不到 map 文件: {map_file}")
        print("请先在本工程构建一次:  idf.py build")
        return 2

    py = find_idf_python(build_dir, args.idf_python)
    if not py:
        # Report what we can (bin size) and explain how to get the full report.
        print("=" * 78)
        print(f" 固件资源占用报告  [{name}]  (仅固件大小；按文件/分组统计不可用)")
        print("=" * 78)
        print_overall(bin_file)
        print("\n[!] 未找到能运行 IDF size 工具的 python。")
        print("    按文件/分组的精确统计需要它。解决办法(任选其一):")
        print("      1) 在 IDF 终端里运行 (先执行 export.ps1 / export.sh)，或")
        print("      2) 显式指定:  python ui_size_report.py --idf-python <路径>\\Scripts\\python.exe")
        print("    (通常它就是 IDF 的 python_env，例如 <IDF_TOOLS_PATH>\\python_env\\idf5.5_py3.11_env)")
        print("    提示: 本脚本也会自动读取 build\\CMakeCache.txt 里记录的 python；")
        print("          若这里没找到，说明该工程的 build 目录不完整，重跑一次 idf.py build 即可。")
        return 3

    try:
        per_file = load_per_file(py, map_file, root)
    except Exception as e:
        print(f"[错误] 调用 IDF size 工具失败: {e}")
        print(f"       使用的 python: {py}")
        return 4

    print_report(name, per_file, bin_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
