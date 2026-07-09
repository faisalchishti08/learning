---
card: java
gi: 596
slug: optional-or
title: Optional.or
---

## 1. What it is

`Optional.or` is a Java 9 method that returns the same `Optional` if it contains a value, or evaluates a `Supplier<Optional<T>>` and returns its result if the `Optional` is empty. It is the lazy-evaluation counterpart to `Optional.orElseGet` — while `orElseGet` returns a raw value (unwrapping the `Optional`), `or` returns another `Optional`, allowing you to chain multiple fallback `Optional` sources into a single pipeline without unwrapping until the very end.

## 2. Why & when

Real systems often have multiple fallback data sources: try the cache, then the primary database, then the secondary replica, then a configuration default. Before Java 9, chaining `Optional` fallbacks required nested `orElseGet` calls that unwrapped each layer: `cache.orElseGet(() -> db.orElseGet(() -> replica.orElse(default)))`. This pattern was verbose and lost the `Optional` wrapper at each step, making it impossible to stay in `Optional`'s fluent API through the chain. `or` solves this by returning `Optional<T>` instead of `T`, so you can write `cache.or(() -> db).or(() -> replica).orElse(default)` — a flat, left-to-right chain where each fallback is a lazily-computed `Optional`.

## 3. Core concept

```java
Optional<String> primary   = Optional.empty();
Optional<String> secondary = Optional.of("Fallback");

String result = primary
    .or(() -> secondary)
    .orElse("default");

System.out.println(result); // "Fallback"
```

`primary` is empty, so `or(() -> secondary)` evaluates the supplier, which returns `secondary` (an `Optional` containing `"Fallback"`). Since `secondary` is present, the result of `or` is that `Optional("Fallback")`. The final `.orElse("default")` unwraps it, producing `"Fallback"`. If `secondary` were also empty, the chain would continue through additional `.or(...)` calls, eventually reaching `.orElse("default")`.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Optional.or chains multiple fallback Optional sources lazily">
  <rect x="20" y="10" width="560" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">primary.or(() → secondary).or(() → tertiary).orElse("default")</text>

  <rect x="30" y="50" width="100" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="80" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">primary ∅</text>
  <text x="138" y="70" fill="#79c0ff" font-size="11" font-family="monospace">→</text>

  <rect x="150" y="50" width="110" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="205" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">secondary ✓</text>
  <text x="268" y="70" fill="#79c0ff" font-size="11" font-family="monospace">→</text>

  <rect x="280" y="50" width="100" height="30" rx="4" fill="#8b949e" stroke="#8b949e" opacity="0.5"/>
  <text x="330" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">tertiary —</text>

  <text x="30" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">primary empty → evaluates supplier → gets Optional("Fallback") → present → stops chain</text>
  <text x="30" y="122" fill="#8b949e" font-size="10" font-family="sans-serif">tertiary supplier is never evaluated (lazy — secondary satisfied the chain)</text>

  <text x="30" y="148" fill="#e6edf3" font-size="11" font-family="sans-serif">Result: "Fallback" — unwrapped by final .orElse("default")</text>
</svg>

Each `.or(...)` adds another fallback `Optional`; only the first non-empty one is returned, and suppliers after it are never evaluated.

## 5. Runnable example

Scenario: a configuration resolver that looks up a setting from multiple sources in priority order — system property, then environment variable, then a configuration file, then a hardcoded default — starting with a simple two-source chain, extending to a real multi-source resolver, and finally handling edge cases where a fallback supplier itself throws or returns null.

### Level 1 — Basic

```java
// File: OptionalOrDemo.java
import java.util.Optional;

public class OptionalOrDemo {
    public static void main(String[] args) {
        Optional<String> fromCache = Optional.empty();
        Optional<String> fromDB    = Optional.of("database_value");

        String value = fromCache
            .or(() -> fromDB)
            .orElse("default");

        System.out.println("Resolved: " + value);
    }
}
```

**How to run:** `java OptionalOrDemo.java`

Expected output:
```
Resolved: database_value
```

The simplest two-source chain: `fromCache` is empty, so `or(() -> fromDB)` evaluates the supplier and returns `fromDB`, which contains `"database_value"`. The final `orElse` unwraps it.

### Level 2 — Intermediate

```java
// File: ConfigResolver.java
import java.util.Map;
import java.util.Optional;

public class ConfigResolver {
    // Simulated configuration sources
    private static final Map<String, String> configFile = Map.of(
        "app.timeout", "30",
        "app.retries", "3"
    );

    static Optional<String> fromSystemProperty(String key) {
        return Optional.ofNullable(System.getProperty(key));
    }

    static Optional<String> fromEnv(String key) {
        return Optional.ofNullable(System.getenv(key));
    }

    static Optional<String> fromConfigFile(String key) {
        return Optional.ofNullable(configFile.get(key));
    }

    static String resolve(String key) {
        return fromSystemProperty(key)                    // 1st priority: -D flag
            .or(() -> fromEnv(key))                       // 2nd priority: env var
            .or(() -> fromConfigFile(key))                // 3rd priority: config file
            .orElse("UNSET");                              // fallback
    }

    public static void main(String[] args) {
        // Simulate: no system property, no env var, but present in config file
        System.out.println("app.timeout = " + resolve("app.timeout"));

        // Simulate: not in any source
        System.out.println("app.secret = " + resolve("app.secret"));

        // Simulate: system property set (via -D on command line)
        System.setProperty("app.timeout", "45");
        System.out.println("app.timeout (after -D) = " + resolve("app.timeout"));
    }
}
```

**How to run:** `java ConfigResolver.java`

Expected output:
```
app.timeout = 30
app.secret = UNSET
app.timeout (after -D) = 45
```

The real-world concern added: a multi-source configuration resolver with clear priority ordering. Each `.or(...)` delegates to the next lower-priority source only if the previous one is empty. The first lookup (`app.timeout`) resolves through `fromSystemProperty` (empty), then `fromEnv` (empty), then `fromConfigFile` (present → returns `"30"`). The second lookup (`app.secret`) exhausts all three sources and falls through to the final `.orElse("UNSET")`. The third demonstrates that when a higher-priority source later becomes available (`System.setProperty`), the chain picks it up on the next call — the chain is evaluated fresh each time.

### Level 3 — Advanced

```java
// File: RobustConfigResolver.java
import java.util.Map;
import java.util.Optional;

public class RobustConfigResolver {
    private static final Map<String, String> configFile = Map.of(
        "db.host", "localhost",
        "db.port", "5432"
    );

    // A fallback source that might fail (simulated flaky service)
    static class RemoteConfigService {
        private final boolean available;

        RemoteConfigService(boolean available) { this.available = available; }

        Optional<String> get(String key) {
            if (!available) {
                System.err.println("  [ERROR] Remote config unreachable for key: " + key);
                return Optional.empty(); // graceful degradation — return empty, don't throw
            }
            return Optional.ofNullable(Map.of("db.host", "prod-db.example.com").get(key));
        }
    }

    static Optional<String> fromEnv(String key) {
        return Optional.ofNullable(System.getenv(key));
    }

    static Optional<String> fromFile(String key) {
        return Optional.ofNullable(configFile.get(key));
    }

    static String resolve(String key, RemoteConfigService remote) {
        return fromEnv(key)
            .or(() -> remote.get(key))
            .or(() -> fromFile(key))
            .or(() -> {
                System.err.println("  [WARN] No value found for '" + key + "', using default");
                return Optional.of("DEFAULT");
            })
            .get(); // safe because the last or() guarantees a value
    }

    public static void main(String[] args) {
        RemoteConfigService remoteHealthy = new RemoteConfigService(true);
        RemoteConfigService remoteDown    = new RemoteConfigService(false);

        System.out.println("=== Healthy remote ===");
        System.out.println("db.host = " + resolve("db.host", remoteHealthy));

        System.out.println("\n=== Remote down — falls back to config file ===");
        System.out.println("db.host = " + resolve("db.host", remoteDown));

        System.out.println("\n=== Unknown key, remote down ===");
        System.out.println("db.user = " + resolve("db.user", remoteDown));
    }
}
```

**How to run:** `java RobustConfigResolver.java`

Expected output (stderr may interleave):
```
=== Healthy remote ===
db.host = prod-db.example.com

=== Remote down — falls back to config file ===
  [ERROR] Remote config unreachable for key: db.host
db.host = localhost

=== Unknown key, remote down ===
  [ERROR] Remote config unreachable for key: db.user
  [WARN] No value found for 'db.user', using default
db.user = DEFAULT
```

The production-flavoured edge cases: (1) a fallback supplier may itself produce an empty `Optional` — the chain continues to the next `.or(...)` as if that source were never consulted; (2) the final `.or(...)` can produce a guaranteed value (via `Optional.of("DEFAULT")`) so that calling `.get()` is safe — this is a pattern for ensuring a non-empty result at the end of an `or` chain; (3) each fallback supplier is only evaluated if needed — the remote config service is only called when the previous source(s) were empty, and its internal error handling (logging + returning empty) isolates the caller from the failure.

## 6. Walkthrough

Tracing the third lookup in the Level 3 example: `resolve("db.user", remoteDown)`:

1. `resolve("db.user", remoteDown)` is called. The parameter `remote` is the `remoteDown` instance, whose `available` flag is `false`.

2. `fromEnv("db.user")` executes: `System.getenv("db.user")` returns `null` (no such environment variable). `Optional.ofNullable(null)` returns `Optional.empty()`. The chain's first element is empty.

3. `.or(() -> remote.get("db.user"))` is reached. Since the previous `Optional` (from `fromEnv`) was empty, the supplier is evaluated:
   - `remote.get("db.user")` is called. `remote.available` is `false`.
   - The `if (!available)` branch executes: `System.err.println(...)` prints the error message.
   - The method returns `Optional.empty()`.
   - The supplier returns this empty `Optional`.

4. The `.or(...)` operation receives the supplier's result: another empty `Optional`. Since this fallback `Optional` is also empty, `or` returns it (empty), and the chain is still unresolved.

5. `.or(() -> fromFile("db.user"))` is reached. Again, the previous result is empty, so the supplier is evaluated:
   - `configFile.get("db.user")` looks up the key in the static map. No such key exists. Returns `null`.
   - `Optional.ofNullable(null)` returns `Optional.empty()`.
   - The supplier returns empty.

6. `.or(() -> { ... })` — the fourth and final `.or()`. The supplier executes:
   - `System.err.println(...)` prints the warning.
   - Returns `Optional.of("DEFAULT")` — a guaranteed non-empty `Optional`.

7. The chain now holds `Optional.of("DEFAULT")`. `.get()` is called — since the `Optional` is present, it returns the string `"DEFAULT"`.

8. The caller prints `"db.user = DEFAULT"`.

```
fromEnv("db.user")          → Optional.empty()
  .or(remote.get)           → Optional.empty()  (remote down — logged error)
  .or(fromFile)             → Optional.empty()  (key not in file)
  .or(() -> Optional.of("DEFAULT")) → Optional.of("DEFAULT")  (guaranteed fallback)
  .get()                    → "DEFAULT"
```

## 7. Gotchas & takeaways

> The supplier passed to `.or()` must return an `Optional<T>`, not a `T`. If you accidentally pass `() -> someString` instead of `() -> Optional.of(someString)`, the code will not compile because a `String` is not an `Optional<String>`. This is the most common mistake when migrating from `orElseGet`, which takes a `Supplier<T>` returning a raw value.

- `.or()` is lazy — the supplier is only evaluated if the preceding `Optional` is empty. This makes it safe and cheap to chain expensive fallback operations (remote calls, DB queries), since they are only executed when all higher-priority sources have failed.
- Unlike `orElseGet`, which unwraps the `Optional` and returns a `T`, `.or()` returns `Optional<T>` — this keeps you inside the `Optional` API so you can chain further `.map()`, `.filter()`, `.or()`, or conditionally unwrap at the end.
- The pattern `.or(() -> ...).or(() -> ...).orElse(default)` is the idiomatic way to express "try these sources in order, use this default if all fail." The final `.orElse(...)` unwraps the value.
- `or` does not cache the result of the supplier — if you call the resulting `Optional`'s methods multiple times, the supplier will be re-evaluated each time if the original was empty. If the fallback is expensive and you need to avoid recomputation, call `.or(...)` and store the result in a local variable before further use.
- A supplier that returns `null` (not `Optional.empty()`) will cause a `NullPointerException` — the contract of the `Supplier<Optional<T>>` requires that the returned `Optional` is non-null, even if it is empty. 