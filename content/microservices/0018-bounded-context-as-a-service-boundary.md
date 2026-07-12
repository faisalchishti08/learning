---
card: microservices
gi: 18
slug: bounded-context-as-a-service-boundary
title: Bounded context as a service boundary
---

## 1. What it is

A **bounded context**, a term from Domain-Driven Design (DDD), is a boundary within which a particular business model and its vocabulary have one single, consistent meaning. The same word — "Customer," "Product," "Order" — can legitimately mean different things in different parts of a business: in a Sales context, a "Customer" might be a lead with a name and a sales rep assigned; in a Support context, the same word "Customer" might mean an account with a support tier and open ticket history. Rather than forcing one giant, universal "Customer" model that tries to satisfy both, DDD says: let each context define its own model of "Customer," scoped to what it actually needs, and translate explicitly at the boundary when contexts need to talk to each other.

In microservices, a bounded context is a natural, principled place to draw a service boundary — each service owns one bounded context's model and vocabulary.

## 2. Why & when

A single, universal domain model that tries to represent "Customer" correctly for every part of the business tends to grow unbounded: every team's edge case adds another optional field, another special flag, until the model satisfies no one well and changing it risks breaking everyone. Bounded contexts avoid this by admitting, explicitly, that different parts of the business genuinely have different mental models of the same real-world concept — and that's fine, as long as each model stays internally consistent within its own boundary.

Draw service boundaries around bounded contexts when you can identify genuinely distinct business sub-domains with their own vocabulary and rules — Sales, Support, Billing, Fulfillment are common examples in a typical company. This is the DDD-flavored, more rigorous version of [organized around business capabilities](0005-organized-around-business-capabilities.md): a bounded context isn't just "a feature area," it specifically means a place where a term's meaning is fixed and consistent.

## 3. Core concept

Two contexts can use the identical word for genuinely different things, and that's by design:

- **Sales context's "Customer":** name, sales rep, lead score, negotiated discount.
- **Support context's "Customer":** account ID, support tier, list of open tickets.

Neither is "more correct" — they're both accurate models of "Customer" *for what that context actually needs to do*. When Sales needs to know something Support tracks (or vice versa), the translation happens explicitly at the boundary, through each context's own API, not by merging the two models into one shared, universal one.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sales context and Support context each have their own distinct model of Customer, translated explicitly at the boundary through their APIs">
  <rect x="30" y="35" width="240" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Sales context</text>
  <text x="150" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Customer = { name, salesRep,</text>
  <text x="150" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">leadScore, discount }</text>

  <rect x="370" y="35" width="240" height="110" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Support context</text>
  <text x="490" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Customer = { accountId,</text>
  <text x="490" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">supportTier, openTickets }</text>

  <line x1="270" y1="90" x2="370" y2="90" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a18)"/>
  <text x="320" y="80" fill="#f0883e" font-size="7.5" text-anchor="middle" font-family="sans-serif">explicit translation</text>
  <defs><marker id="a18" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

Same word, two deliberately distinct models — connected only through an explicit translation at the boundary.

## 5. Runnable example

Scenario: Sales and Support each modeling "Customer" for their own needs, first as a single failed universal model, then as two proper bounded contexts, then with an explicit translation layer bridging them.

### Level 1 — Basic

```java
// File: UniversalCustomerModel.java -- ONE model trying to serve BOTH contexts
public class UniversalCustomerModel {
    record Customer(
        String name, String salesRep, int leadScore, double discount, // Sales-only fields
        String accountId, String supportTier, int openTickets          // Support-only fields, bolted on
    ) { }

    public static void main(String[] args) {
        // a Sales use case has to populate Support fields it doesn't understand or care about
        Customer forSales = new Customer("Alice", "Bob (rep)", 85, 0.1, null, null, 0);
        // a Support use case has to populate Sales fields it doesn't understand or care about
        Customer forSupport = new Customer(null, null, 0, 0.0, "acct-42", "gold", 3);

        System.out.println("Sales use: " + forSales.name() + ", rep=" + forSales.salesRep());
        System.out.println("Support use: " + forSupport.accountId() + ", tier=" + forSupport.supportTier());
    }
}
```

**How to run:** `javac UniversalCustomerModel.java && java UniversalCustomerModel` (JDK 17+).

Expected output:
```
Sales use: Alice, rep=Bob (rep)
Support use: acct-42, tier=gold
```

The single `Customer` record has to carry seven fields, four of which are meaningless `null`/`0` placeholders in any given use case. Every new field either context needs gets bolted onto this one shared, ever-growing record — a maintenance burden neither context actually wants.

### Level 2 — Intermediate

```java
// File: BoundedContexts.java -- TWO separate models, each scoped to its own context
public class BoundedContexts {
    static class SalesContext {
        record Customer(String name, String salesRep, int leadScore, double discount) { }
        Customer describe(String name) { return new Customer(name, "Bob (rep)", 85, 0.1); }
    }

    static class SupportContext {
        record Customer(String accountId, String supportTier, int openTickets) { }
        Customer describe(String accountId) { return new Customer(accountId, "gold", 3); }
    }

    public static void main(String[] args) {
        SalesContext sales = new SalesContext();
        SupportContext support = new SupportContext();

        var salesCustomer = sales.describe("Alice");
        var supportCustomer = support.describe("acct-42");

        System.out.println("Sales: " + salesCustomer.name() + ", leadScore=" + salesCustomer.leadScore());
        System.out.println("Support: " + supportCustomer.accountId() + ", tier=" + supportCustomer.supportTier());
    }
}
```

**How to run:** `javac BoundedContexts.java && java BoundedContexts` (JDK 17+).

Expected output:
```
Sales: Alice, leadScore=85
Support: acct-42, tier=gold
```

Each context now has its own, tightly-scoped `Customer` record — `SalesContext.Customer` has no idea Support fields even exist, and vice versa. Each model stays internally consistent and only carries the fields its own context actually needs.

### Level 3 — Advanced

```java
// File: ExplicitTranslation.java -- Sales needs a piece of Support's data;
// the translation happens EXPLICITLY at the boundary, models stay separate.
public class ExplicitTranslation {
    static class SalesContext {
        record Customer(String name, String salesRep, int leadScore, double discount) { }
        Customer describe(String name) { return new Customer(name, "Bob (rep)", 85, 0.1); }
    }

    static class SupportContext {
        record Customer(String accountId, String supportTier, int openTickets) { }
        Customer describe(String accountId) { return new Customer(accountId, "gold", 3); }
    }

    // an EXPLICIT translation, living at the boundary between the two contexts --
    // NOT a shared model, just a one-off mapping for this specific cross-context need.
    static String salesDiscountJustification(SalesContext.Customer salesCustomer, SupportContext.Customer supportCustomer) {
        if (supportCustomer.openTickets() > 2) {
            return salesCustomer.name() + " has " + supportCustomer.openTickets() + " open tickets -- consider a retention discount alongside the existing " + (salesCustomer.discount() * 100) + "% discount";
        }
        return salesCustomer.name() + " has no support concerns -- standard " + (salesCustomer.discount() * 100) + "% discount applies";
    }

    public static void main(String[] args) {
        SalesContext sales = new SalesContext();
        SupportContext support = new SupportContext();

        var salesCustomer = sales.describe("Alice");        // Sales' own model, unchanged
        var supportCustomer = support.describe("acct-42");  // Support's own model, unchanged

        // the ONLY place the two models ever meet -- an explicit function, not a merged data structure
        System.out.println(salesDiscountJustification(salesCustomer, supportCustomer));
    }
}
```

**How to run:** `javac ExplicitTranslation.java && java ExplicitTranslation` (JDK 17+).

Expected output:
```
Alice has 3 open tickets -- consider a retention discount alongside the existing 10.0% discount
```

The production-flavored case: `salesDiscountJustification` is the *only* piece of code in the whole example that knows about both `SalesContext.Customer` and `SupportContext.Customer` at once. It reads exactly the two fields it needs (`openTickets` from Support, `name` and `discount` from Sales) and produces a new, narrowly-scoped piece of information — it does not merge the two models into one shared type, and neither `SalesContext` nor `SupportContext` needed to change to make this cross-context logic possible.

## 6. Walkthrough

1. `sales.describe("Alice")` runs entirely within `SalesContext`, returning a `SalesContext.Customer` with exactly the four fields Sales cares about — `salesDiscountJustification` hasn't been called yet, and `SupportContext` hasn't been touched.
2. `support.describe("acct-42")` runs entirely within `SupportContext`, returning a `SupportContext.Customer` with exactly the three fields Support cares about — a completely different, unrelated type from step 1's result.
3. `salesDiscountJustification(salesCustomer, supportCustomer)` is called with both objects. Inside it, `supportCustomer.openTickets()` is read (`3`), and because `3 > 2`, the "retention discount" branch is taken.
4. The method then reads `salesCustomer.name()` (`"Alice"`) and `salesCustomer.discount()` (`0.1`, formatted as `10.0%`) — fields from the *other* model — to build its final message.
5. The returned string is printed directly. Notice that neither `SalesContext.Customer` nor `SupportContext.Customer` themselves ever combined; the combination happened only inside this one dedicated translation function, exactly at the boundary where the two bounded contexts needed to communicate.

```
SalesContext.Customer   { name, salesRep, leadScore, discount }
SupportContext.Customer { accountId, supportTier, openTickets }
        \                                /
         \                              /
      salesDiscountJustification(sales, support)   <- the ONLY place both models meet
                    |
              one narrow, new piece of derived information
```

## 7. Gotchas & takeaways

> **Gotcha:** the temptation to "just add the field" to avoid writing a translation function is exactly what erodes bounded contexts over time — each small addition seems harmless in isolation, but the cumulative effect is `UniversalCustomerModel`'s bloated, everyone-and-no-one's record from Level 1. Resist merging models; write the explicit, narrow translation instead, even when it feels like more code up front.

- A bounded context is a boundary within which a business term (like "Customer") has one consistent, well-defined meaning — different contexts are allowed to define the same term differently.
- Drawing service boundaries around bounded contexts means each service owns its own model and vocabulary, rather than sharing one universal model that tries to satisfy every context's needs at once.
- When two contexts need to share information, translate explicitly at the boundary with dedicated, narrow logic — never by merging their models into one shared type.
- Bounded context is the more rigorous, DDD-flavored version of [organized around business capabilities](0005-organized-around-business-capabilities.md): it specifically requires that a term's meaning stay fixed and consistent within a context's boundary.
