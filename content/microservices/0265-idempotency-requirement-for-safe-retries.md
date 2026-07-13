---
card: microservices
gi: 265
slug: idempotency-requirement-for-safe-retries
title: "Idempotency requirement for safe retries"
---

## 1. What it is

Idempotency is the property of an operation that produces the same end result whether it's performed once or many times — "set the account balance to $100" is idempotent (repeating it changes nothing further), while "add $100 to the account balance" is not (repeating it keeps adding more money) — and it's the precondition that determines whether an operation can be safely retried at all after an ambiguous failure like a timeout.

## 2. Why & when

As [why distributed systems fail](0239-why-distributed-systems-fail-partial-failure.md) covers, a timeout provides no certainty about whether the original request actually completed on the remote side before the response was lost — retrying in that situation risks the operation happening twice. For an idempotent operation, this risk simply doesn't matter: performing "set balance to $100" twice produces the exact same final state as performing it once, so retrying after an ambiguous timeout is completely safe regardless of whether the first attempt actually succeeded. For a non-idempotent operation like "charge $100" or "add item to cart," retrying after a timeout risks a real, harmful duplication — a double charge, a duplicated cart item — making blind retries of such operations actively dangerous rather than merely wasteful.

Verify an operation's idempotency before enabling automatic retries for it — this isn't a detail to assume favorably, since getting it wrong produces real, sometimes financially significant, duplicated side effects. Naturally idempotent operations (most `GET` requests, a `PUT` that fully replaces a resource with a specific new state) can be retried freely; naturally non-idempotent operations (most `POST` requests creating a new resource, any "add" or "increment" operation) need either restructuring to become idempotent or an explicit idempotency mechanism (like an [idempotency key](0239-why-distributed-systems-fail-partial-failure.md)) before they're safe to retry.

## 3. Core concept

An operation's idempotency is a property of its *effect* on state, not of whether it happens to succeed — the test is: if this operation is performed N times instead of once, is the resulting state identical to performing it exactly once? Operations expressed as absolute assignments tend to be idempotent; operations expressed as relative deltas tend not to be.

```java
// NOT idempotent -- each call ADDS 100, so calling it twice DOUBLES the effect
void addToBalance(String accountId, int amount) { balances.merge(accountId, amount, Integer::sum); }

// IDEMPOTENT -- calling it any number of times produces the IDENTICAL final state
void setBalance(String accountId, int newBalance) { balances.put(accountId, newBalance); }

// a NON-idempotent operation made SAFE to retry via an idempotency key (deduplication at the target)
void chargeOnce(String idempotencyKey, int amount) {
    if (processedKeys.contains(idempotencyKey)) return; // the KEY, not the operation itself, makes retrying SAFE
    balances.merge(accountId, amount, Integer::sum);
    processedKeys.add(idempotencyKey);
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling an idempotent operation twice, like setting a balance to one hundred, results in the same final state as calling it once; calling a non-idempotent operation twice, like adding one hundred, results in a doubled, incorrect final state" >
  <rect x="20" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Idempotent: setBalance(100)</text>
  <text x="155" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">called ONCE or TWICE -- SAME result: 100</text>
  <text x="155" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SAFE to retry after a timeout</text>

  <rect x="350" y="20" width="270" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="485" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Non-idempotent: addToBalance(100)</text>
  <text x="485" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">called TWICE -- WRONG result: +200</text>
  <text x="485" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">DANGEROUS to retry blindly</text>
</svg>

The same "retry after a timeout" action produces correct results for one operation and a duplicated, wrong result for the other.

## 5. Runnable example

Scenario: a naive "add to balance" retry that duplicates the effect when the same operation is retried after an ambiguous timeout, refactored to the equivalent idempotent "set balance" formulation that's inherently safe to retry regardless of how many times it's called, and finally demonstrating an idempotency key applied to a genuinely non-idempotent operation (a payment charge that can't naturally be restructured as an assignment), making it safe to retry without changing its fundamental nature.

### Level 1 — Basic

```java
// File: NonIdempotentRetryDuplicates.java -- retrying an "ADD" operation
// after an AMBIGUOUS timeout DUPLICATES its effect -- a real bug.
import java.util.*;

public class NonIdempotentRetryDuplicates {
    static Map<String, Integer> balances = new HashMap<>(Map.of("acct-1", 500));

    static void addToBalance(String accountId, int amount) {
        balances.merge(accountId, amount, Integer::sum); // each call ADDS -- NOT idempotent
    }

    public static void main(String[] args) {
        addToBalance("acct-1", 100); // the ORIGINAL request -- SUCCEEDED, but response was LOST (simulated timeout)
        System.out.println("Balance after original request (response lost): " + balances.get("acct-1"));

        addToBalance("acct-1", 100); // the RETRY, believing the original might not have gone through
        System.out.println("Balance after retry: " + balances.get("acct-1") + " -- should be 600, but retrying DOUBLED the deposit!");
    }
}
```

**How to run:** `javac NonIdempotentRetryDuplicates.java && java NonIdempotentRetryDuplicates` (JDK 17+).

Expected output:
```
Balance after original request (response lost): 600
Balance after retry: 700 -- should be 600, but retrying DOUBLED the deposit!
```

### Level 2 — Intermediate

```java
// File: IdempotentSetIsSafeToRetry.java -- restructured to an ABSOLUTE
// "SET" operation -- retrying it ANY number of times produces the SAME
// final result.
import java.util.*;

public class IdempotentSetIsSafeToRetry {
    static Map<String, Integer> balances = new HashMap<>(Map.of("acct-1", 500));

    static void setBalance(String accountId, int newBalance) {
        balances.put(accountId, newBalance); // IDEMPOTENT -- an absolute assignment, not a relative delta
    }

    public static void main(String[] args) {
        int intendedNewBalance = 600; // the CLIENT computes the target state, not a delta

        setBalance("acct-1", intendedNewBalance); // ORIGINAL request -- succeeded, response lost
        System.out.println("Balance after original request (response lost): " + balances.get("acct-1"));

        setBalance("acct-1", intendedNewBalance); // RETRY -- SAFE, produces the IDENTICAL result
        System.out.println("Balance after retry: " + balances.get("acct-1") + " -- CORRECT, retrying changed NOTHING further.");
    }
}
```

**How to run:** `javac IdempotentSetIsSafeToRetry.java && java IdempotentSetIsSafeToRetry` (JDK 17+).

Expected output:
```
Balance after original request (response lost): 600
Balance after retry: 600 -- CORRECT, retrying changed NOTHING further.
```

### Level 3 — Advanced

```java
// File: IdempotencyKeyForUnavoidableAddOperation.java -- a payment
// CHARGE can't naturally be expressed as a "set" (each charge is a
// genuinely NEW, distinct event) -- an IDEMPOTENCY KEY makes it SAFE
// to retry WITHOUT changing the operation's fundamental "add" nature.
import java.util.*;

public class IdempotencyKeyForUnavoidableAddOperation {
    static Map<String, Integer> balances = new HashMap<>(Map.of("acct-1", 500));
    static Set<String> processedIdempotencyKeys = new HashSet<>(); // the SERVER'S own deduplication record

    static void chargeAccount(String idempotencyKey, String accountId, int amount) {
        if (processedIdempotencyKeys.contains(idempotencyKey)) {
            System.out.println("  [server] idempotency key '" + idempotencyKey + "' already processed -- SKIPPING, not charging again");
            return; // the KEY, checked FIRST, prevents the underlying non-idempotent "add" from running twice
        }
        balances.merge(accountId, amount, Integer::sum); // the actual, genuinely non-idempotent ADD
        processedIdempotencyKeys.add(idempotencyKey);
        System.out.println("  [server] charge of " + amount + " processed under key '" + idempotencyKey + "'");
    }

    public static void main(String[] args) {
        String idempotencyKey = "charge-order-42"; // STABLE across retries for the SAME logical charge

        chargeAccount(idempotencyKey, "acct-1", 100); // ORIGINAL -- succeeded, response lost
        System.out.println("Balance after original charge (response lost): " + balances.get("acct-1"));

        chargeAccount(idempotencyKey, "acct-1", 100); // RETRY -- the SAME key -- server recognizes and SKIPS it
        System.out.println("Balance after retry: " + balances.get("acct-1") + " -- CORRECT, the key prevented a duplicate charge.");
    }
}
```

**How to run:** `javac IdempotencyKeyForUnavoidableAddOperation.java && java IdempotencyKeyForUnavoidableAddOperation` (JDK 17+).

Expected output:
```
  [server] charge of 100 processed under key 'charge-order-42'
Balance after original charge (response lost): 600
  [server] idempotency key 'charge-order-42' already processed -- SKIPPING, not charging again
Balance after retry: 600 -- CORRECT, the key prevented a duplicate charge.
```

## 6. Walkthrough

1. **Level 1, the bug made concrete** — `addToBalance` executes `balances.merge(accountId, amount, Integer::sum)`, which unconditionally adds `amount` to whatever the current balance is; calling this twice with the identical `100` produces `500 + 100 + 100 = 700`, not the intended `600` — this is exactly what happens if a caller retries a non-idempotent "add money" operation after a timeout, unaware the original request had actually already succeeded.
2. **Level 2, restructuring as an assignment** — `setBalance` takes the *target* value directly (`intendedNewBalance`, computed by the caller as "current balance plus deposit amount, resolved once, upfront") and assigns it unconditionally via `balances.put`, overwriting whatever was there before, rather than modifying it relative to the current value.
3. **Level 2, the retry becoming harmless** — calling `setBalance("acct-1", 600)` twice in a row produces `600` both times, since the second call simply overwrites the balance with the identical value the first call already set it to — the operation's mathematical structure itself, not any external tracking mechanism, is what makes the retry safe here.
4. **Level 3, an operation that genuinely can't be restructured this way** — a payment charge is fundamentally a *new event* each time (a real charge, a real transaction record) rather than a state that can be meaningfully expressed as "set the total charged amount to X" — `chargeAccount` still performs the same kind of relative `merge`/add operation as Level 1's problematic version, since that's the operation's true nature.
5. **Level 3, the idempotency key providing safety externally** — `chargeAccount` checks `processedIdempotencyKeys.contains(idempotencyKey)` *before* performing the actual balance modification; the first call with a given key processes normally and records that key, while any subsequent call with the *same* key is recognized and skipped entirely, regardless of how many times it's retried.
6. **Level 3, the resulting safety without changing the operation's nature** — the balance ends up at the correct `600` after both the original call and the retry, exactly matching Level 2's outcome, but achieved through an entirely different mechanism: rather than the operation itself being mathematically idempotent (as `setBalance` is), an external deduplication record makes an inherently non-idempotent operation *behave* idempotently from the caller's perspective — this is precisely why idempotency keys exist: for the many real operations (payments, order creation, any genuinely new-event-generating action) that cannot naturally be expressed as an absolute assignment the way a balance update sometimes can.

## 7. Gotchas & takeaways

> **Gotcha:** an idempotency key only provides safety if it's genuinely stable across retries of the *same logical operation* — generating a new, random key for every retry attempt (rather than reusing the same key derived from the original request) defeats the entire mechanism, since the server would then see each "retry" as a distinct, new key and process it as a brand-new charge; the key must be derived deterministically from something identifying the original logical request (an order ID, a client-generated request ID sent once and reused across retries), not freshly generated per attempt.

- Idempotency is the property that performing an operation multiple times produces the same final state as performing it once — it's the precondition for safely retrying an operation after an ambiguous failure like a timeout.
- Operations expressed as absolute assignments ("set to X") tend to be naturally idempotent; operations expressed as relative deltas ("add X," "increment by X") are not, and retrying them blindly risks real, duplicated effects.
- Where an operation can be restructured as an idempotent assignment without losing its intended meaning, doing so is the simplest way to make it safe to retry.
- Where an operation is fundamentally non-idempotent by nature (like a payment charge, a genuinely new event each time), an idempotency key lets the server deduplicate repeated attempts, making the operation safe to retry without changing its underlying structure.
- An idempotency key only works if it's stable and reused across retries of the same logical operation — a freshly generated key on every retry attempt defeats the mechanism entirely, since the server would then see each attempt as an unrelated, new request.
