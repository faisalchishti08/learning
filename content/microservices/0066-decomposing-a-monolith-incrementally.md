---
card: microservices
gi: 66
slug: decomposing-a-monolith-incrementally
title: "Decomposing a monolith incrementally"
---

## 1. What it is

Decomposing a monolith incrementally means extracting one bounded context at a time into its own service, verifying it in production, and only then moving on to the next — rather than attempting to redesign the whole system into microservices in a single, sweeping rewrite. It pulls together the other techniques in this section: [event storming](0063-event-storming-for-boundary-discovery.md) or [DDD](0049-bounded-context.md) to find the boundary, [identifying seams](0069-identifying-seams-in-a-monolith.md) to find a safe cut line, the [strangler fig pattern](0064-strangler-fig-pattern.md) to route traffic during the transition, [branch by abstraction](0065-branch-by-abstraction.md) to swap the implementation safely, and [database decomposition](0068-database-decomposition-splitting-a-shared-schema.md) to split the data.

## 2. Why & when

A full-system, big-bang microservices migration carries enormous risk: it takes months or years, the business keeps needing new features throughout, and the design only gets validated against real production traffic on the day of the final cutover — the worst possible time to discover a design flaw. Incremental decomposition inverts that risk profile. Each extracted service is validated against real traffic almost immediately after extraction, while the bulk of the system remains the known-working monolith. If an extraction reveals the boundary was drawn wrong, the cost of that mistake is contained to one service, not the whole rewrite.

Choose incremental decomposition whenever there's an existing, live monolith to migrate. It also naturally accommodates the reality that most organizations cannot pause feature delivery for a rewrite — incremental extraction and ordinary feature work can proceed in parallel.

## 3. Core concept

Order matters: extract the pieces with the fewest and clearest dependencies first, building both team confidence and reusable migration tooling before tackling the monolith's most tangled, business-critical core.

```
1. Pick candidate (event storming / seam analysis)
2. Extract behind a routing facade (strangler fig) + interface (branch by abstraction)
3. Split its data out (database decomposition)
4. Verify in production, keep monolith path as fallback
5. Once trusted: remove monolith code + fallback for that piece
6. Repeat from step 1 for the NEXT candidate
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A monolith shrinks over three extraction rounds as Notifications, then Shipping, then Ordering are pulled out into their own services, one at a time">
  <rect x="20" y="20" width="180" height="180" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <text x="110" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">round 1: everything</text>

  <rect x="230" y="20" width="140" height="180" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <text x="300" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">round 2: shrinking</text>
  <rect x="380" y="20" width="60" height="45" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="410" y="46" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Notif.</text>

  <rect x="460" y="20" width="90" height="180" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="505" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <text x="505" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">round 3: core only</text>
  <rect x="560" y="20" width="65" height="45" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="592" y="46" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Notif.</text>
  <rect x="560" y="75" width="65" height="45" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="592" y="101" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Shipping</text>
</svg>

Each round extracts one more bounded context; the monolith shrinks a little more each time.

## 5. Runnable example

Scenario: a monolith handling orders, notifications, and shipping in one class, decomposed in two incremental rounds — first extracting Notifications (low-risk, few dependents), then extracting Shipping (higher-risk, depends on Order state) — tracking after each round which capabilities the monolith still owns.

### Level 1 — Basic

```java
// File: MonolithBeforeExtraction.java -- one class owns Orders,
// Notifications, and Shipping. This is round 0: nothing extracted yet.
import java.util.*;

public class MonolithBeforeExtraction {
    static class Monolith {
        List<String> ownedCapabilities = new ArrayList<>(List.of("Orders", "Notifications", "Shipping"));

        void placeOrder(String id) {
            System.out.println("[Monolith/Orders] order " + id + " placed");
            System.out.println("[Monolith/Notifications] email sent for " + id);
            System.out.println("[Monolith/Shipping] shipment scheduled for " + id);
        }
    }

    public static void main(String[] args) {
        Monolith monolith = new Monolith();
        monolith.placeOrder("ORD-1");
        System.out.println("Monolith still owns: " + monolith.ownedCapabilities);
    }
}
```

**How to run:** `javac MonolithBeforeExtraction.java && java MonolithBeforeExtraction` (JDK 17+).

Expected output:
```
[Monolith/Orders] order ORD-1 placed
[Monolith/Notifications] email sent for ORD-1
[Monolith/Shipping] shipment scheduled for ORD-1
Monolith still owns: [Orders, Notifications, Shipping]
```

### Level 2 — Intermediate

```java
// File: ExtractNotifications.java -- round 1: Notifications is the
// LOWEST-RISK candidate (few dependents, no shared writes to Order data),
// so it is extracted first, behind a facade, while Orders and Shipping stay put.
import java.util.*;

public class ExtractNotifications {
    static class NotificationService { // NEW, standalone service
        void send(String orderId) { System.out.println("[NotificationService] email sent for " + orderId); }
    }

    static class Monolith {
        List<String> ownedCapabilities = new ArrayList<>(List.of("Orders", "Shipping")); // Notifications removed
        NotificationService notifications = new NotificationService(); // calls OUT to the new service now

        void placeOrder(String id) {
            System.out.println("[Monolith/Orders] order " + id + " placed");
            notifications.send(id); // was in-process, now a call to an extracted service
            System.out.println("[Monolith/Shipping] shipment scheduled for " + id);
        }
    }

    public static void main(String[] args) {
        Monolith monolith = new Monolith();
        monolith.placeOrder("ORD-1");
        System.out.println("Monolith still owns: " + monolith.ownedCapabilities);
    }
}
```

**How to run:** `javac ExtractNotifications.java && java ExtractNotifications` (JDK 17+).

Expected output:
```
[Monolith/Orders] order ORD-1 placed
[NotificationService] email sent for ORD-1
[Monolith/Shipping] shipment scheduled for ORD-1
Monolith still owns: [Orders, Shipping]
```

The externally observable order-placement flow is unchanged — only the second line's source changed, from an in-process method to a call against a standalone `NotificationService`. This is one full "round" of incremental extraction, completed and shippable on its own.

### Level 3 — Advanced

```java
// File: ExtractShippingWithFallback.java -- round 2: Shipping is
// extracted next -- HIGHER risk, because it depends on order data. Wrap
// the call with a strangler-fig-style fallback in case the new service
// isn't ready yet, so this round doesn't jeopardize order placement itself.
import java.util.*;

public class ExtractShippingWithFallback {
    static class NotificationService {
        void send(String orderId) { System.out.println("[NotificationService] email sent for " + orderId); }
    }

    static class ShippingService { // NEW, standalone service, still maturing
        void scheduleShipment(String orderId) {
            if (orderId.equals("ORD-2")) throw new RuntimeException("ShippingService not ready for " + orderId);
            System.out.println("[ShippingService] shipment scheduled for " + orderId);
        }
    }

    static class Monolith {
        List<String> ownedCapabilities = new ArrayList<>(List.of("Orders")); // only the core remains
        NotificationService notifications = new NotificationService();
        ShippingService shipping = new ShippingService();

        void legacyScheduleShipment(String orderId) { // kept temporarily as a fallback
            System.out.println("[Monolith/Shipping-fallback] shipment scheduled for " + orderId);
        }

        void placeOrder(String id) {
            System.out.println("[Monolith/Orders] order " + id + " placed");
            notifications.send(id);
            try {
                shipping.scheduleShipment(id);
            } catch (RuntimeException e) {
                System.out.println("  [round-2 fallback: " + e.getMessage() + "]");
                legacyScheduleShipment(id);
            }
        }
    }

    public static void main(String[] args) {
        Monolith monolith = new Monolith();
        monolith.placeOrder("ORD-1"); // ShippingService healthy
        monolith.placeOrder("ORD-2"); // ShippingService fails, falls back
        System.out.println("Monolith still owns: " + monolith.ownedCapabilities);
    }
}
```

**How to run:** `javac ExtractShippingWithFallback.java && java ExtractShippingWithFallback` (JDK 17+).

Expected output:
```
[Monolith/Orders] order ORD-1 placed
[NotificationService] email sent for ORD-1
[ShippingService] shipment scheduled for ORD-1
[Monolith/Orders] order ORD-2 placed
[NotificationService] email sent for ORD-2
  [round-2 fallback: ShippingService not ready for ORD-2]
[Monolith/Shipping-fallback] shipment scheduled for ORD-2
Monolith still owns: [Orders]
```

By the end of round 2, `ownedCapabilities` has shrunk to just `[Orders]` — the monolith's true bounded core — while both Notifications and Shipping now live in their own services, with Shipping still protected by a temporary fallback until it earns enough production trust to have that fallback (and `legacyScheduleShipment`) deleted entirely.

## 6. Walkthrough

1. **Level 1 (round 0)** — `Monolith.placeOrder` handles Orders, Notifications, and Shipping in one method, all three capabilities listed in `ownedCapabilities`. This is the starting state before any decomposition.
2. **Level 2 (round 1)** — Notifications is chosen first specifically *because* it is low-risk: nothing else in the flow depends on its output, and it doesn't write back into order state. `ExtractNotifications.Monolith.placeOrder` now calls out to a standalone `NotificationService` for that one line, while `ownedCapabilities` drops to `[Orders, Shipping]`. Running `main` shows the exact same three log lines in the exact same order as Level 1 — the extraction is invisible to any caller of `placeOrder`, which is the entire point: round 1 shipped a real architectural change with zero externally visible behavior change.
3. **Level 3 (round 2)** — Shipping is extracted next, but it's treated as higher-risk (in a real system, because shipment scheduling might need to read order line items, a genuine cross-context dependency), so the extraction is wrapped in a try/catch fallback exactly like the [strangler fig pattern](0064-strangler-fig-pattern.md)'s facade-level fallback, just applied at the method level.
4. **Tracing `placeOrder("ORD-1")`** — Orders line prints, `notifications.send` succeeds and prints, then `shipping.scheduleShipment("ORD-1")` succeeds and prints directly — no fallback needed.
5. **Tracing `placeOrder("ORD-2")`** — Orders and Notifications proceed identically, but `shipping.scheduleShipment("ORD-2")` throws (simulating the new `ShippingService` not yet being fully production-ready for this case). The `catch` block prints the `[round-2 fallback: ...]` diagnostic and then calls `legacyScheduleShipment`, still present in the monolith specifically as a temporary safety net — printing the fallback's own log line.
6. **Final state** — `ownedCapabilities` prints as `[Orders]`, confirming the monolith has shrunk to its true core across two independent, individually-verified rounds. The pattern for round 3, round 4, and so on is identical: pick the next candidate, extract behind a fallback, verify, then delete the fallback and repeat.

## 7. Gotchas & takeaways

> **Gotcha:** extracting the hardest, most tangled part of the monolith first (often the "core" business logic) before the team has any practice with the extraction process is a common and costly mistake. Build confidence and reusable tooling on lower-risk extractions first, exactly as Notifications was chosen before Shipping here.

- Incremental decomposition sequences the *order* of extraction as much as the mechanics of any single extraction — pick low-risk, low-dependency candidates first.
- Each round should be independently shippable and independently verifiable in production, with the monolith continuing to serve everything not yet extracted.
- A temporary fallback to the old in-monolith code (as with `legacyScheduleShipment`) de-risks each round; remove it, and the corresponding monolith code, only once the new service is trusted.
- This process leans on several other techniques together: [event storming](0063-event-storming-for-boundary-discovery.md) or DDD to find boundaries, [seam identification](0069-identifying-seams-in-a-monolith.md) to find safe cut points, and [database decomposition](0068-database-decomposition-splitting-a-shared-schema.md) to split the data layer.
- Track "what the monolith still owns" explicitly (as `ownedCapabilities` does here) — it turns an open-ended migration into a visibly shrinking, measurable list.
