---
card: microservices
gi: 498
slug: deprecation-sunset-policies
title: "Deprecation & sunset policies"
---

## 1. What it is

A **deprecation policy** is a service's explicit, communicated process for retiring an old API version or endpoint: marking it deprecated (still working, but flagged as scheduled for removal), giving consumers advance notice and a migration path, and only then actually removing it — the **sunset date** — after that notice period has passed. It turns "we might remove this someday" into a concrete, trackable commitment both provider and consumers can plan around.

## 2. Why & when

You need an explicit deprecation and sunset policy the moment you have more than one version of an API coexisting, because "old version stays forever" and "old version disappears without warning" are both bad outcomes:

- **Removing an old API version without warning breaks every consumer still using it, with no chance to react.** A sunset policy gives consumers a defined window to migrate, converting a surprise outage into a planned, manageable piece of work on their own schedule.
- **Never removing old versions accumulates unbounded maintenance burden.** Every additional live version is more surface area to test, secure, and reason about — a deprecation policy is what actually lets a provider eventually stop paying that cost, rather than supporting every version ever shipped, forever.
- **A deprecation without a communicated sunset date isn't really a deprecation — it's just a suggestion nobody feels pressure to act on.** Consumers reasonably deprioritize migrating away from something with no concrete deadline, so the "deprecated" version ends up living indefinitely anyway, defeating the purpose.
- **You establish this policy formally as soon as you ship a second version of any API** — retrofitting a sunset process onto a version that's already been "deprecated, someday" for two years with no real deadline is a much harder conversation than establishing the expectation from the start.

## 3. Core concept

Think of a building being scheduled for demolition: tenants aren't evicted the instant demolition is decided — they're given formal notice with a specific move-out date, enough advance warning to find a new place, and reminders as the date approaches. Only once that date actually arrives does demolition proceed. A deprecation policy is that same formal notice-and-deadline process applied to an API version instead of a building.

Concretely, the lifecycle:

1. **Deprecation announcement**: the provider marks a version or endpoint as deprecated — communicated via documentation, response headers (`Deprecation: true`, `Sunset: <date>`), release notes, or direct outreach to known consumers — while the deprecated version continues working normally.
2. **Migration guidance**: consumers are told specifically what to migrate to, ideally with concrete examples of the change needed, not just "this is deprecated" with no next step.
3. **Sunset date is fixed and communicated in advance**, giving consumers a defined, non-negotiable deadline to plan their migration around — this date should give a reasonable amount of lead time appropriate to how disruptive the migration actually is.
4. **Monitoring usage of the deprecated version** as the sunset date approaches lets the provider know whether consumers have actually migrated, and can inform targeted outreach to anyone still using it close to the deadline.
5. **The version is actually removed on the sunset date** — this is what makes the whole policy credible; a sunset date that's repeatedly pushed back trains consumers to ignore future deadlines entirely.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline: deprecation is announced, consumers migrate during a notice window, and the version is removed on the fixed sunset date">
  <line x1="40" y1="100" x2="620" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="80" cy="100" r="6" fill="#f0883e"/>
  <text x="80" y="80" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">deprecation announced</text>

  <rect x="80" y="115" width="440" height="30" rx="4" fill="none" stroke="#79c0ff" stroke-dasharray="3,2"/>
  <text x="300" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">migration window -- both versions work</text>

  <circle cx="560" cy="100" r="6" fill="#f85149"/>
  <text x="560" y="80" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">sunset date -- removed</text>
</svg>

A fixed window between announcement and sunset, during which both versions coexist and consumers migrate.

## 5. Runnable example

Scenario: a deprecation tracker managing a version's lifecycle. We start with a basic deprecation announcement with a sunset date, extend it to monitoring which consumers are still using the deprecated version as the date approaches, then handle the hard case: the sunset date arriving while some consumers still haven't migrated, requiring a deliberate decision rather than either silently removing (breaking them) or silently extending forever (undermining the policy's credibility).

### Level 1 — Basic

```java
// File: DeprecationAnnouncementBasic.java -- models ANNOUNCING a
// deprecation with an EXPLICIT sunset date, while the OLD version
// continues to work normally during the notice period.
import java.time.*;

public class DeprecationAnnouncementBasic {
    record DeprecationNotice(String version, LocalDate announcedDate, LocalDate sunsetDate, String migrateTo) {}

    static DeprecationNotice v1Deprecation = new DeprecationNotice(
        "v1", LocalDate.of(2024, 1, 15), LocalDate.of(2024, 7, 15), "v2"
    );

    static String handleV1Request(String orderId) {
        System.out.println("[server] serving v1 request -- DEPRECATED, sunset on " + v1Deprecation.sunsetDate()
                + ", migrate to " + v1Deprecation.migrateTo());
        return "{\"id\":\"" + orderId + "\"}"; // v1 still works normally
    }

    public static void main(String[] args) {
        String response = handleV1Request("42");
        System.out.println("[client] received: " + response);
    }
}
```

How to run: `java DeprecationAnnouncementBasic.java`

`handleV1Request` still returns a fully valid response — deprecation doesn't mean broken, it means flagged — while every response includes a clear notice of the sunset date and migration target, giving the consumer everything they need to plan without disrupting them today.

### Level 2 — Intermediate

```java
// File: DeprecationUsageMonitoring.java -- the SAME deprecated version,
// now with USAGE MONITORING tracking WHICH consumers are still calling
// it as the sunset date approaches -- informing whether outreach is needed.
import java.time.*;
import java.util.*;

public class DeprecationUsageMonitoring {
    record DeprecationNotice(String version, LocalDate sunsetDate, String migrateTo) {}
    static DeprecationNotice v1Deprecation = new DeprecationNotice("v1", LocalDate.of(2024, 7, 15), "v2");

    static Map<String, Integer> consumerCallCounts = new LinkedHashMap<>();

    static String handleV1Request(String callingConsumer, String orderId) {
        consumerCallCounts.merge(callingConsumer, 1, Integer::sum);
        return "{\"id\":\"" + orderId + "\"}";
    }

    public static void main(String[] args) {
        handleV1Request("legacy-reporting-tool", "1");
        handleV1Request("legacy-reporting-tool", "2");
        handleV1Request("mobile-app-v3.2", "3");

        System.out.println("[monitoring] " + v1Deprecation.version() + " usage as of today, sunset " + v1Deprecation.sunsetDate() + ":");
        for (Map.Entry<String, Integer> entry : consumerCallCounts.entrySet()) {
            System.out.println("  " + entry.getKey() + ": " + entry.getValue() + " calls -- STILL ON v1, needs outreach");
        }
    }
}
```

How to run: `java DeprecationUsageMonitoring.java`

`consumerCallCounts` accumulates per-consumer call counts to the deprecated version, keyed by whatever identifies the calling consumer (an API key, a user-agent string) — this gives the provider a concrete, actionable list of exactly which consumers still need to migrate, rather than a vague sense that "someone" might still be using the old version.

### Level 3 — Advanced

```java
// File: SunsetDateArrivesWithStragglers.java -- the SAME monitored
// deprecation, now handling the PRODUCTION-FLAVORED hard case: the SUNSET
// DATE ARRIVES, but usage monitoring shows SOME consumers STILL haven't
// migrated. Neither silently removing (breaking them without warning,
// despite the formal notice) nor silently extending forever (undermining
// the policy's credibility for every FUTURE deprecation) is automatic --
// this requires an explicit, deliberate decision, made visible in code.
import java.time.*;
import java.util.*;

public class SunsetDateArrivesWithStragglers {
    record DeprecationNotice(String version, LocalDate sunsetDate, String migrateTo) {}
    static DeprecationNotice v1Deprecation = new DeprecationNotice("v1", LocalDate.of(2024, 7, 15), "v2");

    static Map<String, Integer> consumerCallCounts = new LinkedHashMap<>(Map.of(
        "legacy-reporting-tool", 340, // still actively using v1, hasn't migrated
        "old-partner-integration", 12  // trickle of stragglers
    ));

    static LocalDate today = LocalDate.of(2024, 7, 15); // the sunset date has arrived

    static void evaluateSunsetDecision() {
        boolean sunsetDateReached = !today.isBefore(v1Deprecation.sunsetDate());
        System.out.println("[sunset check] today=" + today + ", sunset date=" + v1Deprecation.sunsetDate()
                + " -- date reached: " + sunsetDateReached);

        if (!sunsetDateReached) {
            System.out.println("[decision] sunset date not yet reached -- v1 continues normally");
            return;
        }

        if (consumerCallCounts.isEmpty()) {
            System.out.println("[decision] sunset date reached, ZERO remaining consumers -- v1 REMOVED cleanly, no impact");
            return;
        }

        System.out.println("[decision] sunset date reached, but " + consumerCallCounts.size()
                + " consumer(s) still active on v1: " + consumerCallCounts);
        System.out.println("[decision] REQUIRES A DELIBERATE CALL: either (a) remove v1 now, accepting these consumers break,"
                + " having had full formal notice, or (b) grant a short, EXPLICIT final extension with direct outreach --"
                + " this is a business decision, not an automatic one, and must be made visibly, not by default inaction");
    }

    public static void main(String[] args) {
        evaluateSunsetDecision();
    }
}
```

How to run: `java SunsetDateArrivesWithStragglers.java`

`evaluateSunsetDecision` first checks whether the sunset date has actually arrived, then checks whether `consumerCallCounts` is empty. Because it's non-empty here (two consumers still actively calling v1), the code explicitly refuses to make the removal-or-extension decision silently or automatically — it prints the exact remaining consumers and their call volumes, and states plainly that a deliberate, visible decision is required, rather than letting the deprecated version linger indefinitely by default inaction, or removing it and silently breaking real, known consumers without any final signal.

## 6. Walkthrough

Trace `SunsetDateArrivesWithStragglers.main` in order. **First**, `evaluateSunsetDecision()` computes `sunsetDateReached` by checking `!today.isBefore(v1Deprecation.sunsetDate())` — since `today` is set to exactly `2024-07-15`, matching the sunset date, `isBefore` is `false`, so `sunsetDateReached` is `true`.

**Next**, the `if (!sunsetDateReached)` check is `false` (the date has been reached), so that early-return branch is skipped, and execution proceeds to check `consumerCallCounts.isEmpty()`.

**Then**, `consumerCallCounts` contains two entries — `legacy-reporting-tool` and `old-partner-integration` — so `isEmpty()` is `false`, meaning the clean-removal branch is also skipped.

**After that**, execution falls through to the final branch, which prints the exact set of remaining consumers and their call counts, followed by an explicit statement that a deliberate decision is required between two named options — immediate removal (accepting the consequence, since formal notice was given) or a final, explicit extension with direct outreach — rather than either outcome happening automatically or silently.

**Finally**, the program ends having made no unilateral decision on the provider's behalf — the code's entire point in this scenario is to surface the situation clearly and force a human, business-level decision, rather than letting the sunset policy either collapse into "never actually enforced" or "broke real consumers with no final acknowledgment."

```
[sunset check] today=2024-07-15, sunset date=2024-07-15 -- date reached: true
[decision] sunset date reached, but 2 consumer(s) still active on v1: {legacy-reporting-tool=340, old-partner-integration=12}
[decision] REQUIRES A DELIBERATE CALL: either (a) remove v1 now, accepting these consumers break, having had full formal notice, or (b) grant a short, EXPLICIT final extension with direct outreach -- this is a business decision, not an automatic one, and must be made visibly, not by default inaction
```

## 7. Gotchas & takeaways

> A sunset date that gets silently pushed back every time it arrives, without ever actually being enforced, teaches every consumer that your deprecation deadlines aren't real — which means the *next* deprecation you announce will be taken less seriously, compounding the problem for every future migration you'll ever need consumers to make.
- Deprecation notices should be visible in the response itself (standard headers like `Deprecation` and `Sunset` exist for exactly this) so consumers can detect and even automate alerts on deprecated usage, not just rely on someone reading a changelog once.
- Usage monitoring (Level 2) is what makes the sunset-date decision (Level 3) informed rather than a guess — knowing exactly who's still on the old version, and how much, is essential input to deciding whether removal is safe or a final extension is warranted.
- This entire lifecycle depends on [API versioning strategies](0494-api-versioning-strategies-uri-header-media-type.md) existing in the first place — you can only deprecate and sunset a *version* if versioning gives you a way to keep old and new coexisting during the notice period.
- Give migration lead time proportional to how disruptive the change actually is — a trivial field rename might need only weeks of notice; a fundamentally different authentication mechanism might reasonably need many months.
