#!/usr/bin/env python3
"""Make the Maven Central Portal upload bundle for io.github.rhino-lens:batik-js-lens-base.

Writes, under <out>/bundle/io/github/rhino-lens/batik-js-lens-base/<version>/:
  the jar (from build.sh), a sources jar, a javadoc jar (from <javadoc-dir>) and the POM,
  each with .md5 and .sha1 files and, if GPG_KEY is set, a detached .asc signature.
Then zips that tree into <out>/central-bundle.zip, ready for "Publish Component" upload.

Usage: make_bundle.py <repo-root> <out-dir> <javadoc-dir>
"""
import hashlib, os, subprocess, sys, zipfile

GROUP, ARTIFACT, VERSION = "io.github.rhino-lens", "batik-js-lens-base", "1.7"
TIMESTAMP = (2007, 11, 13, 21, 51, 22)
SOURCE_DIRS = ("src", "toolsrc", "xmlimplsrc", "deprecatedsrc")

root, out, javadoc = sys.argv[1:4]
base = f"{ARTIFACT}-{VERSION}"
dest = os.path.join(out, "bundle", *GROUP.split("."), ARTIFACT, VERSION)
os.makedirs(dest, exist_ok=True)

def write_jar(path, files):  # files: {name: bytes}; reproducible
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, files[name])

def tree(top, keep):
    files = {}
    for b, dirs, names in os.walk(top):
        dirs.sort()
        for n in names:
            if keep(n):
                p = os.path.join(b, n)
                files[os.path.relpath(p, top).replace(os.sep, "/")] = open(p, "rb").read()
    return files

manifest = b"Manifest-Version: 1.0\r\n\r\n"
license_txt = open(os.path.join(root, "LICENSE.txt"), "rb").read()

sources = {"META-INF/MANIFEST.MF": manifest, "META-INF/LICENSE.txt": license_txt}
for d in SOURCE_DIRS:
    sources.update(tree(os.path.join(root, d), lambda n: n.endswith((".java", ".properties"))))
write_jar(os.path.join(dest, f"{base}-sources.jar"), sources)

docs = {"META-INF/MANIFEST.MF": manifest, "META-INF/LICENSE.txt": license_txt}
docs.update(tree(javadoc, lambda n: True))
write_jar(os.path.join(dest, f"{base}-javadoc.jar"), docs)

with open(os.path.join(root, "out", f"{base}.jar"), "rb") as f:
    open(os.path.join(dest, f"{base}.jar"), "wb").write(f.read())
with open(os.path.join(root, "release", "pom.xml"), "rb") as f:
    open(os.path.join(dest, f"{base}.pom"), "wb").write(f.read())

key = os.environ.get("GPG_KEY")
for name in (f"{base}.jar", f"{base}-sources.jar", f"{base}-javadoc.jar", f"{base}.pom"):
    p = os.path.join(dest, name)
    data = open(p, "rb").read()
    for algo in ("md5", "sha1"):
        open(f"{p}.{algo}", "w").write(hashlib.new(algo, data).hexdigest())
    if key:
        if os.path.exists(p + ".asc"):
            os.remove(p + ".asc")
        subprocess.run(["gpg", "--batch", "--yes", "--local-user", key, "--armor",
                        "--detach-sign", "--output", p + ".asc", p], check=True)

zpath = os.path.join(out, "central-bundle.zip")
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    bundle_root = os.path.join(out, "bundle")
    for b, dirs, names in os.walk(bundle_root):
        for n in sorted(names):
            p = os.path.join(b, n)
            z.write(p, os.path.relpath(p, bundle_root))
print(f"wrote {zpath}")
for n in sorted(os.listdir(dest)):
    print("  ", n)
if not key:
    print("NOTE: GPG_KEY not set, so no .asc signatures; Central will reject this bundle.")
