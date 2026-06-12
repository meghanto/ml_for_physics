#!/usr/bin/env python3
"""Preload the course's packages into the in-page JupyterLite (Pyodide) kernel.

The myst book theme starts thebe-lite's JupyterLite server without passing any
options (`connectToJupyterLiteServer()`), so its hardcoded default kernel
settings always win and no jupyter-lite.json config can reach them. This script
injects a `loadPyodideOptions.packages` list into those defaults inside the
built thebe-lite bundle, so the in-browser kernel boots with everything already
installed and notebooks need no `%pip install` cell.

Usage: python3 patch_thebe_lite.py [build_dir]   (default: _build/html)
Run after every `jupyter-book build --html` / `myst build --html`.
"""

import json
import re
import sys
from pathlib import Path

PACKAGES = [
    # available in the Pyodide distribution
    "numpy",
    "scipy",
    "matplotlib",
    "pandas",
    "micropip",
    # not in the distribution: loaded as wheels from the PyPI CDN
    "https://files.pythonhosted.org/packages/83/11/00d3c3dfc25ad54e731d91449895a79e4bf2384dc3ac01809010ba88f6d5/seaborn-0.13.2-py3-none-any.whl",
    "https://files.pythonhosted.org/packages/56/6d/0d9848617b9f753b87f214f1c682592f7ca42de085f564352f10f0843026/ipywidgets-8.1.8-py3-none-any.whl",
]

build_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "_build/html")
bundle = build_dir / "thebe-lite.min.js"
src = bundle.read_text()

if 'whl",loadPyodideOptions:' in src:
    print(f"{bundle} already patched")
    sys.exit(0)

# Anchor on the default pyodide-kernel plugin settings object:
#   {pipliteUrls:[...],pipliteWheelUrl:"...piplite-X.Y.Z-py3-none-any.whl"}
pattern = re.compile(r'(pipliteWheelUrl:"[^"]*piplite-[\d.]+-py3-none-any\.whl")\}')
matches = pattern.findall(src)
if len(matches) != 1:
    sys.exit(
        f"expected exactly 1 default-settings anchor in {bundle}, "
        f"found {len(matches)} - thebe-lite layout changed?"
    )

patched = pattern.sub(
    lambda m: m.group(1) + ",loadPyodideOptions:{packages:" + json.dumps(PACKAGES) + "}}",
    src,
    count=1,
)
bundle.write_text(patched)
print(f"patched {bundle}: kernel now preloads {len(PACKAGES)} packages")
