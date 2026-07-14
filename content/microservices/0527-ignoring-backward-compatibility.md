---
card: microservices
gi: 527
slug: ignoring-backward-compatibility
title: "Ignoring backward compatibility"
---

## 1. What it is

**Ignoring backward compatibility** is the anti-pattern of changing a service's API in a way that breaks existing callers, without any transition period, versioning, or coordination — renaming a field, changing a type, removing an endpoint, or altering behavior that callers depend on, and simply deploying the change. In a monolith, a breaking internal change and its callers can be updated together, atomically, in one deploy. In microservices, callers are separate deployables, often owned by separate teams, that cannot be guaranteed to update in lockstep — so a breaking change deployed unilaterally breaks whichever callers haven't (and often can't, on short notice) update yet.

## 2. Why & when

You protect backward compatibility deliberately because independent deployability — one of the central promises of microservices — is meaningless without it:

- **Independent deployability requires that a service can change without requiring its callers to change at the same instant.** If every change to Service A's API requires every caller of A to deploy a corresponding update simultaneously, A and its callers are coupled at deploy time regardless of how many separate repositories or pipelines exist between them — exactly the [distributed monolith](0519-distributed-monolith.md) symptom.
- **Callers are often owned by different teams, on different schedules, sometimes even different companies (for a public API).** There is frequently no realistic way to coordinate "everyone deploy the compatible version at exactly the same moment" — and even when it's theoretically possible, requiring it recreates the very coordination overhead microservices are meant to avoid.
- **A breaking change without a transition period fails immediately and completely** for any caller still using the old contract — not a graceful degradation, an outright error, often in production, often for calls that were working perfectly fine moments before the deploy.
- **The fix is to make changes additive and versioned, with an explicit deprecation and sunset process** — adding a new field or new endpoint version alongside the old one, giving callers a real window to migrate, and only removing the old contract once monitoring confirms nothing is still using it (or after a clearly communicated sunset date has passed).

## 3. Core concept

Think of a public train station changing its platform numbering scheme overnight, with no announcement, no transition period, and no signage explaining the change — every passenger who memorized "my train leaves from platform 4" the day before now stands on the wrong platform, with no warning until their train doesn't show up where expected. A well-run transition instead keeps the old platform numbers working (perhaps with a temporary sign pointing travelers to the new number) for a clearly announced period, giving every passenger — who cannot all be individually notified or forced to relearn the scheme at the same instant — a real chance to adapt before the old numbers stop working entirely.

Concretely:

1. **Additive changes are safe by default**: adding a new optional field to a response, adding a new endpoint, adding a new accepted value — existing callers that don't know about the addition are entirely unaffected, since they simply ignore what they don't recognize.
2. **Removing or renaming an existing field, changing a field's type or meaning, or changing an endpoint's URL are breaking changes** — any caller depending on the old shape fails the moment the change deploys, with no transition at all.
3. **A safe breaking change requires versioning plus a deprecation period**: introduce the new version (a new endpoint path, a new media type, a new API version header) alongside the old one, mark the old one deprecated with a documented and monitored sunset date, and only remove the old version once traffic to it has genuinely dropped to zero, or the sunset date has passed with adequate notice.
4. **Monitoring which callers are still using a deprecated contract is what makes the sunset decision safe** — removing a deprecated version "because it's been a while" without checking actual usage risks breaking a caller nobody remembered still depended on it.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A breaking change deployed with no transition fails every existing caller instantly; a versioned, deprecated rollout gives callers a real window to migrate before the old contract is removed">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">No transition</text>
  <rect x="20" y="35" width="260" height="26" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">day 1: v1 API, all callers happy</text>
  <rect x="20" y="70" width="260" height="26" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="150" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">day 2: v1 REMOVED, no warning</text>
  <text x="150" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">every caller still on v1 fails instantly, no window to react</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Versioned + deprecated</text>
  <rect x="380" y="35" width="260" height="26" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">day 1: v2 added, v1 still works</text>
  <rect x="380" y="70" width="260" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">day 2-60: v1 deprecated, monitored</text>
  <rect x="380" y="105" width="260" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="123" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">day 61: v1 removed, usage confirmed zero</text>
</svg>

Adding the new version alongside the old, monitoring usage, and only removing once usage drops to zero turns a breaking change into a safe migration.

## 5. Runnable example

Scenario: an API that returns a customer's full name as a single field, needing to split it into first/last name. We start with an immediate breaking change, extend it to a versioned rollout that keeps both shapes available, then handle the hard case: tracking real usage of the deprecated version to decide when it's actually safe to remove.

### Level 1 — Basic

```java
// File: BreakingChangeNoTransition.java -- v2 REPLACES v1's response
// shape immediately, with no transition -- any caller still expecting
// "fullName" breaks the instant this deploys.
import java.util.*;

public class BreakingChangeNoTransition {
    // BEFORE: what every existing caller currently depends on
    static Map<String, Object> getCustomerV1() {
        return Map.of("fullName", "Alice Smith");
    }

    // AFTER: deployed as a straight replacement -- "fullName" is just GONE
    static Map<String, Object> getCustomerAfterChange() {
        return Map.of("firstName", "Alice", "lastName", "Smith");
    }

    static void existingCallerCode(Map<String, Object> response) {
        String fullName = (String) response.get("fullName"); // existing caller code, unchanged
        System.out.println("Welcome, " + fullName);
    }

    public static void main(String[] args) {
        existingCallerCode(getCustomerV1()); // works today
        existingCallerCode(getCustomerAfterChange()); // BREAKS the instant the API changes -- fullName is null
    }
}
```

How to run: `java BreakingChangeNoTransition.java`

The second call prints `"Welcome, null"` — `existingCallerCode` still looks for `"fullName"`, which simply no longer exists in the new response shape. This code represents every caller that hasn't updated yet; the API's team deployed the change and moved on, with no way for those callers to have seen it coming or any window to react before it took effect.

### Level 2 — Intermediate

```java
// File: VersionedRollout.java -- v2 is ADDED alongside v1; v1 keeps
// working UNCHANGED, giving existing callers a real window to migrate
// to v2 on their own schedule instead of breaking on this deploy.
import java.util.*;

public class VersionedRollout {
    static Map<String, Object> getCustomerV1() {
        // v1 stays fully functional -- existing callers are completely unaffected by v2 existing
        return Map.of("fullName", "Alice Smith");
    }
    static Map<String, Object> getCustomerV2() {
        // v2 is the new, additive shape -- available for callers ready to migrate
        return Map.of("firstName", "Alice", "lastName", "Smith");
    }

    static void legacyCallerCode(Map<String, Object> response) {
        System.out.println("Welcome, " + response.get("fullName"));
    }
    static void migratedCallerCode(Map<String, Object> response) {
        System.out.println("Welcome, " + response.get("firstName") + " " + response.get("lastName"));
    }

    public static void main(String[] args) {
        legacyCallerCode(getCustomerV1());       // still works, unaffected by v2's existence
        migratedCallerCode(getCustomerV2());     // new callers can use the improved shape immediately
        System.out.println("Both versions coexist -- no caller is forced to change on this deploy.");
    }
}
```

How to run: `java VersionedRollout.java`

`getCustomerV1` is left completely untouched, so `legacyCallerCode` (representing every caller that hasn't migrated) keeps working exactly as before. `getCustomerV2` is a genuinely new, additive endpoint/shape that new or migrating callers can adopt on their own timeline. Nobody is broken by this deploy — the breaking change from Level 1 has been converted into a purely additive one, with the actual cutover deferred to a later, deliberate step.

### Level 3 — Advanced

```java
// File: MonitoredDeprecationSunset.java -- v1 is marked DEPRECATED and
// its usage is TRACKED, so the decision to actually remove it is based
// on real evidence that no caller still depends on it -- not a guess.
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class MonitoredDeprecationSunset {
    static AtomicInteger v1CallCount = new AtomicInteger(0);
    static final String V1_SUNSET_DATE = "2026-09-01";

    static Map<String, Object> getCustomerV1() {
        v1CallCount.incrementAndGet(); // every v1 call is counted -- this is the evidence the sunset decision relies on
        System.out.println("[WARN] deprecated v1 endpoint called -- sunset date: " + V1_SUNSET_DATE + " (call #" + v1CallCount.get() + ")");
        return Map.of("fullName", "Alice Smith");
    }
    static Map<String, Object> getCustomerV2() {
        return Map.of("firstName", "Alice", "lastName", "Smith");
    }

    static boolean isSafeToRemoveV1() {
        // in a real system this would check monitoring over a full recent window (e.g. the last 30 days), not just this process's counter
        return v1CallCount.get() == 0;
    }

    public static void main(String[] args) {
        getCustomerV1(); // some caller still hasn't migrated -- this call is now visible and counted
        getCustomerV2();
        System.out.println("Safe to remove v1 now? " + isSafeToRemoveV1() + " (v1 was called " + v1CallCount.get() + " time(s) -- NOT safe yet)");
        System.out.println("Decision: keep v1 alive past " + V1_SUNSET_DATE + " if traffic isn't actually zero, and follow up with whoever's still calling it.");
    }
}
```

How to run: `java MonitoredDeprecationSunset.java`

Every call to the deprecated `getCustomerV1` logs a visible warning and increments `v1CallCount` — in a real system this would emit a metric tagged by caller identity, so the owning team can see exactly which caller is still on the old version and reach out directly. `isSafeToRemoveV1` makes the sunset decision based on that real evidence (`v1CallCount.get() == 0`) rather than simply trusting that "the sunset date passed, so it should be fine to remove now" — here, it correctly reports the deprecated version is still in active use and should not yet be removed, regardless of what the calendar says.

## 6. Walkthrough

Trace `MonitoredDeprecationSunset.main` end to end:

1. **`getCustomerV1()` is called.** Before returning anything, it increments `v1CallCount` from 0 to 1 and prints a warning log line including the sunset date — this line is the observable signal that, in production, would be captured by monitoring/metrics rather than a console log, tagged with information about which caller made the request.
2. **`getCustomerV1()` returns the same `fullName`-shaped response it always has** — nothing about the deprecated version's actual behavior changes; deprecation is a signal about the future, not an immediate behavior change.
3. **`getCustomerV2()` is called separately**, returning the new `firstName`/`lastName` shape, with no interaction with the deprecation tracking at all — this represents a caller that has already migrated.
4. **`isSafeToRemoveV1()` is called**, checking whether `v1CallCount.get() == 0`. Since step 1 already incremented it to 1, this returns `false`.
5. **`main` prints the sunset decision**, explicitly reporting that v1 was called at least once and is therefore not yet safe to remove, regardless of the sunset date `2026-09-01` — the decision is driven by actual observed usage, not by the calendar alone.

In a real rollout, this same shape scales up: `v1CallCount` becomes a dashboard tracking requests-per-day to the deprecated endpoint, broken down by caller (via an API key, client ID, or user-agent), sustained monitoring over weeks confirms the trend is genuinely dropping toward zero (not just quiet for one hour), and the owning team proactively contacts whichever caller is still showing up in that dashboard well before the sunset date, rather than discovering the breakage only after removing the old version and waiting for a support ticket.

## 7. Gotchas & takeaways

> **Gotcha:** setting and publishing a sunset date is necessary but not sufficient — a date on a document doesn't stop a caller from actually calling the deprecated endpoint on day one past the deadline; the removal decision still needs to be backed by monitored evidence that usage has actually dropped to zero (or been proactively migrated), not just by the calendar having advanced past the announced date.

- Independent deployability requires backward-compatible changes by default — additive changes (new optional fields, new endpoints) are safe; renaming, removing, or changing the type/meaning of an existing field is a breaking change that needs a transition plan.
- Roll out breaking changes as new, versioned additions alongside the old contract, not as in-place replacements — this converts a breaking change into a purely additive one from every existing caller's point of view.
- Track real usage of a deprecated version before removing it — a documented sunset date without monitored usage data is a guess, not evidence, about whether removal is actually safe.
- Backward compatibility discipline is what makes independent deployability real; without it, "separately deployable services" still require the same cross-team, same-instant coordination a monolith would, just with extra network hops and less visibility into who's affected.
