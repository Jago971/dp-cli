---
name: roles-and-permissions
description: Accounts, sessions, roles or permission checks in a Datumpin service. Identity lives in the central auth service, roles and grants live per app.
---

# Roles and permissions

Two pieces, built in separate places:

| Piece | Owner | File |
|---|---|---|
| **Identity** (who is this): accounts, sessions, tokens | the central auth service | [IDENTITY.md](IDENTITY.md) |
| **Authorization** (what can they do in this app): roles, grants, checks | each app (curator, AHJV2, ...) | [AUTHORIZATION.md](AUTHORIZATION.md) |

The repo you are in decides which piece you build. A repo builds one of them.

- The central service answers "who", and every app answers "what can they do here". An app's role vocabulary stays inside that app.
- Human sessions use an opaque, DB-checked token, which gives instant revocation with no blocklist for one lookup per request. JWTs are reserved for the service-to-service lane, where statelessness across services pays off.
- Each app owns its roles table (curator's consultant/approver roles differ from AHJV2's document-workflow roles). The apps share the pattern in AUTHORIZATION.md.

## Done when

- The `users` table has no role or permission column.
- A revoked role takes effect on the next request (test).
- Stored tokens are 64-hex SHA-256 hashes (test).
- A grants row with both `scope_type` and `scope_id` set fails the CHECK (test).
