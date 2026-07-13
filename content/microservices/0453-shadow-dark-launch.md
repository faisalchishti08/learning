---
card: microservices
gi: 453
slug: shadow-dark-launch
title: "Shadow / dark launch"
---

## 1. What it is

A **shadow launch** (also called a **dark launch**) mirrors real production requests to a new version of a service alongside the current stable version, but never returns the new version's response to the actual caller — the caller always gets the stable version's answer, and the new version's response is only observed internally, typically compared against the stable response for correctness or performance signals, then discarded. Unlike [canary release](0452-canary-release.md), where a percentage of *real users* get real responses from the new version, shadow traffic never reaches a real user at all: zero users are ever affected, no matter how badly the new version behaves.

## 2. Why & when

You reach for a shadow launch when you want real production traffic exercising a new version, with literally zero risk to any actual user's experience:

- **Even a small canary percentage still risks real users.** A 5% canary still means some fraction of real users get real responses from an unproven version. A shadow launch removes that risk entirely: the new version's output is compared and discarded, never served.
- **It's the only way to validate against production-scale, production-shaped traffic before anyone is exposed at all.** A rewrite of a pricing engine, a new recommendation algorithm, or a performance-sensitive query path can be run against real request volume and real data distributions for days or weeks, gathering correctness and latency data, before a single real user ever sees its output.
- **It surfaces both correctness bugs and performance regressions.** Comparing shadow responses against primary responses catches logic differences; measuring shadow latency and error rate under real load (without it affecting anyone) catches performance and stability problems before they matter.
- **You use this specifically for high-risk rewrites** — a payment calculation, a critical business rule, a data migration path — where even a small percentage of real users seeing a wrong answer is unacceptable, and where the cost of running the shadow version alongside primary (extra compute, careful isolation) is justified by that risk.

## 3. Core concept

A useful analogy is a flight simulator versus an actual test flight. A canary release is like putting a new autopilot on a real plane carrying a few real passengers — safer than putting it on every plane, but real people are still at risk if it fails. A shadow launch is like feeding the new autopilot the exact same real flight data in real time, in a simulator, so its decisions can be compared against what the actual, human-flown plane did — the simulator's mistakes affect nobody, no matter how wrong they are.

Concretely, the mechanics are:

1. **Every real request is mirrored** to both the primary (stable) version and the shadow (new) version, typically fired off in parallel or just after the real request is already being handled.
2. **Only the primary's response is ever returned to the caller.** The shadow's response has no path back to the real user — this is the entire safety property of the pattern.
3. **The shadow's response is compared or logged for analysis** — matched against the primary's response to catch correctness divergence, and its latency/error rate measured to catch performance or stability problems.
4. **The shadow call must be isolated from the primary's request path.** If a shadow call is slow, hangs, or throws, that must never delay or break the primary response — this requires a hard timeout on the shadow call and defensive exception handling around it, since "the shadow is broken" is exactly the scenario shadow launches exist to safely discover.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request is mirrored to both primary and shadow versions; only the primary response returns to the caller; the shadow call is isolated with a timeout so its failure or slowness never affects the caller">
  <rect x="20" y="90" width="110" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="75" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Real request</text>

  <rect x="240" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Primary (v1)</text>
  <text x="315" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">response -&gt; caller</text>

  <rect x="240" y="150" width="150" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="315" y="175" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Shadow (v2)</text>
  <text x="315" y="190" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">response discarded, timeout-bound</text>

  <line x1="130" y1="110" x2="240" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="130" y1="115" x2="240" y2="175" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#a2)"/>

  <rect x="450" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="525" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Caller</text>
  <text x="525" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">only ever sees primary</text>
  <line x1="390" y1="55" x2="450" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>

  <text x="315" y="215" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">shadow response is compared/logged, then thrown away -- never routed to any real user</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
  </defs>
</svg>

The caller only ever sees the primary's response; the shadow call runs in parallel, bounded by a timeout, and its result never reaches any real user.

## 5. Runnable example

Scenario: a request handler mirroring traffic to a new pricing engine. We start with the bare mirror-and-discard mechanism, add comparison logic that surfaces a real correctness bug (a rounding difference) without ever affecting the caller, then handle the hard case: the shadow version starts hanging and throwing exceptions under real load, requiring strict isolation so neither failure mode ever touches the primary response path.

### Level 1 — Basic

```java
// File: ShadowBasic.java -- models the CORE idea: MIRROR every real
// request to a shadow (new) version alongside the primary (stable)
// version, but return ONLY the primary's response to the real caller --
// the shadow's response is observed internally and then discarded.
public class ShadowBasic {
    static String callPrimary(String request) {
        return "primary-response-for(" + request + ")";
    }

    static String callShadow(String request) {
        return "shadow-response-for(" + request + ")";
    }

    public static void main(String[] args) {
        String[] requests = { "req-1", "req-2", "req-3" };

        for (String req : requests) {
            String primaryResponse = callPrimary(req);
            String shadowResponse = callShadow(req); // mirrored, but NEVER returned to the caller

            System.out.println(req + ": returned to caller -> " + primaryResponse);
            System.out.println(req + ": shadow observed internally, then discarded -> " + shadowResponse);
        }
    }
}
```

How to run: `java ShadowBasic.java`

`primaryResponse` is the only value ever attributed to "what the caller gets" in the print statements — `shadowResponse` is computed and logged, but nothing in this program ever routes it anywhere a real caller would see it. That asymmetry — compute both, return only one — is the entire structural definition of a shadow launch.

### Level 2 — Intermediate

```java
// File: ShadowWithDiffComparison.java -- the SAME mirroring idea, now
// COMPARING the shadow's response against the primary's for each request,
// logging any mismatch as a correctness signal -- without ever letting the
// comparison or the shadow's result affect what the caller receives.
import java.util.*;

public class ShadowWithDiffComparison {
    static final double UNIT_PRICE = 19.999; // deliberately sub-cent, to make rounding visible

    // Pricing logic under test: v1 (primary) rounds to cents; v2 (shadow) has a latent rounding bug.
    static double callPrimary(int quantity) {
        return Math.round(quantity * UNIT_PRICE * 100) / 100.0; // v1: rounds to cents
    }
    static double callShadow(int quantity) {
        return quantity * UNIT_PRICE; // v2: NOT rounded -- a latent bug
    }

    public static void main(String[] args) {
        int[] quantities = { 1, 2, 3 };
        int mismatches = 0;

        for (int quantity : quantities) {
            double primaryResult = callPrimary(quantity);
            double shadowResult = callShadow(quantity);
            boolean matches = Double.compare(primaryResult, shadowResult) == 0;

            System.out.println("qty=" + quantity + ": primary=" + primaryResult + " shadow=" + shadowResult
                    + " -> " + (matches ? "MATCH" : "MISMATCH (logged for investigation)"));
            if (!matches) mismatches++;

            // The caller ONLY ever sees primaryResult -- the comparison is purely observational.
        }

        System.out.println("Total mismatches observed: " + mismatches + "/" + quantities.length
                + " -- caller was unaffected throughout; this is a correctness signal, not a routing decision.");
    }
}
```

How to run: `java ShadowWithDiffComparison.java`

`callPrimary` rounds to whole cents, matching how a real invoicing system must behave; `callShadow` models a new pricing engine that forgot the rounding step — a subtle but real bug. Every comparison in this run reports `MISMATCH`, and critically, that mismatch is purely a logged signal: the loop never uses `shadowResult` for anything the caller would see. This is exactly how a shadow launch would catch this class of bug in real production data, before it ever reached a real invoice.

### Level 3 — Advanced

```java
// File: ShadowWithIsolationAdvanced.java -- the SAME mirror-and-compare
// idea, now handling a PRODUCTION-FLAVORED hard case: the shadow version
// starts throwing exceptions AND hanging far longer than the primary. The
// shadow call MUST be isolated -- bounded by a timeout and wrapped so its
// failure or slowness never delays or breaks the response the real caller
// receives.
import java.util.concurrent.*;

public class ShadowWithIsolationAdvanced {
    static final long SHADOW_TIMEOUT_MS = 200;
    static final ExecutorService shadowExecutor = Executors.newFixedThreadPool(2);

    static String callPrimary(String request) {
        return "primary-response-for(" + request + ")"; // fast, reliable, always succeeds
    }

    // The shadow version is broken: it either hangs or throws, depending on the request.
    static String callShadowUnsafe(String request) throws InterruptedException {
        if (request.equals("req-slow")) {
            Thread.sleep(2000); // simulates a shadow that hangs far past any reasonable budget
            return "shadow-response-for(" + request + ")";
        }
        if (request.equals("req-error")) {
            throw new RuntimeException("shadow NPE on malformed input");
        }
        return "shadow-response-for(" + request + ")";
    }

    // Isolation wrapper: runs the shadow call off to the side, bounded by a
    // timeout, and NEVER lets an exception or a hang escape to the caller's path.
    static void callShadowIsolated(String request) {
        Future<String> future = shadowExecutor.submit(() -> callShadowUnsafe(request));
        try {
            String result = future.get(SHADOW_TIMEOUT_MS, TimeUnit.MILLISECONDS);
            System.out.println("  shadow for " + request + " completed: " + result);
        } catch (TimeoutException e) {
            future.cancel(true);
            System.out.println("  shadow for " + request + " TIMED OUT after " + SHADOW_TIMEOUT_MS + "ms -- abandoned, primary unaffected");
        } catch (Exception e) {
            System.out.println("  shadow for " + request + " THREW an exception (" + e.getCause() + ") -- swallowed, primary unaffected");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String[] requests = { "req-ok", "req-error", "req-slow" };

        for (String request : requests) {
            long start = System.currentTimeMillis();
            String primaryResponse = callPrimary(request); // returned to the caller immediately
            long primaryElapsed = System.currentTimeMillis() - start;

            System.out.println(request + ": returned to caller in " + primaryElapsed + "ms -> " + primaryResponse);
            callShadowIsolated(request); // observed separately; can fail or be slow with zero caller impact
        }

        shadowExecutor.shutdown();
        System.out.println("All requests served successfully despite the shadow version being broken.");
    }
}
```

How to run: `java ShadowWithIsolationAdvanced.java`

`callPrimary` runs synchronously and returns immediately, completely independent of anything the shadow does. `callShadowIsolated` submits the shadow call to a separate thread pool and bounds it with `future.get(SHADOW_TIMEOUT_MS, ...)`: if the shadow throws (`req-error`), the `catch (Exception e)` block swallows it; if the shadow hangs (`req-slow`, sleeping 2 seconds against a 200ms budget), `TimeoutException` fires, the future is cancelled, and execution moves on. In neither failure case does the primary response's timing or content change at all.

## 6. Walkthrough

Trace `ShadowWithIsolationAdvanced.main` in order, focusing on `"req-slow"`, the third request. **First**, `callPrimary("req-slow")` runs and returns immediately — `primaryElapsed` measures in low single-digit milliseconds, and the primary response is printed to the caller right away, exactly as fast as for any other request.

**Next**, `callShadowIsolated("req-slow")` is called. Inside it, `shadowExecutor.submit(() -> callShadowUnsafe("req-slow"))` hands the shadow call off to a background thread and returns a `Future` immediately — the calling thread (which already returned the primary response) doesn't block waiting for the shadow's actual work to start.

**Then**, `future.get(SHADOW_TIMEOUT_MS, TimeUnit.MILLISECONDS)` blocks *only this isolated call*, waiting up to 200ms. Inside the background thread, `callShadowUnsafe` calls `Thread.sleep(2000)` — 2 full seconds, ten times the timeout budget. Because 200ms elapses long before the sleep finishes, `future.get` throws `TimeoutException`.

**Finally**, the `catch (TimeoutException e)` block runs: it calls `future.cancel(true)` to signal the background thread to stop, then prints the "TIMED OUT ... abandoned, primary unaffected" message. Crucially, this entire sequence happens *after* the primary response was already returned and printed — the shadow's 2-second hang never delayed the caller by even a millisecond, which is the property the isolation wrapper exists to guarantee.

```
req-ok: returned to caller in 1ms -> primary-response-for(req-ok)
  shadow for req-ok completed: shadow-response-for(req-ok)
req-error: returned to caller in 0ms -> primary-response-for(req-error)
  shadow for req-error THREW an exception (java.lang.RuntimeException: shadow NPE on malformed input) -- swallowed, primary unaffected
req-slow: returned to caller in 0ms -> primary-response-for(req-slow)
  shadow for req-slow TIMED OUT after 200ms -- abandoned, primary unaffected
All requests served successfully despite the shadow version being broken.
```

## 7. Gotchas & takeaways

> An un-isolated shadow call is worse than no shadow launch at all: without a timeout and exception boundary around it, a hanging or crashing shadow can consume the same thread pool, connection pool, or resource budget the primary path depends on, turning a supposedly zero-risk validation technique into a real production incident.

- The single non-negotiable property of a shadow launch is that the shadow's result never reaches a real caller — if a code path exists where it could (even a fallback, even an error case), it's no longer a true shadow launch.
- Always bound shadow calls with a strict timeout and wrap them in defensive exception handling, exactly as Level 3 does — discovering that the shadow is slow or broken is a legitimate and expected outcome of running one, not a bug in the isolation wrapper.
- Comparing shadow output against primary output is a powerful correctness signal for rewrites, but expect false-positive mismatches from things like timestamps, random IDs, or non-deterministic ordering — normalize those out of the comparison rather than treating every difference as a bug.
- Shadow launches consume real compute for zero direct product value during the validation window — budget for that cost explicitly rather than treating shadow traffic as free.
- Shadow launches and [canary release](0452-canary-release.md) are often used in sequence: shadow first to validate correctness and performance with zero user risk, then canary to validate real user-facing behavior with a small, controlled, and reversible blast radius.
