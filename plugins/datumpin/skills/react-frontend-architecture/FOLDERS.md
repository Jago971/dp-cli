# Folder vocabulary

Parent: [SKILL.md](SKILL.md). Every frontend uses these folder names for these roles, taken from AHJV2's per-folder READMEs (`frontend/src/<folder>/README.md`).

| Folder | Role |
|---|---|
| `views/` | Route-mounted top-level components: whatever a `<Route element={...}>` renders. The folder marks "this is a page", and the name describes what it shows (`DocumentView`, `Picker`). |
| `layouts/` | The persistent nav and chrome shell wrapping every route (`AppLayout.jsx`), composed once above `<Routes>`. |
| `chrome/` | Cross-cutting working-experience UI that is never persisted and never route-specific: toolbars, modals, feedback banners. Composed into a view. |
| `panels/` | Editing panels composed into one view (settings sections within a page). |
| `drawers/` | A generic slide-out drawer shell plus specific drawers (export, publish, selection). |
| `instances/` | Pickers and insertion flows for choosing an existing instance of something to insert. |
| `blocks/` | Reusable, purely presentational domain content components, one subfolder per block type. They hold content, with no knowledge of the surrounding chrome or panels. |
| `primitives/` | App-agnostic, dependency-free UI atoms (`Button.jsx`, a generic overlay or menu), copy-pasteable into any frontend. |
| `vendor/` | Thin wrappers isolating a third-party library, imported only by the wrapper's own consumers (see [DATA-WIDGETS.md](DATA-WIDGETS.md), role 4). |
| `hooks/` | `data/` (fetch hooks, framework-agnostic) and `editor/` (hooks tied to editor or page state). Keep the two apart. |
| `api/` | One flat fetch-function module. |

A new frontend creates a folder when a component needs that role (curator has no `panels/`, `drawers/`, `instances/`, `blocks/` or `vendor/` yet). A role that fits none of these gets a new folder with a README explaining the gap, as AHJV2's `views/README.md` points to its own `VIEWS.md`.

## Done when

- Every new component sits in the folder matching its role.
- Every folder you added has a README.
