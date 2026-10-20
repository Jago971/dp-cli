---
name: react-frontend-architecture
description: React frontends in the Datumpin fleet - CSS Modules, config-driven components, fetch-function API modules, theming, URL filter state. Folder vocabulary, data widgets, and loading states plus toolchain sit in sibling files.
---

# React frontend architecture

The default structure for every frontend (AHJV2, curator, future), so components, API calls and widgets look the same across them.

Branches that load a sibling file:

| When | File |
|---|---|
| Choosing where a new component or hook goes | [FOLDERS.md](FOLDERS.md) |
| Building a chart or table that fetches and transforms data | [DATA-WIDGETS.md](DATA-WIDGETS.md) |
| Page loading states, guided per-item walks, Vite/Node/npm pins | [STATES-AND-TOOLCHAIN.md](STATES-AND-TOOLCHAIN.md) |

## One CSS Module per component

Every `Foo.jsx` has its own `Foo.module.css` beside it. CSS Modules only, with no CSS-in-JS and no per-feature global stylesheet. Global tokens and utilities (`:root` palette, `.card`, `.container`, spacing classes) live in one top-level `index.css`, and component modules reuse them through `composes`:

```css
.card {
  composes: card from global;
  cursor: pointer;
}
```

Component-specific rules (hover, layout) stay local, and changing a token once updates every component. PACKAGES' `docs/reference/design-tokens.md` holds the token-sharing convention.

## Config-driven generic components

When near-identical screens differ only in copy, routes or labels (AHJV2's `Picker.jsx` serves journals, reports, manuals and a publish mode), add a config entry to one component, keyed by the thing that varies:

```jsx
const CONFIG = {
  journal: { heading: "Select a Journal", templateRoute: (id) => `/journal/template/${id}` },
  report:  { heading: "Select a Report",  templateRoute: (id) => `/report/template/${id}` },
};
```

Display-only concerns (a badge label) stay in their own flat lookup, apart from routing and capability concerns (which fields exist, which endpoints to call), because things that look alike today can diverge.

## Fetch-function API modules

`api/backend.js` is a flat module of exported functions over one internal `request()` helper that handles base path, headers and error-body parsing once. Each export is a one-liner, and every caller imports the function it needs:

```js
export function fetchSourcebuilds() {
  return request("/sourcebuilds/");
}
```

A function name greps to every call site.

## Theming: one token file, loaded at startup

The instance supplies `branding/theme.css` of neutral design tokens (`--color-*`, `--chart-*`, `--font-body`, `--radius`, `--shadow`, `--series-N`). `@datumpin/theme`'s `ThemeProvider` loads and validates it at startup, and a missing or incomplete file shows no branded content. Each package documents the tokens it reads, and a host adds its own through `extraTokens`. Logos come from the `assets` block through `GET /branding/assets` (`assetsUrl` on the provider). Components read `var(--color-*)`. Delivery details: `config-led-deployment` (`branding.md`).

## Filter and selection state lives in the URL

On a page where a user filters a list and navigates away and back, keep the selection in the query string (`useSearchParams`). Local state resets on remount, and the URL survives it, including the browser's Back button. Each filter change replaces the history entry, so Back does not step through intermediate filter states.

## Region markers

Large component files fold their sections (Imports, Config, State, Load, Render) with `#region` markers. See `code-comments-and-docstrings`.

## Done when

- `grep -rnE "#[0-9a-fA-F]{3,6}" src --include=*.css` finds a hex colour only in `theme.css`.
- Every `Foo.jsx` has a `Foo.module.css` beside it.
- Each API function is exported from `api/` and calls `request()`.
- The page loads in headless Chromium with no console error.
