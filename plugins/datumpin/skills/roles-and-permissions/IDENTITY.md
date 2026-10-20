# Identity (central auth service)

Parent: [SKILL.md](SKILL.md).

- **`users` holds identity and lifecycle only:** id, email, password hash, `is_active`, `email_verified_at`, `frozen_at` or similar. Roles and permissions belong to each app, so the user row stays free of them.
- **Passwords:** bcrypt or argon2id through `passlib` (or `argon2-cffi`). A malformed hash fails closed (deny, not a 500).
- **Session tokens are opaque, high-entropy and server-side** (`secrets.token_urlsafe(32)`). The database stores a SHA-256 hash of the token, and the raw token exists only in the client's cookie or header.
- **Ephemeral tokens** (email verification, password reset, invite links) share one small table, distinguished by a `purpose` enum plus `used_at` and `expires_at`.
- **Auth endpoints** (register, login, forgot-password) return the same response whether or not the email exists, and are rate-limited per route (`slowapi`). Rate limiting is the abuse control, since account lockout is itself a DoS vector.
- **Service-to-service calls use their own lane:** an API key or client-credentials-style credential, issued and revocable independently of human logins. Every pairing (curator's backend calling its paired `api` instance) uses it.
- **CSRF:** cookies cross origin and subdomain boundaries in a multi-service fleet, so state-changing routes use a real CSRF token (double-submit or synchronizer pattern). `SameSite=Lax` alone is not enough.

## Done when

- `grep -in "role\|permission"` on the users model finds nothing.
- A test shows the same login-failure response for a known and an unknown email.
- A test asserts the stored token value is a 64-character hex SHA-256.
