---
card: java
gi: 192
slug: constructor-overloading
title: Constructor overloading
---

## 1. What it is

**Constructor overloading** means defining multiple constructors in the same class with different signatures (different parameter lists), giving callers several ways to create an object depending on what information they have available. Java also allows one constructor to call another constructor **in the same class** using `this(...)` as its very first statement, avoiding duplicated setup logic across the overloads.

```java
class Rectangle {
    double width;
    double height;

    Rectangle(double width, double height) { // full constructor
        this.width = width;
        this.height = height;
    }

    Rectangle(double side) { // overload: a square, delegates to the full constructor
        this(side, side); // must be the FIRST statement in this constructor
    }
}

Rectangle r1 = new Rectangle(4, 5); // uses the two-arg constructor directly
Rectangle r2 = new Rectangle(4);    // uses the one-arg constructor, which delegates to the two-arg one
```

`this(side, side)` calls the other constructor in the same class, passing `side` for both `width` and `height` — this delegation must be the constructor's very first line, and Java enforces this rule at compile time.

## 2. Why & when

Constructor overloading exists to offer flexible, convenient ways to create objects without forcing every caller to supply every possible piece of information, while avoiding duplicated initialization logic:

- **Convenience overloads** — a "full" constructor requiring every detail, plus simpler overloads that fill in sensible values for the rest (like the square-from-side example above, or a constructor that assumes a default color, quantity, or starting state).
- **Avoiding duplicated logic with `this(...)`** — rather than repeating validation and assignment code in every overload, simpler constructors delegate to the most complete one, so validation logic lives in exactly one place.
- **Matching real-world creation scenarios** — sometimes you know a full set of details, and sometimes you only know a subset; overloaded constructors let both scenarios construct a valid object cleanly, without needing separate factory methods for each case.

You add constructor overloads when there are genuinely multiple sensible ways a caller might reasonably want to create an instance of your class — as opposed to just one constructor that always demands every field's value up front, even when some of those values usually don't vary.

## 3. Core concept

```java
class Pizza {
    String size;
    int toppingCount;

    Pizza(String size, int toppingCount) { // most detailed constructor — the "designated" one
        if (toppingCount < 0) {
            throw new IllegalArgumentException("Topping count cannot be negative: " + toppingCount);
        }
        this.size = size;
        this.toppingCount = toppingCount;
    }

    Pizza(String size) { // overload: assumes no toppings, delegates for validation too
        this(size, 0);
    }

    Pizza() { // overload: assumes a default medium size and no toppings
        this("medium", 0);
    }
}
```

All three constructors ultimately run through the two-argument constructor's validation (`toppingCount < 0`) via `this(...)` delegation — even `new Pizza()`, which supplies no toppings information at all, still passes through the exact same check (with `0`, which always passes), so the validation logic never needs to be duplicated or risk going out of sync between overloads.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three overloaded Pizza constructors, with the no argument and one argument versions both delegating via this to the two argument designated constructor which performs the actual validation and field assignment">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="52" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Pizza()</text>

  <rect x="30" y="80" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="105" y="102" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">Pizza(size)</text>

  <rect x="330" y="55" width="240" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="450" y="75" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Pizza(size, toppingCount)</text>
  <text x="450" y="90" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">validation + assignment here</text>

  <line x1="180" y1="47" x2="330" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#d)"/>
  <text x="240" y="50" fill="#79c0ff" font-size="9" font-family="sans-serif">this("medium", 0)</text>

  <line x1="180" y1="97" x2="330" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#d)"/>
  <text x="240" y="105" fill="#79c0ff" font-size="9" font-family="sans-serif">this(size, 0)</text>

  <defs><marker id="d" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Every path ends up running the same validation exactly once, in one place.</text>
</svg>

Simpler overloads delegate to the most complete constructor via `this(...)`, keeping validation in one place.

## 5. Runnable example

Scenario: representing a simple `Email` message — starting with two basic overloaded constructors, then extending with a third overload delegating through the chain, then hardening into a version where the designated constructor performs real validation shared correctly by every overload.

### Level 1 — Basic

```java
public class EmailBasic {
    static class Email {
        String to;
        String subject;

        Email(String to, String subject) {
            this.to = to;
            this.subject = subject;
        }

        Email(String to) { // overload: default subject
            this(to, "(no subject)");
        }
    }

    public static void main(String[] args) {
        Email e1 = new Email("ann@example.com", "Meeting notes");
        Email e2 = new Email("bo@example.com"); // uses the default subject

        System.out.println(e1.to + ": " + e1.subject);
        System.out.println(e2.to + ": " + e2.subject);
    }
}
```

**How to run:** `java EmailBasic.java`

`new Email("bo@example.com")` matches the one-argument constructor, which immediately delegates to the two-argument constructor via `this(to, "(no subject)")` — both constructors ultimately run the exact same assignment logic, just with different supplied values for `subject`.

### Level 2 — Intermediate

Same `Email`, now with a third overload — a fully default, no-argument constructor — extending the delegation chain one level further.

```java
public class EmailIntermediate {
    static class Email {
        String to;
        String subject;

        Email(String to, String subject) {
            this.to = to;
            this.subject = subject;
        }

        Email(String to) {
            this(to, "(no subject)");
        }

        Email() { // overload: no recipient or subject specified yet
            this("undisclosed-recipients@example.com", "(no subject)");
        }
    }

    public static void main(String[] args) {
        Email draft = new Email(); // fully default
        System.out.println(draft.to + ": " + draft.subject);
    }
}
```

**How to run:** `java EmailIntermediate.java`

`new Email()` calls the no-argument constructor, which itself calls `this("undisclosed-recipients@example.com", "(no subject)")`, ultimately running the two-argument constructor's assignment logic — a chain three constructors deep, each adding one layer of convenient defaults on top of the one below it.

### Level 3 — Advanced

Same `Email`, now with the designated (two-argument) constructor performing real validation, correctly shared by every overload in the delegation chain, including a case where the *default* value itself would need to be valid too.

```java
public class EmailAdvanced {
    static class Email {
        String to;
        String subject;

        Email(String to, String subject) { // designated constructor — all validation lives here
            if (to == null || !to.contains("@")) {
                throw new IllegalArgumentException("Invalid recipient address: " + to);
            }
            this.to = to;
            this.subject = (subject == null || subject.isEmpty()) ? "(no subject)" : subject;
        }

        Email(String to) {
            this(to, null); // delegate; designated constructor handles the null subject
        }
    }

    public static void main(String[] args) {
        Email valid = new Email("ann@example.com");
        System.out.println(valid.to + ": " + valid.subject);

        try {
            new Email("not-an-email");
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java EmailAdvanced.java`

`Email(String to)` passes `null` for `subject` via `this(to, null)`, relying on the designated constructor's own `(subject == null || subject.isEmpty())` check to substitute the default text — this means the "what counts as a valid/default subject" logic exists in exactly one place, and every overload automatically benefits from it without repeating the check.

## 6. Walkthrough

Trace `new Email("not-an-email")` from `EmailAdvanced.main`:

**Overload matched.** One argument, a `String` — matches `Email(String to)`.

**Delegation.** `this(to, null)` is the first (and only) statement in `Email(String to)`; it immediately invokes `Email(String to, String subject)` with `to = "not-an-email"` and `subject = null`.

**Validation in the designated constructor.** `to == null || !to.contains("@")` — `to` isn't `null`, but `"not-an-email".contains("@")` is `false`, so `!false` is `true` — the overall condition is `true`. The guard throws `IllegalArgumentException("Invalid recipient address: not-an-email")` immediately.

**Propagation.** Because the exception is thrown inside the designated constructor, which was invoked via `this(...)` from `Email(String to)`, it propagates straight back out through both constructor calls to `new Email("not-an-email")` in `main` — no `Email` object is ever created, at any point in the chain.

```
new Email("not-an-email")
  matches Email(String to)
  -> this(to, null) delegates to Email(String to, String subject)
     to.contains("@")? false -> !false = true -> guard fires
     throw IllegalArgumentException("Invalid recipient address: not-an-email")
  exception propagates all the way back out of new Email(...)
```

**Caught in `main`.** Prints `"Rejected: Invalid recipient address: not-an-email"`.

**Contrast with `new Email("ann@example.com")`.** This one-argument call delegates to the designated constructor with `subject = null`; validation passes (`"ann@example.com".contains("@")` is `true`), and `this.subject = (null == null || ...) ? "(no subject)" : subject` evaluates to `"(no subject)"`, since the first half of the condition is already `true`. Prints `"ann@example.com: (no subject)"`.

## 7. Gotchas & takeaways

> **`this(...)` (calling another constructor) must be the very first statement in a constructor — nothing, not even a validation check, can come before it.** Attempting to run any code before the `this(...)` call is a compile error; if you need to validate an argument *before* delegating, that validation must live in the constructor being delegated *to*, not the one doing the delegating.

> **Constructor overloading is a compile-time mechanism — the compiler picks which constructor to run based purely on the number and types of arguments at each `new` call site.** Just like ordinary method overloading, two constructors that would have identical signatures (even with different parameter names) cannot coexist in the same class.

- Constructor overloading provides multiple ways to create an object, matched by the compiler based on the arguments supplied.
- `this(...)` calls another constructor in the same class and must be the first statement in the calling constructor.
- Centralizing validation and full initialization in one "designated" constructor, with simpler overloads delegating to it via `this(...)`, avoids duplicating that logic across every overload.
- Every overload in a delegation chain ultimately still passes through the designated constructor's checks, so no overload can bypass the validation the class relies on.
