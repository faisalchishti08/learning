---
card: system-design
gi: 219
slug: canary-release-feature-flags
title: Canary release & feature flags
---

## 1. What it is

A **canary release** rolls out a new version to a small percentage of real traffic first, monitors it closely, and gradually increases that percentage only if the new version looks healthy — unlike [blue-green deployment](0218-blue-green-deployment.md), where the cutover is instant and total. A **feature flag** is a runtime switch that turns a specific feature on or off (or on for a subset of users) without a deployment at all, decoupling "deploying code" from "activating a feature" entirely.

## 2. Why & when

Even careful pre-production testing cannot catch every problem — some bugs only show up under real production traffic patterns and real data. A canary release limits the blast radius of that risk: if the new version has a problem, only the small percentage of traffic it received is affected, and you catch it before it reaches everyone. This is a meaningfully different risk profile from blue-green's all-or-nothing cutover.

Feature flags solve an adjacent but distinct problem: sometimes you want to ship code to production (so it is tested and ready) without turning the corresponding user-facing behavior on yet, or you want to turn a feature on for internal users only, or roll a feature out to 5% of users gradually — all without a new deployment for each step. Use canary releases when you are rolling out a *new version* of a service and want to limit exposure to infrastructure-level risk. Use feature flags when you want to control *when and for whom* a specific feature is active, independent of when its code was deployed.

## 3. Core concept

- **Traffic splitting.** A canary release routes a small percentage of requests (e.g. 5%) to the new version and the rest to the current stable version, using the same router/load-balancer mechanism as blue-green, but with a percentage split instead of an all-or-nothing switch.
- **Automated health signals gate the rollout.** A canary's percentage should only increase if error rates, latency, and other key metrics for the canary group stay within acceptable bounds compared to the stable group — a human or an automated system checks this at each step before proceeding.
- **Gradual ramp-up.** A typical canary progresses through stages — 5% → 25% → 50% → 100% — pausing at each stage to observe, rather than jumping straight from a small percentage to full traffic.
- **Feature flags decouple deploy from release.** The code path for a new feature can be deployed to 100% of servers while the flag controlling it is off for 100% of users — "deploying" and "releasing" become two separate, independently controllable actions.
- **Flag targeting rules.** A feature flag's state is not just on/off globally — it can be scoped by user ID, by percentage of users, by user attribute (e.g. "beta testers"), letting you expose a feature to an increasingly wide, precisely chosen audience.

## 4. Diagram

```
  CANARY RELEASE (traffic split by version)     FEATURE FLAG (behavior split by flag state)

  Router                                         Router
    |  95% ---------> Stable (v1.0)                |  100% ---> App (both code paths deployed)
    |   5% ---------> Canary (v1.1)                              |
                                                                    |  flag "new-checkout" = on for:
  watch canary's error rate & latency                                - internal users: YES
  vs stable's, at each stage:                                        - 5% of external users: YES
    5% -> 25% -> 50% -> 100%                                         - everyone else: NO
  (rolls back to 0% if metrics degrade)                            (no new deployment needed to
                                                                      change any of these percentages)
```
*Caption: canary controls which VERSION of the code handles a request. A feature flag controls which BEHAVIOR that code exhibits, once it is already running — the two mechanisms solve different, complementary problems.*

## 5. Runnable example

**Level 1 — Basic.** A canary router splitting traffic by percentage between stable and canary versions.

**Level 2 — Intermediate.** Gate the canary's ramp-up on a health check: only advance to the next stage if the canary's error rate stays acceptable.

**Level 3 — Advanced.** A feature flag with percentage-based and attribute-based targeting, applied independently of which version is currently deployed.

```java
// CanaryFeatureFlagDemo.java
import java.util.*;
import java.util.function.*;

public class CanaryFeatureFlagDemo {

    // ---------- Level 1: canary traffic splitting ----------
    static class CanaryRouter {
        int canaryPercentage; // 0-100
        Random rnd = new Random(42);

        String route(String request) {
            boolean toCanary = rnd.nextInt(100) < canaryPercentage;
            return (toCanary ? "canary (v1.1)" : "stable (v1.0)") + " handled: " + request;
        }
    }

    // ---------- Level 2: health-gated ramp-up ----------
    static class HealthGatedRollout {
        int[] stages = {5, 25, 50, 100};
        int currentStageIndex = 0;
        Function<Integer, Double> canaryErrorRateAtPercentage; // simulated metric source

        HealthGatedRollout(Function<Integer, Double> errorRateSource) { this.canaryErrorRateAtPercentage = errorRateSource; }

        void advanceIfHealthy(double errorRateThreshold) {
            int currentPercentage = stages[currentStageIndex];
            double errorRate = canaryErrorRateAtPercentage.apply(currentPercentage);
            System.out.println("    stage " + currentPercentage + "% canary traffic: error rate = " +
                String.format("%.1f%%", errorRate * 100));
            if (errorRate > errorRateThreshold) {
                System.out.println("    error rate exceeds threshold (" + (errorRateThreshold * 100) +
                    "%) - ROLLING BACK canary to 0%");
                currentStageIndex = -1; // signal: rolled back
                return;
            }
            if (currentStageIndex < stages.length - 1) {
                currentStageIndex++;
                System.out.println("    healthy - advancing to next stage: " + stages[currentStageIndex] + "%");
            } else {
                System.out.println("    healthy - already at 100%, rollout complete");
            }
        }
    }

    // ---------- Level 3: feature flag with percentage + attribute targeting ----------
    static class FeatureFlag {
        String name;
        boolean enabledForInternalUsers;
        int enabledPercentageOfExternalUsers;

        FeatureFlag(String name) { this.name = name; }

        boolean isEnabledFor(String userId, boolean isInternal) {
            if (isInternal) return enabledForInternalUsers;
            int userBucket = Math.abs(userId.hashCode()) % 100; // stable per-user bucket, 0-99
            return userBucket < enabledPercentageOfExternalUsers;
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - canary traffic split, 20% to canary:");
        CanaryRouter router = new CanaryRouter();
        router.canaryPercentage = 20;
        Map<String, Integer> counts = new TreeMap<>();
        for (int i = 0; i < 10; i++) {
            String result = router.route("req-" + i);
            String version = result.startsWith("canary") ? "canary" : "stable";
            counts.merge(version, 1, Integer::sum);
        }
        System.out.println("  distribution over 10 requests: " + counts);

        System.out.println("\nLevel 2 - health-gated ramp-up, canary is healthy at every stage:");
        HealthGatedRollout healthyRollout = new HealthGatedRollout(pct -> 0.01); // always 1% errors
        for (int i = 0; i < 4; i++) healthyRollout.advanceIfHealthy(0.05);

        System.out.println("\n  health-gated ramp-up, canary degrades at 50%:");
        HealthGatedRollout degradingRollout = new HealthGatedRollout(pct -> pct >= 50 ? 0.15 : 0.01);
        for (int i = 0; i < 4 && degradingRollout.currentStageIndex >= 0; i++) degradingRollout.advanceIfHealthy(0.05);

        System.out.println("\nLevel 3 - feature flag targeting, independent of which version is deployed:");
        FeatureFlag newCheckout = new FeatureFlag("new-checkout");
        newCheckout.enabledForInternalUsers = true;
        newCheckout.enabledPercentageOfExternalUsers = 10;
        System.out.println("  internal user 'admin-1': enabled = " + newCheckout.isEnabledFor("admin-1", true));
        for (String user : List.of("user-1", "user-2", "user-3", "user-4", "user-5")) {
            System.out.println("  external user '" + user + "': enabled = " + newCheckout.isEnabledFor(user, false));
        }
    }
}
```

**How to run:** `java CanaryFeatureFlagDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `router.route(...)` is called ten times with `canaryPercentage = 20`. Each call draws a random number 0-99 and sends the request to canary if it falls below 20 — over ten requests, roughly 2 land on canary and 8 on stable, though the exact split varies request by request since each decision is independent.
2. **Level 2 (healthy path):** `healthyRollout.advanceIfHealthy(0.05)` is called four times. Because `canaryErrorRateAtPercentage` always returns `0.01` (1%), which is below the `0.05` (5%) threshold, every call advances `currentStageIndex` — the stages progress 5% → 25% → 50% → 100%, printing "advancing" each time until the last call, which reports the rollout complete.
3. **Level 2 (degrading path):** `degradingRollout`'s error-rate function returns `0.15` (15%) once the stage reaches 50% or higher, but `0.01` below that. The first two calls (at 5% and 25%) stay healthy and advance normally. The **third** call evaluates at the 50% stage, finds `errorRate (0.15) > threshold (0.05)`, prints the rollback message, and sets `currentStageIndex = -1` — the loop condition `degradingRollout.currentStageIndex >= 0` then stops further iterations, since the rollout has been rolled back to 0%.
4. **Level 3:** `newCheckout.isEnabledFor("admin-1", true)` checks the `isInternal` branch directly and returns `enabledForInternalUsers`, which is `true` — internal users get a simple, direct flag check independent of any percentage.
5. For each external user, `isEnabledFor` computes `userBucket = Math.abs(userId.hashCode()) % 100` — a number 0-99 derived deterministically from that specific user's ID — and compares it against `enabledPercentageOfExternalUsers = 10`. Because the bucket is a stable function of the user ID (not a fresh random roll per request), the same user consistently gets the same enabled/disabled result across multiple calls, which is what lets a real feature flag give a user a *consistent* experience rather than flickering on and off between requests.

## 7. Gotchas & takeaways

> **Gotcha:** using a fresh random number on every request for percentage-based flag targeting (instead of a stable hash of the user's own ID, as Level 3 does) makes a feature flicker on and off for the same user between requests — a confusing, inconsistent experience. Always derive percentage-based targeting from something stable per user.

- Automate the canary's health check and rollback decision wherever possible — a human watching a dashboard is slower and less consistent than an automated gate comparing canary metrics against stable metrics at each stage.
- Keep canary stages small enough that a bad rollout is caught while it is still affecting a small fraction of users — jumping straight from 5% to 100% defeats the purpose.
- Feature flags accumulate as technical debt if never cleaned up — once a feature is fully rolled out and stable, remove the flag and the old code path it was gating, rather than leaving the flag in place indefinitely.
- Canary release and feature flags are complementary, not competing: you can canary-release a new version of a service while a feature flag inside that same version controls whether a specific new behavior is active for any given request.
