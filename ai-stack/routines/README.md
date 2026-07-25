# Routines

Scheduled work, tuned to an **Oman work week (Sunday–Thursday, UTC+4, no DST)**.

Cron in the Routines API is **UTC** — the expressions below are already converted. Times are
also deliberately off the `:00` and `:30` marks, because every routine on the platform that
asks for "9am" fires at exactly `0 9` and lands on the API in the same instant.

## Live now

These two are created and enabled. They need no connectors, which is why they work
unattended — see the limitation below.

### 1. Weekly AI Stack Digest — Saturdays

`20 4 * * 6` (UTC) = **Saturday 08:20 Oman** · notifications: push + email

Reports what actually changed in the last 7 days across agent skills, Claude Code / Agent SDK,
MCP (including security advisories), RAG, and agent frameworks. Instructed to verify every
claim against a primary source, to cut any item it cannot say changes something for you, and
to end with exactly one recommendation. "A quiet week is a valid finding" is in the prompt on
purpose — a digest that manufactures five items every week is a digest you stop reading.

Saturday because it is the start of the Oman week, so you get it before Sunday planning.

### 2. Skills Fork Upstream Sync Watch — Mondays

`15 5 * * 1` (UTC) = **Monday 09:15 Oman** · notifications: push

Checks whether `aj-omanai/Anthropic-Cybersecurity-Skills` has fallen behind
`mukul975/Anthropic-Cybersecurity-Skills`, and if so summarizes new skills, changed framework
mappings, validator changes, and likely merge conflicts. Reports only — it will not merge,
push, or open a PR.

**Why this exists:** the fork had no `upstream` remote configured at all, so there was no way
to know when it drifted. The routine adds the remote on first run. As of 2026-07-25 the fork
is exactly level with upstream at `673da1f`.

The ideal output is one line: "in sync." The prompt says so explicitly.

---

## Connector limitation — read before adding more

Routines created programmatically from a Claude Code session **cannot carry MCP connectors** on
this org. The API rejects the `connectors` parameter outright, and a routine created without it
fires sessions that have **no `mcp__*` tools at all** — no Gmail, no Calendar, no Todoist, no
HubSpot.

This is why only the two connector-free routines above are live. A Morning Brief was created
and then **deleted**, because without Gmail, Calendar, and Todoist it would have delivered
"I could not access your data" every weekday morning at 07:05 rather than a brief.

**The fix:** create connector-dependent routines from the **claude.ai Routines UI**, where the
connector grant is attached properly. The prompts below are written to be pasted in as-is.

---

## To create in the claude.ai UI

### 3. Morning Brief — Sunday–Thursday, 07:05 Oman

Requires: **Gmail, Google Calendar, Todoist**

> Produce my morning brief for today. I am based in Oman (Asia/Muscat, UTC+4); my work week is Sunday–Thursday.
>
> 1. **Google Calendar** — today's events, plus anything tomorrow that needs preparation today. Flag conflicts, back-to-back blocks with no gap, and any meeting with no agenda or no clear owner.
> 2. **Gmail** — last 24 hours, sorted into (a) needs a reply from me today, (b) waiting on someone else, distinguishing where I am the blocker from where they are, (c) FYI only. Ignore newsletters and automated notifications unless they carry a deadline or an action.
> 3. **Todoist** — due or overdue today. Call out anything overdue more than 3 days; that usually needs rescoping, not rescheduling.
> 4. **Reconcile all three** — name any commitment that appears in email but has no calendar block and no task behind it. That gap is the most useful thing this brief can find.
>
> Lead with the one thing that will go wrong today if I ignore it. Keep it scannable, no filler, and do not restate my calendar back to me verbatim. If a deadline appears to be a court, filing, or client deadline, put it at the very top and state the date explicitly.
>
> Read-and-report only: do not send emails, modify calendar events, or complete tasks.

The step-4 reconciliation is the part that earns the routine. Anyone can list a calendar; the
value is catching the thing you agreed to in email on Tuesday that never became a task.

You also have the `morning` skill enabled, which can set this up conversationally — say
"set up my morning brief as a recurring weekday task." Use one or the other, not both.

### 4. Weekly Close-the-Loop Review — Thursdays, 16:40 Oman

Requires: **Gmail, Google Calendar, Todoist**

> It is the end of my work week (Oman, Sunday–Thursday). Help me close loops rather than summarize activity.
>
> 1. **Dropped threads** — emails from the last 7 days where someone asked me something and I never replied. This is the most important section; put it first.
> 2. **Stalled commitments** — things I said I would do this week, in email or in tasks, that show no evidence of progress.
> 3. **Aging tasks** — anything in Todoist that has been rescheduled more than twice, or is more than 2 weeks overdue. These are not late tasks, they are badly-scoped ones. Say which.
> 4. **Next week's shape** — from the calendar: where the heavy days are, and what needs preparation before Sunday.
>
> Be direct about what slipped. A review that tells me everything went fine is useless. End with the two or three things that genuinely must not slide into next week.
>
> Read-and-report only: do not send emails or modify tasks.

### 5. Client and Matter Deadline Sweep — Sundays, 08:10 Oman

Requires: **Gmail, Google Calendar, Todoist** (add **Google Drive** if matter files live there)

> Scan for hard external deadlines in the coming 14 days — court dates, filing deadlines, hearing dates, client-committed dates, regulatory or contractual deadlines.
>
> Check Gmail, Calendar, and Todoist. For each deadline found, report: the date, what it is, what it depends on, and whether preparation is visibly underway or not started.
>
> Sort by date. Flag separately, at the top, any deadline inside 14 days with **no** corresponding preparation task or calendar block — that combination is the actual risk.
>
> If a date is ambiguous or you are inferring it rather than reading it directly, say so explicitly and quote the source text. Do not guess at a legal deadline.
>
> Read-and-report only.

That last instruction matters. A confidently-stated wrong court date is worse than no routine
at all, so the prompt requires it to show its work whenever it is inferring.

---

## Managing routines

Via this session or any Claude Code session:

- `mcp__Claude_Code_Remote__list_triggers` — includes `trig_` IDs, next run, enabled state
- `mcp__Claude_Code_Remote__update_trigger` — change cron, prompt, or enabled state **in place**,
  preserving run history. Prefer this over delete-and-recreate when only the prompt is wrong.
- `mcp__Claude_Code_Remote__fire_trigger` — run one immediately to test, without waiting for
  its schedule. Do this before trusting a new routine.
- `mcp__Claude_Code_Remote__delete_trigger` — remove entirely

Current IDs:

| Routine | ID |
|---|---|
| Weekly AI Stack Digest | `trig_01FYFPnHbcroJYTcqqTkAq9k` |
| Skills Fork Upstream Sync Watch | `trig_01PnsPNnRkWfF9EiXgzXwU1u` |

## Do not confuse these with CronCreate

Claude Code also exposes `CronCreate`, which looks like the same thing and is not. `CronCreate`
jobs are **session-only, in-memory, and auto-expire after 7 days** — they vanish when the
session ends. Routines (`create_trigger`) are durable and account-level.

For anything you want next month, use Routines.

## Design notes

Four principles behind these prompts, worth keeping if you write more:

1. **Reconcile sources, don't list them.** The value is in the gap between calendar, inbox, and
   task list — not in any one of them.
2. **Permit the empty result.** Every prompt states that "nothing changed" is a valid, useful
   answer. Without that, the model pads.
3. **Read-only unless there is a reason.** None of these send, delete, or modify. An unattended
   routine that writes is a routine that eventually writes something wrong while you are asleep.
4. **Require sourcing on anything consequential.** The deadline sweep must quote its source
   when inferring. Dates drive real obligations.
