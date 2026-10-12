# Stage A spike findings

Each section records the question, what was tried, the observed result and the decision.
Spec: /home/nh/office-boost/docs/superpowers/specs/2026-10-12-calc-home-redesign-design.md §6.

## 0a Declarative dropdown menus

## 0b Theme engine reach under gtk3

## 0c Custom scheme switching with the system

## 0d Runtime packaging (icon zip drop-in, configuration-only extension)

## 0e UITest access to notebookbar widgets

Question: can a UITest reach widgets of a notebookbar by id after `.uno:ToolbarMode`?

Tried: switch with `.uno:ToolbarMode?Mode:string=notebookbar_office.ui`, then
`getTopFocusWindow().getChild("phbHome")` and check state `Visible`.

Result: YES.
- Before the variant existed (RED): `getChild("phbHome")` raised "Could not find child
  with id: phbHome" (children listed were only the sidebar/grid/input bar), so no
  fallback notebookbar was loaded and the test was not a false pass.
- After adding the variant (GREEN): `notebookbarOffice.NotebookbarOffice.test_office_variant_loads`
  PASS and `test_switch_back_to_compact` PASS (`NewDocSection`, unique to
  notebookbar_compact.ui, is reachable after switching back).

Decision: later tasks may assert notebookbar content through `getChild` by widget id.
Note: on failure, the UITest log ends with an unrelated Python 3.14 traceback-cleaning
error from UNO exceptions; the real cause is the `Could not find child` line above it.
