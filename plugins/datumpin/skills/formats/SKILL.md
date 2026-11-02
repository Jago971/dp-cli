---
name: formats
description: Formats - the fixed shape of everything the plugin prints or writes. Use before printing a workflow message or writing to Gitea or git.
---

# Formats

Everything a flow prints or writes has a shape, so the plugin reads like a CLI tool with code behind it. Use the shape exactly: no preamble, no recap, no sign-off. Conversation outside a shape (a `shape` interview, an answer to a direct question) stays to three lines or fewer.

A flow that prints or writes something new adds its shape here, or to the sibling file the table names, before it writes anything.

| Output | Shape | In |
|---|---|---|
| Any event or result in the terminal | Log line | below |
| A yes/no or choice for the user | Prompt | below |
| The kanban | Board view | [terminal.md](terminal.md) |
| Parked work at session start | Status line | [terminal.md](terminal.md) |
| Drift between code, tickets and plans | Drift report | [terminal.md](terminal.md) |
| Tickets or milestones before pushing | Draft list | [terminal.md](terminal.md) |
| Superseded tickets left for a human to close | To-close list | [terminal.md](terminal.md) |
| The end of a session, for the next one | Handover | [terminal.md](terminal.md) |
| The end of an agent step | Step ending | [terminal.md](terminal.md) |
| A scoping question | Shaping question | [terminal.md](terminal.md) |
| The next choice in a flow | Guide prompt | [terminal.md](terminal.md) |
| An agent step handed to a session | Job prompt | [terminal.md](terminal.md) |
| Gitea issue | Ticket | [gitea.md](gitea.md) |
| Gitea milestone | Milestone | [gitea.md](gitea.md) |
| Gitea comment | Comment (pointer, scope, progress, question) | [gitea.md](gitea.md) |
| Gitea pull request | Pull request | [gitea.md](gitea.md) |
| Git commit / branch | Commit, Branch | [git.md](git.md) |
| Gitea project | Board (one per repo, see `gitea`) | [gitea.md](gitea.md) |

## Quiet steps

While a flow step runs, nothing is printed between tool calls: no "checking…", no plan, no running commentary. The step ends with its output in its shape (log lines, a board, a draft list) and, when a choice follows, one Prompt per question. Reasons and detail wait until the user asks for them. A finding that changes what the user decides goes in the output as a log line, never as prose between calls.
The three-line cap above applies only outside a flow step.

## Terminal

### Log line

`[<flow> <ref>] <event> · <detail> · <detail>`

- `<flow>` is the flow name; `<ref>` is `#N`, `Owner/Repo#N` or a milestone, omitted when there is none.
- One line per event; a run ends with one summary line.
- Outcome words are upper case: `DONE`, `FAILED`, `SKIPPED`, `PASS`, `CHANGES`, `READY`, `BLOCKED`.
- A failure says what failed and the next step: `FAILED · <what> · <next step>`.

```
[board] synced Datumpin/BDS · 61 open · 1 PR
[shape #31] created · Backlog · TYPE/FEATURE · COMPONENT/API · v0.4.0
[shape] FAILED · Gitea unreachable · 2 drafts saved to .factory/outbox/
[shape] DONE · 3 created · 0 failed
```

### Prompt

`? <question> (<option> / <option>)`

```
? Push all 3 tickets? (yes / edit N / drop N)
? Move #44 to In Progress and assign MattM? (yes / no)
```
