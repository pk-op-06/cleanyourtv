#!/usr/bin/env bash
# One command for the whole job: checks what this computer needs, then runs tools/setup_wizard.py, which asks every
# question first (apps to keep, services, dock, Live TV, theme, remote) and then debloats, installs the launcher,
# pushes the theme and checks the result. Usage: ./setup.sh   (macOS or Linux, from the repository root)
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null 2>&1; }
confirm() { read -r -p "$1 (y/N) " a; [[ "$a" =~ ^[Yy] ]]; }

need python3 || { echo "Python 3 is needed: https://www.python.org/downloads/ (or: brew install python)" >&2; exit 1; }

if [ ! -x tools/venv/bin/python ] || ! tools/venv/bin/python -I -c "import adb_shell" 2>/dev/null; then
  echo "The TV tools need a Python environment in tools/venv (adb-shell, rsa, cryptography from PyPI)."
  confirm "Create it now?" || exit 1
  python3 -m venv tools/venv
  tools/venv/bin/pip install -q -r tools/requirements.txt
fi

# The launcher build needs JDK 17 and the Android SDK (platform 34, build-tools 34); build-and-install.sh finds them.
if ! /usr/libexec/java_home -v 17 >/dev/null 2>&1 && [ ! -d /opt/homebrew/opt/openjdk@17 ] && ! java -version 2>&1 | grep -q '"17'; then
  echo "JDK 17 was not found; the launcher cannot be built without it."
  if need brew && confirm "Install it with Homebrew (brew install openjdk@17)?"; then brew install openjdk@17; fi
fi
if [ -z "${ANDROID_HOME:-}" ] && [ ! -d ~/Library/Android/sdk ] && [ ! -d ~/Android/Sdk ] \
   && [ ! -d /opt/homebrew/share/android-commandlinetools ]; then
  echo "The Android SDK was not found; the launcher cannot be built without it."
  if need brew && confirm "Install the command-line tools with Homebrew (brew install android-commandlinetools)?"; then
    brew install android-commandlinetools
    yes | sdkmanager --sdk_root=/opt/homebrew/share/android-commandlinetools "platforms;android-34" "build-tools;34.0.0" >/dev/null
  fi
fi

exec tools/venv/bin/python -I tools/setup_wizard.py "$@"
