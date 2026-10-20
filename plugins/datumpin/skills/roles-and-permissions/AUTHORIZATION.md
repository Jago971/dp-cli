# Authorization (per app)

Parent: [SKILL.md](SKILL.md).

- **A separate `roles`/`grants` table:** `(id, user_id, role_name, scope_type, scope_id, granted_by, granted_at)`. `scope_type` and `scope_id` let one user hold different roles at different resources (admin at one site, nothing at another). A DB CHECK allows at most one scope dimension set per row, and all-NULL means a global role.
- **A broader grant satisfies a narrower check** by cascading through the resource's own parent lookup (an org-level role implies its sites), with one row per grant.
- **`role_name` is a small closed vocabulary** (a CHECK-constrained string for one app). It becomes a real `role → permission` join when more than one app needs to share or extend the same permission vocabulary.
- **Authorize through `Depends` factories.** A base `get_current_user` dependency, plus `require_role(*names)` / `require_permission(*names)` closures that return a `Depends`-able callable and read any resource id from the route's path parameters:

  ```python
  def require_role(*names: str):
      def check(
          user: User = Depends(get_current_user),
          site_id: UUID = Path(...),
      ) -> User:
          if not user_has_site_role(user, site_id, *names):
              raise HTTPException(403)
          return user
      return check

  @router.post("/sites/{site_id}/approve")
  def approve(user: User = Depends(require_role("admin", "staff"))): ...
  ```

  The rule sits in the function signature, is unit-testable outside the request cycle, and composes per route.
- **Check live.** Re-derive role and permission state from the database on every call, so a revoked role takes effect on the next request. Tokens and request-scoped caches hold identity only.
- **Review and approval workflows:** model the resource lifecycle as an explicit status column (`building → pending → approved`) and gate the *transition into approved* behind a role check. Everything before that stays open to anyone with base access.

## Done when

- A test shows a revoked role takes effect on the next request.
- Inserting a grants row with both `scope_type` and `scope_id` set fails.
- Every role check is a `Depends` factory in a route signature, with no role check in middleware.
