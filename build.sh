#!/usr/bin/env bash
# Build batik-js-lens-base and verify it against org.apache.xmlgraphics:batik-js:1.7.
#
# Requires:
#   JDK142   an installed Sun J2SDK 1.4.2_12 (with lib/tools.jar and jre/lib/rt.jar unpacked)
#   python3, curl
#
# On Linux x86, JDK 1.4.2_12 runs natively. Elsewhere (e.g. macOS), set HOST_JAVA to a
# Java 9+ `java`: the 1.4.2_12 compiler (tools.jar) then runs on it, compiling against
# 1.4.2_12's rt.jar. Both give byte-identical classes.
#
# Output: out/batik-js-lens-base-1.7.jar, byte-identical to batik-js-1.7.jar (the build fails otherwise)
#
# MODE=report keeps the same recipe but only lists entries that differ from batik-js-1.7.jar,
# for work that changes Rhino on purpose. See RECIPE.md for every detail of the recipe.
set -euo pipefail
cd "$(dirname "$0")"

: "${JDK142:?set JDK142 to the J2SDK 1.4.2_12 directory}"
OUT=out
DEPS=$OUT/deps
CLASSES=$OUT/classes
MAVEN=https://repo1.maven.org/maven2

fetch() {  # fetch <maven path> <sha1>: download into $DEPS and check the SHA-1
  local f="$DEPS/$(basename "$1")"
  [ -f "$f" ] || curl -sSfL -o "$f" "$MAVEN/$1"
  local got; got=$(python3 -I -c 'import hashlib,sys;print(hashlib.sha1(open(sys.argv[1],"rb").read()).hexdigest())' "$f")
  [ "$got" = "$2" ] || { echo "SHA-1 mismatch for $f: $got" >&2; exit 1; }
  echo "$f"
}

if [ -n "${HOST_JAVA:-}" ]; then
  javac142() { "$HOST_JAVA" --limit-modules java.base -cp "$JDK142/lib/tools.jar" \
                 com.sun.tools.javac.Main -bootclasspath "$JDK142/jre/lib/rt.jar" "$@"; }
else
  javac142() { "$JDK142/bin/javac" "$@"; }
fi

rm -rf "$CLASSES" && mkdir -p "$CLASSES" "$DEPS"
XMLBEANS=$(fetch org/apache/xmlbeans/xmlbeans/2.3.0/xmlbeans-2.3.0.jar 8704dcf5c9f10265a08f5020b0fab70eb64ac3c4)
STAX=$(fetch stax/stax-api/1.0.1/stax-api-1.0.1.jar 49c100caf72d658aca8e58bd74a4ba90fa2b0d70)
REFERENCE=$(fetch org/apache/xmlgraphics/batik-js/1.7/batik-js-1.7.jar 688eb1bf13b7a54491fcb3405068fc5092589884)

find src toolsrc xmlimplsrc deprecatedsrc -name '*.java' | sort > "$OUT/files.txt"
javac142 -nowarn -g:none -source 1.3 -target 1.3 \
  -classpath "$XMLBEANS:$STAX" -d "$CLASSES" @"$OUT/files.txt"

REPORT=(); [ "${MODE:-verify}" = report ] && REPORT=(--report)
python3 -I provenance/package_and_verify.py "${REPORT[@]+"${REPORT[@]}"}" . "$CLASSES" "$OUT/batik-js-lens-base-1.7.jar" "$REFERENCE"
