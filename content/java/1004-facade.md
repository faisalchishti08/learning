---
card: java
gi: 1004
slug: facade
title: Facade
---

## 1. What it is

The **Facade** pattern provides a single, simplified interface to a larger, more complex subsystem made up of many interacting classes. Instead of calling several classes in a specific order, handling their interdependencies yourself, you call one method on the facade, and it internally coordinates all the subsystem classes on your behalf. It doesn't hide the subsystem's classes from existing users who need fine-grained control — it just gives everyone else a much simpler front door.

## 2. Why & when

Complex subsystems (an order-processing pipeline that touches inventory, payment, shipping, and notifications) require callers to know the correct sequence of calls across several classes, along with how their outputs feed into each other's inputs. That's a lot of knowledge to demand of every caller, and it means every caller re-implements the same coordination logic, drifting apart over time as the subsystem evolves. Facade exists to package that coordination knowledge into one place, giving most callers one clean method call while the individual subsystem classes remain available underneath for the rare caller that needs finer control.

Reach for Facade when a common use case requires calling several classes in a specific, non-obvious sequence, and most callers just want "the normal thing" to happen without knowing the details. It's unnecessary when the subsystem genuinely has only one class or one obvious call — there's nothing to simplify.

## 3. Core concept

```
// The complex subsystem: several classes, each with its own job
class InventoryService { boolean reserve(String item) { /* ... */ return true; } }
class PaymentService { boolean charge(double amount) { /* ... */ return true; } }
class ShippingService { void scheduleShipment(String item) { /* ... */ } }
class NotificationService { void notifyCustomer(String message) { /* ... */ } }

// Facade: one method coordinates the whole subsystem for the common case
class OrderFacade {
    private final InventoryService inventory = new InventoryService();
    private final PaymentService payment = new PaymentService();
    private final ShippingService shipping = new ShippingService();
    private final NotificationService notifications = new NotificationService();

    void placeOrder(String item, double price) {
        if (!inventory.reserve(item)) throw new IllegalStateException("out of stock");
        if (!payment.charge(price)) throw new IllegalStateException("payment failed");
        shipping.scheduleShipment(item);
        notifications.notifyCustomer("Your order for " + item + " is on its way!");
    }
}

// Callers just do this instead of coordinating four services themselves:
new OrderFacade().placeOrder("widget", 19.99);
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Caller talks only to OrderFacade, which internally coordinates InventoryService, PaymentService, ShippingService, and NotificationService in the correct order">
  <rect x="20" y="80" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="80" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <rect x="200" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="270" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderFacade</text>

  <rect x="420" y="10" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="30" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1. InventoryService</text>
  <rect x="420" y="55" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">2. PaymentService</text>
  <rect x="420" y="100" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">3. ShippingService</text>
  <rect x="420" y="145" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">4. NotificationService</text>

  <line x1="140" y1="100" x2="200" y2="100" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="340" y1="85" x2="420" y2="25" stroke="#79c0ff"/>
  <line x1="340" y1="95" x2="420" y2="70" stroke="#79c0ff"/>
  <line x1="340" y1="105" x2="420" y2="115" stroke="#79c0ff"/>
  <line x1="340" y1="115" x2="420" y2="160" stroke="#79c0ff"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The caller sends one call to `OrderFacade`; the facade fans it out to four subsystem classes in the correct sequence.

## 5. Runnable example

Scenario: an order-placement workflow spanning inventory, payment, shipping, and notifications, evolving from caller-coordinated chaos into a single facade method that hides the sequencing.

### Level 1 — Basic

```java
// File: FacadeBasic.java
class InventoryService {
    boolean reserve(String item) {
        System.out.println("Reserving " + item);
        return true;
    }
}
class PaymentService {
    boolean charge(double amount) {
        System.out.println("Charging $" + amount);
        return true;
    }
}
class ShippingService {
    void scheduleShipment(String item) {
        System.out.println("Scheduling shipment for " + item);
    }
}

public class FacadeBasic {
    public static void main(String[] args) {
        // Caller has to know the exact sequence AND handle each service directly.
        InventoryService inventory = new InventoryService();
        PaymentService payment = new PaymentService();
        ShippingService shipping = new ShippingService();

        if (inventory.reserve("widget")) {
            if (payment.charge(19.99)) {
                shipping.scheduleShipment("widget");
            }
        }
    }
}
```

**How to run:** save as `FacadeBasic.java`, then `javac FacadeBasic.java && java FacadeBasic` (JDK 17+).

Expected output:
```
Reserving widget
Charging $19.99
Scheduling shipment for widget
```

Every caller that wants to place an order needs to know this exact three-step sequence and re-implement the nested `if` checks — repeated at every call site across the codebase.

### Level 2 — Intermediate

```java
// File: FacadeIntermediate.java
class InventoryService {
    boolean reserve(String item) {
        System.out.println("Reserving " + item);
        return true;
    }
}
class PaymentService {
    boolean charge(double amount) {
        System.out.println("Charging $" + amount);
        return true;
    }
}
class ShippingService {
    void scheduleShipment(String item) {
        System.out.println("Scheduling shipment for " + item);
    }
}
class NotificationService {
    void notifyCustomer(String message) {
        System.out.println("Notifying: " + message);
    }
}

class OrderFacade {
    private final InventoryService inventory = new InventoryService();
    private final PaymentService payment = new PaymentService();
    private final ShippingService shipping = new ShippingService();
    private final NotificationService notifications = new NotificationService();

    void placeOrder(String item, double price) {
        if (!inventory.reserve(item)) throw new IllegalStateException("out of stock");
        if (!payment.charge(price)) throw new IllegalStateException("payment failed");
        shipping.scheduleShipment(item);
        notifications.notifyCustomer("Your order for " + item + " is on its way!");
    }
}

public class FacadeIntermediate {
    public static void main(String[] args) {
        new OrderFacade().placeOrder("widget", 19.99);
    }
}
```

**How to run:** save as `FacadeIntermediate.java`, then `javac FacadeIntermediate.java && java FacadeIntermediate` (JDK 17+).

Expected output:
```
Reserving widget
Charging $19.99
Scheduling shipment for widget
Notifying: Your order for widget is on its way!
```

The real-world concern added: any caller across the codebase now writes just `new OrderFacade().placeOrder("widget", 19.99)` — the four-step sequencing and error handling live in exactly one place instead of being duplicated everywhere an order is placed.

### Level 3 — Advanced

```java
// File: FacadeAdvanced.java
class OutOfStockException extends RuntimeException {
    OutOfStockException(String item) { super(item + " is out of stock"); }
}
class PaymentFailedException extends RuntimeException {
    PaymentFailedException() { super("payment failed"); }
}

class InventoryService {
    boolean reserve(String item) {
        System.out.println("Reserving " + item);
        return !item.equals("sold-out-widget");
    }
    void release(String item) {
        System.out.println("Releasing reservation for " + item);
    }
}
class PaymentService {
    boolean charge(double amount) {
        System.out.println("Charging $" + amount);
        return amount <= 100.0;
    }
}
class ShippingService {
    void scheduleShipment(String item) { System.out.println("Scheduling shipment for " + item); }
}
class NotificationService {
    void notifyCustomer(String message) { System.out.println("Notifying: " + message); }
    void notifyFailure(String reason) { System.out.println("Notifying failure: " + reason); }
}

class OrderFacade {
    private final InventoryService inventory = new InventoryService();
    private final PaymentService payment = new PaymentService();
    private final ShippingService shipping = new ShippingService();
    private final NotificationService notifications = new NotificationService();

    void placeOrder(String item, double price) {
        if (!inventory.reserve(item)) {
            notifications.notifyFailure("out of stock");
            throw new OutOfStockException(item);
        }
        // Compensating action: if payment fails AFTER reserving stock, release it --
        // this rollback logic is exactly the kind of coordination knowledge a
        // facade is meant to centralize so callers never have to think about it.
        if (!payment.charge(price)) {
            inventory.release(item);
            notifications.notifyFailure("payment declined");
            throw new PaymentFailedException();
        }
        shipping.scheduleShipment(item);
        notifications.notifyCustomer("Your order for " + item + " is on its way!");
    }
}

public class FacadeAdvanced {
    public static void main(String[] args) {
        OrderFacade facade = new OrderFacade();
        facade.placeOrder("widget", 19.99);

        try {
            facade.placeOrder("premium-widget", 150.0); // price too high -> payment fails
        } catch (PaymentFailedException e) {
            System.out.println("order failed: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `FacadeAdvanced.java`, then `javac FacadeAdvanced.java && java FacadeAdvanced` (JDK 17+).

Expected output:
```
Reserving widget
Charging $19.99
Scheduling shipment for widget
Notifying: Your order for widget is on its way!
Reserving premium-widget
Charging $150.0
Releasing reservation for premium-widget
Notifying failure: payment declined
order failed: payment failed
```

The production-flavored hard case: when payment fails *after* inventory was already reserved, `OrderFacade` compensates by releasing that reservation before propagating the failure — a rollback sequence that would otherwise need to be duplicated by every caller if they coordinated the subsystem themselves.

## 6. Walkthrough

Tracing `facade.placeOrder("premium-widget", 150.0)` in `FacadeAdvanced.main`:

1. `inventory.reserve("premium-widget")` runs: since the item isn't `"sold-out-widget"`, it prints `"Reserving premium-widget"` and returns `true` — the `if (!inventory.reserve(item))` check is false, so execution continues.
2. `payment.charge(150.0)` runs: it prints `"Charging $150.0"`, and since `150.0 <= 100.0` is `false`, it returns `false`.
3. The `if (!payment.charge(price))` check is now true, entering the failure branch: `inventory.release("premium-widget")` runs first, printing `"Releasing reservation for premium-widget"` — undoing step 1's reservation.
4. `notifications.notifyFailure("payment declined")` runs next, printing `"Notifying failure: payment declined"`.
5. `throw new PaymentFailedException()` is thrown, unwinding out of `placeOrder` entirely — `shipping.scheduleShipment` and the success notification are never reached.
6. That exception propagates up to `main`'s `try`/`catch`, caught by `catch (PaymentFailedException e)`, which prints `"order failed: payment failed"`. The entire four-service coordination — including the rollback — happened behind the single `facade.placeOrder(...)` call; `main` never touched `InventoryService`, `PaymentService`, `ShippingService`, or `NotificationService` directly.

## 7. Gotchas & takeaways

> **Gotcha:** a facade should simplify the *common* case, not become the *only* way to use the subsystem. Callers who genuinely need fine-grained control (partial refunds, custom shipment scheduling) should still be able to reach the individual subsystem classes directly — don't seal them off just because a facade exists.

- Facade provides one simple entry point to a subsystem made of several interacting classes, hiding the coordination sequence from most callers.
- It centralizes not just the "happy path" call sequence but also error handling and compensating actions (like releasing a reservation after a failed payment).
- The individual subsystem classes remain available and usable directly for callers with more specialized needs — Facade adds a simpler option, it doesn't remove the detailed one.
- Unlike [Adapter](1002-adapter.md), which makes one incompatible interface match another, Facade's goal is to make a *complex* set of interfaces feel like one *simple* interface — the two are often confused but solve different problems.
- Don't build a facade for a subsystem with only one class or one obvious call — there's nothing to simplify, and the extra layer would be unearned indirection.
- Facade often sits at architectural boundaries — e.g., a service layer facade in front of several repositories and external clients — a very common pattern in Spring-based applications.
