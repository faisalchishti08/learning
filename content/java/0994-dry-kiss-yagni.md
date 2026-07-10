---
card: java
gi: 994
slug: dry-kiss-yagni
title: DRY / KISS / YAGNI
---

## 1. What it is

Three small, complementary rules of thumb that guard against three different failure modes:

- **DRY (Don't Repeat Yourself):** every piece of knowledge should have a single, unambiguous representation in the system. If the same tax-rate calculation appears in three places, a change means finding and fixing all three — and missing one is a bug waiting to happen.
- **KISS (Keep It Simple, Stupid):** prefer the simplest design that solves the actual problem. A clever, general, heavily-abstracted solution to a problem that didn't need one is harder to read, debug, and change than a plain one.
- **YAGNI (You Aren't Gonna Need It):** don't build functionality — configurability, extension points, extra parameters — for a requirement that doesn't exist yet. Build for what's asked, not for what might be asked someday.

They pull in slightly different directions (DRY says "unify," KISS and YAGNI both say "don't over-build"), and the skill is knowing when each one applies — and when applying one too aggressively fights the others.

## 2. Why & when

Duplicated logic (violating DRY) rots because each copy drifts independently — one gets patched, the others don't, and now the system's behavior is inconsistent depending on which code path ran. Over-engineered abstractions (violating KISS) rot because every reader has to hold an unnecessary layer of indirection in their head just to understand a simple operation. Speculative flexibility (violating YAGNI) rots because the "just in case" configuration option or extension hook usually guesses wrong about what future requirement actually shows up, and by the time the real requirement arrives, the existing speculative code often has to be ripped out anyway.

Apply DRY when you find the *same knowledge* — not just similar-looking code — repeated; two loops that happen to look alike but express different business rules aren't a DRY violation. Apply KISS when you catch yourself reaching for a design pattern, generic type parameter, or configuration layer that the current, actual requirement doesn't need. Apply YAGNI when you're tempted to add a parameter, an interface, or a plugin point "because it might be useful later" without a concrete need in front of you right now.

## 3. Core concept

```
// Violates DRY: the same discount-eligibility knowledge duplicated in two places
boolean eligibleA = order.total() > 100 && order.customer().isMember();
boolean eligibleB = order.total() > 100 && order.customer().isMember(); // copy elsewhere, will drift

// Violates KISS: a generic strategy-and-factory setup for one hardcoded rule
interface DiscountRule<T> { boolean applies(T context); }
class OverHundredMemberRule implements DiscountRule<Order> {
    public boolean applies(Order o) { return o.total() > 100 && o.customer().isMember(); }
}
// ...factory, registry, and lookup machinery just to call this one rule

// Follows DRY + KISS + YAGNI: one small, named, direct method -- nothing more
boolean isEligibleForDiscount(Order order) {
    return order.total() > 100 && order.customer().isMember();
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Duplicated logic in two places, an over-engineered generic factory for one rule, versus one simple named method used everywhere">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Copy A of the rule</text>
  <text x="110" y="60" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(DRY violation)</text>
  <rect x="220" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="310" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Copy B of the rule</text>
  <text x="310" y="60" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(now they can drift)</text>

  <rect x="20" y="100" width="380" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-dasharray="4"/>
  <text x="210" y="124" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DiscountRule&lt;T&gt; + factory + registry</text>
  <text x="210" y="144" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(KISS/YAGNI violation for ONE rule)</text>

  <rect x="450" y="60" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="86" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">isEligibleForDiscount()</text>
  <text x="535" y="105" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">one method, called everywhere</text>
</svg>

Two duplicated copies and an over-built factory all collapse into a single, direct, well-named method.

## 5. Runnable example

Scenario: a discount-eligibility check duplicated across a shopping cart system, evolving from copy-pasted logic and an over-engineered abstraction into one simple, reused rule that's easy to extend only when a real second rule actually shows up.

### Level 1 — Basic

```java
// File: DryKissYagniBasic.java
record Customer(String name, boolean isMember) {}
record Order(double total, Customer customer) {}

public class DryKissYagniBasic {
    public static void main(String[] args) {
        Order cartOrder = new Order(150.0, new Customer("Ana", true));
        Order checkoutOrder = new Order(150.0, new Customer("Ana", true));

        // Same knowledge, duplicated -- a DRY violation waiting to drift.
        boolean eligibleInCart = cartOrder.total() > 100 && cartOrder.customer().isMember();
        boolean eligibleAtCheckout = checkoutOrder.total() > 100 && checkoutOrder.customer().isMember();

        System.out.println("cart: " + eligibleInCart);
        System.out.println("checkout: " + eligibleAtCheckout);
    }
}
```

**How to run:** save as `DryKissYagniBasic.java`, then `javac DryKissYagniBasic.java && java DryKissYagniBasic` (JDK 17+).

Expected output:
```
cart: true
checkout: true
```

The eligibility rule (`total > 100 && isMember`) is written out twice. If the threshold changes from `100` to `150`, both copies must be found and updated — miss one, and the cart and checkout pages silently disagree.

### Level 2 — Intermediate

```java
// File: DryKissYagniIntermediate.java
record Customer(String name, boolean isMember) {}
record Order(double total, Customer customer) {}

public class DryKissYagniIntermediate {
    // DRY: the knowledge lives in exactly one place.
    // KISS: it's a plain method, not a framework.
    static boolean isEligibleForDiscount(Order order) {
        return order.total() > 100 && order.customer().isMember();
    }

    public static void main(String[] args) {
        Order cartOrder = new Order(150.0, new Customer("Ana", true));
        Order checkoutOrder = new Order(150.0, new Customer("Ana", true));

        System.out.println("cart: " + isEligibleForDiscount(cartOrder));
        System.out.println("checkout: " + isEligibleForDiscount(checkoutOrder));
    }
}
```

**How to run:** save as `DryKissYagniIntermediate.java`, then `javac DryKissYagniIntermediate.java && java DryKissYagniIntermediate` (JDK 17+).

Expected output:
```
cart: true
checkout: true
```

The real-world concern added: the eligibility rule now lives in exactly one method. Changing the threshold means editing one line, and both the cart and checkout pages update automatically because they both call the same method.

### Level 3 — Advanced

```java
// File: DryKissYagniAdvanced.java
record Customer(String name, boolean isMember) {}
record Order(double total, Customer customer) {}

public class DryKissYagniAdvanced {
    // A second, genuinely different discount rule has now actually arrived
    // (a seasonal promotion) -- so introducing a small abstraction here is
    // justified by a REAL second case, not a speculative one (that would be YAGNI).
    // KISS still applies: this is the simplest shape that fits two concrete rules,
    // not a generic framework built for an unknown number of future rules.
    interface DiscountEligibility {
        boolean applies(Order order);
    }

    static final DiscountEligibility MEMBER_OVER_HUNDRED =
        order -> order.total() > 100 && order.customer().isMember();

    static final DiscountEligibility SEASONAL_PROMO =
        order -> order.total() > 50;

    static boolean isEligibleForAnyDiscount(Order order, DiscountEligibility... rules) {
        for (DiscountEligibility rule : rules) {
            if (rule.applies(order)) return true;
        }
        return false;
    }

    public static void main(String[] args) {
        Order smallNonMemberOrder = new Order(75.0, new Customer("Ben", false));

        boolean eligible = isEligibleForAnyDiscount(smallNonMemberOrder, MEMBER_OVER_HUNDRED, SEASONAL_PROMO);
        System.out.println("eligible: " + eligible);
    }
}
```

**How to run:** save as `DryKissYagniAdvanced.java`, then `javac DryKissYagniAdvanced.java && java DryKissYagniAdvanced` (JDK 17+).

Expected output:
```
eligible: true
```

The production-flavored hard case: a second rule genuinely exists now, so a tiny `DiscountEligibility` functional interface unifies both without duplicating the "check any rule" loop — but note it's still just one interface and a loop, not a full rule-engine with a registry and configuration file, because nothing today calls for that.

## 6. Walkthrough

Tracing `isEligibleForAnyDiscount(smallNonMemberOrder, MEMBER_OVER_HUNDRED, SEASONAL_PROMO)`:

1. `smallNonMemberOrder` has `total = 75.0` and a non-member customer.
2. `isEligibleForAnyDiscount` receives both rules as a varargs array: `[MEMBER_OVER_HUNDRED, SEASONAL_PROMO]`.
3. The loop checks the first rule: `MEMBER_OVER_HUNDRED.applies(smallNonMemberOrder)` evaluates `75.0 > 100 && false` — `75.0 > 100` is already `false`, so this rule returns `false`.
4. The loop moves to the second rule: `SEASONAL_PROMO.applies(smallNonMemberOrder)` evaluates `75.0 > 50`, which is `true` — the method returns `true` immediately without checking any further rules.
5. `main` prints `"eligible: true"` — the order qualifies through the seasonal promotion even though it fails the membership rule.
6. Note that adding `SEASONAL_PROMO` required no change to `MEMBER_OVER_HUNDRED` or to the loop itself — each rule is a self-contained lambda, and the loop is generic over however many rules are passed in.

## 7. Gotchas & takeaways

> **Gotcha:** DRY targets duplicated *knowledge*, not duplicated *text*. Two `if` statements that happen to look identical but check unrelated business rules (one checks discount eligibility, one happens to also compare a number to `100` for shipping cost reasons) are not a DRY violation — unifying them would wrongly couple two independent rules that just happen to share a magic number today.

- DRY: one piece of knowledge, one place it's defined — but only when it's genuinely the *same* knowledge, not superficially similar code.
- KISS: solve today's actual problem with the simplest workable design; don't reach for a pattern or framework a plain method would cover.
- YAGNI: don't build configurability or extension points for requirements that don't exist yet — build them when the second real case shows up.
- The three principles can pull against each other: over-applying DRY too early can *cause* a KISS/YAGNI violation (a premature abstraction built to "avoid future duplication" that never materializes).
- A good rule of thumb: tolerate a little duplication until a second concrete, real case appears — then unify, and no sooner.
- These principles underpin why [SOLID — Single Responsibility](0989-solid-single-responsibility.md) and [SOLID — Open/Closed](0990-solid-open-closed.md) work well together — well-scoped, simple classes are naturally easier to keep DRY without over-engineering.
