---
template: session_heartbeat
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
schema_version: "3.0"
schema: A18
purpose: "Heartbeat section to paste INTO memory/sessions/session_state.md every ~30 min per MEMORY_PROTOCOL §4.4"
template_type: section-insert (NOT standalone document; paste this block into session_state.md)
---

## 🔵 Heartbeat {{date}} {{time}} — {{slice_name}}

**Status:** _One-line state of play (e.g., "Building LLMLingua installer Skill; 3 of 5 files done")_

### Current task
- **Task name:** _What's being worked on right now_
- **Sub-step:** _Specific phase within the task (e.g., "writing SKILL.md")_
- **File(s) being modified:** _Path + line numbers if applicable_
- **Specific blocker (if any):** _Why I'm stuck, what I need_

### Decisions in progress
- _Any TENTATIVE decisions being weighed; cite DEC-### if already drafted_

### Recent completed (this slice)
- _Bullet list of what just shipped_

### Next up (post-this-task)
- _Bullet list of immediate next pieces_

### Files mirrored (D ↔ C) since last heartbeat
- _List of files changed and parity status; "n/n at byte parity" if all clean_

### Open threads (don't lose these)
- _Items that need resolution but aren't the current task_

---

> **Template author note (DELETE before saving):**
> Per MEMORY_PROTOCOL §4.4 heartbeat protocol: update `session_state.md` every ~30 min of active work (or before any `/compact` invocation). Prevents context loss if session ends unexpectedly (laptop lid close, browser crash, mid-task compaction).
>
> **Compaction safety per §15:**
> After compaction, the next session reads this heartbeat first. Be SPECIFIC — vague heartbeats are useless after context loss. Say exactly what file, function, line, issue.
