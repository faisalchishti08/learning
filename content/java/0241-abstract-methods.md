---
card: java
gi: 241
slug: abstract-methods
title: Abstract methods
---

## 1. What it is

An abstract method is a method declared with no body at all — just a signature ending in a semicolon — inside an abstract class (the previous topic). It defines *what* a method must do (its name, parameters, and return type) without saying *how*, leaving that entirely to whichever concrete subclass eventually implements it.

```java
abstract class Notifier {
    abstract void send(String message); // no body — a contract, not an implementation

    void log(String message) { // ordinary method, has a body
        System.out.println("Logging: " + message);
    }
}

class EmailNotifier extends Notifier {
    @Override
    void send(String message) { // required: must supply a body
        System.out.println("Emailing: " + message);
    }
}
```

`send` in `Notifier` has no `{ }` body — just `abstract void send(String message);` — while `log` is a normal method with a full implementation; `EmailNotifier` is forced by the compiler to supply a concrete body for `send`, or it too would have to be declared `abstract` and could not be instantiated.

## 2. Why & when

Abstract methods let a class declare a required capability without committing to any particular way of providing it, which is useful anywhere different subclasses genuinely need to behave differently for the same operation.

- **Enforcing a contract at compile time** — declaring a method `abstract` guarantees every concrete subclass provides *some* implementation before the program can even compile, which is far stronger than a comment saying "subclasses should override this."
- **Expressing "I don't know how, but someone must"** — a `Shape.area()` or `Notifier.send()` method has no sensible default implementation at the superclass level; each subclass's version is fundamentally different (a circle's area formula bears no resemblance to a square's), so leaving it abstract is more honest than inventing a meaningless default.
- **Enabling polymorphism through a shared type** — code that only knows about the abstract superclass (or an interface, covered shortly) can still call the abstract method and trust that, at runtime, the correct subclass-specific behaviour will run, without needing to know which subclass it actually is.

Declare a method `abstract` whenever a superclass cannot provide any meaningful default implementation, and every subclass must supply its own — if there *is* a sensible default that most subclasses would want (with only some needing to override it), a normal, overridable method is usually the better choice instead.

## 3. Core concept

```java
abstract class PaymentMethod {
    abstract boolean charge(double amount); // must be implemented — no sensible universal default

    void processPayment(double amount) { // shared logic using the abstract method
        System.out.println("Processing $" + amount + "...");
        boolean success = charge(amount);
        System.out.println(success ? "Payment succeeded" : "Payment failed");
    }
}
```

`processPayment` is fully implemented once, on the abstract class, and works correctly for *any* subclass's `charge` implementation, because it calls `charge(amount)` polymorphically — the abstract method is the single point of variation that every concrete subclass fills in differently, while the surrounding logic stays shared and consistent.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An abstract method has a signature but no body in the superclass, each concrete subclass supplies its own distinct body for that same method">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="200" y="20" width="200" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">abstract boolean charge(amount);</text>

  <line x1="240" y1="55" x2="140" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="360" y1="55" x2="460" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="95" width="200" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="117" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">CreditCard.charge() body A</text>

  <rect x="360" y="95" width="200" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="117" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">PayPal.charge() body B</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same signature, no shared body — each subclass fills in its own distinct implementation.</text>
</svg>

An abstract method has one shared signature but no shared body — every concrete subclass provides its own.

## 5. Runnable example

Scenario: a payment-processing system with different payment methods, evolved from a single abstract method into a working polymorphic checkout flow, then hardened with per-method failure logic showing how truly different the implementations can be.

### Level 1 — Basic

```java
public class AbstractMethodBasic {
    abstract static class PaymentMethod {
        abstract boolean charge(double amount);
    }

    static class CreditCard extends PaymentMethod {
        @Override
        boolean charge(double amount) {
            System.out.println("Charging credit card: $" + amount);
            return true;
        }
    }

    public static void main(String[] args) {
        PaymentMethod method = new CreditCard();
        System.out.println("Charge result: " + method.charge(49.99));
    }
}
```

**How to run:** `java AbstractMethodBasic.java`

`CreditCard` supplies the required body for `charge`, so it can be instantiated and used through the `PaymentMethod` reference — calling `method.charge(...)` runs `CreditCard`'s specific implementation.

### Level 2 — Intermediate

Same system, now with a second payment method whose `charge` implementation looks nothing like the first, plus a shared `processPayment` method demonstrating how the abstract method plugs into common logic.

```java
public class AbstractMethodIntermediate {
    abstract static class PaymentMethod {
        abstract boolean charge(double amount);

        void processPayment(double amount) {
            System.out.println("--- Processing $" + amount + " ---");
            boolean success = charge(amount);
            System.out.println(success ? "Success" : "Failed");
        }
    }

    static class CreditCard extends PaymentMethod {
        @Override
        boolean charge(double amount) {
            System.out.println("Charging credit card via card network");
            return true;
        }
    }

    static class BankTransfer extends PaymentMethod {
        @Override
        boolean charge(double amount) {
            System.out.println("Initiating bank transfer (takes 1-3 days)");
            return amount <= 10000; // banks reject very large instant transfers, in this simplified model
        }
    }

    public static void main(String[] args) {
        PaymentMethod[] methods = { new CreditCard(), new BankTransfer() };
        for (PaymentMethod m : methods) {
            m.processPayment(500.0);
        }
    }
}
```

**How to run:** `java AbstractMethodIntermediate.java`

`processPayment` is written once and never mentions `CreditCard` or `BankTransfer` by name; it works correctly for both because `charge(amount)` dispatches, at runtime, to whichever subclass's implementation matches the actual object — two utterly different charging mechanisms, unified through one abstract method signature.

### Level 3 — Advanced

Same payment system, now with a third method that fails under realistic conditions, and a checkout routine that aggregates results across several payment attempts — demonstrating the abstract method's role in a more production-flavoured flow with retries and mixed outcomes.

```java
import java.util.List;

public class AbstractMethodAdvanced {
    abstract static class PaymentMethod {
        String label;
        PaymentMethod(String label) { this.label = label; }

        abstract boolean charge(double amount);

        boolean processPayment(double amount) {
            System.out.println("--- " + label + ": processing $" + amount + " ---");
            boolean success = charge(amount);
            System.out.println(label + ": " + (success ? "SUCCESS" : "DECLINED"));
            return success;
        }
    }

    static class CreditCard extends PaymentMethod {
        double limit;
        CreditCard(double limit) { super("CreditCard"); this.limit = limit; }
        @Override
        boolean charge(double amount) { return amount <= limit; } // declines if over the credit limit
    }

    static class BankTransfer extends PaymentMethod {
        BankTransfer() { super("BankTransfer"); }
        @Override
        boolean charge(double amount) { return amount <= 10000; }
    }

    static class GiftCard extends PaymentMethod {
        double balance;
        GiftCard(double balance) { super("GiftCard"); this.balance = balance; }
        @Override
        boolean charge(double amount) {
            if (amount > balance) return false; // insufficient funds
            balance -= amount; // gift card actually mutates its own state on success
            return true;
        }
    }

    public static void main(String[] args) {
        List<PaymentMethod> attempts = List.of(
            new CreditCard(300.0),
            new GiftCard(50.0),
            new BankTransfer()
        );

        double amount = 200.0;
        int successCount = 0;
        for (PaymentMethod m : attempts) {
            if (m.processPayment(amount)) successCount++;
        }
        System.out.println("Successful methods: " + successCount + " / " + attempts.size());
    }
}
```

**How to run:** `java AbstractMethodAdvanced.java`

Each `charge` implementation encodes a completely different business rule (a credit limit check, a fixed transfer cap, a mutating balance deduction), yet the loop in `main` treats every element uniformly as a `PaymentMethod`, calling `processPayment` without any type-specific branching — the abstract method is what makes this uniform treatment possible despite the wildly different underlying logic.

## 6. Walkthrough

Trace the loop in `AbstractMethodAdvanced.main`, attempting to charge `200.0` against each payment method in order.

**`attempts.get(0)` is `CreditCard(300.0)`.** `processPayment(200.0)` prints `"--- CreditCard: processing $200.0 ---"`, then calls `charge(200.0)`, which dispatches to `CreditCard.charge`: `200.0 <= 300.0` is `true`, so it returns `true`. Back in `processPayment`, `success` is `true`, so it prints `"CreditCard: SUCCESS"` and returns `true`. `successCount` becomes `1`.

**`attempts.get(1)` is `GiftCard(50.0)`.** `processPayment(200.0)` prints `"--- GiftCard: processing $200.0 ---"`, then calls `charge(200.0)`, dispatching to `GiftCard.charge`: `200.0 > 50.0` is `true`, so it returns `false` immediately, without touching `balance`. `processPayment` prints `"GiftCard: DECLINED"` and returns `false`. `successCount` stays at `1`.

**`attempts.get(2)` is `BankTransfer()`.** `processPayment(200.0)` prints `"--- BankTransfer: processing $200.0 ---"`, then calls `charge(200.0)`, dispatching to `BankTransfer.charge`: `200.0 <= 10000` is `true`, returns `true`. `processPayment` prints `"BankTransfer: SUCCESS"` and returns `true`. `successCount` becomes `2`.

**Final summary.** `successCount` is `2`, `attempts.size()` is `3`, so the last line prints `"Successful methods: 2 / 3"`.

```
CreditCard.charge(200.0):  200.0 <= 300.0   -> true  -> SUCCESS
GiftCard.charge(200.0):    200.0 > 50.0     -> false -> DECLINED (balance untouched)
BankTransfer.charge(200.0):200.0 <= 10000   -> true  -> SUCCESS

successCount = 2, attempts.size() = 3
```

**Final output.**
```
--- CreditCard: processing $200.0 ---
CreditCard: SUCCESS
--- GiftCard: processing $200.0 ---
GiftCard: DECLINED
--- BankTransfer: processing $200.0 ---
BankTransfer: SUCCESS
Successful methods: 2 / 3
```

## 7. Gotchas & takeaways

> **An abstract method cannot be `private`, `static`, or `final`** — `private` methods aren't inherited or overridable at all, `static` methods belong to the class itself rather than participating in dynamic dispatch, and `final` explicitly forbids overriding — all three directly contradict the entire purpose of an abstract method, which is to be overridden by a subclass. The compiler rejects any such combination.

> **Declaring a method `abstract` inside a *non*-abstract class is a compile error** — if a class contains even one abstract method (whether declared directly or inherited and not yet overridden), the class itself must also be declared `abstract`, since it would otherwise be possible to instantiate an object with a method that has no body at all.

- An abstract method has a signature but no body, forcing every concrete subclass to supply its own implementation before it can be instantiated.
- It is used when a superclass genuinely cannot provide a sensible default implementation, and each subclass's behaviour must differ meaningfully.
- Shared, concrete methods on the same abstract class can call the abstract method polymorphically, letting common logic work correctly across every subclass automatically.
- Abstract methods cannot be `private`, `static`, or `final` — all three are fundamentally incompatible with being overridden.
