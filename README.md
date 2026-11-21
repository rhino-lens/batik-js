# batik-js-lens

The exact Mozilla Rhino JavaScript engine shipped in Apache Batik 1.7 (`org.apache.xmlgraphics:batik-js:1.7`), rebuilt from public source and published under `io.github.rhino-lens`.

> Not affiliated with or endorsed by the Apache Software Foundation or Mozilla.

## Use it

```xml
<dependency>
  <groupId>io.github.rhino-lens</groupId>
  <artifactId>batik-js-lens</artifactId>
  <version>1.7</version>
</dependency>
```

It replaces `org.apache.xmlgraphics:batik-js:1.7`. Remove that dependency (or exclude it where another library pulls it in) so only one copy of `org.mozilla.javascript` is on the classpath. The Java package is unchanged, so no code changes are needed.

## Proof it is identical

| Step | Evidence |
|---|---|
| The jar is Batik's | [`lib/js.jar`](https://github.com/apache/xmlgraphics-batik/blob/batik-1_7/lib/js.jar) at Batik tag `batik-1_7` (last changed in commit [`de8efc1b`](https://github.com/apache/xmlgraphics-batik/commit/de8efc1bfddfaae5f180a0a790eade82ccd1c6a7)) is byte-identical to `batik-js-1.7.jar` on Maven Central (SHA-1 `688eb1bf13b7a54491fcb3405068fc5092589884`). |
| The source is Rhino trunk `e53fc732` | Batik's [`README.js.txt`](provenance/batik-1.7-README.js.txt) says to check out Rhino with `cvs co -D2006-11-20`. That is trunk, not the 1.6R5 release tag: the jar has `Context.reportWarning(String, Throwable)`, which the tag lacks. The last trunk commit before that date is [`e53fc732`](https://github.com/mozilla/rhino/commit/e53fc732eceaff572c3002c88992dcdc7c529531). |
| Every class matches | Compiled as below, this repository produces all **269** classes of the jar, **byte-identical** (`cmp` per class). |

## What differs from plain Rhino trunk

This repository is Rhino's own git history up to `e53fc732`, plus two additions that Batik's build had and trunk alone does not:

1. **Batik's debugger patch:** [bug 367627](https://bugzilla.mozilla.org/show_bug.cgi?id=367627), [attachment 288467](https://bugzilla.mozilla.org/attachment.cgi?id=288467). It changes only `toolsrc/.../debugger/SwingGui.java`. A copy is in [`provenance/bug367627-288467.patch`](provenance/bug367627-288467.patch); apply it to plain trunk with `patch -p0`.
2. **Four debugger TreeTable sources** in `toolsrc/.../debugger/downloaded/`. Rhino's build downloaded them from Sun's TreeTable sample, a URL that no longer exists. They are recovered from the [Internet Archive](https://web.archive.org/web/2007id_/http://java.sun.com/products/jfc/tsc/articles/treetable2/downloads/src.zip) with the same edits Rhino's `build.xml` made, by [`provenance/recreate-treetable-sources.py`](provenance/recreate-treetable-sources.py). Their license headers are the BSD headers Mozilla later committed for the same code (rhino commit [`2e746cd5`](https://github.com/mozilla/rhino/commit/2e746cd5fb4de9a641b10550909997acb508d324)).

Batik's own note on how its jar was made is kept verbatim in [`provenance/batik-1.7-README.js.txt`](provenance/batik-1.7-README.js.txt).

The script engine (`org.mozilla.javascript` and its subpackages, except the debugger) is plain trunk `e53fc732`.

## Build it yourself

You need Sun J2SDK **1.4.2_12** (the jar's manifest says `Created-By: 1.4.2_12-b03`) from the Oracle Java SE archive, plus `xmlbeans-2.3.0.jar` and `stax-api-1.0.1.jar` from Maven Central for E4X.

```sh
find src toolsrc xmlimplsrc deprecatedsrc -name '*.java' > files.txt
$JDK142/bin/javac -nowarn -g:none -source 1.3 -target 1.3 \
  -classpath xmlbeans-2.3.0.jar:stax-api-1.0.1.jar \
  -d out @files.txt
```

Then compare each `.class` in `out/` with the same entry in `batik-js-1.7.jar`.

## License

Rhino is dual-licensed under the Mozilla Public License 1.1 and the GNU GPL 2.0 (see the header of each source file). The four TreeTable sources are under a BSD license from Sun Microsystems (see their headers).

## Sources

Everything this project started from:

| What | Link |
|---|---|
| Original jar on Maven Central | [`org.apache.xmlgraphics:batik-js:1.7`](https://repo1.maven.org/maven2/org/apache/xmlgraphics/batik-js/1.7/) |
| Apache Batik repository | [apache/xmlgraphics-batik](https://github.com/apache/xmlgraphics-batik) |
| Batik commit that last changed the jar before tag `batik-1_7` | [`de8efc1b`](https://github.com/apache/xmlgraphics-batik/commit/de8efc1bfddfaae5f180a0a790eade82ccd1c6a7) |
| The jar inside Batik | [`lib/js.jar`](https://github.com/apache/xmlgraphics-batik/blob/batik-1_7/lib/js.jar) |
| Batik's note on its Rhino build | [`lib/README.js.txt`](https://github.com/apache/xmlgraphics-batik/blob/batik-1_7/lib/README.js.txt) |
| Mozilla Rhino repository | [mozilla/rhino](https://github.com/mozilla/rhino) |
| Rhino trunk commit used | [`e53fc732`](https://github.com/mozilla/rhino/commit/e53fc732eceaff572c3002c88992dcdc7c529531) "Updates for version 1.6R5." (2006-11-18) |
| Batik's Rhino patch | [Bugzilla attachment 288467](https://bugzilla.mozilla.org/attachment.cgi?id=288467) on [bug 367627](https://bugzilla.mozilla.org/show_bug.cgi?id=367627) |
| Sun TreeTable sample (archived) | [Internet Archive copy of `src.zip`](https://web.archive.org/web/2007id_/http://java.sun.com/products/jfc/tsc/articles/treetable2/downloads/src.zip) |
| BSD headers for the TreeTable files | Rhino commit [`2e746cd5`](https://github.com/mozilla/rhino/commit/2e746cd5fb4de9a641b10550909997acb508d324) |
| Compiler (Sun J2SDK 1.4.2_12) | [Oracle Java SE 1.4 archive](https://www.oracle.com/java/technologies/java-archive-javase-v14-downloads.html) |
| E4X compile dependencies | [`xmlbeans:2.3.0`](https://repo1.maven.org/maven2/org/apache/xmlbeans/xmlbeans/2.3.0/), [`stax-api:1.0.1`](https://repo1.maven.org/maven2/stax/stax-api/1.0.1/) |

## Roadmap

Opt-in hooks for observing and debugging the scripts Rhino executes, kept separate from the unchanged 1.7 baseline.
