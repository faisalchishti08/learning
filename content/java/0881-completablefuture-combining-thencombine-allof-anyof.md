---
card: java
gi: 881
slug: completablefuture-combining-thencombine-allof-anyof
title: CompletableFuture combining (thenCombine/allOf/anyOf)
---

## 1. What it is

`thenCombine` merges the results of exactly **two** independent `CompletableFuture`s into one, via a `BiFunction`, once *both* have completed. `CompletableFuture.allOf(futures...)` waits for **all** of an arbitrary number of futures to complete, returning `CompletableFuture<Void>` (it deliberately discards individual results — you retrieve them from the original futures once `allOf` completes). `CompletableFuture.anyOf(futures...)` completes as soon as **any one** of the given futures completes, returning `CompletableFuture<Object>` with whichever one finished first (or fastest).

## 2. Why & when

Use `thenCombine` when exactly two independent asynchronous operations both need to finish before you can compute something from both of their results together — fetching a user's profile and their account balance concurrently, then combining them into a dashboard view. Use `allOf` when you have a variable-length list of independent futures (fetching prices for N stock symbols) and need to wait for every one before proceeding, typically followed by mapping over the original list to collect each individual `join()`ed result. Use `anyOf` when you only need the *first* of several redundant or competing operations to finish — similar in spirit to [`CompletionService`](0878-completionservice.md), but expressed as a single composable future rather than a queue you poll. All three let independent work run genuinely in parallel, only synchronizing at the point where you actually need combined results.

## 3. Core concept

```java
CompletableFuture<Integer> priceFuture = CompletableFuture.supplyAsync(() -> fetchPrice("AAPL"));
CompletableFuture<Integer> quantityFuture = CompletableFuture.supplyAsync(() -> fetchQuantity("AAPL"));

CompletableFuture<Integer> totalFuture = priceFuture.thenCombine(quantityFuture, (price, qty) -> price * qty);

List<CompletableFuture<Integer>> allPrices = symbols.stream()
    .map(s -> CompletableFuture.supplyAsync(() -> fetchPrice(s)))
    .toList();
CompletableFuture<Void> allDone = CompletableFuture.allOf(allPrices.toArray(new CompletableFuture[0]));
allDone.join(); // now every future in allPrices is guaranteed complete
List<Integer> results = allPrices.stream().map(CompletableFuture::join).toList(); // safe, non-blocking join
```

`thenCombine` needs exactly two futures and a merge function; `allOf`/`anyOf` work over an arbitrary array and return no useful typed result of their own — they're synchronization points you use alongside the original list of futures.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two independent futures running concurrently, combined via thenCombine into one result once both complete; separately, allOf waits for a list of N futures, anyOf completes as soon as the first of several finishes">
  <rect x="20" y="20" width="140" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">priceFuture</text>
  <rect x="20" y="65" width="140" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="90" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">quantityFuture</text>
  <rect x="220" y="42" width="150" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="295" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">thenCombine -&gt; total</text>
  <line x1="160" y1="37" x2="216" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a17)"/>
  <line x1="160" y1="82" x2="216" y2="65" stroke="#8b949e" stroke-width="2" marker-end="url(#a17)"/>

  <text x="500" y="15" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">allOf: waits for ALL N</text>
  <rect x="420" y="25" width="30" height="20" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="460" y="25" width="30" height="20" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="500" y="25" width="30" height="20" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="560" y="20" width="60" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="590" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">all done</text>

  <text x="500" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">anyOf: first of N wins</text>
  <rect x="420" y="110" width="30" height="20" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <rect x="460" y="110" width="30" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="500" y="110" width="30" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2"/>
  <rect x="560" y="105" width="60" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="590" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1st wins</text>

  <defs><marker id="a17" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*`thenCombine` merges exactly two; `allOf` waits for every one of N; `anyOf` proceeds as soon as one of N finishes.*

## 5. Runnable example

Scenario: building a stock trade summary, growing from sequential fetching, to `thenCombine` for two independent values, to `allOf` over a variable-length list of symbol lookups plus `anyOf` racing two redundant price feeds for the freshest quote.

### Level 1 — Basic

```java
public class SequentialFetch {
    static int fetchPrice(String symbol) {
        try { Thread.sleep(80); } catch (InterruptedException ignored) {}
        return 100 + Math.abs(symbol.hashCode() % 50);
    }
    static int fetchQuantity(String symbol) {
        try { Thread.sleep(60); } catch (InterruptedException ignored) {}
        return 10 + Math.abs(symbol.hashCode() % 5);
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        int price = fetchPrice("AAPL");       // blocks 80ms
        int quantity = fetchQuantity("AAPL");  // blocks ANOTHER 60ms, sequentially
        System.out.println("total value = " + (price * quantity));
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (sequential: ~140ms)");
    }
}
```

**How to run:** `java SequentialFetch.java` (JDK 17+).

Expected output shape:
```
total value = ...
elapsed ~140ms (sequential: ~140ms)
```

Correct, but the two independent fetches (price, quantity) are needlessly serialized — nothing about `fetchQuantity` actually depends on `fetchPrice`'s result.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class ThenCombineParallel {
    static int fetchPrice(String symbol) {
        try { Thread.sleep(80); } catch (InterruptedException ignored) {}
        return 100 + Math.abs(symbol.hashCode() % 50);
    }
    static int fetchQuantity(String symbol) {
        try { Thread.sleep(60); } catch (InterruptedException ignored) {}
        return 10 + Math.abs(symbol.hashCode() % 5);
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();

        CompletableFuture<Integer> priceFuture = CompletableFuture.supplyAsync(() -> fetchPrice("AAPL"));
        CompletableFuture<Integer> quantityFuture = CompletableFuture.supplyAsync(() -> fetchQuantity("AAPL"));

        CompletableFuture<Integer> totalFuture = priceFuture.thenCombine(quantityFuture, (price, qty) -> price * qty);

        System.out.println("total value = " + totalFuture.join());
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (parallel: ~80ms, the slower of the two)");
    }
}
```

**How to run:** `java ThenCombineParallel.java`.

Expected output shape:
```
total value = ...
elapsed ~80ms (parallel: ~80ms, the slower of the two)
```

The real-world concern added: both independent fetches now run concurrently, and `thenCombine` merges their results the instant both are ready — total elapsed time drops to roughly the slower of the two calls (80ms) instead of their sum (140ms).

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class AllOfAndAnyOf {
    static int fetchPrice(String symbol, int delayMs) {
        try { Thread.sleep(delayMs); } catch (InterruptedException ignored) {}
        return 100 + Math.abs(symbol.hashCode() % 50);
    }

    public static void main(String[] args) {
        // allOf: fetch prices for an arbitrary-length list of symbols, wait for ALL of them
        List<String> symbols = List.of("AAPL", "GOOG", "MSFT", "AMZN");
        List<CompletableFuture<Integer>> priceFutures = symbols.stream()
            .map(s -> CompletableFuture.supplyAsync(() -> fetchPrice(s, 50)))
            .toList();

        CompletableFuture<Void> allDone = CompletableFuture.allOf(
            priceFutures.toArray(new CompletableFuture[0]));
        allDone.join(); // blocks until EVERY symbol's price is ready

        List<Integer> allPrices = priceFutures.stream().map(CompletableFuture::join).toList();
        System.out.println("all prices (allOf): " + allPrices);

        // anyOf: race two redundant feeds for the SAME symbol, take whichever responds first
        CompletableFuture<Integer> feedA = CompletableFuture.supplyAsync(() -> fetchPrice("AAPL-feedA", 200));
        CompletableFuture<Integer> feedB = CompletableFuture.supplyAsync(() -> fetchPrice("AAPL-feedB", 30));

        CompletableFuture<Object> fastest = CompletableFuture.anyOf(feedA, feedB);
        System.out.println("fastest feed's price (anyOf): " + fastest.join());
    }
}
```

**How to run:** `java AllOfAndAnyOf.java`.

Expected output shape (allPrices values are deterministic given the hashes; anyOf's result matches feedB's, since it's the faster of the two):
```
all prices (allOf): [..., ..., ..., ...]
fastest feed's price (anyOf): ...
```

This adds the production-flavored hard case: `allOf` over a genuinely variable-length list of futures (four symbols, but the code works for any number), correctly waiting for all before collecting each individual result via `join()` (safe to call without blocking further, since `allDone.join()` already guaranteed completion) — and separately, `anyOf` racing two redundant price feeds and completing with whichever's result arrives first, discarding the slower one's eventual result entirely.

## 6. Walkthrough

Tracing the `allOf` portion of `AllOfAndAnyOf.main`:

1. `symbols.stream().map(...)` creates four independent `CompletableFuture<Integer>`s, each running `fetchPrice` concurrently on the common pool — none of them block `main` at this point.
2. `CompletableFuture.allOf(priceFutures.toArray(...))` returns a `CompletableFuture<Void>` that will complete only once **every** one of the four input futures has completed — internally, it registers a completion callback on each and completes itself when the last one finishes.
3. `allDone.join()` blocks `main` until that condition is met — since all four fetches run concurrently with the same 50ms delay, this takes roughly 50ms total, not 200ms.
4. Because `allDone` has now completed, it's guaranteed every future in `priceFutures` is also complete — the subsequent `.map(CompletableFuture::join)` calls are safe and return instantly, no additional waiting, just retrieving each already-computed value.
5. For the `anyOf` portion: `feedA` (200ms delay) and `feedB` (30ms delay) both start concurrently; `CompletableFuture.anyOf(feedA, feedB)` returns a `CompletableFuture<Object>` that completes the instant *either* input completes — since `feedB` finishes first (30ms vs. 200ms), `fastest` completes with `feedB`'s result.
6. `fastest.join()` returns that value immediately once available (around the 30ms mark) — `feedA`'s still-pending 200ms computation continues running in the background but its eventual result is never retrieved or used by this code.

## 7. Gotchas & takeaways

> **Gotcha:** `allOf` returns `CompletableFuture<Void>` — it deliberately does not give you the individual results directly. You must keep a reference to the original list of futures and call `join()` (or `get()`) on each one yourself after `allOf` completes, exactly as `AllOfAndAnyOf` does with `priceFutures`.

- `thenCombine` merges exactly two independent futures via a `BiFunction`, once both complete — for anything other than exactly two, use `allOf`/`anyOf` instead.
- `allOf` waits for every future in an arbitrary-length collection to complete, but discards their individual results — retrieve those from your original list of futures afterward.
- `anyOf` completes as soon as the first of several futures completes, discarding the rest — useful for racing redundant, competing operations, similar in spirit to [`CompletionService`](0878-completionservice.md) but expressed as a single future.
- All three combinators only synchronize at the point you actually need combined or complete results — the underlying operations still run genuinely in parallel up until then.
- Futures whose results are discarded by `anyOf` (the "losing" ones) keep running to completion in the background unless you explicitly `cancel()` them — consider doing so if their work is expensive and truly no longer needed.
