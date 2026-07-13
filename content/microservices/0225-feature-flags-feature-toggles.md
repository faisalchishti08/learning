---
card: microservices
gi: 225
slug: feature-flags-feature-toggles
title: "Feature flags / feature toggles"
---

## 1. What it is

A feature flag (also called a feature toggle) is a piece of configuration that controls whether a feature — or a code path — is active at runtime, letting a feature be turned on or off (or targeted to specific users) without deploying new code, by branching on the flag's current value rather than on which code was deployed.

## 2. Why & when

Without feature flags, shipping a new feature and enabling it are the same event — deploying the code that implements a feature makes it immediately live for everyone, and disabling it again means deploying a revert. This coupling is a real constraint: a feature that needs gradual rollout, A/B testing, or an instant kill switch if something goes wrong in production has no way to achieve any of that without another deployment cycle. Feature flags decouple deployment from release: the code implementing a feature can be deployed dark (present but flagged off), then enabled for a subset of traffic, then fully rolled out, or instantly disabled — all through a configuration change, not a code change, making it a natural fit for [dynamic runtime configuration refresh](0223-dynamic-runtime-configuration-refresh.md).

Use feature flags for anything that benefits from being enabled, disabled, or targeted independently of deployment timing — risky new features, gradual rollouts, emergency kill switches, A/B tests. Avoid using flags as a permanent branching mechanism for logic that should really just be two separate, deliberate code paths maintained long-term — flags that never get removed after a feature fully ships accumulate as clutter and complexity.

## 3. Core concept

A feature flag is checked at the point where behavior diverges, and the check reads the flag's *current* value on each evaluation (not a value captured once), so a flag change takes effect for the very next check without requiring a restart, exactly as with [dynamic configuration refresh](0223-dynamic-runtime-configuration-refresh.md) generally.

```java
interface FeatureFlagService { boolean isEnabled(String flagName, String userId); }

// application code branches on the FLAG, not on which code was deployed
if (featureFlagService.isEnabled("new-checkout-flow", userId)) {
    return newCheckoutFlow(order); // the NEW code path, deployed but only active when flagged on
} else {
    return legacyCheckoutFlow(order); // the OLD, still-live path
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request checks a feature flag service to decide which of two already-deployed code paths to take -- the new flagged feature or the existing legacy path -- with the choice controlled entirely by the flag's current configuration, not by which code is deployed" >
  <rect x="20" y="65" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Request</text>

  <rect x="215" y="55" width="160" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Feature flag check</text>
  <text x="295" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">reads CURRENT value</text>

  <rect x="460" y="20" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">New flow (if ON)</text>

  <rect x="460" y="110" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Legacy flow (if OFF)</text>

  <line x1="140" y1="85" x2="213" y2="85" stroke="#8b949e" marker-end="url(#arr225)"/>
  <line x1="375" y1="72" x2="458" y2="45" stroke="#8b949e" marker-end="url(#arr225)"/>
  <line x1="375" y1="98" x2="458" y2="125" stroke="#8b949e" marker-end="url(#arr225)"/>

  <defs>
    <marker id="arr225" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Both code paths are already deployed; the flag alone decides which one a given request actually takes.

## 5. Runnable example

Scenario: a checkout feature that starts with two hard-coded, mutually exclusive versions selectable only by editing code, refactors to select between them via a runtime-checked feature flag (both paths deployed together, toggled by configuration), and finally adds percentage-based gradual rollout targeting only a fraction of users — demonstrating flags enabling a controlled, incremental release rather than an all-or-nothing switch.

### Level 1 — Basic

```java
// File: HardCodedFeatureChoice.java -- switching between the old and new
// checkout flow means EDITING this constant and REDEPLOYING.
public class HardCodedFeatureChoice {
    static final boolean USE_NEW_CHECKOUT = false; // hard-coded -- changing this needs a new deploy

    static String legacyCheckoutFlow() { return "legacy checkout"; }
    static String newCheckoutFlow() { return "new checkout"; }

    public static void main(String[] args) {
        String result = USE_NEW_CHECKOUT ? newCheckoutFlow() : legacyCheckoutFlow();
        System.out.println("Checkout result: " + result);
        System.out.println("Switching flows requires editing USE_NEW_CHECKOUT and redeploying.");
    }
}
```

**How to run:** `javac HardCodedFeatureChoice.java && java HardCodedFeatureChoice` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RuntimeFeatureFlag.java -- BOTH flows are deployed together; a
// runtime-checked flag decides which one runs, with NO redeploy needed
// to flip between them.
import java.util.*;

public class RuntimeFeatureFlag {
    static class FeatureFlagService {
        Map<String, Boolean> flags = new HashMap<>(Map.of("new-checkout-flow", false));
        boolean isEnabled(String flagName) { return flags.getOrDefault(flagName, false); } // read LIVE, every call
        void setFlag(String flagName, boolean enabled) { flags.put(flagName, enabled); } // toggled at RUNTIME
    }

    static String legacyCheckoutFlow() { return "legacy checkout"; }
    static String newCheckoutFlow() { return "new checkout"; }

    static String handleCheckout(FeatureFlagService flags) {
        return flags.isEnabled("new-checkout-flow") ? newCheckoutFlow() : legacyCheckoutFlow();
    }

    public static void main(String[] args) {
        FeatureFlagService flags = new FeatureFlagService();
        System.out.println("Before flag flip: " + handleCheckout(flags));

        flags.setFlag("new-checkout-flow", true); // RUNTIME toggle -- no redeploy
        System.out.println("After flag flip: " + handleCheckout(flags));
    }
}
```

**How to run:** `javac RuntimeFeatureFlag.java && java RuntimeFeatureFlag` (JDK 17+).

Expected output:
```
Before flag flip: legacy checkout
After flag flip: new checkout
```

### Level 3 — Advanced

```java
// File: PercentageBasedGradualRollout.java -- the flag targets only a
// PERCENTAGE of users, using a deterministic hash so a given user
// consistently lands on the same side across repeated checks.
import java.util.*;

public class PercentageBasedGradualRollout {
    static class FeatureFlagService {
        Map<String, Integer> rolloutPercentage = new HashMap<>(Map.of("new-checkout-flow", 30)); // 30% rollout

        boolean isEnabled(String flagName, String userId) {
            int percentage = rolloutPercentage.getOrDefault(flagName, 0);
            int userBucket = Math.floorMod((flagName + userId).hashCode(), 100); // DETERMINISTIC per user
            return userBucket < percentage; // SAME user always lands in the SAME bucket
        }

        void setRolloutPercentage(String flagName, int percentage) { rolloutPercentage.put(flagName, percentage); }
    }

    static String handleCheckout(FeatureFlagService flags, String userId) {
        return flags.isEnabled("new-checkout-flow", userId) ? "new checkout" : "legacy checkout";
    }

    public static void main(String[] args) {
        FeatureFlagService flags = new FeatureFlagService();
        List<String> users = List.of("user-1", "user-2", "user-3", "user-4", "user-5", "user-6", "user-7", "user-8", "user-9", "user-10");

        System.out.println("=== at 30% rollout ===");
        long enabledAt30 = users.stream().filter(u -> flags.isEnabled("new-checkout-flow", u)).count();
        for (String u : users) System.out.println("  " + u + ": " + handleCheckout(flags, u));
        System.out.println("Users on new flow: " + enabledAt30 + "/10 (approximately 30%)");

        flags.setRolloutPercentage("new-checkout-flow", 100); // FULL rollout, no redeploy, no code change
        System.out.println("\n=== after raising rollout to 100% ===");
        long enabledAt100 = users.stream().filter(u -> flags.isEnabled("new-checkout-flow", u)).count();
        System.out.println("Users on new flow: " + enabledAt100 + "/10");
    }
}
```

**How to run:** `javac PercentageBasedGradualRollout.java && java PercentageBasedGradualRollout` (JDK 17+).

Expected output (exact per-user split may vary with hash values, but totals follow the pattern):
```
=== at 30% rollout ===
  user-1: legacy checkout
  user-2: new checkout
  ...
Users on new flow: 3/10 (approximately 30%)

=== after raising rollout to 100% ===
Users on new flow: 10/10
```

## 6. Walkthrough

1. **Level 1, the coupling problem** — `USE_NEW_CHECKOUT` is a compile-time constant; the ternary in `main` resolves to whichever branch that constant selects at compile time, meaning switching flows requires editing this line and rebuilding — deployment and release are the same event.
2. **Level 2, decoupling via a runtime flag** — `FeatureFlagService.isEnabled` reads `flags` fresh on every call rather than capturing a value once, and `handleCheckout` branches on that live read instead of a compiled constant; both `legacyCheckoutFlow` and `newCheckoutFlow` are present in the deployed program simultaneously.
3. **Level 2, toggling without redeploying** — `flags.setFlag("new-checkout-flow", true)` mutates the flag's live state, and the very next call to `handleCheckout` (with no restart, no rebuild) takes the new branch — this is the core decoupling feature flags provide.
4. **Level 3, moving beyond all-or-nothing** — `isEnabled` in `PercentageBasedGradualRollout` no longer returns a single boolean for everyone; it computes a deterministic `userBucket` (a stable hash-derived number between 0 and 99) per `(flagName, userId)` pair, and compares it against the currently configured `rolloutPercentage`.
5. **Level 3, why determinism matters** — because `userBucket` is derived from a hash of the user's own ID combined with the flag name, the *same* user always lands in the *same* bucket across repeated checks — meaning a given user consistently sees either the new or legacy flow throughout their session, rather than flickering between them on every request, which would be a confusing and inconsistent experience.
6. **Level 3, the rollout increasing over time** — the first block queries all ten simulated users at a 30% rollout, and roughly three of them (whichever fall in buckets 0–29) see the new flow; after `setRolloutPercentage("new-checkout-flow", 100)`, the *same* users are queried again, and now all ten see the new flow — the rollout percentage changed via a plain configuration update, with the code, the deployed artifact, and even the running process left completely untouched.

## 7. Gotchas & takeaways

> **Gotcha:** feature flags that outlive their purpose become clutter and a source of bugs — once a feature is fully rolled out and stable, the flag check and the old, now-dead code path it guards should be removed; an accumulation of long-forgotten flags makes the codebase harder to reason about and creates a combinatorial explosion of flag-state combinations that were never actually tested together.

- Feature flags decouple deploying code from releasing a feature, letting a feature be toggled, targeted, or rolled back through configuration rather than a new deployment.
- Because a flag's value is read live on each check, flag changes take effect immediately, without a restart — a direct application of [dynamic configuration refresh](0223-dynamic-runtime-configuration-refresh.md).
- Percentage-based, deterministic-per-user rollout enables gradual, controlled releases rather than an instant all-or-nothing switch, while keeping each individual user's experience consistent across requests.
- Flags are best used for genuinely temporary, release-oriented branching — risky rollouts, A/B tests, kill switches — not as a permanent structural pattern.
- A flag should be removed, along with the old code path it guarded, once a feature is fully and stably rolled out; flags left in place indefinitely accumulate as technical debt.
