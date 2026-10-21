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

End by printing the Handover block (`formats`): the document's absolute path, the first prompt to paste into the new session (naming the document and the next flow step), and the steps still open for the human.
