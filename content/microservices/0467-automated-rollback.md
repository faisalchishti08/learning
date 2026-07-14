---
card: microservices
gi: 467
slug: automated-rollback
title: "Automated rollback"
---

## 1. What it is

**Automated rollback** is a deployment pipeline automatically detecting that a newly-deployed version is unhealthy — via failing health checks, elevated error rates, or other monitored signals — and reverting to the last known-good version **without a human needing to notice the problem and intervene manually**. The pipeline watches its own deployment and undoes it if things go wrong.

## 2. Why & when

You build automated rollback because the time between "a bad deployment starts serving traffic" and "a human notices and reacts" is exactly the window where users experience the outage:

- **Humans are slow compared to automated monitoring.** Even a well-staffed on-call rotation takes minutes to notice an alert, investigate, and decide to roll back — an automated system watching the same signals can react in seconds, shrinking the blast radius dramatically.
- **3am deployments (or any deployment nobody is actively watching) still need protection.** If a deploy happens outside business hours, or an engineer kicks one off and steps away, automated rollback is what catches the failure instead of it running unhealthy until someone happens to check.
- **It removes the emotional and cognitive load of manual rollback decisions during an incident.** Deciding "is this bad enough to roll back" under pressure, mid-incident, is a worse environment for that judgment call than defining the threshold calmly, in advance, as monitored code.
- **You want it on any pipeline handling meaningful production traffic** — paired naturally with a [rolling deployment](0450-rolling-deployment.md) or canary strategy, where a small fraction of traffic hitting the new version gives the system a safe, bounded window to detect trouble before it spreads further.

## 3. Core concept

Think of a home smoke detector versus a person checking for fire by walking through the house periodically: the detector is always watching, reacts within seconds of smoke appearing, and doesn't depend on anyone's attention or schedule. Automated rollback is that smoke detector for a deployment — continuously watching a defined signal, and reacting immediately and consistently the moment that signal crosses a threshold, with no dependence on a human noticing.

Concretely:

1. **A new version is deployed**, typically gradually (a rolling deployment, a canary receiving a small percentage of traffic).
2. **A health signal is continuously monitored** during and after the rollout — error rate, latency, health-check failures, or a custom business metric.
3. **A threshold defines "unhealthy"** — say, error rate above 5% sustained for 60 seconds, or health checks failing for more than N consecutive checks.
4. **If the threshold is crossed, the pipeline automatically triggers a rollback** — redeploying the previous, [versioned](0464-artifact-versioning-promotion.md) artifact, without waiting for any human approval.
5. **The rollback itself is monitored too** — confirming the previous version comes back healthy, and alerting a human either way, since an automated system correcting itself doesn't mean the underlying problem doesn't still need investigation.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A new version is deployed and monitored; if its error rate crosses a threshold, the pipeline automatically rolls back to the previous version" >
  <rect x="20" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">deploy v2.0</text>

  <rect x="240" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">monitor error rate</text>
  <text x="330" y="71" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">threshold: &gt;5% for 60s</text>

  <rect x="460" y="30" width="160" height="50" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="540" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">threshold crossed</text>
  <text x="540" y="71" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">auto-triggered</text>

  <rect x="240" y="130" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">rollback to v1.9</text>
  <text x="330" y="171" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">last known-good</text>

  <line x1="200" y1="55" x2="240" y2="55" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="420" y1="55" x2="460" y2="55" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="540" y1="80" x2="330" y2="130" stroke="#f85149" stroke-width="2" marker-end="url(#a2)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f85149"/></marker>
  </defs>
</svg>

The pipeline monitors the new version's health continuously and automatically triggers a rollback the moment the failure threshold is crossed — no human in the loop.

## 5. Runnable example

Scenario: a deployment monitor watching a new version's error rate and triggering automated rollback. We start with a basic single health check, extend it to sustained monitoring across multiple checks with a threshold, then handle the hard case: distinguishing a brief, transient blip (which should not trigger rollback) from genuinely sustained unhealthiness (which must).

### Level 1 — Basic

```java
// File: AutoRollbackBasic.java -- models deploying a new version and
// checking its health ONCE, rolling back immediately if unhealthy.
public class AutoRollbackBasic {
    static double checkErrorRate(String version) {
        System.out.println("[monitor] checking error rate for " + version);
        return 0.12; // simulated: 12% error rate, clearly unhealthy
    }

    static void rollback(String fromVersion, String toVersion) {
        System.out.println("[pipeline] AUTO-ROLLBACK: " + fromVersion + " -> " + toVersion + " (no human approval needed)");
    }

    public static void main(String[] args) {
        String newVersion = "order-service:2.0";
        String previousVersion = "order-service:1.9";
        double threshold = 0.05; // 5% error rate

        double errorRate = checkErrorRate(newVersion);
        if (errorRate > threshold) {
            System.out.println("[monitor] error rate " + errorRate + " exceeds threshold " + threshold);
            rollback(newVersion, previousVersion);
        } else {
            System.out.println("[monitor] healthy, no action needed");
        }
    }
}
```

How to run: `java AutoRollbackBasic.java`

`checkErrorRate` stands in for a single health check reading, and the `if (errorRate > threshold)` comparison is the entire decision logic — no human is consulted anywhere in this path. `rollback` is called directly and unconditionally once the threshold is crossed, exactly like a real pipeline's automated trigger.

### Level 2 — Intermediate

```java
// File: AutoRollbackSustained.java -- the SAME threshold check, now
// SUSTAINED across multiple monitoring intervals rather than a single
// reading -- rollback only triggers if the error rate stays above
// threshold for several consecutive checks, not on one noisy sample.
import java.util.*;

public class AutoRollbackSustained {
    static void rollback(String fromVersion, String toVersion) {
        System.out.println("[pipeline] AUTO-ROLLBACK: " + fromVersion + " -> " + toVersion);
    }

    public static void main(String[] args) {
        String newVersion = "order-service:2.0";
        String previousVersion = "order-service:1.9";
        double threshold = 0.05;
        int requiredConsecutiveBreaches = 3;

        // Simulated readings across successive monitoring intervals -- consistently bad.
        double[] errorRateReadings = {0.08, 0.09, 0.11, 0.10};

        int consecutiveBreaches = 0;
        for (int i = 0; i < errorRateReadings.length; i++) {
            double rate = errorRateReadings[i];
            System.out.println("[monitor] interval " + (i + 1) + ": error rate " + rate);
            if (rate > threshold) {
                consecutiveBreaches++;
                System.out.println("[monitor] breach " + consecutiveBreaches + "/" + requiredConsecutiveBreaches);
            } else {
                consecutiveBreaches = 0;
            }
            if (consecutiveBreaches >= requiredConsecutiveBreaches) {
                rollback(newVersion, previousVersion);
                break;
            }
        }
    }
}
```

How to run: `java AutoRollbackSustained.java`

`consecutiveBreaches` accumulates across loop iterations rather than triggering on any single reading — each interval above `threshold` increments it, and the rollback only fires once `consecutiveBreaches >= requiredConsecutiveBreaches`. With all four simulated readings above threshold, the count reaches `3` on the third interval and `rollback` fires there, with the `break` stopping further monitoring since the decision is already made.

### Level 3 — Advanced

```java
// File: AutoRollbackTransientVsSustained.java -- the SAME sustained
// monitoring, now handling the PRODUCTION-FLAVORED hard case: a BRIEF,
// TRANSIENT blip (one bad interval, then recovery) must NOT trigger a
// rollback -- only genuinely SUSTAINED unhealthiness should. This is why
// consecutiveBreaches resets to zero on any healthy reading, rather than
// counting total breaches over the whole monitoring window.
public class AutoRollbackTransientVsSustained {
    static void rollback(String fromVersion, String toVersion, String reason) {
        System.out.println("[pipeline] AUTO-ROLLBACK: " + fromVersion + " -> " + toVersion + " (" + reason + ")");
    }

    static boolean monitorAndDecide(String newVersion, String previousVersion, double[] readings, double threshold, int requiredConsecutiveBreaches) {
        int consecutiveBreaches = 0;
        for (int i = 0; i < readings.length; i++) {
            double rate = readings[i];
            boolean breached = rate > threshold;
            System.out.println("[monitor] interval " + (i + 1) + ": error rate " + rate + (breached ? " (BREACH)" : " (healthy)"));
            consecutiveBreaches = breached ? consecutiveBreaches + 1 : 0; // reset on ANY healthy reading
            if (consecutiveBreaches >= requiredConsecutiveBreaches) {
                rollback(newVersion, previousVersion, "sustained error rate for " + requiredConsecutiveBreaches + " consecutive intervals");
                return true;
            }
        }
        System.out.println("[monitor] monitoring window complete -- no sustained breach, deployment stays live");
        return false;
    }

    public static void main(String[] args) {
        double threshold = 0.05;
        int requiredConsecutiveBreaches = 3;

        System.out.println("--- scenario A: transient blip, then recovery ---");
        double[] transientBlip = {0.08, 0.02, 0.01, 0.03}; // one bad interval, then healthy
        boolean rolledBackA = monitorAndDecide("order-service:2.0", "order-service:1.9", transientBlip, threshold, requiredConsecutiveBreaches);

        System.out.println();
        System.out.println("--- scenario B: sustained failure ---");
        double[] sustainedFailure = {0.02, 0.08, 0.09, 0.11}; // healthy, then consistently bad
        boolean rolledBackB = monitorAndDecide("order-service:2.1", "order-service:2.0", sustainedFailure, threshold, requiredConsecutiveBreaches);

        System.out.println();
        System.out.println("[summary] scenario A rolled back: " + rolledBackA + ", scenario B rolled back: " + rolledBackB);
    }
}
```

How to run: `java AutoRollbackTransientVsSustained.java`

`consecutiveBreaches = breached ? consecutiveBreaches + 1 : 0;` is the key line: any single healthy reading resets the count to zero, regardless of how many breaches preceded it. In scenario A, the second reading (`0.02`) is healthy, resetting the count that the first breach had started building — the loop finishes its whole window without ever reaching `requiredConsecutiveBreaches`, so `monitorAndDecide` returns `false`. In scenario B, three breaches happen back to back with no healthy reading between them, so the count reaches `3` and triggers rollback.

## 6. Walkthrough

Trace `AutoRollbackTransientVsSustained.main` in order, starting with scenario A. **First**, `monitorAndDecide` is called with `transientBlip`. Interval 1 (`0.08`) breaches, so `consecutiveBreaches` becomes `1`; this is less than `3`, so the loop continues.

**Next**, interval 2 (`0.02`) does not breach (`breached` is `false`), so `consecutiveBreaches` resets to `0` — the single earlier breach is now forgotten entirely, exactly as intended for a transient blip.

**Then**, intervals 3 and 4 (`0.01`, `0.03`) are both healthy, keeping `consecutiveBreaches` at `0` throughout. The loop reaches its end having never hit the threshold count, so it prints the "no sustained breach" message and returns `false` — no rollback occurs for scenario A.

**After that**, scenario B begins: `monitorAndDecide` is called fresh with `sustainedFailure` (a new call, so `consecutiveBreaches` starts again at `0` inside this new invocation). Interval 1 (`0.02`) is healthy, keeping the count at `0`. Interval 2 (`0.08`) breaches, count becomes `1`. Interval 3 (`0.09`) breaches again with no healthy reading in between, count becomes `2`. Interval 4 (`0.11`) breaches a third consecutive time, count reaches `3`, which meets `requiredConsecutiveBreaches` — `rollback` fires immediately, and `monitorAndDecide` returns `true` without processing any further readings (there are none left anyway).

**Finally**, `main` prints the summary, showing scenario A did not roll back while scenario B did — the exact same threshold and consecutive-breach logic produced two different, correct outcomes based purely on whether the unhealthiness was sustained or merely transient.

```
--- scenario A: transient blip, then recovery ---
[monitor] interval 1: error rate 0.08 (BREACH)
[monitor] interval 2: error rate 0.02 (healthy)
[monitor] interval 3: error rate 0.01 (healthy)
[monitor] interval 4: error rate 0.03 (healthy)
[monitor] monitoring window complete -- no sustained breach, deployment stays live

--- scenario B: sustained failure ---
[monitor] interval 1: error rate 0.02 (healthy)
[monitor] interval 2: error rate 0.08 (BREACH)
[monitor] interval 3: error rate 0.09 (BREACH)
[monitor] interval 4: error rate 0.11 (BREACH)
[pipeline] AUTO-ROLLBACK: order-service:2.1 -> order-service:2.0 (sustained error rate for 3 consecutive intervals)

[summary] scenario A rolled back: false, scenario B rolled back: true
```

## 7. Gotchas & takeaways

> A rollback threshold based on a single reading, rather than sustained breaches, turns automated rollback into a source of instability itself — one noisy sample triggers a rollback, the previous version's own noise triggers a rollback of the rollback, and the system oscillates instead of protecting availability. Always require sustained breach, not a single bad sample.
- Pair automated rollback with a gradual rollout strategy (canary, or a [rolling deployment](0450-rolling-deployment.md)) — detecting a bad version while it's only serving 5% of traffic bounds the damage far more than detecting it after it's fully rolled out.
- The rollback target must be a proven-good, [versioned](0464-artifact-versioning-promotion.md) artifact — rolling back to "whatever was there before" only works if that prior state is precisely identified and still available to redeploy.
- An automated rollback should still page a human — reverting the immediate symptom automatically doesn't mean the underlying bug doesn't need investigation and a real fix.
- Tune the threshold and the required-consecutive-breach count deliberately: too sensitive and normal noise triggers false rollbacks; too lax and real problems run for too long before the system reacts.
- Automated rollback itself needs monitoring — confirm the rollback actually restored healthy behavior, rather than assuming "we rolled back" automatically means "we're fine now."
