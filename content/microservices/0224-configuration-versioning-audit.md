---
card: microservices
gi: 224
slug: configuration-versioning-audit
title: "Configuration versioning & audit"
---

## 1. What it is

Configuration versioning and audit means every configuration value carries an identifiable version, and every change to it is recorded with enough detail (who, what, when, why) to answer, after the fact, exactly what configuration a service was running at any given point in time, and what changed between two points.

## 2. Why & when

[Configuration as code](0221-configuration-as-code.md) provides history through Git when configuration lives in a repository, but not every configuration path goes through Git directly — a value pushed dynamically through [runtime refresh](0223-dynamic-runtime-configuration-refresh.md), or one stored in a database-backed [config backend](0233-config-backends-git-vault-jdbc-redis-filesystem.md), needs its own explicit versioning and audit trail to retain the same guarantees. Without this, diagnosing an incident that traces back to "someone changed a config value" becomes guesswork — there's no way to confirm what the value actually was at the time of the incident, or who changed it and when.

Version and audit configuration wherever incident diagnosis, compliance, or rollback correctness depends on knowing a value's exact history — which is nearly always true in a production system managed by more than one person. A single-developer local prototype with no compliance requirement can reasonably skip formal audit trails.

## 3. Core concept

Versioning attaches an incrementing identifier to each distinct state of a configuration value, and an audit log records, for every transition between versions, the actor, timestamp, and reason — together these let any past state be identified precisely and any change be attributed and explained.

```java
record ConfigVersion(int version, String value, String changedBy, Instant changedAt, String reason) {}

// EVERY change appends a new, immutable ConfigVersion -- past entries are NEVER overwritten
List<ConfigVersion> history = new ArrayList<>();
history.add(new ConfigVersion(1, "3000", "alice", Instant.now(), "initial value"));
history.add(new ConfigVersion(2, "5000", "bob", Instant.now(), "tuning under load"));
// "what was the timeout at version 1?" and "who changed it to 5000, and why?" are BOTH answerable
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A configuration value's history is a sequence of immutable, timestamped versions, each recording the actor and reason for that change, letting any past state be reconstructed and any change be attributed" >
  <rect x="20" y="55" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">v1: 3000</text>
  <text x="85" y="90" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">alice, initial</text>

  <rect x="255" y="55" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">v2: 5000</text>
  <text x="320" y="90" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">bob, tuning</text>

  <rect x="490" y="55" width="130" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">v3: 8000 (current)</text>
  <text x="555" y="90" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">carol, incident response</text>

  <line x1="150" y1="77" x2="253" y2="77" stroke="#8b949e" marker-end="url(#arr224)"/>
  <line x1="385" y1="77" x2="488" y2="77" stroke="#8b949e" marker-end="url(#arr224)"/>

  <defs>
    <marker id="arr224" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each version is immutable and attributed; the full chain answers both "what was it then" and "who changed it, and why."

## 5. Runnable example

Scenario: a configuration value that starts with only its current state visible (no way to answer "what was it an hour ago"), is refactored to record every version with full audit metadata, and finally adds a point-in-time reconstruction query that answers "what value was active at a given timestamp" — the exact question an incident investigation needs answered.

### Level 1 — Basic

```java
// File: OnlyCurrentStateVisible.java -- only the CURRENT value is kept;
// the moment it changes, the previous state is GONE.
public class OnlyCurrentStateVisible {
    static String timeoutMs = "3000";

    public static void main(String[] args) {
        System.out.println("Current value: " + timeoutMs);
        timeoutMs = "8000"; // overwritten -- "3000" is now UNRECOVERABLE
        System.out.println("Current value: " + timeoutMs);
        System.out.println("What was the value 5 minutes ago? UNANSWERABLE from this program's state.");
    }
}
```

**How to run:** `javac OnlyCurrentStateVisible.java && java OnlyCurrentStateVisible` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FullAuditHistory.java -- EVERY change is recorded as an
// immutable, attributed version -- who, what, when, why.
import java.time.*;
import java.util.*;

public class FullAuditHistory {
    record ConfigVersion(int version, String value, String changedBy, Instant changedAt, String reason) {}

    static List<ConfigVersion> history = new ArrayList<>();

    static void applyChange(String value, String changedBy, String reason) {
        history.add(new ConfigVersion(history.size() + 1, value, changedBy, Instant.now(), reason)); // APPENDED, never overwritten
    }

    public static void main(String[] args) {
        applyChange("3000", "alice", "initial value");
        applyChange("8000", "carol", "incident response -- raise timeout under load");

        System.out.println("Full audit trail:");
        for (ConfigVersion v : history) {
            System.out.println("  v" + v.version() + " = " + v.value() + " (by " + v.changedBy() + ": " + v.reason() + ")");
        }
    }
}
```

**How to run:** `javac FullAuditHistory.java && java FullAuditHistory` (JDK 17+).

Expected output:
```
Full audit trail:
  v1 = 3000 (by alice: initial value)
  v2 = 8000 (by carol: incident response -- raise timeout under load)
```

### Level 3 — Advanced

```java
// File: PointInTimeReconstruction.java -- answers the KEY incident-response
// question: "what value was ACTIVE at a given point in time?" -- using
// only the recorded, timestamped audit history.
import java.time.*;
import java.util.*;

public class PointInTimeReconstruction {
    record ConfigVersion(int version, String value, String changedBy, Instant changedAt, String reason) {}

    static List<ConfigVersion> history = new ArrayList<>();

    static void applyChangeAt(String value, String changedBy, String reason, Instant at) {
        history.add(new ConfigVersion(history.size() + 1, value, changedBy, at, reason));
    }

    // finds the LATEST version whose changedAt is <= the queried timestamp -- that was the ACTIVE value then
    static Optional<ConfigVersion> valueActiveAt(Instant queryTime) {
        return history.stream()
            .filter(v -> !v.changedAt().isAfter(queryTime))
            .max(Comparator.comparing(ConfigVersion::changedAt));
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-07-13T09:00:00Z");
        Instant t1 = Instant.parse("2026-07-13T10:00:00Z");
        Instant t2 = Instant.parse("2026-07-13T14:30:00Z");

        applyChangeAt("3000", "alice", "initial value", t0);
        applyChangeAt("8000", "carol", "incident response", t1);

        // an incident is reported as having occurred at 09:30 -- what was the CONFIG then?
        Instant incidentTime = Instant.parse("2026-07-13T09:30:00Z");
        Optional<ConfigVersion> activeThen = valueActiveAt(incidentTime);
        System.out.println("Value active at incident time (09:30): " + activeThen.map(ConfigVersion::value).orElse("unknown"));

        Optional<ConfigVersion> activeNow = valueActiveAt(t2);
        System.out.println("Value active now (14:30): " + activeNow.map(ConfigVersion::value).orElse("unknown"));
    }
}
```

**How to run:** `javac PointInTimeReconstruction.java && java PointInTimeReconstruction` (JDK 17+).

Expected output:
```
Value active at incident time (09:30): 3000
Value active now (14:30): 8000
```

## 6. Walkthrough

1. **Level 1, no history at all** — `timeoutMs` is a single mutable field; after `timeoutMs = "8000"` executes, the prior value `"3000"` exists nowhere the program can access — any question about a past state is fundamentally unanswerable from this program's own state.
2. **Level 2, appending immutable versions** — `applyChange` never modifies an existing `ConfigVersion` entry; it always constructs a *new* one and appends it to `history`, with `changedBy` and `reason` capturing exactly who made the change and why, alongside an automatically recorded `changedAt` timestamp.
3. **Level 2, the resulting trail** — printing `history` shows both recorded transitions in order, each attributed to its author and reason — a structural improvement over Level 1 even though only the two most recent states happen to be shown here.
4. **Level 3, timestamps as the reconstruction key** — `applyChangeAt` accepts an explicit `Instant` (standing in for `Instant.now()` in a real system, made explicit here for a reproducible example) so each version's exact activation time is recorded precisely.
5. **Level 3, the point-in-time query** — `valueActiveAt` filters `history` to versions whose `changedAt` is at or before the queried timestamp, then picks the one with the *latest* such timestamp — this correctly identifies which version was the "current" one at any earlier moment, not just the most recent version overall.
6. **Level 3, answering the incident-response question** — querying `valueActiveAt(incidentTime)` for `09:30` (after `v1`'s `09:00` change but before `v2`'s `10:00` change) correctly returns `v1`'s value, `"3000"`, even though the *current* value by the time anyone investigates is `"8000"` — this is precisely the question an incident investigation needs answered ("what configuration was actually in effect when the problem occurred?"), and it's only answerable because every version was recorded immutably with its own timestamp rather than being overwritten in place.

## 7. Gotchas & takeaways

> **Gotcha:** an audit trail is only as trustworthy as its tamper-resistance — if the storage holding `history` can itself be edited or truncated by the same actors making configuration changes, the trail can be falsified after the fact; production audit logging typically writes to append-only storage with restricted write access, separate from the systems that consume the configuration values themselves.

- Configuration versioning and audit records every change with an identifiable version, an actor, a timestamp, and a reason, so past states can be reconstructed and changes attributed after the fact.
- This closes a gap that Git-based [configuration as code](0221-configuration-as-code.md) doesn't automatically cover for configuration paths that don't flow through a Git-backed repository, such as dynamically pushed runtime values.
- A point-in-time query — "what value was active at timestamp X" — is only answerable when every past version and its exact activation time were recorded immutably, never overwritten.
- Versioning and audit matter most wherever incident diagnosis, compliance, or rollback correctness depend on knowing a configuration value's exact history, which is nearly always true for a production system with more than one contributor.
- An audit trail's guarantees depend on its storage being tamper-resistant and append-only; a trail that can be edited after the fact by the same actors it's meant to hold accountable isn't a trustworthy audit trail.
