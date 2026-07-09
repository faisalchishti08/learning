---
card: java
gi: 675
slug: parallelscavenge-serialold-deprecation
title: ParallelScavenge + SerialOld deprecation
---

## 1. What it is

**Java 14** (JEP 366) **deprecated** the specific combination of the **ParallelScavenge** young-generation collector paired with the **SerialOld** old-generation collector — the flag combination `-XX:+UseParallelGC -XX:-UseParallelOldGC` (or equivalently, some older ways of forcing this specific pairing). This is narrower than it might first sound: the **Parallel collector itself** (`-XX:+UseParallelGC`, pairing ParallelScavenge with ParallelOld) was **not** deprecated and remains fully supported — only the *mixed* combination that uses ParallelScavenge for young-generation collection but falls back to the older, single-threaded SerialOld collector for old-generation collection was marked for eventual removal. This mixed mode was a leftover configuration from before ParallelOld existed as a mature option, and by Java 14 it was serving no purpose that the pure Parallel or pure Serial collectors didn't already cover better.

## 2. Why & when

Maintaining every possible pairing of young-generation and old-generation collectors multiplies the JVM's internal complexity and testing burden — the ParallelScavenge+SerialOld combination specifically existed as a historical artifact from an era when ParallelOld was newer and less proven, giving cautious users an escape hatch to use the faster parallel young-generation collector while keeping the safer, simpler (if slower and single-threaded) SerialOld for the old generation. By Java 14, ParallelOld had been the default old-generation partner for ParallelScavenge for many releases and was thoroughly battle-tested, making the mixed mode pure legacy weight with essentially no remaining users who genuinely needed it over the alternatives. Deprecating it (with removal following in a later release) let OpenJDK simplify its collector combination matrix. If your JVM configuration explicitly forces this exact mixed pairing, you should migrate to plain `-XX:+UseParallelGC` (letting it use its default, matched ParallelOld partner) well before whichever future release actually removes the mixed-mode option.

## 3. Core concept

```bash
# The (deprecated) mixed pairing: ParallelScavenge young-gen + SerialOld old-gen
java -XX:+UseParallelGC -XX:-UseParallelOldGC MyApp
# Prints a deprecation warning on Java 14+:
# "Option UseParallelOldGC was deprecated in version 14.0 and will likely be removed in a future release."

# The supported, recommended form: plain Parallel collector
# (ParallelScavenge automatically paired with ParallelOld — the modern default pairing)
java -XX:+UseParallelGC MyApp

# Fully serial, single-threaded collector (unaffected by this deprecation)
java -XX:+UseSerialGC MyApp
```

The deprecation is specifically about the *unusual cross-pairing* — using the fast, multi-threaded young-generation collector alongside the slow, single-threaded old-generation one — not about either collector individually, both of which remain fully available in their natural pairings (`UseParallelGC` for both parallel, `UseSerialGC` for both serial).

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four historical young/old generation collector pairings; the mixed ParallelScavenge plus SerialOld pairing is deprecated while the pure pairings remain supported">
  <rect x="10" y="10" width="600" height="30" fill="#1c2430"/>
  <text x="160" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">young: ParallelScavenge</text>
  <text x="460" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">young: Serial</text>

  <rect x="10" y="45" width="290" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="155" y="65" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">old: ParallelOld</text>
  <text x="155" y="85" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:+UseParallelGC — SUPPORTED (default pairing)</text>

  <rect x="320" y="45" width="290" height="60" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="465" y="65" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">old: SerialOld</text>
  <text x="465" y="85" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:-UseParallelOldGC — DEPRECATED (mixed mode)</text>

  <rect x="10" y="115" width="290" height="60" rx="6" fill="#1c2430" stroke="#8b949e" opacity="0.5"/>
  <text x="155" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(uncommon, not a JEP 366 target)</text>

  <rect x="320" y="115" width="290" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="135" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">old: SerialOld</text>
  <text x="465" y="155" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">-XX:+UseSerialGC — SUPPORTED (default pairing)</text>
</svg>

Only the cross-pairing of the fast parallel young-gen collector with the slow serial old-gen collector was targeted — both "pure" pairings remain fully supported.

## 5. Runnable example

Scenario: an application launched with the deprecated mixed-collector flag combination — first observing the deprecation warning it produces, then migrating to the recommended pure-Parallel configuration, then writing a small startup self-check (using `GarbageCollectorMXBean`) that verifies both the young- and old-generation collectors in use actually form a sensible, non-deprecated pairing.

### Level 1 — Basic

```java
// File: CollectorApp.java
public class CollectorApp {
    public static void main(String[] args) {
        System.out.println("Application started.");
    }
}
```

**How to run with the deprecated mixed pairing:**
```
javac CollectorApp.java
java -XX:+UseParallelGC -XX:-UseParallelOldGC CollectorApp
```

Expected output on Java 14 (the deprecation warning goes to stderr; the program still runs):
```
Java HotSpot(TM) 64-Bit Server VM warning: Option UseParallelOldGC was deprecated in version 14.0 and will likely be removed in a future release.
Application started.
```

### Level 2 — Intermediate

**How to run with the recommended, non-deprecated configuration:**
```
java -XX:+UseParallelGC CollectorApp
```

Expected output (no deprecation warning):
```
Application started.
```

Simply omitting `-XX:-UseParallelOldGC` lets `-XX:+UseParallelGC` use its natural, fully-supported default pairing (ParallelScavenge young-generation with ParallelOld old-generation) — the fix here, like the CMS removal case, is typically just deleting a stale flag from launch scripts rather than any code change.

### Level 3 — Advanced

```java
// File: CollectorPairingCheck.java
import java.lang.management.ManagementFactory;
import java.lang.management.GarbageCollectorMXBean;
import java.util.List;
import java.util.Set;

public class CollectorPairingCheck {
    // Known non-deprecated collector name pairings as of Java 14.
    static final Set<String> SUPPORTED_YOUNG_NAMES = Set.of(
        "PS Scavenge", "Copy", "G1 Young Generation", "ZGC"
    );
    static final Set<String> SUPPORTED_OLD_NAMES = Set.of(
        "PS MarkSweep", "MarkSweepCompact", "G1 Old Generation", "ZGC"
    );

    public static void main(String[] args) {
        List<GarbageCollectorMXBean> beans = ManagementFactory.getGarbageCollectorMXBeans();

        System.out.println("Detected collector beans:");
        for (GarbageCollectorMXBean bean : beans) {
            System.out.println("  " + bean.getName());
        }

        boolean allRecognized = beans.stream().allMatch(b ->
            SUPPORTED_YOUNG_NAMES.contains(b.getName()) || SUPPORTED_OLD_NAMES.contains(b.getName()));

        if (allRecognized) {
            System.out.println("Collector configuration looks like a standard, supported pairing.");
        } else {
            System.out.println("WARNING: unrecognized collector bean name(s) detected — "
                + "verify this isn't a deprecated or unusual collector combination.");
        }
    }
}
```

**How to run:** `java -XX:+UseParallelGC CollectorPairingCheck.java`

Expected output:
```
Detected collector beans:
  PS Scavenge
  PS MarkSweep
Collector configuration looks like a standard, supported pairing.
```

Level 3 uses `GarbageCollectorMXBean` names to fingerprint which actual collector implementations are active — `"PS Scavenge"` paired with `"PS MarkSweep"` confirms the standard, fully-supported ParallelScavenge+ParallelOld pairing is in effect; had the deprecated mixed mode been active instead, the old-generation bean would report a different name (`"MarkSweepCompact"`, SerialOld's bean name) alongside `"PS Scavenge"`, an unusual combination this check is specifically designed to flag.

## 6. Walkthrough

1. `main` calls `ManagementFactory.getGarbageCollectorMXBeans()`, which returns one `GarbageCollectorMXBean` per distinct collector algorithm actually running inside this JVM instance — for the Parallel collector configuration, that's exactly two beans: one representing young-generation collection work, one representing old-generation collection work (this is different from G1 or ZGC, which — being unified, region-based collectors — typically expose their generational split differently or as a single bean, as seen for ZGC in [ZGC on macOS & Windows](0673-zgc-on-macos-windows.md)).
2. The loop prints each bean's `getName()` — for a JVM launched with `-XX:+UseParallelGC` and no conflicting flags, these come back as `"PS Scavenge"` (the young-generation ParallelScavenge collector's bean name) and `"PS MarkSweep"` (the old-generation ParallelOld collector's bean name, somewhat confusingly retaining a historical name from before ParallelOld was distinguished from other mark-sweep variants).
3. `beans.stream().allMatch(...)` checks whether **every** bean's name appears in either the `SUPPORTED_YOUNG_NAMES` or `SUPPORTED_OLD_NAMES` sets. `"PS Scavenge"` is in `SUPPORTED_YOUNG_NAMES`, and `"PS MarkSweep"` is in `SUPPORTED_OLD_NAMES` — both match, so `allMatch` returns `true`.
4. Because `allRecognized` is `true`, `main` prints the confirmation message that the configuration looks standard and supported.
5. Now consider what would happen if this same check ran under the **deprecated** mixed pairing (`-XX:+UseParallelGC -XX:-UseParallelOldGC`, run on a Java version where it still works but is deprecated — Java 14 itself, before eventual removal): the young-generation bean would still be named `"PS Scavenge"` (ParallelScavenge is unaffected), but the old-generation bean would instead be named `"MarkSweepCompact"` — SerialOld's actual bean name — which does **not** appear in this program's `SUPPORTED_OLD_NAMES` set.
6. In that scenario, `allMatch` would encounter `"MarkSweepCompact"`, find it absent from both supported-name sets, and return `false` — sending execution to the `else` branch, printing the warning about an unrecognized collector bean name, flagging exactly the kind of unusual pairing this JEP targeted for eventual removal.
7. This illustrates a general, reusable diagnostic technique: rather than trying to parse or remember every `-XX` flag combination a deployment script might use, inspecting the *actual running collector beans* via `GarbageCollectorMXBean` tells you unambiguously which real collector implementations ended up active — a more reliable signal than trusting flags were interpreted the way you expected.

```
-XX:+UseParallelGC (no conflicting flags)
   │
   ▼
beans: ["PS Scavenge", "PS MarkSweep"]  ──► both recognized ──► "standard pairing" ✓

-XX:+UseParallelGC -XX:-UseParallelOldGC  (deprecated mixed mode)
   │
   ▼
beans: ["PS Scavenge", "MarkSweepCompact"]  ──► MarkSweepCompact unrecognized ──► WARNING ⚠
```

## 7. Gotchas & takeaways

> This deprecation is specifically about the **cross-pairing**, not either collector individually — don't confuse this with [CMS GC removed](0674-cms-gc-removed.md), which is a full, hard removal of a different collector entirely. `-XX:+UseParallelGC` on its own remains completely supported and is not affected by this deprecation at all; only the explicit override to force SerialOld as its old-generation partner (`-XX:-UseParallelOldGC`) is deprecated.

- The Parallel collector itself (`-XX:+UseParallelGC`, using its default ParallelOld partner) is fully supported and unaffected — this deprecation targets only the unusual mixed pairing.
- Deprecation warnings print to stderr at JVM startup but do **not** prevent the JVM from starting (unlike CMS's later hard removal) — deprecated-but-still-functional is a distinct lifecycle stage from fully removed.
- The fix is typically trivial: remove the `-XX:-UseParallelOldGC` override from launch scripts, letting `-XX:+UseParallelGC` use its natural default pairing.
- `GarbageCollectorMXBean` names (`"PS Scavenge"`, `"PS MarkSweep"`, `"MarkSweepCompact"`, `"G1 Young Generation"`, etc.) are a reliable way to programmatically verify which actual collector implementations are active, useful for auditing deployment configurations beyond just grepping for flag names.
- As with the CMS removal, always audit deployment scripts, `JAVA_OPTS`, and container configurations for `-XX:-UseParallelOldGC` specifically before relying on continued support in a future JDK release beyond Java 14's deprecation warning stage.
