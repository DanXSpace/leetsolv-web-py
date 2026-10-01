# leetsolv-web

A personal web app that replaces the leetsolv CLI: it logs LeetCode problems, schedules spaced-repetition reviews with leetsolv's exact algorithm, syncs across devices through a hosted backend, and gives a mentor a read-only view.

## Language

**Problem**:
A LeetCode DSA problem the user tracks, identified by a normalized LeetCode URL, carrying a note and review state.
_Avoid_: Question, item, card, task

**Log**:
To record a problem's outcome after attempting it — its note, familiarity, importance, and (when applicable) memory. Logging a never-before-seen problem adds it; logging an existing one is a review.
_Avoid_: Track, upsert, check-in

**Review**:
Logging a problem that was already logged; this reschedules its next review.
_Avoid_: Repeat, redo, retry

**Familiarity**:
A 1–5 self-rating of how the latest attempt went (Struggled → Fluent). Distinct from the problem's own LeetCode difficulty.
_Avoid_: Difficulty, mastery, confidence

**Importance**:
A 1–4 rating of how important the problem is to retain.
_Avoid_: Priority, severity

**Memory**:
Whether the solve relied on memory rather than reasoning (Reasoned / Partial / Full). Only recorded when familiarity is 3 or higher.
_Avoid_: Recall, retention

**Due**:
A problem whose next review date is today or earlier.
_Avoid_: Overdue, pending

**Upcoming**:
A problem whose next review date is tomorrow.
_Avoid_: Soon, scheduled

**Mentor view**:
A read-only mode of the app reached by a share link; it can see problems, notes, and progress but cannot change anything.
_Avoid_: Observer, dashboard, admin
