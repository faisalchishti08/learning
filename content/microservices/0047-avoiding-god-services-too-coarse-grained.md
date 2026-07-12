---
card: microservices
gi: 47
slug: avoiding-god-services-too-coarse-grained
title: Avoiding god services (too coarse-grained)
---

## 1. What it is

A **god service** is the opposite failure mode from a [chatty service](0046-avoiding-chatty-services-too-fine-grained.md): a single service that has grown to own far too much — many unrelated business capabilities, many unrelated data entities, code changed by many unrelated teams — until it behaves like the exact monolith microservices was meant to move away from, just now wrapped in a "microservice" label and its own deployment pipeline. It's the direct violation of [Single Responsibility Principle at the service level](0017-single-responsibility-principle-at-service-level.md), typically arrived at gradually, one "just one more small addition" at a time.

## 2. Why & when

God services usually don't start that way — they grow into it. A service that begins with one clear responsibility accumulates unrelated features over time because it's often easier, in the short term, to add "just one more endpoint" to an existing, already-deployed service than to properly stand up a new one. Each individual addition seems reasonable in isolation; the cumulative effect, after enough of them, is a service that inherited a monolith's coordination problems (many unrelated teams needing to coordinate releases) while also carrying a microservice's network overhead for anyone calling into it.

Watch for the warning signs continuously, not just at initial design time: a service whose codebase keeps growing across multiple unrelated business concerns, a service more than one team regularly needs to modify for unrelated reasons, or a service whose deploys are held up waiting on unrelated features to finish. Any of these, especially several together, is a concrete signal a service has become — or is becoming — a god service.

## 3. Core concept

The concrete detection method: count genuinely distinct responsibilities and teams touching one service's code.

- **Well-scoped service:** one core responsibility, one owning team, changes driven by one coherent concern.
- **God service:** multiple unrelated responsibilities (orders, notifications, reporting, user preferences...) bundled together, multiple teams pushing unrelated code, changes driven by many unrelated concerns that happen to share a deploy pipeline purely by historical accident.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A well-scoped service has one responsibility and one team; a god service has accumulated many unrelated responsibilities and many teams pushing unrelated code into the same deployable unit">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Well-scoped</text>
  <rect x="60" y="40" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersService</text>
  <text x="150" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">one responsibility</text>
  <text x="150" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">one owning team</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">God service</text>
  <rect x="380" y="30" width="240" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="500" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"CoreService"</text>
  <text x="500" y="68" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders + notifications</text>
  <text x="500" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">+ reporting + preferences</text>
  <text x="500" y="96" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">4+ teams pushing code</text>
</svg>

One clean responsibility per service, versus an accumulation of unrelated concerns sharing one deployable unit.

## 5. Runnable example

Scenario: a service that grows, addition by addition, into a god service, then measured to reveal the accumulated coupling, then split back into properly-scoped services.

### Level 1 — Basic

```java
// File: WellScopedStart.java -- a service that starts with ONE clear responsibility
public class WellScopedStart {
    static class OrderService {
        String placeOrder(String item) { return "order placed: " + item; }
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService();
        System.out.println(orders.placeOrder("widget"));
    }
}
```

**How to run:** `javac WellScopedStart.java && java WellScopedStart` (JDK 17+).

Expected output:
```
order placed: widget
```

A clean, single-responsibility service — exactly what it should look like before any scope creep begins.

### Level 2 — Intermediate

```java
// File: GradualScopeCreep.java -- the SAME service, after several
// "just one more small addition" decisions over time.
public class GradualScopeCreep {
    static class CoreService { // renamed from "OrderService" -- a subtle early warning sign
        String placeOrder(String item) { return "order placed: " + item; } // original responsibility

        String sendEmail(String to, String subject) { return "email sent to " + to + ": " + subject; } // added by NotificationsTeam

        String generateSalesReport() { return "sales report generated"; } // added by AnalyticsTeam

        String updateUserPreference(String userId, String key, String value) { return "preference " + key + " updated for " + userId; } // added by PlatformTeam
    }

    public static void main(String[] args) {
        CoreService service = new CoreService();
        System.out.println(service.placeOrder("widget"));
        System.out.println(service.sendEmail("alice@example.com", "Order confirmed"));
        System.out.println(service.generateSalesReport());
        System.out.println(service.updateUserPreference("cust-1", "theme", "dark"));
    }
}
```

**How to run:** `javac GradualScopeCreep.java && java GradualScopeCreep` (JDK 17+).

Expected output:
```
order placed: widget
email sent to alice@example.com: Order confirmed
sales report generated
preference theme updated for cust-1
```

Four genuinely unrelated responsibilities — order placement, email sending, report generation, and user preferences — now live in one class, each added by a different team for their own unrelated reason. Deploying a fix to any one of these four requires coordinating with, or at least being cautious about, the other three.

### Level 3 — Advanced

```java
// File: SplitBackApart.java -- detect the accumulated responsibilities,
// then split the god service back into FOUR properly-scoped services.
import java.util.*;

public class SplitBackApart {
    // detection: count DISTINCT responsibilities by grouping method names by their concern
    static Map<String, List<String>> detectResponsibilities() {
        Map<String, List<String>> responsibilities = new LinkedHashMap<>();
        responsibilities.put("Orders", List.of("placeOrder"));
        responsibilities.put("Notifications", List.of("sendEmail"));
        responsibilities.put("Analytics", List.of("generateSalesReport"));
        responsibilities.put("Preferences", List.of("updateUserPreference"));
        return responsibilities;
    }

    // the SPLIT: four properly-scoped services, each owned by ONE team
    static class OrderService { String placeOrder(String item) { return "order placed: " + item; } }
    static class NotificationService { String sendEmail(String to, String subject) { return "email sent to " + to + ": " + subject; } }
    static class AnalyticsService { String generateSalesReport() { return "sales report generated"; } }
    static class PreferencesService { String updatePreference(String userId, String key, String value) { return "preference " + key + " updated for " + userId; } }

    public static void main(String[] args) {
        Map<String, List<String>> responsibilities = detectResponsibilities();
        System.out.println("Detected " + responsibilities.size() + " distinct responsibilities bundled in CoreService:");
        for (var entry : responsibilities.entrySet()) System.out.println("  " + entry.getKey() + ": " + entry.getValue());

        System.out.println("Splitting into " + responsibilities.size() + " properly-scoped services:");
        System.out.println(new OrderService().placeOrder("widget"));
        System.out.println(new NotificationService().sendEmail("alice@example.com", "Order confirmed"));
        System.out.println(new AnalyticsService().generateSalesReport());
        System.out.println(new PreferencesService().updatePreference("cust-1", "theme", "dark"));
    }
}
```

**How to run:** `javac SplitBackApart.java && java SplitBackApart` (JDK 17+).

Expected output:
```
Detected 4 distinct responsibilities bundled in CoreService:
  Orders: [placeOrder]
  Notifications: [sendEmail]
  Analytics: [generateSalesReport]
  Preferences: [updateUserPreference]
Splitting into 4 properly-scoped services:
order placed: widget
email sent to alice@example.com: Order confirmed
sales report generated
preference theme updated for cust-1
```

The production-flavored fix: `detectResponsibilities` makes the god service's accumulated scope explicit and countable — 4 genuinely distinct concerns, each traceable to a different team's addition. The split into `OrderService`, `NotificationService`, `AnalyticsService`, and `PreferencesService` restores exactly what [service per team](0043-service-per-team.md) and [single responsibility at the service level](0017-single-responsibility-principle-at-service-level.md) call for — each service can now be deployed, owned, and reasoned about independently of the other three.

## 6. Walkthrough

1. `detectResponsibilities()` returns a map grouping method names under four responsibility labels — `"Orders"`, `"Notifications"`, `"Analytics"`, `"Preferences"` — representing the analysis step of recognizing that `CoreService`'s four methods actually serve four unrelated purposes, not one.
2. The first loop prints each detected responsibility and the method(s) that belong to it, turning "this service feels overloaded" into a specific, itemized list — exactly the kind of concrete evidence [identifying service boundaries](0044-identifying-service-boundaries.md) calls for before acting.
3. `new OrderService().placeOrder("widget")` constructs and calls the first newly-split service, producing the exact same observable output as `CoreService.placeOrder` did in Level 2 — the behavior is unchanged; only the deployment and ownership boundary has moved.
4. The remaining three calls — `NotificationService.sendEmail`, `AnalyticsService.generateSalesReport`, `PreferencesService.updatePreference` — each run against their own newly-split, independent class, again preserving Level 2's exact observable behavior while separating what were previously four intertwined concerns into four independently deployable, independently ownable units.
5. After this split, a fix to `NotificationService`'s email logic touches only `NotificationService` — `OrderService`, `AnalyticsService`, and `PreferencesService` are entirely unaffected, unlike in Level 2 where all four lived in one class sharing one deploy.

```
CoreService (god service):  placeOrder + sendEmail + generateSalesReport + updateUserPreference  (1 class, 4 teams)
        |
   detect 4 distinct responsibilities
        |
OrderService | NotificationService | AnalyticsService | PreferencesService   (4 classes, 4 independent teams)
```

## 7. Gotchas & takeaways

> **Gotcha:** splitting a god service back apart is genuinely harder than the reverse — data that accumulated in one shared store during the god-service phase often needs to be carefully migrated and re-partitioned across the newly-split services, and any code elsewhere in the system that came to depend on the god service's convenient "everything in one place" API needs to be updated to call the right service instead. This is exactly why watching for scope creep continuously, and resisting "just one more small addition," is much cheaper than the eventual untangling.

- A god service accumulates many unrelated responsibilities over time, usually through a series of individually-reasonable "just one more small addition" decisions, until it recreates a monolith's coordination cost while also carrying microservices' network overhead.
- The concrete detection method: count genuinely distinct responsibilities and teams regularly pushing code into one service — several unrelated concerns bundled together is a clear signal.
- Watch for warning signs continuously as a system evolves, not just during initial design — scope creep happens gradually, and each individual addition rarely looks alarming in isolation.
- Splitting a god service back apart is more expensive than avoiding the accumulation in the first place, since it requires migrating shared data and updating every caller that came to depend on the service's convenient, but improperly broad, single API.
