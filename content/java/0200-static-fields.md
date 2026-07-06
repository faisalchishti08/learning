---
card: java
gi: 200
slug: static-fields
title: static fields
---

## 1. What it is

A **static field** is declared with the `static` keyword and belongs to the **class itself**, not to any individual instance — there is exactly **one** copy of a static field, shared by every object of that class (and accessible even without creating any object at all). This contrasts directly with an ordinary instance field, where every object gets its own independent copy.

```java
class Counter {
    static int totalCreated = 0; // ONE shared copy, belonging to the class itself
    int id;                       // an ordinary instance field — each object gets its OWN copy

    Counter() {
        totalCreated++;   // modifies the single shared static field
        id = totalCreated; // each object still gets its own distinct id
    }
}

new Counter();
new Counter();
new Counter();
System.out.println(Counter.totalCreated); // 3 — accessed via the CLASS name, not an instance
```

`Counter.totalCreated` is accessed through the **class name**, not through any particular object — this is the idiomatic way to access a static field, though `someCounterInstance.totalCreated` also technically works (accessing the same single shared value through an instance reference), it's discouraged since it can misleadingly suggest each instance has its own copy.

## 2. Why & when

Static fields exist for data that logically belongs to the *concept* of the class as a whole, rather than to any one specific instance:

- **Shared counters and totals** — tracking how many objects have been created, a running total across all instances, or any aggregate statistic that doesn't make sense to duplicate per-object.
- **Shared constants** — values like `Math.PI` that are the same for every use everywhere in a program, and never need per-instance variation (constants are typically also marked `final`, covered together with `static` in practice, though `final` itself is a separate topic).
- **Shared configuration or state** — a single, class-wide setting (like a debug flag, or a shared cache) that every instance should see and be affected by identically.

You reach for `static` specifically when a piece of data is a property of the *class* — true for every instance collectively — rather than a property that naturally varies from one instance to the next, which is what ordinary instance fields are for.

## 3. Core concept

```java
class BankAccount {
    static double interestRate = 0.02; // shared by ALL accounts — one interest rate for the whole bank
    double balance;                     // each account's OWN balance

    BankAccount(double balance) {
        this.balance = balance;
    }

    void applyInterest() {
        balance += balance * interestRate; // reads the ONE shared static field
    }
}

public class StaticFieldDemo {
    public static void main(String[] args) {
        BankAccount a = new BankAccount(1000);
        BankAccount b = new BankAccount(2000);

        BankAccount.interestRate = 0.05; // changes the rate for EVERY account, since there's only one copy

        a.applyInterest();
        b.applyInterest();

        System.out.println(a.balance); // 1050.0 — used the NEW shared rate, 0.05
        System.out.println(b.balance); // 2100.0 — same shared rate applied here too
    }
}
```

Changing `BankAccount.interestRate` once affects *every* account's subsequent `applyInterest()` call, since all accounts read from the exact same single static field — there is no way for one account to have a "different" interest rate than another, since the field itself is shared, not per-instance.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One shared static interest rate field belonging to the BankAccount class itself, with two separate account objects each having their own independent balance field but both reading from that same single shared rate">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="220" y="30" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">static interestRate = 0.05</text>
  <text x="300" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ONE copy, on the class itself</text>

  <line x1="260" y1="70" x2="150" y2="110" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="340" y1="70" x2="450" y2="110" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="60" y="110" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">account a</text>
  <text x="150" y="147" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">balance: 1050.0</text>

  <rect x="360" y="110" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">account b</text>
  <text x="450" y="147" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">balance: 2100.0</text>
</svg>

Each account keeps its own `balance`, but both read from the single, shared `interestRate` field.

## 5. Runnable example

Scenario: assigning unique sequential IDs to objects in a ticketing system — starting with a basic shared counter, then extending to a shared configuration value affecting every instance, then hardening into a class combining both patterns with proper encapsulation of the shared state.

### Level 1 — Basic

```java
public class TicketBasic {
    static class Ticket {
        static int nextId = 1; // shared across all Ticket instances
        int id;

        Ticket() {
            id = nextId;
            nextId++;
        }
    }

    public static void main(String[] args) {
        Ticket t1 = new Ticket();
        Ticket t2 = new Ticket();
        Ticket t3 = new Ticket();

        System.out.println(t1.id + ", " + t2.id + ", " + t3.id); // 1, 2, 3
    }
}
```

**How to run:** `java TicketBasic.java`

Each `new Ticket()` call reads the single shared `nextId`, assigns it to that instance's own `id`, then increments the shared counter — since `nextId` is `static`, every `Ticket` ever created sees and updates the exact same counter, guaranteeing unique, sequential IDs.

### Level 2 — Intermediate

Same tickets, now with a shared, mutable configuration value (a venue-wide prefix) that affects how every ticket displays itself, changeable at any point for all existing and future tickets alike.

```java
public class TicketIntermediate {
    static class Ticket {
        static int nextId = 1;
        static String venuePrefix = "GEN"; // shared, can change for everyone at once
        int id;

        Ticket() {
            id = nextId;
            nextId++;
        }

        String display() {
            return venuePrefix + "-" + id;
        }
    }

    public static void main(String[] args) {
        Ticket t1 = new Ticket();
        Ticket t2 = new Ticket();

        System.out.println(t1.display()); // GEN-1
        System.out.println(t2.display()); // GEN-2

        Ticket.venuePrefix = "VIP"; // changes the prefix for ALL tickets, including t1 and t2 already created

        System.out.println(t1.display()); // VIP-1 — even an already-created ticket reflects the new shared value
        System.out.println(t2.display()); // VIP-2
    }
}
```

**How to run:** `java TicketIntermediate.java`

Changing `Ticket.venuePrefix` after `t1` and `t2` were already created still changes what `t1.display()` and `t2.display()` produce — since `venuePrefix` is a single shared field, every instance (regardless of when it was created) always reads its current, up-to-date value at the moment `display()` runs.

### Level 3 — Advanced

Same ticket system, now with the shared counter properly encapsulated behind a static method (introduced fully in the next topic, previewed here) to prevent external code from directly manipulating `nextId` in ways that could break uniqueness, alongside a method reporting the total tickets issued.

```java
public class TicketAdvanced {
    static class Ticket {
        private static int nextId = 1; // private: cannot be tampered with from outside this class
        private static int totalIssued = 0;

        int id;
        String venuePrefix;

        Ticket(String venuePrefix) {
            this.id = nextId;
            this.venuePrefix = venuePrefix;
            nextId++;
            totalIssued++;
        }

        String display() {
            return venuePrefix + "-" + id;
        }

        static int totalIssued() { // controlled, read-only access to the shared static state
            return totalIssued;
        }
    }

    public static void main(String[] args) {
        Ticket t1 = new Ticket("GEN");
        Ticket t2 = new Ticket("VIP");
        Ticket t3 = new Ticket("GEN");

        System.out.println(t1.display());
        System.out.println(t2.display());
        System.out.println(t3.display());
        System.out.println("Total issued: " + Ticket.totalIssued());
    }
}
```

**How to run:** `java TicketAdvanced.java`

Making `nextId` and `totalIssued` `private` prevents any code outside the `Ticket` class from directly reading or, worse, modifying them — external code can only observe the shared `totalIssued` count through the controlled `Ticket.totalIssued()` method, which is the correct, encapsulated way to expose shared static state without letting outside code corrupt it.

## 6. Walkthrough

Trace `TicketAdvanced.main` through all three ticket creations:

**`new Ticket("GEN")`.** `id = nextId` reads the shared counter's current value, `1`; `t1.id = 1`. `venuePrefix = "GEN"`. `nextId++` makes the shared counter `2`. `totalIssued++` makes the shared total `1`.

**`new Ticket("VIP")`.** `id = nextId` reads `2` (the now-updated shared value); `t2.id = 2`. `venuePrefix = "VIP"`. `nextId` becomes `3`. `totalIssued` becomes `2`.

**`new Ticket("GEN")`.** `id = nextId` reads `3`; `t3.id = 3`. `venuePrefix = "GEN"` (same prefix as `t1`, but a distinct object with a distinct `id`). `nextId` becomes `4`. `totalIssued` becomes `3`.

```
nextId (shared):      1 -> 2 -> 3 -> 4
totalIssued (shared): 0 -> 1 -> 2 -> 3

t1: id=1, prefix="GEN" -> display "GEN-1"
t2: id=2, prefix="VIP" -> display "VIP-2"
t3: id=3, prefix="GEN" -> display "GEN-3"
```

**Final output.** `"GEN-1"`, `"VIP-2"`, `"GEN-3"`, then `"Total issued: 3"` — each ticket's own `id` and `venuePrefix` are independent instance data, while `nextId` and `totalIssued` are the single shared counters that every `Ticket` constructor call reads from and updates together.

## 7. Gotchas & takeaways

> **A static field's single shared value means a change made through one object's perspective is visible through every other object of that class, immediately.** This is easy to forget when a static field is used casually, and can cause subtle bugs if code mistakenly assumes each instance has its own independent copy, as ordinary instance fields do.

> **Accessing a static field through an instance reference (`someInstance.staticField`) compiles and works, but is discouraged and can mislead readers** into thinking the field is per-instance data. Always prefer accessing static fields through the class name (`ClassName.staticField`), which makes the shared nature explicit at every use.

- A `static` field has exactly one copy, shared by the class itself and every instance of it.
- Static fields are appropriate for shared counters, shared constants, and class-wide configuration or state.
- Changing a static field's value affects what every existing and future instance sees, since there is only one underlying value.
- Access static fields through the class name (`ClassName.field`), not through an instance reference, to keep their shared nature clear in the code.
