---
card: microservices
gi: 46
slug: avoiding-chatty-services-too-fine-grained
title: Avoiding chatty services (too fine-grained)
---

## 1. What it is

A **chatty service** relationship is a specific symptom of over-fine [service granularity](0019-service-granularity-nano-micro-macro-mini-services.md): completing one logical operation requires many small, back-and-forth network calls between two or more services, where each individual call is itself too fine-grained to be worth its own network round trip. The telltale sign is an "N+1"-style pattern — fetching a list from Service A, then calling Service B once *per item* in that list, turning what should be one or two network hops into dozens.

## 2. Why & when

Each network call carries real, fixed overhead — connection setup, serialization, latency — that doesn't shrink just because the call itself is doing very little work. A service boundary drawn too finely (say, splitting "get order" and "get order's line items" into two separate services when they're always needed together) forces every consumer to pay that fixed overhead repeatedly for what's conceptually one piece of work. This is the same [fallacy](0025-fallacies-of-distributed-computing-network-reliable-latency.md) — assuming latency is negligible — playing out specifically at the boundary between two services rather than within one call.

Recognize chattiness by counting network calls per logical operation, the same way [right-sizing](0045-right-sizing-services-granularity-decisions.md) recommends: if completing one user-facing action requires calling another service more than a small handful of times, that's a concrete, measurable signal worth investigating — either by merging the chatty services, or by redesigning the API to return richer, batched responses instead of many small ones.

## 3. Core concept

Two API shapes for the same underlying need, with very different call counts:

- **Chatty:** `getOrder(id)` returns just an order header; each of its N line items requires a separate `getLineItem(lineItemId)` call — N+1 total calls for one logical "get full order" operation.
- **Batched:** `getOrderWithLineItems(id)` returns the order and all its line items in one response — 1 call for the same logical operation.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chatty pattern makes one call to get an order, then N more calls, one per line item; a batched pattern gets everything in one call">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Chatty (N+1)</text>
  <rect x="30" y="35" width="220" height="35" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">1. getOrder(id) -&gt; header only</text>
  <rect x="30" y="80" width="220" height="35" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="140" y="102" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">2..N+1. getLineItem() x N calls</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Batched (1 call)</text>
  <rect x="400" y="50" width="220" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">getOrderWithLineItems(id)</text>
</svg>

N+1 small calls versus one call returning everything needed for the operation.

## 5. Runnable example

Scenario: fetching a full order with its line items, first via a chatty N+1 pattern, then measured to reveal the true cost, then refactored to a single batched call.

### Level 1 — Basic

```java
// File: ChattyPattern.java -- ONE call per line item, an N+1 pattern
import java.util.*;

public class ChattyPattern {
    static Map<String, List<String>> orderLineItemIds = Map.of("ord-1", List.of("li-1", "li-2", "li-3"));
    static int networkCallCount = 0;

    static List<String> getOrderLineItemIds(String orderId) { networkCallCount++; return orderLineItemIds.get(orderId); }
    static String getLineItem(String lineItemId) { networkCallCount++; return lineItemId + "-detail"; }

    static List<String> getFullOrder(String orderId) {
        List<String> lineItemIds = getOrderLineItemIds(orderId); // call #1
        List<String> details = new ArrayList<>();
        for (String id : lineItemIds) details.add(getLineItem(id)); // one call PER line item
        return details;
    }

    public static void main(String[] args) {
        List<String> order = getFullOrder("ord-1");
        System.out.println("order details: " + order);
        System.out.println("total network calls: " + networkCallCount);
    }
}
```

**How to run:** `javac ChattyPattern.java && java ChattyPattern` (JDK 17+).

Expected output:
```
order details: [li-1-detail, li-2-detail, li-3-detail]
total network calls: 4
```

Getting one order with 3 line items took 4 network calls (1 for the ID list, 3 more for each item individually) — for an order with 100 line items, this pattern would need 101 calls for what's conceptually one operation.

### Level 2 — Intermediate

```java
// File: MeasureAtScale.java -- show HOW BADLY the chatty pattern scales
// as the number of line items grows.
import java.util.*;

public class MeasureAtScale {
    static int networkCallCount = 0;

    static List<String> generateLineItemIds(int count) {
        List<String> ids = new ArrayList<>();
        for (int i = 0; i < count; i++) ids.add("li-" + i);
        return ids;
    }

    static List<String> getOrderLineItemIds(int count) { networkCallCount++; return generateLineItemIds(count); }
    static String getLineItem(String id) { networkCallCount++; return id + "-detail"; }

    static int callsNeededForOrder(int lineItemCount) {
        networkCallCount = 0;
        List<String> lineItemIds = getOrderLineItemIds(lineItemCount);
        for (String id : lineItemIds) getLineItem(id);
        return networkCallCount;
    }

    public static void main(String[] args) {
        for (int lineItems : new int[]{3, 10, 50, 100}) {
            System.out.println(lineItems + " line items -> " + callsNeededForOrder(lineItems) + " network calls");
        }
    }
}
```

**How to run:** `javac MeasureAtScale.java && java MeasureAtScale` (JDK 17+).

Expected output:
```
3 line items -> 4 network calls
10 line items -> 11 network calls
50 line items -> 51 network calls
100 line items -> 101 network calls
```

The N+1 pattern's cost grows linearly and directly with order size — a large order (100 items) needs over a hundred network round trips just to be read, a genuinely severe, measurable cost that scales with data size rather than staying constant.

### Level 3 — Advanced

```java
// File: BatchedPattern.java -- refactor to ONE call returning everything,
// regardless of how many line items the order has.
import java.util.*;

public class BatchedPattern {
    static Map<String, List<String>> orderLineItems = Map.of(
        "ord-1", List.of("li-1-detail", "li-2-detail", "li-3-detail")
    );
    static int networkCallCount = 0;

    // ONE method, ONE call, returns EVERYTHING needed for the logical operation
    static List<String> getOrderWithLineItems(String orderId) {
        networkCallCount++;
        return orderLineItems.get(orderId);
    }

    static int callsNeededForOrder(String orderId) {
        networkCallCount = 0;
        getOrderWithLineItems(orderId);
        return networkCallCount;
    }

    public static void main(String[] args) {
        List<String> order = getOrderWithLineItems("ord-1");
        System.out.println("order details: " + order);
        System.out.println("total network calls: " + callsNeededForOrder("ord-1"));
        System.out.println("this stays at 1 call regardless of how many line items the order has");
    }
}
```

**How to run:** `javac BatchedPattern.java && java BatchedPattern` (JDK 17+).

Expected output:
```
order details: [li-1-detail, li-2-detail, li-3-detail]
total network calls: 1
this stays at 1 call regardless of how many line items the order has
```

The production-flavored fix: `getOrderWithLineItems` returns the order header and all its line items in a single response. Unlike Level 2's N+1 pattern, this call count stays constant at `1` no matter how large the order is — an order with 100 line items costs exactly the same single network round trip as an order with 3.

## 6. Walkthrough

1. `getOrderWithLineItems("ord-1")` is called once directly in `main`, incrementing `networkCallCount` to `1` and returning the full list of line item details, already assembled server-side (standing in for a real service that joined its own local order and line-item tables before responding).
2. `callsNeededForOrder("ord-1")` is called separately to demonstrate the measurement: it resets `networkCallCount` to `0`, calls `getOrderWithLineItems` once, and returns the resulting count — `1`.
3. Contrast this directly with `MeasureAtScale`'s `callsNeededForOrder`, which had to call `getOrderLineItemIds` once *and then* `getLineItem` once per item in a loop — here, there is no loop making per-item network calls at all, because all the data needed was returned in the single initial call.
4. The final print states the general property directly: this call count is independent of the order's size, because the batching decision was made once, in the API's design (return everything needed for "get a full order" in one response), rather than left to the caller to assemble via repeated small calls.

```
Chatty (N+1):    getOrderLineItemIds() -> [3 IDs] -> getLineItem() x3  = 4 total calls (scales with order size)
Batched (1 call): getOrderWithLineItems() -> [everything already included]  = 1 total call (constant, regardless of order size)
```

## 7. Gotchas & takeaways

> **Gotcha:** batching too aggressively — returning far more data than a typical caller actually needs, "just in case" — trades the chattiness problem for a different one: large, wasteful responses that slow down the common case to avoid a rare one. Design the batched response around what the *typical* caller of this operation actually needs, not the maximum conceivable superset of everything any caller might ever want.

- A chatty service relationship requires many small network calls to complete one logical operation, most commonly seen as an N+1 pattern: one call to get a list, then one more call per item in that list.
- The concrete cost of chattiness scales directly with data size — a chatty pattern that costs 4 calls for a small order can cost over 100 calls for a large one, since each additional item adds another full network round trip.
- The fix is API design, not just implementation: shape the response to return everything a typical caller needs for the logical operation in one call, rather than leaving the caller to assemble it through repeated small requests.
- Recognizing chattiness is measurable, not just a feeling: count network calls per logical operation, and treat a high, size-dependent count as a concrete signal to redesign the API or reconsider the granularity of the boundary between the two services involved.
