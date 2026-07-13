---
card: microservices
gi: 221
slug: configuration-as-code
title: "Configuration as code"
---

## 1. What it is

Configuration as code means storing configuration values in version-controlled, structured files (YAML, properties, JSON) that live alongside the application source or in a dedicated config repository, tracked with the same tools (Git) and processes (pull requests, review, history) used for the application's actual code — rather than in a mutable, unversioned place like a manually edited server file or a dashboard with no audit trail.

## 2. Why & when

Configuration that lives only in a running system's local state — hand-edited on a server, set through a UI with no history — has no record of who changed what, when, or why, and no way to reproduce a past configuration state or roll back a bad change except by remembering (or guessing) what the previous value was. Treating configuration as code brings the same guarantees version control gives application code: every change is a reviewable diff, every prior state is recoverable via `git log`/`git checkout`, and a bad change can be reverted exactly, the same way a bad code change can be.

Store configuration as code whenever it's stable enough to benefit from review and history — most structural and non-secret settings fit this well. It pairs naturally with [centralized configuration servers](0219-centralized-configuration-server.md) like [Spring Cloud Config Server](0231-spring-cloud-config-server.md), which commonly serve configuration directly from a Git-backed [config backend](0233-config-backends-git-vault-jdbc-redis-filesystem.md). Genuinely dynamic, frequently toggled values (like some [feature flags](0225-feature-flags-feature-toggles.md)) may call for a different, more dynamic storage mechanism instead.

## 3. Core concept

Configuration as code represents settings as plain, diffable text files committed to version control, and an application (or a config server sitting between the repository and the application) reads its active configuration from that versioned source rather than from an untracked, out-of-band location.

```java
// application-config.yaml -- committed to Git, reviewable, historied
// order-service:
//   timeout-ms: 3000
//   retry-count: 3

// the APPLICATION reads from the VERSIONED file, not an untracked, hand-edited source
Properties config = new Properties();
try (InputStream in = Files.newInputStream(Path.of("application-config.yaml"))) {
    // parse and load -- this file's entire history is `git log application-config.yaml`
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A configuration file change flows through a pull request and review, gets committed to Git history, and is then what the application reads at startup -- giving every configuration change a reviewable diff and a recoverable history" >
  <rect x="20" y="65" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Config change (diff)</text>

  <rect x="220" y="65" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="285" y="90" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">PR + review</text>

  <rect x="420" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Git history</text>
  <text x="495" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">every state recoverable</text>

  <line x1="150" y1="85" x2="218" y2="85" stroke="#8b949e" marker-end="url(#arr221)"/>
  <line x1="350" y1="85" x2="418" y2="85" stroke="#8b949e" marker-end="url(#arr221)"/>

  <defs>
    <marker id="arr221" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every configuration change becomes a reviewed, versioned commit rather than an untracked, unreviewable edit.

## 5. Runnable example

Scenario: a configuration value that starts as an untracked, in-memory mutation (no record of prior state), is refactored to be a version-tracked change (each update recorded with metadata mirroring a Git commit), and finally demonstrates rolling back to a previous configuration state using that recorded history — exactly what a manually edited, unversioned config file cannot offer.

### Level 1 — Basic

```java
// File: UntrackedMutableConfig.java -- config is mutated DIRECTLY, with
// NO record of what the value was before, or who/why it changed.
public class UntrackedMutableConfig {
    static int timeoutMs = 3000;

    public static void main(String[] args) {
        System.out.println("Current timeout: " + timeoutMs);
        timeoutMs = 5000; // MUTATED directly -- the "3000" is now GONE, no trace
        System.out.println("Updated timeout: " + timeoutMs);
        System.out.println("No record exists of the PREVIOUS value, who changed it, or why.");
    }
}
```

**How to run:** `javac UntrackedMutableConfig.java && java UntrackedMutableConfig` (JDK 17+).

### Level 2 — Intermediate

```java
// File: VersionTrackedConfig.java -- EVERY change is recorded as a
// commit-like entry: old value, new value, author, message -- mirroring
// what a real Git-committed config file's history preserves.
import java.util.*;

public class VersionTrackedConfig {
    record ConfigCommit(int version, String key, String oldValue, String newValue, String author, String message) {}

    static List<ConfigCommit> history = new ArrayList<>();
    static Map<String, String> currentConfig = new HashMap<>(Map.of("timeout.ms", "3000"));

    static void applyChange(String key, String newValue, String author, String message) {
        String oldValue = currentConfig.get(key);
        history.add(new ConfigCommit(history.size() + 1, key, oldValue, newValue, author, message)); // RECORDED
        currentConfig.put(key, newValue);
    }

    public static void main(String[] args) {
        applyChange("timeout.ms", "5000", "alice", "increase timeout under load");
        System.out.println("Current timeout: " + currentConfig.get("timeout.ms"));
        System.out.println("History:");
        for (ConfigCommit c : history) {
            System.out.println("  v" + c.version() + " by " + c.author() + ": " + c.oldValue() + " -> " + c.newValue() + " (" + c.message() + ")");
        }
    }
}
```

**How to run:** `javac VersionTrackedConfig.java && java VersionTrackedConfig` (JDK 17+).

Expected output:
```
Current timeout: 5000
History:
  v1 by alice: 3000 -> 5000 (increase timeout under load)
```

### Level 3 — Advanced

```java
// File: RollbackUsingHistory.java -- uses the SAME recorded history to
// roll back to a PREVIOUS configuration state, exactly as `git revert`
// would for a versioned config file -- impossible with untracked mutation.
import java.util.*;

public class RollbackUsingHistory {
    record ConfigCommit(int version, String key, String oldValue, String newValue, String author, String message) {}

    static List<ConfigCommit> history = new ArrayList<>();
    static Map<String, String> currentConfig = new HashMap<>(Map.of("timeout.ms", "3000"));

    static void applyChange(String key, String newValue, String author, String message) {
        String oldValue = currentConfig.get(key);
        history.add(new ConfigCommit(history.size() + 1, key, oldValue, newValue, author, message));
        currentConfig.put(key, newValue);
    }

    static void rollbackToVersion(int targetVersion) {
        // find the commit AFTER targetVersion whose oldValue is what we want to restore to
        for (ConfigCommit c : history) {
            if (c.version() == targetVersion + 1) {
                applyChange(c.key(), c.oldValue(), "system-rollback", "revert to v" + targetVersion);
                return;
            }
        }
    }

    public static void main(String[] args) {
        applyChange("timeout.ms", "5000", "alice", "increase timeout under load");
        applyChange("timeout.ms", "8000", "bob", "increase further after incident");
        System.out.println("Before rollback: " + currentConfig.get("timeout.ms"));

        rollbackToVersion(1); // roll back to the value AFTER v1 (i.e., "5000"), undoing bob's v2 change
        System.out.println("After rollback to v1's resulting state: " + currentConfig.get("timeout.ms"));

        System.out.println("\nFull history:");
        for (ConfigCommit c : history) {
            System.out.println("  v" + c.version() + " by " + c.author() + ": " + c.oldValue() + " -> " + c.newValue() + " (" + c.message() + ")");
        }
    }
}
```

**How to run:** `javac RollbackUsingHistory.java && java RollbackUsingHistory` (JDK 17+).

Expected output:
```
Before rollback: 8000
After rollback to v1's resulting state: 5000

Full history:
  v1 by alice: 3000 -> 5000 (increase timeout under load)
  v2 by bob: 8000 -> 5000 (increase further after incident)
  v3 by system-rollback: 8000 -> 5000 (revert to v1)
```

## 6. Walkthrough

1. **Level 1, mutation with no trace** — `timeoutMs = 5000` directly overwrites the field; once this line executes, the previous value `3000` exists nowhere in the program's state — there is no way to answer "what was this before?" from the running program alone.
2. **Level 2, recording every change** — `applyChange` reads `oldValue` from `currentConfig` *before* overwriting it, and appends a `ConfigCommit` capturing that old value, the new value, who made the change, and why — mirroring exactly what a Git commit to a versioned config file preserves (a diff, an author, a message).
3. **Level 2, the resulting audit trail** — printing `history` after one change shows a single commit entry recording the full before/after transition, something Level 1's direct mutation could never reconstruct.
4. **Level 3, applying two more changes** — `applyChange` is called twice more (v2 by bob, implicitly v3 later by the rollback itself), each appending its own commit entry with its own old and new values, building a chronological record exactly as a Git log would.
5. **Level 3, rolling back** — `rollbackToVersion(1)` searches `history` for the commit immediately after version 1 (which is v2, bob's change) and applies a *new* change restoring `key` to that commit's `oldValue` — this mirrors how `git revert` doesn't delete history but adds a new commit that undoes a prior one, preserving the full record of what happened.
6. **Level 3, the output confirms both the effect and the record** — `currentConfig.get("timeout.ms")` drops from `8000` back to `5000` after the rollback, and the printed history shows all three commits in order, including the rollback itself recorded as its own entry (v3) — nothing was erased, only appended to, which is exactly the durability guarantee that treating configuration as version-controlled code provides.

## 7. Gotchas & takeaways

> **Gotcha:** configuration as code is not the right storage mechanism for everything — secrets should never be committed in plaintext to a Git repository (see [secrets management & encryption](0222-secrets-management-encryption.md)), and highly dynamic, frequently toggled values may be better served by a purpose-built store (see [dynamic runtime configuration refresh](0223-dynamic-runtime-configuration-refresh.md)) than by a commit-per-change workflow, which adds friction that's disproportionate for values changing many times a day.

- Configuration as code means storing settings in version-controlled files, giving every change a reviewable diff and a recoverable history — the same guarantees version control gives application source code.
- This makes past configuration states reconstructible and bad changes revertible, unlike configuration mutated in place with no audit trail.
- It pairs naturally with a [centralized configuration server](0219-centralized-configuration-server.md) backed by a Git repository, a common real-world combination.
- A rollback under configuration as code is itself a new, recorded change (like `git revert`), not an erasure of history — the full record of what happened is preserved.
- Not every kind of configuration belongs in version control — secrets need dedicated secure storage, and very frequently changing values may be better served by a more dynamic mechanism than a commit-based workflow.
