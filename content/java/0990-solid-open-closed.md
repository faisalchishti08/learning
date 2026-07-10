---
card: java
gi: 990
slug: solid-open-closed
title: SOLID — Open/Closed
---

## 1. What it is

The **Open/Closed Principle (OCP)** says a class (or module) should be **open for extension but closed for modification**. In practice: when a new requirement shows up — a new discount type, a new shape, a new payment method — you should be able to add a new class that implements an existing interface, rather than opening up an existing class and editing its `if`/`else` or `switch` chain to add another branch.

"Closed" doesn't mean "never touched again forever." It means the class's *existing, already-tested* behavior is stable and doesn't need to be re-verified every time a new variant is added elsewhere.

## 2. Why & when

Editing a working class every time a new case arrives has two costs: it risks breaking the existing cases (a typo in the new `else if` branch can silently corrupt an unrelated one), and it forces re-testing the whole class every release even though most of it didn't change. OCP exists to convert "add a new branch to an existing method" into "add a new class implementing an existing interface" — the old code is untouched and stays trusted.

Reach for OCP when you notice a `switch` or `if`/`else if` chain keyed on a type or category, and you already know more cases are coming (new shapes, new payment providers, new notification channels). It's less useful for logic that truly will never grow another case — introducing an interface and a class per branch for something that's genuinely fixed forever is unnecessary ceremony.

## 3. Core concept

```
// Violates OCP: adding a new shape means opening this method and editing it
double area(Object shape) {
    if (shape instanceof Circle c) return Math.PI * c.radius() * c.radius();
    if (shape instanceof Square s) return s.side() * s.side();
    // new shape => another edit here, risking the existing branches
    throw new IllegalArgumentException("unknown shape");
}

// Follows OCP: each shape knows its own area; adding a shape means adding a class
interface Shape { double area(); }
class Circle implements Shape {
    double radius;
    public double area() { return Math.PI * radius * radius; }
}
class Square implements Shape {
    double side;
    public double area() { return side * side; }
}
// A new shape is a new class implementing Shape -- area(Object) never changes.
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A growing if-else chain versus a Shape interface with independent implementations added as new classes">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before: edit to extend</text>
  <rect x="30" y="40" width="240" height="110" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">area(Object shape)</text>
  <text x="150" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">if Circle ...</text>
  <text x="150" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">if Square ...</text>
  <text x="150" y="115" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">if Triangle ... (new edit!)</text>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">After: extend, don't edit</text>
  <rect x="420" y="40" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="61" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Shape (interface)</text>
  <rect x="370" y="100" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="415" y="124" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Circle</text>
  <rect x="470" y="100" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="515" y="124" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Square</text>
  <rect x="570" y="100" width="55" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-dasharray="4"/>
  <text x="597" y="124" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">new!</text>
</svg>

A new shape becomes a new class implementing `Shape`; nothing that already worked has to be reopened.

## 5. Runnable example

Scenario: a discount calculator for an order total, evolving from a branching chain into an extensible set of discount classes that new discount types can join without touching existing code.

### Level 1 — Basic

```java
// File: OcpBasic.java
public class OcpBasic {
    static double applyDiscount(String discountType, double total) {
        if (discountType.equals("NONE")) return total;
        if (discountType.equals("TEN_PERCENT")) return total * 0.90;
        throw new IllegalArgumentException("unknown discount: " + discountType);
    }

    public static void main(String[] args) {
        System.out.println(applyDiscount("NONE", 100.0));
        System.out.println(applyDiscount("TEN_PERCENT", 100.0));
    }
}
```

**How to run:** save as `OcpBasic.java`, then `javac OcpBasic.java && java OcpBasic` (JDK 17+).

Expected output:
```
100.0
90.0
```

Every new discount type means opening `applyDiscount` and adding another `if` — risking the existing branches with each edit.

### Level 2 — Intermediate

```java
// File: OcpIntermediate.java
interface Discount {
    double apply(double total);
}

class NoDiscount implements Discount {
    public double apply(double total) { return total; }
}

class TenPercentDiscount implements Discount {
    public double apply(double total) { return total * 0.90; }
}

public class OcpIntermediate {
    static double checkout(Discount discount, double total) {
        return discount.apply(total);
    }

    public static void main(String[] args) {
        System.out.println(checkout(new NoDiscount(), 100.0));
        System.out.println(checkout(new TenPercentDiscount(), 100.0));
    }
}
```

**How to run:** save as `OcpIntermediate.java`, then `javac OcpIntermediate.java && java OcpIntermediate` (JDK 17+).

Expected output:
```
100.0
90.0
```

The real-world concern added: `checkout` is now closed for modification — it only ever calls `discount.apply(total)`, regardless of which `Discount` it's handed. Each discount is open for extension as its own class.

### Level 3 — Advanced

```java
// File: OcpAdvanced.java
import java.util.List;

interface Discount {
    double apply(double total);
}

class NoDiscount implements Discount {
    public double apply(double total) { return total; }
}

class TenPercentDiscount implements Discount {
    public double apply(double total) { return total * 0.90; }
}

// New requirement: a seasonal discount stacked on top of a percentage discount.
// Added as a NEW class -- OcpAdvanced's checkout logic below is untouched.
class BulkOrderDiscount implements Discount {
    private final int itemCount;
    BulkOrderDiscount(int itemCount) { this.itemCount = itemCount; }
    public double apply(double total) {
        return itemCount >= 10 ? total * 0.85 : total;
    }
}

// Composite: combines several discounts without any of them knowing about each other.
class StackedDiscount implements Discount {
    private final List<Discount> discounts;
    StackedDiscount(List<Discount> discounts) { this.discounts = discounts; }
    public double apply(double total) {
        double result = total;
        for (Discount d : discounts) {
            result = d.apply(result);
        }
        return result;
    }
}

public class OcpAdvanced {
    static double checkout(Discount discount, double total) {
        return discount.apply(total);
    }

    public static void main(String[] args) {
        Discount combo = new StackedDiscount(List.of(new TenPercentDiscount(), new BulkOrderDiscount(12)));
        System.out.println(checkout(new NoDiscount(), 100.0));
        System.out.println(checkout(combo, 100.0));
    }
}
```

**How to run:** save as `OcpAdvanced.java`, then `javac OcpAdvanced.java && java OcpAdvanced` (JDK 17+).

Expected output:
```
100.0
76.5
```

The production-flavored hard case: `BulkOrderDiscount` and `StackedDiscount` are both brand-new classes, and `checkout` — the method every discount ultimately flows through — was never reopened to support either of them, because both just implement `Discount`.

## 6. Walkthrough

Tracing `checkout(combo, 100.0)` in `OcpAdvanced.main`:

1. `combo` is a `StackedDiscount` built from two discounts: `TenPercentDiscount` and `BulkOrderDiscount(12)`.
2. `checkout(combo, 100.0)` calls `combo.apply(100.0)`, which is `StackedDiscount.apply`.
3. Inside, `result` starts at `100.0`. The loop applies `TenPercentDiscount.apply(100.0)` first, producing `90.0`.
4. `result` is now `90.0`; the loop applies `BulkOrderDiscount(12).apply(90.0)` next. Since `itemCount` (`12`) is `>= 10`, it returns `90.0 * 0.85 = 76.5`.
5. The loop has no more discounts, so `StackedDiscount.apply` returns `76.5`, which `checkout` returns and `main` prints.
6. Note that `checkout`'s own code — `return discount.apply(total)` — is identical to the one used for `NoDiscount` in the first `println`; it never needed to know that a stacked, bulk-aware discount existed.

## 7. Gotchas & takeaways

> **Gotcha:** OCP doesn't mean a class can *never* be modified. It means the stable, already-tested parts of a system shouldn't need modification just to add a new *variant* of something the system already models as a type. Fixing an actual bug in `TenPercentDiscount` is still fine — that's not the kind of "modification" OCP is protecting against.

- OCP: open for extension (new classes implementing an interface), closed for modification (existing, tested code doesn't change just to add a variant).
- A growing `if`/`else if` or `switch` chain keyed on type is the classic sign a design violates OCP.
- Introducing an interface (like `Discount` or `Shape`) turns "add a branch" into "add a class" — the dispatching code stays fixed.
- Composite implementations (like `StackedDiscount`) let new combinations emerge from existing pieces without any of those pieces changing.
- Don't apply OCP preemptively to logic that will genuinely never grow another case — the abstraction has a cost too.
- OCP and [SOLID — Single Responsibility](0989-solid-single-responsibility.md) work together: each new implementation class typically has exactly one responsibility of its own.
