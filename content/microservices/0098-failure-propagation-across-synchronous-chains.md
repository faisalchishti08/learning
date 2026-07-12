---
card: microservices
gi: 98
slug: failure-propagation-across-synchronous-chains
title: "Failure propagation across synchronous chains"
---

## 1. What it is

Failure propagation is what happens when one service in a chain of [synchronous calls](0075-synchronous-request-response-model.md) fails, and that failure travels — sometimes amplified — back up through every caller in the chain, all the way to the original request's origin. A single failing service deep in a call graph can, without deliberate containment, take down every service that (directly or transitively) depends on it, turning one localized problem into a system-wide outage.

## 2. Why & when

In a synchronous chain, each service typically waits for its downstream dependency's response before it can produce its own — so when a downstream service fails or hangs, every caller waiting on it is affected too, and *their* callers are affected in turn, and so on up the chain. Without deliberate failure-containment measures (timeouts, circuit breakers, fallbacks, bulkheads), a single failing service's blast radius is effectively the entire set of services that transitively depend on it — often much larger than the team that owns the failing service ever anticipated when they thought about that one service's own reliability in isolation.

Every service with any synchronous downstream dependency needs to consciously decide how it will behave when that dependency fails — this isn't optional hardening reserved for critical paths; it's baseline responsible design for any service embedded in a call chain. The specific containment mechanisms (timeouts, circuit breakers, fallbacks) are covered in depth elsewhere; this topic focuses on understanding *how* and *why* failure actually spreads, so those mechanisms' purpose is clear.

## 3. Core concept

Without containment, a failure at any point in the chain propagates upward through every caller; with containment at each hop, a failure's effect can be stopped at the point closest to where it occurred.

```
WITHOUT containment:
A calls B calls C calls D (D fails)
D fails -> C's call to D fails -> C fails -> B's call to C fails -> B fails -> A's call to B fails -> A fails
(one failure at D took down the ENTIRE chain)

WITH containment at each hop (timeout + fallback):
D fails -> C catches it, returns a FALLBACK value -> C succeeds -> B succeeds -> A succeeds
(the failure's blast radius was contained to C, one hop away from where it occurred)
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chain of four services where a failure at the last service propagates all the way back to the first without containment, versus being stopped one hop away when the calling service has a fallback">
  <text x="160" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Without containment</text>
  <rect x="20" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="50" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">A: FAILS</text>
  <rect x="100" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="130" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">B: FAILS</text>
  <rect x="180" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="210" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">C: FAILS</text>
  <rect x="260" y="30" width="60" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="290" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">D: fails</text>
  <line x1="80" y1="45" x2="100" y2="45" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a98)"/>
  <line x1="160" y1="45" x2="180" y2="45" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a98)"/>
  <line x1="240" y1="45" x2="260" y2="45" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a98)"/>

  <text x="480" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">With containment at C</text>
  <rect x="340" y="130" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="370" y="149" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">A: OK</text>
  <rect x="420" y="130" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="450" y="149" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">B: OK</text>
  <rect x="500" y="130" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="530" y="149" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">C: fallback</text>
  <rect x="580" y="130" width="55" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="607" y="149" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">D: fails</text>
  <line x1="400" y1="145" x2="420" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a98g)"/>
  <line x1="480" y1="145" x2="500" y2="145" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a98g)"/>
  <line x1="560" y1="145" x2="580" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a98)"/>

  <defs>
    <marker id="a98" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#79c0ff"/></marker>
    <marker id="a98g" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#6db33f"/></marker>
  </defs>
</svg>

Containment at one hop stops the failure from reaching every caller further up the chain.

## 5. Runnable example

Scenario: a 4-service synchronous chain (`A -> B -> C -> D`), first with `D` failing and no containment anywhere, propagating the failure all the way back to `A`, then fixed with `C` catching `D`'s failure and returning a fallback value, containing the blast radius, then extended to show a *partial* failure scenario where containment at the right point preserves a degraded-but-functional response rather than an outright failure.

### Level 1 — Basic

```java
// File: UncontainedPropagation.java -- D fails; NOTHING catches it
// anywhere in the chain -- the failure propagates all the way to A.
public class UncontainedPropagation {
    static class DownstreamFailureException extends RuntimeException {
        DownstreamFailureException(String service) { super(service + " failed"); }
    }

    static String serviceD() { throw new DownstreamFailureException("D"); }
    static String serviceC() { return "C used: " + serviceD(); } // no try/catch -- propagates straight through
    static String serviceB() { return "B used: " + serviceC(); } // no try/catch -- propagates straight through
    static String serviceA() { return "A used: " + serviceB(); } // no try/catch -- propagates straight through

    public static void main(String[] args) {
        try {
            serviceA();
        } catch (DownstreamFailureException e) {
            System.out.println("A ultimately failed because: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac UncontainedPropagation.java && java UncontainedPropagation` (JDK 17+).

Expected output:
```
A ultimately failed because: D failed
```

Even though `D` is the actual point of failure, `A`, `B`, and `C` all failed too — the exception traveled unmodified through all three, with no service along the way attempting to contain it.

### Level 2 — Intermediate

```java
// File: ContainedAtC.java -- SAME chain, but C now catches D's failure
// and returns a FALLBACK value -- B and A never even know D had a problem.
public class ContainedAtC {
    static class DownstreamFailureException extends RuntimeException {
        DownstreamFailureException(String service) { super(service + " failed"); }
    }

    static String serviceD() { throw new DownstreamFailureException("D"); }

    static String serviceC() {
        try {
            return "C used: " + serviceD();
        } catch (DownstreamFailureException e) {
            System.out.println("  [C caught D's failure, returning fallback]");
            return "C used FALLBACK (D unavailable)"; // containment happens HERE
        }
    }

    static String serviceB() { return "B used: " + serviceC(); } // never sees a failure -- C's fallback looks like success
    static String serviceA() { return "A used: " + serviceB(); } // never sees a failure either

    public static void main(String[] args) {
        String result = serviceA(); // completes successfully, despite D having failed
        System.out.println("A succeeded: " + result);
    }
}
```

**How to run:** `javac ContainedAtC.java && java ContainedAtC` (JDK 17+).

Expected output:
```
  [C caught D's failure, returning fallback]
A succeeded: A used: B used: C used FALLBACK (D unavailable)
```

### Level 3 — Advanced

```java
// File: PartialDegradationVsTotalFailure.java -- a MORE REALISTIC case:
// B depends on BOTH C (which depends on the failing D) and a separate,
// healthy service E -- containment at C lets B still produce a USEFUL,
// PARTIALLY degraded response instead of failing entirely.
import java.util.*;

public class PartialDegradationVsTotalFailure {
    static class DownstreamFailureException extends RuntimeException {
        DownstreamFailureException(String service) { super(service + " failed"); }
    }

    static String serviceD() { throw new DownstreamFailureException("D"); }

    static String serviceC() { // depends on the FAILING D
        try {
            return serviceD();
        } catch (DownstreamFailureException e) {
            return null; // signals "unavailable" rather than throwing -- containment
        }
    }

    static String serviceE() { return "recommendations from E"; } // a SEPARATE, healthy dependency

    static String serviceB() { // combines results from BOTH C and E
        String fromC = serviceC(); // may be null if D/C had a problem
        String fromE = serviceE(); // always succeeds in this scenario
        List<String> parts = new ArrayList<>();
        parts.add(fromE); // E's contribution is always present
        if (fromC != null) parts.add(fromC); // C's contribution only if it succeeded
        else System.out.println("  [B noticed C was unavailable -- omitting that part, not failing entirely]");
        return String.join(" + ", parts);
    }

    public static void main(String[] args) {
        String result = serviceB(); // partial success: E's data present, C's data gracefully omitted
        System.out.println("B's final response: " + result);
    }
}
```

**How to run:** `javac PartialDegradationVsTotalFailure.java && java PartialDegradationVsTotalFailure` (JDK 17+).

Expected output:
```
  [B noticed C was unavailable -- omitting that part, not failing entirely]
B's final response: recommendations from E
```

## 6. Walkthrough

1. **Level 1** — `serviceD` unconditionally throws `DownstreamFailureException`. `serviceC`, `serviceB`, and `serviceA` each call their respective downstream dependency with no `try`/`catch` at all — the exception thrown deep inside `serviceD` propagates up through `serviceC`'s call, then `serviceB`'s call, then `serviceA`'s call, entirely unmodified, exactly as an uncaught exception naturally propagates up a Java call stack. `main`'s own `try`/`catch` around `serviceA()` is the *only* place the failure is finally caught, and the message printed (`"D failed"`) reveals that the true point of failure was four calls deep — but from `main`'s point of view, `A` itself simply failed, with no indication that `A`, `B`, and `C` were all actually healthy.
2. **Level 2 — containment at one hop** — `serviceC` now wraps its call to `serviceD` in a `try`/`catch`, and on catching `DownstreamFailureException`, prints a diagnostic and returns a fallback string instead of propagating the exception further. `serviceB` and `serviceA` are *unchanged* from Level 1 — they still call their respective dependencies with no error handling of their own — but because `serviceC` no longer throws, `serviceB`'s call to it simply returns a (fallback-flavored) string, which `serviceB` treats as an ordinary successful result, and the same happens one level up at `serviceA`. `main` calls `serviceA()` directly (no `try`/`catch` needed this time) and it returns normally, printing a result that includes the word "FALLBACK" — visible evidence that something degraded happened deep in the chain, but critically, *nothing failed*.
3. **Level 3 — partial degradation instead of binary success/failure** — this scenario introduces a more realistic shape: `serviceB` depends on *both* `serviceC` (which depends on the failing `serviceD`) and a separate, independently healthy `serviceE`. `serviceC` now returns `null` on failure (a simple signal for "this specific piece is unavailable") rather than throwing or returning a fallback string.
4. **Tracing `serviceB`'s combination logic** — `serviceB` calls `serviceC()`, getting back `null` (since `D` still fails and `C` still contains that failure). It calls `serviceE()`, which succeeds normally, returning `"recommendations from E"`. `serviceB` then builds its response by always including `fromE`, but only including `fromC` if it's non-null — since `fromC` is `null` here, the `else` branch runs, printing the diagnostic about omitting that part, and the final `parts` list contains only `fromE`'s contribution. `main` prints `serviceB`'s final response, which is just `"recommendations from E"` — a genuinely useful, if incomplete, response, rather than an outright failure of the whole request.
5. **Why the distinction between Level 2 and Level 3 matters** — Level 2 masks the failure entirely (the caller sees a normal-looking success, just with fallback content baked in); Level 3 makes a more nuanced choice — it produces a response that's honestly *partial* (missing the recommendations that would have come from `C`/`D`), while still succeeding for the parts of the request that had nothing to do with the failing dependency. Which approach is right depends on the specific feature: sometimes a fallback value is the better user experience (Level 2's approach), and sometimes gracefully omitting the unavailable part while still serving everything else is better (Level 3's approach) — but both are dramatically preferable to Level 1's uncontained propagation, where one failing service four hops away took down the entire response.

## 7. Gotchas & takeaways

> **Gotcha:** containing a failure by silently swallowing it and returning a fallback (as Level 2 does) can mask real, ongoing problems from monitoring and alerting if the fallback path isn't *also* logged and measured distinctly from genuine successes. A service that's been silently running on fallback data for hours because a downstream dependency is down needs that fact visible to operators, even though callers of the containing service never see a failure.

- Without deliberate containment, a failure at any point in a synchronous chain propagates unmodified through every caller above it, all the way to the chain's origin.
- Containment (catching a specific failure and providing a fallback or a degraded-but-useful response) should happen as close as possible to where the failure actually occurs — the deeper the containment point, the smaller the failure's ultimate blast radius.
- A binary fallback (Level 2, masking the failure entirely) and a partial-degradation response (Level 3, honestly reflecting what succeeded and what didn't) are both valid containment strategies — the right choice depends on the specific feature and what a genuinely useful degraded response looks like for it.
- Always log and measure fallback/degraded paths distinctly from genuine successes — silent containment that also hides the underlying problem from monitoring defeats half the purpose of noticing failures at all.
- The concrete mechanisms that implement this containment — circuit breakers, bulkheads, retries with backoff — build directly on the principle demonstrated here: catch the failure as close to its source as possible, and decide deliberately what the caller should see instead.
