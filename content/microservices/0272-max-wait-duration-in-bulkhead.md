---
card: microservices
gi: 272
slug: max-wait-duration-in-bulkhead
title: "Max wait duration in bulkhead"
---

## 1. What it is

Max wait duration is a [bulkhead](0267-bulkhead-pattern.md) configuration option controlling what happens when a call arrives while the bulkhead is already at full [max concurrent calls](0271-max-concurrent-calls.md) capacity: rather than rejecting the call immediately (a wait duration of zero), the caller can be allowed to wait briefly, up to the configured maximum, for a slot to free up before finally being rejected if none becomes available in time.

## 2. Why & when

Immediate rejection the instant a bulkhead is at capacity is the simplest, safest default, but it can be needlessly aggressive for a brief, momentary spike where a slot is very likely to free up within a short time — an in-flight call finishing a moment later, freeing its slot for a waiting caller almost immediately, rather than that caller being rejected outright for a capacity constraint that resolved itself within milliseconds. A small, non-zero max wait duration absorbs this kind of brief burst gracefully, giving waiting callers a real chance to succeed rather than an automatic rejection, while a wait duration of zero (or a very small one) keeps the bulkhead's behavior close to its strongest, most protective form — no waiting at all, immediate feedback.

Set a small, non-zero max wait duration when brief capacity spikes are common and a short wait is preferable to an immediate rejection for calls likely to succeed shortly after. Keep the wait duration at zero (immediate rejection) when the calling code has its own fast, effective fallback and prefers instant feedback over any waiting at all, or when waiting itself risks accumulating queued callers in a way the bulkhead's whole design was meant to avoid.

## 3. Core concept

A non-zero max wait duration makes the bulkhead's acquisition attempt blocking (up to that duration) rather than purely non-blocking — the caller either acquires a slot within the wait window (because one freed up in time) or is rejected once the wait duration elapses without success, exactly mirroring the semaphore's own timed-acquire semantics.

```java
Semaphore bulkheadPermits = new Semaphore(10);

<T> T callWithBulkhead(Supplier<T> operation, Duration maxWaitDuration) throws Exception {
    boolean acquired = bulkheadPermits.tryAcquire(maxWaitDuration.toMillis(), TimeUnit.MILLISECONDS); // WAITS up to this long
    if (!acquired) throw new BulkheadFullException("no slot became available within " + maxWaitDuration);
    try {
        return operation.get();
    } finally {
        bulkheadPermits.release();
    }
}
// maxWaitDuration = ZERO: reject IMMEDIATELY if no slot is free (the strictest, most protective default)
// maxWaitDuration = a SHORT duration: give a BRIEF chance for a slot to free up before rejecting
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="With a zero wait duration, a caller arriving when the bulkhead is full is rejected instantly; with a short non-zero wait duration, the same caller waits briefly, and if a slot frees up within that window, the call proceeds instead of being rejected" >
  <rect x="20" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Wait duration = 0</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">rejected INSTANTLY if bulkhead full</text>

  <rect x="350" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Wait duration &gt; 0</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">waits briefly; a freed slot AVOIDS rejection</text>
</svg>

A brief wait window can absorb a short-lived spike that would otherwise cause an unnecessary rejection.

## 5. Runnable example

Scenario: a bulkhead configured with zero wait duration that rejects a call outright even though a slot frees up almost immediately afterward, refactored to a short, non-zero wait duration that catches that exact same brief opening and admits the call successfully, and finally demonstrating a wait duration that's too long, tying up a waiting caller for an unreasonably long time when the bulkhead never actually frees up within a sensible window.

### Level 1 — Basic

```java
// File: ZeroWaitRejectsInstantly.java -- a WAIT DURATION of ZERO --
// REJECTS immediately, even though a slot frees up MOMENTS later.
import java.util.concurrent.*;

public class ZeroWaitRejectsInstantly {
    static Semaphore bulkhead = new Semaphore(1); // capacity of ONE, for a clear demo

    public static void main(String[] args) throws InterruptedException {
        bulkhead.acquire(); // ONE slot occupied by an in-flight call
        new Thread(() -> {
            try { Thread.sleep(50); bulkhead.release(); } catch (InterruptedException ignored) {} // frees up in 50ms
        }).start();

        boolean acquiredImmediately = bulkhead.tryAcquire(); // ZERO wait -- checks ONCE, instantly
        System.out.println("Immediate acquisition attempt: " + (acquiredImmediately ? "SUCCEEDED" : "REJECTED -- even though a slot frees up in just 50ms!"));
    }
}
```

**How to run:** `javac ZeroWaitRejectsInstantly.java && java ZeroWaitRejectsInstantly` (JDK 17+).

Expected output:
```
Immediate acquisition attempt: REJECTED -- even though a slot frees up in just 50ms!
```

### Level 2 — Intermediate

```java
// File: ShortWaitCatchesTheOpening.java -- a SHORT, non-zero wait
// duration -- catches the SAME brief opening Level 1 missed entirely.
import java.util.concurrent.*;

public class ShortWaitCatchesTheOpening {
    static Semaphore bulkhead = new Semaphore(1);

    public static void main(String[] args) throws InterruptedException {
        bulkhead.acquire();
        new Thread(() -> {
            try { Thread.sleep(50); bulkhead.release(); } catch (InterruptedException ignored) {} // SAME 50ms delay as Level 1
        }).start();

        long start = System.currentTimeMillis();
        boolean acquiredWithWait = bulkhead.tryAcquire(200, TimeUnit.MILLISECONDS); // WAITS up to 200ms
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("With a 200ms wait window: " + (acquiredWithWait ? "SUCCEEDED after ~" + elapsed + "ms -- caught the slot as it freed up!" : "still rejected"));
    }
}
```

**How to run:** `javac ShortWaitCatchesTheOpening.java && java ShortWaitCatchesTheOpening` (JDK 17+).

Expected output (timing approximate):
```
With a 200ms wait window: SUCCEEDED after ~50ms -- caught the slot as it freed up!
```

### Level 3 — Advanced

```java
// File: ExcessiveWaitTiesUpCallerNeedlessly.java -- a WAIT DURATION set
// TOO LONG -- ties up a caller for an UNREASONABLY long time when the
// bulkhead genuinely never frees up within a sensible window.
import java.util.concurrent.*;

public class ExcessiveWaitTiesUpCallerNeedlessly {
    static Semaphore bulkhead = new Semaphore(1);

    public static void main(String[] args) throws InterruptedException {
        bulkhead.acquire(); // held for the ENTIRE duration of this demo -- simulates a GENUINELY stuck/overloaded dependency

        long start = System.currentTimeMillis();
        boolean acquired = bulkhead.tryAcquire(2000, TimeUnit.MILLISECONDS); // an EXCESSIVELY long 2-second wait
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Waited " + elapsed + "ms before finally giving up (acquired=" + acquired + ").");
        System.out.println("The CALLER's own thread was tied up for the FULL " + elapsed + "ms, waiting for a slot that NEVER actually freed --");
        System.out.println("an excessively long wait duration turns the bulkhead's protection into its OWN source of unresponsiveness.");
    }
}
```

**How to run:** `javac ExcessiveWaitTiesUpCallerNeedlessly.java && java ExcessiveWaitTiesUpCallerNeedlessly` (JDK 17+).

Expected output (timing approximate, ~2000ms):
```
Waited 2000ms before finally giving up (acquired=false).
The CALLER's own thread was tied up for the FULL 2000ms, waiting for a slot that NEVER actually freed --
an excessively long wait duration turns the bulkhead's protection into its OWN source of unresponsiveness.
```

## 6. Walkthrough

1. **Level 1, the missed opportunity** — `bulkhead.tryAcquire()` (with no wait argument) checks for an available permit exactly once, instantaneously, and returns `false` immediately since the one permit is currently held by the in-flight call; the background thread releasing that permit 50ms later happens completely independently, with no chance for the already-rejected caller to benefit from it.
2. **Level 2, the timed wait catching the same event** — `bulkhead.tryAcquire(200, TimeUnit.MILLISECONDS)` doesn't check just once; it blocks the calling thread, actively waiting for up to 200ms for a permit to become available, checking continuously (efficiently, via the underlying semaphore's own signaling mechanism) rather than instantly failing.
3. **Level 2, the successful catch** — because the background thread releases its permit after 50ms, well within the 200ms wait window, `tryAcquire` successfully returns `true` at approximately the 50ms mark, exactly when the permit became available — the identical timing scenario from Level 1, but with a materially different, successful outcome purely due to the non-zero wait duration.
4. **Level 3, a bulkhead that genuinely never frees up in time** — unlike the first two examples, no background thread ever releases the held permit in this scenario, modeling a genuinely stuck, fully overloaded dependency where no slot becomes available within any reasonable window.
5. **Level 3, the caller tied up for the full wait duration** — `tryAcquire(2000, TimeUnit.MILLISECONDS)` blocks for the entire 2000ms before finally giving up and returning `false`, since no permit was ever released during that window; the measured `elapsed` time confirms the caller's thread was genuinely occupied for the full duration, not released early.
6. **Level 3, the cost this represents** — a 2-second wait, while the bulkhead is genuinely and persistently at capacity (not just a brief blip), means every caller hitting this bulkhead during that period experiences a 2-second delay before finally being told the call couldn't be admitted — this is a real cost in caller-perceived latency, and it demonstrates precisely why the wait duration needs to be set short and deliberate (matching the kind of brief, momentary spike it's actually meant to absorb, as in Level 2) rather than long enough to also inadvertently tolerate a genuinely sustained overload, where an immediate or near-immediate rejection would actually serve the caller far better than a long, ultimately futile wait.

## 7. Gotchas & takeaways

> **Gotcha:** a non-zero wait duration means waiting callers themselves consume a resource (typically a blocked thread) for the duration of their wait — under a sustained, genuine overload (not the brief spike the wait duration is meant to help with), many callers waiting simultaneously can accumulate their own resource pressure from the waiting itself, partially undermining the bulkhead's core purpose; keep the wait duration short enough that this accumulated waiting cost stays negligible even under a worse-than-expected load scenario.

- Max wait duration controls whether a call arriving at a full bulkhead is rejected instantly (zero wait) or given a brief chance to wait for a slot to free up (a short, non-zero wait) before finally being rejected.
- A zero wait duration is the strictest, most protective default, giving immediate feedback with no waiting at all.
- A short, non-zero wait duration can absorb brief, momentary capacity spikes gracefully, letting a call succeed if a slot frees up shortly after it arrives, rather than an automatic rejection for a constraint that resolves within milliseconds.
- An excessively long wait duration ties up the calling thread for an unreasonably long time during a genuine, sustained overload, where the bulkhead never actually frees up — turning the bulkhead's own protective mechanism into a source of caller-perceived unresponsiveness.
- Waiting callers themselves consume resources (typically blocked threads) for the duration of their wait, so the wait duration should be kept short enough that this accumulated cost stays negligible even under worse-than-expected sustained load.
