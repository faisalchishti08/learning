---
card: microservices
gi: 82
slug: idempotency-of-operations
title: "Idempotency of operations"
---

## 1. What it is

An operation is idempotent when performing it multiple times produces the same end result as performing it once. This is a property you *design into* an operation, not something that just happens to be true — as touched on in [HTTP verbs & status code semantics](0078-http-verbs-status-code-semantics.md), `GET`, `PUT`, and `DELETE` are idempotent by convention, but achieving that in practice requires the underlying business logic to actually behave that way, which doesn't happen automatically just by choosing the right verb.

## 2. Why & when

In a distributed system, a caller frequently cannot tell whether a request it sent actually succeeded — the request might have been processed and only the *response* got lost on the way back, in which case retrying re-executes an operation that already happened. Idempotent operations make this ambiguity harmless: retry as many times as needed, and the end state is identical to a single successful call. Non-idempotent operations turn that same ambiguity into a real bug — retrying "charge the customer $50" after a lost response can charge them twice.

Design every operation that might reasonably need retrying — which, in a microservices system with network calls between services, is nearly all of them — to be idempotent wherever the operation's actual semantics allow it. For operations where true idempotency isn't naturally achievable (like "create a new order"), use an [idempotency key](0083-idempotency-keys-for-safe-retries.md) to make retries safe anyway.

## 3. Core concept

Idempotency is achieved by designing the operation around an absolute target state or a unique identity check, not around a relative action that accumulates with each call.

```
NOT idempotent:  balance = balance + 50          (each call adds another 50)
IS idempotent:   balance = 50                     (each call sets the SAME final value)

NOT idempotent:  createOrder()                    (each call creates ANOTHER order)
IS idempotent:   createOrderIfNotExists(orderKey)  (each call with the SAME key has ONE effect)
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A relative increment operation applied three times results in three different balances, while an absolute set operation applied three times always results in the same final balance">
  <text x="160" y="20" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">balance += 50 (relative, NOT idempotent)</text>
  <rect x="20" y="35" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="55" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">50</text>
  <rect x="130" y="35" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="175" y="55" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">100</text>
  <rect x="240" y="35" width="90" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="285" y="55" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">150</text>
  <text x="175" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3 identical calls -&gt; 3 DIFFERENT results</text>

  <text x="480" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">balance = 50 (absolute, idempotent)</text>
  <rect x="340" y="125" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="385" y="145" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">50</text>
  <rect x="450" y="125" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="495" y="145" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">50</text>
  <rect x="560" y="125" width="60" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="590" y="145" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">50</text>
  <text x="480" y="170" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3 identical calls -&gt; SAME result every time</text>
</svg>

Relative operations accumulate on retry; absolute operations converge to the same state on retry.

## 5. Runnable example

Scenario: a customer loyalty-points balance, first incremented with a relative, non-idempotent operation that breaks under retry, then fixed by redesigning it as an idempotent, absolute "set" operation, then extended to a realistic case — order creation — where a true absolute-set redesign isn't natural, solved instead with a uniqueness check keyed by a client-supplied identifier.

### Level 1 — Basic

```java
// File: RelativeIncrementBreaksOnRetry.java -- addPoints is RELATIVE:
// retrying it (because the response was lost) adds points AGAIN.
import java.util.*;

public class RelativeIncrementBreaksOnRetry {
    static Map<String, Integer> balances = new HashMap<>(Map.of("cust-1", 0));

    static void addPoints(String customerId, int points) {
        balances.merge(customerId, points, Integer::sum);
    }

    public static void main(String[] args) {
        addPoints("cust-1", 50);          // first attempt -- succeeds server-side
        System.out.println("(response lost on the wire, client retries...)");
        addPoints("cust-1", 50);          // retry -- but this ADDS 50 AGAIN
        System.out.println("Balance: " + balances.get("cust-1") + " (should be 50, not 100)");
    }
}
```

**How to run:** `javac RelativeIncrementBreaksOnRetry.java && java RelativeIncrementBreaksOnRetry` (JDK 17+).

Expected output:
```
(response lost on the wire, client retries...)
Balance: 100 (should be 50, not 100)
```

### Level 2 — Intermediate

```java
// File: AbsoluteSetIsIdempotent.java -- redesign the operation around
// an ABSOLUTE target state instead of a relative delta -- now retrying
// is safe, because every call sets the SAME final value.
import java.util.*;

public class AbsoluteSetIsIdempotent {
    static Map<String, Integer> balances = new HashMap<>(Map.of("cust-1", 0));

    static void setBalance(String customerId, int newBalance) {
        balances.put(customerId, newBalance); // ABSOLUTE -- overwrites, doesn't accumulate
    }

    public static void main(String[] args) {
        setBalance("cust-1", 50);
        System.out.println("(response lost on the wire, client retries...)");
        setBalance("cust-1", 50); // retry -- SAME final value, no harm done
        System.out.println("Balance: " + balances.get("cust-1") + " (correct, regardless of retry count)");
    }
}
```

**How to run:** `javac AbsoluteSetIsIdempotent.java && java AbsoluteSetIsIdempotent` (JDK 17+).

Expected output:
```
(response lost on the wire, client retries...)
Balance: 50 (correct, regardless of retry count)
```

### Level 3 — Advanced

```java
// File: UniquenessCheckForCreation.java -- "create an order" has no
// natural absolute-set form (you can't just "set" a new resource into
// existence idempotently) -- so make it idempotent via a UNIQUENESS
// CHECK keyed by a caller-supplied identifier instead.
import java.util.*;

public class UniquenessCheckForCreation {
    static Map<String, String> ordersByRequestKey = new LinkedHashMap<>(); // requestKey -> orderId
    static int nextOrderId = 1;

    static String createOrder(String requestKey, String sku) {
        if (ordersByRequestKey.containsKey(requestKey)) {
            String existingOrderId = ordersByRequestKey.get(requestKey);
            System.out.println("  [duplicate request detected for key=" + requestKey + ", returning EXISTING order " + existingOrderId + "]");
            return existingOrderId; // idempotent: same key -> same result, no new order created
        }
        String orderId = "ORD-" + (nextOrderId++);
        ordersByRequestKey.put(requestKey, orderId);
        System.out.println("  [new order created: " + orderId + " for key=" + requestKey + "]");
        return orderId;
    }

    public static void main(String[] args) {
        String requestKey = "client-generated-key-abc123";
        String first = createOrder(requestKey, "widget");
        System.out.println("(response lost on the wire, client retries with the SAME key...)");
        String retried = createOrder(requestKey, "widget");
        System.out.println("First call returned: " + first + ", retry returned: " + retried + " -- same order, no duplicate");
        System.out.println("Total orders created: " + new HashSet<>(ordersByRequestKey.values()).size());
    }
}
```

**How to run:** `javac UniquenessCheckForCreation.java && java UniquenessCheckForCreation` (JDK 17+).

Expected output:
```
  [new order created: ORD-1 for key=client-generated-key-abc123]
(response lost on the wire, client retries with the SAME key...)
  [duplicate request detected for key=client-generated-key-abc123, returning EXISTING order ORD-1]
First call returned: ORD-1, retry returned: ORD-1 -- same order, no duplicate
Total orders created: 1
```

## 6. Walkthrough

1. **Level 1** — `addPoints` uses `Integer::sum` to merge a *relative* delta into the existing balance. `main` calls it twice with `50`, simulating a lost response followed by a client retry, and the balance ends up at `100` — double the correct value — because each call unconditionally added `50` on top of whatever was already there.
2. **Level 2 — redesigning around an absolute target** — `setBalance` replaces the existing value outright with `balances.put`, rather than merging a delta. Calling it twice with the same target value `50` leaves the balance at exactly `50` both times — the second call is a genuine no-op in terms of end state, which is precisely what idempotency requires.
3. **Level 3 — a case where "absolute set" doesn't naturally apply** — creating a new order has no meaningful absolute target state to "set to" the way a balance does; each legitimate call is supposed to create something new. `createOrder` solves this differently: it takes a `requestKey` — an identifier the *client* generates once per logical intent and reuses on every retry of that same logical request — and checks `ordersByRequestKey` for that key before creating anything.
4. **Tracing the two calls in `main`** — the first `createOrder(requestKey, "widget")` finds no existing entry for `requestKey`, so it proceeds to the "new order" branch: assigns `ORD-1`, stores the mapping, prints the creation message, and returns `"ORD-1"`. The second call, simulating the client's retry with the *identical* `requestKey* (because the client is retrying what it believes might be the same failed request, not creating a new order), finds `requestKey` already present in `ordersByRequestKey`, takes the "duplicate detected" branch, prints that diagnostic, and returns the *same* `"ORD-1"` without creating anything new.
5. **Confirming no duplication occurred** — `main`'s final line converts `ordersByRequestKey.values()` to a `HashSet` (deduplicating any repeated order ids) and prints its size, which is `1` — proving that despite two calls to `createOrder`, only one order genuinely exists. This is the general pattern for making an inherently non-idempotent operation (creation) safe to retry: shift from "does the operation itself always converge to the same state" to "does calling it twice with the same identifying key produce the same observable result" — see [idempotency keys for safe retries](0083-idempotency-keys-for-safe-retries.md) for the full treatment of this pattern as used over HTTP.

## 7. Gotchas & takeaways

> **Gotcha:** the uniqueness key in Level 3 must be generated by the *client*, once, before the first attempt — and reused unchanged on every retry of that same logical request. If the client instead generates a fresh key on each retry (a common mistake when the key generation is accidentally placed inside the retry loop itself), the uniqueness check never catches the duplicate, and the operation is no more idempotent than Level 1's naive version.

- Idempotency must be designed into an operation's actual logic — choosing an idempotent HTTP verb alone doesn't make the underlying operation behave idempotently.
- Prefer redesigning around an absolute target state (`set` rather than `increment`) wherever the operation's real-world meaning allows it — this is the simplest, most robust form of idempotency.
- Where an absolute-state redesign genuinely doesn't fit (like creating a new resource), use a client-generated, stable-across-retries uniqueness key instead — see [idempotency keys for safe retries](0083-idempotency-keys-for-safe-retries.md).
- Idempotency is what makes blind retries — the simplest, most common way distributed systems recover from transient failures — safe in the first place.
- Test idempotency explicitly: call the same operation twice (or more) with identical input and assert the end state matches a single call, exactly as this tutorial's runnable examples do.
