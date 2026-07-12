---
card: microservices
gi: 55
slug: domain-services
title: Domain services
---

## 1. What it is

A **domain service** is a stateless operation that expresses a genuine piece of business logic that doesn't naturally belong to any single entity or value object — most commonly because it involves *multiple* aggregates together, or because forcing it onto one entity would feel arbitrary and awkward. Transferring money between two `Account` aggregates is a classic example: the operation genuinely involves both accounts equally, and shoving the logic entirely into one `Account`'s `transferTo(otherAccount)` method would arbitrarily privilege one side of a fundamentally symmetric operation.

```java
class TransferService { // a DOMAIN SERVICE -- stateless, expresses logic spanning TWO aggregates
    void transfer(Account from, Account to, Money amount) {
        from.withdraw(amount); // each aggregate still enforces ITS OWN invariants
        to.deposit(amount);
    }
}
```

## 2. Why & when

Not every piece of business logic fits naturally as a method on one entity. Forcing it to anyway — picking one aggregate somewhat arbitrarily to own an operation that's genuinely about the relationship between two or more aggregates — produces awkward, asymmetric code and can hide the true nature of the operation behind a misleading "it's just a method on Account" framing. A domain service makes that multi-aggregate nature explicit: it's a piece of business logic that operates *on* aggregates from the outside, coordinating between them, rather than being logic that belongs to any one of them.

Reach for a domain service specifically when an operation genuinely spans multiple aggregates, or when a calculation or business rule doesn't have an obvious "owning" entity at all (a shipping-cost calculation considering an order, a destination, and a set of shipping rules, none of which is clearly the "right" place to put the logic). Don't reach for a domain service as a default dumping ground for logic that's actually simple enough to belong on one entity — that's a step backward toward procedural code organized by verb rather than by the domain's own natural structure.

## 3. Core concept

The distinguishing test: does this operation's logic genuinely belong to one specific aggregate, or does it coordinate between two or more?

- **Belongs on the entity:** `order.addLineItem(...)` — clearly and naturally a responsibility of `Order` itself.
- **Belongs in a domain service:** `transferService.transfer(fromAccount, toAccount, amount)` — genuinely about the relationship between two accounts, not naturally "belonging" to either one alone.

A domain service is stateless — it holds no data of its own between calls, only orchestrating operations on the aggregates it's given.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A domain service coordinates an operation spanning two separate account aggregates, with each aggregate still enforcing its own invariants">
  <rect x="30" y="60" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Account (from)</text>

  <rect x="250" y="30" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">TransferService</text>

  <rect x="470" y="60" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Account (to)</text>

  <line x1="250" y1="65" x2="170" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a55)"/>
  <line x1="390" y1="65" x2="470" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a55)"/>
  <defs><marker id="a55" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The domain service sits outside both aggregates, coordinating an operation that genuinely spans them both.

## 5. Runnable example

Scenario: transferring money between two accounts, first awkwardly forced onto one entity, then properly modeled as a domain service, then extended to enforce a cross-aggregate business rule that neither account alone could enforce.

### Level 1 — Basic

```java
// File: AwkwardlyOnOneEntity.java -- forcing a two-aggregate operation
// onto ONE entity, arbitrarily privileging it.
public class AwkwardlyOnOneEntity {
    static class Account {
        String id; double balance;
        Account(String id, double balance) { this.id = id; this.balance = balance; }

        // AWKWARD: Account has to reach into ANOTHER Account's internals to do this
        void transferTo(Account other, double amount) {
            this.balance -= amount;
            other.balance += amount; // reaching into another aggregate's state DIRECTLY
        }
    }

    public static void main(String[] args) {
        Account alice = new Account("acc-1", 100.0);
        Account bob = new Account("acc-2", 50.0);

        alice.transferTo(bob, 30.0); // WHY does "transferTo" live on Account, specifically? arbitrary choice
        System.out.println("Alice: $" + alice.balance + ", Bob: $" + bob.balance);
    }
}
```

**How to run:** `javac AwkwardlyOnOneEntity.java && java AwkwardlyOnOneEntity` (JDK 17+).

Expected output:
```
Alice: $70.0, Bob: $80.0
```

This works, but `transferTo` living specifically on `Account` (rather than, say, on some hypothetical `Bob`-initiated `receiveFrom`) is an arbitrary choice, and it required `Account` to reach directly into another `Account` instance's internal `balance` field — exactly the kind of aggregate-boundary violation [aggregates and aggregate roots](0052-aggregates-and-aggregate-roots.md) warns against.

### Level 2 — Intermediate

```java
// File: ProperDomainService.java -- TransferService coordinates between
// TWO aggregates, each still protecting its OWN invariants.
public class ProperDomainService {
    static class Account { // each aggregate ENFORCES ITS OWN invariant (no negative balance)
        String id; private double balance;
        Account(String id, double balance) { this.id = id; this.balance = balance; }

        void withdraw(double amount) {
            if (amount > balance) throw new IllegalStateException("insufficient funds in " + id);
            balance -= amount;
        }
        void deposit(double amount) { balance += amount; }
        double getBalance() { return balance; }
    }

    static class TransferService { // STATELESS -- holds no data between calls
        void transfer(Account from, Account to, double amount) {
            from.withdraw(amount); // Account still enforces ITS OWN rule
            to.deposit(amount);    // neither Account reaches into the other's internals
        }
    }

    public static void main(String[] args) {
        Account alice = new Account("acc-1", 100.0);
        Account bob = new Account("acc-2", 50.0);
        TransferService transferService = new TransferService();

        transferService.transfer(alice, bob, 30.0);
        System.out.println("Alice: $" + alice.getBalance() + ", Bob: $" + bob.getBalance());
    }
}
```

**How to run:** `javac ProperDomainService.java && java ProperDomainService` (JDK 17+).

Expected output:
```
Alice: $70.0, Bob: $80.0
```

Same result, but now the operation lives in `TransferService`, symmetric and independent of either `Account`. `Account.balance` is private, and each account enforces its own invariant (`withdraw` checks for sufficient funds) — `TransferService` coordinates the two calls without ever reaching into either account's internal state directly.

### Level 3 — Advanced

```java
// File: CrossAggregateRule.java -- the domain service enforces a rule
// that spans BOTH aggregates -- neither account alone could check it.
public class CrossAggregateRule {
    static class Account {
        String id; private double balance; boolean isFrozen;
        Account(String id, double balance, boolean isFrozen) { this.id = id; this.balance = balance; this.isFrozen = isFrozen; }
        void withdraw(double amount) {
            if (amount > balance) throw new IllegalStateException("insufficient funds in " + id);
            balance -= amount;
        }
        void deposit(double amount) { balance += amount; }
        double getBalance() { return balance; }
    }

    static class TransferService {
        static final double DAILY_TRANSFER_LIMIT = 25.0;

        void transfer(Account from, Account to, double amount) {
            // a rule spanning BOTH accounts -- neither Account's own withdraw/deposit could enforce this alone
            if (from.isFrozen || to.isFrozen) {
                throw new IllegalStateException("cannot transfer -- one or both accounts are frozen");
            }
            if (amount > DAILY_TRANSFER_LIMIT) {
                throw new IllegalStateException("transfer exceeds daily limit of $" + DAILY_TRANSFER_LIMIT);
            }
            from.withdraw(amount);
            to.deposit(amount);
        }
    }

    public static void main(String[] args) {
        Account alice = new Account("acc-1", 100.0, false);
        Account bob = new Account("acc-2", 50.0, true); // Bob's account is FROZEN
        TransferService transferService = new TransferService();

        try {
            transferService.transfer(alice, bob, 20.0);
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        Account carol = new Account("acc-3", 200.0, false);
        try {
            transferService.transfer(alice, carol, 30.0); // exceeds the $25 daily limit
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        transferService.transfer(alice, carol, 20.0); // within limit, both accounts active -- succeeds
        System.out.println("Alice: $" + alice.getBalance() + ", Carol: $" + carol.getBalance());
    }
}
```

**How to run:** `javac CrossAggregateRule.java && java CrossAggregateRule` (JDK 17+).

Expected output:
```
Rejected: cannot transfer -- one or both accounts are frozen
Rejected: transfer exceeds daily limit of $25.0
Alice: $80.0, Carol: $220.0
```

The production-flavored payoff: `TransferService.transfer` enforces two rules — no transfers involving a frozen account, and a per-transfer limit — that genuinely require looking at *both* accounts' state (or a system-wide policy) together. Neither `Account.withdraw` nor `Account.deposit` alone could express "reject this if the *other* account is frozen," because that fact isn't knowable from inside a single account's own state — it's inherently a cross-aggregate concern, exactly where a domain service belongs.

## 6. Walkthrough

1. `transferService.transfer(alice, bob, 20.0)` runs first: inside `transfer`, the check `from.isFrozen || to.isFrozen` evaluates `bob.isFrozen`, which is `true`, so the method throws immediately, before either `withdraw` or `deposit` is ever called — no partial state change occurs.
2. `transferService.transfer(alice, carol, 30.0)` runs next: `carol.isFrozen` is `false` and `alice.isFrozen` is `false`, so the first check passes. The second check, `amount > DAILY_TRANSFER_LIMIT` (`30.0 > 25.0`), is `true`, so this call also throws before any state change.
3. `transferService.transfer(alice, carol, 20.0)` runs last: both checks pass (`20.0 <= 25.0`, neither account frozen), so `from.withdraw(20.0)` runs on `alice` (reducing her balance from `100.0` to `80.0`), and `to.deposit(20.0)` runs on `carol` (increasing hers from `200.0` to `220.0`).
4. The final print confirms both balances reflect exactly the one successful transfer — the two earlier rejected attempts left both accounts' balances completely untouched, since the domain service's checks ran and failed before any mutation occurred.

```
transfer(alice, bob, 20)    -> bob.isFrozen == true       -> REJECTED, no mutation
transfer(alice, carol, 30)  -> amount > $25 limit          -> REJECTED, no mutation
transfer(alice, carol, 20)  -> both checks pass             -> alice -20, carol +20 -> SUCCEEDS
```

## 7. Gotchas & takeaways

> **Gotcha:** a domain service should stay stateless and hold no persistent data of its own — if `TransferService` started accumulating its own state across calls (like a running total of transfers processed), it would start acquiring aggregate-like responsibilities without the discipline of being an actual aggregate (identity, enforced invariants, a proper [repository](0056-repositories-ddd-sense.md)). If an operation genuinely needs to remember state across calls, that's a sign it needs its own aggregate, not a domain service.

- A domain service expresses business logic that doesn't naturally belong to one entity — most commonly because it coordinates an operation spanning two or more aggregates.
- Domain services are stateless: they hold no data of their own between calls, only orchestrating operations on the aggregates passed into them.
- The concrete test: does forcing this logic onto one specific aggregate feel natural, or arbitrary and asymmetric? Arbitrary and asymmetric is the signal for a domain service instead.
- Cross-aggregate business rules — a rule that genuinely can't be checked from inside just one aggregate's own state — belong in the domain service coordinating those aggregates, not artificially forced into one of them.
