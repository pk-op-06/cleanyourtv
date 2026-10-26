#!/usr/bin/env python3
"""Interactive setup: asks everything first, then debloats the TV, installs the launcher and pushes a theme.

Run it through ./setup.sh from the repository root, which prepares tools/venv first. Every step uses the repository's
own tools (tv.py, disable.sh, launcher/build-and-install.sh, push-theme.sh, adb-closed.py), so their safety checks
apply: packages are disabled, never uninstalled; Android's core packages are refused; the stock launcher goes off only
after the new one owns Home. Undo with the restore command it prints at the end.

The answers are saved in work/setup-<model>.json, and a second run offers them as the defaults.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
PY = str(TOOLS / "venv" / "bin" / "python")
WORK = ROOT / "work"

# Friendly names for apps the TV shows only as package names. Unknown packages are listed as they are.
KNOWN_APPS = {
    "com.netflix.ninja": "Netflix", "com.google.android.youtube.tv": "YouTube",
    "com.amazon.amazonvideo.livingroom": "Prime Video", "in.startv.hotstar": "JioHotstar",
    "com.jio.jioplay.tv": "JioTV (live TV)", "com.jio.media.stb.ondemand": "JioCinema",
    "com.sonyliv": "Sony LIV", "com.graymatrix.did": "ZEE5", "org.videolan.vlc": "VLC",
    "com.google.android.videos": "Google TV app", "com.google.android.youtube.tvmusic": "YouTube Music",
    "com.disney.disneyplus": "Disney+", "com.apple.atve.androidtv.appletv": "Apple TV",
    "com.spotify.tv.android": "Spotify", "com.mxtech.videoplayer.television": "MX Player",
    "com.mitv.livetv": "Live TV (Xiaomi tuner/HDMI)", "com.mediatek.wwtv.tvcenter": "Live TV (MediaTek tuner)",
    "com.android.vending": "Google Play Store", "com.xiaomi.mitv.mediaexplorer": "USB media player",
    "com.mitv.gallery": "Gallery", "com.xiaomi.mitv.smartshare": "Mi Cast", "com.xiaomi.mitv.tvmanager": "TV Manager",
    "com.teamsmart.videomanager.tv": "SmartTube", "org.smarttube.beta": "SmartTube",
    "com.cloudtv.sonyliv": "Sony LIV", "com.erosnow.tv": "Eros Now", "com.altbalaji.android": "ALTT",
    "com.mxplayer.tv": "MX Player", "com.voot.tv": "Voot", "com.tatasky.binge": "Tata Play Binge",
}
LIVE_TV_HINTS = ("livetv", "tvcenter", "jioplay", "tvinput", "dtv", "tuner")

# Services people use without opening them: asked one by one, kept unless the answer is no.
SERVICES = [
    ("com.google.android.katniss", "Google Assistant / voice search (the mic button)"),
    ("com.google.android.apps.mediashell", "Chromecast built-in (casting from phones and laptops)"),
    ("com.mediatek.partner.airplay_sys", "AirPlay (casting from iPhone/Mac)"),
    ("com.xiaomi.mitv.smartshare", "Mi Cast / screen mirroring"),
    ("com.xiaomi.wfdsinkhelperservice", "Miracast"),
    ("com.xiaomi.mitv.updateservice", "Firmware updates (Xiaomi)"),
    ("com.mitv.upgrader", "Firmware updates (Xiaomi upgrader)"),
    ("com.mediatek.tv.systemupdater", "Firmware updates (MediaTek)"),
]
# Telemetry, promo and cleaner packages that are safe to disable wherever they exist.
ALWAYS_SAFE = [
    "com.miui.tv.analytics", "com.xiaomi.statistic", "com.xiaomi.tvqs.overseas.y24", "com.xiaomi.tvqs.overseas",
    "com.google.android.feedback", "com.xm.webcontent", "com.xiaomi.mitv.tvmanager",
    "com.mitv.tvhome.oemtab", "com.mitv.tvhome.michannel", "com.mitv.tvhome.mitvplus", "com.mitv.tvhome.atv",
    "android.autoinstalls.config.google.gtvpai", "android.autoinstalls.config.xiaomi.amelie",
    "com.google.android.tvrecommendations", "fusion.android.tv.demo",
]
SETUP_WIZARD = "com.google.android.tungsten.setupwraith"


# ---- terminal helpers ---------------------------------------------------------------------------------------------

def say(text=""):
    print(text, flush=True)


def title(text):
    say()
    say("=" * 72)
    say(text)
    say("=" * 72)


def ask(question, default=""):
    hint = f" [{default}]" if default != "" else ""
    answer = input(f"{question}{hint}: ").strip()
    return answer or str(default)


def yes(question, default=True):
    answer = ask(question + (" (Y/n)" if default else " (y/N)"), "").lower()
    return default if answer == "" else answer.startswith("y")


def pick_numbers(prompt, count, default):
    """Numbers like '1 3 4' or '1-3,5' from 1..count, in the order typed."""
    while True:
        raw = ask(prompt, default)
        if raw.lower() in ("all", "*"):
            return list(range(count))
        out = []
        try:
            for part in re.split(r"[ ,]+", raw.strip()):
                if not part:
                    continue
                if "-" in part:
                    a, b = part.split("-", 1)
                    out.extend(range(int(a), int(b) + 1))
                else:
                    out.append(int(part))
        except ValueError:
            say("  Please type numbers, e.g. 1 2 5 or 1-4.")
            continue
        if all(1 <= n <= count for n in out):
            seen = []
            for n in out:
                if n - 1 not in seen:
                    seen.append(n - 1)
            return seen
        say(f"  Numbers go from 1 to {count}.")


# ---- the TV -------------------------------------------------------------------------------------------------------

class TV:
    def __init__(self, host):
        self.host = host
        self.env = dict(os.environ, TV_HOST=host)

    def sh(self, command, check=False, timeout=180):
        r = subprocess.run([PY, "-I", str(TOOLS / "tv.py"), command], env=self.env, capture_output=True, text=True,
                           timeout=timeout)
        if check and r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or r.stdout.strip())
        return r.stdout

    def run_tool(self, args, extra_env=None, cwd=ROOT):
        env = dict(self.env, **(extra_env or {}))
        say(f"\n$ {' '.join(str(a) for a in args)}")
        return subprocess.run([str(a) for a in args], env=env, cwd=cwd).returncode

    def probe(self):
        r = subprocess.run([PY, "-I", str(TOOLS / "tv.py"), "--probe"], env=self.env, capture_output=True, text=True,
                           timeout=150)
        return r.returncode == 0, r.stdout + r.stderr

    def packages(self, flags=""):
        return sorted(line.split(":", 1)[1].strip() for line in self.sh(f"pm list packages {flags}").splitlines()
                      if line.startswith("package:"))

    def launchable(self):
        out = self.sh("cmd package query-activities --brief -a android.intent.action.MAIN "
                      "-c android.intent.category.LEANBACK_LAUNCHER")
        apps = []
        for line in out.splitlines():
            line = line.strip()
            if "/" in line and not line.startswith(("priority", "Activity")):
                pkg = line.split("/", 1)[0]
                if pkg not in apps:
                    apps.append(pkg)
        return apps


def find_tv_candidates():
    """Hosts that answer mDNS for ADB or Cast (macOS dns-sd only); best effort."""
    if not shutil.which("dns-sd"):
        return []
    found = []
    for service in ("_adb._tcp", "_googlecast._tcp"):
        try:
            p = subprocess.Popen(["dns-sd", "-B", service, "local."], stdout=subprocess.PIPE, text=True)
            time.sleep(3)
            p.terminate()
            out = p.communicate(timeout=3)[0]
        except Exception:  # noqa: BLE001 - discovery is only a hint
            continue
        for line in out.splitlines():
            if " Add " in line:
                found.append(line.split()[-1])
    return found


# ---- steps --------------------------------------------------------------------------------------------------------

def connect():
    title("1. Connect to the TV")
    say("On the TV: Settings > Device Preferences > About > press OK on 'Build' 7 times, then Developer options >")
    say("turn on USB debugging (and Network/ADB debugging if it is there). The TV and this computer must share Wi-Fi.")
    names = find_tv_candidates()
    if names:
        say("Seen on the network: " + ", ".join(names) + "  (the TV's IP is in Settings > Network & Internet)")
    while True:
        host = ask("The TV's IP address (e.g. 192.168.1.50)")
        tv = TV(host)
        say("Connecting... if the TV shows 'Allow USB debugging?', choose Allow (tick 'Always allow').")
        ok, out = tv.probe()
        if ok:
            say(out.strip())
            return tv
        say("Could not connect: " + (out.strip().splitlines() or ["no answer"])[-1])
        if not yes("Try again?"):
            sys.exit(1)


def device_info(tv):
    props = {}
    for key in ("ro.product.model", "ro.product.manufacturer", "ro.build.version.sdk", "ro.build.display.id",
                "ro.product.device"):
        props[key] = tv.sh(f"getprop {key}").strip()
    sdk = int(props["ro.build.version.sdk"] or 0)
    if sdk < 26:
        say(f"This TV runs SDK {sdk}; the launcher needs 26 (Android 8). Only the debloat half is possible.")
    return props


def matching_example(model):
    """The examples/ list whose header names this model, if any."""
    for path in sorted((ROOT / "examples").glob("*/debloat.txt")):
        head = path.read_text(encoding="utf-8", errors="replace")[:600]
        if model and model.lower() in head.lower():
            return path
    return None


def list_entries(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line.split()[0])
    return out


def backup(tv, model):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = ROOT / "backup" / f"{re.sub(r'[^A-Za-z0-9_-]', '_', model)}-{stamp}"
    folder.mkdir(parents=True, exist_ok=True)
    dumps = {
        "packages-all.txt": "pm list packages -f -U", "packages-disabled.txt": "pm list packages -d",
        "packages-thirdparty.txt": "pm list packages -3", "getprop.txt": "getprop",
        "settings-system.txt": "settings list system", "settings-secure.txt": "settings list secure",
        "settings-global.txt": "settings list global",
        "home-candidates.txt": "cmd package query-activities --brief -a android.intent.action.MAIN "
                               "-c android.intent.category.HOME",
    }
    for name, command in dumps.items():
        (folder / name).write_text(tv.sh(command), encoding="utf-8")
    say(f"Backup written to {folder.relative_to(ROOT)}")
    return folder


def ask_apps(tv, saved):
    title("2. Which apps do you use?")
    apps = [p for p in tv.launchable() if p != "com.gathin.tvhome"]
    for i, pkg in enumerate(apps, 1):
        say(f"  {i:2}. {KNOWN_APPS.get(pkg, pkg)}" + (f"   ({pkg})" if pkg in KNOWN_APPS else ""))
    default = " ".join(str(apps.index(p) + 1) for p in saved.get("keep", []) if p in apps) or "all"
    say("Apps you do not pick are switched off (not uninstalled; the restore command brings them back).")
    keep = [apps[i] for i in pick_numbers("Numbers of the apps to KEEP ('all' keeps every one)", len(apps), default)]
    tuners = [p for p in apps if p not in keep and any(h in p for h in LIVE_TV_HINTS)]
    if tuners:
        say("Kept anyway (they run Live TV and on some TVs the HDMI inputs): "
            + ", ".join(KNOWN_APPS.get(p, p) for p in tuners))
    return apps, keep


def ask_services(tv, installed, saved):
    title("3. Background services")
    off = []
    for pkg, label in SERVICES:
        if pkg not in installed:
            continue
        keep_default = pkg not in saved.get("services_off", [])
        if not yes(f"Keep {label}?", keep_default):
            off.append(pkg)
    return off


def ask_dock(apps, keep, saved):
    title("4. The dock")
    choices = [p for p in keep if p in apps]
    for i, pkg in enumerate(choices, 1):
        say(f"  {i:2}. {KNOWN_APPS.get(pkg, pkg)}")
    raw = ask("How many dock slots (4-7)", saved.get("dock_size", min(7, max(4, len(choices)))))
    size = max(4, min(7, int(raw))) if raw.isdigit() else 7
    default = " ".join(str(choices.index(p) + 1) for p in saved.get("dock", []) if p in choices) \
        or " ".join(str(i) for i in range(1, min(size, len(choices)) + 1))
    order = [choices[i] for i in pick_numbers(f"Dock apps in order (up to {size})", len(choices), default)][:size]
    live = [p for p in choices if any(h in p for h in LIVE_TV_HINTS)]
    live_tv = ""
    if live:
        say("Live TV apps: " + ", ".join(f"{i}. {KNOWN_APPS.get(p, p)}" for i, p in enumerate(live, 1)))
        n = ask("Which one is your Live TV (shown in the Inputs menu; 0 for none)", saved.get("live_tv_index", 1))
        if n.isdigit() and 1 <= int(n) <= len(live):
            live_tv = live[int(n) - 1]
    return size, order, live_tv


def ask_theme(saved):
    title("5. Theme")
    themes = sorted(p.name for p in (ROOT / "themes").iterdir() if (p / "config.json").is_file())
    for i, name in enumerate(themes, 1):
        say(f"  {i:2}. {name}")
    default = themes.index(saved["theme"]) + 1 if saved.get("theme") in themes else themes.index("default") + 1
    theme = themes[pick_numbers("Theme number", len(themes), default)[0]]
    font = ""
    layouts = list((ROOT / "themes" / theme).glob("config-*.json"))
    wants_font = any("clock_font" in p.read_text(encoding="utf-8") for p in layouts)
    if wants_font:
        say("This theme's layouts can use a display font for the weekday (e.g. Anurati, not shipped here).")
        font = ask("Path to a .otf/.ttf font, or leave empty to skip", saved.get("font", ""))
    if layouts:
        say("After setup, the Theme button (first icon top right) switches between this theme's layouts.")
    return theme, font


def ask_remote(saved):
    title("6. Remote buttons")
    say("Google TV remotes often have YouTube and Apps buttons that only the stock home screen answered.")
    youtube = yes("Does your remote have a YouTube button?", saved.get("youtube_button", True))
    input_helper = yes("Turn on the Input-button helper (use it if the Input/Source button stops working)?",
                       saved.get("input_helper", False))
    return youtube, input_helper


def write_theme(theme, font, size, dock, live_tv, youtube, model):
    src = ROOT / "themes" / theme
    out = WORK / f"theme-{re.sub(r'[^A-Za-z0-9_-]', '_', model)}"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("screenshot.jpg", "make", "*.md", "*.py"))
    config = json.loads((out / "config.json").read_text(encoding="utf-8"))
    config["dock_apps"] = dock
    config["columns"] = size
    if live_tv:
        config["live_tv_package"] = live_tv
        # The Inputs menu opens it; a tuner app off the dock would otherwise be one more tile.
        if live_tv not in dock:
            config["hidden_apps"] = sorted(set(config.get("hidden_apps", [])) | {live_tv})
    keys = [k for k in config.get("app_keys", []) if not k.startswith("190:")]
    if youtube:
        keys.append("190:com.google.android.youtube.tv")
    config["app_keys"] = keys
    (out / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    for layout in out.glob("config-*.json"):
        data = json.loads(layout.read_text(encoding="utf-8"))
        if "logo_slots" in data:
            # A layout draws one slot per dock app: keep only the apps that have a logo and a slot.
            banners = {e.split("=", 1)[0] for e in data.get("app_banners", [])}
            data["dock_apps"] = [p for p in dock if p in banners][:len(data["logo_slots"])] or dock
        layout.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if font:
        font_path = Path(os.path.expanduser(font))
        if font_path.is_file():
            shutil.copy(font_path, out / ("font-anurati" + font_path.suffix.lower()))
        else:
            say(f"Font not found: {font_path}; the weekday keeps the launcher's font.")
    return out


def debloat_list(installed, disabled, apps, keep, services_off, example, model):
    entries = []
    if example:
        entries += list_entries(example)
    entries += ALWAYS_SAFE
    # An unticked app goes off, except the store and Live TV/tuner apps: on some TVs the tuner app also owns the
    # HDMI input switcher (Xiaomi's com.mitv.livetv does), and switching it off loses input switching.
    entries += [p for p in apps if p not in keep and p != "com.android.vending"
                and not any(h in p for h in LIVE_TV_HINTS)]
    entries += services_off
    # A service asked about in step 3 goes off only when the answer was no, whatever a list or an unticked app says.
    asked = {pkg for pkg, _ in SERVICES}
    entries = [p for p in entries if p not in asked or p in services_off]
    seen, out = set(), []
    for pkg in entries:
        if pkg in installed and pkg not in disabled and pkg not in seen and pkg not in keep and pkg != SETUP_WIZARD:
            seen.add(pkg)
            out.append(pkg)
    path = WORK / f"debloat-{re.sub(r'[^A-Za-z0-9_-]', '_', model)}.txt"
    path.write_text(f"# {model}: written by tools/setup_wizard.py\n" + "\n".join(out) + "\n", encoding="utf-8")
    return path, out


def setup_wizard_step(tv):
    """Google TV: the setup wizard may own the saved Wi-Fi network; disabling it then deletes that network."""
    if SETUP_WIZARD not in tv.packages("-e"):
        return
    owners = tv.sh("dumpsys wifi | grep -o 'cname=[^ ]*' | sort -u")
    on_wifi = "WIFI" in tv.sh("dumpsys connectivity | grep -m1 -o 'Active default network.*'") or "WIFI" in \
        tv.sh("dumpsys connectivity | grep -m1 'NetworkAgentInfo'")
    title("Google TV setup wizard")
    say("The new home screen needs Google TV's setup wizard switched off, or Home can crash-loop.")
    if "setupwraith" in owners:
        say("Your saved Wi-Fi network belongs to the setup wizard: switching it off makes the TV forget that network.")
        say("Have the Wi-Fi password ready, or plug in Ethernet first.")
        if not yes("Switch the setup wizard off now?"):
            say("Left on: the launcher half is skipped.")
            raise SystemExit(1)
    path = WORK / "debloat-setupwizard.txt"
    path.write_text(SETUP_WIZARD + "\n", encoding="utf-8")
    tv.run_tool([TOOLS / "disable.sh", path], {"FORCE_SETUPWRAITH": "1"})
    if "setupwraith" in owners and on_wifi:
        say("\nOn the TV: Settings > Network & Internet > your Wi-Fi > join it again with the password.")
        say("Check that Developer options > USB debugging is still on.")
        input("Press Enter here when the TV is back on Wi-Fi... ")
        while not tv.probe()[0]:
            if not yes("No answer from the TV yet. Try again?"):
                raise SystemExit(1)


def build_and_install(tv, input_helper):
    title("Building and installing the launcher")
    env = {"HOME_KEY_SERVICE": "1"}
    if input_helper:
        env["INPUT_KEY_SERVICE"] = "1"
    return tv.run_tool(["./build-and-install.sh"], env, cwd=ROOT / "launcher")


def close_adb(tv):
    title("Last step: close the debug port")
    say("Port 5555 is plaintext: anything on your Wi-Fi can get a shell while it is open.")
    say("On the TV: Developer options > turn off USB debugging (and Network debugging), optionally revoke authorisations.")
    input("Press Enter when that is done... ")
    subprocess.run([PY, "-I", str(TOOLS / "adb-closed.py"), tv.host])


# ---- main ---------------------------------------------------------------------------------------------------------

def main():
    title("CleanYourTV setup")
    say("Asks everything first, then: backup, debloat, new home screen, theme, checks. Nothing is uninstalled.")
    tv = connect()
    props = device_info(tv)
    model = props["ro.product.model"] or "tv"
    saved_path = WORK / f"setup-{re.sub(r'[^A-Za-z0-9_-]', '_', model)}.json"
    saved = json.loads(saved_path.read_text(encoding="utf-8")) if saved_path.is_file() else {}
    example = matching_example(model)
    say(f"\n{props['ro.product.manufacturer']} {model}, SDK {props['ro.build.version.sdk']}, {props['ro.build.display.id']}")
    say(f"Tested list for this model: {example.relative_to(ROOT)}" if example else
        "No tested list for this model: only telemetry/promo packages and the apps you untick are switched off.")

    installed = set(tv.packages())
    disabled = set(tv.packages("-d"))
    apps, keep = ask_apps(tv, saved)
    services_off = ask_services(tv, installed, saved)
    size, dock, live_tv = ask_dock(apps, keep, saved)
    theme, font = ask_theme(saved)
    youtube, input_helper = ask_remote(saved)

    WORK.mkdir(exist_ok=True)
    list_path, entries = debloat_list(installed, disabled, apps, keep, services_off, example, model)
    theme_dir = write_theme(theme, font, size, dock, live_tv, youtube, model)
    saved = {"keep": keep, "services_off": services_off, "dock_size": size, "dock": dock, "theme": theme,
             "font": font, "youtube_button": youtube, "input_helper": input_helper}
    saved_path.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")

    title("Summary")
    say(f"Switch off {len(entries)} packages (list: {list_path.relative_to(ROOT)}):")
    for pkg in entries:
        say(f"   - {KNOWN_APPS.get(pkg, pkg)}" + (f" ({pkg})" if pkg in KNOWN_APPS else ""))
    say(f"Dock ({size} slots): " + ", ".join(KNOWN_APPS.get(p, p) for p in dock))
    say(f"Live TV: {KNOWN_APPS.get(live_tv, live_tv) if live_tv else 'none'}   Theme: {theme}   "
        f"YouTube button: {'yes' if youtube else 'no'}")
    if not yes("\nRun all of it now?"):
        say("Nothing changed on the TV. Your answers are saved; run ./setup.sh again to continue.")
        return

    backup_dir = backup(tv, model)
    if entries:
        title("Switching off packages")
        if tv.run_tool([TOOLS / "disable.sh", list_path]) != 0:
            say("disable.sh stopped; see above. Nothing else was changed.")
            return
    setup_wizard_step(tv)
    if build_and_install(tv, input_helper) != 0:
        say("The build or install failed (see above). The TV keeps its stock home screen.")
        return
    title("Pushing the theme")
    args = [TOOLS / "push-theme.sh", theme_dir] + (["--input-key-service"] if input_helper else [])
    tv.run_tool(args)

    title("Check it on the TV")
    say("Press Home, Back, every app button and the Input button on the real remote; hold Volume + for 2 s.")
    if yes("Reboot once to check Home comes back by itself?", True):
        try:
            tv.sh("reboot", timeout=30)
        except subprocess.TimeoutExpired:
            pass   # the connection drops as the TV goes down
        say("Rebooting... wait for Home on the TV.")
        input("Press Enter when Home is showing... ")
        while not tv.probe()[0]:
            if not yes("No answer yet. Try again?"):
                break
    say(f"\nUndo everything: TV_HOST={tv.host} tools/restore.sh {list_path.relative_to(ROOT)}")
    say(f"Backup of the TV's state: {backup_dir.relative_to(ROOT)}")
    close_adb(tv)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nStopped.")
