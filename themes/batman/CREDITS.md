# Credits for themes/batman

Batman is a trademark of DC Comics. The pictures and logos below belong to their owners; they are here for use on
your own TV and are not covered by this repository's MIT licence.

| File | What it is | Source |
|---|---|---|
| `wallpaper.jpg` | Gotham skyline and Bat-Signal, used by Classic | Drawn in code by `make/make_gotham.py` (MIT) |
| `wallpaper-arc.webp` | Batman in shadow (Dark Knight layout), brightened and grained | [Wallhaven 6lld66](https://wallhaven.cc/w/6lld66), `make/make_wallpapers.py` |
| `wallpaper-side.webp` | Comic Batman with arms crossed (Gotham Guardian layout), dimmed | [Wallhaven poo9ze](https://wallhaven.cc/w/poo9ze), `make/make_wallpapers.py` |
| `launcher/.../drawable-nodpi/banner_white_*.png` | White app glyphs for the layouts | Wikimedia Commons: `Netflix 2016 N logo.svg`, `Prime Video logo (2024).svg`, `YouTube Logo 2017.svg`, `ZEE5 2025.svg`, `VLC Icon.svg`, `JioHotstar 2025.png`; the Sony LIV mark is set in SuperClarendon and Arial Rounded. `make/fetch.py` and `make/make_white_hq.py` rebuild them |
| `preview-*.webp`, `screenshot.jpg` | Home on a Xiaomi MiTV-MZTU0 | Screenshots from the TV |

The layouts name a weekday font, `font-anurati.otf`, that is not in the repository: Anurati's free download is a
demo licence that does not allow redistribution, and it has no digits. Put your own copy beside `config.json` under
that name (the setup wizard asks for it) or leave it out; the weekday then uses the launcher's font.
