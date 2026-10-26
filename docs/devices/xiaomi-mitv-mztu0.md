# Xiaomi TV A Pro (MiTV-MZTU0, river), Google TV 14: remote keys, Bluetooth, boot and theme pushes

Tested on a MiTV-MZTU0 (codename river, MediaTek merak, 1.8 GB RAM), Android 14 (SDK 34), firmware
`UKN1.240806.017.V816.0.26.5.6.5.URTMIXM`, over Wi-Fi. The debloat is [examples/xiaomi-tv-a-pro-2026](../../examples/xiaomi-tv-a-pro-2026/debloat.txt);
these are the things found after it, with the launcher in place.

## The setup Wi-Fi belongs to the setup wizard

`dumpsys wifi | grep -o 'cname=[^ ]*'` listed `com.google.android.tungsten.setupwraith` as the owner of the saved
network. Disabling setupwraith (`FORCE_SETUPWRAITH=1 tools/disable.sh`, with the stock launcher still enabled, so Home
kept an owner) deleted the network as expected; re-joining it in Settings > Network & Internet made `android.uid.system`
the owner, and USB debugging stayed on. No Ethernet was needed.

## Remote buttons after launcherx is disabled

`logcat` shows what each button sends (`WindowManager ... keyCode:`) and whether Xiaomi's `mitv.service` handles it
(`GlobalKey ... receive ACTION_GLOBAL_BUTTON`):

| Button | Keycode | After the stock launcher is gone |
|---|---|---|
| Netflix | 193 | Works: GlobalKey starts Netflix |
| Prime Video | 194 | Works: GlobalKey sends `AMAZON_BUTTON` |
| JioHotstar | 202 | Works: GlobalKey hot key |
| SonyLIV | 195 | Works: GlobalKey hot key |
| YouTube | 190 (`KEYCODE_BUTTON_3`) | Dead: only launcherx handled it. `"app_keys": ["190:com.google.android.youtube.tv"]` |
| Apps | 284 (`KEYCODE_ALL_APPS`) | Dead: Android sends `ALL_APPS` to Settings (`result code=-91`). `HOME_KEY_SERVICE=1` routes it to Home |

`HOME_KEY_SERVICE=1 launcher/build-and-install.sh` alone covers both (HomeKeyService reads `app_keys` too), and holding
Volume + still repeats with it on.

## Bluetooth settings

`android.settings.BLUETOOTH_SETTINGS` resolves to nothing on this firmware, so the top bar's Bluetooth button opens
the "Remotes and accessories" slice instead:
`am start -a android.settings.SLICE_SETTINGS --es slice_uri content://com.android.tv.settings.accessories.sliceprovider/general`.

## Shared storage mounts 30-40 s after boot

Home starts before `/sdcard/Android/data/com.gathin.tvhome/files` is readable. Without a private copy Home came up in
the built-in config, then switched to the theme when the card mounted; the launcher now keeps private copies of the
theme files in use (`Config.cached`), and Home comes up in the picked layout at about 29 s.

## theme.sh's restart times out

Every file of `tools/theme.sh` arrived (md5 match), but its last command - force-stop, Home, then the accessibility
toggle, in one shell call - ran into adb_shell's 120 s read timeout or `Connection reset by peer`, leaving
`enabled_accessibility_services` empty and the YouTube and Apps buttons dead. The same steps as separate calls take
about a second each. `tools/push-theme.sh` pushes that way and checks each file's md5 and the bound helper at the end.
A failed push can also leave `config.json` deleted (the push removes it before writing): check with
`tools/tv.py 'ls /sdcard/Android/data/com.gathin.tvhome/files'`.

## Memory

Before the debloat, 8 minutes after boot: 760 MB available of 1.8 GB, the stock launcher at about 137 MB PSS
(launcherx 113 MB + coreservices 24 MB). After: the launcher at 26-34 MB PSS with a wallpaper. Right after a reboot the
Play Store and Play services run update jobs (about 125 MB together) that hide the gain until they finish.
