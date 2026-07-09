---
card: java
gi: 535
slug: ifpresent
title: ifPresent()
---

## 1. What it is

`Optional.ifPresent(consumer)` runs the given `Consumer<T>` on the held value, but only if the `Optional` actually holds one — if it's empty, nothing happens at all, no exception, no action. `Optional.ifPresentOrElse(consumer, emptyAction)` (Java 9+) extends this with a second branch: a `Runnable` that runs specifically when the `Optional` is empty, letting you express both "what to do with a present value" and "what to do when there isn't one" in a single expression.

## 2. Why & when

`ifPresent` collapses the `isPresent()`/`get()` pattern (see [[ispresent-get]]) into one call: the value is only ever handed to your code inside the consumer, and only when it's genuinely there — there's no separate `get()` call to accidentally run unguarded. It's the natural choice whenever you want to *act* on a present value (print it, save it, pass it elsewhere) without needing a return value from that action, and you're fine with silently doing nothing when the `Optional` is empty. `ifPresentOrElse` extends this to cases where "doing nothing" isn't quite right — you want an explicit fallback action instead.

## 3. Core concept

```java
import java.util.*;

Optional<String> username = Optional.of("alice");

username.ifPresent(name -> System.out.println("Welcome, " + name)); // runs -- value is present

Optional<String> empty = Optional.empty();
empty.ifPresent(name -> System.out.println("Welcome, " + name)); // does nothing -- no exception either

username.ifPresentOrElse(
        name -> System.out.println("Welcome, " + name),
        () -> System.out.println("No user logged in"));
```

`ifPresent` runs its consumer only when a value exists; `ifPresentOrElse` adds an explicit alternative action for when it doesn't, both without ever risking an unguarded `get()` call.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ifPresent runs its consumer only when a value exists; ifPresentOrElse also runs a fallback when empty">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="105" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Optional[alice]</text>
  <line x1="180" y1="35" x2="260" y2="35" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowIF)"/>
  <rect x="270" y="20" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="360" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">consumer runs: "Welcome, alice"</text>

  <rect x="30" y="65" width="150" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="105" y="85" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Optional.empty</text>
  <line x1="180" y1="80" x2="260" y2="80" stroke="#8b949e" stroke-width="2" marker-end="url(#arrowIF2)"/>
  <rect x="270" y="65" width="180" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="360" y="85" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">emptyAction runs (ifPresentOrElse)</text>
  <defs>
    <marker id="arrowIF" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrowIF2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`ifPresent`'s consumer only runs on a present value; `ifPresentOrElse` additionally routes to a specific action when the `Optional` is empty.

## 5. Runnable example

Scenario: sending a welcome notification to a user, if one is currently logged in — evolved from a plain `ifPresent` action, through `ifPresentOrElse` with a distinct fallback, to a version chaining `ifPresent` on the result of a lookup pipeline to trigger multiple downstream actions.

### Level 1 — Basic

```java
import java.util.*;

public class IfPresentBasic {
    public static void main(String[] args) {
        Optional<String> loggedInUser = Optional.of("alice");
        Optional<String> noUser = Optional.empty();

        loggedInUser.ifPresent(name -> System.out.println("Welcome back, " + name + "!"));
        noUser.ifPresent(name -> System.out.println("Welcome back, " + name + "!")); // silently does nothing

        System.out.println("Done checking both.");
    }
}
```

**How to run:** `java IfPresentBasic.java`

Expected output:
```
Welcome back, alice!
Done checking both.
```

`loggedInUser.ifPresent(...)` runs the consumer since a value is present, printing the welcome message. `noUser.ifPresent(...)` does absolutely nothing — no output, no exception — since `noUser` is empty; execution simply continues to the next line.

### Level 2 — Intermediate

```java
import java.util.*;

public class IfPresentOrElseBasic {
    public static void main(String[] args) {
        Optional<String> loggedInUser = Optional.of("alice");
        Optional<String> noUser = Optional.empty();

        loggedInUser.ifPresentOrElse(
                name -> System.out.println("Welcome back, " + name + "!"),
                () -> System.out.println("Please log in to continue."));

        noUser.ifPresentOrElse(
                name -> System.out.println("Welcome back, " + name + "!"),
                () -> System.out.println("Please log in to continue."));
    }
}
```

**How to run:** `java IfPresentOrElseBasic.java`

Expected output:
```
Welcome back, alice!
Please log in to continue.
```

The real-world concern this adds: a genuine fallback action is now needed for the empty case, rather than silence. `ifPresentOrElse(...)` runs exactly one of its two arguments per call — the `Consumer` when present, the `Runnable` when empty — expressing both branches of the logic in a single, self-contained call, with no separate `if`/`else` structure needed.

### Level 3 — Advanced

```java
import java.util.*;

public class IfPresentChained {
    record User(String username, boolean emailVerified) {}

    static final Map<String, User> USERS = Map.of(
            "alice", new User("alice", true),
            "bob", new User("bob", false)
    );

    static Optional<User> findUser(String username) {
        return Optional.ofNullable(USERS.get(username));
    }

    static List<String> notificationLog = new ArrayList<>();

    public static void main(String[] args) {
        // Chain: find the user, then only act if they exist AND their email is verified.
        findUser("alice")
                .filter(User::emailVerified)
                .ifPresentOrElse(
                        user -> notificationLog.add("Sent welcome email to " + user.username()),
                        () -> notificationLog.add("Skipped: alice not found or email not verified"));

        findUser("bob")
                .filter(User::emailVerified)
                .ifPresentOrElse(
                        user -> notificationLog.add("Sent welcome email to " + user.username()),
                        () -> notificationLog.add("Skipped: bob not found or email not verified"));

        findUser("carol") // doesn't exist at all
                .filter(User::emailVerified)
                .ifPresentOrElse(
                        user -> notificationLog.add("Sent welcome email to " + user.username()),
                        () -> notificationLog.add("Skipped: carol not found or email not verified"));

        notificationLog.forEach(System.out::println);
    }
}
```

**How to run:** `java IfPresentChained.java`

Expected output:
```
Sent welcome email to alice
Skipped: bob not found or email not verified
Skipped: carol not found or email not verified
```

This chains `findUser(...)` with `.filter(User::emailVerified)` (see [[map-flatmap-filter]]) before `ifPresentOrElse`, so the final action reflects **two** combined conditions: the user must exist *and* have a verified email. `alice` satisfies both, triggering the welcome-email branch. `bob` exists but has `emailVerified = false`, so `.filter(...)` turns his present `Optional` into an empty one, triggering the skip branch. `carol` doesn't exist at all — `findUser` already returns an empty `Optional`, so `.filter(...)` has nothing to filter, and the same skip branch runs, though for a different underlying reason.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `USERS` maps `"alice"` to a verified user and `"bob"` to an unverified one; `"carol"` isn't in the map at all.

For the first call, `findUser("alice")` returns `Optional.ofNullable(USERS.get("alice"))` — since `"alice"` maps to a `User`, this is `Optional.of(User("alice", true))`. `.filter(User::emailVerified)` checks the predicate against the held `User`: `emailVerified()` is `true`, so the predicate passes and the `Optional` remains `Optional.of(User("alice", true))`, unchanged. `.ifPresentOrElse(...)` sees a present value, so it runs the first lambda: `notificationLog.add("Sent welcome email to alice")`.

For the second call, `findUser("bob")` returns `Optional.of(User("bob", false))`. `.filter(User::emailVerified)` checks `emailVerified()`, which is `false` — since the predicate fails, `.filter(...)` returns `Optional.empty()`, discarding the held `User` entirely, even though it was present a moment ago. `.ifPresentOrElse(...)` now sees an empty `Optional`, so it runs the second lambda (the `Runnable`): `notificationLog.add("Skipped: bob not found or email not verified")`.

For the third call, `findUser("carol")` returns `Optional.ofNullable(USERS.get("carol"))` — since `"carol"` isn't a key in `USERS`, `USERS.get("carol")` is `null`, so this is `Optional.empty()` from the very start. `.filter(User::emailVerified)` on an already-empty `Optional` has nothing to test the predicate against, so it simply remains `Optional.empty()`. `.ifPresentOrElse(...)` runs the fallback: `notificationLog.add("Skipped: carol not found or email not verified")`.

```
alice: findUser -> present(verified=true)  -> filter passes -> present -> "Sent welcome email to alice"
bob:   findUser -> present(verified=false) -> filter FAILS  -> empty   -> "Skipped: bob..."
carol: findUser -> empty (not in map)      -> filter has nothing to check -> stays empty -> "Skipped: carol..."
```

After all three calls, `notificationLog` holds three entries in order, and `notificationLog.forEach(System.out::println)` prints each on its own line — exactly reflecting each user's outcome, even though `bob` and `carol` both end up in the "skipped" branch for entirely different reasons (existing-but-unverified versus not-existing-at-all).

## 7. Gotchas & takeaways

> `ifPresent`'s consumer runs purely for its side effect and returns nothing — you cannot use `ifPresent` to compute and return a transformed value out of the `Optional`'s contents; for that, `map(...)` (see [[map-flatmap-filter]]) is the appropriate tool. Reaching for `ifPresent` when you actually need a return value (e.g. trying to assign a variable from inside the consumer lambda, which requires it to be effectively final and doesn't actually propagate the result out) is a common early mistake.

- `ifPresent(consumer)` runs its consumer only when a value is present; does nothing (no exception) when empty.
- `ifPresentOrElse(consumer, emptyAction)` (Java 9+) adds an explicit fallback `Runnable` for the empty case, expressing both branches in one call.
- Both structurally prevent the "check, then separately call `get()`" pattern's fragility, since the value is only ever passed into the consumer when genuinely present.
- Chaining `.filter(...)` before `ifPresent`/`ifPresentOrElse` lets you express additional conditions beyond mere presence, turning a present-but-unsatisfying value into an empty `Optional` before the final action runs.
- Since `ifPresent`'s consumer returns nothing, it's for side effects only — use `map`/`orElse`/`orElseThrow` when you need to compute and return a value derived from the `Optional`'s contents instead.
