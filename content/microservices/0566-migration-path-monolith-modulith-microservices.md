---
card: microservices
gi: 566
slug: migration-path-monolith-modulith-microservices
title: "Migration path: monolith → Modulith → microservices"
---

## 1. What it is

A **migration path** from a monolith to microservices rarely succeeds as a single, risky big-bang rewrite — a proven intermediate step is restructuring the monolith internally into well-defined, loosely-coupled modules first (a **modular monolith**, which Spring's own **Spring Modulith** project provides explicit tooling for), and only *then* extracting individual modules into separately-deployed microservices, one at a time, once each module's boundary has already been proven clean *while still running in a single process*. This staged approach catches boundary mistakes cheaply (a bad module boundary is a refactor; a bad microservice boundary, discovered after extraction, is a much costlier distributed-systems problem to fix) before paying any of the operational cost of actual distribution.

## 2. Why & when

You follow this staged migration path specifically because jumping straight from monolith to microservices skips the cheapest, safest opportunity to validate your service boundaries:

- **A monolith's internal module boundaries can be wrong in ways that are cheap to fix, as long as they're still just code organization within one process** — a misplaced class, a leaky abstraction between two modules, an accidental shared-state dependency are all straightforward refactors when everything still runs in one JVM, with the compiler and a good test suite catching many mistakes directly.
- **The exact same boundary mistakes, discovered only *after* extracting modules into separate microservices, are far more expensive to fix** — you're now dealing with [shared-database](0520-shared-database.md) coupling across network-separated services, [synchronous call chains](0522-synchronous-call-chains-death-star.md) that didn't exist as a concern when everything was in-process, and the general operational overhead of running, deploying, and debugging genuinely separate deployables, all while trying to fix what was, at its root, just a design mistake.
- **Spring Modulith provides explicit tooling to enforce and verify module boundaries *before* extraction** — it can detect (and fail a build on) improper cross-module dependencies, verify that modules don't accidentally share internal state, and even generate documentation of the module structure — turning "we think our modules are well-separated" into a testable, enforced, compiler/build-checked claim.
- **You reach for this staged path specifically when uncertain whether your proposed service boundaries are actually correct** — for a system where the domain boundaries are already extremely well-understood and stable (rare, but it happens), going straight to microservices might be reasonable; for most real systems, especially ones evolving from an existing monolith, validating boundaries as modules first, cheaply, is the safer default.

## 3. Core concept

Think of renovating a house by first testing a proposed wall placement with a cheap, movable partition — living with it for a while, seeing if the room divisions actually make sense for how the space is used, adjusting the partition's position freely as you learn — before committing to knocking down and rebuilding a real, permanent, load-bearing wall in that exact location. The movable partition (a well-defined internal module boundary) lets you validate the *idea* of where a boundary should go cheaply and reversibly; only once you're confident the partition's placement is actually right do you invest in the permanent, much costlier wall (an extracted, independently-deployed microservice) — and if the partition reveals the boundary was wrong, moving it costs an afternoon, not a full renovation.

Concretely, the staged path looks like:

1. **Start with (or arrive at) a monolith with poorly-defined internal boundaries** — classes and packages organized ad hoc, with unclear or leaky dependencies between what should eventually become separate concerns.
2. **Refactor into explicit, well-bounded modules within the same deployable** — using package structure (and, with Spring Modulith, `@ApplicationModule` annotations or convention-based module detection) to make each module's public API and internal implementation details explicit, verified by Spring Modulith's own test support (`ApplicationModules.verify()`) that no module improperly reaches into another's internals.
3. **Live with this modular monolith for a meaningful period**, observing whether the chosen boundaries actually hold up under real, evolving requirements — a boundary that turns out wrong is still just a code reorganization to fix, since everything remains in one process.
4. **Once a specific module's boundary has proven stable and its team is ready to deploy and scale it independently, extract that one module into its own microservice** — the module's already-explicit public API (enforced by Spring Modulith) becomes the seam along which extraction happens, ideally with the internal implementation details staying hidden exactly as they were inside the monolith.
5. **Repeat extraction for other modules over time, incrementally**, rather than attempting to extract everything into microservices simultaneously — each extraction is a smaller, more isolated risk than a single, all-at-once rewrite.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A staged migration: unstructured monolith, then a modular monolith with enforced module boundaries, then incremental extraction of proven modules into separate microservices">
  <rect x="20" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Unstructured monolith</text>
  <text x="110" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">unclear boundaries</text>

  <rect x="240" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Modular monolith</text>
  <text x="330" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">enforced boundaries, ONE process</text>

  <rect x="460" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="550" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Extracted microservices</text>
  <text x="550" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one module at a time</text>

  <line x1="200" y1="45" x2="240" y2="45" stroke="#8b949e" marker-end="url(#a19)"/>
  <line x1="420" y1="45" x2="460" y2="45" stroke="#8b949e" marker-end="url(#a19)"/>

  <text x="330" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a wrong boundary caught at the modular stage is a cheap refactor;</text>
  <text x="330" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the same mistake caught after extraction is a distributed-systems problem</text>
  <defs><marker id="a19" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

Validating boundaries as enforced modules first, before extraction, catches design mistakes at their cheapest possible point.

## 5. Runnable example

Scenario: an Orders/Inventory boundary being validated as a module before extraction. We start with an unstructured, leaky-boundary version, extend it to an explicit, enforced modular boundary, then show the extracted microservice using the exact same public interface the module already had.

### Level 1 — Basic

```java
// File: UnstructuredMonolith.java -- models the STARTING POINT: an
// unclear boundary, where "Orders" code reaches directly into
// "Inventory" internals, with no enforced separation.
import java.util.*;

public class UnstructuredMonolith {
    // Inventory's "internal" data, but nothing stops Orders code from touching it directly
    static Map<String, Integer> inventoryInternalStock = new HashMap<>(Map.of("widget", 10));

    static void placeOrder(String item, int qty) {
        // Orders code reaches DIRECTLY into Inventory's internal map -- no defined boundary at all
        int current = inventoryInternalStock.get(item);
        inventoryInternalStock.put(item, current - qty);
        System.out.println("Order placed, directly modified Inventory's internal stock map");
    }

    public static void main(String[] args) {
        placeOrder("widget", 3);
        System.out.println("Remaining stock: " + inventoryInternalStock);
        System.out.println("Problem: Orders code has NO boundary respecting Inventory as a separate concern -- this WILL be painful to extract later.");
    }
}
```

How to run: `java UnstructuredMonolith.java`

`placeOrder` reaches directly into `inventoryInternalStock` — there's no defined module boundary here at all, exactly the [shared-database](0520-shared-database.md)-style coupling that, if this code were extracted into two separate microservices as-is, would require a real, cross-network shared-data problem to untangle.

### Level 2 — Intermediate

```java
// File: ExplicitModuleBoundary.java -- models refactoring into an
// EXPLICIT, enforced module boundary -- Orders can ONLY reach Inventory
// through its declared public API, verified within a SINGLE process.
import java.util.*;

public class ExplicitModuleBoundary {
    // --- Inventory module: internal state is now PRIVATE, only a public API is exposed ---
    static class InventoryModule {
        private Map<String, Integer> stock = new HashMap<>(Map.of("widget", 10)); // now PRIVATE

        // the ONLY way any other module can interact with Inventory's data
        public boolean reserve(String item, int qty) {
            int current = stock.getOrDefault(item, 0);
            if (current < qty) return false;
            stock.put(item, current - qty);
            return true;
        }
    }

    // --- Orders module: depends ONLY on InventoryModule's public API ---
    static class OrdersModule {
        private InventoryModule inventory;
        OrdersModule(InventoryModule inventory) { this.inventory = inventory; }

        String placeOrder(String item, int qty) {
            boolean reserved = inventory.reserve(item, qty); // through the API, never direct field access
            return reserved ? "Order placed for " + qty + "x " + item : "Order REJECTED: insufficient stock";
        }
    }

    public static void main(String[] args) {
        InventoryModule inventory = new InventoryModule();
        OrdersModule orders = new OrdersModule(inventory);
        System.out.println(orders.placeOrder("widget", 3));
        System.out.println("Orders can ONLY reach Inventory through reserve() -- boundary is now EXPLICIT, still ONE process.");
    }
}
```

How to run: `java ExplicitModuleBoundary.java`

`InventoryModule.stock` is now `private` — `OrdersModule` has no way to touch it directly, only through the public `reserve(...)` method. This is precisely what Spring Modulith's `ApplicationModules.verify()` checks for automatically across an entire codebase (flagging any cross-module reach into non-public internals as a build-time failure), letting you validate this boundary is actually respected everywhere, not just in this one hand-checked example.

### Level 3 — Advanced

```java
// File: ExtractedMicroservice.java -- the EXTRACTION step: Inventory
// becomes its OWN microservice, exposing the SAME public interface
// (reserve) that was already proven correct as a module boundary --
// Orders now calls it over the network, via the SAME logical operation.
import java.util.*;
import java.util.concurrent.*;

public class ExtractedMicroservice {
    // Inventory, now a SEPARATE service -- but its PUBLIC operation is UNCHANGED from the module version
    static class InventoryService {
        private Map<String, Integer> stock = new HashMap<>(Map.of("widget", 10));

        // simulates a network call: same LOGICAL operation as InventoryModule.reserve(), now remote
        CompletableFuture<Boolean> reserveAsync(String item, int qty) {
            return CompletableFuture.supplyAsync(() -> {
                int current = stock.getOrDefault(item, 0);
                if (current < qty) return false;
                stock.put(item, current - qty);
                return true;
            });
        }
    }

    // Orders, now a SEPARATE service, calling Inventory over the network -- same LOGICAL flow as before
    static class OrdersService {
        private InventoryService inventoryClient; // now a REMOTE client, not a local module reference
        OrdersService(InventoryService inventoryClient) { this.inventoryClient = inventoryClient; }

        String placeOrder(String item, int qty) throws Exception {
            boolean reserved = inventoryClient.reserveAsync(item, qty).get(); // network call, same OPERATION as before
            return reserved ? "Order placed for " + qty + "x " + item : "Order REJECTED: insufficient stock";
        }
    }

    public static void main(String[] args) throws Exception {
        InventoryService inventory = new InventoryService();
        OrdersService orders = new OrdersService(inventory);
        System.out.println(orders.placeOrder("widget", 3));
        System.out.println("SAME logical operation as the module version -- extraction changed the TRANSPORT, not the BOUNDARY or the API shape.");
    }
}
```

How to run: `java ExtractedMicroservice.java`

Compare `OrdersService.placeOrder` directly against `OrdersModule.placeOrder` from Level 2 — the logical flow (reserve inventory, check the result, build a response) is identical; the only change is that `inventoryClient.reserveAsync(...)` now models a real network call (via `CompletableFuture`) instead of a direct in-process method call. Because the module boundary was already correct and already expressed as a narrow public API (`reserve`), extraction didn't require redesigning the interaction — it only required changing *how* that same interaction happens, exactly the payoff of validating the boundary as a module first.

## 6. Walkthrough

Trace the full migration arc across all three levels, focusing on what specifically changes (and, just as importantly, what does *not* change) at each stage:

1. **In the Level 1 unstructured version**, `placeOrder` directly manipulates `inventoryInternalStock` — there is no API, no boundary, and no way to even ask "is this boundary correct," since there's no boundary defined at all yet.
2. **Moving to Level 2**, the team makes `stock` private and introduces `reserve(item, qty)` as the sole entry point — this is a pure refactor, verifiable by the compiler (any remaining direct access to `stock` from outside `InventoryModule` simply won't compile) and, with real Spring Modulith tooling, verifiable automatically across an entire real codebase's module structure via a test that fails the build on any violation.
3. **The team lives with this modular structure for some period**, using it in production, observing whether `reserve(item, qty)` actually captures everything Orders ever needs from Inventory, or whether new requirements reveal the boundary needs adjusting (perhaps a second operation, `release(item, qty)`, turns out to be needed too) — any such adjustment, at this stage, is still just editing code within one deployable.
4. **Once the team is confident `reserve` is the right, stable boundary**, they extract Inventory into `InventoryService`, a genuinely separate deployable — and critically, `OrdersService.placeOrder`'s *logic* barely changes at all; only the mechanism of the call (`inventoryClient.reserveAsync(...).get()` instead of a direct method call) is different.
5. **Because the boundary was validated before extraction**, the team avoids the much costlier alternative: extracting a poorly-understood boundary directly into two microservices, discovering only afterward (through a painful, cross-network refactor) that the "right" interface was actually different from what got extracted.

## 7. Gotchas & takeaways

> **Gotcha:** treating the modular-monolith stage as a permanent destination rather than a deliberate intermediate step can be perfectly valid — not every module needs to eventually become a microservice, and a well-structured modular monolith that never gets further split can still be a perfectly good, simpler architecture; don't extract a module into a microservice just because the migration path exists as an option, without an actual reason (independent scaling, independent deployment cadence, a different team owning it) that justifies paying the real cost of distribution.

- Validating a proposed service boundary as an enforced module *within* a single deployable first is far cheaper than discovering the same boundary is wrong only after extracting it into a genuinely separate, network-connected microservice.
- Spring Modulith provides explicit, build-verifiable tooling (`ApplicationModules.verify()`, `@ApplicationModule`) to enforce and check module boundaries automatically, turning "we believe our modules are well-separated" into a testable, continuously-checked property of the codebase.
- Extract modules into microservices incrementally, one at a time, once each specific boundary has proven stable — not as a single, simultaneous, all-at-once rewrite of the entire system.
- Not every module needs to eventually become a microservice — a well-structured modular monolith is itself a legitimate, often simpler, architecture, and extraction should be justified by a real, specific need (independent scaling or deployment), not pursued simply because it's the next available step.
