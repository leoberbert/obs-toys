#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUILD_DIR="$ROOT_DIR/dist/appimage"
APPDIR="$BUILD_DIR/OBS-Toys.AppDir"
DESKTOP_FILE="$ROOT_DIR/packaging/linux/io.github.leoberbert.obs_toys.desktop"
ICON_SOURCE="$ROOT_DIR/src/obs_toys/data/icons/obs-toys.svg"
ICON_TARGET="$APPDIR/usr/share/icons/hicolor/scalable/apps/io.github.leoberbert.obs_toys.svg"
PYTHON_BIN="$(command -v python3)"
PYTHON_VERSION="$(python3 - <<'EOF'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
EOF
)"
PYTHON_PREFIX="$APPDIR/usr/python"
PYTHON_SITE_PACKAGES="$PYTHON_PREFIX/lib/python$PYTHON_VERSION/site-packages"
SYSTEM_DIST_PACKAGES="/usr/lib/python3/dist-packages"
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
PYTHON_STDLIB="$(python3 - <<'EOF'
import sysconfig
print(sysconfig.get_path("stdlib") or "")
EOF
)"

rm -rf "$APPDIR"
mkdir -p \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/lib" \
  "$APPDIR/usr/lib/girepository-1.0" \
  "$PYTHON_PREFIX/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps"

cp "$ROOT_DIR/packaging/linux/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
cp "$DESKTOP_FILE" "$APPDIR/usr/share/applications/"
cp "$ICON_SOURCE" "$ICON_TARGET"
ln -sf "usr/share/applications/$(basename "$DESKTOP_FILE")" "$APPDIR/$(basename "$DESKTOP_FILE")"
ln -sf "usr/share/icons/hicolor/scalable/apps/io.github.leoberbert.obs_toys.svg" \
  "$APPDIR/io.github.leoberbert.obs_toys.svg"
ln -sf "usr/share/icons/hicolor/scalable/apps/io.github.leoberbert.obs_toys.svg" \
  "$APPDIR/.DirIcon"

if [[ -n "$PYTHON_LIBS" ]]; then
  while IFS= read -r libpath; do
    [[ -z "$libpath" ]] && continue
    cp -L "$libpath" "$APPDIR/usr/lib/"
    if [[ -L "$libpath" ]]; then
      ln -sf "$(basename "$(readlink -f "$libpath")")" "$APPDIR/usr/lib/$(basename "$libpath")"
    fi
  done <<< "$PYTHON_LIBS"
fi

cp -L "$PYTHON_BIN" "$PYTHON_PREFIX/bin/python3"

if [[ -n "$PYTHON_STDLIB" && -d "$PYTHON_STDLIB" ]]; then
  mkdir -p "$PYTHON_PREFIX/lib/python$PYTHON_VERSION"
  cp -a "$PYTHON_STDLIB"/. "$PYTHON_PREFIX/lib/python$PYTHON_VERSION"/
fi

mkdir -p "$PYTHON_SITE_PACKAGES"
python3 -m pip install --upgrade pip wheel setuptools
python3 -m pip install --no-deps --target "$PYTHON_SITE_PACKAGES" "$ROOT_DIR"

for path in \
  "$SYSTEM_DIST_PACKAGES/gi" \
  "$SYSTEM_DIST_PACKAGES/pygtkcompat" \
  "$SYSTEM_DIST_PACKAGES/cairo" \
  "$SYSTEM_DIST_PACKAGES/PyGObject-"*.dist-info \
  "$SYSTEM_DIST_PACKAGES/pycairo-"*.dist-info; do
  [[ -e "$path" ]] || continue
  cp -a "$path" "$PYTHON_SITE_PACKAGES"/
done

if [[ -d /usr/lib/x86_64-linux-gnu/girepository-1.0 ]]; then
  cp -a /usr/lib/x86_64-linux-gnu/girepository-1.0/. "$APPDIR/usr/lib/girepository-1.0"/
fi

if command -v setfattr >/dev/null 2>&1; then
  find "$APPDIR" -exec setfattr -x system.posix_acl_access {} + 2>/dev/null || true
  find "$APPDIR" -exec setfattr -x system.posix_acl_default {} + 2>/dev/null || true
fi

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
