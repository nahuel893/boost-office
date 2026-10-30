# Feature: the Apply Style box stops refilling on every cursor move (release 0.1.4)

- **Status:** in progress, 2026-10-29.
- **Locator:** `product/odd/tasks/style-box-perf.md`; **Engram mirror:** `odd/style-box-perf/tasks`.
- **Repo / branch:** `/mnt/games/libreoffice/core`, branch `feature/style-box-perf` from `main` (8e4d81b62). Runners:
  `python3 -I -m unittest discover -s product/tests -t .`; LibreOffice CppUnit/UITest through `product/dev/lo-make.sh`
  and `product/dev/uitest.sh`.
- **First heavy change to LibreOffice C++ code:** design first, test first, independent verification, blind dual review.

## Specs

- **S1** The user (2026-10-29): "hace un analisis del rendimiento de libre office. Abriendo archivos medianos. Se traba
  muchisimo."
- **S2** The user (2026-10-29), after the analysis: "Si, me encantaria que apliques esto. Es nuestro primer cambio heavy
  de codigo de libre office. Asi que procuremos usar las mejores metodologias de ingenieria y revision con subagentes.
  Usando ODD como venimos haciendo". "Esto" = the recommendation: fix 1 (refill the list only when the styles change)
  together with fix 2 (fill the list only when the drop-down opens), shipped in 0.1.4.
- **S3** Evidence (P1, `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-P1-report.md`): at 61,105 cell styles
  every cursor move costs about 1.2 s wall / 0.9 s main-thread CPU in `SvxStyleToolBoxControl::FillStyleBox()`
  (`svx/source/tbxctrls/tbcontrl.cxx:3104`, `// TODO: Check whether fill is necessary` at `:3116`), reached from
  `Update()` (`:3213`/`:3251`) through `statusChanged`/`SetFamilyState` (`:3257-3281`); about 2 s more right after
  opening (`addStatusListener`). Stock LibreOffice pays the same (hidden `.uno:StyleApply` still gets a controller).
  Synthetic reproducer: `/mnt/games/libreoffice/perf-scratch-w4ly/files/stylebloat.xlsx` and the P1 harness in
  `/mnt/games/libreoffice/perf-scratch-w4ly/scripts/`.

## Rulings (controller, 2026-10-29)

1. **Behavior kept:** the box always shows the current style of the selection, and its list is always the same set
   and order as today (no stale entry after creating, deleting, renaming, hiding or modifying a style, undo/redo,
   loading another document into the frame, switching between documents/windows, switching family: paragraph,
   character, cell, drawing/presentation styles; Writer, Calc, Impress, Draw). Typing a new style name in the box
   (create by example) and picking an entry keep working, keyboard and accessibility included.
2. **Performance target:** with `stylebloat.xlsx`, a cursor move costs under 0.05 s main-thread CPU (from 0.9 s), and
   the time to a usable window drops by the post-open fill (about 2 s); opening the drop-down may cost what one fill
   costs today. Normal documents get no slower.
3. **Scope:** the narrowest change in `svx` (and where hints come from, if needed); no change to `.ui`/toolbar
   definitions, no Boost-only switch: the fix is meant to be upstreamable (LibreOffice coding style, a CppUnit or
   UITest that would be accepted upstream).
4. **Out of scope:** capping the list (fix 3), cleaning the user's file, hidden-item controllers (fix 5).
5. **Release:** ships as 0.1.4, built and proven as 0.1.3 was.
6. **Design (2026-10-29, on D1):** design B, "fill when engaged". The box keeps only the current style name while it
   is neither focused nor open; it fills the full list (exactly today's `FillStyleBox`) on focus-in and on popup
   toggle, and while engaged every update refills as today; a non-engaged update after a fill clears the list once
   (idle task if that clear costs over 0.05 s). LibreOfficeKit always counts as engaged. Pool re-read from
   `SfxObjectShell::Current()` at fill time. State in `SvxStyleToolBoxControl::Impl`. Fix 1 (refill on pool hints) is
   dropped: svl has no "created" hint, Writer's undo of a delete sends none, and Calc's "Used" styles change with cell
   content, so a hint-driven list would go stale (ruling 1). A change outside svx (gtk3 popup sizing in
   `vcl/unx/gtk3/gtkinst.cxx`) is allowed only if a probe shows the gtk3 popup opening at the wrong size, with that
   probe as its test.

## Tasks

- [x] **D1 — design** (delegated, read-only explorer/architect; mapping trigger: shared svx control across four apps,
  needs far more than the inline evidence budget): every refill trigger and caller, where style-pool change hints
  come from per app, how `StylesPreviewWindow` avoids refills, the lazy-fill option against gtk3 combo behavior, the
  test plan (RED first), risks. Controller rules on the design. Done: ruling 6, L4.
- [x] **I1 — implementation** (delegated writer, opus; context reason: svx/sc builds, tests and measurements): the
  ruled design, test first, `svx` build, before/after measurement with the P1 harness. Commits e046627af (guards),
  f6b15801e (change + RED tests). L6.
- [ ] **SB-V1 — independent verification** (delegated verifier; Risk item 6 and item 3: shared code in four apps where a
  stale list would go unnoticed): the whole document, probes from rulings 1-2 against the baseline build.
- [ ] **SB-R1 — blind dual review** (judgment-day: two independent reviewers on the diff; at most one correction round).
- [ ] **SB-F3 — release 0.1.4** (delegated packaging and container proof, as F2 of `icon-accent-fill.md`; controller
  publishes): ruling 5.

## Log

- **L1** (2026-10-29, verbatim) "hace un analisis del rendimiento de libre office. Abriendo archivos medianos. Se traba
  muchisimo."
- **L2** (2026-10-29, verbatim) "Si, me encantaria que apliques esto. Es nuestro primer cambio heavy de codigo de libre
  office. Asi que procuremos usar las mejores metodologias de ingenieria y revision con subagentes. Usando ODD como
  venimos haciendo"
- L3 (2026-10-29) RDD is off for this clone (clone-local); the user's review request is met with an independent
  verifier (V1) and a blind dual review (R1), not by switching RDD on.
- L4 (2026-10-29) D1 done (delegated, Plan agent, read-only): full map with path:line in the D1 handoff, kept in
  `.superpowers/sdd/2026-10-20-writer-impress-ribbons/task-D1-design.md`. Ruling 6 adopts design B; the user's
  "fix 1 + fix 2" becomes fix 2 widened to focus (same outcome, no stale-list risk).
- L5 (2026-10-29) I1 launched (delegated, opus; brief `task-I1-brief.md`). Name clash: the Impress series already used
  I1 and R1 in the same SDD folder; the old Impress I1 brief was overwritten (uncommitted history, the Impress I1 report
  is kept as `task-I1-impress-report.md`). Later briefs of this feature use the prefix `task-SB-` (V1, R1, F3).
- L6 (2026-10-29) I1 done (delegated, opus): RED Calc 11 entries / Writer 13 where at most 1 expected; GREEN after.
  Guards pass on the old and new library; two mutants (no refill, no clear) each fail a test. Suites: sc_uicalc2 72,
  sw_uibase_uiview 13, sc_tiledrendering 86, sw_tiledrendering 110, notebookbar UITest 1, product 1155 OK. gtk3
  stylebloat.xlsx (median of 3): cursor step 1.23 s / 0.90 s CPU -> 0.35 s (timer) / 0.02-0.03 s; load 3.67 -> 2.36 s;
  to idle 6.20 -> 3.37 s (stock 5.94 -> 3.20 s); medium xlsx/docx/pptx no slower in CPU. The one-off clear (0.08-0.10 s
  at 61k rows) runs in a lowest-priority idle. gtk3 mouse probe: full-height popup with the current style highlighted
  on stylebloat.xlsx and medium.docx, pick applies; `gtkinst.cxx` unchanged. Concerns: opening the drop-down at 61k
  styles costs about 100 s CPU on gtk3 in old and new code (only capping, ruling 4, would fix it); Calc crashes at
  close after renaming a used cell style through the API, old code too. Keyboard, `gen`, Impress/Draw and
  accessibility left to SB-V1. Controller spot check: `CppunitTest_sw_uibase_uiview` rerun OK; popup screenshot
  looked at; assess `high` via item 6, RDD off.
