---
card: system-design
gi: 64
slug: denormalization-for-read-performance
title: Denormalization for read performance
---

## 1. What it is

**Denormalization** is the deliberate act of duplicating data across tables — the opposite of normalization — in order to make reads faster, by removing the need for a query to join several tables together to answer a common question.

## 2. Why & when

Normalization protects update consistency, but every join a query performs costs time, especially at scale with millions of rows. Denormalization is applied deliberately, after understanding the normalized design, to speed up specific read patterns that are known to be frequent and performance-sensitive — for example, showing an order's total item count on a list page without joining and counting `order_items` every single time. Use it once you have measured that a specific join is a real bottleneck, not as a default starting design.

## 3. Core concept

**The trade being made:** denormalization copies a value (or a precomputed aggregate) into a table where it can be read directly, at the cost of that copy needing to be kept in sync whenever the original changes. It reintroduces the update-anomaly risk normalization removed — this cost must be actively managed, not ignored.

**A common pattern — a denormalized counter:** instead of counting `order_items` rows every time an order's item count is displayed, store `item_count` directly on the `orders` row, and update it (increment or decrement) every time an item is added or removed. Reads become a single-row lookup with no join and no count; writes must remember to keep the counter accurate.

**A common pattern — a denormalized copy of frequently-joined data:** instead of joining `orders` to `customers` on every query just to show the customer's name next to their order, store `customer_name` directly on the `orders` row at the time the order is placed. This trades a join for a copy that must be updated if the customer's name ever changes (or, often, is deliberately left as a historical snapshot of the name at order time, which is sometimes exactly what you want).

**Keeping denormalized data in sync:** every place that writes the original value must also update every denormalized copy, in the same transaction or process — this is the ongoing cost of the trade, and it is easy to forget one of the copies as a schema evolves.

## 4. Diagram

```
NORMALIZED (always joins, always accurate on every write):
  orders: | id | customer_id |        order_items: | order_id | product | qty |
          | 1  | 42          |                       | 1        | Pen     | 3   |
                                                       | 1        | Book    | 1   |
  "how many items in order 1?" -> JOIN + COUNT every time (slow at scale)

DENORMALIZED (fast read, extra write work):
  orders: | id | customer_id | item_count |
          | 1  | 42          | 4          |   <- precomputed, updated on every item add/remove
  "how many items in order 1?" -> single row read, no join, no count
```
*Caption: the denormalized `item_count` column answers the common question with one row read, at the cost of every write needing to keep it accurate.*

## 5. Runnable example

**Level 1 — Basic.** A normalized model where the item count is computed by scanning `order_items` every read.

**Level 2 — Denormalized counter.** The same data, but `itemCount` is stored directly on the order and kept in sync on every add/remove.

**Level 3 — The sync risk.** Deliberately forget to update the denormalized counter on one code path, showing exactly how it drifts out of sync.

```java
// Denormalization.java
import java.util.*;

public class Denormalization {

    record OrderItem(int orderId, String product) {}

    // Level 1: normalized - count computed fresh from order_items every time.
    static int normalizedItemCount(List<OrderItem> items, int orderId) {
        int count = 0;
        for (OrderItem item : items) if (item.orderId() == orderId) count++;
        return count; // correct, but scans every item row on every read
    }

    // Level 2 & 3: denormalized - item_count is a field kept in sync on writes.
    static class DenormalizedOrder {
        int id;
        int itemCount = 0;
        DenormalizedOrder(int id) { this.id = id; }
    }

    static void addItemCorrectly(DenormalizedOrder order, List<OrderItem> items, String product) {
        items.add(new OrderItem(order.id, product));
        order.itemCount++; // kept in sync, in the same operation
    }

    static void addItemForgettingSync(DenormalizedOrder order, List<OrderItem> items, String product) {
        items.add(new OrderItem(order.id, product));
        // BUG: forgot to update order.itemCount here
    }

    public static void main(String[] args) {
        List<OrderItem> items = new ArrayList<>();
        items.add(new OrderItem(1, "Pen"));
        items.add(new OrderItem(1, "Book"));

        System.out.println("normalized count (scans order_items): " + normalizedItemCount(items, 1));

        DenormalizedOrder order = new DenormalizedOrder(1);
        order.itemCount = normalizedItemCount(items, 1); // initialize the counter correctly

        addItemCorrectly(order, items, "Pencil");
        System.out.println("after correct add - denormalized count: " + order.itemCount
            + " | normalized recount (ground truth): " + normalizedItemCount(items, 1));

        addItemForgettingSync(order, items, "Eraser");
        System.out.println("after buggy add - denormalized count: " + order.itemCount
            + " | normalized recount (ground truth): " + normalizedItemCount(items, 1));
        System.out.println("  -> the denormalized counter has now DRIFTED out of sync");
    }
}
```

**How to run:** save as `Denormalization.java`, then run `java Denormalization.java`.

## 6. Walkthrough

1. `normalizedItemCount` always scans the full `items` list and counts matching rows — always correct, but the cost grows with the number of items in the system, not just the one order.
2. `order.itemCount` is initialized once from that same ground-truth count, giving `2`.
3. `addItemCorrectly` adds a new `OrderItem` and increments `order.itemCount` in the same call — both stay in agreement, confirmed by comparing the denormalized field to a fresh `normalizedItemCount` recount, which both show `3`.
4. `addItemForgettingSync` adds a new item to `items` but never updates `order.itemCount`, deliberately modeling a missed code path.
5. The final printout shows `order.itemCount` still at `3` while the ground-truth `normalizedItemCount` recount now reports `4` — the denormalized copy has drifted, exactly the failure mode denormalization risks if any write path forgets to keep it in sync.

## 7. Gotchas & takeaways

> Gotcha: as shown in Level 3, a denormalized value is only as correct as every single write path that is supposed to update it; a single forgotten update site is enough to silently desynchronize it, and nothing about the schema itself will warn you — this is the real, ongoing cost of the trade.

- Denormalize deliberately, for a specific, measured read bottleneck — not by default, and not everywhere.
- Every denormalized copy needs an explicit, disciplined update path (often inside the same database transaction) everywhere the original data changes.
- Related concepts: [Normalization (1NF–3NF, BCNF)](0063-normalization-1nf3nf-bcnf.md) (the baseline design this trades away from), [Covering indexes & index-only scans](0066-covering-indexes-index-only-scans.md) (another, index-based way to speed up reads without duplicating application-level data).
