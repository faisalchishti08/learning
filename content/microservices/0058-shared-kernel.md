---
card: microservices
gi: 58
slug: shared-kernel
title: Shared kernel
---

## 1. What it is

A **Shared Kernel** is a deliberate, small piece of domain model — a class, a small set of value objects, a shared library — that two (or occasionally more) bounded contexts explicitly agree to jointly own and maintain together, rather than each context maintaining its own independent copy. A `Money` value object used identically by both an `OrdersContext` and a `BillingContext` is a classic example: both teams agree it should behave identically everywhere, and both teams share responsibility for changing it, with any change requiring coordination between them.

## 2. Why & when

Most cross-context relationships should avoid tight coupling — that's the whole point of drawing bounded context boundaries in the first place. A Shared Kernel is a deliberate, narrow exception: for a small piece of model where independent evolution genuinely isn't worth the cost (two contexts maintaining their own, potentially subtly-diverging `Money` implementations, with rounding or currency-handling bugs creeping in from the duplication), sharing that one piece and coordinating changes to it together can be the pragmatic choice.

Choose a Shared Kernel only when the piece being shared is genuinely small, stable, and foundational enough that both teams agree keeping it identical everywhere matters more than each team's independent autonomy over that specific piece — and only when both teams have enough trust and communication bandwidth to coordinate changes without it becoming a bottleneck. This is the narrowest, most tightly-coupled of the context relationship patterns; use it sparingly.

## 3. Core concept

The defining trait: unlike every other relationship pattern in this section, a Shared Kernel means *both* teams have write access to the same shared code, and *both* must agree before it changes.

```
OrdersContext  \
                +--> SharedKernel.Money  (jointly owned, jointly changed)
BillingContext /
```

Contrast with Customer-Supplier or Conformist, where exactly one team owns the shared concept and the other only consumes it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrdersContext and BillingContext both directly depend on and jointly maintain the same shared Money value object">
  <rect x="40" y="30" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="115" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrdersContext</text>

  <rect x="450" y="30" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">BillingContext</text>

  <rect x="250" y="100" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SharedKernel.Money</text>
  <text x="320" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">jointly owned</text>

  <line x1="115" y1="80" x2="290" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="525" y1="80" x2="350" y2="100" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Two contexts both directly depending on, and both responsible for maintaining, the same shared piece of model.

## 5. Runnable example

Scenario: `OrdersContext` and `BillingContext` each needing money handling, first duplicated and diverging, then unified as a shared kernel, then extended to show coordinated changes to the shared kernel reaching both contexts simultaneously.

### Level 1 — Basic

```java
// File: DuplicatedMoneyDrifts.java -- each context maintains its OWN
// Money implementation, which can silently DRIFT apart.
public class DuplicatedMoneyDrifts {
    static class OrdersMoney { // OrdersContext's OWN copy
        double amount;
        OrdersMoney(double amount) { this.amount = amount; }
        OrdersMoney plus(OrdersMoney other) { return new OrdersMoney(Math.round((amount + other.amount) * 100.0) / 100.0); } // rounds to cents
    }

    static class BillingMoney { // BillingContext's SEPARATE copy -- maintained independently
        double amount;
        BillingMoney(double amount) { this.amount = amount; }
        BillingMoney plus(BillingMoney other) { return new BillingMoney(amount + other.amount); } // NO rounding -- a drift that crept in
    }

    public static void main(String[] args) {
        OrdersMoney ordersTotal = new OrdersMoney(9.999).plus(new OrdersMoney(0.001));
        BillingMoney billingTotal = new BillingMoney(9.999).plus(new BillingMoney(0.001));

        System.out.println("OrdersContext total: " + ordersTotal.amount);
        System.out.println("BillingContext total: " + billingTotal.amount + " (subtly different precision handling)");
    }
}
```

**How to run:** `javac DuplicatedMoneyDrifts.java && java DuplicatedMoneyDrifts` (JDK 17+).

Expected output:
```
OrdersContext total: 10.0
BillingContext total: 10.0
```

Wait — these happen to match here, but the two implementations use genuinely different logic (`OrdersMoney` explicitly rounds, `BillingMoney` doesn't), meaning they could easily diverge on other inputs — a real risk of two independently-maintained copies of the same conceptual value object silently drifting apart over time as each team makes its own, uncoordinated changes.

### Level 2 — Intermediate

```java
// File: SharedKernelUnified.java -- BOTH contexts use the SAME Money
// class from a jointly-maintained SHARED KERNEL.
public class SharedKernelUnified {
    // SHARED KERNEL -- jointly owned by BOTH OrdersTeam and BillingTeam, changes require BOTH teams' agreement
    static class SharedKernel {
        static class Money {
            double amount;
            Money(double amount) { this.amount = amount; }
            Money plus(Money other) { return new Money(Math.round((amount + other.amount) * 100.0) / 100.0); } // ONE agreed rounding rule
        }
    }

    static class OrdersContext { // uses the SHARED Money, does not maintain its own copy
        SharedKernel.Money calculateOrderTotal() {
            return new SharedKernel.Money(9.999).plus(new SharedKernel.Money(0.001));
        }
    }

    static class BillingContext { // ALSO uses the SAME SHARED Money
        SharedKernel.Money calculateInvoiceTotal() {
            return new SharedKernel.Money(9.999).plus(new SharedKernel.Money(0.001));
        }
    }

    public static void main(String[] args) {
        System.out.println("OrdersContext total: " + new OrdersContext().calculateOrderTotal().amount);
        System.out.println("BillingContext total: " + new BillingContext().calculateInvoiceTotal().amount + " (GUARANTEED identical logic)");
    }
}
```

**How to run:** `javac SharedKernelUnified.java && java SharedKernelUnified` (JDK 17+).

Expected output:
```
OrdersContext total: 10.0
BillingContext total: 10.0 (GUARANTEED identical logic)
```

Both contexts now call the exact same `SharedKernel.Money.plus` method — there is no possibility of the two contexts' rounding logic diverging, because there's only one implementation, jointly owned and maintained by both teams together.

### Level 3 — Advanced

```java
// File: CoordinatedKernelChange.java -- a change to the SHARED KERNEL
// (adding currency handling) reaches BOTH contexts SIMULTANEOUSLY.
public class CoordinatedKernelChange {
    static class SharedKernel {
        static class Money { // UPGRADED: now tracks currency too -- a change BOTH teams agreed to and adopted together
            double amount; String currency;
            Money(double amount, String currency) { this.amount = amount; this.currency = currency; }
            Money plus(Money other) {
                if (!currency.equals(other.currency)) throw new IllegalArgumentException("cannot add different currencies: " + currency + " and " + other.currency);
                return new Money(Math.round((amount + other.amount) * 100.0) / 100.0, currency);
            }
        }
    }

    static class OrdersContext {
        SharedKernel.Money calculateOrderTotal() {
            return new SharedKernel.Money(9.99, "USD").plus(new SharedKernel.Money(10.00, "USD"));
        }
    }

    static class BillingContext {
        SharedKernel.Money calculateInvoiceTotal() {
            return new SharedKernel.Money(9.99, "USD").plus(new SharedKernel.Money(10.00, "USD"));
        }

        // BillingContext IMMEDIATELY benefits from the currency-safety the shared kernel now provides
        void attemptMismatchedCurrencyAdd() {
            try {
                new SharedKernel.Money(10.00, "USD").plus(new SharedKernel.Money(5.00, "EUR"));
            } catch (IllegalArgumentException e) {
                System.out.println("BillingContext caught: " + e.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("OrdersContext total: $" + new OrdersContext().calculateOrderTotal().amount);
        System.out.println("BillingContext total: $" + new BillingContext().calculateInvoiceTotal().amount);
        new BillingContext().attemptMismatchedCurrencyAdd(); // BOTH contexts get this new safety, from ONE shared change
    }
}
```

**How to run:** `javac CoordinatedKernelChange.java && java CoordinatedKernelChange` (JDK 17+).

Expected output:
```
OrdersContext total: $19.99
BillingContext total: $19.99
BillingContext caught: cannot add different currencies: USD and EUR
```

The production-flavored payoff: `SharedKernel.Money` gained currency-safety in one coordinated change, jointly agreed to by both `OrdersTeam` and `BillingTeam`. Both `OrdersContext` and `BillingContext` immediately benefit from this new invariant (`plus` now rejects mismatched currencies) — a single fix or enhancement to the shared kernel reaches every context depending on it at once, exactly the payoff that makes the coordination cost of a Shared Kernel worthwhile for a piece of model this foundational.

## 6. Walkthrough

1. `new OrdersContext().calculateOrderTotal()` constructs two `SharedKernel.Money` instances, both with currency `"USD"`, and calls `plus` on them. Inside `plus`, `currency.equals(other.currency)` checks `"USD".equals("USD")`, which is `true`, so the addition proceeds normally, returning `Money(19.99, "USD")`.
2. `new BillingContext().calculateInvoiceTotal()` runs the identical logic — same `SharedKernel.Money` class, same `plus` method — producing the same result, `19.99`, confirming both contexts share exactly one implementation.
3. `attemptMismatchedCurrencyAdd()` constructs two `Money` instances with *different* currencies (`"USD"` and `"EUR"`), then calls `plus`. This time, `currency.equals(other.currency)` evaluates `"USD".equals("EUR")`, which is `false`, so the method throws `IllegalArgumentException`.
4. The `catch` block in `attemptMismatchedCurrencyAdd` catches this exception and prints the message — demonstrating that `BillingContext`, without any BillingTeam-specific code changes of its own, immediately gained this currency-safety check the moment the shared kernel was upgraded, because both contexts depend on that exact same, single implementation.

```
SharedKernel.Money upgraded (jointly, by BOTH teams):  amount + CURRENCY, plus() now validates matching currencies
        |
   +----------------------------+-----------------------------+
   OrdersContext                  BillingContext
   gets currency-safe plus()      gets currency-safe plus() -- SAME change, reached BOTH instantly
```

## 7. Gotchas & takeaways

> **Gotcha:** a Shared Kernel's coordination requirement is a genuine, ongoing cost — every change to it requires both teams' agreement, which can become a real bottleneck if the kernel grows beyond a small, genuinely stable core. If a shared kernel keeps needing new capabilities that only one team actually uses, that's a signal it's grown beyond what should be jointly owned, and part of it should be split out to be owned independently by the team that actually needs it.

- A Shared Kernel is a small, deliberately jointly-owned piece of domain model that two contexts explicitly agree to share and maintain together, rather than each maintaining independent copies.
- Choose it only for something genuinely small, stable, and foundational enough that keeping it identical everywhere matters more than either team's independent autonomy over that specific piece.
- The concrete payoff: a coordinated improvement to the shared kernel (like adding currency-safety) reaches every dependent context simultaneously, with no risk of the independently-maintained copies silently drifting apart.
- This is the tightest-coupled context relationship pattern in DDD's toolkit — use it sparingly, and watch for the shared kernel growing beyond what genuinely needs joint ownership, which turns its coordination cost into a real bottleneck.
