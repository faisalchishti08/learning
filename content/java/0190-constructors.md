---
card: java
gi: 190
slug: constructors
title: Constructors
---

## 1. What it is

A **constructor** is a special block of code that runs automatically when an object is created with `new`, responsible for setting up that object's initial state. It looks like a method but has no return type (not even `void`) and shares its exact name with the class. Constructors are the proper place to validate and assign initial field values, so an object never exists in an invalid or incompletely-set-up state.

```java
class Point {
    int x;
    int y;

    Point(int x, int y) { // constructor: same name as the class, no return type
        this.x = x;
        this.y = y;
    }
}

Point p = new Point(3, 4); // constructor runs immediately, x and y are set before p is usable
```

`new Point(3, 4)` both allocates the object *and* immediately runs the constructor with arguments `3` and `4` — by the time the `new` expression finishes and `p` is assigned, the object is already fully initialized, unlike the earlier examples in this series where fields were left at their defaults and assigned manually afterward.

## 2. Why & when

Constructors exist to guarantee that an object is properly initialized the instant it comes into existence, rather than leaving initialization as a separate, easy-to-forget step:

- **Guaranteed initialization** — without a constructor, fields default to `0`/`false`/`null` and must be set manually afterward, a step that's easy to forget entirely, leaving the object in a nonsensical state (as seen in an earlier topic's `broken` product with a negative price).
- **Validation at creation time** — a constructor can reject invalid initial values immediately, by throwing an exception, so an invalid object is never created in the first place, rather than only being caught later when some method happens to check.
- **Required data upfront** — a constructor with parameters *forces* the caller to supply essential values right away; there's no way to call `new Point(3, 4)` without providing both coordinates, unlike optional field assignment afterward.

You define a constructor whenever an object has required initial data or invariants that should be enforced from the moment it exists — which, in well-designed code, is essentially always, rather than relying on the caller to remember to assign every field correctly after `new`.

## 3. Core concept

```java
class BankAccount {
    String owner;
    double balance;

    BankAccount(String owner, double initialBalance) {
        if (initialBalance < 0) {
            throw new IllegalArgumentException("Initial balance cannot be negative: " + initialBalance);
        }
        this.owner = owner;
        this.balance = initialBalance;
    }
}

public class ConstructorDemo {
    public static void main(String[] args) {
        BankAccount acc = new BankAccount("Ann", 100.0); // valid — constructor runs cleanly
        System.out.println(acc.owner + ": $" + acc.balance);

        try {
            new BankAccount("Bo", -50.0); // invalid — constructor throws before the object is usable
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

The validation happens *inside the constructor itself*, before `this.balance` is even assigned — an invalid `BankAccount` is never fully created; the exception propagates out of `new BankAccount("Bo", -50.0)` immediately, so no reference to a broken object ever escapes into the rest of the program.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline showing new BankAccount call triggering memory allocation, then the constructor running validation and field assignment, and only then handing back a usable object reference to the caller">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">new BankAccount("Ann", 100.0)</text>

  <rect x="30" y="45" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1. allocate object</text>

  <line x1="160" y1="65" x2="200" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#c)"/>

  <rect x="200" y="45" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2. run constructor body</text>

  <line x1="380" y1="65" x2="420" y2="65" stroke="#3fb950" stroke-width="2" marker-end="url(#c)"/>

  <rect x="420" y="45" width="150" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="495" y="65" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">3. return reference</text>

  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">if the constructor throws at step 2, step 3 never happens — no broken object escapes</text>
</svg>

The constructor runs completely, including any validation, before `new` ever hands back a usable reference.

## 5. Runnable example

Scenario: modeling a simple `Ticket` for an event booking system — starting with a basic constructor assigning fields, then extending with validation of required data, then hardening into a constructor that computes a derived field from its parameters at construction time.

### Level 1 — Basic

```java
public class TicketBasic {
    static class Ticket {
        String eventName;
        int seatNumber;

        Ticket(String eventName, int seatNumber) {
            this.eventName = eventName;
            this.seatNumber = seatNumber;
        }
    }

    public static void main(String[] args) {
        Ticket t = new Ticket("Concert", 42);
        System.out.println(t.eventName + ", seat " + t.seatNumber);
    }
}
```

**How to run:** `java TicketBasic.java`

The constructor assigns both fields immediately from its parameters — `new Ticket("Concert", 42)` produces a fully-populated object in one step, with no separate manual field assignment needed afterward.

### Level 2 — Intermediate

Same `Ticket`, now validating that the seat number is positive and the event name isn't empty, rejecting invalid tickets at the moment of creation.

```java
public class TicketIntermediate {
    static class Ticket {
        String eventName;
        int seatNumber;

        Ticket(String eventName, int seatNumber) {
            if (eventName == null || eventName.isEmpty()) {
                throw new IllegalArgumentException("Event name is required");
            }
            if (seatNumber <= 0) {
                throw new IllegalArgumentException("Seat number must be positive: " + seatNumber);
            }
            this.eventName = eventName;
            this.seatNumber = seatNumber;
        }
    }

    public static void main(String[] args) {
        Ticket valid = new Ticket("Concert", 42);
        System.out.println(valid.eventName + ", seat " + valid.seatNumber);

        try {
            new Ticket("Concert", -5);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java TicketIntermediate.java`

Both validation checks run *before* either field is assigned — if `seatNumber <= 0` fires, `eventName` and `seatNumber` are never set on the new object at all, and the exception unwinds out of the `new` expression entirely, so no invalid `Ticket` object is ever returned to the caller.

### Level 3 — Advanced

Same `Ticket`, now computing a derived field (a formatted confirmation code) directly inside the constructor from the validated input, so every valid `Ticket` automatically has a consistent, ready-to-use confirmation code from the moment it's created.

```java
public class TicketAdvanced {
    static class Ticket {
        String eventName;
        int seatNumber;
        String confirmationCode;

        Ticket(String eventName, int seatNumber) {
            if (eventName == null || eventName.isEmpty()) {
                throw new IllegalArgumentException("Event name is required");
            }
            if (seatNumber <= 0) {
                throw new IllegalArgumentException("Seat number must be positive: " + seatNumber);
            }
            this.eventName = eventName;
            this.seatNumber = seatNumber;
            this.confirmationCode = buildConfirmationCode(eventName, seatNumber);
        }

        private static String buildConfirmationCode(String eventName, int seatNumber) {
            String prefix = eventName.substring(0, Math.min(3, eventName.length())).toUpperCase();
            return prefix + "-" + seatNumber;
        }
    }

    public static void main(String[] args) {
        Ticket t1 = new Ticket("Concert", 42);
        Ticket t2 = new Ticket("Ballet", 7);

        System.out.println(t1.confirmationCode); // CON-42
        System.out.println(t2.confirmationCode); // BAL-7
    }
}
```

**How to run:** `java TicketAdvanced.java`

`buildConfirmationCode` is called from inside the constructor itself, after validation but before the constructor finishes — this guarantees `confirmationCode` is always present and consistent for every successfully-constructed `Ticket`, since there's no path through the constructor that skips computing it.

## 6. Walkthrough

Trace `new Ticket("Concert", 42)` from `TicketAdvanced.main`:

**Validation.** `eventName == null || eventName.isEmpty()` — `"Concert"` is neither, so this guard doesn't fire. `seatNumber <= 0` — `42 <= 0` is false, so this guard doesn't fire either.

**Field assignment.** `this.eventName = "Concert"`; `this.seatNumber = 42`.

**Derived field.** `buildConfirmationCode("Concert", 42)` runs: `Math.min(3, "Concert".length())` is `Math.min(3, 7) = 3`, so `eventName.substring(0, 3)` is `"Con"`, and `.toUpperCase()` makes it `"CON"`. The method returns `"CON" + "-" + 42 = "CON-42"`. Back in the constructor, `this.confirmationCode = "CON-42"`.

**Object ready.** The constructor finishes; `new Ticket(...)` returns a reference to this fully-initialized object, assigned to `t1`.

```
new Ticket("Concert", 42)
  validate eventName: not null/empty -> OK
  validate seatNumber: 42 > 0 -> OK
  this.eventName = "Concert"
  this.seatNumber = 42
  buildConfirmationCode("Concert", 42):
    prefix = "Concert".substring(0, min(3,7)=3).toUpperCase() = "CON"
    return "CON-42"
  this.confirmationCode = "CON-42"
```

**Final output.** `t1.confirmationCode` prints `"CON-42"`; `t2 = new Ticket("Ballet", 7)` follows the identical process, computing `"Ballet".substring(0,3).toUpperCase() = "BAL"`, giving `"BAL-7"`.

## 7. Gotchas & takeaways

> **A constructor has no return type at all — not even `void`.** Writing `void Ticket(String eventName, int seatNumber) { ... }` inside the `Ticket` class does not define a constructor; it defines an ordinary method that happens to share the class's name, which must be called explicitly (`t.Ticket(...)`) rather than running automatically with `new`.

> **If validation inside a constructor throws, the object is never fully created and no reference to it ever exists anywhere** — this is precisely why validating in the constructor (rather than in a separate method called after `new`) is the strongest guarantee against invalid objects: there is no window during which an invalid object could be accessed by other code.

- A constructor runs automatically when `new` is called, and is responsible for setting up the object's complete initial state.
- Constructors share the class's exact name and declare no return type, not even `void`.
- Validating required invariants inside the constructor (throwing on invalid input) guarantees no invalid object is ever created or returned.
- A constructor can compute and assign derived fields directly, ensuring they're always consistent with the object's other fields from the moment it exists.
