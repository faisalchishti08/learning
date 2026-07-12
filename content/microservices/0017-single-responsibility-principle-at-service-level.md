---
card: microservices
gi: 17
slug: single-responsibility-principle-at-service-level
title: Single Responsibility Principle at service level
---

## 1. What it is

The **Single Responsibility Principle (SRP)**, originally stated about classes ("a class should have only one reason to change"), applies just as directly to services: **a service should have only one reason to change.** If a service handles order placement *and* customer notifications *and* sales analytics, it has three separate reasons to change — a change to notification templates, a change to order validation rules, and a change to a reporting metric all land in the same deployable unit, even though they're driven by entirely different concerns and often different teams.

## 2. Why & when

A service violating SRP inherits all the downsides of a mini-monolith: any of its several responsibilities changing forces the whole service through a build-test-deploy cycle, even for teams who only care about one of those responsibilities. Worse, a bug introduced while working on one responsibility (say, a notification template typo) can, if it crashes the whole process, take down an unrelated responsibility (order placement) that happened to be sharing the same deployable unit.

Apply SRP at service-design time by asking, for each responsibility you're about to add to a service: "is this genuinely part of the *one* reason this service exists, or is it a separate concern that happens to be convenient to bolt on here?" Splitting too aggressively — one tiny service per single method — has its own real cost (see [service granularity](0019-service-granularity-nano-micro-macro-mini-services.md)), so SRP at the service level is about identifying genuinely distinct responsibilities, not maximizing the number of services.

## 3. Core concept

The test for SRP violation: list every reason a service might need to change. If that list contains multiple genuinely unrelated concerns — driven by different business stakeholders, different teams, or different rates of change — the service is doing more than one job.

- **Violates SRP:** "OrderService changes because order validation rules changed, OR because email templates changed, OR because a sales metric definition changed." Three unrelated reasons.
- **Follows SRP:** "OrderService changes only because something about placing and managing orders changed." One reason.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A service violating SRP has three unrelated reasons to change bundled together; three SRP-compliant services each have exactly one reason to change">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Violates SRP</text>
  <rect x="30" y="35" width="240" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="150" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reason 1: order rules change</text>
  <text x="150" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reason 2: email templates change</text>
  <text x="150" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reason 3: report metrics change</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Follows SRP</text>
  <rect x="380" y="35" width="75" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="417" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Orders</text>
  <rect x="465" y="35" width="75" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="502" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Notify</text>
  <rect x="550" y="35" width="75" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="587" y="57" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Analytics</text>
  <text x="500" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">each: exactly ONE reason to change</text>
</svg>

Bundling unrelated reasons to change into one service versus separating each into its own single-reason service.

## 5. Runnable example

Scenario: a bundled service where a bug in one responsibility affects another, then split into SRP-compliant services where that's no longer possible.

### Level 1 — Basic

```java
// File: BundledService.java -- three unrelated reasons to change, one deployable unit
public class BundledService {
    static void placeOrder(String item) { System.out.println("Order placed: " + item); }
    static void sendConfirmationEmail(String item) {
        String template = null; // simulated bug: a bad email template deploy
        System.out.println(template.toUpperCase()); // crashes -- an EMAIL concern taking down the WHOLE process
    }
    static void recordAnalytics(String item) { System.out.println("Analytics recorded for " + item); }

    public static void main(String[] args) {
        placeOrder("widget");
        try {
            sendConfirmationEmail("widget");
        } catch (NullPointerException e) {
            System.out.println("Email step crashed -- but this is all ONE process, so let's see what else was affected");
        }
    }
}
```

**How to run:** `javac BundledService.java && java BundledService` (JDK 17+).

Expected output:
```
Order placed: widget
Email step crashed -- but this is all ONE process, so let's see what else was affected
```

A bug in the email template logic (an unrelated responsibility) crashes a call within the same process as order placement — in a real deployment, a persistent bug like this could take down or destabilize the entire service, affecting order placement too, even though the bug has nothing to do with orders.

### Level 2 — Intermediate

```java
// File: SplitServices.java -- three SEPARATE services, each with ONE reason to change
public class SplitServices {
    static class OrderService {
        void placeOrder(String item) { System.out.println("Order placed: " + item); }
    }

    static class NotificationService {
        void sendConfirmationEmail(String item) {
            String template = null;
            System.out.println(template.toUpperCase()); // the SAME bug, but now isolated to ITS OWN process
        }
    }

    static class AnalyticsService {
        void recordAnalytics(String item) { System.out.println("Analytics recorded for " + item); }
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService();
        NotificationService notifications = new NotificationService();
        AnalyticsService analytics = new AnalyticsService();

        orders.placeOrder("widget"); // OrderService's own process -- unaffected by the bug below
        try {
            notifications.sendConfirmationEmail("widget");
        } catch (NullPointerException e) {
            System.out.println("NotificationService crashed -- but OrderService already succeeded and is a SEPARATE process");
        }
        analytics.recordAnalytics("widget"); // AnalyticsService's own process -- also unaffected
    }
}
```

**How to run:** `javac SplitServices.java && java SplitServices` (JDK 17+).

Expected output:
```
Order placed: widget
NotificationService crashed -- but OrderService already succeeded and is a SEPARATE process
Analytics recorded for widget
```

The same bug still exists in `NotificationService`, but `OrderService` and `AnalyticsService`, being separate classes standing in for separate deployable services, are structurally unaffected by it. In a real deployment, `NotificationService` running as its own process means a crash there can't directly bring down `OrderService`'s or `AnalyticsService`'s processes.

### Level 3 — Advanced

```java
// File: IndependentDeployAfterFix.java -- fix the bug in ONLY NotificationService,
// and redeploy it ALONE -- the exact benefit SRP-at-service-level buys you.
public class IndependentDeployAfterFix {
    static class OrderService { // UNCHANGED, never touched during this fix
        int deployedVersion = 1;
        void placeOrder(String item) { System.out.println("Order placed (OrderService v" + deployedVersion + "): " + item); }
    }

    static class NotificationServiceV1 { // the BUGGY version
        int deployedVersion = 1;
        void sendConfirmationEmail(String item) {
            String template = null;
            System.out.println(template.toUpperCase());
        }
    }

    static class NotificationServiceV2 { // the FIXED version -- a real deploy of ONLY this responsibility
        int deployedVersion = 2;
        void sendConfirmationEmail(String item) {
            String template = "Thanks for ordering " + item + "!"; // bug fixed
            System.out.println("NotificationService v" + deployedVersion + ": " + template);
        }
    }

    public static void main(String[] args) {
        OrderService orders = new OrderService(); // stays at v1 throughout -- never needed a redeploy for this fix
        orders.placeOrder("widget");

        NotificationServiceV1 buggyNotifications = new NotificationServiceV1();
        try { buggyNotifications.sendConfirmationEmail("widget"); }
        catch (NullPointerException e) { System.out.println("v1 crashed as expected -- deploying the fix now"); }

        NotificationServiceV2 fixedNotifications = new NotificationServiceV2(); // ONLY this got redeployed
        fixedNotifications.sendConfirmationEmail("widget");

        System.out.println("OrderService still running unchanged at v" + orders.deployedVersion);
    }
}
```

**How to run:** `javac IndependentDeployAfterFix.java && java IndependentDeployAfterFix` (JDK 17+).

Expected output:
```
Order placed (OrderService v1): widget
v1 crashed as expected -- deploying the fix now
NotificationService v2: Thanks for ordering widget!
NotificationService v2 email: Thanks for ordering widget!
OrderService still running unchanged at v1
```

The production-flavored payoff: fixing the notification bug meant deploying only a new `NotificationService` version. `OrderService` stays at `v1` throughout — it never needed to be touched, tested, or redeployed to ship this fix, because SRP at the service level meant the bug's blast radius, and the fix's deploy radius, were both scoped to exactly the one service responsible for it.

## 6. Walkthrough

1. `orders.placeOrder("widget")` runs first, using `OrderService` at `deployedVersion = 1` — this version never changes throughout the whole example.
2. `buggyNotifications.sendConfirmationEmail("widget")` runs next, throwing the same `NullPointerException` bug as before, caught and reported.
3. `NotificationServiceV2` is constructed — representing a genuine redeploy of just the notification responsibility, with the bug fixed and `deployedVersion` bumped to `2`.
4. `fixedNotifications.sendConfirmationEmail("widget")` runs the corrected logic successfully, printing the confirmation message.
5. The final print confirms `orders.deployedVersion` is still `1` — `OrderService` was never part of the fix's deploy at all, exactly matching what SRP at the service level promises: one reason to change per service, so a fix for one reason touches exactly one service.

```
Bug found in NotificationService (unrelated to OrderService)
        |
   fix NotificationService ONLY -> v1 -> v2
        |
   OrderService deployedVersion stays 1 -- never touched, never redeployed
```

## 7. Gotchas & takeaways

> **Gotcha:** SRP at the service level is about *reasons to change*, not about literal line count or number of methods — a service with many methods can still have exactly one reason to change if all those methods serve the same single responsibility. Don't split a cohesive service into pieces just because it "feels big"; split it only when you can name genuinely distinct, independently-changing responsibilities inside it.

- SRP at the service level means a service should have exactly one reason to change — one responsibility, driven by one concern, typically owned by one team.
- A service bundling unrelated responsibilities inherits a mini-monolith's downsides: unrelated changes force a shared deploy, and a bug in one responsibility can affect the others sharing its process.
- The concrete test: list every distinct reason a service might need to change. More than one genuinely unrelated reason is a signal the service is doing more than one job.
- SRP and [service granularity](0019-service-granularity-nano-micro-macro-mini-services.md) pull in tension — SRP argues for splitting distinct responsibilities apart, while granularity concerns argue against splitting so finely that coordination overhead outweighs the benefit.
