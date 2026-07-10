---
card: java
gi: 841
slug: natural-ordering-vs-custom
title: natural ordering vs custom
---

## 1. What it is

"Natural ordering" refers to the single default sort order a type declares for itself by implementing [`Comparable`](0838-comparable-compareto.md) — the order `Collections.sort(list)` or `list.sort(null)` uses when no comparator is supplied. "Custom ordering" refers to any [`Comparator`](0839-comparator-compare.md) supplied externally at the call site, which **overrides** natural ordering for that specific sort or that specific `TreeMap`/`TreeSet` instance, without altering the type's own `compareTo` implementation at all. A single type can have exactly one natural ordering but an unlimited number of custom orderings, each used wherever it's explicitly supplied.

## 2. Why & when

The choice between relying on natural ordering and supplying a custom comparator comes down to a simple question: is there one obviously "default" way to sort this data that most callers would expect without being told otherwise, or does the right order genuinely depend on context? A `LocalDate`'s natural ordering (chronological) is obviously the default everyone expects; sorting a list of `Employee` objects has no single obvious default (by name? by salary? by hire date?), so it's a better candidate for always-explicit custom comparators, or no `Comparable` implementation at all. Understanding that a custom comparator always overrides natural ordering **only for the specific call it's passed to** — never modifying the type itself — is what makes it safe to sort the exact same list of `Comparable` objects one way in one part of a program and a completely different way elsewhere, without any conflict.

## 3. Core concept

```java
List<String> words = new ArrayList<>(List.of("Banana", "apple", "Cherry"));

Collections.sort(words); // natural ordering: String's compareTo, which is case-sensitive
System.out.println(words); // [Banana, Cherry, apple] -- uppercase sorts before lowercase in Unicode

Collections.sort(words, String.CASE_INSENSITIVE_ORDER); // custom ordering, overriding natural ordering for THIS call only
System.out.println(words); // [apple, Banana, Cherry] -- alphabetical regardless of case

// String itself is completely unchanged by either call -- its compareTo still behaves exactly as before:
System.out.println("Banana".compareTo("apple")); // still negative (case-sensitive), unaffected by the sort calls above
```

Supplying `String.CASE_INSENSITIVE_ORDER` to `Collections.sort` doesn't modify `String`'s natural ordering in any way — it's a completely separate, external `Comparator` object that happens to produce a different result for these particular strings, used only for this one call.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same list of Comparable objects can be sorted by natural ordering in one call and by a completely different custom comparator in another call, without the type itself ever changing">
  <rect x="240" y="15" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">List&lt;String&gt; (unchanged)</text>

  <line x1="280" y1="55" x2="160" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a841)"/>
  <line x1="360" y1="55" x2="480" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a841)"/>

  <rect x="60" y="100" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sort(list) -- natural order</text>
  <text x="160" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Comparable.compareTo</text>

  <rect x="380" y="100" width="200" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="122" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sort(list, comparator)</text>
  <text x="480" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">external Comparator, this call only</text>
</svg>

*Natural ordering lives inside the type permanently; a custom comparator overrides it only for the specific call it's passed to.*

## 5. Runnable example

Scenario: a product catalog needing both a "default" listing order and several report-specific custom orderings, growing from relying on natural ordering, to overriding it per call with a custom comparator, to a utility method that gracefully falls back to natural ordering when no custom comparator is supplied.

### Level 1 — Basic

```java
import java.util.*;

public class CatalogNaturalOrder {
    record Product(String sku, double price) implements Comparable<Product> {
        @Override public int compareTo(Product other) { return this.sku.compareTo(other.sku); } // natural: by SKU
    }

    public static void main(String[] args) {
        List<Product> catalog = new ArrayList<>(List.of(
            new Product("SKU-042", 19.99), new Product("SKU-007", 49.99), new Product("SKU-100", 9.99)
        ));

        Collections.sort(catalog); // uses Product's natural ordering: by SKU
        catalog.forEach(p -> System.out.println(p.sku() + ": $" + p.price()));
    }
}
```

**How to run:** `java CatalogNaturalOrder.java` (JDK 17+).

Expected output:
```
SKU-007: $49.99
SKU-042: $19.99
SKU-100: $9.99
```

`Product` declares SKU-based natural ordering as its one canonical default — reasonable, since SKU is a stable, unique identifier most catalog views would sensibly default to.

### Level 2 — Intermediate

```java
import java.util.*;

public class CatalogCustomOverride {
    record Product(String sku, double price) implements Comparable<Product> {
        @Override public int compareTo(Product other) { return this.sku.compareTo(other.sku); }
    }

    public static void main(String[] args) {
        List<Product> catalog = new ArrayList<>(List.of(
            new Product("SKU-042", 19.99), new Product("SKU-007", 49.99), new Product("SKU-100", 9.99)
        ));

        // A "cheapest first" report -- overrides natural ordering for THIS call only.
        List<Product> cheapestFirst = new ArrayList<>(catalog);
        cheapestFirst.sort(Comparator.comparingDouble(Product::price));
        System.out.println("cheapest-first report:");
        cheapestFirst.forEach(p -> System.out.println("  " + p.sku() + ": $" + p.price()));

        // The ORIGINAL list is completely unaffected by the custom sort above.
        System.out.println("original catalog list, still in natural (SKU) order: ");
        catalog.forEach(p -> System.out.println("  " + p.sku() + ": $" + p.price()));
    }
}
```

**How to run:** `java CatalogCustomOverride.java`.

Expected output:
```
cheapest-first report:
  SKU-100: $9.99
  SKU-042: $19.99
  SKU-007: $49.99
original catalog list, still in natural (SKU) order: 
  SKU-042: $19.99
  SKU-007: $49.99
  SKU-100: $9.99
```

The real-world concern added: proving that supplying a custom comparator to sort a *copy* of the list (`cheapestFirst`) doesn't touch the original `catalog` list at all — the original retains whatever order it already had (in this case, unsorted insertion order, since it was never sorted by natural ordering in this version), and `Product`'s `compareTo` method itself is completely unaffected by having been bypassed for the price-based sort.

### Level 3 — Advanced

```java
import java.util.*;

public class FlexibleSortUtility {
    record Product(String sku, double price) implements Comparable<Product> {
        @Override public int compareTo(Product other) { return this.sku.compareTo(other.sku); }
    }

    // A utility accepting an OPTIONAL custom comparator -- falls back to natural ordering if none is given.
    static <T extends Comparable<T>> List<T> sortedCopy(List<T> source, Comparator<T> customOrderingOrNull) {
        List<T> copy = new ArrayList<>(source);
        Comparator<T> ordering = (customOrderingOrNull != null) ? customOrderingOrNull : Comparator.naturalOrder();
        copy.sort(ordering);
        return copy;
    }

    public static void main(String[] args) {
        List<Product> catalog = List.of(
            new Product("SKU-042", 19.99), new Product("SKU-007", 49.99), new Product("SKU-100", 9.99)
        );

        List<Product> defaultReport = sortedCopy(catalog, null); // falls back to natural ordering
        System.out.println("default report (natural order, by SKU):");
        defaultReport.forEach(p -> System.out.println("  " + p.sku()));

        List<Product> priceReport = sortedCopy(catalog, Comparator.comparingDouble(Product::price));
        System.out.println("price report (custom order):");
        priceReport.forEach(p -> System.out.println("  " + p.sku() + ": $" + p.price()));
    }
}
```

**How to run:** `java FlexibleSortUtility.java`.

Expected output:
```
default report (natural order, by SKU):
  SKU-007
  SKU-042
  SKU-100
price report (custom order):
  SKU-100
  SKU-042
  SKU-007
```

This adds the production-flavored hard case: a genuinely reusable utility method that accepts an *optional* comparator, using `Comparator.naturalOrder()` (which itself calls the type's own `compareTo` internally) as the fallback whenever no custom ordering is supplied — the `T extends Comparable<T>` bound is required specifically so `Comparator.naturalOrder()` is guaranteed to be valid for whatever type `T` turns out to be. This pattern — "use natural ordering by default, but let the caller override it" — is exactly how much of the JDK's own API (like `TreeSet`'s constructors) is designed.

## 6. Walkthrough

Tracing `FlexibleSortUtility.main`'s two calls to `sortedCopy`:

1. `sortedCopy(catalog, null)` is called with `customOrderingOrNull = null`. Inside the method, the ternary expression `(customOrderingOrNull != null) ? customOrderingOrNull : Comparator.naturalOrder()` evaluates to `Comparator.naturalOrder()`, since the passed argument was `null`.
2. `Comparator.naturalOrder()` returns a `Comparator<T>` implemented internally to simply call `a.compareTo(b)` on the elements themselves — for `Product`, this delegates straight to `Product`'s own `compareTo` method, which compares by `sku`.
3. `copy.sort(ordering)` sorts the defensive copy using that natural-ordering comparator, producing `SKU-007, SKU-042, SKU-100` — identical to what `Collections.sort(copy)` (with no comparator argument at all) would have produced, since both paths ultimately invoke the same `compareTo` logic.
4. `sortedCopy(catalog, Comparator.comparingDouble(Product::price))` is called with a genuine custom comparator this time. The ternary now evaluates to that supplied comparator directly, bypassing `Product`'s `compareTo` entirely for this call.
5. `copy.sort(ordering)` sorts a **fresh** defensive copy of `catalog` by price ascending — `SKU-100` ($9.99), `SKU-042` ($19.99), `SKU-007` ($49.99) — while the original `catalog` list (declared as an immutable `List.of(...)`) and the `Product` class's own `compareTo` implementation remain completely unaffected, exactly as the natural-ordering-vs-custom distinction guarantees.

## 7. Gotchas & takeaways

> **Gotcha:** a type's natural ordering and a custom comparator used for the *same* type should ideally agree on what counts as "equal" whenever both are used to key a [`TreeSet`](0819-treeset.md)/[`TreeMap`](0825-treemap-red-black-tree.md) — mixing a `TreeSet` built with natural ordering and another built with a custom comparator that disagrees on equality (as in the case-insensitive-string example) can produce genuinely different sets of "unique" elements from the same source data, which is sometimes exactly the intent (as with `String.CASE_INSENSITIVE_ORDER`) but should always be a deliberate choice, not an accident.

- Natural ordering (via [`Comparable`](0838-comparable-compareto.md)) is a type's single, built-in default sort order; a custom [`Comparator`](0839-comparator-compare.md) is supplied externally and overrides it only for the specific call or structure it's passed to.
- Supplying a custom comparator never modifies the type's `compareTo` implementation or affects any other code using natural ordering elsewhere.
- A single type can have any number of custom orderings coexisting for different purposes, but only ever one natural ordering.
- `Comparator.naturalOrder()` is the bridge between the two systems — it wraps a type's own `compareTo` as a first-class `Comparator` object, useful for utility methods that want to default to natural ordering while still accepting an optional override.
- Choose natural ordering for types with one obvious canonical default; prefer explicit custom comparators (or skip `Comparable` entirely) for types where the "right" order genuinely depends on context.
