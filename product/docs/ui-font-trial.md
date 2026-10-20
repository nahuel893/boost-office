# UI font trial: Selawik and Inter

The Calc user interface normally uses the desktop's font (GTK `gtk-font-name`, "Noto Sans 9" on
the dev machine). The trial bundled two open fonts and let each launch pick one of them instead.
On 2026-10-20 the user picked Inter: it is now the default UI font of the Boost looks.

## Use it

```sh
product/dev/calc.sh light --profile /path/to/scratch-profile                 # Inter
product/dev/calc.sh light --font system --profile /path/to/scratch-profile   # the desktop's font
product/dev/calc.sh dark --font selawik --profile /path/to/scratch-profile
SHOT_FONT=system product/dev/shot-tab.sh light Home /tmp/home-system.png 1920
```

- Without `--font`, the Boost looks (`light` and `dark`) use Inter. The stock LibreOffice modes
  (`tabbed`, `tabbed-light`, `compact`) keep the desktop's font. `shot-tab.sh` always shoots the
  Boost looks, so `SHOT_FONT` defaults to `inter` there.
- `--font system` keeps the desktop's font in any mode. The launcher output and the profile are
  exactly what they were before the switch existed.
- `--font selawik` or `--font inter` changes the whole UI: tab bar, ribbon labels, menus,
  dialogs, tooltips and status bar. The document and cell fonts do not change.
- The font only changes the family. The size, weight and style are the desktop's at startup. While
  a font is set, a desktop font change made while Calc runs applies only after a restart.
- `--font` (and `SHOT_FONT`) wins over the default; it works with every mode of `calc.sh` (light, dark, tabbed, ...).

## What it does

1. **Fonts.** `product/fonts/selawik/` and `product/fonts/inter/` hold the static TTFs with their
   SIL OFL 1.1 license. `product/dev/profile.py --font NAME` copies the chosen font into the
   profile's `user/fonts`, which VCL adds to the font path.
2. **Choice.** `profile.py` also writes one configuration item,
   `/org.openoffice.VCL/VCLSettings/UIFont/FamilyName` (`Selawik` or `Inter`). With `system`,
   nothing is copied and no item is written.
3. **Effect.** The gtk3 VCL plugin reads that item once, before it loads its GTK styles
   (`vcl/unx/gtk3/salnativewidgets-gtk.cxx`, `applyConfiguredUIFontFamily`). If it is not empty,
   the plugin:
   - replaces the family in GTK's `gtk-font-name` and keeps the size. An application value wins
     over XSETTINGS, GSettings and the settings portal, so it holds in the headless sway and in a
     normal desktop session, for this process only;
   - makes sure the office's own fonts are added to fontconfig, and resets pango's default font
     map, because pango keeps the font list it read before VCL added them.

   Native GTK widgets (menus, dialogs, entries) take the font from GTK. VCL widgets (tab bar,
   ribbon labels, status bar) take it from the fonts the plugin reads back from GTK.

## Why this way

A shipped suite sets its own UI font whatever the desktop's font is, so the setting lives in the
office's configuration, not in the launcher's environment:

- GTK's `settings.ini` loses to GSettings on Wayland and to XSETTINGS on X11.
- A private `gtk.css` works only when `XDG_CONFIG_HOME` points to a private directory. That would
  also move the user's dconf and `~/.config/libreoffice`, so a product cannot do it.
- LibreOffice's configuration had no UI font setting for gtk3. `UI_SANS` in VCL.xcu is only a
  glyph fallback, and the `UseSystemUIFonts` flag is only saved and restored, never acted on.

The VCL schema default stays empty. With the item unset, the plugin behaves exactly as before. A product can ship the
fonts in `share/fonts/truetype`, which VCL adds to fontconfig the same way as `user/fonts`, and set
the item in its own configuration layer. Users can change it in Tools > Options > Advanced > Open
Expert Configuration (`UIFont`). It applies after a restart.

Only the gtk3 plugin reads the item. Other VCL plugins (gtk4, Qt, Windows, macOS) ignore it.

## Known limitations

These were found by reading the GTK and Pango sources and have not been reproduced:

- pango's default font map is kept per thread. If a non-main thread creates the first window, for
  example `soffice --invisible --accept=...`, native GTK widgets do not see the bundled font.
- If fontconfig is reinitialized while Calc runs, for example because a font was installed, GTK3
  drops the folders VCL added. Native GTK menus and dialogs then fall back to another sans, while
  VCL widgets keep the trial font.
- The family name is not validated. A misspelled name, or a font missing from `user/fonts`,
  switches the UI to a fallback font, and nothing is logged.

Fix these before the setting ships or goes upstream.
