---
card: microservices
gi: 451
slug: blue-green-deployment
title: "Blue-green deployment"
---

## 1. What it is

A **blue-green deployment** runs two complete, independent environments — conventionally named "blue" and "green" — where exactly one is **active** (receiving all real user traffic) and the other is **idle**. Deploying a new version means standing it up entirely in the idle environment, verifying it there with zero user impact, and then flipping a router or load balancer to make it active in one atomic switch. The previously active environment isn't torn down immediately — it stays intact as a ready fallback, so rolling back is just flipping the switch back, not redeploying anything.

## 2. Why & when

You reach for blue-green when you want deployment risk concentrated into a single, instantly reversible moment rather than spread across a gradual rollout:

- **Rollback is nearly instant.** Because the old environment is kept running rather than torn down, reverting a bad deploy means flipping the router back — seconds, not the time it takes to redeploy and restart instances, which is what a [rolling deployment](0450-rolling-deployment.md) rollback usually requires.
- **No mixed-version window in production.** Unlike a rolling deployment, where old and new versions serve real traffic simultaneously for the duration of the rollout, blue-green's switch is atomic — every request goes to the old version, or every request goes to the new version, never a mix. This avoids designing for two live versions coexisting, at the cost of needing double the running capacity during the deploy window.
- **The idle environment can be fully verified before it ever sees real traffic** — smoke tests, synthetic checks, even manual verification — since nothing is routed to it until the switch happens.
- **You choose this when the cost of running two full environments is acceptable** and rollback speed matters more than gradual exposure — for a service where a bad deploy is expensive and the infrastructure cost of temporary duplication is not a blocker. It's less suited to very large or very stateful fleets, where running two complete copies is expensive or where in-flight state can't cleanly live in only one environment at a time.

## 3. Core concept

Picture live TV broadcasting from two identical studios, A and B, with a single switch controlling which studio's feed actually goes out to viewers. While studio A is live, the crew can freely rehearse, test lighting, and rehearse in studio B — none of it reaches viewers. Only when B is ready does the director flip the switch, and the broadcast instantly comes from B instead. If something goes wrong the moment B goes live, flipping back to A is just as instant, because A never stopped being ready.

Concretely, the mechanics are:

1. **Two environments, one active pointer.** A router, load balancer, or DNS record holds a reference to whichever environment is currently "active"; the other sits idle, fully deployed but receiving no live traffic.
2. **Deploy into the idle environment only.** The active environment is completely undisturbed during this step — users see no change, no matter how long the new version takes to deploy and warm up.
3. **Gate the switch on verification**, typically smoke tests run directly against the idle environment before it becomes active — catching obviously broken builds before any real user is exposed to them.
4. **Flip the pointer atomically.** All new traffic goes to the newly active environment in one step; there's no gradual ramp, unlike [canary release](0452-canary-release.md).
5. **Keep the old environment intact for a rollback window** rather than tearing it down immediately — this is what makes rollback nearly instant rather than requiring a fresh deploy.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A router points at exactly one of two environments, blue or green; the idle one is deployed and smoke tested before the router flips, and flips back instantly if the newly active environment misbehaves">
  <rect x="20" y="30" width="180" height="70" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="110" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Blue (v1)</text>
  <text x="110" y="72" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ACTIVE -- live traffic</text>

  <rect x="440" y="30" width="180" height="70" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="530" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Green (v2)</text>
  <text x="530" y="72" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">idle -- smoke-tested here first</text>

  <rect x="250" y="140" width="140" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="320" y="170" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Router / LB</text>

  <line x1="320" y1="140" x2="110" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="320" y1="140" x2="530" y2="100" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#a2)"/>

  <text x="320" y="220" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">after a flip to green, an error spike flips the pointer back to blue INSTANTLY -- no redeploy</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The router holds a single pointer to whichever environment is active; the idle environment is fully deployed and testable in isolation, and rollback is just flipping the pointer back.

## 5. Runnable example

Scenario: a service with two environments, blue (currently live on `v1`) and green (idle). We start with the bare pointer-flip mechanism, add a smoke-test gate that must pass before the flip happens, then handle the hard case: green passes its smoke tests but starts throwing real errors once it's actually serving production traffic, requiring an instant rollback that a redeploy-based rolling strategy couldn't match in speed.

### Level 1 — Basic

```java
// File: BlueGreenBasic.java -- models the CORE idea: TWO complete
// environments exist side by side (blue and green); a router points at
// exactly one of them ("active"); deploying means standing up the new
// version in the IDLE environment, then flipping the router pointer.
public class BlueGreenBasic {
    static class Environment {
        final String name;
        final String version;
        Environment(String name, String version) { this.name = name; this.version = version; }
        public String toString() { return name + "@" + version; }
    }

    public static void main(String[] args) {
        Environment blue = new Environment("blue", "v1");
        Environment green = new Environment("green", "idle");
        Environment active = blue;

        System.out.println("Router points at: " + active);
        System.out.println("(green sits idle, ready to receive the next deploy)");

        // Deploy v2 into the IDLE environment (green). Blue keeps serving
        // live traffic, completely undisturbed, throughout this step.
        green = new Environment("green", "v2");
        System.out.println("Deployed " + green + " -- router STILL points at " + active + ", zero user impact so far");

        // Flip the router: ALL traffic switches to green in one atomic step.
        active = green;
        System.out.println("Router flipped -- now points at: " + active);
    }
}
```

How to run: `java BlueGreenBasic.java`

`active` is a single reference that determines which `Environment` receives traffic. Deploying `green` (reassigning it to a new `Environment` with `version = "v2"`) doesn't touch `active` at all — the router keeps pointing at `blue` until the explicit `active = green` line, which is the entire "switch" in one atomic assignment.

### Level 2 — Intermediate

```java
// File: BlueGreenWithSmokeTest.java -- the SAME two-environment model, now
// GATED by a smoke test run against the idle environment BEFORE the router
// is flipped -- catching an obviously broken deploy before it ever reaches
// real users.
public class BlueGreenWithSmokeTest {
    static class Environment {
        final String name;
        final String version;
        final boolean smokeTestPasses;
        Environment(String name, String version, boolean smokeTestPasses) {
            this.name = name; this.version = version; this.smokeTestPasses = smokeTestPasses;
        }
        public String toString() { return name + "@" + version; }
    }

    static boolean runSmokeTests(Environment env) {
        System.out.println("Running smoke tests against idle environment " + env + " (no user traffic reaches it yet)...");
        return env.smokeTestPasses;
    }

    public static void main(String[] args) {
        Environment blue = new Environment("blue", "v1", true);
        Environment active = blue;

        Environment green = new Environment("green", "v2", true); // this build passes its smoke tests
        System.out.println("Deployed " + green + " into the idle environment.");

        if (runSmokeTests(green)) {
            active = green;
            System.out.println("Smoke tests PASSED -- flipping router to " + active);
        } else {
            System.out.println("Smoke tests FAILED -- router stays at " + active + ", green is torn down or fixed and retried");
        }

        System.out.println("Router points at: " + active);
    }
}
```

How to run: `java BlueGreenWithSmokeTest.java`

`runSmokeTests` runs entirely against `green` while `active` still points at `blue` — exactly the "verify in isolation before it's live" property that makes blue-green safer than deploying straight into production. The flip (`active = green`) only happens inside the `if` branch, guarded by the smoke test result; a failing build never becomes active at all.

### Level 3 — Advanced

```java
// File: BlueGreenWithInstantRollback.java -- the SAME smoke-tested switch,
// now handling a PRODUCTION-FLAVORED hard case: green PASSES its smoke
// tests (which only exercise a few known paths) but starts throwing real
// errors once it's under actual production traffic -- a class of bug smoke
// tests structurally can't catch. Because blue was never torn down, the
// router can flip back INSTANTLY, with no redeploy needed.
import java.util.*;

public class BlueGreenWithInstantRollback {
    static class Environment {
        final String name;
        final String version;
        Environment(String name, String version) { this.name = name; this.version = version; }
        public String toString() { return name + "@" + version; }
    }

    static final double ERROR_RATE_ROLLBACK_THRESHOLD = 0.05; // 5%

    public static void main(String[] args) {
        Environment blue = new Environment("blue", "v1"); // stays fully intact, still running, just idle
        Environment green = new Environment("green", "v2");
        Environment active = blue;

        System.out.println("Smoke tests passed for " + green + " -- flipping router to green");
        active = green;
        System.out.println("Router points at: " + active + " (blue@v1 kept running, idle, as an instant fallback)");

        // Live traffic error rate observed AFTER the flip, tick by tick.
        double[] observedErrorRates = { 0.01, 0.02, 0.09, 0.15 };

        for (int tick = 0; tick < observedErrorRates.length; tick++) {
            double errorRate = observedErrorRates[tick];
            System.out.println("tick " + tick + ": error rate on " + active + " = " + (errorRate * 100) + "%");

            if (errorRate > ERROR_RATE_ROLLBACK_THRESHOLD) {
                System.out.println("  error rate exceeds " + (ERROR_RATE_ROLLBACK_THRESHOLD * 100)
                        + "% threshold -- INSTANT ROLLBACK: flipping router back to " + blue);
                active = blue;
                System.out.println("Router points at: " + active + " (no redeploy needed -- blue never stopped running)");
                break;
            }
        }

        System.out.println("Final state: router -> " + active);
    }
}
```

How to run: `java BlueGreenWithInstantRollback.java`

`blue` is never reassigned or discarded after the flip to `green` — it remains a fully valid, ready-to-route `Environment` reference the entire time. The tick loop simulates real production error rates arriving *after* the switch, which smoke tests (run before any real traffic existed) could never have observed. The moment `errorRate` crosses `ERROR_RATE_ROLLBACK_THRESHOLD`, `active = blue` executes — a single assignment, not a redeploy — immediately restoring service to the last known-good version.

## 6. Walkthrough

Trace `BlueGreenWithInstantRollback.main` in order. **First**, `blue` (`v1`) and `green` (`v2`) are both constructed, and `active` is set to `green` directly (representing that smoke tests, run separately, already passed) — the print confirms the router now points at `green@v2` while noting `blue@v1` is still running, just idle.

**Next**, the tick loop begins processing `observedErrorRates`. Tick 0 (`0.01`, i.e. 1%) and tick 1 (`0.02`, 2%) are both below `ERROR_RATE_ROLLBACK_THRESHOLD` (`0.05`, 5%), so the `if` condition is `false` each time — the loop just prints the observed rate and continues, `active` still pointing at `green`.

**Then**, tick 2 reads `0.09` (9%), which is greater than the `0.05` threshold. The `if` branch executes: it prints the rollback message referencing `blue`, then executes `active = blue`, then prints the confirmation that the router now points at `blue@v1` with no redeploy required. The `break` statement exits the loop immediately — tick 3's `0.15` (15%) is never even evaluated, because the rollback has already happened.

**Finally**, the last print confirms the ending state: `active` is `blue@v1`, exactly where it needs to be to keep serving traffic correctly while the `green` build is investigated and fixed offline.

```
Smoke tests passed for green@v2 -- flipping router to green
Router points at: green@v2 (blue@v1 kept running, idle, as an instant fallback)
tick 0: error rate on green@v2 = 1.0%
tick 1: error rate on green@v2 = 2.0%
tick 2: error rate on green@v2 = 9.0%
  error rate exceeds 5.0% threshold -- INSTANT ROLLBACK: flipping router back to blue@v1
Router points at: blue@v1 (no redeploy needed -- blue never stopped running)
Final state: router -> blue@v1
```

## 7. Gotchas & takeaways

> Smoke tests only exercise the paths someone thought to write tests for — they cannot catch a defect that only surfaces under real production traffic patterns, real data shapes, or real concurrent load. Blue-green's real safety net isn't the smoke test gate; it's that the previous environment is kept alive and instantly reachable, so a defect smoke tests missed still gets caught quickly and rolled back cheaply.

- Don't tear down the previously active environment immediately after a successful flip — keep it warm for a defined rollback window, since that's the entire source of blue-green's fast-rollback advantage.
- Running two full environments simultaneously roughly doubles infrastructure cost during the deploy window — a real trade-off against the cheaper, single-pool approach of [rolling deployment](0450-rolling-deployment.md).
- Stateful resources (databases, in-flight sessions, message queue consumers) usually can't cleanly exist in two places at once — blue-green works most cleanly for stateless services, per [twelve-factor app principles](0442-twelve-factor-app-principles.md), with shared stateful dependencies handled separately.
- Unlike a rolling deployment, blue-green's switch is atomic — there's no window where old and new versions serve real traffic simultaneously, which simplifies reasoning about compatibility but means you get zero real-traffic signal about the new version until the full switch has already happened.
- For a strategy that gets *some* real-traffic signal before committing 100% of users, see [canary release](0452-canary-release.md), which ramps up traffic to the new version gradually instead of flipping all at once.
