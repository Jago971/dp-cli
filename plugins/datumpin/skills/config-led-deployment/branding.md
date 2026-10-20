# Branding: files, with no fallback identity

For frontend apps (AHJ, curator). BDS has none. Parent: [SKILL.md](SKILL.md).

- **One `theme.css` holds every theme decision** as a normalised, neutral token set (`--color-*`, `--font-body`, `--radius`, `--shadow`, `--series-N` for chart colours), with no package-scoped names. Packages and the host each pick the tokens they need and document them. A missing required token stops startup.
- **Logos have no fixed file names.** `instance.json`'s optional `assets` block assigns a file in `branding/` to each role: `{"assets": {"logo_banner": "<file>", "logo_chart": "<file>"}}`.
  - A role left out means no logo, and never falls back to a default name, the other role or another brand's.
  - Both roles may name one file.
  - A named file that is missing stops startup.
- **The browser reads the assignment from the host's backend.** It cannot read `instance.json`, so the backend serves `GET /branding/assets` (the browser URL may carry a proxy prefix such as `/api`), returning only the roles the instance assigns. The theme loader fetches that list.
- **Delivery is a mount.** The instance's `branding/` folder, and only that subfolder, mounts read-only into the frontend and is served as static files the app loads at startup. A branding change needs no rebuild, and nothing is baked into the image.
- **A product with no real visual identity yet** copies an existing neutral option as a deliberate placeholder, confirmed against that product's actual history, with real assets listed as future work.

## Done when

- Removing a required token from `theme.css` stops startup with a message naming the token.
- An instance with no `assets` block shows no logo, and a named missing file stops startup.
- `docker exec <frontend> ls /<served path>` shows the instance's own `branding/` files, and the image holds none.
