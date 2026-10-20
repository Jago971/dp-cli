# Loading states, per-item walks, toolchain

Parent: [SKILL.md](SKILL.md).

## Page loading: a skeleton

Page-level loading is a pulsing skeleton shaped like a page (a title bar and 8 row bars), so the real content replaces it without the layout jumping. Curator has `PageSkeleton` in `components/PageShell.jsx`, and AHJ has `chrome/PageSkeleton.jsx` (used by `DocumentView` and `Picker`). A new host copies the component and its CSS.

- The wrapper carries `role="status"`, `aria-busy="true"` and `aria-label="Loading"`.
- Colours come from theme tokens (`var(--color-border)`, `var(--radius-lg)`).
- The pulse switches off under `@media (prefers-reduced-motion: reduce)`.
- Top spacing is the global `mt-24` utility on the `container` wrapper (`className={`container mt-24 ${styles.skeleton}`}`). The `container` class's `margin: 0 auto` shorthand overrides a `margin-top` in the module.
- Error ("This page couldn't be loaded.") and empty ("No items match the current filters.") states, and small inline loading text (a button label, a select's placeholder option), stay plain text.

Done when: a test asserts the status role and `aria-busy="true"` and the absence of `Loading...` text and the page body, and a real browser shows a 24 px gap under the header (or breadcrumb bar).

## Per-item walks

A guided pass over a list (Curator's want/label/supersede walks) keeps explicit per-item state (`unseen`, `skipped`, `submitted`) and changes it only on an explicit Skip or Submit, never because a page opened or a field was prefilled.

- Save per item, with no group save.
- The server computes "what next" from the state, and owns the completeness gate and bulk confirm.
- The UI shows the state as markers and a progress count.

## Toolchain

Every host pins the same Vite, `@vitejs/plugin-react` and vitest versions in `package.json`, exact, with no `^`, so the shared `@datumpin` packages behave identically (read the current values from AHJV2's `package.json`). Node is a minor tag meeting Vite's minimum (`node:20.20-slim`), and npm is 11.x because npm 10 crashes resolving the larger dependency tree. Each host's `vite.config.js` carries the `@datumpin` `.jsx` source pattern. No package-specific `optimizeDeps.include`: fix the package or the toolchain version.

A packaged library needs no browser global (`global`, `process`, `Buffer`) that the bundler leaves undefined. Plotly's source modules did, which blanked both hosts, so use its prebuilt dist.

Done when: every host's `npm ls vite vitest @vitejs/plugin-react` shows the same versions, and the page loads in headless Chromium with no console error after any change to a shared frontend package. Unit tests do not catch the browser-global failure.
