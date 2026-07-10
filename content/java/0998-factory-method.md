---
card: java
gi: 998
slug: factory-method
title: Factory Method
---

## 1. What it is

The **Factory Method** pattern defines a method whose job is to create and return an object, letting the *caller* work against an abstract return type while a subclass (or a parameter) decides which concrete class actually gets instantiated. Instead of calling `new ConcreteClass()` scattered throughout your code, you call `create(...)`, and the decision of exactly which concrete class to build is centralized in one place, often varying by a parameter or by which factory subclass is in play.

## 2. Why & when

Scattering `new SpecificClass()` calls throughout a codebase couples every one of those call sites to that specific class — adding a new variant means finding and updating every place `new` was called directly. Factory Method centralizes that decision: callers depend only on the abstract product type and the factory's creation method, so adding a new product variant means adding a new branch (or a new factory subclass) in one place, not hunting down scattered `new` calls (see [SOLID — Open/Closed](0990-solid-open-closed.md)).

Reach for Factory Method when object creation involves a decision — which concrete class to build based on a type code, a configuration value, or an environment — and you want that decision made in one place rather than repeated everywhere an object is needed. It's overkill for a class with one always-the-same constructor and no variation; plain `new` is simpler and the honest choice there.

## 3. Core concept

```
interface Notification { void send(String message); }
class EmailNotification implements Notification {
    public void send(String message) { System.out.println("Email: " + message); }
}
class SmsNotification implements Notification {
    public void send(String message) { System.out.println("SMS: " + message); }
}

// Factory Method: centralizes the "which concrete class?" decision in one place
class NotificationFactory {
    static Notification create(String type) {
        return switch (type) {
            case "EMAIL" -> new EmailNotification();
            case "SMS" -> new SmsNotification();
            default -> throw new IllegalArgumentException("unknown type: " + type);
        };
    }
}

// Callers never call `new EmailNotification()` themselves:
Notification n = NotificationFactory.create("EMAIL");
n.send("Order shipped");
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Caller asks NotificationFactory to create a Notification, and the factory decides internally whether to build an EmailNotification or SmsNotification">
  <rect x="30" y="70" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <rect x="230" y="70" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">NotificationFactory.create()</text>

  <rect x="470" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">EmailNotification</text>
  <rect x="470" y="120" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="141" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SmsNotification</text>

  <line x1="150" y1="90" x2="230" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="390" y1="80" x2="470" y2="45" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="390" y1="100" x2="470" y2="130" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The caller only talks to the factory and the abstract `Notification` type — it never names `EmailNotification` or `SmsNotification` directly.

## 5. Runnable example

Scenario: a notification system that creates different delivery channels, evolving from direct `new` calls scattered in caller code into a centralized factory that new channel types can join without touching existing callers.

### Level 1 — Basic

```java
// File: FactoryMethodBasic.java
interface Notification {
    void send(String message);
}
class EmailNotification implements Notification {
    public void send(String message) { System.out.println("Email: " + message); }
}
class SmsNotification implements Notification {
    public void send(String message) { System.out.println("SMS: " + message); }
}

public class FactoryMethodBasic {
    public static void main(String[] args) {
        String type = "EMAIL";

        // Caller decides directly which concrete class to construct.
        Notification notification = type.equals("EMAIL") ? new EmailNotification() : new SmsNotification();
        notification.send("Order shipped");
    }
}
```

**How to run:** save as `FactoryMethodBasic.java`, then `javac FactoryMethodBasic.java && java FactoryMethodBasic` (JDK 17+).

Expected output:
```
Email: Order shipped
```

The decision of which concrete class to build is inline in `main` — if this decision needs to be made in ten different places across the codebase, each one repeats (and can drift from) the same `if`/`else` logic.

### Level 2 — Intermediate

```java
// File: FactoryMethodIntermediate.java
interface Notification {
    void send(String message);
}
class EmailNotification implements Notification {
    public void send(String message) { System.out.println("Email: " + message); }
}
class SmsNotification implements Notification {
    public void send(String message) { System.out.println("SMS: " + message); }
}

class NotificationFactory {
    static Notification create(String type) {
        return switch (type) {
            case "EMAIL" -> new EmailNotification();
            case "SMS" -> new SmsNotification();
            default -> throw new IllegalArgumentException("unknown type: " + type);
        };
    }
}

public class FactoryMethodIntermediate {
    public static void main(String[] args) {
        Notification email = NotificationFactory.create("EMAIL");
        Notification sms = NotificationFactory.create("SMS");
        email.send("Order shipped");
        sms.send("Order shipped");
    }
}
```

**How to run:** save as `FactoryMethodIntermediate.java`, then `javac FactoryMethodIntermediate.java && java FactoryMethodIntermediate` (JDK 17+).

Expected output:
```
Email: Order shipped
SMS: Order shipped
```

The real-world concern added: the "which concrete class?" decision lives in exactly one place, `NotificationFactory.create`. Every caller across the codebase calls the same method instead of repeating the same `if`/`else` or `switch` logic.

### Level 3 — Advanced

```java
// File: FactoryMethodAdvanced.java
import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;

interface Notification {
    void send(String message);
}
class EmailNotification implements Notification {
    public void send(String message) { System.out.println("Email: " + message); }
}
class SmsNotification implements Notification {
    public void send(String message) { System.out.println("SMS: " + message); }
}
// A new channel, added later, without touching NotificationFactory's existing code path.
class PushNotification implements Notification {
    public void send(String message) { System.out.println("Push: " + message); }
}

// A registry-based factory: new types are added by registering a Supplier,
// not by editing a switch statement -- this satisfies Open/Closed as well.
class NotificationFactory {
    private final Map<String, Supplier<Notification>> registry = new HashMap<>();

    void register(String type, Supplier<Notification> supplier) {
        registry.put(type, supplier);
    }

    Notification create(String type) {
        Supplier<Notification> supplier = registry.get(type);
        if (supplier == null) {
            throw new IllegalArgumentException("unknown type: " + type);
        }
        return supplier.get();
    }
}

public class FactoryMethodAdvanced {
    public static void main(String[] args) {
        NotificationFactory factory = new NotificationFactory();
        factory.register("EMAIL", EmailNotification::new);
        factory.register("SMS", SmsNotification::new);
        factory.register("PUSH", PushNotification::new); // new channel, registered, not hardcoded

        for (String type : new String[]{"EMAIL", "SMS", "PUSH"}) {
            factory.create(type).send("Order shipped");
        }
    }
}
```

**How to run:** save as `FactoryMethodAdvanced.java`, then `javac FactoryMethodAdvanced.java && java FactoryMethodAdvanced` (JDK 17+).

Expected output:
```
Email: Order shipped
SMS: Order shipped
Push: Order shipped
```

The production-flavored hard case: `PushNotification` is added as a genuinely new channel by *registering* a constructor reference at startup, rather than editing a hardcoded `switch` inside `NotificationFactory` — the factory's own `create` method is completely unchanged from a version that only knew about two channels.

## 6. Walkthrough

Tracing the loop in `FactoryMethodAdvanced.main`:

1. `factory.register("EMAIL", EmailNotification::new)` stores a `Supplier<Notification>` — a constructor reference — under the key `"EMAIL"` in the factory's internal map. No `Notification` is created yet; only the *recipe* for creating one is stored.
2. The same happens for `"SMS"` and `"PUSH"`, each mapped to its own constructor reference.
3. The loop iterates over `["EMAIL", "SMS", "PUSH"]`. For `"EMAIL"`, `factory.create("EMAIL")` looks up the registry, finds `EmailNotification::new`, and calls `supplier.get()`, which invokes `new EmailNotification()` and returns the new instance.
4. `.send("Order shipped")` is called immediately on that returned instance, dispatching to `EmailNotification.send`, printing `"Email: Order shipped"`.
5. The same sequence repeats for `"SMS"` (constructing an `SmsNotification` and printing `"SMS: Order shipped"`) and then `"PUSH"` (constructing a `PushNotification` and printing `"Push: Order shipped"`).
6. Note that `PushNotification` never existed when `NotificationFactory`'s `create` method was first written — it was added purely by registering a new supplier at the call site in `main`, with zero changes to the `NotificationFactory` class itself.

## 7. Gotchas & takeaways

> **Gotcha:** a `switch`-based factory (Level 2) still has to be edited every time a new type is added — it centralizes the decision, but it doesn't make the factory itself open for extension. The registry-based version (Level 3) fixes that by letting new types be added via registration instead of code edits.

- Factory Method centralizes the "which concrete class to build?" decision behind a method, so callers depend on an abstract type and a creation call, not on scattered `new` expressions.
- A `switch`/`if` inside the factory is a fine starting point, but every new variant still requires editing the factory — a registry of suppliers (or subclassed factories, the classic Gang-of-Four form) removes even that edit.
- Method references (`EmailNotification::new`) make registering a constructor as a `Supplier` concise and avoid an extra wrapper lambda.
- Factory Method pairs naturally with [SOLID — Open/Closed](0990-solid-open-closed.md): the registry form lets new product types join without modifying the factory's existing code.
- Don't introduce a factory for a class with exactly one always-the-same construction path — plain `new` is simpler and factory ceremony there adds nothing.
- See [Abstract Factory](0999-abstract-factory.md) for the related pattern that creates *families* of related objects instead of one object at a time.
