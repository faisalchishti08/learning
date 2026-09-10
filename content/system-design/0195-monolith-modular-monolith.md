---
card: system-design
gi: 195
slug: monolith-modular-monolith
title: Monolith & modular monolith
---

## 1. What it is

A **monolith** is a system built and deployed as one single unit. Every feature — orders, payments, users — lives in one codebase, runs in one process, and ships in one deployment. A **modular monolith** is the same single-deployment unit, but the code inside it is split into clearly bounded modules with explicit interfaces, so each module could later become its own service without a full rewrite.

## 2. Why & when

A plain monolith is the fastest way to start a new product. One codebase means one build, one test suite, and no network calls between features, so early development is simple and fast. The problem shows up as the team and codebase grow: modules start calling each other's internals directly, and soon nobody can change one feature without breaking another.

A modular monolith fixes this without paying for [microservices](0196-microservices.md) too early. You get the deployment simplicity of a monolith, but the module boundaries stop the "big ball of mud" problem. Choose a plain monolith for a new, small product. Choose a modular monolith once more than one team touches the code. Choose microservices only when you have a real, measured reason — independent scaling, independent deployment, or team autonomy at real organizational scale.

## 3. Core concept

- **Deployment unit vs. code structure.** "Monolith" describes how you *deploy* the system (one unit). "Modular" describes how you *structure the code inside* that unit. These are independent choices — you can have a well-structured monolith or a tangled one.
- **Module boundary.** Each module (e.g. `orders`, `payments`, `users`) owns its own data and exposes a small public interface. Other modules may call that interface, but never reach into another module's internal classes or tables directly.
- **Enforcing the boundary.** Java package-private classes, or a build tool like Spring Modulith, stop code outside a module from importing its internals. This turns a social convention ("please don't do that") into a compiler error.
- **In-process calls, not network calls.** A modular monolith's modules call each other through plain Java method calls. There is no network hop, no serialization, and no partial-failure risk — the tradeoffs microservices must handle do not exist yet.
- **The extraction path.** Because each module already has a clean interface and owns its own data, pulling one module out into a standalone service later is a boundary change, not a redesign. This is the core payoff of doing the modular split early.

## 4. Diagram

```
 PLAIN MONOLITH                       MODULAR MONOLITH
 (one process, tangled)               (one process, clean modules)

 +-----------------------+            +-------------------------------+
 |  OrderService         |            |  module: orders                |
 |   -> reads UserRepo   |            |   OrderService, OrderRepo      |
 |   -> reads PaymentRepo|            |   (public: OrderApi)           |
 |  PaymentService       |            +-------------------------------+
 |   -> writes UserTable |                        | OrderApi calls only
 |  UserService          |                        v
 |   -> everyone reaches |            +-------------------------------+
 |      in directly      |            |  module: payments              |
 +-----------------------+            |   (public: PaymentApi)         |
        one deploy unit               +-------------------------------+
        no clear owner per table                  | PaymentApi calls only
                                                    v
                                       +-------------------------------+
                                       |  module: users                 |
                                       |   (public: UserApi)            |
                                       +-------------------------------+
                                                one deploy unit
                                       each module owns its own tables
```
*Caption: both diagrams ship as one process. The difference is whether calls cross module boundaries through a public interface, or reach into another module's internals directly.*

## 5. Runnable example

**Level 1 — Basic.** A plain monolith where `OrderService` reaches directly into `PaymentRepository`'s internals — no boundary at all.

**Level 2 — Modular.** The same features, but each module exposes only a small public interface (`OrdersApi`, `PaymentsApi`), and internal classes are package-private in spirit (marked here with a comment, since a single file cannot show real Java packages).

**Level 3 — Enforced boundary + extraction readiness.** Add a simple runtime check that rejects any call that tries to bypass a module's public API, showing why this discipline makes pulling a module into its own service later a boundary change, not a rewrite.

```java
// ModularMonolithDemo.java
import java.util.*;

public class ModularMonolithDemo {

    // ---------- Level 1: plain monolith, no boundary ----------
    static class TangledOrderService {
        // Reaches directly into payments' internal data structure - no interface.
        Map<String, Double> paymentBalances;
        TangledOrderService(Map<String, Double> paymentBalances) {
            this.paymentBalances = paymentBalances;
        }
        void placeOrder(String userId, double amount) {
            // Any module can read or mutate payments' internal map directly.
            paymentBalances.merge(userId, -amount, Double::sum);
            System.out.println("  [tangled] order placed, balance mutated directly: " + paymentBalances.get(userId));
        }
    }

    // ---------- Level 2: modular monolith, public interfaces only ----------
    // module: payments (internals below are "package-private" in spirit)
    interface PaymentsApi {
        boolean charge(String userId, double amount);
        double balanceOf(String userId);
    }

    static class PaymentsModule implements PaymentsApi {
        private final Map<String, Double> balances = new HashMap<>(); // internal, not exposed

        void seed(String userId, double amount) { balances.put(userId, amount); }

        public boolean charge(String userId, double amount) {
            double current = balances.getOrDefault(userId, 0.0);
            if (current < amount) return false;
            balances.put(userId, current - amount);
            return true;
        }
        public double balanceOf(String userId) { return balances.getOrDefault(userId, 0.0); }
    }

    // module: orders - only calls PaymentsApi, never touches PaymentsModule internals
    static class OrdersModule {
        private final PaymentsApi payments;
        OrdersModule(PaymentsApi payments) { this.payments = payments; }

        boolean placeOrder(String userId, double amount) {
            boolean ok = payments.charge(userId, amount);
            System.out.println("  [modular] order " + (ok ? "placed" : "rejected") +
                ", remaining balance: " + payments.balanceOf(userId));
            return ok;
        }
    }

    // ---------- Level 3: enforce the boundary at runtime ----------
    static class BoundaryGuard {
        // Simulates what a tool like Spring Modulith checks at build time:
        // reject any call whose "module tag" does not match an allowed public API.
        static void checkCall(String callingModule, String targetModule, boolean viaPublicApi) {
            if (!viaPublicApi) {
                throw new IllegalStateException(
                    callingModule + " tried to reach into " + targetModule + "'s internals directly");
            }
            System.out.println("  [guard] " + callingModule + " -> " + targetModule + " via public API: OK");
        }
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - plain monolith (no boundary):");
        TangledOrderService tangled = new TangledOrderService(new HashMap<>(Map.of("alice", 100.0)));
        tangled.placeOrder("alice", 30.0);

        System.out.println("\nLevel 2 - modular monolith (public interface only):");
        PaymentsModule payments = new PaymentsModule();
        payments.seed("bob", 50.0);
        OrdersModule orders = new OrdersModule(payments);
        orders.placeOrder("bob", 20.0);
        orders.placeOrder("bob", 40.0); // insufficient balance now

        System.out.println("\nLevel 3 - enforced boundary:");
        BoundaryGuard.checkCall("orders", "payments", true);
        try {
            BoundaryGuard.checkCall("orders", "payments", false);
        } catch (IllegalStateException e) {
            System.out.println("  [guard] blocked: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ModularMonolithDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1 runs first.** `TangledOrderService` holds a direct reference to the payments module's internal `Map<String, Double>`. It mutates that map itself with `merge(...)`. Nothing stops any other module from doing the same thing to the same map.
2. **Level 2 replaces the shared map with a module.** `PaymentsModule` keeps `balances` as a private field and exposes only `charge` and `balanceOf` through the `PaymentsApi` interface. `OrdersModule` holds a reference to `PaymentsApi`, not to `PaymentsModule` — it cannot see the `balances` field at all, only the two methods.
3. **`orders.placeOrder("bob", 20.0)` runs first** and succeeds: bob's balance is 50, the charge of 20 leaves 30. **`orders.placeOrder("bob", 40.0)` runs next** and fails: 30 is less than 40, so `charge` returns `false` and the order is rejected. Orders never touched the balance map directly — it only ever called `charge`.
4. **Level 3 simulates the build-time check** that a real tool like Spring Modulith performs. `BoundaryGuard.checkCall("orders", "payments", true)` passes, because the call went through the public API. The second call passes `viaPublicApi = false` and throws, modeling what happens when a developer accidentally imports an internal class from another module — the build fails before the bad code ever ships.
5. Because orders never depended on anything inside `PaymentsModule` except `PaymentsApi`, you could delete `PaymentsModule` entirely and replace it with a network client that calls a separate payments *service*, implementing the same `PaymentsApi` interface. `OrdersModule`'s code would not change at all.

## 7. Gotchas & takeaways

> **Gotcha:** splitting into modules with no enforcement is not a modular monolith — it is a monolith with a convention nobody follows. Without a build-time check (a tool, or at minimum strict package-private visibility), module boundaries erode within a few sprints as deadlines push developers to "just call it directly this once."

- Start every new product as a monolith. Add module boundaries as soon as more than one team or clear feature domain exists.
- A modular monolith is not a stepping stone you are forced to use — plenty of systems run this way in production forever, because the team never needed independent deployment.
- Only extract a module into a real microservice when you have a concrete reason (independent scaling, independent release cadence, a separate team owning it) — not because "microservices are the modern way."
- The clean-boundary discipline that makes extraction cheap later is exactly what most teams skip when they are in a hurry — so enforce it early, while it is cheap.
