---
card: microservices
gi: 266
slug: retry-storm-amplification-risk
title: "Retry storm / amplification risk"
---

## 1. What it is

A retry storm is the runaway scenario where retries, instead of helping a system recover from a failure, actively make it worse — a struggling dependency gets hit with amplified load from many callers' retries, which pushes it further into failure, generating even more retries, in a self-reinforcing feedback loop that can turn a brief, recoverable blip into a prolonged, severe outage.

## 2. Why & when

Each individual safeguard covered earlier in this section — [max attempts](0260-max-retry-attempts.md), [backoff](0261-fixed-vs-exponential-backoff.md), [jitter](0262-jitter-randomized-backoff.md), [retry budgets](0263-retry-budgets.md), [transient-only classification](0264-retry-only-on-transient-retryable-errors.md) — addresses one specific contributing factor to this same underlying risk, but a retry storm is what happens when several of them are missing or under-tuned *simultaneously*: unbounded or overly aggressive retries, applied indiscriminately to every failure type, with no coordination across concurrent callers, layered on top of retries happening at *multiple levels* of a call chain (a client retries, and the service it called also retries its own downstream call, multiplying the effective retry count at each hop) — each factor alone might be manageable, but their combination can produce amplification factors many times the original traffic volume, arriving precisely when the target system is least able to absorb it.

Treat retry storm risk as the reason every other topic in this cluster (budgets, classification, backoff, jitter, bounded attempts) matters together, not in isolation — a system with excellent backoff and jitter but no retry budget, or excellent budgets but no per-call attempt limit, still has real amplification exposure through whichever safeguard is missing.

## 3. Core concept

Amplification compounds multiplicatively across every layer of a call chain that independently retries — if a client retries up to 3 times, and the service it calls also retries its own downstream dependency up to 3 times per client attempt, the effective load multiplier at the innermost dependency isn't 3, it's 3 × 3 = 9, and this compounding grows rapidly with each additional layer of independent retrying.

```java
// EACH layer's retry count MULTIPLIES with the layers above it
int clientMaxAttempts = 3;
int gatewayMaxAttempts = 3;   // the gateway ALSO retries its own call to the next layer
int serviceMaxAttempts = 3;   // and THAT service retries its OWN downstream call too

// the WORST-CASE amplification at the innermost dependency:
int worstCaseMultiplier = clientMaxAttempts * gatewayMaxAttempts * serviceMaxAttempts; // = 27, NOT 3+3+3=9
// ONE original client request can generate up to 27 actual calls to the innermost dependency
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client retrying up to three times calls a gateway that independently retries up to three times per client attempt, calling a service that independently retries up to three times per gateway attempt, so the innermost dependency can receive up to twenty seven calls from a single original client request due to multiplicative compounding across layers" >
  <rect x="20" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Client (x3)</text>

  <rect x="200" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="250" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Gateway (x3)</text>

  <rect x="380" y="70" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="430" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Service (x3)</text>

  <rect x="530" y="60" width="90" height="55" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="575" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Innermost</text>
  <text x="575" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">up to 27x</text>

  <line x1="120" y1="90" x2="198" y2="90" stroke="#8b949e" marker-end="url(#arr266)"/>
  <line x1="300" y1="90" x2="378" y2="90" stroke="#8b949e" marker-end="url(#arr266)"/>
  <line x1="480" y1="90" x2="528" y2="90" stroke="#8b949e" marker-end="url(#arr266)"/>

  <defs>
    <marker id="arr266" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Retry counts multiply, not add, across independently-retrying layers of a call chain.

## 5. Runnable example

Scenario: a three-layer call chain where each layer retries independently with no coordination, measuring the resulting worst-case amplification at the innermost dependency, refactored to disable retries at intermediate layers (retrying only at the outermost layer, which is the layer that actually knows about the end-to-end operation), and finally demonstrating the full storm scenario under a sustained failure, measuring the actual call volume generated compared to the original request rate.

### Level 1 — Basic

```java
// File: MultiLayerRetryAmplification.java -- EACH layer retries
// INDEPENDENTLY, with NO coordination -- amplification COMPOUNDS
// multiplicatively across the chain.
public class MultiLayerRetryAmplification {
    static int innermostCallCount = 0;

    static void callInnermostDependency() { innermostCallCount++; throw new RuntimeException("still failing"); }

    static void callService(int maxAttempts) {
        for (int i = 1; i <= maxAttempts; i++) {
            try { callInnermostDependency(); return; } catch (RuntimeException ignored) {}
        }
    }

    static void callGateway(int maxAttempts) {
        for (int i = 1; i <= maxAttempts; i++) {
            callService(3); // the GATEWAY retries its own call to `callService`, WHICH ITSELF retries internally
        }
    }

    static void callFromClient(int maxAttempts) {
        for (int i = 1; i <= maxAttempts; i++) {
            callGateway(3); // the CLIENT retries its call to the GATEWAY, WHICH retries its OWN downstream call
        }
    }

    public static void main(String[] args) {
        callFromClient(3); // ONE logical client request
        System.out.println("ONE original client request generated " + innermostCallCount + " actual calls to the innermost dependency!");
        System.out.println("Expected worst case: 3 x 3 x 3 = 27 -- COMPOUNDING, not additive.");
    }
}
```

**How to run:** `javac MultiLayerRetryAmplification.java && java MultiLayerRetryAmplification` (JDK 17+).

Expected output:
```
ONE original client request generated 27 actual calls to the innermost dependency!
Expected worst case: 3 x 3 x 3 = 27 -- COMPOUNDING, not additive.
```

### Level 2 — Intermediate

```java
// File: RetryOnlyAtOneLayer.java -- retries happen ONLY at the OUTERMOST
// layer (the one that actually knows about the end-to-end operation);
// intermediate layers do NOT retry independently -- amplification is
// now LINEAR, not multiplicative.
public class RetryOnlyAtOneLayer {
    static int innermostCallCount = 0;

    static void callInnermostDependency() { innermostCallCount++; throw new RuntimeException("still failing"); }

    static void callService() { callInnermostDependency(); } // NO retry loop here -- just propagates the failure UP
    static void callGateway() { callService(); }              // NO retry loop here EITHER

    static void callFromClient(int maxAttempts) { // ONLY the outermost layer retries
        for (int i = 1; i <= maxAttempts; i++) {
            try { callGateway(); return; } catch (RuntimeException ignored) {}
        }
    }

    public static void main(String[] args) {
        try { callFromClient(3); } catch (RuntimeException ignored) {}
        System.out.println("ONE original client request generated " + innermostCallCount + " actual calls to the innermost dependency.");
        System.out.println("Expected: exactly 3 -- LINEAR, matching the client's OWN retry count, no multiplicative compounding.");
    }
}
```

**How to run:** `javac RetryOnlyAtOneLayer.java && java RetryOnlyAtOneLayer` (JDK 17+).

Expected output:
```
ONE original client request generated 3 actual calls to the innermost dependency.
Expected: exactly 3 -- LINEAR, matching the client's OWN retry count, no multiplicative compounding.
```

### Level 3 — Advanced

```java
// File: MeasuredStormUnderConcurrentClients.java -- measures the FULL
// storm scenario: MANY concurrent clients, each independently retrying
// through a MULTI-LAYER chain, all during a SUSTAINED failure --
// comparing multi-layer vs single-layer retry against REALISTIC scale.
public class MeasuredStormUnderConcurrentClients {
    static int multiLayerInnermostCalls;
    static int singleLayerInnermostCalls;

    static void multiLayerCallChain() {
        for (int client = 1; client <= 3; client++) {          // client layer: 3 attempts
            for (int gateway = 1; gateway <= 3; gateway++) {    // gateway layer: 3 attempts PER client attempt
                for (int service = 1; service <= 3; service++) { // service layer: 3 attempts PER gateway attempt
                    multiLayerInnermostCalls++;
                }
            }
        }
    }

    static void singleLayerCallChain() {
        for (int client = 1; client <= 3; client++) { // ONLY the client retries
            singleLayerInnermostCalls++;
        }
    }

    public static void main(String[] args) {
        int concurrentClients = 100; // a realistic burst during a sustained outage

        for (int i = 0; i < concurrentClients; i++) multiLayerCallChain();
        for (int i = 0; i < concurrentClients; i++) singleLayerCallChain();

        System.out.println(concurrentClients + " concurrent clients, each with 1 original logical request:");
        System.out.println("Multi-layer independent retries -- innermost dependency receives: " + multiLayerInnermostCalls + " calls");
        System.out.println("Single-layer (outermost only) retries -- innermost dependency receives: " + singleLayerInnermostCalls + " calls");
        System.out.println("\nAmplification factor: multi-layer = " + (multiLayerInnermostCalls / concurrentClients) +
            "x per client, single-layer = " + (singleLayerInnermostCalls / concurrentClients) + "x per client.");
        System.out.println("The multi-layer chain, during a SUSTAINED failure, hits the struggling dependency " +
            (multiLayerInnermostCalls / singleLayerInnermostCalls) + "x HARDER than the single-layer approach.");
    }
}
```

**How to run:** `javac MeasuredStormUnderConcurrentClients.java && java MeasuredStormUnderConcurrentClients` (JDK 17+).

Expected output:
```
100 concurrent clients, each with 1 original logical request:
Multi-layer independent retries -- innermost dependency receives: 2700 calls
Single-layer (outermost only) retries -- innermost dependency receives: 300 calls

Amplification factor: multi-layer = 27x per client, single-layer = 3x per client.
The multi-layer chain, during a SUSTAINED failure, hits the struggling dependency 9x HARDER than the single-layer approach.
```

## 6. Walkthrough

1. **Level 1, the multiplicative compounding traced explicitly** — `callFromClient`'s loop calls `callGateway` up to 3 times, and *each* of those calls runs `callGateway`'s own loop, which calls `callService` up to 3 more times, and *each* of *those* calls runs `callService`'s own loop, calling `callInnermostDependency` up to 3 more times — the innermost function ends up called `3 × 3 × 3 = 27` times from a single top-level invocation, exactly matching the printed count.
2. **Level 1, why this is dangerous** — none of the three layers individually looks unreasonable in isolation (each retries "only" 3 times), but their combination, entirely invisible from looking at any single layer's code alone, produces a 27x amplification at the dependency that's actually struggling — a system designed layer-by-layer without considering this compounding can accidentally build exactly this structure.
3. **Level 2, retrying at only one layer** — `callService` and `callGateway` are now simple pass-through calls with no retry loop of their own; only `callFromClient`, the outermost layer that actually represents the true end-to-end logical operation, contains a retry loop.
4. **Level 2, the resulting linear (not multiplicative) count** — `innermostCallCount` ends at exactly 3, matching the client's own retry count directly, since no intermediate layer adds its own independent multiplication on top.
5. **Level 3, scaling both approaches to a realistic concurrent load** — `multiLayerCallChain` and `singleLayerCallChain` each model the identical per-request retry structure from Levels 1 and 2 respectively, and both are run 100 times to simulate 100 concurrent client requests, all experiencing the same sustained downstream failure simultaneously.
6. **Level 3, the measured real-world-scale difference** — the multi-layer approach results in 2700 total calls to the innermost dependency (27 per client × 100 clients), while the single-layer approach results in only 300 (3 per client × 100 clients) — a 9x difference in aggregate load hitting the exact dependency that's already struggling, purely as a consequence of *where* in the call chain retry logic is placed, not how aggressive any individual layer's retry configuration looks on its own; this measured, concrete gap is exactly what makes retry storms a real, severe risk rather than a theoretical concern, and exactly why coordinating retry responsibility to a single, deliberate layer of a call chain (rather than adding it independently at every layer "just in case") is a critical design decision.

## 7. Gotchas & takeaways

> **Gotcha:** the "retry only at the outermost layer" principle demonstrated in Level 2 is a useful simplification, but real systems sometimes have legitimate reasons for retries at more than one layer (a gateway retrying a load-balancer-level routing failure independently of the client's own application-level retry logic) — the actual guiding principle is to be *deliberate and aware* of how many layers retry independently and what the resulting worst-case multiplication is, not to assume every layer needs its own retry logic, and not to assume retries must be confined to exactly one layer either; the danger is *unintentional*, unaccounted-for compounding, not multi-layer retrying per se.

- A retry storm occurs when retries, instead of aiding recovery, amplify load on an already-struggling dependency, potentially turning a brief blip into a severe, prolonged outage.
- Retry counts compound multiplicatively, not additively, across independently-retrying layers of a call chain — three layers each retrying three times produces a worst-case 27x multiplier, not 9.
- This risk emerges from the combination of missing or under-tuned safeguards (unbounded attempts, indiscriminate retrying of non-transient errors, no retry budget, no jitter) rather than any single factor alone.
- Consolidating retry responsibility to a deliberate, specific layer of a call chain — rather than adding independent retry logic at every layer by default — prevents unintentional multiplicative amplification.
- The other topics in this cluster (budgets, classification, backoff, jitter, bounded attempts) each address one contributing factor; retry storm risk is what results when several of them are simultaneously absent or poorly tuned across a real system.
