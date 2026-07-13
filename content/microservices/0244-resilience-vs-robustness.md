---
card: microservices
gi: 244
slug: resilience-vs-robustness
title: "Resilience vs robustness"
---

## 1. What it is

Robustness is a system's ability to resist a known, anticipated set of disturbances without changing behavior — like a car's suspension absorbing a pothole. Resilience is a system's ability to adapt and recover when something *unanticipated* happens, including situations its designers never explicitly planned for — surviving, degrading gracefully, or recovering, even from surprises. The two are related but distinct properties, and a system can be strong in one while weak in the other.

## 2. Why & when

A system engineered purely for robustness — hardened against every failure mode its designers thought to enumerate — can still be fragile against the failure modes they *didn't* anticipate, and worse, heavy robustness engineering against known scenarios can sometimes make a system more rigid and harder to adapt when something genuinely novel occurs (a robust system optimized for "handle dependency X being slow" might have no graceful path at all for "dependency X returns malformed data in a new way"). Resilience-oriented design instead favors general-purpose adaptive mechanisms — [circuit breakers](0248-circuit-breaker-pattern.md) that react to *any* kind of failure signal, [graceful degradation](0245-graceful-degradation.md) that falls back regardless of the specific cause, [bulkheads](0242-fault-isolation.md) that contain *any* kind of resource exhaustion — that work correctly even against failure modes nobody explicitly designed for.

Invest in robustness for well-understood, high-probability failure modes worth handling precisely (validating a specific malformed input format that's known to occur regularly). Invest in resilience mechanisms as the general safety net underneath everything else, since a real production system inevitably encounters failure modes nobody anticipated in advance — resilience is what determines whether those genuinely unexpected situations are survivable.

## 3. Core concept

Robustness mechanisms check for and handle *specific, known* conditions; resilience mechanisms react to a *general signal* (a failure, a timeout, a resource threshold) regardless of its specific underlying cause, which is what lets them protect against situations nobody explicitly enumerated in advance.

```java
// ROBUSTNESS -- handles a SPECIFIC, KNOWN failure mode precisely
if (response.getStatusCode() == 429) { // "known": this specific dependency rate-limits at exactly this code
    Thread.sleep(parseRetryAfterHeader(response)); // a PRECISE, tailored response to a KNOWN scenario
}

// RESILIENCE -- reacts to a GENERAL signal, regardless of WHY it's failing
CircuitBreaker breaker = CircuitBreaker.ofDefaults("dependency");
breaker.executeSupplier(() -> callDependency());
// the breaker trips on ANY kind of failure -- a 429, a timeout, a connection refusal, a malformed response
// nobody had to ANTICIPATE the specific failure mode for this protection to work
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Robustness handles specific, anticipated failure modes precisely, covering only the scenarios its designers enumerated; resilience reacts to a general failure signal regardless of cause, covering both anticipated and unanticipated scenarios" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Robustness</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">handles KNOWN scenarios precisely</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">gaps against the UNANTICIPATED</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Resilience</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">reacts to ANY failure signal</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">covers the UNANTICIPATED too</text>

  <rect x="180" y="115" width="280" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="137" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Both are needed together, not either/or</text>
</svg>

Robustness excels at known scenarios; resilience is the general safety net for whatever nobody thought to enumerate.

## 5. Runnable example

Scenario: a dependency-calling client that starts with robustness handling for one specific, known failure mode (a 429 rate-limit response) but nothing protecting against a different, unanticipated failure mode, refactors to add a general resilience mechanism reacting to any kind of failure, and finally demonstrates the resilience mechanism successfully protecting against a genuinely novel failure mode that the robustness handling was never designed for.

### Level 1 — Basic

```java
// File: RobustAgainstOneKnownScenario.java -- handles ONE specific,
// KNOWN failure mode (HTTP 429) precisely -- but has NOTHING for
// anything else that might go wrong.
public class RobustAgainstOneKnownScenario {
    static int callCount = 0;

    // simulates a dependency: first call returns 429 (KNOWN, anticipated); later behavior UNANTICIPATED
    static int simulateCall() {
        callCount++;
        if (callCount == 1) return 429; // the ONE scenario this code was built to handle
        return 500; // an UNANTICIPATED scenario -- e.g. the dependency starts returning generic server errors
    }

    static String callDependency() throws InterruptedException {
        int status = simulateCall();
        if (status == 429) {
            System.out.println("  [robustness] 429 detected -- KNOWN scenario, waiting and retrying precisely");
            Thread.sleep(10);
            status = simulateCall();
        }
        // NOTHING handles status == 500 -- this scenario was NEVER anticipated
        if (status != 200) throw new RuntimeException("unhandled status: " + status);
        return "success";
    }

    public static void main(String[] args) throws Exception {
        try {
            String result = callDependency();
            System.out.println("Result: " + result);
        } catch (RuntimeException e) {
            System.out.println("UNPROTECTED failure: " + e.getMessage() + " -- no general safety net existed for this.");
        }
    }
}
```

**How to run:** `javac RobustAgainstOneKnownScenario.java && java RobustAgainstOneKnownScenario` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ResilientAgainstAnyFailure.java -- adds a GENERAL resilience
// mechanism reacting to ANY failure signal, alongside the SPECIFIC
// robustness handling -- both layers working together.
public class ResilientAgainstAnyFailure {
    static int callCount = 0;
    static boolean breakerOpen = false;
    static int consecutiveFailures = 0;

    static int simulateCall() {
        callCount++;
        if (callCount == 1) return 429;
        return 500; // still the SAME unanticipated scenario as Level 1
    }

    static String callDependencyRobustly() {
        int status = simulateCall();
        if (status == 429) {
            System.out.println("  [robustness] 429 detected -- KNOWN scenario handled precisely");
            status = simulateCall();
        }
        if (status != 200) throw new RuntimeException("unhandled status: " + status);
        return "success";
    }

    static String callDependencyResiliently() {
        if (breakerOpen) return "FALLBACK (breaker open)";
        try {
            return callDependencyRobustly(); // the ROBUSTNESS layer still runs INSIDE the resilience layer
        } catch (RuntimeException e) {
            consecutiveFailures++;
            if (consecutiveFailures >= 1) { breakerOpen = true; } // trips on ANY unhandled failure, KNOWN or not
            System.out.println("  [resilience] GENERAL failure signal caught -- falling back safely, regardless of the specific cause");
            return "FALLBACK (just failed)";
        }
    }

    public static void main(String[] args) {
        String result = callDependencyResiliently();
        System.out.println("Result: " + result + " -- the system SURVIVED, even though this specific failure mode (500) was never explicitly anticipated.");
    }
}
```

**How to run:** `javac ResilientAgainstAnyFailure.java && java ResilientAgainstAnyFailure` (JDK 17+).

Expected output:
```
  [robustness] 429 detected -- KNOWN scenario handled precisely
  [resilience] GENERAL failure signal caught -- falling back safely, regardless of the specific cause
Result: FALLBACK (just failed) -- the system SURVIVED, even though this specific failure mode (500) was never explicitly anticipated.
```

### Level 3 — Advanced

```java
// File: SurvivingAGenuinelyNovelFailureMode.java -- introduces a THIRD,
// completely DIFFERENT failure mode (a malformed response causing a
// parsing exception) that NEITHER the robustness layer NOR the earlier
// resilience layer's exception type were built for -- yet the GENERAL
// resilience mechanism still protects against it, because it reacts to
// ANY thrown exception, not a specific enumerated list.
public class SurvivingAGenuinelyNovelFailureMode {
    static boolean breakerOpen = false;
    static int consecutiveFailures = 0;

    // a COMPLETELY novel failure mode: malformed data causing a DIFFERENT exception type entirely
    static String simulateMalformedResponseCall() {
        String rawResponse = "{ malformed json !!"; // never anticipated by ANY prior handling
        if (!rawResponse.trim().endsWith("}")) {
            throw new IllegalStateException("response body is malformed JSON"); // a NEW exception type, never seen before
        }
        return rawResponse;
    }

    static String callDependencyResiliently() {
        if (breakerOpen) return "FALLBACK (breaker open)";
        try {
            return simulateMalformedResponseCall(); // NEITHER the 429 handling NOR the 500 handling covers THIS
        } catch (Exception e) { // catches ANY exception type -- GENERAL, not enumerated
            consecutiveFailures++;
            if (consecutiveFailures >= 1) breakerOpen = true;
            System.out.println("  [resilience] caught " + e.getClass().getSimpleName() + " -- a failure type NEVER explicitly anticipated -- falling back anyway");
            return "FALLBACK (novel failure)";
        }
    }

    public static void main(String[] args) {
        String result = callDependencyResiliently();
        System.out.println("Result: " + result);
        System.out.println("The system survived a COMPLETELY novel failure mode -- because resilience mechanisms react to the GENERAL signal (any exception), not a specific, pre-enumerated list.");
    }
}
```

**How to run:** `javac SurvivingAGenuinelyNovelFailureMode.java && java SurvivingAGenuinelyNovelFailureMode` (JDK 17+).

Expected output:
```
  [resilience] caught IllegalStateException -- a failure type NEVER explicitly anticipated -- falling back anyway
Result: FALLBACK (novel failure)
The system survived a COMPLETELY novel failure mode -- because resilience mechanisms react to the GENERAL signal (any exception), not a specific, pre-enumerated list.
```

## 6. Walkthrough

1. **Level 1, robustness's precise but narrow coverage** — `callDependency` explicitly checks for `status == 429` and handles exactly that case with a tailored retry; when `simulateCall` instead returns `500` (a scenario this code never anticipated), there is no corresponding handling at all, and the `RuntimeException` thrown for the unhandled status propagates all the way out uncaught, printed in `main` as an "UNPROTECTED failure."
2. **Level 2, layering resilience underneath robustness** — `callDependencyResiliently` wraps `callDependencyRobustly` (which still contains the exact same precise 429-handling robustness logic from Level 1) in a `try`/`catch` that catches `RuntimeException` generally, not any specific status code; when the same unanticipated 500 scenario occurs, the *robustness* layer still has no specific handling for it, but the *resilience* layer catches the resulting exception anyway.
3. **Level 2, the combined outcome** — the printed log shows both layers active: the robustness layer correctly handles the *known* 429 case precisely, and the resilience layer catches the *unknown* 500 case generally, resulting in a safe fallback rather than an uncaught crash — demonstrating the two working together, not as alternatives to each other.
4. **Level 3, a failure mode from an entirely different category** — `simulateMalformedResponseCall` doesn't return an HTTP status code at all; it throws `IllegalStateException` due to malformed response data, a failure category structurally unrelated to either the 429 or 500 scenarios handled or caught in the earlier levels.
5. **Level 3, the resilience mechanism's generality proven** — `callDependencyResiliently`'s `catch (Exception e)` block catches `IllegalStateException` exactly as readily as it would have caught the earlier `RuntimeException` (of which `IllegalStateException` happens to be a subtype, but the catch would work identically even for an unrelated exception hierarchy, since it catches the general `Exception` type) — nothing about this catch block needed to be modified or extended to handle this new, previously unseen failure type.
6. **Level 3, why this demonstrates the resilience/robustness distinction concretely** — the robustness-style handling from Level 1 and Level 2 (the specific `status == 429` check) provides zero protection here, since there's no status code involved at all in this failure mode; only the general, cause-agnostic resilience mechanism (catching *any* exception and falling back) successfully protects the system against this genuinely novel scenario — precisely illustrating why resilience mechanisms, reacting to a general signal rather than an enumerated list of anticipated causes, are what make a system survivable against failure modes nobody explicitly designed for in advance.

## 7. Gotchas & takeaways

> **Gotcha:** a purely resilience-oriented system that falls back generically on *every* failure, with no robustness-layer precision for well-understood, high-frequency scenarios, can end up masking recurring, fixable problems behind a generic fallback — treating a known, common 429 rate-limit response identically to a rare, catastrophic failure wastes an opportunity to handle the common case efficiently (with a proper backoff) rather than paying the fallback's cost every time; robustness for known scenarios and resilience as the general safety net are complementary, not substitutes for each other.

- Robustness handles specific, anticipated failure modes precisely; resilience reacts to a general failure signal regardless of its specific, possibly unanticipated cause.
- A system can be robust against every failure mode its designers thought to enumerate while still being fragile against a genuinely novel one — resilience mechanisms are what provide protection in that gap.
- Resilience mechanisms (circuit breakers, graceful degradation, bulkheads) work by reacting to general signals — an exception, a timeout, a resource threshold — rather than a specific, enumerated list of known causes.
- The two properties are complementary: robustness handles known, high-frequency scenarios efficiently and precisely, while resilience provides the safety net underneath for everything else, including situations nobody anticipated.
- Relying purely on generic resilience fallbacks for problems that are actually well-understood and recurring wastes an opportunity to handle them more efficiently and precisely with dedicated robustness logic.
