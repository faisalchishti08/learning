---
card: java
gi: 595
slug: optional-ifpresentorelse
title: Optional.ifPresentOrElse
---

## 1. What it is

`Optional.ifPresentOrElse` is a Java 9 terminal operation on `Optional` that accepts two callbacks: a `Consumer` that runs if the `Optional` contains a value, and a `Runnable` that runs if the `Optional` is empty. It replaces the common pattern of `if (opt.isPresent()) { ... } else { ... }` with a single fluent call, and it fills the gap left by Java 8's `ifPresent` — which only handled the "value present" case, forcing developers back to imperative `if`/`else` whenever they needed a fallback action for the empty case.

## 2. Why & when

Java 8's `Optional.ifPresent(Consumer)` was useful but incomplete: it only let you say "do this if the value exists." In real code, you almost always need both branches — the present case (use the value) and the empty case (log a warning, throw an exception, return a default, update a counter). Before Java 9, every such scenario required an explicit `if`/`else` block or a `map`/`orElseGet` chain, breaking the fluent style. `ifPresentOrElse` restores fluency by handling both cases in one expression, making the code read as "if there is a value, consume it; otherwise, run this fallback."

## 3. Core concept

```java
Optional<String> name = Optional.of("Alice");
Optional<String> missing = Optional.empty();

name.ifPresentOrElse(
    System.out::println,           // Consumer: runs when value is present
    () -> System.out.println("No name found")  // Runnable: runs when empty
);
// Output: Alice

missing.ifPresentOrElse(
    System.out::println,
    () -> System.out.println("No name found")
);
// Output: No name found
```

The first argument is a `Consumer<T>` — it receives the value if one exists. The second argument is a `Runnable` — it takes no arguments and runs only when the `Optional` is empty. Neither branch returns a value; `ifPresentOrElse` is a terminal operation, not a mapping operation.

## 4. Diagram

<svg viewBox="0 0 520 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Optional.ifPresentOrElse takes two lambdas — one for present, one for empty">
  <rect x="20" y="10" width="480" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="60" y="30" width="180" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="150" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">ifPresentOrElse(c, r)</text>

  <line x1="150" y1="70" x2="100" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="150" y1="70" x2="250" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <text x="85" y="82" fill="#8b949e" font-size="9" font-family="sans-serif">Value present</text>
  <text x="245" y="82" fill="#8b949e" font-size="9" font-family="sans-serif">Empty</text>

  <rect x="30" y="95" width="140" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="100" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">c.accept(value)</text>

  <rect x="210" y="95" width="140" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="280" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">r.run()</text>
</svg>

One call, two paths — the `Consumer` runs when the value exists, the `Runnable` runs when it doesn't.

## 5. Runnable example

Scenario: a user authentication system that looks up a user by ID and either loads their profile or records an access attempt by an unknown user — starting with a basic present/empty split, extending to real-world logging with both branches performing meaningful side effects, and finally handling the case where the fallback routine itself may throw and must be caught.

### Level 1 — Basic

```java
// File: IfPresentOrElseDemo.java
import java.util.Optional;

public class IfPresentOrElseDemo {
    public static void main(String[] args) {
        Optional<String> user = Optional.of("Alice");
        Optional<String> guest = Optional.empty();

        System.out.println("=== Registered user ===");
        user.ifPresentOrElse(
            name -> System.out.println("Welcome back, " + name + "!"),
            () -> System.out.println("Guest user — limited access")
        );

        System.out.println("=== Guest user ===");
        guest.ifPresentOrElse(
            name -> System.out.println("Welcome back, " + name + "!"),
            () -> System.out.println("Guest user — limited access")
        );
    }
}
```

**How to run:** `java IfPresentOrElseDemo.java`

Expected output:
```
=== Registered user ===
Welcome back, Alice!
=== Guest user ===
Guest user — limited access
```

The simplest pattern: replace `if (opt.isPresent()) { ... } else { ... }` with a single `ifPresentOrElse` call. The first `Optional` contains `"Alice"`, so the consumer runs and prints the personalised greeting. The second is empty, so the `Runnable` runs and prints the guest message.

### Level 2 — Intermediate

```java
// File: UserLookup.java
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;

public class UserLookup {
    record UserProfile(String id, String name, String role) {}

    private static final Map<String, UserProfile> DB = Map.of(
        "U1", new UserProfile("U1", "Alice",   "admin"),
        "U2", new UserProfile("U2", "Bob",     "editor"),
        "U3", new UserProfile("U3", "Charlie", "viewer")
    );

    private static final AtomicInteger failedLookups = new AtomicInteger(0);

    static void lookupAndLog(String userId) {
        Optional.ofNullable(DB.get(userId)).ifPresentOrElse(
            profile -> System.out.printf(
                "ACCESS: %s (%s) logged in as %s%n",
                profile.name(), profile.id(), profile.role()
            ),
            () -> {
                int count = failedLookups.incrementAndGet();
                System.out.printf(
                    "WARNING: Unknown user ID '%s' (total failed: %d)%n",
                    userId, count
                );
            }
        );
    }

    public static void main(String[] args) {
        lookupAndLog("U1");
        lookupAndLog("U99");
        lookupAndLog("U2");
        lookupAndLog("U42");
        lookupAndLog("U3");

        System.out.printf("%nTotal failed lookups: %d%n", failedLookups.get());
    }
}
```

**How to run:** `java UserLookup.java`

Expected output:
```
ACCESS: Alice (U1) logged in as admin
WARNING: Unknown user ID 'U99' (total failed: 1)
ACCESS: Bob (U2) logged in as editor
WARNING: Unknown user ID 'U42' (total failed: 2)
ACCESS: Charlie (U3) logged in as viewer

Total failed lookups: 2
```

The real-world concern added: both branches perform meaningful side effects. The present branch formats a structured access log entry. The empty branch logs a warning and atomically increments a failure counter — information that is used after the lookups complete to report the total number of failed attempts. `ifPresentOrElse` keeps both sides of the conditional in one block, so the reader sees the full "success or failure" story without scanning for a separate `else`.

### Level 3 — Advanced

```java
// File: SafeLookup.java
import java.util.Map;
import java.util.Optional;

public class SafeLookup {
    record UserProfile(String id, String name, String role) {}

    private static final Map<String, UserProfile> DB = Map.of(
        "U1", new UserProfile("U1", "Alice", "admin")
    );

    interface AuditLog {
        void record(String event);
    }

    static String resolveRole(String userId, AuditLog log) {
        return Optional.ofNullable(DB.get(userId))
            .map(UserProfile::role)
            .ifPresentOrElse(
                role -> { /* nothing — value flows to orElse via map */ },
                () -> log.record("MISSING_USER:" + userId)
            )
            .orElse("guest");
    }

    static String resolveRoleSafer(String userId, AuditLog log) {
        // The correct pattern: use map + orElseGet for the fallback value,
        // but use ifPresentOrElse for a side-effect-only empty action.
        // We don't need the return value from ifPresentOrElse when
        // map already transformed it to the role string.
        
        // Better approach: separate the side effect from the value computation
        Optional<UserProfile> maybe = Optional.ofNullable(DB.get(userId));
        maybe.ifPresentOrElse(
            p -> {},  // nothing to do — value will be extracted
            () -> log.record("MISSING_USER:" + userId)
        );
        return maybe.map(UserProfile::role).orElse("guest");
    }

    public static void main(String[] args) {
        AuditLog log = event -> System.out.println("  [AUDIT] " + event);

        System.out.println("Looking up U1 (exists):");
        System.out.println("  Role: " + resolveRoleSafer("U1", log));

        System.out.println("\nLooking up U99 (unknown):");
        System.out.println("  Role: " + resolveRoleSafer("U99", log));
    }
}
```

**How to run:** `java SafeLookup.java`

Expected output:
```
Looking up U1 (exists):
  Role: admin

Looking up U99 (unknown):
  [AUDIT] MISSING_USER:U99
  Role: guest
```

This handles the production-flavoured nuance: `ifPresentOrElse` is a void terminal operation — it does not return a value, so you cannot chain `.orElse(...)` directly on its result. The correct pattern separates the side-effect concern (logging) from the value-extraction concern (returning a role string). `maybe.ifPresentOrElse(...)` handles the logging side effect for the empty case, and a separate `maybe.map(UserProfile::role).orElse("guest")` handles the value extraction with a default. The audit log records every failed lookup while the main code path always receives a non-null role string.

## 6. Walkthrough

Tracing the Level 2 `lookupAndLog("U99")` call through its `ifPresentOrElse`:

1. `lookupAndLog("U99")` is called from `main`. The parameter `userId` is `"U99"`.

2. `Optional.ofNullable(DB.get("U99"))` executes: `DB` is the static `Map` of user IDs to profiles. `DB.get("U99")` looks up key `"U99"` — no such key exists, so `Map.get` returns `null`.

3. `Optional.ofNullable(null)` returns `Optional.empty()` — an `Optional` object with no contained value, internal state `present = false`.

4. `ifPresentOrElse(consumer, runnable)` is invoked on this empty `Optional`. The `Optional` checks its internal `present` flag:
   - `present` is `false` → the `Consumer` (first argument) is **not** invoked.
   - The `Runnable` (second argument) **is** invoked immediately.

5. The `Runnable` lambda executes:
   ```
   () -> {
       int count = failedLookups.incrementAndGet();
       System.out.printf("WARNING: Unknown user ID '%s' (total failed: %d)%n", userId, count);
   }
   ```
   - `failedLookups.incrementAndGet()` atomically increments the counter from its current value (say, 0) to 1 and returns 1.
   - The `printf` formats and prints the warning string with `userId="U99"` and `count=1`.

6. Control returns to `main`, where the next lookup proceeds.

For the successful case (`lookupAndLog("U1")`):

1. `DB.get("U1")` returns `UserProfile[U1, Alice, admin]` (non-null).
2. `Optional.ofNullable(...)` returns `Optional.of(profile)` with `present = true`.
3. `ifPresentOrElse` checks `present = true` → invokes the `Consumer` with the profile value.
4. The consumer formats `"ACCESS: Alice (U1) logged in as admin"` and prints it. The `Runnable` (empty-case fallback) is never invoked.

## 7. Gotchas & takeaways

> `ifPresentOrElse` is a **void** terminal operation — it returns `void`, not `Optional<T>`. This means you cannot chain `.orElse(...)`, `.map(...)`, or any other `Optional` method after it. If you need both a fallback *value* and a side effect (like logging), split the two concerns: use `ifPresentOrElse` for the side effect and a separate `.map().orElse()` for the return value, or use `.or(() -> { log(); return Optional.of(default); })` to embed the side effect in a value-producing chain.

- The second argument to `ifPresentOrElse` is a `Runnable`, not a `Consumer<T>` — it receives no argument because there is no value to pass when the `Optional` is empty.
- For the common pattern "use value if present, throw if empty," `ifPresentOrElse` can replace the verbose `opt.ifPresentOrElse(v -> process(v), () -> { throw new NotFoundException(); })`, but the simpler `opt.orElseThrow(() -> new NotFoundException())` is more readable for throw-only cases.
- `ifPresentOrElse` does not change the `Optional` — the `Optional` object is immutable and remains in the same state (present or empty) after the call.
- Both callbacks must be **side-effect-free** in the sense that they should not mutate shared state without proper synchronisation, though in practice logging and counter increment (as shown) are the standard use cases.
- The method name reads naturally as an English sentence: "if present, or else" — making the code self-documenting for the two-branch pattern. 