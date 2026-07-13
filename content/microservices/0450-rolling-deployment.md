---
card: microservices
gi: 450
slug: rolling-deployment
title: "Rolling deployment"
---

## 1. What it is

A **rolling deployment** replaces instances of a service with a new version incrementally, one (or a small batch) at a time, rather than stopping every instance and starting the new version all at once. At every point during the rollout, some instances run the old version and some run the new version, and the pool of *available* capacity never drops to zero — traffic keeps being served throughout the entire deployment.

## 2. Why & when

You need a rolling deployment strategy the moment a service must stay available while it's being updated, which in practice is nearly every production microservice:

- **A "stop everything, start the new version" deploy causes a visible outage** for exactly as long as the new version takes to start — unacceptable for anything user-facing with real availability requirements.
- **Incremental replacement bounds the blast radius of a bad release.** If the new version is broken, only the instances already replaced are affected, not the whole fleet at once — and a health-gated rollout (Level 2 onward in this topic) can catch the problem after the first replacement, well before it reaches every instance.
- **It's the default strategy for a Kubernetes Deployment** — when you update a Deployment's Pod template, Kubernetes performs a rolling update automatically unless you configure a different strategy, making this the behavior you get "for free" and should understand even if you never write custom rollout logic.
- **You choose it whenever you want a middle ground between deployment speed and risk exposure** — it's slower than an all-at-once deploy but touches only a fraction of capacity at any moment, and it's simpler to operate than the two full parallel environments a [blue-green deployment](0451-blue-green-deployment.md) requires.

## 3. Core concept

Think of resurfacing a busy road one lane at a time instead of closing the whole road. Traffic keeps flowing throughout the work — slower, on fewer lanes, but never fully stopped — and if a problem shows up on the lane just resurfaced (a defect in the new asphalt), the crew can stop before touching the remaining lanes, leaving most of the road on the proven, working surface.

Concretely, the mechanics are:

1. **Replace instances incrementally**, typically one at a time (or a configurable batch size), rather than all simultaneously.
2. **Never let total available capacity drop below a safe floor.** A common pattern is `maxSurge` (how many *extra* instances can exist temporarily, above the desired count, while a new one comes up) and `maxUnavailable` (how many instances can be briefly missing from the pool during the swap) — Kubernetes Deployments expose both settings directly.
3. **Gate each step on a health check.** A newly started instance shouldn't be considered "replacing" the old one until it's actually healthy and ready to serve traffic (see [health checks for orchestrators](0445-health-checks-for-orchestrators.md)) — replacing based on "process started" rather than "process is healthy" can silently roll out a broken version.
4. **Pause and roll back on failure.** If a new instance fails its health check partway through the rollout, the correct response is to stop touching further instances immediately, and typically to roll the already-upgraded instances back to the previous known-good version rather than leaving the fleet in a mixed, partially broken state.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A rolling deployment replaces instances one at a time, health-checking each new instance before retiring the old one and moving to the next, and pausing to roll back if a health check fails">
  <text x="320" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">fleet of 4 instances, rolling v1 -&gt; v2</text>

  <rect x="30" y="40" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="60" y="61" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">i-1 v2</text>
  <rect x="100" y="40" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="61" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">i-2 v2</text>
  <rect x="170" y="40" width="60" height="34" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="200" y="61" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">i-3 v2 FAIL</text>
  <rect x="240" y="40" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="270" y="61" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">i-4 v1</text>

  <text x="165" y="100" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">i-3's health check fails -- pause, then roll back i-1 and i-2</text>

  <rect x="30" y="130" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="151" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">i-1 v1</text>
  <rect x="100" y="130" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="151" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">i-2 v1</text>
  <rect x="170" y="130" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="200" y="151" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">i-3 v1</text>
  <rect x="240" y="130" width="60" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="270" y="151" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">i-4 v1</text>
  <text x="165" y="190" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">fleet restored to the last fully known-good version</text>
</svg>

A rolling deployment gates each replacement on a health check; a failure partway through pauses further replacement and rolls the already-upgraded instances back.

## 5. Runnable example

Scenario: a four-instance fleet rolling from `v1` to `v2`. We start with the bare one-at-a-time replacement, add a health-check gate before each old instance is retired, then handle the hard case: the third instance's new version fails its health check, requiring the rollout to pause and roll the already-upgraded instances back rather than continuing or leaving the fleet in a mixed state.

### Level 1 — Basic

```java
// File: RollingDeploymentBasic.java -- models the CORE idea: replace
// instances ONE AT A TIME, so the pool never drops to zero capacity, until
// every instance runs the new version.
import java.util.*;

public class RollingDeploymentBasic {
    static class Instance {
        final String name;
        String version;
        Instance(String name, String version) { this.name = name; this.version = version; }
        public String toString() { return name + "@" + version; }
    }

    public static void main(String[] args) {
        List<Instance> pool = new ArrayList<>(List.of(
                new Instance("i-1", "v1"), new Instance("i-2", "v1"), new Instance("i-3", "v1")));
        String newVersion = "v2";

        System.out.println("Before rollout: " + pool);

        for (int i = 0; i < pool.size(); i++) {
            Instance old = pool.get(i);
            System.out.println("Replacing " + old + " with " + old.name + "@" + newVersion + " -- pool stays at " + pool.size() + " capacity throughout");
            pool.set(i, new Instance(old.name, newVersion));
            System.out.println("  pool now: " + pool);
        }

        System.out.println("After rollout: " + pool);
    }
}
```

How to run: `java RollingDeploymentBasic.java`

The loop replaces exactly one element of `pool` per iteration, so `pool.size()` never changes — the fleet always has three instances present, just a shifting mix of `v1` and `v2` as the loop progresses. This is the bare mechanical shape of a rolling deployment, before any health gating.

### Level 2 — Intermediate

```java
// File: RollingDeploymentWithHealthGate.java -- the SAME one-at-a-time
// replacement, now GATED by a health check: a new instance must pass its
// health check before the old instance it's replacing is torn down, and
// before the rollout proceeds to the next instance.
import java.util.*;

public class RollingDeploymentWithHealthGate {
    static class Instance {
        final String name;
        final String version;
        boolean healthy;
        Instance(String name, String version, boolean healthy) { this.name = name; this.version = version; this.healthy = healthy; }
        public String toString() { return name + "@" + version + (healthy ? "" : "(unhealthy)"); }
    }

    // Simulates waiting for a health check to pass after starting an instance.
    static boolean waitForHealthy(Instance inst) {
        System.out.println("  health-checking " + inst.name + "@" + inst.version + "...");
        return inst.healthy; // in Level 2, everything comes up healthy
    }

    public static void main(String[] args) {
        List<Instance> pool = new ArrayList<>(List.of(
                new Instance("i-1", "v1", true), new Instance("i-2", "v1", true), new Instance("i-3", "v1", true)));
        String newVersion = "v2";

        for (int i = 0; i < pool.size(); i++) {
            Instance old = pool.get(i);
            Instance replacement = new Instance(old.name, newVersion, true);
            System.out.println("Starting " + replacement + " alongside " + old + " (surge +1)");

            if (!waitForHealthy(replacement)) {
                System.out.println("  " + replacement + " failed health check -- ABORTING rollout, leaving " + old + " in place");
                return;
            }

            pool.set(i, replacement);
            System.out.println("  " + replacement + " healthy -- retiring " + old + ". pool now: " + pool);
        }

        System.out.println("Rollout complete: " + pool);
    }
}
```

How to run: `java RollingDeploymentWithHealthGate.java`

Each step now starts a `replacement` alongside the existing instance — a brief surge above the steady-state count — and only calls `pool.set(i, replacement)` (retiring the old instance) after `waitForHealthy` confirms the new one is actually ready. If the new instance is never healthy, the rollout aborts immediately instead of blindly proceeding to the next instance with a broken version already live.

### Level 3 — Advanced

```java
// File: RollingDeploymentWithRollback.java -- the SAME health-gated
// rollout, now handling a PRODUCTION-FLAVORED hard case: the new version
// is healthy for the first two instances, then FAILS its health check on
// the third. The rollout must pause immediately (stop touching further
// instances) and then roll back the instances already upgraded, restoring
// the fleet to a fully known-good state rather than limping along
// half-upgraded.
import java.util.*;

public class RollingDeploymentWithRollback {
    static class Instance {
        final String name;
        String version;
        Instance(String name, String version) { this.name = name; this.version = version; }
        public String toString() { return name + "@" + version; }
    }

    // pod named "i-3" has a bad v2 build that never becomes healthy.
    static boolean waitForHealthy(String name, String version) {
        System.out.println("  health-checking " + name + "@" + version + "...");
        return !(name.equals("i-3") && version.equals("v2"));
    }

    public static void main(String[] args) {
        List<Instance> pool = new ArrayList<>(List.of(
                new Instance("i-1", "v1"), new Instance("i-2", "v1"),
                new Instance("i-3", "v1"), new Instance("i-4", "v1")));
        String oldVersion = "v1";
        String newVersion = "v2";
        List<String> upgraded = new ArrayList<>();

        for (int i = 0; i < pool.size(); i++) {
            Instance inst = pool.get(i);
            System.out.println("Upgrading " + inst.name + " to " + newVersion + "...");

            if (!waitForHealthy(inst.name, newVersion)) {
                System.out.println("  " + inst.name + "@" + newVersion + " FAILED health check -- PAUSING rollout, " + inst.name + " NOT upgraded");
                System.out.println("Rolling back already-upgraded instances " + upgraded + " to " + oldVersion + "...");
                for (Instance rollbackTarget : pool) {
                    if (upgraded.contains(rollbackTarget.name)) {
                        rollbackTarget.version = oldVersion;
                        System.out.println("  " + rollbackTarget.name + " rolled back to " + oldVersion);
                    }
                }
                System.out.println("Final fleet state after rollback: " + pool);
                return;
            }

            inst.version = newVersion;
            upgraded.add(inst.name);
            System.out.println("  " + inst.name + "@" + newVersion + " healthy. pool now: " + pool);
        }

        System.out.println("Rollout complete: " + pool);
    }
}
```

How to run: `java RollingDeploymentWithRollback.java`

`waitForHealthy` deliberately fails only for `i-3` running `v2`, modeling a defect that surfaces only on that specific instance (or, just as plausibly, a defect that would surface on every instance, first caught here). `upgraded` tracks which instances have already been successfully moved to `v2`. When `i-3` fails its check, the rollout doesn't touch `i-4` at all, and instead walks back through `upgraded` (`i-1` and `i-2`) restoring each to `oldVersion` — leaving the entire fleet on the last version that's actually proven to work.

## 6. Walkthrough

Trace `RollingDeploymentWithRollback.main` in order. **First**, `pool` starts as four instances all on `v1`, and `upgraded` is empty.

**Next**, the loop processes `i-1`: `waitForHealthy("i-1", "v2")` returns `true` (not the special-cased `i-3`), so `inst.version` is set to `v2` and `"i-1"` is appended to `upgraded`. The same happens for `i-2` in the next iteration — `upgraded` is now `["i-1", "i-2"]`, and both instances are running `v2` in `pool`.

**Then**, the loop reaches `i-3`. `waitForHealthy("i-3", "v2")` evaluates `!(name.equals("i-3") && version.equals("v2"))`, which is `!(true && true) = false` — the health check fails. The rollout enters the failure branch: it prints the pause message, then iterates `pool` looking for any instance whose name is in `upgraded`. It finds `i-1` and `i-2`, sets each `version` back to `oldVersion` (`v1`), and prints the rollback confirmation for each. Critically, `i-3` and `i-4` are untouched by this loop — `i-3` was never added to `upgraded` (its upgrade failed before that line ran), and `i-4` was never reached at all.

**Finally**, the method returns immediately after printing the fleet's final state, without ever executing the loop body for `i-4` — the pause is absolute, not just a skip-and-continue.

```
Upgrading i-1 to v2...
  health-checking i-1@v2...
  i-1@v2 healthy. pool now: [i-1@v2, i-2@v1, i-3@v1, i-4@v1]
Upgrading i-2 to v2...
  health-checking i-2@v2...
  i-2@v2 healthy. pool now: [i-1@v2, i-2@v2, i-3@v1, i-4@v1]
Upgrading i-3 to v2...
  health-checking i-3@v2...
  i-3@v2 FAILED health check -- PAUSING rollout, i-3 NOT upgraded
Rolling back already-upgraded instances [i-1, i-2] to v1...
  i-1 rolled back to v1
  i-2 rolled back to v1
Final fleet state after rollback: [i-1@v1, i-2@v1, i-3@v1, i-4@v1]
```

## 7. Gotchas & takeaways

> A rolling deployment that gates on "the process started" instead of "the process is healthy and ready" will happily roll a broken version out to 100% of the fleet, one instance at a time, with each individual step looking perfectly fine in isolation — the health check is the entire safety mechanism, and a weak or missing one turns a rolling deployment into a slow-motion outage.

- Because old and new versions run simultaneously during the rollout, both versions must be able to coexist safely — compatible API contracts, compatible database schema, no assumption that "only one version is ever live" (see [provider vs consumer contracts](0416-provider-vs-consumer-contracts.md) for the API-compatibility discipline this requires).
- Gate every replacement on a real health check, not just process liveness — see [health checks for orchestrators](0445-health-checks-for-orchestrators.md) for the readiness-versus-liveness distinction that should drive this gate.
- On failure, prefer pausing and rolling back over continuing — a partially rolled-out broken version left in place is a worse state than either "fully old" or "fully new."
- Rolling deployment trades speed for safety compared to replacing everything at once, but is simpler to operate than running two complete parallel environments, which is the trade-off [blue-green deployment](0451-blue-green-deployment.md) makes instead.
- A rolling deployment upgrades a fixed set of instances gradually; releasing to a *subset of traffic* rather than a subset of instances is the different technique covered in [canary release](0452-canary-release.md).
