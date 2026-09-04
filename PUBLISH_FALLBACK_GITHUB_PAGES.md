# Publish Fallback — GitHub Pages (Option 2, NOT ACTIVE)

**Status:** Documented, not enabled. Decision on 2026-09-04: stay with the Claude Artifact
as the daily deliverable (Option 1). This runbook exists so Option 2 can be switched on in
~10 minutes if the Artifact publish becomes unreliable again.

---

## Why this exists

The daily report is published by updating one Claude Artifact in place:

```
https://claude.ai/code/artifact/44d3813a-980b-4964-a58e-53e52744bb21
```

Every scheduled run is a brand-new session that has never seen that Artifact, so the
`Artifact` tool's stale-version guard requires the run to `WebFetch` the live URL and
`Read` the saved file in full before it may overwrite. Most days that works with **zero
human input** (e.g. 2026-09-04, report #70, published first try). On some days the guard
glitches and keeps refusing even after a correct fetch+read (2026-08-25, 2026-08-26). The
only way past a glitched guard is `force:true`, and `force:true` requires a live human's
explicit "yes" — that is the "approve" prompt the user sees on bad days.

**There is no setting that removes this.** Verified 2026-09-04:

| Lever | State | Result |
|---|---|---|
| `.claude/settings.json` | `defaultMode: bypassPermissions` + `allow: ["Artifact"]` | Already maxed; no stronger repo-level setting exists |
| Routine → Connectors tab | CoinDesk / Crypto.com / FMP set to not-ask | Only governs MCP connectors, not Artifact |
| Routine → Behavior tab | Only "Auto-fix pull requests" toggle | No permission/approval setting exists here |
| Routine → Notifications tab | Push + email | Unrelated |

The guard is a conflict-protection check, not a permission, so it cannot be "always
allowed." The only way to get a **guaranteed** no-approval publish is to not depend on
the `Artifact` tool: commit the rendered HTML to this repo and let GitHub Pages serve it.

---

## Design

```
report HTML (built each run, same file used for the Artifact)
   │
   ├─▶ docs/index.html                 ← "latest" — overwritten every run
   ├─▶ docs/reports/YYYY-MM-DD.html    ← archive — one new file per run
   └─▶ docs/reports/index.json         ← archive manifest (date, report #, headline)
                                          (optional; lets docs/index.html or a tiny
                                           archive page list prior reports)

GitHub Pages (source: main branch, /docs folder)
   └─▶ https://mrmclaude1.github.io/Daily-Market-Intelligence-Report/
         └─ /reports/2026-09-04.html  etc.
```

- Writes go through the **GitHub MCP `create_or_update_file` tool** — the same path the
  cache push already uses. `git push` and `curl -X PUT` are both proxy-blocked from the
  container (see `CLAUDE.md` → End-of-Run Protocol), so MCP is the only write path.
- Nothing about the report generation changes. The HTML file that would be sent to the
  `Artifact` tool is simply also committed.
- The Artifact step can stay in the pipeline (best-effort) or be removed. If it stays and
  glitches, the run still succeeds because Pages already has today's report.
- A `.nojekyll` file in `docs/` stops GitHub from running Jekyll over the HTML (avoids it
  choking on `{{`/`}}` or underscored paths). Add it once at activation.

**Pages deploy latency:** typically 30–120 s after the commit lands on `main`.

**Privacy note:** GitHub Pages sites on a public repo are public. The Artifact is private
by default. If the repo is private, Pages requires GitHub Pro/Team/Enterprise to serve a
private-repo site. Check this before activating if the report must stay non-public.

---

## Activation checklist

### One-time — user, in the GitHub UI (~2 minutes)

1. Repo → **Settings** → **Pages**.
2. **Source:** "Deploy from a branch".
3. **Branch:** `main`, **Folder:** `/docs` → **Save**.
4. Note the published URL shown on that page (expected:
   `https://mrmclaude1.github.io/Daily-Market-Intelligence-Report/`).

### One-time — agent, in a session (~5 minutes)

Create these files on `main` via `mcp__github__create_or_update_file`:

- `docs/.nojekyll` — empty file.
- `docs/index.html` — seed with the most recent report HTML (or a one-line placeholder;
  the next scheduled run overwrites it).
- `docs/reports/index.json` — seed with `[]`.

Then update `CLAUDE.md`:

- In **Publish procedure**, insert the per-run step below **after** the cache push and
  **before** the Artifact publish (so Pages lands even if the Artifact step stalls).
- Change the Artifact step's stuck-guard guidance from "stop after 3 refusals and notify"
  to "stop after 3 refusals, note it in the notification, and move on — Pages has the
  report."
- Flip the **Status** line at the top of this file to ACTIVE with the date.

### Per-run step to paste into `CLAUDE.md` (the actual pipeline change)

```markdown
### Publish to GitHub Pages (no-approval path) — run after the cache push

Using `mcp__github__create_or_update_file` (owner `mrmclaude1`,
repo `Daily-Market-Intelligence-Report`, branch `main`) — the tool base64-encodes
`content` itself; pass the raw HTML string:

1. `docs/reports/YYYY-MM-DD.html` — NEW file, today's report HTML.
   message: `report: YYYY-MM-DD (#NN)`
   (If it already exists — a re-run the same day — fetch its SHA with
   `mcp__github__get_file_contents` and pass it to overwrite.)

2. `docs/index.html` — OVERWRITE with the same HTML.
   Fetch the current blob SHA with `mcp__github__get_file_contents`
   (ref `refs/heads/main`) immediately before the write; pass it as `sha`.
   message: `pages: latest → YYYY-MM-DD (#NN)`

3. `docs/reports/index.json` — fetch current content + SHA, prepend
   `{"date":"YYYY-MM-DD","report":NN,"headline":"<masthead h1 text>",
     "file":"reports/YYYY-MM-DD.html"}`, write back with `sha`.
   message: `pages: index → YYYY-MM-DD`

A 409 on any write means the SHA went stale — re-fetch and retry once.
Confirm each response's `commit.sha`. Live URL:
https://mrmclaude1.github.io/Daily-Market-Intelligence-Report/
Archive: …/reports/YYYY-MM-DD.html
```

### Optional polish (not required to activate)

- Add a small `docs/archive.html` that fetches `reports/index.json` and lists prior
  reports with headlines. Keep it inline-CSS, no external hosts (mirrors the Artifact's
  CSP posture; Pages has no such restriction, but consistency keeps the template reusable).
- Add a link to the archive in the report footer template (`report_template.html`).

---

## Rollback

Delete the per-run step from `CLAUDE.md`. Nothing else is needed — Pages keeps serving the
last committed `docs/index.html` indefinitely, and the Artifact path is unaffected.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-08-14 | Root-caused the daily "approve artifact" interruption to the Artifact stale-version guard; `WebFetch` before publish fixed the common case. |
| 2026-08-25, 08-26 | Guard glitched two days running; `force:true` with live user "yes" was the only fix. Suggested a static-hosting fallback in `CLAUDE.md`. |
| 2026-09-04 | Report #70 published cleanly first try. Confirmed no settings/UI lever exists for the guard. **User chose Option 1 (keep Artifact) for now; this runbook written so Option 2 is a quick switch later.** |
