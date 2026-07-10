---
card: java
gi: 1007
slug: strategy
title: Strategy
---

## 1. What it is

The **Strategy** pattern defines a family of interchangeable algorithms, encapsulates each one behind a common interface, and lets client code pick and swap between them at runtime. Instead of a method containing a `switch` that picks which algorithm to run inline, each algorithm becomes its own class implementing a shared interface, and the calling code holds a reference to whichever one it currently wants — swappable without touching the calling code itself.

## 2. Why & when

When a class needs to support several interchangeable ways of doing the same kind of work — different sorting orders, different pricing rules, different compression algorithms — hardcoding them as a branching `switch` inside one method means every new variant requires editing that method, and testing one variant means dragging along all the others. Strategy exists to pull each variant out into its own class, so the calling code becomes indifferent to *which* algorithm it's using — it just calls the same method on whichever `Strategy` object it's holding.

Reach for Strategy when a method's behavior needs to vary independently of the object using it, and you want to swap that behavior at runtime — a payment processor supporting several payment methods, a route planner supporting "fastest," "shortest," and "avoid tolls" modes. It's unnecessary when there's really only one way to do the thing and no plausible need to swap it — that's just a private method.

## 3. Core concept

```
interface SortStrategy { void sort(int[] array); }

class BubbleSort implements SortStrategy {
    public void sort(int[] array) { /* bubble sort logic */ }
}
class QuickSort implements SortStrategy {
    public void sort(int[] array) { /* quicksort logic */ }
}

class Sorter {
    private SortStrategy strategy; // holds whichever algorithm is currently chosen
    Sorter(SortStrategy strategy) { this.strategy = strategy; }
    void setStrategy(SortStrategy strategy) { this.strategy = strategy; } // swappable at runtime
    void sortArray(int[] array) { strategy.sort(array); }
}

Sorter sorter = new Sorter(new BubbleSort());
sorter.sortArray(smallArray);
sorter.setStrategy(new QuickSort()); // swap algorithms without touching Sorter's own code
sorter.sortArray(bigArray);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sorter holding a reference to whichever SortStrategy is currently assigned, swappable between BubbleSort and QuickSort at runtime">
  <rect x="30" y="60" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Sorter</text>

  <rect x="280" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="350" y="41" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BubbleSort</text>

  <rect x="280" y="115" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="350" y="136" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">QuickSort</text>

  <line x1="170" y1="80" x2="280" y2="40" stroke="#79c0ff" stroke-dasharray="4" marker-end="url(#a)"/>
  <line x1="170" y1="90" x2="280" y2="130" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="230" y="60" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">swapped to</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Sorter` holds a reference to one `SortStrategy` at a time, and that reference can be reassigned to a different implementation without changing `Sorter`'s own code.

## 5. Runnable example

Scenario: a checkout system supporting multiple discount strategies, evolving from a hardcoded branching method into swappable, independently-testable strategy classes.

### Level 1 — Basic

```java
// File: StrategyBasic.java
public class StrategyBasic {
    static double applyDiscount(String strategyName, double total) {
        return switch (strategyName) {
            case "NONE" -> total;
            case "TEN_PERCENT" -> total * 0.90;
            case "FLAT_FIVE" -> total - 5.0;
            default -> throw new IllegalArgumentException("unknown strategy: " + strategyName);
        };
    }

    public static void main(String[] args) {
        System.out.println(applyDiscount("TEN_PERCENT", 100.0));
        System.out.println(applyDiscount("FLAT_FIVE", 100.0));
    }
}
```

**How to run:** save as `StrategyBasic.java`, then `javac StrategyBasic.java && java StrategyBasic` (JDK 17+).

Expected output:
```
90.0
95.0
```

Every discount rule lives inline in one `switch` — adding a new discount, or testing one discount rule in isolation from the others, means editing (and re-verifying) this one shared method.

### Level 2 — Intermediate

```java
// File: StrategyIntermediate.java
interface DiscountStrategy {
    double apply(double total);
}

class NoDiscount implements DiscountStrategy {
    public double apply(double total) { return total; }
}
class TenPercentDiscount implements DiscountStrategy {
    public double apply(double total) { return total * 0.90; }
}
class FlatFiveDiscount implements DiscountStrategy {
    public double apply(double total) { return total - 5.0; }
}

class Checkout {
    private DiscountStrategy strategy;
    Checkout(DiscountStrategy strategy) { this.strategy = strategy; }
    void setStrategy(DiscountStrategy strategy) { this.strategy = strategy; }
    double total(double amount) { return strategy.apply(amount); }
}

public class StrategyIntermediate {
    public static void main(String[] args) {
        Checkout checkout = new Checkout(new TenPercentDiscount());
        System.out.println(checkout.total(100.0));

        checkout.setStrategy(new FlatFiveDiscount()); // swap at runtime
        System.out.println(checkout.total(100.0));
    }
}
```

**How to run:** save as `StrategyIntermediate.java`, then `javac StrategyIntermediate.java && java StrategyIntermediate` (JDK 17+).

Expected output:
```
90.0
95.0
```

The real-world concern added: each discount rule is its own class, independently testable, and `Checkout` never changes when a discount rule is added, removed, or swapped — it only ever calls `strategy.apply(amount)`.

### Level 3 — Advanced

```java
// File: StrategyAdvanced.java
import java.util.function.DoubleUnaryOperator;

interface DiscountStrategy {
    double apply(double total);
}

class NoDiscount implements DiscountStrategy {
    public double apply(double total) { return total; }
}
class TenPercentDiscount implements DiscountStrategy {
    public double apply(double total) { return total * 0.90; }
}

// A strategy chosen dynamically based on runtime context (loyalty tier),
// not just picked once and held statically -- the decision itself is data-driven.
class LoyaltyTierDiscount implements DiscountStrategy {
    private final int loyaltyPoints;
    LoyaltyTierDiscount(int loyaltyPoints) { this.loyaltyPoints = loyaltyPoints; }
    public double apply(double total) {
        DoubleUnaryOperator rule = loyaltyPoints >= 1000 ? t -> t * 0.80
                                  : loyaltyPoints >= 500  ? t -> t * 0.90
                                  : t -> t;
        return rule.applyAsDouble(total);
    }
}

class Checkout {
    private DiscountStrategy strategy;
    Checkout(DiscountStrategy strategy) { this.strategy = strategy; }
    void setStrategy(DiscountStrategy strategy) { this.strategy = strategy; }
    double total(double amount) { return strategy.apply(amount); }
}

public class StrategyAdvanced {
    static DiscountStrategy resolveStrategy(int loyaltyPoints) {
        return new LoyaltyTierDiscount(loyaltyPoints);
    }

    public static void main(String[] args) {
        Checkout checkout = new Checkout(new NoDiscount());

        checkout.setStrategy(resolveStrategy(1200)); // gold tier
        System.out.println("gold tier: " + checkout.total(100.0));

        checkout.setStrategy(resolveStrategy(600)); // silver tier
        System.out.println("silver tier: " + checkout.total(100.0));

        checkout.setStrategy(resolveStrategy(50)); // no tier
        System.out.println("no tier: " + checkout.total(100.0));
    }
}
```

**How to run:** save as `StrategyAdvanced.java`, then `javac StrategyAdvanced.java && java StrategyAdvanced` (JDK 17+).

Expected output:
```
gold tier: 80.0
silver tier: 90.0
no tier: 100.0
```

The production-flavored hard case: `LoyaltyTierDiscount` itself picks a sub-rule based on runtime data (`loyaltyPoints`), showing that a strategy can encapsulate a whole decision tree internally — `Checkout` still just calls `strategy.apply(total)`, unaware of how many sub-cases the current strategy actually has.

## 6. Walkthrough

Tracing `checkout.setStrategy(resolveStrategy(600))` followed by `checkout.total(100.0)`:

1. `resolveStrategy(600)` constructs `new LoyaltyTierDiscount(600)` and returns it.
2. `checkout.setStrategy(...)` replaces `Checkout`'s internal `strategy` field with this new `LoyaltyTierDiscount` instance — `Checkout` itself has no idea what kind of discount logic it now holds, only that it satisfies `DiscountStrategy`.
3. `checkout.total(100.0)` calls `strategy.apply(100.0)`, dispatching to `LoyaltyTierDiscount.apply`.
4. Inside, the ternary chain evaluates `loyaltyPoints >= 1000` first: `600 >= 1000` is `false`. It then evaluates `loyaltyPoints >= 500`: `600 >= 500` is `true`, so `rule` is set to the lambda `t -> t * 0.90`.
5. `rule.applyAsDouble(100.0)` computes `100.0 * 0.90 = 90.0`, which `LoyaltyTierDiscount.apply` returns.
6. `checkout.total` returns that `90.0` up to `main`, which prints `"silver tier: 90.0"`. Note `Checkout.total`'s own code never branched on loyalty points at all — all of that decision-making happened entirely inside the strategy object it was handed.

## 7. Gotchas & takeaways

> **Gotcha:** Strategy and [State](1012-state.md) look almost identical in code (both hold a swappable object implementing an interface), but their intent differs: Strategy is about the *caller* choosing which algorithm to use; State is about the *object itself* changing its own behavior as it transitions between internal states, often without the caller choosing or even knowing.

- Strategy encapsulates each interchangeable algorithm behind a shared interface, letting calling code swap between them without changing its own logic.
- The classic sign a `switch`/`if` chain should become a Strategy: it's picking among several conceptually equal alternatives (different discount rules, different sort algorithms) rather than branching on unrelated logic.
- A strategy object can itself contain further decision logic internally — the caller only sees the single shared interface method.
- Lambdas and method references often replace tiny strategy classes in modern Java when the strategy interface has exactly one abstract method (a functional interface).
- Don't introduce Strategy for a single, fixed algorithm with no plausible alternative — that's just a plain method.
- Strategy is one of the most common ways [SOLID — Open/Closed](0990-solid-open-closed.md) gets implemented in practice: new algorithms are added as new classes, and the code using them never needs modification.
