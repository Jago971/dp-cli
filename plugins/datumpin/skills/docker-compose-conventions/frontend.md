# Frontend serve stage

A prod frontend image serves the built app from nginx, and one image serves every instance: nothing instance-specific is baked in. The app calls a relative `/api`, and nginx proxies it to the backend the instance names.

```dockerfile
FROM node:20.20-slim AS builder
...
FROM nginxinc/nginx-unprivileged:1.31-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 3000
```

- **Image:** `nginxinc/nginx-unprivileged` runs as its own non-root user, so the Dockerfile adds no `USER` and no ownership entrypoint.
- **Config:** `frontend/default.conf.template` sets `listen 3000;` (the image's default is 8080). nginx's own entrypoint fills `${VAR}`s from the environment when the container starts and leaves nginx's `$uri`-style variables alone. It holds:
  - the SPA fallback, `try_files $uri $uri/ /index.html`;
  - `location /api/ { proxy_pass http://${<APP>_BACKEND_SERVICE}:8000/; }`, where the trailing slash strips `/api`, matching the dev server's proxy;
  - any other backend path the app loads, such as `/static/`, proxied with its path kept;
  - `client_max_body_size` on `/api/` when uploads go through it. nginx refuses bodies over 1 MB by default, and the dev proxy has no limit, so this shows only in prod.
- **Compose:** the frontend keeps the image's own entrypoint and command, because nginx's template step runs there. The backend's service name comes from the instance env file, the frontend shares the backend's network (both in `config-led-deployment`), and branding is mounted as `config-led-deployment/branding.md` describes.
- **SBOM:** the builder stage writes `/sbom.json` with `@cyclonedx/cyclonedx-npm` and the serve stage copies it; it stays in the image (SKILL.md, SBOM).
- **Check:** a frontend image can have a smoke test (`gitea-workflows`, Images) that starts it beside a stub backend and requests `/`, a deep link, `/api` and the branding.
