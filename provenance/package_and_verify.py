#!/usr/bin/env python3
"""Add resources to compiled classes, write the jar exactly as Batik's Ant build did, and verify it.

Resources are copied the way Rhino's Ant build copied them for Batik:
  - src/**/*.properties go through Ant's <filterset>, which (on Batik's build machine)
    read them as UTF-8 and wrote UTF-8. Invalid bytes, such as the Latin-1 non-breaking
    spaces in Messages_fr.properties, became U+FFFD. @IMPLEMENTATION.VERSION@ became
    "Rhino 1.6 release 6 Pre 2007 11 13" (Ant's build date for Batik's jar).
  - toolsrc/**/*.properties are copied unchanged.

The jar is written the way Ant 1.7.0's <jar> task wrote batik-js-1.7.jar:
  - entries: META-INF/, META-INF/MANIFEST.MF, then every directory, then every file,
    each group sorted by name; directories stored, files deflated (zlib level 6)
  - zip headers: "version made by" 0x0314 (Unix, 2.0), "version needed" 1.0, no data
    descriptors, Unix permissions 0755/0644, and Java's 0xCAFE jar marker on META-INF/
  - the manifest text of the original, including its Ant-Version and Created-By lines
  - the original build times, 2007-11-13 21:51 local time. Ant's build compiled src/
    first (files dated :22), then toolsrc/, xmlimplsrc/ and deprecatedsrc/ (:24), wrote
    the manifest (:24) and created META-INF/ (:26). A directory carries the time of the
    newest file or subdirectory created directly in it.

The result is compared with the reference jar entry by entry and as a whole file.

Usage: package_and_verify.py [--report] <repo-root> <classes-dir> <out-jar> [reference-jar]

Without --report the script exits 1 unless the jar is identical to the reference (the 1.7
baseline). With --report it only lists what differs, for builds that change Rhino on purpose.
"""
import hashlib, os, re, struct, sys, zipfile, zlib

IMPLEMENTATION_VERSION = "Rhino 1.6 release 6 Pre 2007 11 13"
MANIFEST = (b"Manifest-Version: 1.0\r\n"
            b"Ant-Version: Apache Ant 1.7.0\r\n"
            b"Created-By: 1.4.2_12-b03 (Sun Microsystems Inc.)\r\n"
            b"Main-Class: org.mozilla.javascript.tools.shell.Main\r\n"
            b"Class-Path: xbean.jar\r\n"
            b"\r\n")
BUILD_DATE = (2007, 11, 13, 21, 51)
STAGE_SECONDS = {"src": 22, "toolsrc": 24, "xmlimplsrc": 24, "deprecatedsrc": 24}
MANIFEST_SECONDS, META_INF_SECONDS = 24, 26
SOURCE_DIRS = ("src", "toolsrc", "xmlimplsrc", "deprecatedsrc")

args = sys.argv[1:]
report_only = "--report" in args
args = [a for a in args if a != "--report"]
root, classes, out_jar = args[0:3]
reference = args[3] if len(args) > 3 else None


def source_dir_of_class(name):
    outer = name[:-len(".class")].split("$")[0] + ".java"
    found = [d for d in SOURCE_DIRS if os.path.exists(os.path.join(root, d, outer))]
    if not found:  # a non-public top-level class declared in another file of its package
        package, simple = os.path.dirname(outer), os.path.basename(outer)[:-len(".java")]
        decl = re.compile(r"^\s*(?:(?:abstract|final|static)\s+)*(?:class|interface)\s+%s\b" % re.escape(simple), re.M)
        for d in SOURCE_DIRS:
            pdir = os.path.join(root, d, package)
            if os.path.isdir(pdir) and any(
                    f.endswith(".java") and decl.search(open(os.path.join(pdir, f), encoding="latin-1").read())
                    for f in os.listdir(pdir)):
                found.append(d)
    if len(found) != 1:
        sys.exit(f"cannot place {name} in exactly one source dir: {found}")
    return found[0]


# name -> (data, seconds)
files = {}
for base, dirs, names in os.walk(classes):
    for f in names:
        if f.endswith(".class"):
            p = os.path.join(base, f)
            name = os.path.relpath(p, classes).replace(os.sep, "/")
            files[name] = (open(p, "rb").read(), STAGE_SECONDS[source_dir_of_class(name)])

for srcdir, filtered in (("src", True), ("toolsrc", False)):
    top = os.path.join(root, srcdir)
    for base, dirs, names in os.walk(top):
        for f in names:
            if f.endswith(".properties"):
                p = os.path.join(base, f)
                data = open(p, "rb").read()
                if filtered:
                    text = data.decode("utf-8", errors="replace")
                    data = text.replace("@IMPLEMENTATION.VERSION@", IMPLEMENTATION_VERSION).encode("utf-8")
                files[os.path.relpath(p, top).replace(os.sep, "/")] = (data, STAGE_SECONDS[srcdir])

# Directories: created when their first file was written; touched by each child created in them.
created, children = {}, {}
for name, (_, sec) in files.items():
    parts = name.split("/")[:-1]
    for i in range(1, len(parts) + 1):
        d = "/".join(parts[:i]) + "/"
        created[d] = min(created.get(d, sec), sec)
for name, (_, sec) in files.items():
    parent = name.rsplit("/", 1)[0] + "/"
    children.setdefault(parent, []).append(sec)
for d in created:
    if d.count("/") > 1:
        parent = d[:-1].rsplit("/", 1)[0] + "/"
        children.setdefault(parent, []).append(created[d])
dir_seconds = {d: max([created[d]] + children.get(d, [])) for d in created}

entries = [("META-INF/", None, META_INF_SECONDS), ("META-INF/MANIFEST.MF", MANIFEST, MANIFEST_SECONDS)]
entries += [(d, None, dir_seconds[d]) for d in sorted(dir_seconds)]
entries += [(n, files[n][0], files[n][1]) for n in sorted(files)]


def dos_time(seconds):
    y, mo, d, h, mi = BUILD_DATE
    return (h << 11) | (mi << 5) | (seconds // 2), ((y - 1980) << 9) | (mo << 5) | d


out, central = bytearray(), bytearray()
for name, data, sec in entries:
    is_dir = data is None
    raw = b"" if is_dir else data
    if is_dir:
        method, comp = 0, b""
    else:
        c = zlib.compressobj(6, zlib.DEFLATED, -15, 8)
        method, comp = 8, c.compress(raw) + c.flush()
    crc = zlib.crc32(raw) & 0xFFFFFFFF
    t, d = dos_time(sec)
    fname = name.encode("utf-8")
    extra = b"\xfe\xca\x00\x00" if name == "META-INF/" else b""
    attrs = 0x41ED0010 if is_dir else 0x81A40000
    offset = len(out)
    out += struct.pack("<IHHHHHIIIHH", 0x04034B50, 10, 0, method, t, d, crc, len(comp), len(raw),
                       len(fname), len(extra)) + fname + extra + comp
    central += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 0x0314, 10, 0, method, t, d, crc,
                           len(comp), len(raw), len(fname), len(extra), 0, 0, 0, attrs, offset) + fname + extra
cd_offset = len(out)
out += central + struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(entries), len(entries),
                             len(central), cd_offset, 0)

os.makedirs(os.path.dirname(os.path.abspath(out_jar)), exist_ok=True)
open(out_jar, "wb").write(out)
sha1 = hashlib.sha1(out).hexdigest()
print(f"wrote {out_jar} ({len(entries)} entries) sha1 {sha1}")

if reference:
    ref_bytes = open(reference, "rb").read()
    ref, ours = zipfile.ZipFile(reference), zipfile.ZipFile(out_jar)
    ref_files = [n for n in ref.namelist() if not n.endswith("/")]
    our_names = set(ours.namelist())
    same = [n for n in ref_files if n in our_names and ours.read(n) == ref.read(n)]
    diff = sorted(n for n in ref_files if n in our_names and ours.read(n) != ref.read(n))
    missing = sorted(set(ref.namelist()) - our_names)
    extra = sorted(our_names - set(ref.namelist()))
    print(f"compared with {os.path.basename(reference)}: {len(same)}/{len(ref_files)} file entries identical"
          f" ({sum(n.endswith('.class') for n in same)} classes,"
          f" {sum(n.endswith('.properties') for n in same)} resources, manifest)")
    for label, names in (("DIFFERENT", diff), ("MISSING", missing), ("EXTRA", extra)):
        for n in names:
            print(f"  {label}: {n}")
    whole = out == ref_bytes
    print("whole jar file:", "IDENTICAL (sha1 %s)" % sha1 if whole
          else "differs from reference (sha1 %s)" % hashlib.sha1(ref_bytes).hexdigest())
    sys.exit(0 if whole or report_only else 1)
