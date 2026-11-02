---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Output follows `formats`, including its Quiet steps rule.

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save it as `.factory/handoff-<YYYY-MM-DD>.md` in the repo the next session starts in, so that session finds it; when the session spanned several repos and that is unclear, ask. Add `.factory/` to that repo's `.gitignore` if it is missing.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, decision-log entries, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

The document's "Next" section never tells the chat to start or build a ticket: the person starts work in `dp guide`, so it lists what is open and leaves the choice to them. A chat that reads a handoff tells the user to run `dp guide`; it does not start the ticket itself.

End by printing the Handover block (`formats`) in a code block, so markdown cannot change it. It shows the repo-relative path with forward slashes (a backslash is lost to markdown), a prompt that tells the user to run `dp guide` in dp-cli with the recommended ticket and step and names the document by that path, and the steps still open for the human.
