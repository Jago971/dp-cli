# Data-driven widgets

Parent: [SKILL.md](SKILL.md). A component that fetches, transforms and renders external data (AHJV2's `DataStack` and `DataTable`) splits into four independently reusable and testable roles:

1. **Fetch hook** (`hooks/data/useX.js`): owns the network call and the loading and error state, with no knowledge of the page or editor using it.
2. **Generic intermediate shape:** the hook outputs plain, library-agnostic data (rows, a pivoted map), shaped for no chart library.
3. **Package adapter:** turns the generic shape into one vendor library's props (Plotly figure props, TanStack Table column defs).
4. **Vendor wrapper** (`vendor/PlotlyChart.jsx`): a thin component around the third-party library, taking only that library's props.

The component consumers import (`DataStack.jsx`) composes the four and holds no fetch or transform logic. The same fetch hook then backs both a chart and a table of the same data, and another frontend reuses the fetch and transform layers through a shared package without AHJV2's chrome.

## Neutral spec, adapters in the view package

In PACKAGES' modular set, the backend builds a **neutral spec** (a table spec, a chart spec: no library names, no colours, only palette indexes) as the wire format. A JS view package (`chart-view`, `table-view`) holds the adapters, one per library, chosen by name from a registry, so changing the library leaves the backend alone.

- Zoom, y ranges and hidden series are view state owned by the host, outside the spec, so a refetch or save cannot reset them and zooming does not refetch.
- The fetch hook comes from `@datumpin/fetch-layer` (it cancels and keeps the last good data).
- Host-only targets (Word, Tiptap) stay in the host.

## Done when

- A component importing a vendor library is under `vendor/`, and nothing else imports that library.
- The fetch hook runs in a test with no chart or table component mounted.
- Changing a chart library touches an adapter and a wrapper only.
