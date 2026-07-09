---
card: java
gi: 536
slug: orelse-orelseget-orelsethrow
title: orElse() / orElseGet() / orElseThrow()
---

## 1. What it is

These three methods extract a value from an `Optional`, each handling the empty case differently. `orElse(defaultValue)` returns the held value if present, or a supplied default value if empty — but the default value expression is **always evaluated**, even when the `Optional` is present and the default ends up unused. `orElseGet(supplier)` is the lazy version: the `Supplier` is only invoked if the `Optional` is actually empty. `orElseThrow(exceptionSupplier)` throws a custom exception (built by the supplier) if empty, or returns the value if present — and the no-argument `orElseThrow()` throws `NoSuchElementException` by default.

## 2. Why & when

`orElse` is the simplest choice when the fallback value is cheap to produce — a literal, an already-computed variable, a `new` call with no real cost. `orElseGet` matters specifically when producing the fallback is *expensive* (a database call, a network request, a complex computation) — using `orElse` there would waste that work every single time, even when the `Optional` already has a value and the fallback is never actually needed. `orElseThrow` is for cases where "no value" is itself an error condition that should stop execution with a clear, specific exception, rather than silently substituting some default.

## 3. Core concept

```java
import java.util.*;

Optional<String> present = Optional.of("cached-value");
Optional<String> empty = Optional.empty();

String a = present.orElse(computeExpensiveDefault()); // computeExpensiveDefault() STILL runs, wastefully
String b = present.orElseGet(() -> computeExpensiveDefault()); // only runs if 'present' were actually empty

String c = empty.orElseThrow(() -> new IllegalStateException("No value configured"));
// throws IllegalStateException here, since 'empty' has no value
```

`orElse` always evaluates its argument eagerly; `orElseGet` only invokes its supplier lazily, on demand; `orElseThrow` converts absence into a specific, thrown exception instead of any default value.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="orElse always evaluates its default eagerly; orElseGet only evaluates its supplier when actually needed">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">present.orElse(expensiveCall()):</text>
  <rect x="280" y="15" width="150" height="28" fill="#1c2430" stroke="#f85149"/><text x="355" y="34" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">expensiveCall() RUNS anyway</text>

  <text x="20" y="80" fill="#8b949e" font-size="11" font-family="sans-serif">present.orElseGet(() -&gt; expensiveCall()):</text>
  <rect x="280" y="65" width="150" height="28" fill="#1c2430" stroke="#6db33f"/><text x="355" y="84" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">expensiveCall() SKIPPED</text>
  <text x="20" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">orElse's argument is a value, evaluated eagerly; orElseGet's is a Supplier, evaluated only if needed.</text>
</svg>

`orElse`'s argument is computed before the method is even called, regardless of whether it's needed; `orElseGet`'s supplier is only invoked when the `Optional` is genuinely empty.

## 5. Runnable example

Scenario: loading a user's display name, falling back to a database lookup or an error as appropriate — evolved from a basic `orElse` with a cheap default, through demonstrating `orElse`'s wasted eager evaluation with an expensive fallback, to a version using `orElseThrow` with a custom, informative exception.

### Level 1 — Basic

```java
import java.util.*;

public class OrElseBasic {
    public static void main(String[] args) {
        Optional<String> nickname = Optional.of("Ace");
        Optional<String> noNickname = Optional.empty();

        String displayName1 = nickname.orElse("Anonymous");
        String displayName2 = noNickname.orElse("Anonymous");

        System.out.println("Display 1: " + displayName1);
        System.out.println("Display 2: " + displayName2);
    }
}
```

**How to run:** `java OrElseBasic.java`

Expected output:
```
Display 1: Ace
Display 2: Anonymous
```

`nickname.orElse("Anonymous")` returns `"Ace"`, since `nickname` has a value — the literal `"Anonymous"` is technically still "evaluated" (it's just a literal, so this costs nothing), but it's never actually used or returned. `noNickname.orElse("Anonymous")` returns `"Anonymous"` directly, since `noNickname` is empty.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class OrElseVsOrElseGet {
    static AtomicInteger expensiveCallCount = new AtomicInteger(0);

    static String expensiveDefaultLookup() {
        expensiveCallCount.incrementAndGet(); // simulates a costly operation, e.g. a database query
        return "database-default";
    }

    public static void main(String[] args) {
        Optional<String> cachedValue = Optional.of("cached-value");

        // orElse: the expensive call runs EVERY time, even though cachedValue is present.
        String resultA = cachedValue.orElse(expensiveDefaultLookup());
        System.out.println("orElse result: " + resultA + ", expensive calls so far: " + expensiveCallCount.get());

        // orElseGet: the expensive call is SKIPPED entirely, since cachedValue is present.
        String resultB = cachedValue.orElseGet(OrElseVsOrElseGet::expensiveDefaultLookup);
        System.out.println("orElseGet result: " + resultB + ", expensive calls so far: " + expensiveCallCount.get());
    }
}
```

**How to run:** `java OrElseVsOrElseGet.java`

Expected output:
```
orElse result: cached-value, expensive calls so far: 1
orElseGet result: cached-value, expensive calls so far: 1
```

The real-world concern this adds: `cachedValue.orElse(expensiveDefaultLookup())` requires Java to evaluate `expensiveDefaultLookup()` *before* `orElse` is even called — as a plain method argument, it's evaluated unconditionally, regardless of whether `cachedValue` turns out to be present. This is why `expensiveCallCount` is already `1` after the `orElse` line, even though `cachedValue` was present and the default was never actually used. `cachedValue.orElseGet(...)`, by contrast, passes a `Supplier` (a method reference) that's only invoked if `orElseGet` internally decides it's needed — since `cachedValue` is present, it's never called, and `expensiveCallCount` stays at `1`.

### Level 3 — Advanced

```java
import java.util.*;

public class OrElseThrowCustom {
    record Config(String key, String value) {}

    static final Map<String, Config> CONFIG_STORE = Map.of(
            "timeout", new Config("timeout", "30s")
    );

    static Optional<Config> lookupConfig(String key) {
        return Optional.ofNullable(CONFIG_STORE.get(key));
    }

    static class MissingConfigException extends RuntimeException {
        MissingConfigException(String key) {
            super("Required configuration key '" + key + "' is missing -- check application.properties");
        }
    }

    public static void main(String[] args) {
        Config timeoutConfig = lookupConfig("timeout")
                .orElseThrow(() -> new MissingConfigException("timeout"));
        System.out.println("Timeout config: " + timeoutConfig.value());

        try {
            Config retriesConfig = lookupConfig("retries")
                    .orElseThrow(() -> new MissingConfigException("retries"));
            System.out.println("Retries config: " + retriesConfig.value());
        } catch (MissingConfigException e) {
            System.out.println("Startup failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java OrElseThrowCustom.java`

Expected output:
```
Timeout config: 30s
Startup failed: Required configuration key 'retries' is missing -- check application.properties
```

This uses `orElseThrow(...)` with a **custom exception type** carrying a specific, actionable message — rather than the generic `NoSuchElementException` the no-argument `orElseThrow()` would throw. `lookupConfig("timeout")` finds a value, so the supplier is never invoked and the config's value is returned directly. `lookupConfig("retries")` finds nothing (not in `CONFIG_STORE`), so `orElseThrow`'s supplier runs, constructing and throwing a `MissingConfigException` with a message that tells the developer exactly what's missing and where to look — far more useful for debugging a real startup failure than a bare `NoSuchElementException` would be.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `CONFIG_STORE` has one entry: `"timeout" -> Config("timeout", "30s")`.

`lookupConfig("timeout")` returns `Optional.of(Config("timeout", "30s"))`, since the key exists. `.orElseThrow(() -> new MissingConfigException("timeout"))` is called: since the `Optional` is present, the supplier lambda (`() -> new MissingConfigException("timeout")`) is never invoked at all — `orElseThrow` simply unwraps and returns the held `Config` directly. `timeoutConfig.value()` is `"30s"`, printed as `"Timeout config: 30s"`.

`lookupConfig("retries")` is called next, inside a `try` block. `CONFIG_STORE.get("retries")` returns `null`, since `"retries"` isn't a key in the map, so `lookupConfig` returns `Optional.ofNullable(null)` = `Optional.empty()`. `.orElseThrow(() -> new MissingConfigException("retries"))` is called on this empty `Optional`: this time, since there's no value, the supplier *is* invoked — `new MissingConfigException("retries")` constructs a new exception instance, with its message built from the constructor: `"Required configuration key 'retries' is missing -- check application.properties"`. `orElseThrow` then throws this newly-constructed exception immediately.

```
lookupConfig("timeout") -> Optional.of(Config)  -> orElseThrow: present, supplier SKIPPED -> returns Config
lookupConfig("retries") -> Optional.empty()     -> orElseThrow: empty, supplier INVOKED -> constructs and throws
                                                     MissingConfigException("Required configuration key 'retries'...")
```

This thrown `MissingConfigException` propagates up out of `lookupConfig(...).orElseThrow(...)`, up out of the assignment to `retriesConfig` (which never completes), and is caught by the surrounding `try`/`catch` block in `main`. `e.getMessage()` retrieves the exact message built inside the exception's constructor, printed as `"Startup failed: Required configuration key 'retries' is missing -- check application.properties"` — a clear, specific, actionable error message, precisely because the supplier passed to `orElseThrow` was written to construct exactly that.

## 7. Gotchas & takeaways

> `orElse(value)`'s argument is a plain method argument, not a lazy expression — Java evaluates it *before* calling `orElse`, unconditionally, every single time, regardless of whether the `Optional` is present. This means `orElse(expensiveCall())` always pays the cost of `expensiveCall()`, even when its result is discarded, which is precisely the mistake `orElseGet(() -> expensiveCall())` avoids by deferring the call behind a `Supplier` that `orElseGet` only invokes when genuinely necessary.

- `orElse(value)` eagerly evaluates its argument every time, regardless of whether the `Optional` is present — safe only for cheap, side-effect-free default values.
- `orElseGet(supplier)` lazily invokes its supplier only when the `Optional` is actually empty — the correct choice whenever the fallback is expensive or has side effects.
- `orElseThrow(exceptionSupplier)` throws a custom exception (built lazily, only when needed) instead of any default value, appropriate when absence represents a genuine error condition.
- The no-argument `orElseThrow()` throws a generic `NoSuchElementException`; the argument form lets you throw a specific, more informative exception type with a tailored message.
- When in doubt about whether a default value expression is "cheap enough" for `orElse`, default to `orElseGet` instead — it's never worse, and it avoids the class of bug where a seemingly-innocent default value turns out to have a real cost or side effect.
