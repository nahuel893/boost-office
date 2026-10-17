# UI font trial: Selawik and Inter

The Calc user interface normally uses the desktop's font (GTK `gtk-font-name`, "Noto Sans 9" on
the dev machine). The trial bundles two open fonts and lets each launch pick one of them instead.

## Use it

```sh
product/dev/calc.sh light --font inter --profile /path/to/scratch-profile
product/dev/calc.sh dark --font selawik --profile /path/to/scratch-profile
SHOT_FONT=inter product/dev/shot-tab.sh light Home /tmp/home-inter.png 1920
```

- `--font system` (the default) keeps the desktop's font. The launcher output and the profile are
  exactly what they were before the switch existed.
- `--font selawik` or `--font inter` changes the whole UI: tab bar, ribbon labels, menus,
  dialogs, tooltips and status bar. The document and cell fonts do not change.
- The font only changes the family. The size, weight and style stay the desktop's.
- `--font` works with every mode of `calc.sh` (light, dark, tabbed, ...).

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

With the item unset (the default), the plugin behaves exactly as before. A product can ship the
fonts in `share/fonts/truetype`, which VCL adds to fontconfig the same way as `user/fonts`, and set
the item in its own configuration layer. Users can change it in Tools > Options > Advanced > Open
Expert Configuration (`UIFont`). It applies after a restart.

Only the gtk3 plugin reads the item. Other VCL plugins (gtk4, Qt, Windows, macOS) ignore it.
