---
card: java
gi: 880
slug: completablefuture-chaining-thenapply-thenaccept-thencompose
title: CompletableFuture chaining (thenApply/thenAccept/thenCompose)
---

## 1. What it is

`thenApply`, `thenAccept`, and `thenCompose` all let you attach a follow-up step to a `CompletableFuture`, to run once it completes — without blocking to get the intermediate value first. `thenApply(Function<T,R>)` transforms the result into a new value, returning `CompletableFuture<R>` (like `map` on a stream). `thenAccept(Consumer<T>)` consumes the result for a side effect, returning `CompletableFuture<Void>` (nothing further to chain a *value* onto). `thenCompose(Function<T, CompletableFuture<R>>)` is for when the follow-up step is *itself* asynchronous and returns its own `CompletableFuture<R>` — it flattens the result instead of producing a `CompletableFuture<CompletableFuture<R>>` (like `flatMap` on a stream).

## 2. Why & when

Use `thenApply` for a plain, synchronous transformation of an already-available value (parsing a string, extracting a field, doing arithmetic) — cheap enough that it doesn't need its own async submission. Use `thenAccept` as the terminal step of a chain when you just need to consume the final result (print it, save it, send it) without producing anything further. Use `thenCompose` specifically when the next step is *another asynchronous operation* — fetching a user's ID, then using that ID to fetch their profile, is two dependent async steps; chaining them with `thenApply` would incorrectly produce a `CompletableFuture<CompletableFuture<Profile>>`, a future wrapping a future, which is almost never what you want and forces an awkward, nested unwrap. `thenCompose` is the tool that correctly sequences dependent asynchronous steps into a single, flat pipeline.

## 3. Core concept

```java
CompletableFuture<Integer> userIdFuture = CompletableFuture.supplyAsync(() -> lookupUserId("alice"));

// WRONG for a dependent async step -- produces CompletableFuture<CompletableFuture<Profile>>:
// userIdFuture.thenApply(id -> CompletableFuture.supplyAsync(() -> fetchProfile(id)));

// CORRECT: thenCompose flattens it into CompletableFuture<Profile>
CompletableFuture<Profile> profileFuture = userIdFuture.thenCompose(id ->
    CompletableFuture.supplyAsync(() -> fetchProfile(id)));

profileFuture
    .thenApply(profile -> profile.displayName().toUpperCase()) // synchronous transform
    .thenAccept(name -> System.out.println("Welcome, " + name + "!")); // terminal side effect
```

`thenApply` transforms in place; `thenCompose` sequences a *second* async operation without nesting futures; `thenAccept` ends the chain with a side effect.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chain: supplyAsync produces a user id, thenCompose sequences a dependent async fetch of the profile, thenApply transforms the name, thenAccept prints it">
  <rect x="10" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">supplyAsync -&gt; userId</text>

  <rect x="180" y="20" width="140" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="250" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thenCompose -&gt; profile</text>

  <rect x="350" y="20" width="130" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="415" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thenApply -&gt; name</text>

  <rect x="510" y="20" width="120" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="570" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thenAccept -&gt; print</text>

  <line x1="150" y1="40" x2="176" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a16)"/>
  <line x1="320" y1="40" x2="346" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a16)"/>
  <line x1="480" y1="40" x2="506" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a16)"/>

  <text x="320" y="90" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">thenCompose flattens the SECOND async step (fetchProfile) -- no nested futures</text>
  <defs><marker id="a16" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Each stage runs only after the previous one completes, without the calling thread ever blocking to check.*

## 5. Runnable example

Scenario: looking up a user by name, then fetching their profile, then formatting a welcome message, growing from a naive blocking chain, to a correctly `thenCompose`d async chain, to a version demonstrating the "nested future" bug from misusing `thenApply` and how `thenCompose` fixes it.

### Level 1 — Basic

```java
public class BlockingChain {
    record Profile(String displayName) {}

    static int lookupUserId(String username) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return username.hashCode() & 0xFFFF;
    }

    static Profile fetchProfile(int userId) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return new Profile("Alice_" + userId);
    }

    public static void main(String[] args) {
        int id = lookupUserId("alice");       // blocks
        Profile profile = fetchProfile(id);    // blocks AGAIN, sequentially
        String name = profile.displayName().toUpperCase();
        System.out.println("Welcome, " + name + "!");
    }
}
```

**How to run:** `java BlockingChain.java` (JDK 17+).

Expected output:
```
Welcome, ALICE_63... !
```

(Exact number varies by hash.) Correct, but every step blocks the calling thread sequentially — no concurrency, and no way to react to completion without stopping and waiting at each stage.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class ThenComposeChain {
    record Profile(String displayName) {}

    static int lookupUserId(String username) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return username.hashCode() & 0xFFFF;
    }

    static Profile fetchProfile(int userId) {
        try { Thread.sleep(50); } catch (InterruptedException ignored) {}
        return new Profile("Alice_" + userId);
    }

    public static void main(String[] args) {
        CompletableFuture<Void> chain = CompletableFuture
            .supplyAsync(() -> lookupUserId("alice"))
            .thenCompose(id -> CompletableFuture.supplyAsync(() -> fetchProfile(id))) // dependent async step, flattened
            .thenApply(profile -> profile.displayName().toUpperCase())                 // synchronous transform
            .thenAccept(name -> System.out.println("Welcome, " + name + "!"));         // terminal side effect

        chain.join(); // wait for the whole pipeline to finish (only needed here so main doesn't exit early)
    }
}
```

**How to run:** `java ThenComposeChain.java`.

Expected output:
```
Welcome, ALICE_63... !
```

The real-world concern added: the entire pipeline is now built declaratively and runs asynchronously — no thread blocks at any intermediate step; `thenCompose` correctly sequences the *second* async operation (`fetchProfile`, itself wrapped in its own `supplyAsync`) without producing a nested future.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class NestedFutureBugAndFix {
    record Profile(String displayName) {}

    static int lookupUserId(String username) {
        try { Thread.sleep(30); } catch (InterruptedException ignored) {}
        return username.hashCode() & 0xFFFF;
    }

    static Profile fetchProfile(int userId) {
        try { Thread.sleep(30); } catch (InterruptedException ignored) {}
        return new Profile("Alice_" + userId);
    }

    public static void main(String[] args) throws Exception {
        // BUGGY: thenApply with a lambda that RETURNS a CompletableFuture produces a
        // CompletableFuture<CompletableFuture<Profile>> -- a future wrapping a future.
        CompletableFuture<CompletableFuture<Profile>> nested = CompletableFuture
            .supplyAsync(() -> lookupUserId("alice"))
            .thenApply(id -> CompletableFuture.supplyAsync(() -> fetchProfile(id))); // WRONG combinator

        // To use it, you'd have to awkwardly unwrap TWICE:
        Profile awkward = nested.get().get(); // .get() on the outer, then .get() on the inner
        System.out.println("awkward double-unwrap result: " + awkward.displayName());

        // FIXED: thenCompose flattens automatically -- one future, one .get()
        CompletableFuture<Profile> flat = CompletableFuture
            .supplyAsync(() -> lookupUserId("alice"))
            .thenCompose(id -> CompletableFuture.supplyAsync(() -> fetchProfile(id))); // CORRECT combinator

        Profile clean = flat.get(); // single, clean unwrap
        System.out.println("clean thenCompose result: " + clean.displayName());
    }
}
```

**How to run:** `java NestedFutureBugAndFix.java`.

Expected output shape (names vary by hash, but demonstrate the structural difference):
```
awkward double-unwrap result: Alice_...
clean thenCompose result: Alice_...
```

This adds the production-flavored hard case: explicitly demonstrating the "nested future" bug that results from using `thenApply` (meant for a synchronous transform) with a lambda that itself returns a `CompletableFuture` — the type system faithfully reflects the mistake by producing `CompletableFuture<CompletableFuture<Profile>>`, requiring an awkward double `.get()` to unwrap. `thenCompose` exists precisely to avoid ever needing that double-unwrap: it recognizes the lambda returns a future and flattens the result into a single-level `CompletableFuture<Profile>`.

## 6. Walkthrough

Tracing the `flat` pipeline in `NestedFutureBugAndFix.main`:

1. `CompletableFuture.supplyAsync(() -> lookupUserId("alice"))` starts running `lookupUserId` on a common-pool thread and immediately returns a `CompletableFuture<Integer>` — `main` does not block here.
2. `.thenCompose(id -> CompletableFuture.supplyAsync(() -> fetchProfile(id)))` registers a callback: once the `Integer` (user ID) is ready, the callback runs, itself calling `supplyAsync` to start `fetchProfile` on another common-pool thread — this inner call returns its own `CompletableFuture<Profile>`.
3. Because the outer combinator is `thenCompose` (not `thenApply`), the framework recognizes the callback's return type is itself a `CompletableFuture<Profile>` and **flattens** it — the overall `flat` variable's type is `CompletableFuture<Profile>`, not `CompletableFuture<CompletableFuture<Profile>>`.
4. `flat.get()` blocks until the *entire* two-step chain (lookup, then fetch) has completed, and returns the final `Profile` object directly — one call, one unwrap.
5. Contrast this with `nested` above: because `thenApply` does *not* flatten, `nested.get()` only unwraps the *outer* future, itself yielding another, still-possibly-incomplete `CompletableFuture<Profile>` — a second `.get()` is required to actually reach the `Profile`, and that's the awkward double-unwrap explicitly shown.
6. Both approaches produce the same final `Profile` value eventually, but `thenCompose`'s single, flat future is the version you'd actually want to continue chaining further steps onto (via more `thenApply`/`thenCompose` calls) without accumulating additional levels of nesting.

## 7. Gotchas & takeaways

> **Gotcha:** if the function you pass to `thenApply` returns a `CompletableFuture`, you've almost certainly picked the wrong combinator — you'll end up with a nested `CompletableFuture<CompletableFuture<T>>` that needs an awkward double-unwrap. Reach for `thenCompose` any time the next step is itself asynchronous.

- `thenApply`: synchronous transform of an already-available result — like `map`.
- `thenAccept`: terminal, side-effecting consumption of the result, produces `CompletableFuture<Void>` — nothing further to chain a value onto.
- `thenCompose`: sequences a *second*, dependent asynchronous operation, flattening the result — like `flatMap`; use this whenever your transform function itself returns a `CompletableFuture`.
- None of `thenApply`/`thenAccept`/`thenCompose` block the calling thread — they register callbacks that run once the prior stage completes, on whichever thread the runtime chooses (often the thread that completed the previous stage, unless you use the `*Async` variants with an explicit executor).
- For combining two or more *independent* futures (not a dependent sequence) into one result, see [`thenCombine`/`allOf`/`anyOf`](0881-completablefuture-combining-thencombine-allof-anyof.md) instead — chaining is for sequential dependency, combining is for parallel independence.
