#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/dist/appimage"
APPDIR="$BUILD_DIR/OBS-Toys.AppDir"
DESKTOP_FILE="$ROOT_DIR/packaging/linux/io.github.leoberbert.obs_toys.desktop"
ICON_SOURCE="$ROOT_DIR/src/obs_toys/data/icons/obs-toys.svg"
ICON_TARGET="$APPDIR/usr/share/icons/hicolor/scalable/apps/io.github.leoberbert.obs_toys.svg"
PYTHON_LIB="$(python3 - <<'EOF'
import sysconfig
from pathlib import Path

libdir = Path(sysconfig.get_config_var("LIBDIR") or "")
ldlibrary = sysconfig.get_config_var("LDLIBRARY") or ""
candidate = libdir / ldlibrary
print(candidate if candidate.exists() else "")
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

if [[ -n "$PYTHON_LIB" && -f "$PYTHON_LIB" ]]; then
  cp "$PYTHON_LIB" "$APPDIR/usr/lib/"
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
