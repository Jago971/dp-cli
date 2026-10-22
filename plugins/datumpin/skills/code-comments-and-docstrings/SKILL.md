---
name: code-comments-and-docstrings
description: Comments in source files (py/js/ts) - why-only comments, file headers, Summary/Input/Output docstrings. Use before writing or editing a comment or docstring.
---

# Code comments and docstrings

## File header

Every source file opens with 1-3 sentences: what the file is for, plus a link to the doc that covers it when it solves a specific real problem. A file that enforces an architectural boundary says so ("only this file may import httpx"). A folder README that already covers the file's role can be the pointer.

## Function docstrings: Summary / Input / Process / Output / Raises

Include only the sections that have something to say:

- **Summary**: one or two sentences, what this does and why it exists.
- **Input**: non-obvious parameters (units, valid ranges, what `None` means).
- **Process**: genuinely non-linear logic.
- **Output**: the returned shape or meaning, where the return type alone does not say.
- **Raises**: exceptions that propagate, and when.

```python
def find_active_addressing(source, tier, task, version=None):
    """Find the addressing on this Source's SourceBuild matching tier + task,
    that extraction is allowed to serve.

    Only 'approved' addressings are ever eligible. Multiple approved
    versions of the same (tier, task) can coexist; version pins to one
    exactly, omitted resolves the highest version.

    Raises: AddressingNotFoundError if no approved match exists.
    """
```

A trivial getter or private helper has no docstring.

## Inline comments: why

The default is no inline comment. Write one for a hidden constraint, a subtle invariant, a workaround or surprising dependency behaviour. **Test:** if removing the comment would not confuse a future reader, leave it out.

```python
# binary_extractor_lw's get_int defaults to bit_width=16/signed=True when
# these are omitted — silently misdecoding any dtype that isn't actually
# 16-bit signed. Pass the real dtype through explicitly.
```

A hard algorithm gets a numbered walkthrough above the block, proportional to its complexity.

## Where each kind of information goes

- Tickets and PRs: the commit message.
- Authorship and dates: `git blame`.
- History: the CHANGELOG or decision log.
- Doc content: a link, with the comment standing on its own first. Cite a stable `docs/reference/...` path.
- A convention two files enforce: each comment names its sibling file.

## Region markers

`#region` / `#endregion` group the distinct structural sections of a long file, so an IDE folds them and a reader jumps between them.

```python
# region ---------------------------------------------------------------- Loaders
...
# endregion ---------------------------------------------------------------------------
```

```js
// #region ---------------------------------------------------------------- Handlers
...
// #endregion ---------------------------------------------------------------------------
```

- Keep the dash rule and a short Title Case label naming the section's role ("Dispatch tables", "Mutations").
- One region groups several functions (a service module with Loaders, Transformers and Dispatch tables).
- At five or more regions, split the file into modules.
- Short single-purpose files stay unmarked.
- Test files group tests with a plain banner, no fold keywords: `# --- create_addressing ---`.

## Done when

- Every file opens with a header, and boundary files state the boundary.
- Every inline comment passes the removal test.
- No comment cites a ticket, a date or a line number.
- Every `#region` has a matching `#endregion`, and no file has five or more.
