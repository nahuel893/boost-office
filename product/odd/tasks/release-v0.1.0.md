# Feature: the first public release, Boost Office 0.1.0

- **Status:** in progress, started 2026-10-25.
- **Locator:** `product/odd/tasks/release-v0.1.0.md`
- **Engram mirror:** `odd/release-v0.1.0/tasks`
- **Repo / branch:** worktree `/mnt/games/libreoffice/core-release`, branch `release/v0.1.0`, from `main`
  (e9112a65f). A separate worktree because `/mnt/games/libreoffice/core` is busy with `feature/start-center`.
- **Built tree:** `/mnt/games/libreoffice/release-v0.1.0/instdir`, a copy of `core/instdir` taken on 2026-10-25 before
  the Start Center work rebuilt anything (`libsfxlo.so` 2026-10-23 11:26, the G3-gated build of e9112a65f). Optimized,
  no dbgutil, no debug symbols (`config_host.mk`: `ENABLE_OPTIMIZED=TRUE`, `ENABLE_DBGUTIL=`); 716 MB.

## Objective

Anyone on a common Linux x86_64 desktop can download one file from GitHub Releases, extract it and run `./install.sh`,
with no build and no development packages, and get Boost Office (Writer, Calc, Impress with the Boost ribbons).

## Problem and why

The user (2026-10-25): "quiero desplegar y versionar el estado actual. Asi ya es instalable para cualquier user".
Today `product/install/install.sh` needs a built `instdir` (hours of building), and the repository has no tag and no
release.

## Rulings (controller, 2026-10-25; the user asked for no questions and no review stops)

1. **Version:** `0.1.0`, tag `v0.1.0` on `main` once the release commits are merged; a normal GitHub Release titled
   "Boost Office 0.1.0" (the notes call it a first preview). The state shipped is `main` at e9112a65f plus the
   release tooling; the Start Center redesign is not in it.
2. **Artifact:** `boost-office-0.1.0-linux-x86_64.tar.xz` (xz: every distro's tar reads it) and `SHA256SUMS`. One top
   folder `boost-office-0.1.0/` holding `install.sh` and `uninstall.sh` at the top, `instdir/`, what the installer
   needs from `product/` (with the icon zips prebuilt, so the user needs no Pillow and no `rsvg-convert`), the
   README, the install guide, and the license files.
3. **Tracked packaging:** `product/release/make-release.sh --instdir DIR --version X --out DIR` builds that artifact
   from any built tree, so later releases repeat the same steps; with tests.
4. **Installer from the bundle:** run with no arguments from the extracted folder, `./install.sh` installs that
   bundle's `instdir` with the documented defaults; everything else about `install.sh` stays as G1-G3 left it.
5. **Requirements from evidence:** the notes state the minimum glibc measured from the shipped binaries (the highest
   `GLIBC_` symbol version they need) and the runtime needs (gtk3, python3 for the installer). The bundle is proved on
   this machine (a scratch install from the extracted archive, GUI screenshot) and in containers of other distros
   (podman: at least `ubuntu:24.04` and `fedora:latest`; install, then a headless conversion of a Writer, a Calc and an
   Impress file). A distro the binaries cannot run on is named in the notes with the reason; no rebuild for 0.1.0.
6. **Docs:** a tracked `product/release/notes-0.1.0.md` (what is in it, requirements, install in three commands,
   known issues: window titles say "LibreOfficeDev", stock Start Center, no spelling dictionaries bundled, Linux only,
   unsigned); the README gains a "Download" section pointing at the latest release.
8. **One command (the user, 2026-10-25: "el instalador tiene que ser one command, copiar y pegar un comando y lo deja
   listo. Nada de descargar, descomprimir e instalar"):** a third asset `boost-office-install.sh` (version and archive
   sha256 embedded) so the whole install is
   `curl -fsSL https://github.com/nahuel893/boost-office/releases/latest/download/boost-office-install.sh | bash`
   (options via `| bash -s -- --theme dark`, `--uninstall`, `--purge`). It checks the platform and tools, downloads
   and verifies the archive, extracts to a temp directory, runs the bundled installer, cleans up with a trap; uninstall
   works without the archive (the uninstaller is kept in the prefix); re-running upgrades in place. The docs present
   the one-liner as the way to install; the archive is the manual/offline alternative. Supersedes the "three
   commands" wording in ruling 6.
7. **Publishing:** the controller pushes the branch, fast-forwards `main` and `dev`, tags, and creates the release with
   `gh` (the user asked to deploy). The writer never pushes, tags or publishes.

## Tasks

- [x] **R1 — packaging, verification, docs** (delegated, one writer: 2+ non-trivial files plus container checks):
  rulings 2-6, 8-10; commits 77a1932f9, 6533513a9, 563908f3a, d84cffdde, 9c417412f, 67aac9d81, fd6c896e0.
- [ ] **R2 — publish** (controller, inline: `git`/`gh` state operations): spot-check the archive, push, fast-forward
  `main`/`dev`, tag `v0.1.0`, `gh release create`, download the published asset and compare its checksum.

## Acceptance criteria

1. The archive extracts to `boost-office-0.1.0/`, and `./install.sh` from it installs and launches Writer, Calc and
   Impress with the Boost look on this machine (scratch home).
2. Installs and headless conversions succeed in the `ubuntu:24.04` and `fedora:latest` containers, or the notes name
   the failure and its cause.
3. The release page carries the archive, `SHA256SUMS` and the notes; the downloaded asset matches its checksum.
4. The unit suite is green.

## Checks

- `python3 -I -m unittest discover -s product/tests -t .` (full suite once in R1).
- The archive build, the host install, the container runs, the checksum.

## Progress / evidence

- 2026-10-25: built tree copied; worktree and branch created; feature document written.
- 2026-10-25 R1 first pass (delegated, opus; route: writer trigger, scripts + tests + docs + container proof): commits
  77a1932f9 (release archive), 6533513a9 (one-command install, ruling 8), 563908f3a (notes and docs). Suite 1063 OK.
  Archive 205 MB. **Measured glibc floor 2.44** (`cosh`/`sinh` in `libsclo.so`, `libskialo.so`; `GLIBCXX_3.4.32`):
  host Manjaro and `archlinux:latest` pass; `ubuntu:24.04` (2.39) and `fedora:latest` (44, 2.43) install but cannot
  start. Launchers forcing gtk3 broke `--headless` without a display (exit 0, no output).
- 2026-10-25 controller rulings 9-10 (sent to R1):
  9. The one-liner refuses, before downloading, on a glibc older than the embedded floor, with a clear message
     (rolling distributions only for 0.1.0; a portable build is planned; how to build from source); `--uninstall` is
     never gated.
  10. Launchers do not force gtk3 when the arguments include `--headless`, `--convert-to`, `--print-to-file` or
     `--cat`.
  Publish 0.1.0 as an Arch/Manjaro release with that gate ("deploy and version the current state"); "installable for
  any user" needs a build on an older base system: planned as the next feature (0.1.1), not a 0.1.0 blocker.

- 2026-10-25 R1 second pass: d84cffdde (headless launchers, ruling 10), 9c417412f + 67aac9d81 (glibc gate, ruling 9),
  fd6c896e0 (notes). Suite 1068 OK (RED observed for both rulings). Assets in
  `/mnt/games/libreoffice/release-v0.1.0/out/`: archive 213960172 bytes sha256
  `4269e2e033ca4346298a6d95de0611967d19ffd7faef2bf6eefe024361efb035`, `boost-office-install.sh` sha256
  `406b12770a34bd0a639aac762d71b52c9053fd8f5e7cb9e9a8b29109228b84a8`, `SHA256SUMS`. Host Manjaro install + Writer shot
  + purge clean; `archlinux:latest` six headless conversions with no VCL override; `ubuntu:24.04` refused (exit 1,
  only the script fetched). Controller spot-check: `sha256sum -c` OK; 4347 archive entries, no `instdir/user/`, no
  `.lock`, no e-mail address in the archive bytes; bootstrap carries version, sha256, floor 2.44 and the GitHub URL.
  Not done: libstdc++ check (unreliable, redundant with the glibc floor); `./install.sh` from the archive does not
  check glibc (notes say so).

## Next step

R2 (publish).
