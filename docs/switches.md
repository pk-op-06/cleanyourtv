# Switches on a TV

Every key a theme can set (the Keys table in [`themes/README.md`](../themes/README.md)) gets a
screenshot of what it does on a real TV. This table is where they are listed: the repo and
[cleanyour.tv/addons#switches](https://cleanyour.tv/addons#switches) both show them from here.

## Adding a key

A new key needs a screenshot. Put it in `docs/switches/<key>.jpg` (an existing screenshot in the
repo that shows the key at work also counts) and add a row below:

- From a real TV, with the key set, as a JPEG or PNG, 16:9 (1280×720 is plenty), under 300 KB.
- Show where the key changes something you can see. For a key that maps a remote button, show the
  screen the button opens; for one that changes behaviour only, show the setting's effect, such as
  the panel, the menu or the app that comes up.
- Blur anything personal: Wi-Fi names, people, addresses.

`tests/test_switches.py` checks that every key has a row here with an image that exists and fits
the rules. Keys from before this rule are on its wanted list; a screenshot for one of them is welcome.

## Screenshots

| Key | Screenshot |
|---|---|
| `columns` | <img src="../themes/six-columns/screenshot.jpg" width="320" alt="columns on a TV"> |
| `sky_intensity` | <img src="sky-sunset.jpg" width="320" alt="sky_intensity on a TV"> |
| `wallpaper_rotation_minutes` | <img src="../themes/scenes/screenshot.jpg" width="320" alt="wallpaper_rotation_minutes on a TV"> |
| `festival` | <img src="../themes/dussehra/screenshot.jpg" width="320" alt="festival on a TV"> |
| `settings_key_panel` | <img src="quick-settings-panel.jpg" width="320" alt="settings_key_panel on a TV"> |
| `home_idle_clock_minutes` | <img src="clock-screensaver.png" width="320" alt="home_idle_clock_minutes on a TV"> |
| `gamepad_passthrough` | <img src="switches/gamepad_passthrough.jpg" width="320" alt="gamepad_passthrough on a TV"> |
| `wallpaper_file` | <img src="../themes/batman/screenshot.jpg" width="320" alt="wallpaper_file on a TV"> |
| `logo_slots` | <img src="../themes/batman/screenshot.jpg" width="320" alt="logo_slots on a TV"> |
| `more_slot` | <img src="../themes/batman/screenshot.jpg" width="320" alt="more_slot on a TV"> |
| `logo_tile_height` | <img src="../themes/batman/screenshot.jpg" width="320" alt="logo_tile_height on a TV"> |
| `minimal_header` | <img src="../themes/batman/screenshot.jpg" width="320" alt="minimal_header on a TV"> |
| `bare_buttons` | <img src="../themes/batman/screenshot.jpg" width="320" alt="bare_buttons on a TV"> |
| `auto_hide_top_bar` | <img src="../themes/batman/screenshot.jpg" width="320" alt="auto_hide_top_bar on a TV"> |
| `clock_slot` | <img src="../themes/batman/screenshot.jpg" width="320" alt="clock_slot on a TV"> |
| `header_align_left` | <img src="../themes/batman/screenshot.jpg" width="320" alt="header_align_left on a TV"> |
| `logo_axis` | <img src="switches/logo_axis.jpg" width="320" alt="logo_axis on a TV"> |
| `logo_scale` | <img src="switches/logo_axis.jpg" width="320" alt="logo_scale on a TV"> |
| `day_slot` | <img src="switches/logo_axis.jpg" width="320" alt="day_slot on a TV"> |
| `date_slot` | <img src="switches/logo_axis.jpg" width="320" alt="date_slot on a TV"> |
| `day_size` | <img src="switches/logo_axis.jpg" width="320" alt="day_size on a TV"> |
| `date_size` | <img src="switches/logo_axis.jpg" width="320" alt="date_size on a TV"> |
| `clock_font` | <img src="switches/logo_axis.jpg" width="320" alt="clock_font on a TV"> |
| `tagline_slot` | <img src="switches/tagline_slot.jpg" width="320" alt="tagline_slot on a TV"> |
| `tagline_size` | <img src="switches/tagline_slot.jpg" width="320" alt="tagline_size on a TV"> |
| `app_colors` | <img src="switches/tagline_slot.jpg" width="320" alt="app_colors on a TV"> |
