---
card: system-design
gi: 139
slug: chaos-engineering
title: Chaos engineering
---

## 1. What it is

**Chaos engineering** is the practice of deliberately injecting failures into a system — killing a server, adding artificial network latency, cutting off a dependency — while it is running, to verify that the resilience mechanisms you built (redundancy, timeouts, circuit breakers, fallbacks) actually work as intended, rather than assuming they do because the design looks correct on paper.

## 2. Why & when

Every resilience mechanism covered so far — [redundancy](0130-redundancy-replication.md), [timeouts](0134-timeouts.md), [circuit breakers](0136-circuit-breaker.md), [fallbacks](0138-fallbacks-graceful-degradation.md) — is code, and code can have bugs, misconfiguration, or untested edge cases, same as any other code. A resilience mechanism that has never actually been triggered by a real failure is untested, no matter how confident the design looks. Chaos engineering closes this gap by deliberately causing the failures a design claims to handle, in a controlled way, so you find out whether it actually works *before* a real, uncontrolled failure does the same test for you, in production, at the worst possible time. Use it once a system has resilience mechanisms in place worth verifying — there is little point testing failure handling for a system with none.

## 3. Core concept

- **Start small, in a controlled blast radius:** begin chaos experiments against a small slice of traffic or a non-critical service, not the entire production system at once, so a mistake in the experiment itself does not cause a real outage.
- **Form a hypothesis first:** before running an experiment, state what you expect to happen (e.g. "if this instance dies, the load balancer should reroute traffic within 5 seconds with no failed requests") — the experiment either confirms or refutes this specific, testable claim.
- **Common failure injections:** killing a process or instance, adding artificial network latency or packet loss, exhausting a resource (CPU, memory, disk), or blocking access to a specific dependency.
- **Observe, don't just survive:** the goal is not merely "did the system stay up," but confirming the *specific* expected mechanism (a circuit breaker tripping, a fallback engaging, traffic rerouting) actually activated correctly and within the expected time.
- **Game days:** a scheduled, planned exercise where a team deliberately triggers a realistic failure scenario together, to practice both the system's automated response and the team's own incident-response process at the same time.
- **A safety mechanism (an "abort button"):** any chaos experiment needs a fast, reliable way to stop the injected failure immediately if the system does not behave as expected, to prevent an experiment from becoming a real incident.

## 4. Diagram

```
1. HYPOTHESIS: "if instance B dies, load balancer reroutes
    within 5s, checkout success rate stays above 99%"

2. INJECT FAILURE (small blast radius):
    kill instance B, deliberately, during low-traffic hours

3. OBSERVE:
    t=0s: instance B killed
    t=2s: health check detects failure, removes B from rotation
    t=2s: checkout success rate: still 99.8% (traffic rerouted to A, C)

4. CONCLUSION: hypothesis CONFIRMED - failover worked as designed
   (if it had NOT recovered in time, this is discovered safely now,
    not during a real, uncontrolled outage later)
```
*Caption: a chaos experiment states a hypothesis, injects a real but controlled failure, and observes whether the expected resilience mechanism actually activates.*

## 5. Runnable example

**Level 1 — Basic.** State a hypothesis, inject a simulated failure, and check whether the expected mechanism activates.

**Level 2 — Detect a resilience gap.** An experiment reveals a fallback that does not actually work as designed.

**Level 3 — Confirm the fix.** Re-run the same experiment after fixing the gap, and confirm the hypothesis now holds.

```java
// ChaosEngineering.java
import java.util.*;

public class ChaosEngineering {

    record ExperimentResult(String hypothesis, boolean confirmed, String observation) {}

    // Models a system with a circuit breaker + fallback, and a deliberately introduced bug in the fallback.
    static ExperimentResult runExperiment(boolean fallbackHasBug) {
        String hypothesis = "if the recommendations service fails, the fallback returns a static default with no error";

        // INJECT FAILURE: simulate the recommendations service being down.
        boolean recommendationsServiceHealthy = false;
        System.out.println("chaos injection: recommendations service killed");

        String observation;
        boolean confirmed;
        try {
            if (!recommendationsServiceHealthy) {
                if (fallbackHasBug) {
                    // the bug: the "fallback" code itself has an unguarded call that also fails.
                    throw new RuntimeException("fallback itself threw an unhandled exception (a bug!)");
                }
                String fallbackResult = "Popular Item X, Popular Item Y"; // the fallback working as intended
                observation = "fallback engaged successfully, returned: " + fallbackResult;
                confirmed = true;
            } else {
                observation = "service was healthy, fallback not needed";
                confirmed = true;
            }
        } catch (RuntimeException e) {
            observation = "UNEXPECTED FAILURE: " + e.getMessage() + " - the whole request failed instead of degrading gracefully";
            confirmed = false;
        }

        return new ExperimentResult(hypothesis, confirmed, observation);
    }

    public static void main(String[] args) {
        // Level 1 & 2: run the experiment against the CURRENT (buggy) fallback implementation.
        System.out.println("--- chaos experiment run 1 (fallback has an undiscovered bug) ---");
        ExperimentResult run1 = runExperiment(true);
        System.out.println("hypothesis: " + run1.hypothesis());
        System.out.println("observation: " + run1.observation());
        System.out.println("hypothesis confirmed? " + run1.confirmed());
        if (!run1.confirmed()) {
            System.out.println("-> chaos engineering caught a real resilience gap, SAFELY, before a real outage would have");
        }

        // Level 3: after fixing the fallback bug, re-run the SAME experiment to confirm the fix.
        System.out.println("--- fix applied to the fallback code ---");
        System.out.println("--- chaos experiment run 2 (re-verifying the fix) ---");
        ExperimentResult run2 = runExperiment(false);
        System.out.println("observation: " + run2.observation());
        System.out.println("hypothesis confirmed? " + run2.confirmed());
    }
}
```

**How to run:** save as `ChaosEngineering.java`, then run `java ChaosEngineering.java`.

## 6. Walkthrough

1. `runExperiment` first states its `hypothesis` explicitly, then injects the failure by setting `recommendationsServiceHealthy = false` — modeling deliberately killing that dependency, the "chaos injection" step.
2. Run 1 passes `fallbackHasBug = true`; inside the `catch`-guarded block, this deliberately introduced bug throws a `RuntimeException` *from within the fallback path itself*, which the outer `catch` block catches, setting `confirmed = false` and recording the unexpected failure.
3. The printed observation shows the resilience mechanism did not work as hoped: instead of gracefully degrading, the fallback itself broke, causing the whole request to fail — this is exactly the kind of gap chaos engineering is designed to surface, safely, in a controlled experiment.
4. Run 2 passes `fallbackHasBug = false`, modeling the bug having been fixed after the first experiment revealed it; this time the fallback path completes normally, returning the static default list without throwing.
5. `run2.confirmed()` prints `true`, confirming the hypothesis now genuinely holds — the same experiment, re-run after a real fix, demonstrates the resilience mechanism now actually works as designed, closing the loop from "assumed to work" to "verified to work."

## 7. Gotchas & takeaways

> Gotcha: running chaos experiments directly against full production traffic, with no abort mechanism and no communication to the team, is how a controlled experiment turns into an actual incident. Always start with a small blast radius, have a fast way to halt the experiment, and make sure the on-call team knows an experiment is happening so they do not mistake it for a real, unplanned outage.

- Chaos engineering deliberately injects real failures to verify that a system's resilience mechanisms actually work, rather than assuming they do based on design alone.
- A good experiment states a specific, testable hypothesis up front, and observes whether the expected mechanism (failover, a circuit breaker, a fallback) actually activates as intended.
- Starting with a small, controlled blast radius and having a fast abort mechanism keeps a chaos experiment from becoming a real incident itself.
- Related concepts: [Circuit breaker](0136-circuit-breaker.md), [Fallbacks & graceful degradation](0138-fallbacks-graceful-degradation.md), and [Redundancy & replication](0130-redundancy-replication.md) (the mechanisms chaos engineering exists specifically to verify).
