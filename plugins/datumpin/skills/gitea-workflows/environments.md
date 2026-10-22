# Environments and branches

Where work runs, and the branches that carry it. Parent: [SKILL.md](SKILL.md).

## Environments

Work moves dev → prep → prod, and only through PRs and images. This table is the one place that names them; the other skills link here.

| Environment | Host | Branch | Image | Compose | Env file |
|---|---|---|---|---|---|
| dev | The laptop, Docker Desktop | A ticket branch | Built locally from `Dockerfile.dev`, tagged `:dev` | `docker-compose.dev.yml` | `.env.<app>-<instance>.dev` |
| prep | Hammond, internal staging | `prep` | `:prep`, pulled | `docker-compose.yml`, `CHANNEL=prep` | `.env.<app>-<instance>` on the host |
| prod | External server, not built yet | `main`, tag `vX.Y.Z` | `:X.Y.Z`, pulled | `docker-compose.yml`, `CHANNEL=prod` | `.env.<app>-<instance>` on the host |

- Everything runs in containers. A host holds Docker, git and its env files; the laptop also holds the agent tooling (Claude Code, `tea`, the plugin's `dp` through pipx, and the Python that the plugin's status hook, `hooks/hooks.json`, runs), the one exemption.
- Builds and tests run in dev before the push, and CI runs them again. Servers pull images; they never build or run tests.

## Branch model and protection

| Branch | Role | Protection |
|---|---|---|
| `prot/<topic>` | Exploratory spikes, in dev | None |
| `prep` | Default branch and trunk; deployed to prep | Standard rule |
| `main` | Customer release | Standard rule; only the Owners team merges |
| `<type>/<issue>-<slug>` | One ticket, short-lived | None |

The standard rule, applied under the repo owner's own login (an admin action): `tea api --login <owner> repos/R/branch_protections -X POST -d @rule.json`, and `-X PATCH` on `repos/R/branch_protections/<rule_name>` to change it. With it, the repo deletes a PR's branch when the PR merges: `tea api --login <owner> repos/R -X PATCH -d '{"default_delete_branch_after_merge":true}'`.

```json
{
  "rule_name": "prep",
  "enable_push": false,
  "enable_force_push": false,
  "required_approvals": 1,
  "dismiss_stale_approvals": true,
  "block_on_rejected_reviews": true,
  "block_admin_merge_override": false,
  "enable_status_check": false,
  "status_check_contexts": []
}
```

`main` takes the same rule with `"rule_name": "main"`, `"enable_merge_whitelist": true` and `"merge_whitelist_teams": ["Owners"]`.

- One approval means every agent PR needs a human's approval before it merges. A repo admin can override the approval on their own PR.
- Required checks: `"enable_status_check": true` with `"status_check_contexts": ["CI / *"]`, which requires every job of the repo's `ci.yml` (Gitea matches the pattern against `CI / <job> (pull_request)`). A repo with its own test workflow adds it (PACKAGES: `"Test Suite / *"`).
- A repo whose work still lands directly on `main` takes the rule at onboarding, after its work moves to `prep`.
