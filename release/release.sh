#!/usr/bin/env bash
# Build, verify and bundle io.github.rhino-lens:batik-js:1.7 for the Maven Central Portal.
# Same environment as build.sh (JDK142, optional HOST_JAVA). Set GPG_KEY to sign.
# Output: out/central-bundle.zip
set -euo pipefail
cd "$(dirname "$0")/.."

./build.sh

rm -rf out/javadoc out/bundle out/central-bundle.zip
if [ -n "${HOST_JAVA:-}" ]; then
  javadoc142() { "$HOST_JAVA" --limit-modules java.base -cp "$JDK142/lib/tools.jar" \
                   com.sun.tools.javadoc.Main -bootclasspath "$JDK142/jre/lib/rt.jar" "$@"; }
else
  javadoc142() { "$JDK142/bin/javadoc" "$@"; }
fi
javadoc142 -quiet -source 1.3 -d out/javadoc -windowtitle "batik-js 1.7" \
  -classpath out/deps/xmlbeans-2.3.0.jar:out/deps/stax-api-1.0.1.jar \
  -sourcepath src:toolsrc:xmlimplsrc:deprecatedsrc -subpackages org.mozilla 2>&1 \
  | grep -v -E 'warning|-breakiterator|^"' || true
[ -f out/javadoc/index.html ] || { echo "javadoc failed" >&2; exit 1; }

python3 -I release/make_bundle.py . out out/javadoc
