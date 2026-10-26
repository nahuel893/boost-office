# Fork Strategy

Decision date: 2026-10-12. Status: accepted.

## Goal

Ship an installable, open-source office suite based on LibreOffice, under the name Boost Office (branded at install time, not at configure time: the splash, the logos and the product name are an overlay and a configuration item, so only compiled-in strings still say LibreOfficeDev), competing in the market.

## Model: develop on master, ship from release branches

```
master ───●───●───●───●───●───●───●───●───►   development; upstreamable work goes to Gerrit
            \                   \
libreoffice-26-8 ──●──●──●       libreoffice-27-2 ──●──●
                    \                                 \
product/26.8 ────────●──●──●──►    product/27.2 ───────●──●──►   shipped builds
                (our patch stack)        (same patches ported)
```

This mirrors how existing vendors work: upstream hosts `distro/<vendor>/<version>` branches for Collabora, CIB, MIMO, LHM, Vector, SUSE, allotropia and others.

## Rules

1. **Upstream first.** Anything generic goes to LibreOffice Gerrit: performance work, bug fixes, and features upstream would accept. Once merged, upstream maintains it.
2. **Isolate product-only changes in new files.** Example: a new `notebookbar_office.ui` variant registered in `officecfg`, instead of editing the existing `notebookbar.ui`. New files rarely conflict.
3. **Monthly:** merge upstream minor releases (`libreoffice-X-Y-Z`) into the product branch. They carry security fixes and must not be skipped.
4. **Twice a year:** when upstream branches a new major release (February and August), port the patch stack onto it.
5. **Branding is configuration, not patches.** Use the configure options `--with-product-name`, `--with-branding` and `--with-vendor`.

## Constraints

- **License:** MPL 2.0. Modified files stay MPL, and their source must be published when distributed.
- **Trademark:** "LibreOffice" is a trademark of The Document Foundation. The product must use a different name.
- **Upstream velocity:** about 770 commits per month (measured 2026-10-12). A hard fork is not sustainable.

## Local setup

- **Checkout:** `/mnt/games/libreoffice/core`, a shallow clone (`--depth 1`). Fetch without `--depth` so new commits connect to the existing history.
- **Remote:** `upstream` points to `https://git.libreoffice.org/core`. The product remote `origin` is `https://github.com/nahuel893/boost-office` (`main` is the default branch, `dev` the integration branch).
