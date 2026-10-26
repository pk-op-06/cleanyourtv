#!/usr/bin/env bash
# Pushes a theme folder to the launcher file by file, checks each file's md5 on the TV, and restarts Home in short
# separate steps. tools/theme.sh does the same in one long restart command, which timed out on a Xiaomi MiTV-MZTU0
# and left the remote-key helper switched off (docs/devices/xiaomi-mitv-mztu0.md).
# Usage: TV_HOST=192.168.1.50 tools/push-theme.sh themes/batman [--input-key-service]
set -euo pipefail
THEME_ARG="${1:?usage: push-theme.sh <theme folder> [--input-key-service]}"
THEME="$(cd "$THEME_ARG" && pwd)"
SERVICES=com.gathin.tvhome/.HomeKeyService
[ "${2:-}" = --input-key-service ] && SERVICES="$SERVICES:com.gathin.tvhome/.InputKeyService"
cd "$(dirname "$0")"
[ -x venv/bin/python ] || { echo "run: python3 -m venv tools/venv && tools/venv/bin/pip install -r tools/requirements.txt" >&2; exit 1; }
: "${TV_HOST:?set TV_HOST}"
export TV_HOST
PKG=com.gathin.tvhome
DIR=/sdcard/Android/data/$PKG/files
URI=content://$PKG.theme
tv() { venv/bin/python -I tv.py "$@"; }

for F in "$THEME"/config.json "$THEME"/wallpaper.jpg "$THEME"/config-*.json "$THEME"/wallpaper-*.webp \
         "$THEME"/preview-*.webp "$THEME"/font-*.otf "$THEME"/font-*.ttf; do
  [ -f "$F" ] || continue
  NAME=$(basename "$F")
  venv/bin/python -I b64push.py "$F" "/data/local/tmp/cyt-$NAME" | grep -q MATCH || { echo "push failed: $NAME" >&2; exit 1; }
  tv "rm -f $DIR/$NAME; content write --uri $URI/$NAME < /data/local/tmp/cyt-$NAME; rm -f /data/local/tmp/cyt-$NAME" >/dev/null
  WANT=$( (md5 -q "$F" 2>/dev/null || md5sum "$F") | cut -d' ' -f1)
  GOT=$(tv "md5sum $DIR/$NAME" | cut -d' ' -f1)
  [ "$WANT" = "$GOT" ] && echo "ok   $NAME" || { echo "FAIL $NAME" >&2; exit 1; }
done

tv "am force-stop $PKG" >/dev/null
tv "am start -a android.intent.action.MAIN -c android.intent.category.HOME" >/dev/null
tv "settings put secure enabled_accessibility_services $SERVICES" >/dev/null
tv "settings put secure accessibility_enabled 1" >/dev/null
sleep 3
tv "dumpsys accessibility | grep -m1 'Bound services'"
