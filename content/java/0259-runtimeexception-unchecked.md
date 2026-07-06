---
card: java
gi: 259
slug: runtimeexception-unchecked
title: RuntimeException (unchecked)
---

## 1. What it is

`RuntimeException` is a subclass of `Exception` that represents "unchecked" exceptions: the compiler does not force calling code to catch them or declare them in a `throws` clause. Common JDK examples include `NullPointerException`, `IllegalArgumentException`, `IndexOutOfBoundsException`, and `ArithmeticException` — all of these can be thrown from a method with no special declaration required, and calling code is free to catch them or simply let them propagate.

```java
public class RuntimeExceptionDemo {
    static int divide(int a, int b) {
        return a / b; // no "throws" declaration needed, even though this can throw ArithmeticException
    }

    public static void main(String[] args) {
        System.out.println(divide(10, 2)); // 5, fine
        System.out.println(divide(10, 0)); // throws ArithmeticException: / by zero — program terminates here
    }
}
```

`divide` can throw `ArithmeticException` (a `RuntimeException`) when `b` is `0`, but its signature requires no `throws` clause at all — the compiler places no obligation on `divide` to declare this possibility, nor on `main` to catch it; if uncaught, as here, the exception propagates all the way up and terminates the program with a printed stack trace.

## 2. Why & when

`RuntimeException` exists to represent failures that are usually the result of a programming mistake, rather than conditions genuinely outside the program's control — and Java's designers decided these shouldn't force every calling method to explicitly acknowledge them.

- **Signaling programmer errors, not environmental conditions** — a `NullPointerException` almost always means the code failed to check for `null` where it should have; an `IndexOutOfBoundsException` means an index calculation was wrong. These are bugs to fix, not conditions a caller should be forced to gracefully "handle" every single time.
- **Avoiding overwhelming every method signature** — if every possible programming mistake required a `throws` declaration, nearly every method in a typical program would need a long list of exceptions declared, most of which represent "this code has a bug," not "this is a normal failure mode to plan for" — unchecked exceptions avoid this burden.
- **Still fully catchable when useful** — nothing prevents catching a `RuntimeException` deliberately (as later topics on validation and defensive programming show); the "unchecked" designation only means the compiler doesn't *force* it, not that catching it is forbidden or unusual.

Throw a `RuntimeException` subtype (or a custom one extending it) for conditions that indicate a caller passed invalid arguments, violated a precondition, or otherwise made a programming error your method cannot proceed with — this is the standard, idiomatic choice for input validation failures in modern Java code, as opposed to checked exceptions (the next topic), which are reserved for conditions genuinely outside the program's control.

## 3. Core concept

```java
public class RuntimeExceptionCore {
    static double calculateDiscount(double price, double percentage) {
        if (percentage < 0 || percentage > 100) {
            throw new IllegalArgumentException("percentage must be between 0 and 100, got: " + percentage);
        }
        return price * (1 - percentage / 100);
    }
}
```

`calculateDiscount` throws `IllegalArgumentException` (a `RuntimeException` subtype) when given an invalid `percentage` — no `throws` clause appears on the method signature, and any caller passing an out-of-range value gets an immediate, clear failure rather than a silently wrong calculation; this is the idiomatic way to guard a method's preconditions in Java.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method throwing a RuntimeException needs no throws declaration and no forced catch, the exception can propagate freely up the call stack unless something chooses to catch it">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">divide(a, b)</text>

  <line x1="130" y1="50" x2="130" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="70" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">throws ArithmeticException</text>

  <rect x="40" y="80" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="100" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">main() — no catch here</text>

  <line x1="130" y1="110" x2="130" y2="130" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="128" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">propagates further, terminates program</text>

  <text x="450" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No "throws" clause required</text>
  <text x="450" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">anywhere in this chain —</text>
  <text x="450" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the compiler never forces a catch.</text>
</svg>

Unchecked exceptions require no `throws` declaration and propagate freely unless explicitly caught.

## 5. Runnable example

Scenario: an order-validation routine using unchecked exceptions to guard preconditions, evolved from a single guard clause into several combined, then hardened with a custom `RuntimeException` subclass carrying structured error data.

### Level 1 — Basic

```java
public class RuntimeExceptionBasic {
    static void validateQuantity(int quantity) {
        if (quantity <= 0) {
            throw new IllegalArgumentException("quantity must be positive, got: " + quantity);
        }
    }

    public static void main(String[] args) {
        try {
            validateQuantity(-5);
        } catch (IllegalArgumentException e) {
            System.out.println("Validation failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `java RuntimeExceptionBasic.java`

`validateQuantity` needs no `throws` clause even though it can throw `IllegalArgumentException`, and the caller is free to catch it (as shown) or ignore it entirely — the compiler imposes no obligation either way, which is the defining characteristic of an unchecked exception.

### Level 2 — Intermediate

Same validation idea, now with multiple guard clauses across an order object, demonstrating unchecked exceptions used as the standard mechanism for enforcing several preconditions at once.

```java
public class RuntimeExceptionIntermediate {
    static class Order {
        String product;
        int quantity;
        double price;

        Order(String product, int quantity, double price) {
            if (product == null || product.isBlank()) {
                throw new IllegalArgumentException("product must not be blank");
            }
            if (quantity <= 0) {
                throw new IllegalArgumentException("quantity must be positive, got: " + quantity);
            }
            if (price < 0) {
                throw new IllegalArgumentException("price cannot be negative, got: " + price);
            }
            this.product = product;
            this.quantity = quantity;
            this.price = price;
        }

        double total() { return quantity * price; }
    }

    public static void main(String[] args) {
        try {
            Order order = new Order("Widget", 3, 9.99);
            System.out.println("Order total: $" + order.total());

            Order badOrder = new Order("", 1, 5.0); // will throw before reaching total()
            System.out.println("This line never runs: " + badOrder.total());
        } catch (IllegalArgumentException e) {
            System.out.println("Order rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java RuntimeExceptionIntermediate.java`

Three separate guard clauses inside `Order`'s constructor all throw the same unchecked `IllegalArgumentException` type, each with a message tailored to the specific violated precondition — none of these guard clauses require the constructor (or `main`) to declare any `throws` clause, and a single `catch` clause conveniently handles all three cases at once.

### Level 3 — Advanced

Same order system, now with a custom `RuntimeException` subclass carrying structured data (not just a message), used to distinguish and react to specific validation failures programmatically rather than by parsing message text.

```java
public class RuntimeExceptionAdvanced {
    static class OrderValidationException extends RuntimeException { // custom unchecked exception
        final String field;
        OrderValidationException(String field, String message) {
            super(message);
            this.field = field;
        }
    }

    static class Order {
        String product;
        int quantity;
        double price;

        Order(String product, int quantity, double price) {
            if (product == null || product.isBlank()) {
                throw new OrderValidationException("product", "must not be blank");
            }
            if (quantity <= 0) {
                throw new OrderValidationException("quantity", "must be positive, got: " + quantity);
            }
            if (price < 0) {
                throw new OrderValidationException("price", "cannot be negative, got: " + price);
            }
            this.product = product;
            this.quantity = quantity;
            this.price = price;
        }

        double total() { return quantity * price; }
    }

    public static void main(String[] args) {
        Object[][] attempts = {
            { "Widget", 3, 9.99 },
            { "", 1, 5.0 },
            { "Gadget", -2, 3.0 },
            { "Gizmo", 1, -1.0 }
        };

        for (Object[] attempt : attempts) {
            try {
                Order order = new Order((String) attempt[0], (int) attempt[1], (double) attempt[2]);
                System.out.println("Accepted order, total: $" + order.total());
            } catch (OrderValidationException e) {
                System.out.println("Rejected (field: " + e.field + "): " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java RuntimeExceptionAdvanced.java`

`OrderValidationException` extends `RuntimeException` and adds its own `field` property, letting `catch` blocks programmatically inspect *which* field failed validation (`e.field`), not just read a human-readable message — this remains a fully unchecked exception (no `throws` clause needed anywhere), but carries structured data useful for building richer error responses, such as a form that highlights the specific invalid field.

## 6. Walkthrough

Trace the loop in `RuntimeExceptionAdvanced.main` over all four attempts.

**`attempt = {"Widget", 3, 9.99}`.** `new Order("Widget", 3, 9.99)`: `product` is non-blank, `quantity` (`3`) is positive, `price` (`9.99`) is non-negative — no exception thrown, fields are set. `order.total()` computes `3 * 9.99 = 29.97`. Prints `"Accepted order, total: $29.97"`.

**`attempt = {"", 1, 5.0}`.** `new Order("", 1, 5.0)`: `product.isBlank()` is `true`, so `OrderValidationException("product", "must not be blank")` is thrown immediately — `quantity` and `price` are never even checked. The `catch (OrderValidationException e)` clause catches it: `e.field` is `"product"`, `e.getMessage()` is `"must not be blank"`. Prints `"Rejected (field: product): must not be blank"`.

**`attempt = {"Gadget", -2, 3.0}`.** `new Order("Gadget", -2, 3.0)`: `product` is non-blank, so the first guard passes; `quantity` (`-2`) is `<= 0`, so `OrderValidationException("quantity", "must be positive, got: -2")` is thrown. Caught: `e.field` is `"quantity"`. Prints `"Rejected (field: quantity): must be positive, got: -2"`.

**`attempt = {"Gizmo", 1, -1.0}`.** `new Order("Gizmo", 1, -1.0)`: `product` and `quantity` both pass their guards; `price` (`-1.0`) is `< 0`, so `OrderValidationException("price", "cannot be negative, got: -1.0")` is thrown. Caught: `e.field` is `"price"`. Prints `"Rejected (field: price): cannot be negative, got: -1.0"`.

```
{"Widget", 3, 9.99}    -> all guards pass -> total = 3*9.99 = 29.97 -> "Accepted order, total: $29.97"
{"", 1, 5.0}           -> product.isBlank() true -> OrderValidationException(field="product")
{"Gadget", -2, 3.0}    -> quantity<=0 true       -> OrderValidationException(field="quantity")
{"Gizmo", 1, -1.0}     -> price<0 true           -> OrderValidationException(field="price")
```

**Final output.**
```
Accepted order, total: $29.97
Rejected (field: product): must not be blank
Rejected (field: quantity): must be positive, got: -2
Rejected (field: price): cannot be negative, got: -1.0
```

## 7. Gotchas & takeaways

> **"Unchecked" does not mean "unimportant" or "should be ignored" — it only describes the compiler's lack of enforcement.** A program that lets `NullPointerException`s and `IllegalArgumentException`s propagate uncaught all the way to the user is just as broken as one with unhandled checked exceptions; the difference is purely about whether the *compiler* forces you to acknowledge the possibility, not about whether you, as the developer, should actually think about and handle these cases where appropriate.

> **Custom exceptions extending `RuntimeException` remain unchecked, inheriting that behaviour automatically** — `OrderValidationException` needed no special keyword or declaration to stay unchecked; simply extending `RuntimeException` (rather than `Exception` directly) is what determines this, which is exactly why the choice of which class to extend matters so much when designing your own exception types.

- `RuntimeException` and its subclasses are unchecked: the compiler does not require a `throws` declaration or a mandatory `catch`, though catching them is still fully supported and often appropriate.
- Common JDK unchecked exceptions (`NullPointerException`, `IllegalArgumentException`, `IndexOutOfBoundsException`, `ArithmeticException`) typically signal programming errors or violated preconditions.
- Throw `RuntimeException` subtypes (built-in or custom) for invalid arguments and precondition violations — the standard, idiomatic approach in modern Java for this kind of failure.
- A custom exception extending `RuntimeException` remains unchecked automatically and can carry structured data (like a `field` property) beyond just a message, useful for programmatic error handling.
