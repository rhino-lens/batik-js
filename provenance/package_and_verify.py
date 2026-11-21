#!/usr/bin/env python3
"""Add resources to compiled classes, write the jar, and compare it with Batik's.

Resources are copied the way Rhino's Ant build copied them for Batik:
  - src/**/*.properties go through Ant's <filterset>, which (on Batik's build machine)
    read them as UTF-8 and wrote UTF-8. Invalid bytes, such as the Latin-1 non-breaking
    spaces in Messages_fr.properties, became U+FFFD. @IMPLEMENTATION.VERSION@ became
    "Rhino 1.6 release 6 Pre 2007 11 13" (Ant's build date for Batik's jar).
  - toolsrc/**/*.properties are copied unchanged.

The jar has fixed timestamps and sorted entries, so it is reproducible. Every class and
resource entry is compared byte-for-byte with the reference jar; the manifest is ours.

Usage: package_and_verify.py <repo-root> <classes-dir> <out-jar> [reference-jar]
"""
import os, sys, zipfile

IMPLEMENTATION_VERSION = "Rhino 1.6 release 6 Pre 2007 11 13"
TIMESTAMP = (2007, 11, 13, 21, 51, 22)  # Batik's jar entries are dated 2007-11-13 21:51
MANIFEST = ("Manifest-Version: 1.0\r\n"
            "Main-Class: org.mozilla.javascript.tools.shell.Main\r\n"
            "Class-Path: xbean.jar\r\n\r\n")

root, classes, out_jar = sys.argv[1:4]
reference = sys.argv[4] if len(sys.argv) > 4 else None

entries = {}
for base, dirs, files in os.walk(classes):
    for f in files:
        if f.endswith(".class"):
            p = os.path.join(base, f)
            entries[os.path.relpath(p, classes).replace(os.sep, "/")] = open(p, "rb").read()

for srcdir, filtered in (("src", True), ("toolsrc", False)):
    top = os.path.join(root, srcdir)
    for base, dirs, files in os.walk(top):
        for f in files:
            if f.endswith(".properties"):
                p = os.path.join(base, f)
                data = open(p, "rb").read()
                if filtered:
                    text = data.decode("utf-8", errors="replace")
                    data = text.replace("@IMPLEMENTATION.VERSION@", IMPLEMENTATION_VERSION).encode("utf-8")
                entries[os.path.relpath(p, top).replace(os.sep, "/")] = data

os.makedirs(os.path.dirname(os.path.abspath(out_jar)), exist_ok=True)
with zipfile.ZipFile(out_jar, "w", zipfile.ZIP_DEFLATED) as z:
    def put(name, data):
        info = zipfile.ZipInfo(name, TIMESTAMP)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, data)
    put("META-INF/MANIFEST.MF", MANIFEST.encode("ascii"))
    for name in sorted(entries):
        put(name, entries[name])
print(f"wrote {out_jar} ({len(entries)} entries + manifest)")

if reference:
    ref = zipfile.ZipFile(reference)
    ref_entries = {n: ref.read(n) for n in ref.namelist()
                   if not n.endswith("/") and n != "META-INF/MANIFEST.MF"}
    same = [n for n in ref_entries if entries.get(n) == ref_entries[n]]
    diff = sorted(n for n in ref_entries if n in entries and entries[n] != ref_entries[n])
    missing = sorted(set(ref_entries) - set(entries))
    extra = sorted(set(entries) - set(ref_entries))
    print(f"compared with {os.path.basename(reference)}: {len(same)}/{len(ref_entries)} entries identical"
          f" ({sum(n.endswith('.class') for n in same)} classes,"
          f" {sum(n.endswith('.properties') for n in same)} resources)")
    for label, names in (("DIFFERENT", diff), ("MISSING", missing), ("EXTRA", extra)):
        for n in names:
            print(f"  {label}: {n}")
    sys.exit(0 if not (diff or missing or extra) else 1)
