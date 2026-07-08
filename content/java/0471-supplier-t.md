---
card: java
gi: 471
slug: supplier-t
title: Supplier<T>
---

## 1. What it is

`Supplier<T>` is the functional interface for "take no input, produce one output of type `T`." Its single abstract method is `T get()`. Where `Function<T, R>` transforms an existing value and `Consumer<T>` acts on an existing value, `Supplier<T>` is about **deferred, on-demand creation** — a value that doesn't exist yet, computed only at the moment something actually calls `get()`.

## 2. Why & when

Some values are expensive or undesirable to compute eagerly — building a detailed error message that's only needed if an error actually occurs, constructing a default object that's only needed if no real one was supplied, or generating a fresh random value each time one is requested. `Supplier<T>` lets you package "how to produce this value" as a value itself, so the actual computation is deferred until — and only happens if — something calls `get()`. This is the core mechanism behind **lazy evaluation** in Java's standard library.

You reach for `Supplier<T>` whenever an API wants "a way to produce a value later" rather than the value itself right now: `Optional.orElseGet(Supplier<T>)` computes a fallback only if the `Optional` is empty (unlike `orElse(T)`, whose argument is always evaluated eagerly, even when not needed); logging frameworks accept a `Supplier<String>` for a log message so expensive string-building is skipped entirely when that log level is disabled; `Map.computeIfAbsent` conceptually plays a similar deferred role for values keyed by absence.

## 3. Core concept

```java
import java.util.function.*;
import java.util.*;

Supplier<String> greeting = () -> "hello"; // no parameters at all -- empty parens
String value = greeting.get(); // "hello" -- computed only NOW, when get() is called

Optional<String> maybeValue = Optional.empty();
String result = maybeValue.orElseGet(() -> {
    System.out.println("computing expensive default...");
    return "default";
}); // the lambda only runs because maybeValue was empty
```

`get()` takes no arguments — the parentheses in `() -> ...` are always empty for a `Supplier`, since there is nothing to supply *to* it, only something to get *from* it.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Supplier takes no input and produces one output only when get is called, deferring computation until needed">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="60" y="30" width="220" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="170" y="55" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Supplier&lt;T&gt;</text>
  <text x="170" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">get() -- no arguments</text>

  <rect x="400" y="40" width="150" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="475" y="65" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace">T output</text>

  <line x1="280" y1="60" x2="395" y2="60" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <text x="170" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">nothing computed until get() is actually called</text>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

No input at all — a `Supplier` exists purely to defer "how to produce a value" until the moment it's actually needed.

## 5. Runnable example

Scenario: providing default configuration values — evolved from a basic `Supplier` producing a fixed value, through `Optional.orElseGet` proving the supplier only runs when actually needed (unlike an eager alternative), to a caching supplier that computes an expensive value once and reuses it on every later call.

### Level 1 — Basic

```java
import java.util.function.*;

public class SupplierBasic {
    public static void main(String[] args) {
        Supplier<String> defaultGreeting = () -> "Welcome, guest!";

        System.out.println(defaultGreeting.get());
        System.out.println(defaultGreeting.get());
    }
}
```

**How to run:** `java SupplierBasic.java`

Expected output:
```
Welcome, guest!
Welcome, guest!
```

`defaultGreeting.get()` runs the lambda's body each time it's called — here, simply returning the same fixed string both times, since there's no varying state involved yet.

### Level 2 — Intermediate

```java
import java.util.function.*;
import java.util.*;

public class SupplierLazyEvaluation {
    static String buildExpensiveDefault() {
        System.out.println("computing expensive default...");
        return "computed-default";
    }

    public static void main(String[] args) {
        Optional<String> present = Optional.of("real-value");
        Optional<String> absent = Optional.empty();

        // orElseGet takes a Supplier -- its lambda only runs if the Optional is actually empty.
        System.out.println("Present case: " + present.orElseGet(SupplierLazyEvaluation::buildExpensiveDefault));
        System.out.println("Absent case: " + absent.orElseGet(SupplierLazyEvaluation::buildExpensiveDefault));
    }
}
```

**How to run:** `java SupplierLazyEvaluation.java`

Expected output:
```
Present case: real-value
computing expensive default...
Absent case: computed-default
```

The real-world concern this shows: for `present`, `orElseGet`'s `Supplier` (`buildExpensiveDefault`) is never called at all — no `"computing expensive default..."` line appears for that case, because `present` already has a value and the fallback is genuinely unnecessary. For `absent`, the supplier runs exactly once, only because a fallback is actually needed. This is precisely the laziness `Supplier` provides — contrast with `Optional.orElse(T)`, whose argument would be evaluated eagerly every time, wasting the computation in the `present` case.

### Level 3 — Advanced

```java
import java.util.function.*;

public class SupplierCaching {
    // A caching Supplier: wraps another Supplier, computes its value AT MOST ONCE,
    // and returns the cached result on every subsequent call.
    static <T> Supplier<T> cache(Supplier<T> original) {
        Object[] cached = { null }; // holder array -- workaround for the effectively-final restriction
        boolean[] computed = { false };
        return () -> {
            if (!computed[0]) {
                cached[0] = original.get();
                computed[0] = true;
            }
            @SuppressWarnings("unchecked")
            T result = (T) cached[0];
            return result;
        };
    }

    public static void main(String[] args) {
        Supplier<String> expensive = () -> {
            System.out.println("running expensive computation...");
            return "result-42";
        };

        Supplier<String> cached = cache(expensive);

        System.out.println(cached.get());
        System.out.println(cached.get());
        System.out.println(cached.get());
    }
}
```

**How to run:** `java SupplierCaching.java`

Expected output:
```
running expensive computation...
result-42
result-42
result-42
```

`cache` wraps any `Supplier<T>` in a new one that runs the original's `get()` **at most once** — the first call computes and stores the result, every subsequent call returns the stored value without re-running `original.get()` at all. `"running expensive computation..."` prints only once, even though `cached.get()` is called three times, proving the underlying computation genuinely only happened on the first call.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `expensive` is a `Supplier<String>` whose body prints a message and returns `"result-42"` every time it's actually invoked. `cache(expensive)` is called once, which does **not** run `expensive`'s body — it only sets up the caching wrapper and returns a new `Supplier<String>` referencing `cached[0]` and `computed[0]`, both starting as `null`/`false`.

The first call, `cached.get()`, runs the wrapper lambda: `computed[0]` is `false`, so the `if` body executes — `original.get()` (calling `expensive`'s actual lambda body) runs for the first time, printing `"running expensive computation..."` and returning `"result-42"`, which is stored into `cached[0]`, and `computed[0]` is set to `true`. The cast `(T) cached[0]` retrieves `"result-42"` as the method's return value, printed as `"result-42"`.

The second call, `cached.get()`, runs the same wrapper lambda again: this time `computed[0]` is already `true`, so the `if` body is skipped entirely — `original.get()` is **not** called again, meaning `expensive`'s print statement does not run a second time. `cached[0]` still holds `"result-42"` from before, and that value is simply returned again.

The third call behaves identically to the second: `computed[0]` is still `true`, the cached value is returned directly, and `expensive`'s body is still never re-invoked.

```
cached.get() #1 --> computed[0]==false --> run expensive --> print + store "result-42" --> return it
cached.get() #2 --> computed[0]==true  --> skip expensive --> return stored "result-42"
cached.get() #3 --> computed[0]==true  --> skip expensive --> return stored "result-42"
```

This is why the output shows the expensive computation's print statement exactly once, followed by the same result printed three times — the `Supplier` returned by `cache` genuinely defers and then memoizes the underlying computation, calling the wrapped `Supplier` no more than once regardless of how many times its own `get()` is called.

## 7. Gotchas & takeaways

> A plain lambda `Supplier` is **not** automatically cached or memoized — calling `.get()` twice on an ordinary `Supplier` (without a wrapper like the one above) re-runs the entire lambda body both times, recomputing everything from scratch. If a value is genuinely expensive and only needs to be computed once, you need an explicit caching wrapper (as shown), or a dedicated memoizing utility — `Supplier` on its own only provides *deferral*, not *reuse*.

- `Supplier<T>` represents "no input, one output, computed on demand" — its single abstract method is `T get()`.
- Its defining benefit is laziness: the value isn't computed until `get()` is actually called, which can save real work when the value turns out not to be needed.
- `Optional.orElseGet(Supplier<T>)` is the classic example contrasting lazy (`Supplier`) versus eager (`Optional.orElse(T)`) fallback evaluation — prefer `orElseGet` whenever the fallback is expensive to compute.
- Logging frameworks commonly accept a `Supplier<String>` for a log message specifically so expensive message-building can be skipped entirely when that log level isn't active.
- A `Supplier` does not cache its result automatically — each call to `get()` re-runs the lambda body unless you deliberately wrap it in a caching/memoizing layer, as the `cache` helper above demonstrates.
