---
card: microservices
gi: 65
slug: branch-by-abstraction
title: "Branch by abstraction"
---

## 1. What it is

Branch by abstraction is a technique for replacing a piece of code's implementation gradually, on the main branch, without a long-lived feature branch and without stopping releases. You introduce an abstraction (an interface) in front of the existing implementation, migrate every call site to depend on the abstraction instead of the concrete class, then build the new implementation behind that same interface, switch over (often with a runtime toggle), and finally delete the old implementation once the new one is trusted. It is the code-level sibling of the [strangler fig pattern](0064-strangler-fig-pattern.md), which does the equivalent thing at the level of routing whole requests.

## 2. Why & when

A long-lived feature branch that rips out and replaces a core piece of logic tends to rot: the main branch keeps moving, the feature branch drifts further from it, and the eventual merge becomes a high-risk, painful event. Branch by abstraction avoids this entirely by never branching in the version-control sense — every change lands on main, in small steps, each one shippable on its own. The abstraction layer is what makes this possible: once call sites depend on an interface rather than a concrete class, the concrete implementation behind it can be swapped, in production, behind a toggle, with the option to instantly revert if something goes wrong.

Use it when replacing a core implementation detail that many call sites depend on — a payment gateway integration, a persistence mechanism, or (in a microservices migration) the concrete class that today talks to the monolith's in-process code, and tomorrow needs to talk to a new microservice instead.

## 3. Core concept

The interface is introduced first, purely as a refactor with zero behavior change; the new implementation is built and wired in behind it second; only then does the switch (and eventual old-code deletion) happen — each step independently shippable.

```
Step 1: OrderRepository (interface)  <-- callers now depend on THIS
              ^
              | implements
     LegacyOrderRepository   (old, in-process)

Step 2: add a second implementation behind the SAME interface
     LegacyOrderRepository        RemoteOrderRepository (calls new microservice)
              ^                              ^
              +---- toggle picks one --------+

Step 3: toggle flipped to Remote, Legacy verified unused, Legacy deleted
```

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Callers depend on an OrderRepository interface; a toggle selects between the legacy implementation and a new remote implementation behind it">
  <rect x="230" y="15" width="180" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="39" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Callers (unchanged)</text>

  <rect x="230" y="80" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="103" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderRepository</text>
  <text x="320" y="118" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">interface (the abstraction)</text>

  <rect x="60" y="165" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="188" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">LegacyOrderRepository</text>
  <text x="160" y="203" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">old, in-process</text>

  <rect x="380" y="165" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="188" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">RemoteOrderRepository</text>
  <text x="480" y="203" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">new, calls microservice</text>

  <line x1="320" y1="55" x2="320" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="280" y1="125" x2="180" y2="165" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="360" y1="125" x2="460" y2="165" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="440" y="145" fill="#6db33f" font-size="7.5" font-family="sans-serif">toggle picks</text>
</svg>

Callers depend only on the interface; a toggle decides which implementation answers behind it.

## 5. Runnable example

Scenario: an `OrderRepository` used throughout an application, first as a single concrete class with no abstraction, then refactored behind an interface with a legacy implementation (zero behavior change), then extended with a second, "remote" implementation and a runtime toggle to switch between them safely.

### Level 1 — Basic

```java
// File: DirectDependency.java -- callers depend directly on a concrete
// class -- no abstraction, no way to swap implementations safely.
import java.util.*;

public class DirectDependency {
    static class LegacyOrderRepository {
        String findOrder(String id) { return "order[" + id + "] from LEGACY in-process store"; }
    }

    static class OrderController {
        LegacyOrderRepository repo = new LegacyOrderRepository(); // hard-wired concrete dependency
        void show(String id) { System.out.println(repo.findOrder(id)); }
    }

    public static void main(String[] args) {
        new OrderController().show("ORD-1");
    }
}
```

**How to run:** `javac DirectDependency.java && java DirectDependency` (JDK 17+).

Expected output:
```
order[ORD-1] from LEGACY in-process store
```

`OrderController` cannot be pointed at anything other than `LegacyOrderRepository` without editing its own source — there is no seam to branch behind.

### Level 2 — Intermediate

```java
// File: AbstractionIntroduced.java -- Step 1 of branch by abstraction:
// introduce the OrderRepository interface and make the controller depend
// on it instead. ZERO behavior change -- still backed by the same legacy code.
import java.util.*;

public class AbstractionIntroduced {
    interface OrderRepository {
        String findOrder(String id);
    }

    static class LegacyOrderRepository implements OrderRepository {
        public String findOrder(String id) { return "order[" + id + "] from LEGACY in-process store"; }
    }

    static class OrderController {
        OrderRepository repo; // depends on the ABSTRACTION now, not the concrete class
        OrderController(OrderRepository repo) { this.repo = repo; }
        void show(String id) { System.out.println(repo.findOrder(id)); }
    }

    public static void main(String[] args) {
        OrderController controller = new OrderController(new LegacyOrderRepository());
        controller.show("ORD-1");
    }
}
```

**How to run:** `javac AbstractionIntroduced.java && java AbstractionIntroduced` (JDK 17+).

Expected output:
```
order[ORD-1] from LEGACY in-process store
```

Identical output to Level 1 — this step is purely a refactor. But now `OrderController` only knows about the `OrderRepository` interface, which is the seam the new implementation will be built behind.

### Level 3 — Advanced

```java
// File: ToggleBetweenImplementations.java -- Step 2 & 3: add a NEW
// RemoteOrderRepository behind the same interface, and a runtime toggle
// that picks between old and new -- with instant revert if the new one misbehaves.
import java.util.*;

public class ToggleBetweenImplementations {
    interface OrderRepository {
        String findOrder(String id);
    }

    static class LegacyOrderRepository implements OrderRepository {
        public String findOrder(String id) { return "order[" + id + "] from LEGACY in-process store"; }
    }

    static class RemoteOrderRepository implements OrderRepository {
        public String findOrder(String id) {
            if (id.equals("ORD-2")) throw new RuntimeException("new OrderService unreachable");
            return "order[" + id + "] from NEW OrderService (remote call)";
        }
    }

    static class TogglingOrderRepository implements OrderRepository {
        LegacyOrderRepository legacy = new LegacyOrderRepository();
        RemoteOrderRepository remote = new RemoteOrderRepository();
        boolean useRemote; // the toggle -- can be flipped without a code change (e.g. a feature flag)

        TogglingOrderRepository(boolean useRemote) { this.useRemote = useRemote; }

        public String findOrder(String id) {
            if (!useRemote) return legacy.findOrder(id);
            try {
                return remote.findOrder(id);
            } catch (RuntimeException e) {
                System.out.println("  [toggle: remote failed (" + e.getMessage() + "), reverting to legacy]");
                return legacy.findOrder(id); // instant revert, no redeploy needed
            }
        }
    }

    static class OrderController {
        OrderRepository repo;
        OrderController(OrderRepository repo) { this.repo = repo; }
        void show(String id) { System.out.println(repo.findOrder(id)); }
    }

    public static void main(String[] args) {
        OrderController controller = new OrderController(new TogglingOrderRepository(true));
        controller.show("ORD-1"); // remote succeeds
        controller.show("ORD-2"); // remote fails, reverts to legacy
    }
}
```

**How to run:** `javac ToggleBetweenImplementations.java && java ToggleBetweenImplementations` (JDK 17+).

Expected output:
```
order[ORD-1] from NEW OrderService (remote call)
  [toggle: remote failed (new OrderService unreachable), reverting to legacy]
order[ORD-2] from LEGACY in-process store
```

`OrderController`'s source has not changed at all since Level 2 — it still just calls `repo.findOrder(id)` against the `OrderRepository` interface. All the migration risk is contained inside `TogglingOrderRepository`, which can flip `useRemote` back to `false` globally (a config change, not a code change) if the new service turns out not to be ready.

## 6. Walkthrough

1. **Level 1** — `OrderController` holds a field typed as the concrete `LegacyOrderRepository` and calls `findOrder` on it directly. There is no seam here: swapping in a different data source means editing `OrderController`'s own source code, which is exactly the risky, all-or-nothing kind of change branch by abstraction exists to avoid.
2. **Level 2 — introduce the abstraction** — `OrderRepository` is extracted as an interface, `LegacyOrderRepository` now `implements` it, and `OrderController`'s field type changes from the concrete class to the interface, with the concrete instance passed in through the constructor instead. Running `main` produces byte-for-byte the same output as Level 1 — this step is a pure refactor, safe to ship on main immediately, with no functional change visible to any caller.
3. **Level 3 — new implementation and a toggle** — `RemoteOrderRepository` is added, implementing the same `OrderRepository` interface but simulating a call to a brand-new microservice (and, realistically, sometimes failing — here, hard-coded to throw for `ORD-2`). `TogglingOrderRepository` wraps both implementations and a `useRemote` boolean; it also implements `OrderRepository`, so `OrderController` can hold a `TogglingOrderRepository` without any change to its own code at all.
4. **Tracing the two calls in `main`** — `controller.show("ORD-1")` calls `TogglingOrderRepository.findOrder("ORD-1")`. Since `useRemote` is `true`, it tries `remote.findOrder("ORD-1")`, which succeeds and returns the "NEW OrderService" string — printed directly. `controller.show("ORD-2")` follows the same path, but `remote.findOrder("ORD-2")` throws; the `catch` block prints the `[toggle: ...]` diagnostic line and then calls `legacy.findOrder("ORD-2")` instead, so the final printed line still comes from the legacy path — an automatic, per-call fallback with zero manual intervention.
5. **The migration endgame** — once `RemoteOrderRepository` has proven itself reliable in production (no more silent reverts observed), the next steps — outside what this code sample shows — are: flip `useRemote` to `true` permanently, delete the `catch` fallback and eventually `LegacyOrderRepository` itself, and finally delete `TogglingOrderRepository`, leaving `OrderController` wired directly to `RemoteOrderRepository` behind the same `OrderRepository` interface. Every one of those steps is independently small and shippable — no long-lived branch, no big-bang merge.

## 7. Gotchas & takeaways

> **Gotcha:** the abstraction interface must be introduced *before* any new implementation exists, and every call site must be migrated to depend on it. If even one call site keeps a direct reference to the concrete legacy class, that call site cannot be toggled or safely retired later — it becomes a straggler that blocks final cleanup indefinitely.

- Branch by abstraction avoids long-lived feature branches by making every step — introduce interface, add new implementation, toggle, delete old code — independently shippable on main.
- The toggle is what makes the risky step (switching to new code) reversible without a redeploy — a config flip, not a code change.
- It is the code-level counterpart to the [strangler fig pattern](0064-strangler-fig-pattern.md): strangler fig routes whole *requests* between old and new systems; branch by abstraction routes individual *implementation dependencies* the same way.
- Don't skip the final cleanup step — deleting the old implementation and the toggle itself once the new code is trusted. Abstractions left in place "just in case" forever become permanent complexity with no ongoing benefit.
- This technique composes naturally with [decomposing a monolith incrementally](0066-decomposing-a-monolith-incrementally.md), where the "new implementation" behind the abstraction is often a call to a freshly extracted microservice.
