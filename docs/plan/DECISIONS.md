# Decision log

Newest at the bottom. Format: `domain-modeling/DECISION-FORMAT.md`.

### A ticket is done when it is tested (2026-10-26)

**Status:** accepted

A ticket closes when it leaves `test` with `Tested OK?` answered yes, and reopens to Backlog on a defect. Before, it closed only when its milestone was released, so Gitea's milestone bar showed 0% while tested work sat in DoD. The bar now counts tested work, and the board still shows a merged ticket in Testing until someone has tried it on prep.

**Considered:** closing on merge to `prep` (`Closes #N`). Rejected because a merged ticket is not yet tried where it runs, so the bar would show untested work as delivered.

**Consequences:** the board columns stay Triage, Backlog, In Progress, Review, Testing, DoD, Done. Testing is open, DoD and Done are closed. The release gate runs once per milestone, when all its tickets are closed: review, worksheet, sign-off. DoD is one `TYPE/DoD` ticket per milestone, carrying the worksheet. Closing it is the sign-off, then the tag. `gitea`, `board`, board-sync, `change-ready`, `formats` and `flows.yaml` follow this, through #59 and #61. Board-sync's merge to Testing is unchanged.
