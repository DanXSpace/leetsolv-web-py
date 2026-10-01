# Reimplement leetsolv's scheduler in Python

leetsolv-web replaces the leetsolv CLI, and its scheduling must take exactly from the leetsolv algorithm. We port leetsolv's Go SM-2 variant to Python — keeping the deterministic parts bit-for-bit identical and the random interval jitter distribution-equivalent — rather than shelling out to the Go binary or adopting an off-the-shelf SM-2 library.

## Considered options

- **Shell out to the Go binary** (subprocess per review): rejected — couples a web request to a local process and makes the hosted backend depend on a second runtime.
- **Off-the-shelf SM-2 library** (e.g. Anki-style): rejected — leetsolv's variant is custom (importance-weighted base intervals, familiarity/memory ease-factor deltas, priority-score due ordering), so any library diverges from the "exactly" requirement.
- **Port to Python**: chosen — identical deterministic behavior, native to the FastAPI stack, and the single place where the algorithm's constants live.

## Consequences

- The three leetsolv settings (`RandomizeInterval`, `OverduePenalty`, `OverdueLimit`) are ported too and default to leetsolv's values.
- `RandomizeInterval`'s jitter is reproduced as a distribution (`-1..+2` days), not a bit-identical sequence, since Go's `math/rand/v2` stream isn't reproducible from Python.
