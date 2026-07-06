---
card: java
gi: 215
slug: getters-setters
title: Getters & setters
---

## 1. What it is

A **getter** is a method (conventionally named `getFieldName()`, or `isFieldName()` for a `boolean`) that returns a field's current value; a **setter** is a method (conventionally `setFieldName(value)`) that assigns a new value to a field, typically after validating it. Together, getters and setters are the standard, idiomatic mechanism for exposing controlled access to `private` fields — the concrete technique that makes encapsulation (the previous topic) practical in everyday Java code.

```java
class Person {
    private String name;
    private int age;

    String getName() { return name; } // getter: read access
    void setName(String name) { this.name = name; } // setter: write access

    int getAge() { return age; }
    void setAge(int age) {
        if (age < 0) throw new IllegalArgumentException("Age cannot be negative: " + age);
        this.age = age;
    }
}
```

`getAge()` and `setAge(int)` follow the standard naming convention (`get`/`set` prefix plus the capitalized field name) that many tools, frameworks, and IDEs recognize automatically — this convention is so widely followed that libraries like JavaBeans, many serialization frameworks, and IDE code generators specifically expect and rely on it.

## 2. Why & when

Getters and setters exist to provide controlled, named access points to a class's private state, giving the class author a place to add logic without changing the field's external access pattern:

- **Validation in setters** — a setter can reject invalid values (as `setAge` does above), a guarantee impossible with direct public field access.
- **Computed or lazy values in getters** — a getter isn't required to just return a stored field verbatim; it can compute a derived value on the fly, or trigger some side effect (like lazily initializing a value the first time it's requested), all while looking identical to a simple field access from the caller's perspective.
- **A stable interface even if internal representation changes** — if a class later needs to change how a value is stored internally (say, switching from storing Fahrenheit to storing Celsius internally), the getter and setter method signatures can stay exactly the same, converting internally, so no calling code needs to change at all.

You write getters and setters specifically for fields that genuinely need controlled external access — not automatically for every field, since some fields might reasonably need no external access at all (staying entirely private, with all logic internal to the class), while others might need only a getter (read-only from outside) with no corresponding setter.

## 3. Core concept

```java
class Temperature {
    private double celsius;

    double getCelsius() {
        return celsius;
    }

    void setCelsius(double celsius) {
        if (celsius < -273.15) throw new IllegalArgumentException("Below absolute zero");
        this.celsius = celsius;
    }

    double getFahrenheit() { // a getter with NO corresponding field or setter — purely computed
        return celsius * 9.0 / 5.0 + 32.0;
    }

    void setFahrenheit(double fahrenheit) { // a setter that converts and delegates to setCelsius
        setCelsius((fahrenheit - 32.0) * 5.0 / 9.0); // reuses the SAME validation, via setCelsius
    }
}
```

`getFahrenheit()` has no backing `fahrenheit` field at all — it's computed fresh from `celsius` every time it's called; `setFahrenheit(...)` converts its input and delegates to `setCelsius`, which means the exact same absolute-zero validation applies whether temperature is set in Celsius or Fahrenheit, with no duplicated logic anywhere.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A private celsius field accessible through a getter that returns its value directly and a setter that validates before assigning, plus a second getter for Fahrenheit that computes its result on the fly with no backing field of its own">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="230" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="310" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">private celsius 🔒</text>

  <line x1="230" y1="45" x2="120" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gs)"/>
  <text x="90" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">getCelsius()</text>
  <text x="90" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">setCelsius(v) — validates</text>

  <line x1="390" y1="45" x2="500" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#gs)"/>
  <text x="530" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getFahrenheit()</text>
  <text x="530" y="85" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">(computed, no field)</text>

  <text x="300" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Getters can compute derived values; setters can validate and delegate — both look like simple access from outside.</text>

  <defs><marker id="gs" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Getters and setters can hide validation and computed logic behind what looks, to callers, like plain field access.

## 5. Runnable example

Scenario: a small `Product` class in an online store — starting with basic getters and setters, then extending with a validating setter and a computed getter, then hardening into a class demonstrating a read-only property (getter only, no setter) protecting an invariant that should never change after construction.

### Level 1 — Basic

```java
public class ProductBasic {
    static class Product {
        private String name;
        private double price;

        String getName() { return name; }
        void setName(String name) { this.name = name; }

        double getPrice() { return price; }
        void setPrice(double price) { this.price = price; }
    }

    public static void main(String[] args) {
        Product p = new Product();
        p.setName("Coffee Mug");
        p.setPrice(12.99);

        System.out.println(p.getName() + ": $" + p.getPrice());
    }
}
```

**How to run:** `java ProductBasic.java`

Both fields are `private`, accessible only through their corresponding getter and setter — this is the standard shape of a simple JavaBean-style class, though this basic version doesn't yet add any validation logic of its own.

### Level 2 — Intermediate

Same `Product`, now with a validating setter for `price` and a computed getter for a discounted price, demonstrating both key advantages of getters and setters together.

```java
public class ProductIntermediate {
    static class Product {
        private String name;
        private double price;
        private double discountPercent = 0;

        String getName() { return name; }
        void setName(String name) { this.name = name; }

        double getPrice() { return price; }
        void setPrice(double price) {
            if (price < 0) throw new IllegalArgumentException("Price cannot be negative: " + price);
            this.price = price;
        }

        void setDiscountPercent(double percent) {
            if (percent < 0 || percent > 100) throw new IllegalArgumentException("Invalid discount: " + percent);
            this.discountPercent = percent;
        }

        double getDiscountedPrice() { // computed getter — no backing field of its own
            return price * (1 - discountPercent / 100);
        }
    }

    public static void main(String[] args) {
        Product p = new Product();
        p.setName("Coffee Mug");
        p.setPrice(12.99);
        p.setDiscountPercent(20);

        System.out.println(p.getName() + ": $" + p.getDiscountedPrice()); // 20% off $12.99
    }
}
```

**How to run:** `java ProductIntermediate.java`

`setPrice` and `setDiscountPercent` both validate their inputs before assigning, and `getDiscountedPrice()` computes its result fresh from `price` and `discountPercent` every time it's called — there is no separate stored "discounted price" field to accidentally fall out of sync with the underlying values it depends on.

### Level 3 — Advanced

Same `Product`, now with a read-only property (`sku`, a stock-keeping unit identifier) that has only a getter and no setter — deliberately immutable after construction, protecting an identifier that should never change for the lifetime of a given product object.

```java
public class ProductAdvanced {
    static class Product {
        private final String sku; // set once, at construction — no setter exists at all
        private String name;
        private double price;

        Product(String sku, String name, double price) {
            if (sku == null || sku.isEmpty()) {
                throw new IllegalArgumentException("SKU is required");
            }
            this.sku = sku;
            setName(name);
            setPrice(price);
        }

        String getSku() { return sku; } // getter only — deliberately no setSku()

        String getName() { return name; }
        void setName(String name) {
            if (name == null || name.isEmpty()) throw new IllegalArgumentException("Name is required");
            this.name = name;
        }

        double getPrice() { return price; }
        void setPrice(double price) {
            if (price < 0) throw new IllegalArgumentException("Price cannot be negative: " + price);
            this.price = price;
        }
    }

    public static void main(String[] args) {
        Product p = new Product("SKU-1001", "Coffee Mug", 12.99);

        p.setName("Ceramic Coffee Mug"); // name CAN change after construction
        p.setPrice(14.99);                // price CAN change after construction

        System.out.println(p.getSku() + ": " + p.getName() + " - $" + p.getPrice());
        // p.setSku("SKU-9999"); // would NOT compile — no such method exists; sku is read-only by design
    }
}
```

**How to run:** `java ProductAdvanced.java`

`sku` is `final` and has only a getter — there is deliberately no `setSku` method at all, meaning the identifier assigned at construction can never be changed afterward by any code, anywhere; this is a common, intentional pattern: expose a getter without a corresponding setter specifically for properties that should be readable but permanently fixed once an object is created.

## 6. Walkthrough

Trace `new Product("SKU-1001", "Coffee Mug", 12.99)` followed by the two subsequent setter calls in `ProductAdvanced.main`:

**Construction.** `sku == null || sku.isEmpty()` — `"SKU-1001"` is neither — guard doesn't fire. `this.sku = "SKU-1001"`. `setName("Coffee Mug")` validates (`name` isn't null/empty) and assigns. `setPrice(12.99)` validates (`12.99 >= 0`) and assigns.

**`p.setName("Ceramic Coffee Mug")`.** Validates the new name isn't null/empty — it isn't — and reassigns `name`. `sku` remains completely untouched, since this setter has no way to reach it.

**`p.setPrice(14.99)`.** Validates `14.99 >= 0` — true — and reassigns `price`.

**Final read.** `p.getSku()` still returns `"SKU-1001"` (never changed since construction); `p.getName()` returns `"Ceramic Coffee Mug"` (updated); `p.getPrice()` returns `14.99` (updated).

```
construct: sku="SKU-1001" (final, set once), name="Coffee Mug", price=12.99
setName("Ceramic Coffee Mug"): name updated; sku untouched
setPrice(14.99): price updated; sku untouched

final state: sku="SKU-1001", name="Ceramic Coffee Mug", price=14.99
```

**Final output.** `"SKU-1001: Ceramic Coffee Mug - $14.99"` — `sku` stayed exactly as set at construction throughout, while `name` and `price` were both freely and validly updated afterward through their respective setters.

## 7. Gotchas & takeaways

> **Not every field needs both a getter and a setter — some genuinely need only a getter (read-only, like `sku` above), and some might need neither, staying entirely private with all relevant logic handled internally by the class's own methods.** Automatically generating a getter and setter for every single field (a habit some IDEs make easy) can quietly undermine encapsulation by exposing unrestricted write access to fields that should really be protected or immutable.

> **A getter is not required to simply return a stored field's value verbatim — it can compute a derived result on demand** (as `getFahrenheit()` and `getDiscountedPrice()` do), which lets a class expose useful, always-up-to-date derived values without maintaining a separate field that could fall out of sync with the data it's derived from.

- A getter returns a field's value (or a computed result); a setter validates and assigns a new value.
- Standard naming (`getFieldName`/`setFieldName`, or `isFieldName` for booleans) is widely recognized by tools, frameworks, and other developers.
- A setter is the natural place to enforce validation, guaranteeing invalid values can never be assigned through the public interface.
- Not every field needs both a getter and setter — a getter-only field is a common, deliberate way to expose a read-only, immutable-after-construction property.
