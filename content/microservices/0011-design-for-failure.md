---
card: microservices
gi: 11
slug: design-for-failure
title: Design for failure
---

## 1. What it is

**Design for failure** is the Lewis & Fowler characteristic that says a microservices system should assume, from the start, that any of its network calls to another service can fail — time out, refuse the connection, return an error — and be built to tolerate that gracefully rather than crash or hang. This is a direct consequence of choosing a distributed architecture: a monolith's in-process method calls essentially never fail on their own, but a network call to another service genuinely can, for reasons entirely outside your own code's control.

## 2. Why & when

In a monolith, "the database is down" is close to the only failure mode a call chain needs to worry about, and it's usually rare and severe enough to justify simply failing the whole request. In microservices, a single user-facing request might fan out to five, ten, or more downstream service calls — and if any *one* of them can fail, and failures aren't handled deliberately, the overall reliability of the whole request drops sharply as the number of dependencies grows, even if each individual dependency is quite reliable on its own.

Design for failure from day one of building any service that calls another service over the network — not as an afterthought once an outage has already happened. The three most common tools, applied together, are: a **timeout** (never wait forever for a response), a **retry** (a transient failure might succeed on a second attempt), and a **circuit breaker** (stop hammering a dependency that's clearly down, instead of piling up failing requests against it).

## 3. Core concept

Each tool solves a different failure shape:

- **Timeout** — bounds how long you'll wait for any single call, so one slow dependency can't stall your entire request indefinitely.
- **Retry** — re-attempts a failed call, useful for transient blips (a dropped packet, a momentary hiccup), but dangerous if applied blindly to a dependency that's genuinely down, since it just adds more load to an already-struggling service.
- **Circuit breaker** — tracks recent failures and, past a threshold, stops calling the dependency entirely for a cooldown period, giving it room to recover instead of being hit with a continuous stream of doomed requests. It then allows a small trial request through to check if the dependency has recovered, before fully resuming normal traffic.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker moves between Closed, Open and Half-Open states based on call failures and a cooldown period">
  <circle cx="120" cy="100" r="55" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="96" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CLOSED</text>
  <text x="120" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">calls flow normally</text>

  <circle cx="500" cy="100" r="55" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="500" y="96" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OPEN</text>
  <text x="500" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">calls rejected instantly</text>

  <circle cx="310" cy="170" r="45" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="166" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HALF-OPEN</text>
  <text x="310" y="181" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">one trial call</text>

  <line x1="175" y1="95" x2="445" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a11)"/>
  <text x="310" y="85" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">failure threshold reached</text>

  <line x1="470" y1="130" x2="345" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a11)"/>
  <text x="430" y="135" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">cooldown elapses</text>

  <line x1="280" y1="140" x2="150" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a11)"/>
  <text x="190" y="165" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">trial call succeeds</text>
  <defs><marker id="a11" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Closed lets traffic through; Open blocks it entirely; Half-Open tests recovery with a single trial call.

## 5. Runnable example

Scenario: calling a flaky downstream dependency, first with no protection at all, then with a timeout and retry, then with a full circuit breaker that stops hammering a genuinely down dependency.

### Level 1 — Basic

```java
// File: NaiveCall.java -- no protection against a flaky dependency at all
public class NaiveCall {
    static int callCount = 0;

    static String callDependency() {
        callCount++;
        if (callCount <= 3) throw new RuntimeException("dependency timed out"); // simulates a flaky/down dependency
        return "success";
    }

    public static void main(String[] args) {
        try {
            System.out.println(callDependency()); // FAILS -- no retry, no fallback, request just dies
        } catch (RuntimeException e) {
            System.out.println("Request failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac NaiveCall.java && java NaiveCall` (JDK 17+).

Expected output:
```
Request failed: dependency timed out
```

One transient failure kills the whole request immediately, even though the dependency might have succeeded on a second attempt moments later.

### Level 2 — Intermediate

```java
// File: RetryWithBackoff.java -- retry transient failures a bounded number of times
public class RetryWithBackoff {
    static int callCount = 0;

    static String callDependency() {
        callCount++;
        if (callCount <= 3) throw new RuntimeException("dependency timed out (attempt " + callCount + ")");
        return "success on attempt " + callCount;
    }

    static String callWithRetry(int maxAttempts) {
        RuntimeException lastError = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return callDependency();
            } catch (RuntimeException e) {
                lastError = e;
                System.out.println("  attempt failed: " + e.getMessage() + " -- retrying");
            }
        }
        throw lastError; // exhausted all attempts, give up and propagate
    }

    public static void main(String[] args) {
        try {
            System.out.println(callWithRetry(5));
        } catch (RuntimeException e) {
            System.out.println("Request failed after retries: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac RetryWithBackoff.java && java RetryWithBackoff` (JDK 17+).

Expected output:
```
  attempt failed: dependency timed out (attempt 1) -- retrying
  attempt failed: dependency timed out (attempt 2) -- retrying
  attempt failed: dependency timed out (attempt 3) -- retrying
success on attempt 4
```

The same transient failure that killed the Level 1 request is now absorbed: `callWithRetry` re-attempts up to 5 times, and the dependency happens to succeed on the fourth try — exactly the kind of momentary blip retry is meant to smooth over. (A real implementation would add a growing delay, or "backoff," between attempts to avoid hammering the dependency too fast; this simplified version retries immediately for clarity.)

### Level 3 — Advanced

```java
// File: CircuitBreaker.java -- add a circuit breaker so a GENUINELY DOWN
// dependency stops being hammered with retries that can never succeed.
public class CircuitBreaker {
    enum State { CLOSED, OPEN, HALF_OPEN }

    static State state = State.CLOSED;
    static int consecutiveFailures = 0;
    static final int FAILURE_THRESHOLD = 3;
    static long openedAt = 0;
    static final long COOLDOWN_MS = 100;

    static boolean dependencyIsDown = true; // simulates the dependency being genuinely, persistently down

    static String rawCall() {
        if (dependencyIsDown) throw new RuntimeException("dependency unreachable");
        return "success";
    }

    static String protectedCall(long now) {
        if (state == State.OPEN) {
            if (now - openedAt >= COOLDOWN_MS) {
                state = State.HALF_OPEN; // cooldown elapsed, allow ONE trial call through
                System.out.println("  [breaker] cooldown elapsed -- HALF_OPEN, letting one trial call through");
            } else {
                throw new RuntimeException("circuit OPEN -- rejected instantly, dependency NOT called at all");
            }
        }

        try {
            String result = rawCall();
            consecutiveFailures = 0;
            if (state == State.HALF_OPEN) { state = State.CLOSED; System.out.println("  [breaker] trial call succeeded -- CLOSED"); }
            return result;
        } catch (RuntimeException e) {
            consecutiveFailures++;
            if (state == State.HALF_OPEN || consecutiveFailures >= FAILURE_THRESHOLD) {
                state = State.OPEN;
                openedAt = now;
                System.out.println("  [breaker] tripped -- entering OPEN, no more calls for " + COOLDOWN_MS + "ms");
            }
            throw e;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long t = 0;
        for (int i = 0; i < 5; i++) { // first 5 calls: dependency is down, breaker trips after 3 failures
            try { System.out.println("call " + i + ": " + protectedCall(t)); }
            catch (RuntimeException e) { System.out.println("call " + i + ": failed -- " + e.getMessage()); }
        }

        Thread.sleep(COOLDOWN_MS + 10);
        dependencyIsDown = false; // dependency recovers during the cooldown
        long tAfterCooldown = t + COOLDOWN_MS + 10;
        System.out.println("call 5: " + protectedCall(tAfterCooldown)); // HALF_OPEN trial succeeds, breaker CLOSES
        System.out.println("call 6: " + protectedCall(tAfterCooldown)); // back to normal CLOSED operation
    }
}
```

**How to run:** `javac CircuitBreaker.java && java CircuitBreaker` (JDK 17+).

Expected output:
```
call 0: failed -- dependency unreachable
call 1: failed -- dependency unreachable
call 2: failed -- dependency unreachable
  [breaker] tripped -- entering OPEN, no more calls for 100ms
call 3: failed -- circuit OPEN -- rejected instantly, dependency NOT called at all
call 4: failed -- circuit OPEN -- rejected instantly, dependency NOT called at all
  [breaker] cooldown elapsed -- HALF_OPEN, letting one trial call through
  [breaker] trial call succeeded -- CLOSED
call 5: success
call 6: success
```

The production-flavored case: calls 0–2 each genuinely try `rawCall()` and fail, tripping the breaker to `OPEN` after the third consecutive failure. Calls 3 and 4 are rejected **instantly**, without ever touching `rawCall()` — this is the key difference from Level 2's blind retry, which would have kept calling a dependency that has no chance of succeeding. Once the cooldown elapses and the dependency recovers, one trial call is let through in `HALF_OPEN`, succeeds, and the breaker closes — resuming normal traffic.

## 6. Walkthrough

1. Calls `0`, `1`, and `2` each go through `protectedCall`, which is still in `CLOSED` state, so they proceed straight to `rawCall()`. Since `dependencyIsDown` is `true`, each throws, incrementing `consecutiveFailures` to `1`, then `2`, then `3`.
2. On call `2`'s failure, `consecutiveFailures >= FAILURE_THRESHOLD` becomes true, so `state` flips to `OPEN`, `openedAt` is recorded, and the breaker prints its trip message.
3. Call `3` enters `protectedCall` and immediately sees `state == State.OPEN`. Since not enough time (`COOLDOWN_MS`) has elapsed since `openedAt`, it throws `"circuit OPEN -- rejected instantly"` **without calling `rawCall()` at all** — the dependency isn't touched, unlike a naive retry loop that would keep calling it.
4. Call `4` behaves the same way — still within the cooldown window.
5. `Thread.sleep(COOLDOWN_MS + 10)` advances real time past the cooldown, and `dependencyIsDown = false` simulates the dependency recovering.
6. Call `5` enters `protectedCall` with `state == OPEN`, but now `now - openedAt >= COOLDOWN_MS` is true, so it transitions to `HALF_OPEN` and lets exactly one trial call through to `rawCall()`. Since the dependency has recovered, this call succeeds, `consecutiveFailures` resets to `0`, and because `state == HALF_OPEN`, it transitions to `CLOSED`.
7. Call `6` runs with the breaker fully `CLOSED` again — a normal, protected call that succeeds without any special handling.

```
CLOSED --(3 consecutive failures)--> OPEN --(cooldown elapses)--> HALF_OPEN --(trial succeeds)--> CLOSED
   |                                   |                              |
 calls 0-2 fail normally         calls 3-4 rejected           call 5 succeeds, resumes normal traffic
                                  instantly, no network hit
```

## 7. Gotchas & takeaways

> **Gotcha:** retry and circuit breaker solve different problems and can work against each other if misconfigured — a retry loop *inside* a circuit breaker's trial call can itself generate enough failures to look like several distinct failures to the breaker, tripping it faster than intended. Be deliberate about which layer (the call itself, or the breaker wrapping it) owns the retry logic.

- Design for failure means assuming any network call to another service can fail, and building deliberate handling for that — not hoping it won't happen.
- A timeout bounds how long you wait; a retry re-attempts transient failures; a circuit breaker stops calling a dependency that's clearly, persistently down, protecting both the caller and the struggling dependency.
- Blind retries against a genuinely down dependency make things worse, not better — they add load to a service that's already struggling, which is exactly what a circuit breaker is designed to prevent.
- The circuit breaker's `HALF_OPEN` state is what lets the system self-heal: it periodically tests recovery with minimal risk, rather than either hammering the dependency constantly or staying permanently blocked once tripped.
