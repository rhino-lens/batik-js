# Build recipe: how this repository reproduces batik-js-1.7.jar exactly

`build.sh` follows this recipe and fails unless the jar's SHA-1 is
`688eb1bf13b7a54491fcb3405068fc5092589884`, the same as
`org.apache.xmlgraphics:batik-js:1.7`. Every item below matters: change one and the
jar stops matching. Keep using the same recipe for builds that change Rhino on purpose
(`MODE=report ./build.sh`), so the only differences from 1.7 are the ones you made.

## 1. Source

| What | Value | Why |
|---|---|---|
| Rhino | trunk `e53fc732` (2006-11-18) | Batik's `README.js.txt` says `cvs co -D2006-11-20`; the 1.6R5 tag lacks `Context.reportWarning(String, Throwable)` |
| Patch | bug 367627, attachment 288467 (`provenance/bug367627-288467.patch`) | Batik's debugger fix; touches only `SwingGui.java` |
| TreeTable sources | Sun's archived `src.zip` + the `build.xml` edits, BSD headers from `2e746cd5` (`provenance/recreate-treetable-sources.py`) | Rhino's build downloaded these; headers do not affect classes (`-g:none`) |
| Source dirs compiled | `src`, `toolsrc`, `xmlimplsrc`, `deprecatedsrc` | All four went into Batik's jar (`deprecatedsrc` adds 3 exception classes) |

## 2. Compiler

| What | Value | Why |
|---|---|---|
| Compiler | Sun J2SDK **1.4.2_12-b03** `javac` (`lib/tools.jar`) | The jar's manifest says `Created-By: 1.4.2_12-b03` |
| Class library | 1.4.2_12 `jre/lib/rt.jar` as boot classpath | Method references compile against these signatures |
| Flags | `-g:none -source 1.3 -target 1.3 -nowarn` | Classes are version 47.0 with no debug attributes |
| E4X classpath | `xmlbeans-2.3.0.jar`, `stax-api-1.0.1.jar` (Maven Central, SHA-1 checked) | `xmlimplsrc` needs them; 2.2.0 gives the same classes |
| Invocation | one `javac` call over all four dirs, or one per dir; both give identical classes | |
| Host JVM | any. On Linux x86 run 1.4.2_12 natively; elsewhere set `HOST_JAVA` (Java 9+) and run `tools.jar` with `--limit-modules java.base` | Without `--limit-modules`, a modern JDK silently uses its own `javac` instead |
| Unpacking the JDK | `tools.jar` and `rt.jar` ship as pack format 3.0; only the bundled Linux x86 `lib/unpack` reads it | Corretto 11's `unpack200` rejects 3.0; do this once on Linux x86 |

## 3. Resources

| File | Rule | Why |
|---|---|---|
| `src/**/*.properties` | read as UTF-8, invalid bytes become U+FFFD, write UTF-8; `@IMPLEMENTATION.VERSION@` becomes `Rhino 1.6 release 6 Pre 2007 11 13` | Ant's `<filterset>` copy on Batik's build machine did this. It damaged the 13 non-breaking spaces in `Messages_fr.properties`; keep the damage |
| `toolsrc/**/*.properties` | copied unchanged | No filter in `toolsrc/build.xml` |

## 4. The jar file (Ant 1.7.0 `<jar>` layout)

| What | Value |
|---|---|
| Entry order | `META-INF/`, `META-INF/MANIFEST.MF`, all directories (sorted), all files (sorted) |
| Manifest | `Manifest-Version: 1.0`, `Ant-Version: Apache Ant 1.7.0`, `Created-By: 1.4.2_12-b03 (Sun Microsystems Inc.)`, `Main-Class: org.mozilla.javascript.tools.shell.Main`, `Class-Path: xbean.jar`, CRLF line endings, blank line at the end |
| Compression | directories stored; files deflated, zlib level 6, raw deflate (wbits -15), memLevel 8 |
| Headers | version made by `0x0314`, version needed `10`, flags `0`, no data descriptors, no comment |
| Attributes | directories `0x41ED0010` (0755 + DOS dir bit), files `0x81A40000` (0644) |
| Extra field | `FE CA 00 00` (Java's jar marker) on `META-INF/` only, in both headers |
| Times | 2007-11-13 21:51 local; files from `src/` :22; from `toolsrc/`, `xmlimplsrc/`, `deprecatedsrc/` :24; manifest :24; `META-INF/` :26; a directory has the time of the newest file or subdirectory created directly in it |

## 5. Checks

- `./build.sh`: compares every entry and the whole file with `batik-js-1.7.jar`; exits 1 unless identical.
- `MODE=report ./build.sh`: same build, lists the entries that differ and exits 0. Use it when changing Rhino on purpose; anything listed that you did not mean to change is a mistake.
- If zlib ever changes its level-6 output, the classes and resources still compare equal but the whole-file check fails. The entry-by-entry lines show which case you are in.
