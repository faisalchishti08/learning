---
card: system-design
gi: 89
slug: functional-partitioning-by-service
title: Functional partitioning by service
---

## 1. What it is

**Functional partitioning** splits data by business function instead of by row or column: each service in the system owns and stores only the data its function needs, in its own database. The `orders` service has its own database; the `inventory` service has a separate one; the `users` service has another. No partition key is shared across a single table — the split happens at the service boundary.

## 2. Why & when

As a system grows into multiple services, each with a distinct responsibility, sharing one database between them creates hidden coupling: a schema change for one service can break another, and one service's load can slow down a completely unrelated one. Functional partitioning removes this coupling by giving each service exclusive ownership of its own data store. Use it when you are already splitting a system into services with clear responsibilities (as in a microservices architecture) and want each team to change and scale its own data independently, without coordinating schema changes with every other team.

## 3. Core concept

- **One database per service (or per bounded context):** the `orders` service owns the `orders` and `order_items` tables; nothing else reads or writes them directly.
- **No cross-service joins:** if the `orders` service needs a customer's name, it asks the `users` service through an API call or an event, it does not query the `users` database directly.
- **Independent scaling:** the `orders` database can be scaled, tuned, or even swapped for a different database technology, without touching the `users` database.
- **Data duplication is expected:** the `orders` service may keep a small, denormalized copy of the customer's name and shipping address at the time of order, rather than looking it up live every time.

**How this differs from horizontal/vertical partitioning:** horizontal and vertical partitioning both split *one* table's data across storage for a *single* concern. Functional partitioning splits an entire *system* along its functional boundaries — each partition is a full, independent database serving one service, not a slice of one shared table.

## 4. Diagram

```
                     +----------------+
                     |   API Gateway  |
                     +----------------+
                     /        |        \
                    v         v         v
          +---------+  +-----------+  +-----------+
          |  Orders |  |  Users    |  |  Inventory|
          | Service |  |  Service  |  |  Service  |
          +---------+  +-----------+  +-----------+
               |             |              |
               v             v              v
          +---------+  +-----------+  +-----------+
          | orders_db|  | users_db  |  | inventory_db|
          +---------+  +-----------+  +-----------+

  Orders service needs a customer name -> calls Users service's API,
  never queries users_db directly.
```
*Caption: each service functionally owns one database; cross-service data flows through APIs, never through shared tables.*

## 5. Runnable example

**Level 1 — Basic.** Model two services, each with its own in-memory "database" (a map), with no shared table.

**Level 2 — Cross-service call.** The orders service needs customer data, so it calls the users service's API rather than reading its map directly.

**Level 3 — Denormalized copy.** The orders service stores a snapshot of the customer's name at order time, so later reads do not need a cross-service call at all.

```java
// FunctionalPartitioning.java
import java.util.*;

public class FunctionalPartitioning {

    // Users service - owns its own store, exposes only a public method (its "API").
    static class UsersService {
        private final Map<String, String> usersDb = new HashMap<>(); // userId -> name

        void register(String userId, String name) { usersDb.put(userId, name); }

        String getUserName(String userId) { // the only way another service can reach this data
            return usersDb.get(userId);
        }
    }

    // Orders service - owns its own store, never touches usersDb directly.
    static class OrdersService {
        record Order(String orderId, String userId, String customerNameSnapshot) {}
        private final Map<String, Order> ordersDb = new HashMap<>();
        private final UsersService users; // dependency reached only through its API

        OrdersService(UsersService users) { this.users = users; }

        void placeOrder(String orderId, String userId) {
            String name = users.getUserName(userId); // cross-service call, not a direct DB read
            ordersDb.put(orderId, new Order(orderId, userId, name)); // denormalized snapshot stored
        }

        Order getOrder(String orderId) { return ordersDb.get(orderId); }
    }

    public static void main(String[] args) {
        UsersService users = new UsersService();
        users.register("u1", "Asha Rao");

        OrdersService orders = new OrdersService(users);
        orders.placeOrder("o1", "u1");

        System.out.println("orders_db entry: " + orders.getOrder("o1"));

        // Level 3 payoff: even if the user's name changes later, this order keeps its snapshot.
        users.register("u1", "Asha Rao-Mehta"); // name updated in users_db only
        System.out.println("users_db now has: " + users.getUserName("u1"));
        System.out.println("orders_db snapshot unchanged: " + orders.getOrder("o1").customerNameSnapshot());
    }
}
```

**How to run:** save as `FunctionalPartitioning.java`, then run `java FunctionalPartitioning.java`.

## 6. Walkthrough

1. `UsersService` and `OrdersService` each hold their own private map — `usersDb` and `ordersDb` — modeling two separate databases owned by two separate services.
2. `orders.placeOrder("o1", "u1")` needs the customer's name, so it calls `users.getUserName("u1")`, the only public entry point into the users service's data. It never reads `usersDb` directly.
3. The order is stored in `ordersDb` with a `customerNameSnapshot` field, a denormalized copy of the name at order time.
4. `users.register("u1", "Asha Rao-Mehta")` updates the name inside `usersDb` only. `ordersDb` is completely unaffected because it holds its own independent copy.
5. The final print shows `users_db` with the new name but `orders_db`'s order still showing the old snapshot — proof that the two stores evolve independently once the data crosses the functional boundary.

## 7. Gotchas & takeaways

> Gotcha: functional partitioning trades consistency for independence. Once a service snapshots or duplicates another service's data, that copy can drift out of date (as the order's stale customer name shows). Decide up front which fields must always be fresh (looked up live) versus which are acceptable as a point-in-time snapshot.

- Functional partitioning splits a whole system by service responsibility, giving each service its own database — a different axis from the row/column splits of horizontal and vertical partitioning.
- Cross-service data access goes through an API or event, never a direct cross-database query; this is what makes services independently deployable and scalable.
- Expect and design for some data duplication; it is the price of removing cross-service coupling.
- Related concepts: [Horizontal vs vertical partitioning](0088-horizontal-vs-vertical-partitioning.md) (splitting within one table, a different axis), [Denormalization & data duplication](0081-denormalization-data-duplication.md) (the technique used to snapshot data across the boundary).
