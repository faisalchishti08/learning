---
card: java
gi: 95
slug: shadowing-of-variables
title: Shadowing of variables
---

## 1. What it is

Shadowing occurs when a variable declared in an inner scope uses the same name as a variable in an enclosing scope, making the outer variable inaccessible by name within the inner scope. In Java:

- A **local variable** or **parameter** can shadow an **instance field** or **static field** — the field is still accessible via `this.name` or `ClassName.name`.
- A **method parameter** shadows a **field** when they share the same name — the canonical use case is constructor parameter assignments: `this.name = name`.
- A local variable in a **subclass method** cannot shadow a local of the same name in a superclass method (different frames — not a shadowing scenario at all).
- A **local variable cannot shadow another local** in an enclosing block of the *same method* — the compiler rejects it.

```java
class Example {
    int x = 10;              // instance field

    void demo(int x) {       // parameter x shadows field x
        System.out.println(x);       // 5 (parameter)
        System.out.println(this.x);  // 10 (field, unambiguous via this)
        int y = 1;
        {
            // int y = 2;  // ILLEGAL — y already in scope in enclosing block
        }
    }
}
```

## 2. Why & when

Shadowing is intentional in constructors and setters, where parameter names mirror field names. It becomes a **bug source** when the shadowing is accidental — a loop variable named `count` masking an outer `count` field, producing silent wrong behaviour without a compile error. Understanding shadowing rules lets you:
- Write idiomatic constructors without awkward `_name` or `name_` conventions.
- Avoid accidental shadowing in large methods where a local might mask a field.
- Read unfamiliar code without assuming a name refers to the most visible field.

## 3. Core concept

```java
public class ShadowingDemo {

    // Instance fields
    String name   = "ShadowingDemo";
    int    count  = 42;

    // Static field
    static int MAX = 100;

    // Constructor: parameter 'name' intentionally shadows field 'name'
    ShadowingDemo(String name) {
        this.name = name;   // this.name = field; name = parameter
    }

    void show(int count) {
        // Parameter 'count' shadows instance field 'count'
        System.out.println(count);       // 7 (parameter)
        System.out.println(this.count);  // 42 (field)

        // Local variable shadows static field MAX
        int MAX = 50;                   // local MAX shadows static MAX
        System.out.println(MAX);        // 50 (local)
        System.out.println(ShadowingDemo.MAX);  // 100 (class-qualified static)

        // ILLEGAL: shadowing a local with another local in inner block
        int x = 1;
        {
            // int x = 2;  // COMPILE ERROR: variable x is already defined
        }
    }

    // Method in subclass can have the same local names — different stack frames
    static class Sub extends ShadowingDemo {
        Sub() { super("sub"); }
        void show(int count) {
            // count here is a parameter of Sub.show — no conflict with parent's count
            super.show(count * 2);
        }
    }

    public static void main(String[] args) {
        ShadowingDemo d = new ShadowingDemo("hello");
        d.show(7);
        new Sub().show(3);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three shadowing scenarios: parameter shadows field (this.name resolves field), local shadows static (ClassName.MAX resolves static), illegal inner local shadows outer local (compile error)">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Shadowing scenarios — how to disambiguate each case</text>

  <!-- Scenario 1: parameter shadows field -->
  <rect x="16" y="32" width="210" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="121" y="48" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Parameter shadows field</text>
  <text x="24" y="64" fill="#8b949e" font-size="7.5" font-family="monospace">String name = "field";</text>
  <text x="24" y="78" fill="#8b949e" font-size="7.5" font-family="monospace">void set(String name) {</text>
  <text x="32" y="92" fill="#e6edf3" font-size="7.5" font-family="monospace">name → parameter</text>
  <text x="32" y="106" fill="#6db33f" font-size="7.5" font-family="monospace">this.name → field</text>
  <text x="24" y="120" fill="#8b949e" font-size="7.5" font-family="monospace">}</text>
  <text x="24" y="138" fill="#8b949e" font-size="7" font-family="sans-serif">Disambiguate: this.name</text>
  <text x="24" y="152" fill="#8b949e" font-size="7" font-family="sans-serif">Idiomatic in constructors</text>
  <text x="24" y="164" fill="#6db33f" font-size="7" font-family="sans-serif">Allowed</text>

  <!-- Scenario 2: local shadows static -->
  <rect x="238" y="32" width="210" height="140" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="343" y="48" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">Local shadows static</text>
  <text x="246" y="64" fill="#8b949e" font-size="7.5" font-family="monospace">static int MAX = 100;</text>
  <text x="246" y="78" fill="#8b949e" font-size="7.5" font-family="monospace">void demo() {</text>
  <text x="254" y="92" fill="#e6edf3" font-size="7.5" font-family="monospace">int MAX = 50; // shadows</text>
  <text x="254" y="106" fill="#e6edf3" font-size="7.5" font-family="monospace">MAX → 50 (local)</text>
  <text x="254" y="120" fill="#79c0ff" font-size="7.5" font-family="monospace">Foo.MAX → 100</text>
  <text x="246" y="134" fill="#8b949e" font-size="7.5" font-family="monospace">}</text>
  <text x="246" y="148" fill="#8b949e" font-size="7" font-family="sans-serif">Disambiguate: ClassName.MAX</text>
  <text x="246" y="163" fill="#79c0ff" font-size="7" font-family="sans-serif">Allowed (but avoid)</text>

  <!-- Scenario 3: illegal inner local -->
  <rect x="460" y="32" width="226" height="140" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="573" y="48" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Inner local shadows outer local</text>
  <text x="468" y="64" fill="#8b949e" font-size="7.5" font-family="monospace">void demo() {</text>
  <text x="476" y="78" fill="#e6edf3" font-size="7.5" font-family="monospace">int x = 1;</text>
  <text x="476" y="92" fill="#8b949e" font-size="7.5" font-family="monospace">{</text>
  <text x="484" y="106" fill="#8b949e" font-size="7.5" font-family="monospace">int x = 2; // ERROR</text>
  <text x="476" y="120" fill="#8b949e" font-size="7.5" font-family="monospace">}</text>
  <text x="468" y="134" fill="#8b949e" font-size="7.5" font-family="monospace">}</text>
  <text x="468" y="148" fill="#8b949e" font-size="7" font-family="sans-serif">No disambiguation possible</text>
  <text x="468" y="163" fill="#8b949e" font-size="7" font-family="sans-serif">COMPILE ERROR</text>
</svg>

Parameter/local → field shadowing is allowed and disambiguated with `this.` or `ClassName.`. Local → local shadowing within the same method is illegal.

## 5. Runnable example

Scenario: an inventory management system with a `Product` class — shadowing appears in the constructor (parameter mirrors field), in a bulk-price method (local variable masks a field used for default pricing), and in a utility class (static field shadowed by a loop variable, intentionally to scope the constant narrowly).

### Level 1 — Basic

```java
public class ShadowingBasic {

    String name;    // field
    double price;   // field

    // Parameter 'name' and 'price' shadow fields — idiomatic Java constructor
    ShadowingBasic(String name, double price) {
        this.name  = name;    // this.name = field; name = parameter
        this.price = price;
    }

    void display() {
        System.out.printf("  %-10s $%.2f%n", name, price);
    }

    // Method parameter 'price' shadows field 'price' — accessing both
    void applyDiscount(double price) {
        // 'price' here is the discount rate, not the product price
        System.out.printf("  %-10s: original=$%.2f  after %.0f%% discount=$%.2f%n",
            name, this.price, price * 100, this.price * (1 - price));
    }

    public static void main(String[] args) {
        ShadowingBasic apple = new ShadowingBasic("Apple", 0.99);
        ShadowingBasic bread = new ShadowingBasic("Bread", 2.49);

        System.out.println("Prices:");
        apple.display();
        bread.display();

        System.out.println("Discounts:");
        apple.applyDiscount(0.10);
        bread.applyDiscount(0.20);
    }
}
```

**How to run:** `java ShadowingBasic.java`

In the constructor, `name` refers to the parameter and `this.name` refers to the instance field. In `applyDiscount`, `price` is the discount rate (the parameter) and `this.price` is the product price (the field). Without `this.`, both `name` and `price` would resolve to the parameter, silently ignoring the field — a common and hard-to-spot bug when the `this.` qualification is forgotten on the left-hand side of the assignment.

### Level 2 — Intermediate

Same system: a `Warehouse` class with a static `DEFAULT_MARKUP` field, shadowed inside a pricing method by a local variable of the same name to apply a different markup for a category.

```java
public class ShadowingIntermediate {

    // Static field — class-wide default
    static double DEFAULT_MARKUP = 0.20;   // 20% markup

    String category;
    double costPrice;

    ShadowingIntermediate(String category, double costPrice) {
        this.category  = category;
        this.costPrice = costPrice;
    }

    double sellPrice() {
        // Local 'DEFAULT_MARKUP' shadows static field within this method
        double DEFAULT_MARKUP = switch (category) {
            case "perishable" -> 0.10;   // thin margin
            case "luxury"     -> 0.50;   // high margin
            default           -> ShadowingIntermediate.DEFAULT_MARKUP;  // class static
        };
        // Within this method: DEFAULT_MARKUP = local (category-specific)
        // Class-wide:         ShadowingIntermediate.DEFAULT_MARKUP = 0.20

        return costPrice * (1 + DEFAULT_MARKUP);
    }

    @Override public String toString() {
        return String.format("%-12s cost=$%.2f  sell=$%.2f  markup=%.0f%%",
            category, costPrice, sellPrice(),
            (sellPrice() / costPrice - 1) * 100);
    }

    public static void main(String[] args) {
        ShadowingIntermediate[] items = {
            new ShadowingIntermediate("perishable", 1.00),
            new ShadowingIntermediate("luxury",     50.00),
            new ShadowingIntermediate("general",    10.00)
        };

        System.out.printf("Global DEFAULT_MARKUP = %.0f%%%n",
            DEFAULT_MARKUP * 100);  // static field — 20%

        System.out.println("Item pricing:");
        for (var item : items) {
            System.out.println("  " + item);
        }
    }
}
```

**How to run:** `java ShadowingIntermediate.java`

Inside `sellPrice()`, the local variable `DEFAULT_MARKUP` shadows the static field. The local is computed from the `switch` expression and used for the final price calculation. The static `DEFAULT_MARKUP` is accessed via `ShadowingIntermediate.DEFAULT_MARKUP` in the `default` arm of the switch, which reads through the shadow. After `sellPrice()` returns, the local `DEFAULT_MARKUP` no longer exists — the static field is unaffected. This pattern is valid but risky: renaming the local would be clearer (e.g., `markup`).

### Level 3 — Advanced

Same system: subclass shadowing (a `DiscountedProduct` extends `ShadowingAdvancedBase`), a builder with a fluent API where every setter parameter shadows the corresponding field, and a loop variable that incidentally shares a name with an outer variable — showing all shadowing forms together.

```java
import java.util.*;

public class ShadowingAdvanced {

    // ---- base product ----
    static class Product {
        String name;
        double basePrice;
        List<String> tags;

        // All constructor parameters shadow fields — idiomatic
        Product(String name, double basePrice, List<String> tags) {
            this.name      = name;
            this.basePrice = basePrice;
            this.tags      = new ArrayList<>(tags);
        }

        double effectivePrice() { return basePrice; }

        @Override public String toString() {
            return String.format("%-12s $%.2f  tags=%s", name, effectivePrice(), tags);
        }
    }

    // ---- subclass ----
    static class DiscountedProduct extends Product {
        double discount;   // field in subclass

        DiscountedProduct(String name, double basePrice, double discount, List<String> tags) {
            super(name, basePrice, tags);
            this.discount = discount;
        }

        @Override double effectivePrice() {
            return basePrice * (1 - discount);
        }

        // Parameter 'discount' shadows field 'discount'
        void setDiscount(double discount) {
            this.discount = discount;
        }
    }

    // ---- builder with shadowing setters ----
    static class ProductBuilder {
        private String name      = "unnamed";
        private double basePrice = 0.0;
        private List<String> tags = new ArrayList<>();

        // Each setter parameter shadows the corresponding field
        ProductBuilder name(String name)           { this.name = name; return this; }
        ProductBuilder price(double basePrice)     { this.basePrice = basePrice; return this; }
        ProductBuilder tag(String tag)             { this.tags.add(tag); return this; }

        Product build() { return new Product(name, basePrice, tags); }
    }

    public static void main(String[] args) {
        // Builder: each method call has a parameter shadowing a field
        Product p1 = new ProductBuilder()
            .name("Organic Apple")
            .price(1.49)
            .tag("fruit").tag("organic")
            .build();

        DiscountedProduct p2 = new DiscountedProduct("Premium Bread", 3.99, 0.15,
            List.of("bakery", "premium"));

        List<Product> catalog = List.of(p1, p2);
        System.out.println("Catalog:");
        catalog.forEach(p -> System.out.println("  " + p));

        // Loop variable 'p' shadows outer variable 'p' from above scope?
        // No — p1 and p2 are in main scope, 'p' in the lambda is a lambda parameter.
        // Lambda parameters can shadow outer locals — separate scope.
        double total = 0.0;
        for (Product p : catalog) {    // loop variable 'p' — fine, no conflict
            total += p.effectivePrice();
        }
        System.out.printf("Total: $%.2f%n", total);

        // Explicit demo: lambda parameter shadowing outer variable
        String label = "item";
        catalog.forEach(p -> {
            // 'p' here is the lambda parameter — shadows nothing named 'p' in outer scope
            // 'label' is captured (effectively final) — not shadowed
            System.out.printf("  [%s] %s%n", label, p.name);
        });
    }
}
```

**How to run:** `java ShadowingAdvanced.java`

In `ProductBuilder`, every setter method has a parameter name identical to the private field — `this.name = name`, `this.basePrice = basePrice`. This is the canonical Java builder pattern. In `DiscountedProduct.setDiscount(double discount)`, the parameter `discount` shadows the field `discount`. The loop variable `p` in `for (Product p : catalog)` does not conflict with `p1`/`p2` because those are different names. Lambda parameters (like `p ->`) are in their own scope and can shadow outer locals, though they cannot shadow effectively-final variables in the enclosing method for capture purposes.

## 6. Walkthrough

Trace through `ProductBuilder` and `DiscountedProduct.setDiscount`:

**Builder chain `.name("Organic Apple")`.** Call enters `ProductBuilder.name(String name)`. Inside the method body, `name` resolves to the **parameter** (value `"Organic Apple"`). `this.name` resolves to the **field** (initially `"unnamed"`). The assignment `this.name = name` sets the field to `"Organic Apple"`. Without `this.`, the statement `name = name` would be a no-op (parameter assigned to itself), leaving the field unchanged — the classic shadowing bug in constructors.

**`DiscountedProduct.setDiscount(0.20)`.** Parameter `discount = 0.20` shadows field `discount` (currently `0.15`). Inside the method: `discount` → parameter (0.20); `this.discount` → field. After `this.discount = discount`, the field is updated to `0.20`.

```
Name resolution in ProductBuilder.name(String name):
  Lookup 'name':
    local variables:         none
    parameters:              'name' (String) ← FOUND HERE — stops search
    (field 'name' shadowed, not reached by plain 'name')
  Lookup 'this.name':
    explicit this qualifier  → resolves to instance field 'name'
```

## 7. Gotchas & takeaways

> **Forgetting `this.` in a constructor or setter turns an assignment into a no-op.** `name = name` assigns the parameter to itself and leaves the field unchanged. This compiles without warning and can be very hard to debug. Always use `this.field = param` when they share a name.

> **A local variable cannot shadow another local in an enclosing block of the same method.** Unlike C and C++, Java makes this a compile error. But a local *can* shadow a field — the compiler only warns, not errors (and even warnings depend on IDE settings).

- Parameter or local → field: **allowed**; disambiguate with `this.name` (instance) or `ClassName.name` (static).
- Local → local in enclosing block of same method: **illegal**, compile error.
- Lambda parameter → outer local: **allowed**; the lambda parameter is in its own scope.
- Forgetting `this.` when a parameter shadows a field produces a silent self-assignment bug — the most dangerous form.
- In constructors and builders, intentional shadowing (`String name` parameter with `this.name = name`) is idiomatic and preferred over `_name` naming conventions.
- Use a linter or IDE warning for "field shadowed by local/parameter" to catch accidental shadowing in non-constructor code.
