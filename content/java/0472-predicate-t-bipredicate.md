---
card: java
gi: 472
slug: predicate-t-bipredicate
title: Predicate<T> / BiPredicate
---

## 1. What it is

`Predicate<T>` is the functional interface for "take one input of type `T`, answer a yes/no question about it." Its single abstract method is `boolean test(T t)`. `BiPredicate<T, U>` is its two-argument sibling: `boolean test(T t, U u)`. Where `Function<T, R>` transforms a value into something else, `Predicate` only ever produces a `boolean` — it exists specifically for filtering and conditional logic.

## 2. Why & when

A huge amount of everyday logic boils down to "does this value satisfy some condition?" — filtering a list down to matching elements, deciding whether to include an item, validating input. `Predicate<T>` gives that yes/no logic the same first-class, pass-around-as-a-value treatment other functional interfaces give their own shapes, and — because it's specifically typed to return `boolean` rather than a generic `R` — it comes with a set of `default` methods (`and`, `or`, `negate`) tailored exactly to combining conditions, which a generic `Function<T, Boolean>` would not offer.

You reach for `Predicate<T>` constantly: `Stream.filter(Predicate<T>)` is by far its most common use, keeping only elements that satisfy a condition. `Collection.removeIf(Predicate<T>)` removes elements that satisfy one. `BiPredicate<T, U>` is rarer, appearing when a yes/no question genuinely needs two related inputs — comparing two values for some custom relationship, or checking a key against a value together.

## 3. Core concept

```java
import java.util.function.*;

Predicate<String> isBlank = s -> s.trim().isEmpty();
boolean result = isBlank.test("   "); // true

Predicate<Integer> isPositive = n -> n > 0;
Predicate<Integer> isEven = n -> n % 2 == 0;

// Combine predicates with and/or/negate -- default methods built specifically for boolean logic
Predicate<Integer> isPositiveAndEven = isPositive.and(isEven);
System.out.println(isPositiveAndEven.test(4));  // true
System.out.println(isPositiveAndEven.test(-4)); // false: fails isPositive
System.out.println(isPositive.negate().test(4)); // false: 4 IS positive, so negate() flips it
```

`test` always returns `boolean` — this is `Predicate`'s defining trait, and exactly why its combinators (`and`, `or`, `negate`) can exist: they're only meaningful because the result type is always `boolean`.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Predicate takes one input and answers a boolean yes or no question about it">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <rect x="60" y="45" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="75" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">T input</text>

  <rect x="290" y="35" width="150" height="70" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="365" y="60" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Predicate&lt;T&gt;</text>
  <text x="365" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">test(t)</text>

  <rect x="500" y="45" width="110" height="50" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="555" y="75" fill="#f0883e" font-size="12" text-anchor="middle" font-family="monospace">true / false</text>

  <line x1="180" y1="70" x2="285" y2="70" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="440" y1="70" x2="495" y2="70" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="4" refY="7" orient="auto"><path d="M0,0 L8,0 L4,7 Z" fill="#8b949e"/></marker></defs>
</svg>

Always a `boolean` out — the trait that makes `and`/`or`/`negate` meaningful combinators.

## 5. Runnable example

Scenario: filtering a product catalog — evolved from a single `Predicate` used with `Stream.filter`, through combining multiple predicates with `and`/`or`/`negate` into richer conditions, to a `BiPredicate` checking a product against a customer's budget together.

### Level 1 — Basic

```java
import java.util.function.*;
import java.util.*;
import java.util.stream.*;

public class PredicateBasic {
    public static void main(String[] args) {
        List<Integer> prices = List.of(5, 25, 8, 50, 12, 3);

        Predicate<Integer> isAffordable = price -> price <= 10;

        List<Integer> affordable = prices.stream()
                .filter(isAffordable)
                .collect(Collectors.toList());

        System.out.println(affordable);
    }
}
```

**How to run:** `java PredicateBasic.java`

Expected output:
```
[5, 8, 3]
```

`Stream.filter(isAffordable)` calls `isAffordable.test(price)` on every element, keeping only those where `test` returns `true` — here, prices at or below `10`, in their original relative order.

### Level 2 — Intermediate

```java
import java.util.function.*;
import java.util.*;
import java.util.stream.*;

public class PredicateCombining {
    public static void main(String[] args) {
        List<Integer> prices = List.of(5, 25, 8, 50, 12, 3, 0, -2);

        Predicate<Integer> isPositive = price -> price > 0;
        Predicate<Integer> isAffordable = price -> price <= 10;

        // and/or/negate combine predicates into new ones -- no manual boolean-logic lambda needed.
        Predicate<Integer> isValidAndAffordable = isPositive.and(isAffordable);
        Predicate<Integer> isExpensiveOrInvalid = isAffordable.negate().or(isPositive.negate());

        List<Integer> goodDeals = prices.stream().filter(isValidAndAffordable).collect(Collectors.toList());
        List<Integer> flagged = prices.stream().filter(isExpensiveOrInvalid).collect(Collectors.toList());

        System.out.println("Good deals: " + goodDeals);
        System.out.println("Flagged: " + flagged);
    }
}
```

**How to run:** `java PredicateCombining.java`

Expected output:
```
Good deals: [5, 8, 3]
Flagged: [25, 50, 12, 0, -2]
```

The real-world concern this adds: rather than writing one large lambda mixing multiple conditions (`price -> price > 0 && price <= 10`), each condition is defined once as its own `Predicate` and then combined declaratively with `and`/`or`/`negate` — each piece stays independently readable and reusable, and the combination itself reads almost like the English description of the rule.

### Level 3 — Advanced

```java
import java.util.function.*;
import java.util.*;
import java.util.stream.*;

public class BiPredicateBudgetCheck {
    record Product(String name, double price) {}

    public static void main(String[] args) {
        List<Product> catalog = List.of(
                new Product("Notebook", 4.50),
                new Product("Headphones", 79.99),
                new Product("Pen", 1.20),
                new Product("Monitor", 199.99)
        );

        // BiPredicate: checks a Product AGAINST a budget together -- two related inputs, one boolean.
        BiPredicate<Product, Double> fitsWithinBudget = (product, budget) -> product.price() <= budget;

        double budget = 50.0;
        List<Product> affordable = catalog.stream()
                .filter(product -> fitsWithinBudget.test(product, budget))
                .collect(Collectors.toList());

        for (Product product : affordable) {
            System.out.println(product.name() + " ($" + product.price() + ") fits within $" + budget);
        }
    }
}
```

**How to run:** `java BiPredicateBudgetCheck.java`

Expected output:
```
Notebook ($4.5) fits within $50.0
Pen ($1.2) fits within $50.0
```

Here the yes/no question genuinely needs two independent inputs — the product and the budget — which a plain single-argument `Predicate<Product>` couldn't express on its own without capturing `budget` as an external variable. `BiPredicate<Product, Double>` makes both inputs explicit parameters, and `Stream.filter` (which only accepts a single-argument `Predicate`) adapts it via a wrapping lambda, `product -> fitsWithinBudget.test(product, budget)`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `catalog` holds four `Product` records. `fitsWithinBudget` is a `BiPredicate<Product, Double>`. `budget` is set to `50.0`.

`catalog.stream().filter(product -> fitsWithinBudget.test(product, budget))` processes each of the four products in order, calling the wrapping lambda for each. That lambda in turn calls `fitsWithinBudget.test(product, budget)`, which evaluates `product.price() <= budget`.

For `Notebook` (price `4.50`): `4.50 <= 50.0` is `true`, so it's kept. For `Headphones` (price `79.99`): `79.99 <= 50.0` is `false`, so it's filtered out. For `Pen` (price `1.20`): `1.20 <= 50.0` is `true`, kept. For `Monitor` (price `199.99`): `199.99 <= 50.0` is `false`, filtered out.

```
Notebook  (4.50)   <= 50.0 --> true  --> kept
Headphones(79.99)  <= 50.0 --> false --> dropped
Pen       (1.20)   <= 50.0 --> true  --> kept
Monitor   (199.99) <= 50.0 --> false --> dropped
```

`Collectors.toList()` gathers the surviving elements, in their original stream order, into `affordable`: `[Notebook, Pen]`. The `for` loop then prints one line per surviving product, showing its name, price, and the budget it fit within.

## 7. Gotchas & takeaways

> `Predicate.equals(target)` (a `static` factory method, distinct from the `test` method) returns a `Predicate` that checks equality against a specific target value — but it's easy to confuse with calling `.equals()` on the predicate object itself, which compares predicate *identity*, not the values they test. If you want "does this equal X" as a filter condition, prefer a direct lambda like `value -> value.equals(x)` for clarity over the less-obvious `Predicate.isEqual(x)` factory.

- `Predicate<T>` represents "one input, one boolean answer" — its single abstract method is `boolean test(T t)`.
- `BiPredicate<T, U>` is the two-argument version — `boolean test(T t, U u)` — for yes/no questions genuinely needing two related inputs.
- `and`, `or`, and `negate` are `default` methods that combine predicates into new ones, letting you build complex conditions declaratively out of small, independently readable pieces.
- `Stream.filter(Predicate<T>)` and `Collection.removeIf(Predicate<T>)` are the most common places `Predicate` appears in everyday code.
- Prefer several small, named predicates combined with `and`/`or`/`negate` over one large lambda mixing multiple conditions — it keeps each condition independently testable and the combined logic easy to read.
