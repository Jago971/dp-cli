# tea calls

For what `dp` does not cover. Parent: [SKILL.md](SKILL.md).

- Pass `--repo <owner>/<repo>` and `--login` on every call. The slug is the last two path segments of `git remote get-url origin`, `.git` removed: `ssh://git@host:2222/Datumpin/BDS.git` → `Datumpin/BDS`.
- Write as the agent login, `gitea.agent_login` in the flow config (default `squire`). Read as it too.
- For JSON, add `--output json --fields <list>`. Every field comes back as a string; `labels` is space-separated.
- For anything `tea` lacks, use `tea api --login <login> <endpoint>`, with the endpoint written without a leading slash.
- For a multi-line body, write it to a file in the scratchpad and pass `--description-file <file>`.
- In any body or comment, `#N` links an issue or PR in the same repo. Link another repo's as `Owner/Repo#N`, e.g. `Datumpin/WIKI#46`.
- When Gitea is unreachable (connection refused, timeout), print one log line saying so and take the calling flow's fallback.

| Need | Command |
|---|---|
| One issue, with body | `tea api --login L repos/R/issues/N` |
| Its comments | `tea api --login L repos/R/issues/N/comments` |
| Create an issue | `tea issues create --repo R --login L --title T --description-file F --labels "A,B" --milestone M` |
| Assign, other than on In Progress | `tea issues edit N --repo R --login L --add-assignees USER`, with `USER` the Gitea username |
| Move labels | `tea issues edit N --repo R --login L --add-labels "A" --remove-labels "B"` |
| Comment, other than a Pointer | `tea comment N --repo R --login L --description "<text>"` |
| Create a milestone | `tea milestones create --repo R --login L --title T --description D` |
| Set a milestone | `tea issues edit N --repo R --login L --milestone M`, with `M` the full title |
