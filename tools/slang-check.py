#!/usr/bin/env python3
"""slang-check.py — compile RetroArch .slang shaders (or every pass of .slangp presets) with Khronos glslang,
the way RetroArch preprocesses them: expand #include (relative to the including file), split at
`#pragma stage vertex|fragment` (lines before the first stage pragma go to both), drop `#pragma parameter|name|
format` lines, then compile each stage to Vulkan SPIR-V. Exits non-zero if anything fails.

Usage:
    python tools/slang-check.py <file.slang|preset.slangp> [...]   [--glslang PATH]
glslang: --glslang, else $GLSLANG, else `glslang` on PATH (Khronos release builds: github.com/KhronosGroup/glslang/releases).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile


def expand(path, seen=()):
    path = os.path.normpath(path)
    if path in seen:
        raise RuntimeError(f"recursive #include of {path}")
    out = []
    with open(path, encoding="utf-8") as f:
        for ln in f.read().splitlines():
            m = re.match(r'\s*#include\s+"([^"]+)"', ln)
            if m:
                out += expand(os.path.join(os.path.dirname(path), m.group(1)), seen + (path,))
            else:
                out.append(ln)
    return out


def split_stages(lines):
    stages, cur = {"vertex": [], "fragment": []}, None
    for ln in lines:
        m = re.match(r"\s*#pragma\s+stage\s+(\w+)", ln)
        if m:
            cur = m.group(1)
            stages[cur].append("")                         # keep line numbers roughly aligned
            continue
        if re.match(r"\s*#pragma\s+(parameter|name|format)\b", ln):
            ln = ""
        if cur is None:
            for s in stages.values():
                s.append(ln)
        else:
            stages[cur].append(ln)
    return stages


def check_slang(path, glslang):
    ok = True
    stages = split_stages(expand(path))
    with tempfile.TemporaryDirectory() as td:
        for st, ext in (("vertex", "vert"), ("fragment", "frag")):
            src = os.path.join(td, f"pass.{ext}")
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(stages[st]) + "\n")
            r = subprocess.run([glslang, "-V", "--target-env", "vulkan1.0", "-S", ext, src, "-o", os.path.join(td, ext + ".spv")],
                               capture_output=True, text=True)
            msg = (r.stdout + r.stderr).replace(src, f"{os.path.basename(path)}[{st}]").strip()
            if r.returncode != 0:
                ok = False
                print(f"FAIL {path} [{st}]\n{msg}\n")
    if ok:
        print(f"ok   {path}")
    return ok


def preset_passes(path):
    base = os.path.dirname(path)
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    return [os.path.normpath(os.path.join(base, m.group(1).strip().strip('"')))
            for m in re.finditer(r"^\s*shader\d+\s*=\s*(.+?)\s*$", txt, re.M)]


def main(argv):
    glslang = os.environ.get("GLSLANG") or shutil.which("glslang")
    files = []
    it = iter(argv)
    for a in it:
        if a == "--glslang":
            glslang = next(it)
        else:
            files.append(a)
    if not files:
        print(__doc__)
        return 2
    if not glslang or not os.path.exists(shutil.which(glslang) or glslang):
        print("glslang not found: pass --glslang PATH, set $GLSLANG, or put glslang on PATH")
        return 2
    todo = []
    for f in files:
        todo += preset_passes(f) if f.endswith(".slangp") else [f]
    ok = True
    for s in dict.fromkeys(todo):                          # each pass once, in order
        ok &= check_slang(s, glslang)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
