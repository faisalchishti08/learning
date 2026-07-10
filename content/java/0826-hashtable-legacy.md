---
card: java
gi: 826
slug: hashtable-legacy
title: Hashtable (legacy)
---

## 1. What it is

`Hashtable` is a hash-table-based `Map` implementation that, like [`Vector`](0814-vector-legacy-synchronized.md), predates the Collections Framework — it shipped in Java 1.0, decades before `HashMap` existed. Every method is `synchronized`, giving it built-in (per-method) thread safety at the cost of locking overhead on every single call, even in single-threaded code. It was retrofitted to implement `Map` in Java 1.2. The one functional difference that regularly bites migrations: **`Hashtable` does not permit `null` keys or `null` values** — attempting either throws `NullPointerException` immediately, whereas `HashMap` explicitly permits one `null` key and any number of `null` values.

## 2. Why & when

`Hashtable` exists today almost entirely for backward compatibility with old APIs and codebases — some legacy JDK classes (like `Properties`, which extends `Hashtable<Object,Object>` for historical reasons) still surface it directly. In new code, there is essentially no reason to choose `Hashtable` deliberately: single-threaded code should use `HashMap`, and multi-threaded code should use [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md), which offers far better concurrent performance than `Hashtable`'s single-lock-per-call model, plus genuinely useful atomic compound operations (`computeIfAbsent`, `merge`) that `Hashtable`'s per-method locking doesn't provide for free. The main practical reason to understand `Hashtable` today is recognizing it when it appears in old code (or via `Properties`) and knowing its null-handling difference, which is a common source of a surprising `NullPointerException` when porting code that assumed `HashMap`'s more permissive behavior.

## 3. Core concept

```java
Hashtable<String, String> legacy = new Hashtable<>();
legacy.put("key", "value"); // fine

try {
    legacy.put("missingValueKey", null); // Hashtable disallows null values
} catch (NullPointerException e) {
    System.out.println("Hashtable rejects null values");
}

try {
    legacy.put(null, "value"); // Hashtable disallows null keys too
} catch (NullPointerException e) {
    System.out.println("Hashtable rejects null keys");
}

// Contrast: HashMap permits both.
Map<String, String> modern = new HashMap<>();
modern.put("key", null);  // fine
modern.put(null, "value"); // also fine -- one null key allowed
```

Every `Hashtable` method (`put`, `get`, `remove`, `containsKey`, and the rest) is individually `synchronized` — the same per-method locking strategy `Vector` uses, with the identical limitation that compound check-then-act sequences across multiple calls are still not atomic overall.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HashMap permits a null key and null values; Hashtable rejects both, throwing NullPointerException immediately">
  <rect x="40" y="30" width="250" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HashMap</text>
  <text x="165" y="75" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">permits one null key, any null values</text>

  <rect x="350" y="30" width="250" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Hashtable</text>
  <text x="475" y="75" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">throws NPE on any null key or value</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A common migration surprise: code relying on HashMap's null tolerance breaks immediately on Hashtable</text>
</svg>

*`HashMap` tolerates `null` keys/values; `Hashtable` rejects both outright — a frequent migration gotcha.*

## 5. Runnable example

Scenario: legacy configuration storage code being examined for a migration, growing from basic `Hashtable` usage, to the null-handling difference that breaks naive porting, to the actual recommended modern replacement.

### Level 1 — Basic

```java
import java.util.*;

public class LegacyConfigBasic {
    public static void main(String[] args) {
        Hashtable<String, String> config = new Hashtable<>();
        config.put("timeout", "30");
        config.put("retries", "3");

        System.out.println("config: " + config);
        System.out.println("timeout: " + config.get("timeout"));
    }
}
```

**How to run:** `java LegacyConfigBasic.java` (JDK 17+).

Expected output (Hashtable's iteration order is also unspecified, similar to HashMap):
```
config: {retries=3, timeout=30}
timeout: 30
```

Functionally, `Hashtable` behaves like a basic `Map` here — the differences only surface around null-handling and concurrency behavior.

### Level 2 — Intermediate

```java
import java.util.*;

public class LegacyConfigNullTrap {
    public static void main(String[] args) {
        Hashtable<String, String> config = new Hashtable<>();
        config.put("timeout", "30");

        // A common pattern that works fine on HashMap but breaks on Hashtable:
        String missingSetting = config.get("nonexistent-key"); // returns null -- fine, get() never throws
        System.out.println("missing setting (via get): " + missingSetting);

        try {
            config.put("optional-flag", missingSetting); // attempting to STORE that null value
        } catch (NullPointerException e) {
            System.out.println("caught: Hashtable rejects storing a null value");
        }

        try {
            config.get(null); // Hashtable also rejects even READING with a null key
        } catch (NullPointerException e) {
            System.out.println("caught: Hashtable rejects a null key, even for get()");
        }
    }
}
```

**How to run:** `java LegacyConfigNullTrap.java`.

Expected output:
```
missing setting (via get): null
caught: Hashtable rejects storing a null value
caught: Hashtable rejects a null key, even for get()
```

The real-world concern added: `get()` on a *missing* key correctly returns `null` without throwing (that part matches `HashMap`), but attempting to **store** a `null` value, or to call `get(null)` with a `null` key, both throw immediately — a pattern that would work silently on `HashMap` but crashes on `Hashtable`, a genuine trap when migrating code between the two or when code is written against `Map` without knowing which implementation it'll actually receive at runtime.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.*;

public class LegacyConfigMigration {
    public static void main(String[] args) {
        // The old way: Hashtable, synchronized per-method, null-intolerant.
        Hashtable<String, String> legacyConfig = new Hashtable<>();
        legacyConfig.put("timeout", "30");

        // The modern replacement for concurrent use: ConcurrentHashMap.
        // Note: ConcurrentHashMap ALSO disallows null keys/values (for a different reason --
        // ambiguity between "absent" and "present but null" in a concurrent context) --
        // but it offers far better concurrent throughput and atomic compound operations.
        ConcurrentHashMap<String, String> modernConfig = new ConcurrentHashMap<>(legacyConfig);

        // Atomic "update if present, else compute a default" -- not something Hashtable offers directly.
        modernConfig.merge("retryCount", "1", (oldVal, newVal) -> String.valueOf(Integer.parseInt(oldVal) + 1));
        modernConfig.merge("retryCount", "1", (oldVal, newVal) -> String.valueOf(Integer.parseInt(oldVal) + 1));

        System.out.println("modern config: " + modernConfig);
        System.out.println("retryCount after two merges: " + modernConfig.get("retryCount"));
    }
}
```

**How to run:** `java LegacyConfigMigration.java`.

Expected output (map iteration order not guaranteed, but values are deterministic):
```
modern config: {timeout=30, retryCount=2}
retryCount after two merges: 2
```

This adds the production-flavored hard case: the actual recommended migration path. `ConcurrentHashMap` (constructed here directly from the old `Hashtable` via its copy constructor) still disallows `null` keys/values, so that particular gotcha doesn't disappear — but it replaces `Hashtable`'s crude single-lock-per-call model with fine-grained internal locking (explored further in [ConcurrentHashMap internals](0830-concurrenthashmap-internals.md)) and adds genuinely useful atomic operations like `merge`, letting "increment a counter, initializing it if absent" happen in one call instead of a manual check-then-act sequence.

## 6. Walkthrough

Tracing `LegacyConfigMigration.main`:

1. `legacyConfig` is a `Hashtable` seeded with one entry, `"timeout" -> "30"`.
2. `modernConfig = new ConcurrentHashMap<>(legacyConfig)` copies every entry from the old `Hashtable` into a new `ConcurrentHashMap` — a common first migration step, since both implement `Map<String, String>` and the copy constructor works across implementations.
3. `modernConfig.merge("retryCount", "1", (oldVal, newVal) -> ...)` is called for the first time. Since `"retryCount"` isn't yet a key, `merge` simply inserts the provided value (`"1"`) directly — the combining function is not invoked for a first insertion.
4. The second `merge("retryCount", "1", ...)` call finds `"retryCount"` already present (value `"1"`), so this time the combining function **is** invoked, receiving `oldVal = "1"` and `newVal = "1"` (the value just passed to this call) — it parses `oldVal` as an integer, adds one, and returns `"2"` as a string, which `merge` then stores back into the map atomically.
5. Printing `modernConfig` shows both the original `"timeout"` entry (carried over from the `Hashtable` copy) and the now-twice-incremented `"retryCount"` entry, `"2"` — demonstrating both the successful migration of existing data and the atomic-update idiom `merge` provides, which `Hashtable` has no equivalent for without manual, non-atomic check-then-act code.

## 7. Gotchas & takeaways

> **Gotcha:** `Hashtable` throws `NullPointerException` immediately on any attempt to store a `null` key **or** a `null` value — including via `put`, and even on lookup with `get(null)`. Code originally written against `HashMap` (which permits both) will fail loudly and immediately if later pointed at a `Hashtable`, or at any `Map` reference that happens to hold one at runtime.

- `Hashtable` predates the Collections Framework; every method is individually `synchronized`, adding overhead even without concurrent access.
- Unlike `HashMap`, `Hashtable` disallows `null` keys and `null` values entirely, throwing `NullPointerException` immediately on either.
- Being "synchronized" only protects individual method calls — compound check-then-act sequences across multiple calls still require explicit external locking, exactly as with [`Vector`](0814-vector-legacy-synchronized.md).
- Modern code should use `HashMap` for single-threaded use and [`ConcurrentHashMap`](0830-concurrenthashmap-internals.md) for concurrent use — both offer better performance and, for `ConcurrentHashMap`, genuinely atomic compound operations like `merge` and `computeIfAbsent`.
- `Hashtable` mainly appears today via legacy code or the [`Properties`](0832-properties.md) class, which extends it for historical reasons — recognizing its null-handling quirk avoids a confusing runtime surprise when working with either.
