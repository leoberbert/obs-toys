#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/dist/appimage"
APPDIR="$BUILD_DIR/OBS-Toys.AppDir"
DESKTOP_FILE="$ROOT_DIR/packaging/linux/io.github.leoberbert.obs_toys.desktop"
ICON_SOURCE="$ROOT_DIR/src/obs_toys/data/icons/obs-toys.svg"
ICON_TARGET="$APPDIR/usr/share/icons/hicolor/scalable/apps/io.github.leoberbert.obs_toys.svg"
PYTHON_LIBS="$(python3 - <<'EOF'
import sysconfig
from pathlib import Path

libdir = Path(sysconfig.get_config_var("LIBDIR") or "")
names = []
for key in ("LDLIBRARY", "INSTSONAME", "PY3LIBRARY"):
    value = sysconfig.get_config_var(key)
    if value:
        candidate = libdir / value
        if candidate.exists():
            names.append(str(candidate))
for item in dict.fromkeys(names):
    print(item)
EOF
)"

rm -rf "$APPDIR"
mkdir -p \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/lib" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps"

cp "$ROOT_DIR/packaging/linux/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
cp "$DESKTOP_FILE" "$APPDIR/usr/share/applications/"
cp "$ICON_SOURCE" "$ICON_TARGET"
ln -sf "usr/share/applications/$(basename "$DESKTOP_FILE")" "$APPDIR/$(basename "$DESKTOP_FILE")"
ln -sf "$ICON_TARGET" "$APPDIR/io.github.leoberbert.obs_toys.svg"

if [[ -n "$PYTHON_LIBS" ]]; then
  while IFS= read -r libpath; do
    [[ -z "$libpath" ]] && continue
    cp -L "$libpath" "$APPDIR/usr/lib/"
    if [[ -L "$libpath" ]]; then
      ln -sf "$(basename "$(readlink -f "$libpath")")" "$APPDIR/usr/lib/$(basename "$libpath")"
    fi
  done <<< "$PYTHON_LIBS"
fi

python3 -m venv --copies --system-site-packages "$APPDIR/usr/venv"
"$APPDIR/usr/venv/bin/pip" install --upgrade pip wheel setuptools
"$APPDIR/usr/venv/bin/pip" install --no-deps "$ROOT_DIR"

cat > "$APPDIR/usr/bin/obs-toys" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec "$APPDIR/AppRun" "$@"
EOF
chmod +x "$APPDIR/usr/bin/obs-toys"

APPIMAGETOOL="$BUILD_DIR/appimagetool.AppImage"
if [[ ! -f "$APPIMAGETOOL" ]]; then
  curl -L -o "$APPIMAGETOOL" \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "$APPIMAGETOOL"
fi

ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$BUILD_DIR/OBS-Toys-x86_64.AppImage"
