---
card: microservices
gi: 70
slug: spring-modulith-for-modular-monoliths-as-a-stepping-stone
title: "Spring Modulith for modular monoliths as a stepping stone"
---

## 1. What it is

Spring Modulith is a Spring project that helps you build a **modular monolith**: a single deployable application, organized into explicitly-bounded modules (typically one top-level package per module), with tooling to verify at build time that modules only talk to each other through their intended, published APIs rather than reaching into each other's internals. It gives a team the structural discipline of microservices — clear module boundaries, controlled dependencies — while keeping the operational simplicity of a single deployable unit, and it is explicitly designed to make a later split into real microservices, if one is ever needed, far less disruptive.

## 2. Why & when

Jumping straight to microservices before a team has clarity on where the real bounded contexts are tends to produce boundaries drawn in the wrong place — and once those boundaries are separate deployables with separate databases, moving the line is expensive. A modular monolith built with Spring Modulith gets much of the design benefit without that cost: modules are enforced at build time (a build fails if `Orders` reaches directly into `Shipping`'s internal package), but moving a class between modules, or even merging two modules that turned out to be one concept, is still a same-process refactor, not a distributed-systems migration.

Reach for this approach when you're unsure microservices are justified yet, or explicitly want to validate your bounded contexts under real production load before paying the operational cost of a distributed system. It pairs naturally with everything else in this section — [strategic vs tactical DDD](0062-strategic-vs-tactical-ddd.md) for boundary discovery, and, later, the [strangler fig pattern](0064-strangler-fig-pattern.md) if and when a module genuinely needs to become its own service.

## 3. Core concept

Each top-level package is a module; a class becomes part of that module's public API only if it sits directly in the top-level package (or is explicitly marked), while classes in a nested `internal` sub-package are invisible to every other module — enforced automatically, not just by convention.

```
com.example.shop
├── orders
│   ├── OrderService.java      <- PUBLIC API of the orders module
│   └── internal
│       └── OrderRepository.java   <- INTERNAL, invisible to other modules
├── shipping
│   ├── ShippingService.java
│   └── internal
│       └── ShipmentRepository.java
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two modules inside one monolith, each with a public API class and an internal package; the Shipping module is allowed to call the Orders module's public API but not reach into its internal package">
  <rect x="20" y="20" width="280" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">orders module</text>
  <rect x="45" y="60" width="230" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService (public)</text>
  <rect x="45" y="115" width="230" height="60" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="160" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">internal/</text>
  <text x="160" y="155" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">OrderRepository (hidden)</text>

  <rect x="340" y="20" width="280" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">shipping module</text>
  <rect x="365" y="60" width="230" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ShippingService (public)</text>

  <line x1="365" y1="77" x2="275" y2="77" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="70" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">allowed</text>
  <line x1="365" y1="140" x2="275" y2="140" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="320" y="133" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">BLOCKED at build time</text>
</svg>

Public API classes are the only legal cross-module entry point; internal packages are enforced boundaries, not just naming conventions.

## 5. Runnable example

Scenario: model Spring Modulith's core rule — public module API vs. hidden internal package — with plain Java, first with no enforcement at all (any class can reach anywhere), then with a simple runtime check simulating module-boundary verification, then extended to also verify no cyclic module dependencies exist, matching what `ApplicationModules.verify()` checks for in a real Spring Modulith project.

### Level 1 — Basic

```java
// File: NoModuleBoundaries.java -- ordinary Java packages have NO
// enforcement: any class can reach into any other class, public or not.
import java.util.*;

public class NoModuleBoundaries {
    static class OrderRepository { // meant to be "internal" -- but nothing stops external access
        Map<String, String> data = new HashMap<>();
        void save(String id, String status) { data.put(id, status); }
    }

    static class ShippingService {
        OrderRepository ordersInternalReachIn = new OrderRepository(); // reaching directly into another module's internals
        void checkOrder(String id) {
            System.out.println("Shipping read order status directly: " + ordersInternalReachIn.data.get(id));
        }
    }

    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.save("ORD-1", "PLACED");
        new ShippingService().checkOrder("ORD-1");
    }
}
```

**How to run:** `javac NoModuleBoundaries.java && java NoModuleBoundaries` (JDK 17+).

Expected output:
```
Shipping read order status directly: null
```

Nothing stops `ShippingService` from reaching directly into `OrderRepository`, an implementation detail of the Orders module — and worse, `ShippingService` even instantiated its own, disconnected `OrderRepository`, so it prints `null` instead of `PLACED`. This class of bug is exactly what module boundaries are meant to make structurally impossible.

### Level 2 — Intermediate

```java
// File: SimulatedModuleVerification.java -- simulate Spring Modulith's
// build-time check: declare which classes belong to which module and
// whether they are "public" or "internal," then verify no module
// reaches into another module's internal classes.
import java.util.*;

public class SimulatedModuleVerification {
    enum Visibility { PUBLIC, INTERNAL }
    record ModuleClass(String module, String className, Visibility visibility) {}
    record Dependency(String fromClass, String toClass) {}

    static List<String> verify(List<ModuleClass> classes, List<Dependency> dependencies) {
        Map<String, ModuleClass> byName = new HashMap<>();
        for (ModuleClass c : classes) byName.put(c.className(), c);

        List<String> violations = new ArrayList<>();
        for (Dependency d : dependencies) {
            ModuleClass from = byName.get(d.fromClass());
            ModuleClass to = byName.get(d.toClass());
            boolean crossModule = !from.module().equals(to.module());
            if (crossModule && to.visibility() == Visibility.INTERNAL) {
                violations.add(from.className() + " (module " + from.module() + ") illegally depends on "
                        + to.className() + " (INTERNAL to module " + to.module() + ")");
            }
        }
        return violations;
    }

    public static void main(String[] args) {
        List<ModuleClass> classes = List.of(
            new ModuleClass("orders", "OrderService", Visibility.PUBLIC),
            new ModuleClass("orders", "OrderRepository", Visibility.INTERNAL),
            new ModuleClass("shipping", "ShippingService", Visibility.PUBLIC)
        );
        List<Dependency> deps = List.of(
            new Dependency("ShippingService", "OrderRepository") // reaching into orders' internals
        );

        List<String> violations = verify(classes, deps);
        if (violations.isEmpty()) {
            System.out.println("Module verification PASSED");
        } else {
            violations.forEach(v -> System.out.println("Module verification FAILED: " + v));
        }
    }
}
```

**How to run:** `javac SimulatedModuleVerification.java && java SimulatedModuleVerification` (JDK 17+).

Expected output:
```
Module verification FAILED: ShippingService (module shipping) illegally depends on OrderRepository (INTERNAL to module orders)
```

This mirrors what running `ApplicationModules.of(MyApplication.class).verify()` does in a real Spring Modulith project: it fails the build the moment a module reaches into another module's internal package, instead of letting the mistake from Level 1 ship silently.

### Level 3 — Advanced

```java
// File: FullVerificationWithCycles.java -- extend verification to ALSO
// detect cyclic module dependencies (Orders depends on Shipping AND
// Shipping depends on Orders), which Spring Modulith flags as a design
// smell -- modules should form a directed acyclic graph, not a cycle.
import java.util.*;

public class FullVerificationWithCycles {
    enum Visibility { PUBLIC, INTERNAL }
    record ModuleClass(String module, String className, Visibility visibility) {}
    record Dependency(String fromClass, String toClass) {}

    static List<String> verifyVisibility(List<ModuleClass> classes, List<Dependency> dependencies) {
        Map<String, ModuleClass> byName = new HashMap<>();
        for (ModuleClass c : classes) byName.put(c.className(), c);
        List<String> violations = new ArrayList<>();
        for (Dependency d : dependencies) {
            ModuleClass from = byName.get(d.fromClass());
            ModuleClass to = byName.get(d.toClass());
            if (!from.module().equals(to.module()) && to.visibility() == Visibility.INTERNAL) {
                violations.add(from.className() + " illegally depends on internal " + to.className());
            }
        }
        return violations;
    }

    static List<String> verifyNoCycles(List<ModuleClass> classes, List<Dependency> dependencies) {
        Map<String, ModuleClass> byName = new HashMap<>();
        for (ModuleClass c : classes) byName.put(c.className(), c);
        Map<String, Set<String>> moduleGraph = new HashMap<>();
        for (Dependency d : dependencies) {
            String from = byName.get(d.fromClass()).module();
            String to = byName.get(d.toClass()).module();
            if (!from.equals(to)) moduleGraph.computeIfAbsent(from, k -> new HashSet<>()).add(to);
        }
        List<String> issues = new ArrayList<>();
        for (String a : moduleGraph.keySet()) {
            for (String b : moduleGraph.getOrDefault(a, Set.of())) {
                if (a.compareTo(b) < 0 && moduleGraph.getOrDefault(b, Set.of()).contains(a)) {
                    issues.add("cyclic module dependency: " + a + " <-> " + b); // reported once per pair
                }
            }
        }
        return issues;
    }

    public static void main(String[] args) {
        List<ModuleClass> classes = List.of(
            new ModuleClass("orders", "OrderService", Visibility.PUBLIC),
            new ModuleClass("shipping", "ShippingService", Visibility.PUBLIC)
        );
        List<Dependency> deps = List.of(
            new Dependency("OrderService", "ShippingService"),   // orders -> shipping
            new Dependency("ShippingService", "OrderService")    // shipping -> orders (CYCLE!)
        );

        List<String> visibilityIssues = verifyVisibility(classes, deps);
        List<String> cycleIssues = verifyNoCycles(classes, deps);

        System.out.println("Visibility violations: " + visibilityIssues.size());
        cycleIssues.forEach(i -> System.out.println("FAILED: " + i));
        if (visibilityIssues.isEmpty() && cycleIssues.isEmpty()) System.out.println("Module verification PASSED");
    }
}
```

**How to run:** `javac FullVerificationWithCycles.java && java FullVerificationWithCycles` (JDK 17+).

Expected output:
```
Visibility violations: 0
FAILED: cyclic module dependency: orders <-> shipping
```

## 6. Walkthrough

1. **Level 1** — `ShippingService` holds its own field of type `OrderRepository`, a class meant to be an internal implementation detail of the Orders module. Nothing in plain Java stops this. `main` saves an order via one `OrderRepository` instance, then calls `checkOrder`, which reads from a *different*, disconnected `OrderRepository` instance that `ShippingService` created itself — printing `null`. This demonstrates two problems at once: the boundary violation (reaching into another module's internals) and a realistic consequence of doing so (silently wrong data, because nothing coordinated the two instances).
2. **Level 2 — simulated verification** — `ModuleClass` records which module a class belongs to and whether it is `PUBLIC` or `INTERNAL`; `Dependency` records one class using another. `verify` walks every dependency and flags any case where the target class is `INTERNAL` and belongs to a *different* module than the caller. Running `main` with `ShippingService -> OrderRepository` (cross-module, and `OrderRepository` is `INTERNAL`) produces exactly one violation, printed as a `FAILED` line — the same mistake from Level 1, now caught mechanically instead of shipping silently.
3. **Level 3 — adding cycle detection** — `verifyNoCycles` builds a module-level graph (collapsing individual classes into their owning module) and checks, for every pair of modules with an edge in one direction, whether an edge exists in the *reverse* direction too. `main` sets up `OrderService -> ShippingService` and `ShippingService -> OrderService` — both classes are `PUBLIC`, so `verifyVisibility` reports zero violations, but `verifyNoCycles` correctly still flags the pair as a cyclic dependency.
4. **Why cycles matter separately from visibility** — a cycle between two modules, even one built entirely from legitimate public-API calls, is still a design smell: it means the two modules cannot be reasoned about, tested, or (eventually) extracted independently, because each depends on the other. This is precisely the kind of issue that's cheap to fix inside a modular monolith (rework which module owns which responsibility) and expensive to fix once the two modules are already separate, independently deployed microservices — which is the entire argument for using Spring Modulith as a stepping stone.
5. **The build-time guarantee this models** — in a real Spring Boot application using the actual Spring Modulith library, this same kind of check runs via `ApplicationModules.of(Application.class).verify()`, typically wired into a test that runs on every build — so a violation like either one shown here fails CI immediately, at the moment the offending code is written, rather than being discovered much later during a painful extraction attempt.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Modulith's boundary enforcement only helps if the module structure genuinely reflects real bounded contexts — a modular monolith with the wrong boundaries just makes an architectural mistake mechanically enforced rather than solving it. Do the [strategic DDD](0062-strategic-vs-tactical-ddd.md) work first; let Modulith enforce boundaries you've actually validated.

- A module's public API is whatever sits directly in its top-level package; anything under an `internal` sub-package is invisible to every other module, and this is enforced at build time, not just by convention or code review.
- Boundary violations (reaching into another module's internals) and cyclic module dependencies are two distinct kinds of problems, and both are worth checking — a design can have clean visibility and still have unhealthy cycles.
- The whole point of this approach is that fixing a boundary mistake inside a modular monolith is a same-process refactor; fixing the same mistake after a microservices split means a much more expensive distributed-systems change.
- See also [Spring Modulith application modules & verification](0071-spring-modulith-application-modules-verification.md) for how the real `@ApplicationModule` annotation and `ApplicationModules.verify()` API work, and [Spring Modulith domain events between modules](0072-spring-modulith-domain-events-between-modules.md) for how modules communicate without direct coupling.
- A modular monolith is explicitly a stepping stone, not necessarily a permanent end state — some systems stay modular monoliths forever, quite reasonably, if the operational cost of microservices never becomes justified.
