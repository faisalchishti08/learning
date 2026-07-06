---
card: java
gi: 268
slug: custom-exception-classes
title: Custom exception classes
---

## 1. What it is

A custom exception class is a class you define yourself, extending either `Exception` (making it checked) or `RuntimeException` (making it unchecked), to represent a specific failure condition in your own application's domain. It typically provides constructors matching the common patterns from its superclass (a message-only constructor, and a message-plus-cause constructor) and can add its own fields to carry structured data about the failure beyond just a text message.

```java
class InsufficientFundsException extends RuntimeException { // unchecked: a business-rule violation
    final double shortfall;

    InsufficientFundsException(double shortfall) {
        super("insufficient funds, short by: $" + shortfall); // sets the inherited message
        this.shortfall = shortfall; // additional structured data beyond the message
    }
}

public class CustomExceptionDemo {
    static void withdraw(double balance, double amount) {
        if (amount > balance) {
            throw new InsufficientFundsException(amount - balance);
        }
    }

    public static void main(String[] args) {
        try {
            withdraw(100.0, 150.0);
        } catch (InsufficientFundsException e) {
            System.out.println(e.getMessage() + " (exact shortfall: $" + e.shortfall + ")");
        }
    }
}
```

`InsufficientFundsException` extends `RuntimeException`, calls `super(...)` to set the standard inherited message, and adds its own `shortfall` field carrying a precise numeric value the `catch` block can use directly (`e.shortfall`), rather than having to parse that number back out of the message text.

## 2. Why & when

Custom exceptions let you model your own application's specific failure conditions with the same precision and type-safety Java's built-in exceptions provide for general-purpose failures.

- **Domain-specific meaning beyond generic exceptions** — throwing a generic `RuntimeException("insufficient funds")` works, but `InsufficientFundsException` is far more meaningful: it lets callers write a `catch` clause specifically for this business condition, distinct from any other kind of `RuntimeException` that might occur elsewhere.
- **Carrying structured data alongside the message** — a custom exception can hold fields specific to the failure (like `shortfall` above, or a `field` name as an earlier topic's `OrderValidationException` demonstrated), letting calling code react programmatically to the specifics of what went wrong, not just display a human-readable string.
- **Enabling precise, layered catch handling** — as the multiple-catch-blocks topic explored, having distinct custom exception types for distinct failure categories lets you write ordered, specific `catch` clauses rather than one generic clause with internal branching logic to figure out what actually happened.

Define a custom exception class whenever your application has a specific, recurring failure condition that deserves its own name and, often, its own structured data — choose `RuntimeException` as the superclass for business-rule violations and precondition failures (the common, idiomatic choice in modern Java), and `Exception` directly only for conditions genuinely outside your program's control that you deliberately want the compiler to force callers to acknowledge.

## 3. Core concept

```java
class OrderNotFoundException extends RuntimeException {
    final String orderId;

    OrderNotFoundException(String orderId) {
        super("order not found: " + orderId); // standard message-only super() call
        this.orderId = orderId;
    }

    OrderNotFoundException(String orderId, Throwable cause) {
        super("order not found: " + orderId, cause); // message + cause, for wrapping another exception
        this.orderId = orderId;
    }
}
```

Providing both a message-only constructor and a message-plus-cause constructor mirrors the two most common constructors every `Throwable` subclass typically offers, matching the pattern used throughout the JDK's own exception classes — this makes `OrderNotFoundException` usable both as a fresh, standalone exception and as a wrapper around some other underlying failure (following the exception-chaining pattern from an earlier topic).

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A custom exception class extends RuntimeException or Exception, inherits message and cause handling from Throwable, and can add its own fields carrying structured data about the specific failure">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="300" y="40" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">RuntimeException</text>

  <line x1="300" y1="50" x2="300" y2="75" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="160" y="80" width="280" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">InsufficientFundsException</text>
  <text x="300" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">inherited: message, cause, stack trace</text>
  <text x="300" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own: shortfall (double) — extra structured data</text>

  <text x="300" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Inherits standard Throwable behaviour, adds domain-specific fields on top.</text>
</svg>

A custom exception inherits standard `Throwable` behaviour and adds fields specific to its own domain.

## 5. Runnable example

Scenario: an e-commerce inventory system with domain-specific exceptions, evolved from a single custom exception into several combined with structured data, then hardened with a custom exception hierarchy of its own.

### Level 1 — Basic

```java
public class CustomExceptionBasic {
    static class OutOfStockException extends RuntimeException {
        OutOfStockException(String product) {
            super("out of stock: " + product);
        }
    }

    static void checkStock(String product, int quantity) {
        if (quantity == 0) throw new OutOfStockException(product);
    }

    public static void main(String[] args) {
        try {
            checkStock("Widget", 0);
        } catch (OutOfStockException e) {
            System.out.println("Cannot fulfill order: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CustomExceptionBasic.java`

`OutOfStockException` provides just a message-only constructor, calling `super(...)` to set the inherited message — the simplest, most common form of a custom exception.

### Level 2 — Intermediate

Same inventory idea, now with the custom exception carrying structured data (the requested and available quantities), letting the `catch` block react to the specifics programmatically rather than just displaying a message.

```java
public class CustomExceptionIntermediate {
    static class InsufficientStockException extends RuntimeException {
        final String product;
        final int requested;
        final int available;

        InsufficientStockException(String product, int requested, int available) {
            super("insufficient stock for " + product + ": requested " + requested + ", only " + available + " available");
            this.product = product;
            this.requested = requested;
            this.available = available;
        }
    }

    static void checkStock(String product, int requested, int available) {
        if (requested > available) {
            throw new InsufficientStockException(product, requested, available);
        }
    }

    public static void main(String[] args) {
        try {
            checkStock("Widget", 10, 3);
        } catch (InsufficientStockException e) {
            System.out.println(e.getMessage());
            System.out.println("Suggest ordering only " + e.available + " instead of " + e.requested);
        }
    }
}
```

**How to run:** `java CustomExceptionIntermediate.java`

`InsufficientStockException` carries `product`, `requested`, and `available` as real fields, letting the `catch` block build a specific, actionable suggestion (`"Suggest ordering only 3 instead of 10"`) directly from the exception's data, rather than needing to parse that information back out of a formatted message string.

### Level 3 — Advanced

Same inventory system, now with a small custom exception hierarchy: a common abstract base carrying shared data, with two concrete subclasses for genuinely distinct stock problems — demonstrating custom exceptions participating in inheritance just like ordinary classes.

```java
public class CustomExceptionAdvanced {
    static abstract class InventoryException extends RuntimeException { // shared base for inventory problems
        final String product;
        InventoryException(String message, String product) {
            super(message);
            this.product = product;
        }
    }

    static class OutOfStockException extends InventoryException {
        OutOfStockException(String product) {
            super("out of stock: " + product, product);
        }
    }

    static class DiscontinuedException extends InventoryException {
        final String replacementProduct;
        DiscontinuedException(String product, String replacementProduct) {
            super(product + " has been discontinued", product);
            this.replacementProduct = replacementProduct;
        }
    }

    static void checkAvailability(String product) {
        if (product.equals("Widget")) throw new OutOfStockException(product);
        if (product.equals("Gadget")) throw new DiscontinuedException(product, "Gadget Pro");
    }

    public static void main(String[] args) {
        String[] products = { "Widget", "Gadget", "Gizmo" };
        for (String product : products) {
            try {
                checkAvailability(product);
                System.out.println(product + " is available");
            } catch (DiscontinuedException e) {                     // MOST specific first
                System.out.println(e.getMessage() + " — try " + e.replacementProduct + " instead");
            } catch (InventoryException e) {                          // broader: catches OutOfStockException too
                System.out.println("Cannot get " + e.product + ": " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java CustomExceptionAdvanced.java`

`InventoryException` is an abstract custom base class carrying the shared `product` field, with `OutOfStockException` and `DiscontinuedException` as concrete subclasses adding their own specifics — the `catch` clauses in `main` are ordered from most specific (`DiscontinuedException`) to more general (`InventoryException`, which also catches `OutOfStockException` since it's a subtype), exactly mirroring the same specific-to-general ordering rule that applies to any exception hierarchy, custom or built-in.

## 6. Walkthrough

Trace the loop in `CustomExceptionAdvanced.main` over all three products.

**`product = "Widget"`.** `checkAvailability("Widget")`: `product.equals("Widget")` is `true`, so `OutOfStockException("Widget")` is thrown. This constructs the exception via `super("out of stock: Widget", "Widget")`, setting the inherited message and the `product` field. Checking `catch` clauses: `DiscontinuedException`? No match (wrong type). `InventoryException`? Match — `OutOfStockException` is a subtype of `InventoryException`. Prints `"Cannot get Widget: out of stock: Widget"`.

**`product = "Gadget"`.** `checkAvailability("Gadget")`: doesn't match `"Widget"`, but does match `"Gadget"`, so `DiscontinuedException("Gadget", "Gadget Pro")` is thrown, constructed via `super("Gadget has been discontinued", "Gadget")`, and setting its own `replacementProduct` field to `"Gadget Pro"`. Checking clauses: `DiscontinuedException`? Match immediately (exact type). Prints `"Gadget has been discontinued — try Gadget Pro instead"`.

**`product = "Gizmo"`.** `checkAvailability("Gizmo")`: matches neither `"Widget"` nor `"Gadget"`, so the method returns normally without throwing anything. Back in the loop, `System.out.println(product + " is available")` runs. Prints `"Gizmo is available"`.

```
"Widget": checkAvailability throws OutOfStockException("Widget")
  -> DiscontinuedException? no -> InventoryException? yes (OutOfStockException IS-A InventoryException)
  -> "Cannot get Widget: out of stock: Widget"

"Gadget": checkAvailability throws DiscontinuedException("Gadget", "Gadget Pro")
  -> DiscontinuedException? yes, exact match
  -> "Gadget has been discontinued — try Gadget Pro instead"

"Gizmo": checkAvailability returns normally, no exception
  -> "Gizmo is available"
```

**Final output.**
```
Cannot get Widget: out of stock: Widget
Gadget has been discontinued — try Gadget Pro instead
Gizmo is available
```

## 7. Gotchas & takeaways

> **A custom exception class should almost always be declared `final` or not extended further unless you specifically intend to build a hierarchy of related exceptions** — an unplanned, sprawling exception hierarchy can become just as confusing as unplanned class hierarchies elsewhere in a codebase; the `InventoryException` example above is deliberate and small precisely because a shared base with a couple of well-considered subclasses adds genuine value, not because deep exception hierarchies are always a good idea.

> **Custom exception classes should provide the standard constructor patterns (message-only, and message-plus-cause) that the rest of the JDK expects, even if you don't use the cause-accepting one immediately** — many tools, frameworks, and logging libraries assume these constructors exist and may attempt to use them via reflection; omitting the cause-accepting constructor can cause subtle interoperability issues with code that expects to wrap your custom exception around another failure later.

- A custom exception class extends `Exception` (checked) or `RuntimeException` (unchecked) to represent a domain-specific failure condition with its own name and, often, its own additional fields.
- Extra fields on a custom exception let calling code react programmatically to the specifics of a failure, not just display a message string.
- Custom exceptions can form their own small inheritance hierarchies, exactly like ordinary classes, letting a shared abstract base carry common data while concrete subclasses add their own specifics.
- Provide standard constructor patterns (message-only, message-plus-cause) matching the conventions the rest of the JDK and common tooling expect from any `Throwable` subclass.
