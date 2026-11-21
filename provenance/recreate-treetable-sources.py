#!/usr/bin/env python3
"""Recreate toolsrc/.../debugger/downloaded/*.java exactly as Batik's Rhino build had them.

1. Extract the four TreeTable files from Sun's src.zip (archived copy:
   https://web.archive.org/web/2007id_/http://java.sun.com/products/jfc/tsc/articles/treetable2/downloads/src.zip)
2. Apply the <replace> edits from the `get-swing-ex` target of
   toolsrc/org/mozilla/javascript/tools/debugger/build.xml, read verbatim from that file.
3. Replace Sun's original header comment with the BSD license header Mozilla committed
   for the same files in rhino commit 2e746cd5 (read with `git show`).

The jar is compiled with -g:none, so the header swap does not change any class file.

Usage (from the repository root): python3 provenance/recreate-treetable-sources.py <src.zip>
"""
import os, re, subprocess, sys, zipfile
import xml.etree.ElementTree as ET

zip_path = sys.argv[1]
dbg = "toolsrc/org/mozilla/javascript/tools/debugger"
out = os.path.join(dbg, "downloaded")

# build.xml lives at 2e746cd5^ and earlier; read it from e53fc732 so this works on any checkout.
build_xml = subprocess.run(["git", "show", f"e53fc732:{dbg}/build.xml"],
                           check=True, capture_output=True).stdout
target = next(t for t in ET.fromstring(build_xml) if t.get("name") == "get-swing-ex")

os.makedirs(out, exist_ok=True)
with zipfile.ZipFile(zip_path) as z:
    for inc in target.iter("include"):
        name = inc.get("name")
        with open(os.path.join(out, name), "wb") as f:
            f.write(z.read(name))

for r in target.iter("replace"):
    path = os.path.join(dbg, r.get("file"))
    tok, val = r.find("replacetoken").text, r.find("replacevalue").text
    data = open(path, encoding="latin-1", newline="").read()
    if tok not in data:
        sys.exit(f"token not found in {path}: {tok!r}")
    open(path, "w", encoding="latin-1", newline="").write(data.replace(tok, val))

for inc in target.iter("include"):
    name = inc.get("name")
    bsd = subprocess.run(["git", "show", f"2e746cd5:{dbg}/treetable/{name}"],
                         check=True, capture_output=True, text=True).stdout
    header = re.match(r"\s*/\*.*?\*/\n", bsd, re.S).group(0).lstrip()
    path = os.path.join(out, name)
    data = open(path, encoding="latin-1", newline="").read()
    data = re.sub(r"\A\s*/\*.*?\*/[ \t]*\r?\n", "", data, count=1, flags=re.S)  # drop Sun's header, if any
    open(path, "w", encoding="latin-1", newline="").write(header + data)
    print("wrote", path)
