---
card: java
gi: 212
slug: abstract-modifier
title: abstract modifier
---

## 1. What it is

The `abstract` modifier marks a class or method as **incomplete by design**, meant to be finished by a subclass. An `abstract` class cannot be instantiated directly with `new` — only its concrete (non-abstract) subclasses can be instantiated. An `abstract` method declares a signature with **no body at all** (just a semicolon after the parentheses), leaving the actual implementation entirely to whichever subclass provides it; any subclass that doesn't provide an implementation must itself be declared `abstract` too.

```java
abstract class Shape { // cannot be instantiated directly
    abstract double area(); // no body — every concrete subclass MUST implement this

    void describe() { // a regular, complete method — subclasses inherit this as-is
        System.out.println("This shape's area is " + area());
    }
}

class Circle extends Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }

    @Override
    double area() { // REQUIRED — Circle would fail to compile without this
        return Math.PI * radius * radius;
    }
}

// Shape s = new Shape(); // COMPILE ERROR — cannot instantiate an abstract class
Shape s = new Circle(3); // fine — Circle is concrete and provides area()
```

`Shape` cannot be instantiated on its own — it exists purely to define a shared contract (`area()`) and shared behaviour (`describe()`) for its subclasses; `Circle`, by providing a real `area()` implementation, becomes a concrete class that *can* be instantiated.

## 2. Why & when

`abstract` exists to model concepts that are genuinely incomplete on their own, representing a shared shape or contract that only makes sense once specialized by a subclass:

- **Shared partial implementation** — an abstract class can provide real, complete methods and fields shared by all subclasses (like `describe()` above), while leaving specific pieces genuinely undefined until a subclass fills them in.
- **Enforcing a contract at compile time** — declaring `abstract double area();` guarantees every concrete subclass *must* provide its own `area()` implementation, or the subclass itself fails to compile unless it too is marked `abstract`.
- **Preventing meaningless instantiation** — some concepts, like "a generic shape" with no specific dimensions, genuinely don't make sense as a standalone object; `abstract` makes this restriction explicit and compiler-enforced, rather than relying on documentation or convention alone.

You reach for `abstract` specifically when a base class represents a concept that's only ever meaningful through some specific subclass — if every concrete detail can already be filled in without needing a subclass, an ordinary (non-abstract) class is the right choice instead.

## 3. Core concept

```java
abstract class Employee {
    String name;
    Employee(String name) { this.name = name; }

    abstract double calculatePay(); // every subclass must define how pay is calculated

    void printPaystub() { // shared, concrete behaviour — every subclass gets this for free
        System.out.println(name + "'s pay: $" + calculatePay());
    }
}

class SalariedEmployee extends Employee {
    double annualSalary;
    SalariedEmployee(String name, double annualSalary) {
        super(name);
        this.annualSalary = annualSalary;
    }

    @Override
    double calculatePay() {
        return annualSalary / 12;
    }
}
```

`Employee` never says *how* pay is calculated — that varies entirely by employee type — but it *does* provide `printPaystub()` once, shared identically by every subclass; `SalariedEmployee` fills in the missing piece (`calculatePay()`), and `printPaystub()` (inherited, unchanged) automatically uses that subclass-specific implementation when called.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An abstract Employee class providing a complete shared printPaystub method but declaring calculatePay with no body at all, with a concrete SalariedEmployee subclass supplying that missing implementation, making it instantiable while the abstract base class itself cannot be">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="200" y="20" width="200" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="40" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">abstract class Employee</text>
  <text x="300" y="58" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">printPaystub() { complete }</text>
  <text x="300" y="75" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">abstract calculatePay();</text>

  <line x1="300" y1="90" x2="300" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ab)"/>
  <text x="330" y="105" fill="#8b949e" font-size="9" font-family="sans-serif">extends</text>

  <rect x="200" y="115" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="135" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class SalariedEmployee</text>
  <text x="300" y="150" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">calculatePay() { ...actual code... }</text>

  <defs><marker id="ab" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The abstract class provides shared, complete behaviour and declares the missing piece; the concrete subclass fills that piece in.

## 5. Runnable example

Scenario: a small notification system supporting different delivery channels — starting with a basic abstract class and one concrete subclass, then extending with a second subclass sharing the same contract, then hardening into a case processing a mixed list of notification types polymorphically through the shared abstract type.

### Level 1 — Basic

```java
public class NotifyBasic {
    abstract static class Notification {
        String message;
        Notification(String message) { this.message = message; }

        abstract void send(); // every concrete subclass must implement this
    }

    static class EmailNotification extends Notification {
        EmailNotification(String message) { super(message); }

        @Override
        void send() {
            System.out.println("Emailing: " + message);
        }
    }

    public static void main(String[] args) {
        Notification n = new EmailNotification("Your order shipped");
        n.send();
    }
}
```

**How to run:** `java NotifyBasic.java`

`Notification` cannot be instantiated on its own (`new Notification(...)` would not compile) — only `EmailNotification`, which supplies a real `send()` implementation, can actually be created and used.

### Level 2 — Intermediate

Same system, now with a second subclass implementing the same `abstract` contract differently, plus a shared, concrete method inherited by both.

```java
public class NotifyIntermediate {
    abstract static class Notification {
        String message;
        Notification(String message) { this.message = message; }

        abstract void send();

        void logAttempt() { // shared, concrete — every subclass gets this identically
            System.out.println("Attempting to send: " + message);
        }
    }

    static class EmailNotification extends Notification {
        EmailNotification(String message) { super(message); }
        @Override
        void send() { System.out.println("Emailing: " + message); }
    }

    static class SmsNotification extends Notification {
        SmsNotification(String message) { super(message); }
        @Override
        void send() { System.out.println("Texting: " + message); }
    }

    public static void main(String[] args) {
        Notification email = new EmailNotification("Order shipped");
        Notification sms = new SmsNotification("Order shipped");

        email.logAttempt();
        email.send();

        sms.logAttempt();
        sms.send();
    }
}
```

**How to run:** `java NotifyIntermediate.java`

Both `EmailNotification` and `SmsNotification` inherit `logAttempt()` unchanged from `Notification`, while each provides its own distinct `send()` implementation — demonstrating how an abstract class combines guaranteed shared behaviour with subclass-specific customization for the parts that genuinely vary.

### Level 3 — Advanced

Same notification system, now processing a mixed list of different notification subclasses uniformly through the shared `Notification` type, demonstrating polymorphism: the same loop code correctly invokes each object's own specific `send()` implementation.

```java
import java.util.List;

public class NotifyAdvanced {
    abstract static class Notification {
        String message;
        Notification(String message) { this.message = message; }
        abstract void send();
        void logAttempt() { System.out.println("Attempting to send: " + message); }
    }

    static class EmailNotification extends Notification {
        EmailNotification(String message) { super(message); }
        @Override
        void send() { System.out.println("Emailing: " + message); }
    }

    static class SmsNotification extends Notification {
        SmsNotification(String message) { super(message); }
        @Override
        void send() { System.out.println("Texting: " + message); }
    }

    static class PushNotification extends Notification {
        PushNotification(String message) { super(message); }
        @Override
        void send() { System.out.println("Pushing: " + message); }
    }

    static void sendAll(List<Notification> notifications) {
        for (Notification n : notifications) { // works uniformly, regardless of the actual subclass
            n.logAttempt();
            n.send();
        }
    }

    public static void main(String[] args) {
        List<Notification> queue = List.of(
            new EmailNotification("Order shipped"),
            new SmsNotification("Order shipped"),
            new PushNotification("Order shipped")
        );

        sendAll(queue);
    }
}
```

**How to run:** `java NotifyAdvanced.java`

`sendAll` never needs to know which specific subclass each `Notification` actually is — declaring the parameter as `List<Notification>` and calling `n.send()` inside the loop lets Java's dynamic dispatch automatically invoke whichever concrete subclass's `send()` implementation matches each object's actual runtime type.

## 6. Walkthrough

Trace `sendAll(queue)` from `NotifyAdvanced.main`, where `queue` holds one `EmailNotification`, one `SmsNotification`, and one `PushNotification`, all sharing the message `"Order shipped"`:

**First iteration.** `n` refers to the `EmailNotification` object. `n.logAttempt()` runs `Notification`'s shared method, printing `"Attempting to send: Order shipped"`. `n.send()` dispatches to `EmailNotification`'s own `send()`, printing `"Emailing: Order shipped"`.

**Second iteration.** `n` now refers to the `SmsNotification` object. `n.logAttempt()` runs the same shared method again, printing `"Attempting to send: Order shipped"`. `n.send()` dispatches to `SmsNotification`'s own `send()`, printing `"Texting: Order shipped"`.

**Third iteration.** `n` refers to the `PushNotification` object. Same `logAttempt()` call, same message. `n.send()` dispatches to `PushNotification`'s own `send()`, printing `"Pushing: Order shipped"`.

```
queue = [EmailNotification, SmsNotification, PushNotification]  (all message="Order shipped")

for each n in queue:
  n.logAttempt() -> "Attempting to send: Order shipped"  (same method, every time)
  n.send()       -> dispatches to n's ACTUAL subclass's send() implementation
```

**Final output.** Six lines total, alternating `logAttempt`/`send` pairs: `"Attempting to send: Order shipped"`, `"Emailing: Order shipped"`, `"Attempting to send: Order shipped"`, `"Texting: Order shipped"`, `"Attempting to send: Order shipped"`, `"Pushing: Order shipped"` — one shared method (`logAttempt`) running identically each time, alongside three genuinely different `send()` behaviours, all driven through the exact same loop code.

## 7. Gotchas & takeaways

> **An `abstract` class can still have a constructor, fields, and fully-implemented (concrete) methods — it is not required to be *entirely* empty of implementation.** The only hard rule is that it cannot be instantiated directly with `new`, and any `abstract` method it declares must eventually be implemented by some concrete subclass down the hierarchy before that subclass can be instantiated.

> **A subclass that doesn't implement all of its superclass's `abstract` methods must itself be declared `abstract`** — the compiler enforces this transitively; only once a subclass provides implementations for every inherited abstract method does it become concrete and instantiable.

- `abstract class` means the class cannot be instantiated directly; only its concrete subclasses can be.
- `abstract` method declares a signature with no body — every concrete subclass must provide an implementation.
- An abstract class can still contain complete, concrete methods and fields shared by all subclasses.
- Calling an abstract method through a shared supertype reference (as in `sendAll`) correctly dispatches to whichever concrete subclass's implementation matches the object's actual runtime type.
