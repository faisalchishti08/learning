---
card: system-design
gi: 205
slug: strangler-fig-migration
title: Strangler-fig migration
---

## 1. What it is

The **strangler-fig migration** pattern replaces a legacy system gradually, one piece at a time, instead of rewriting it all at once. A routing layer (a proxy or [API gateway](0197-service-oriented-architecture-soa.md)) sits in front of the legacy system; as each piece of functionality is rebuilt, the router sends traffic for that piece to the new implementation, while everything not yet migrated still flows to the legacy system. Over time, the legacy system handles less and less, until it can be switched off entirely.

## 2. Why & when

A full "big bang" rewrite — freeze the old system, build a new one from scratch, cut over on one day — is high risk: it takes a long time to deliver any value, and the cutover day is a single high-stakes moment where anything can go wrong with no easy way back. The strangler-fig pattern (named after a fig species that grows around a host tree, gradually replacing it while the tree is still alive) avoids that risk by migrating incrementally, with the legacy system and the new system running side by side for as long as the migration takes.

Use this pattern whenever you must replace a legacy system that is still actively used and cannot simply be taken offline during a rewrite — which describes most real production migrations. It is unnecessary for a genuinely small system where a full rewrite can be done and verified in days.

## 3. Core concept

- **The routing layer.** A reverse proxy or gateway that every request passes through first. It decides, per request (often by URL path or feature flag), whether to send it to the legacy system or the new one.
- **Incremental capability migration.** You pick one feature or endpoint at a time to rebuild — for example, `GET /orders/:id` first — deploy the new implementation, then flip the router to send that one endpoint's traffic to it, while every other endpoint still goes to legacy.
- **Both systems run simultaneously.** For the whole migration period, the legacy system and the new system coexist. This often means both need access to the same underlying data, which is usually the hardest part of the whole migration — legacy and new code must agree on the data, or one must be kept in sync with the other.
- **Reversibility.** Because the router makes the routing decision per-endpoint (not a single global switch), a single migrated piece can be routed back to legacy immediately if the new implementation has a problem — this is the core risk-reduction benefit over a big-bang cutover.
- **Completion = the legacy system does nothing.** The migration is "done" not when the new system is deployed, but when the router sends 100% of traffic to it and the legacy system can be decommissioned.

## 4. Diagram

```
                       +----------------+
   All requests ------>|  Router/Gateway |
                       +--------+-------+
                                |
              routes by endpoint, checked against a migration table:
                                |
         +----------------------+-----------------------+
         |                                               |
   endpoints NOT yet migrated                  endpoints ALREADY migrated
         |                                               |
         v                                               v
  +----------------+                            +------------------+
  | Legacy System   |                            |  New System       |
  | (still serves   |                            |  (serves migrated  |
  |  most traffic)  |                            |   endpoints)       |
  +----------------+                            +------------------+
         |                                               |
         +-------------------- shared data ---------------+
                    (both must agree on current state)

   Over time -> more endpoints move to the right side ->
   eventually Legacy System serves nothing and is retired.
```
*Caption: the router is the single seam where migration progress is visible and controllable — flipping one endpoint's route is a small, reversible change, not a rewrite.*

## 5. Runnable example

**Level 1 — Basic.** A router that sends each request to legacy or new based on a per-endpoint migration table.

**Level 2 — Intermediate.** Migrate one endpoint at a time by updating the table, and verify traffic actually shifts.

**Level 3 — Advanced.** Add a rollback: the new implementation for one endpoint starts failing, and the router falls back to legacy for that endpoint automatically.

```java
// StranglerFigDemo.java
import java.util.*;
import java.util.function.*;

public class StranglerFigDemo {

    interface Handler { String handle(String request); }

    // ---------- The two systems ----------
    static class LegacySystem {
        String handleOrder(String request) { return "[legacy] handled: " + request; }
        String handleUser(String request) { return "[legacy] handled: " + request; }
    }
    static class NewSystem {
        boolean healthy = true;
        String handleOrder(String request) {
            if (!healthy) throw new RuntimeException("new-system order handler is failing");
            return "[new] handled: " + request;
        }
    }

    // ---------- Level 1 & 2: router with a per-endpoint migration table ----------
    static class Router {
        LegacySystem legacy = new LegacySystem();
        NewSystem modern = new NewSystem();
        // Migration table: endpoint -> "legacy" or "new". Starts with everything on legacy.
        Map<String, String> migrationTable = new HashMap<>(Map.of(
            "GET /orders/:id", "legacy",
            "GET /users/:id", "legacy"
        ));

        String route(String endpoint, String request) {
            String target = migrationTable.getOrDefault(endpoint, "legacy");
            if (target.equals("new") && endpoint.equals("GET /orders/:id")) {
                try {
                    return modern.handleOrder(request);
                } catch (RuntimeException e) {
                    // Level 3: automatic rollback to legacy if the new system is unhealthy.
                    System.out.println("    [router] new system failed (" + e.getMessage() + ") -> falling back to legacy");
                    migrationTable.put(endpoint, "legacy"); // roll this one endpoint back
                    return legacy.handleOrder(request);
                }
            }
            if (endpoint.equals("GET /orders/:id")) return legacy.handleOrder(request);
            return legacy.handleUser(request);
        }

        void migrate(String endpoint) {
            migrationTable.put(endpoint, "new");
            System.out.println("  [migration] " + endpoint + " now routes to NEW system");
        }
    }

    public static void main(String[] args) {
        Router router = new Router();

        System.out.println("Level 1 - before migration, everything routes to legacy:");
        System.out.println("  " + router.route("GET /orders/:id", "order-42"));
        System.out.println("  " + router.route("GET /users/:id", "user-7"));

        System.out.println("\nLevel 2 - migrate ONE endpoint, traffic for it shifts to new, others stay on legacy:");
        router.migrate("GET /orders/:id");
        System.out.println("  " + router.route("GET /orders/:id", "order-43")); // now new
        System.out.println("  " + router.route("GET /users/:id", "user-8"));    // still legacy

        System.out.println("\nLevel 3 - new system becomes unhealthy, router auto-falls-back for that endpoint:");
        router.modern.healthy = false;
        System.out.println("  " + router.route("GET /orders/:id", "order-44")); // fails on new, falls back
        System.out.println("  migration table after fallback: " + router.migrationTable);
        System.out.println("  " + router.route("GET /orders/:id", "order-45")); // now back on legacy, no retry needed
    }
}
```

**How to run:** `java StranglerFigDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `router.migrationTable` starts with both endpoints mapped to `"legacy"`. Calling `router.route(...)` for either endpoint checks the table, finds `"legacy"`, and calls the matching `legacy` method — every request goes to the old system, exactly as before any migration work began.
2. **Level 2:** `router.migrate("GET /orders/:id")` updates only that one entry in `migrationTable` to `"new"`. The very next call to `route("GET /orders/:id", ...)` now takes the `target.equals("new")` branch and calls `modern.handleOrder(...)` instead. The call to `route("GET /users/:id", ...)` right after it is unaffected — that endpoint's table entry is still `"legacy"`, so it still calls the old system. This is the incremental migration in action: one endpoint moved, nothing else changed.
3. **Level 3:** `router.modern.healthy` is set to `false`, simulating the new implementation breaking after it was already receiving live traffic. The next call to `route("GET /orders/:id", ...)` enters the `try` block, calls `modern.handleOrder(...)`, which throws.
4. **The `catch` block runs**: it prints the failure, then calls `migrationTable.put(endpoint, "legacy")` — rolling that one endpoint's route back to legacy — and immediately serves the current request from `legacy.handleOrder(...)` so the caller still gets a valid response, not an error.
5. **The final `route(...)` call** for the same endpoint now finds `"legacy"` in the table again and goes straight to `legacy.handleOrder(...)`, with no attempt to call the broken new system — this is the reversibility the pattern promises: a bad migration step is caught and undone for just that one piece, without touching any other already-migrated endpoint.

## 7. Gotchas & takeaways

> **Gotcha:** the hardest part of a real strangler-fig migration is almost never the routing layer — it is keeping data consistent when legacy and new systems must both read and write the same underlying data during the overlap period. Plan the data strategy (dual writes, a sync process, or a shared database) before picking the first endpoint to migrate.

- Migrate small, low-risk pieces first to prove the pattern and the routing infrastructure work, before moving business-critical endpoints.
- Keep the routing decision reversible per-piece, as shown in Level 3 — this is what makes the pattern lower-risk than a big-bang rewrite, not just "doing the rewrite slowly."
- The migration is not finished when the new system is deployed — it is finished when the router sends 100% of traffic to it and the legacy system's code and data can actually be deleted.
- This pattern is commonly the practical path when migrating a [monolith](0195-monolith-modular-monolith.md) toward [microservices](0196-microservices.md) — each strangled piece becomes one new independently deployable service.
