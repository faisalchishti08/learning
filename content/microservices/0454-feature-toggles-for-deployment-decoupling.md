---
card: microservices
gi: 454
slug: feature-toggles-for-deployment-decoupling
title: "Feature toggles for deployment decoupling"
---

## 1. What it is

A **feature toggle** (or feature flag) is a runtime-checked switch that decides which code path executes, allowing new code to be **deployed** — present and running in production — without being **released** — actually visible or active for users. This decouples the two actions that are normally bundled together: shipping code to production servers, and exposing its behavior to real traffic. A toggle can be flipped instantly, without a new deployment, which makes it fundamentally different from the deployment-time strategies covered in [rolling deployment](0450-rolling-deployment.md), [blue-green deployment](0451-blue-green-deployment.md), and [canary release](0452-canary-release.md).

## 2. Why & when

You reach for feature toggles the moment you want to control *exposure* to a feature independently of *when its code physically reaches production*:

- **Deployment and release are two different risks, and bundling them makes both harder to reason about.** A deploy risks "does this code run correctly at all" (crashes, startup failures); a release risks "does this behavior make sense for users right now" (business logic, timing, readiness). Toggles let you deploy early and often — reducing the risk and size of each individual deploy — while releasing on a completely separate, business-driven schedule.
- **A toggle can be flipped in seconds, with no build, no redeploy, and no restart** — which makes it the fastest possible incident response tool: if a feature is causing problems, turning it off is immediate, unlike rolling back a deployment, which takes as long as redeploying the previous version.
- **Long-lived feature branches cause painful merges.** Toggles let a team merge incomplete or in-progress features into the main branch continuously, hidden behind a flag that's off by default, avoiding the drift and conflict cost of a branch that diverges from `main` for weeks.
- **You use toggles for anything you want to control the timing or audience of independently from the deploy pipeline** — a coordinated multi-team launch, a feature gated to internal users first, a risky change you want an instant kill switch for regardless of how the rollout is otherwise going.

## 3. Core concept

Think of a toggle as a light switch already wired into the wall, versus the light fixture itself. Installing the wiring and the switch (deploying the code) is a separate, lower-risk activity from actually turning the light on (releasing the feature) — an electrician can run the wiring days or weeks before anyone flips the switch, and if something's wrong once it is flipped, turning it back off is instant, with no need to re-run any wiring.

Concretely, the mechanics are:

1. **A flag store holds the current state of each toggle** — simplest is a flat on/off, but real systems typically support percentage rollouts and audience targeting (see below).
2. **Application code checks the flag at the decision point**, branching between old and new behavior — the check itself should be cheap and fast, since it may run on every relevant request.
3. **Percentage and segment-based rollouts** let a toggle be enabled for a *consistent* subset of traffic — commonly by hashing a stable identifier like user ID, so the same user always gets the same behavior across requests, rather than flipping randomly call to call.
4. **A kill switch is the toggle's most important operational property.** However a feature is currently being rolled out, an operator (or an automated alert) must be able to force it to a hard OFF state immediately, overriding any percentage or segment logic, the moment it's causing real harm.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Deploying code and releasing a feature are decoupled: code ships to production dormant behind a flag, and the flag is flipped independently, with a kill switch able to override any rollout state instantly">
  <rect x="20" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="110" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Deploy (code ships)</text>

  <rect x="230" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Flag: OFF (dormant)</text>

  <rect x="440" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="530" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Flag flipped: released</text>

  <line x1="200" y1="55" x2="230" y2="55" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="410" y1="55" x2="440" y2="55" stroke="#6db33f" marker-end="url(#a1)"/>
  <text x="320" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no redeploy between these two states</text>

  <rect x="230" y="130" width="180" height="50" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="320" y="155" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Kill switch: hard OFF</text>
  <text x="320" y="170" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">overrides any rollout %</text>
  <line x1="530" y1="80" x2="320" y2="130" stroke="#f85149" stroke-dasharray="3,2" marker-end="url(#a2)"/>
  <text x="470" y="105" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">instant, mid-incident</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f85149"/></marker>
  </defs>
</svg>

Deploying and releasing are separate steps connected only by a flag flip; a kill switch can force the flag back off instantly from any state, without touching the deployed code at all.

## 5. Runnable example

Scenario: an `order-service` checkout flow guarded by a `new-checkout-flow` toggle. We start with a plain on/off flag decoupling deploy from release, add a sticky percentage rollout so a consistent subset of users see the new behavior, then handle the hard case: the new flow starts throwing errors mid-rollout, requiring an instant kill switch that overrides the rollout for every user immediately, with no redeploy.

### Level 1 — Basic

```java
// File: FeatureToggleBasic.java -- models the CORE idea: DEPLOY the code
// for both the old and new behavior in the SAME artifact, and use a simple
// on/off flag -- checked at runtime -- to decide which path executes.
// Deploying and RELEASING become two separate actions.
import java.util.*;

public class FeatureToggleBasic {
    static class FeatureFlags {
        final Map<String, Boolean> flags = new HashMap<>();
        boolean isEnabled(String name) { return flags.getOrDefault(name, false); }
        void set(String name, boolean value) { flags.put(name, value); }
    }

    static String checkout(FeatureFlags flags, String orderId) {
        if (flags.isEnabled("new-checkout-flow")) {
            return "checkout(" + orderId + ") -- NEW flow";
        }
        return "checkout(" + orderId + ") -- OLD flow";
    }

    public static void main(String[] args) {
        FeatureFlags flags = new FeatureFlags();

        System.out.println("Deployed with new-checkout-flow OFF (code is live, but path is dormant):");
        System.out.println("  " + checkout(flags, "order-1"));

        flags.set("new-checkout-flow", true); // toggled ON without a redeploy
        System.out.println("Flag flipped ON at runtime, no redeploy:");
        System.out.println("  " + checkout(flags, "order-2"));
    }
}
```

How to run: `java FeatureToggleBasic.java`

Both the old and new `checkout` behavior are compiled into the same running program from the start — nothing is redeployed between the two calls. Only `flags.set("new-checkout-flow", true)` changes, and that alone is enough to switch which branch executes, demonstrating deploy (the code existing, dormant) and release (the flag turning it on) as two genuinely separate moments.

### Level 2 — Intermediate

```java
// File: FeatureToggleWithPercentageRollout.java -- the SAME toggle idea,
// now supporting a PERCENTAGE rollout: instead of a flat on/off, the flag
// is enabled for a consistent (sticky) subset of users, identified by
// hashing their user ID, so the SAME user always sees the SAME behavior.
import java.util.*;

public class FeatureToggleWithPercentageRollout {
    static class FeatureFlags {
        final Map<String, Integer> rolloutPercent = new HashMap<>();
        void setRolloutPercent(String name, int percent) { rolloutPercent.put(name, percent); }

        boolean isEnabledFor(String name, String userId) {
            int percent = rolloutPercent.getOrDefault(name, 0);
            int bucket = Math.floorMod(userId.hashCode(), 100); // sticky per user
            return bucket < percent;
        }
    }

    static String checkout(FeatureFlags flags, String userId, String orderId) {
        boolean useNewFlow = flags.isEnabledFor("new-checkout-flow", userId);
        return "checkout(" + orderId + ") for " + userId + " -- " + (useNewFlow ? "NEW" : "OLD") + " flow";
    }

    public static void main(String[] args) {
        FeatureFlags flags = new FeatureFlags();
        flags.setRolloutPercent("new-checkout-flow", 30);

        String[] users = { "user-alice", "user-bob", "user-carol", "user-dave", "user-erin" };
        for (String user : users) {
            System.out.println(checkout(flags, user, "order-for-" + user));
        }

        System.out.println("Calling again for the SAME users -- results are STICKY, not randomized per call:");
        for (String user : users) {
            System.out.println(checkout(flags, user, "order2-for-" + user));
        }
    }
}
```

How to run: `java FeatureToggleWithPercentageRollout.java`

`isEnabledFor` hashes `userId` into a stable `0-99` bucket and compares it against the configured `rolloutPercent` — the same user always lands in the same bucket, so their experience is consistent across requests, unlike a coin-flip-per-request approach that would flicker a user between old and new behavior. Running the same five users twice confirms this: each user gets identical results both times.

### Level 3 — Advanced

```java
// File: FeatureToggleKillSwitchAdvanced.java -- the SAME percentage-rollout
// toggle, now handling a PRODUCTION-FLAVORED hard case: the new checkout
// flow starts throwing errors mid-incident. An operator flips the flag to
// a hard OFF kill switch, and EVERY subsequent request -- even requests
// from users who were previously bucketed into the new flow -- must
// immediately fall back to the old flow, with no redeploy and no restart.
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class FeatureToggleKillSwitchAdvanced {
    static class FeatureFlags {
        final Map<String, Integer> rolloutPercent = new HashMap<>();
        final AtomicBoolean killSwitch = new AtomicBoolean(false); // hard override, checked FIRST

        void setRolloutPercent(String name, int percent) { rolloutPercent.put(name, percent); }
        void activateKillSwitch() { killSwitch.set(true); }

        boolean isEnabledFor(String name, String userId) {
            if (killSwitch.get()) return false; // kill switch always wins, regardless of rollout bucket
            int percent = rolloutPercent.getOrDefault(name, 0);
            int bucket = Math.floorMod(userId.hashCode(), 100);
            return bucket < percent;
        }
    }

    static String checkout(FeatureFlags flags, String userId) {
        boolean useNewFlow = flags.isEnabledFor("new-checkout-flow", userId);
        if (useNewFlow) {
            // The new flow has a latent bug that throws under certain conditions.
            if (userId.equals("user-alice")) throw new RuntimeException("new-checkout-flow NPE for " + userId);
            return userId + " -- NEW flow OK";
        }
        return userId + " -- OLD flow OK";
    }

    public static void main(String[] args) {
        FeatureFlags flags = new FeatureFlags();
        flags.setRolloutPercent("new-checkout-flow", 30); // user-alice's bucket falls under 30%

        String[] users = { "user-alice", "user-bob", "user-alice", "user-alice" };
        int errors = 0;

        for (int i = 0; i < users.length; i++) {
            String user = users[i];
            try {
                String result = checkout(flags, user);
                System.out.println("request " + i + " (" + user + "): " + result);
            } catch (RuntimeException e) {
                errors++;
                System.out.println("request " + i + " (" + user + "): ERROR -- " + e.getMessage());
                if (errors >= 2 && !flags.killSwitch.get()) {
                    System.out.println("  " + errors + " errors observed -- ACTIVATING KILL SWITCH, no redeploy, no restart");
                    flags.activateKillSwitch();
                }
            }
        }

        System.out.println("Retrying user-alice one more time after the kill switch:");
        System.out.println("  " + checkout(flags, "user-alice"));
    }
}
```

How to run: `java FeatureToggleKillSwitchAdvanced.java`

`isEnabledFor` checks `killSwitch.get()` *before* consulting the rollout percentage at all — the kill switch is structurally a higher-priority override, not just another condition mixed in with the rollout logic. `user-alice` happens to fall inside the 30% rollout bucket and hits a real bug in the new flow; after two observed errors, `activateKillSwitch()` flips `killSwitch` to `true`, and every subsequent call to `isEnabledFor` — for any user, not just `user-alice` — short-circuits to `false` immediately.

## 6. Walkthrough

Trace `FeatureToggleKillSwitchAdvanced.main` in order. **First**, `flags.setRolloutPercent("new-checkout-flow", 30)` configures the rollout, and `user-alice`'s hashed bucket falls below `30`, so `isEnabledFor` returns `true` for her from the start; `killSwitch` is `false`.

**Next**, request 0 calls `checkout(flags, "user-alice")`. `useNewFlow` evaluates to `true`, so the method enters the new-flow branch, checks `userId.equals("user-alice")`, and throws `RuntimeException`. The `catch` block increments `errors` to `1` and prints the error; since `errors` is only `1`, the kill-switch condition (`errors >= 2`) isn't met yet.

**Then**, request 1 calls `checkout(flags, "user-bob")`. `user-bob`'s bucket doesn't fall under `30`, so `useNewFlow` is `false` and the old flow runs successfully — no error, `errors` stays at `1`.

**After that**, request 2 calls `checkout(flags, "user-alice")` again. `killSwitch` is still `false`, so the rollout logic runs again, `useNewFlow` is `true` again, and the same bug throws again. `errors` increments to `2`, and this time `errors >= 2 && !flags.killSwitch.get()` is `true` — the kill switch activates immediately, setting `killSwitch` to `true`.

**Finally**, request 3 calls `checkout(flags, "user-alice")` one more time, but now `isEnabledFor` checks `killSwitch.get()` first, finds it `true`, and returns `false` immediately without even consulting the rollout bucket — `user-alice`, despite being solidly inside the 30% rollout, now gets the old flow, and the retry after the loop confirms the same: the kill switch's effect is immediate and total, not scoped to any particular user or bucket.

```
request 0 (user-alice): ERROR -- new-checkout-flow NPE for user-alice
request 1 (user-bob): user-bob -- OLD flow OK
request 2 (user-alice): ERROR -- new-checkout-flow NPE for user-alice
  2 errors observed -- ACTIVATING KILL SWITCH, no redeploy, no restart
request 3 (user-alice): user-alice -- OLD flow OK
Retrying user-alice one more time after the kill switch:
  user-alice -- OLD flow OK
```

## 7. Gotchas & takeaways

> Feature flags that accumulate forever become their own form of technical debt: every additional flag doubles the number of code paths that theoretically need testing (old and new, for each toggle, combined with every other toggle's state). Remove a flag once its feature is fully released and stable — leaving stale, always-on flags in the code indefinitely is a common and costly anti-pattern.

- Deploy and release are genuinely separate concerns: a toggle lets you ship code early (reducing the size and risk of each deploy) and control exposure on a completely independent timeline driven by business readiness, not build readiness.
- Always give risky features a kill switch that's checked before any percentage or segment logic — as Level 3 shows, the override must win unconditionally, not just be "one more condition" mixed into the rollout calculation.
- Use a stable hash of a consistent identifier (user ID, account ID) for percentage rollouts, not a per-request random choice — flickering behavior for the same user between requests is confusing and makes bugs much harder to reproduce.
- A feature toggle and a [canary release](0452-canary-release.md) solve related but distinct problems: canary ramps traffic to a newly *deployed instance*, while a toggle ramps exposure to a *code path* already deployed everywhere — toggles can flip back instantly with zero infrastructure change, which canary rollback cannot fully match.
- Toggle checks run on a hot path in many systems — keep the flag store lookup fast (in-memory, cached) rather than a network call per check, or the toggle mechanism itself becomes a latency and reliability risk.
