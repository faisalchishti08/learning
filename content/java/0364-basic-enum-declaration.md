---
card: java
gi: 364
slug: basic-enum-declaration
title: Basic enum declaration
---

## 1. What it is

An **enum** (short for enumeration) is a special Java type that represents a fixed, known set of constant values — like the days of the week, or the status of an order. You declare one with the `enum` keyword instead of `class`, and list the allowed values by name, separated by commas. Under the hood, each enum you write becomes a real class, and each constant becomes a `public static final` instance of that class — but the compiler handles all of that for you.

## 2. Why & when

Before Java 5, developers represented fixed sets of options with plain `int` constants (`int MONDAY = 0;`) or `String` constants. Both approaches share the same weakness: nothing stops you from passing `7` or `"Blursday"` where a day of the week is expected — the compiler can't catch the mistake, because an `int` or `String` parameter accepts *any* value of that type, not just the ones that make sense.

Enums fix this by giving the fixed set its own real type. A method that takes an `OrderStatus` parameter can only ever receive one of the values you declared — `PENDING`, `SHIPPED`, `DELIVERED` — never an arbitrary number or typo'd string. The compiler enforces this at compile time, and tools like `switch` can even warn you if you forget to handle one of the possible values.

You reach for an enum whenever a variable's valid values form a small, fixed, known-in-advance set: days of the week, directions (`NORTH`, `SOUTH`, `EAST`, `WEST`), states in a workflow, HTTP methods, and so on — basically anywhere you'd otherwise be tempted to use "magic" integers or strings.

## 3. Core concept

```java
public class OrderStatusDemo {
    enum OrderStatus {
        PENDING, SHIPPED, DELIVERED, CANCELLED // the four, and only four, valid statuses
    }

    public static void main(String[] args) {
        OrderStatus status = OrderStatus.PENDING;
        System.out.println("Status: " + status);
        // OrderStatus bad = OrderStatus.SHELVED; // compile error: no such constant
    }
}
```

**How to run:** `java OrderStatusDemo.java`

`OrderStatus` is declared with `enum`, listing exactly four legal values. `OrderStatus status = OrderStatus.PENDING;` assigns one of them; the commented-out line shows that trying to reference a nonexistent constant (`SHELVED`) is a compile-time error, not something discovered later at runtime.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an enum type defines a fixed, closed set of named constants, each a real singleton instance of the enum type">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="580" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="53" fill="#6db33f" font-size="12" text-anchor="middle">enum OrderStatus</text>

  <rect x="30" y="80" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="105" fill="#79c0ff" font-size="11" text-anchor="middle">PENDING</text>

  <rect x="175" y="80" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="240" y="105" fill="#79c0ff" font-size="11" text-anchor="middle">SHIPPED</text>

  <rect x="320" y="80" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="385" y="105" fill="#79c0ff" font-size="11" text-anchor="middle">DELIVERED</text>

  <rect x="465" y="80" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="105" fill="#79c0ff" font-size="11" text-anchor="middle">CANCELLED</text>

  <text x="20" y="145" fill="#8b949e" font-size="10">Each box is a real, singleton instance of OrderStatus -- no other value of this type can ever exist.</text>
</svg>

## 5. Runnable example

Scenario: representing an order's status, evolved from a fragile `int`-based version, through a safer `String`-based attempt, to the enum version that actually closes off invalid values at compile time.

### Level 1 — Basic

```java
public class OrderIntVersion {
    static final int PENDING = 0;
    static final int SHIPPED = 1;
    static final int DELIVERED = 2;

    static void printStatus(int status) {
        if (status == PENDING) System.out.println("Order is pending");
        else if (status == SHIPPED) System.out.println("Order has shipped");
        else if (status == DELIVERED) System.out.println("Order delivered");
        else System.out.println("Unknown status: " + status);
    }

    public static void main(String[] args) {
        printStatus(SHIPPED);
        printStatus(99); // compiles fine -- nothing stops an invalid int
    }
}
```

**How to run:** `java OrderIntVersion.java`

This is the pre-enum, `int`-constant approach: it compiles and runs, but `printStatus(99)` shows the core weakness — the compiler has no way to reject a nonsensical status value, since any `int` is a legal argument.

### Level 2 — Intermediate

```java
public class OrderStringVersion {
    static void printStatus(String status) {
        switch (status) {
            case "PENDING" -> System.out.println("Order is pending");
            case "SHIPPED" -> System.out.println("Order has shipped");
            case "DELIVERED" -> System.out.println("Order delivered");
            default -> System.out.println("Unknown status: " + status);
        }
    }

    public static void main(String[] args) {
        printStatus("SHIPPED");
        printStatus("Shiped"); // typo compiles fine -- still no compile-time safety
    }
}
```

**How to run:** `java OrderStringVersion.java`

Switching to `String` constants doesn't fix the underlying problem: `"Shiped"` (a typo) compiles perfectly and only fails at *runtime*, falling into `default`. Strings give no more compile-time protection than ints did — just a different flavour of the same mistake.

### Level 3 — Advanced

```java
public class OrderEnumVersion {
    enum OrderStatus { PENDING, SHIPPED, DELIVERED, CANCELLED }

    static void printStatus(OrderStatus status) {
        String message = switch (status) { // compiler checks every case is handled
            case PENDING -> "Order is pending";
            case SHIPPED -> "Order has shipped";
            case DELIVERED -> "Order delivered";
            case CANCELLED -> "Order was cancelled";
        };
        System.out.println(message);
    }

    public static void main(String[] args) {
        printStatus(OrderStatus.SHIPPED);
        printStatus(OrderStatus.CANCELLED);
        // printStatus("Shiped"); // compile error: String is not an OrderStatus
    }
}
```

**How to run:** `java OrderEnumVersion.java`

The parameter type is now `OrderStatus`, an enum — no typo or arbitrary number can be passed where a status is expected, because those values simply aren't of type `OrderStatus`. The `switch` expression on an enum is exhaustive: the compiler verifies every declared constant (`PENDING`, `SHIPPED`, `DELIVERED`, `CANCELLED`) is handled, catching a forgotten case at compile time rather than letting it silently fall through.

## 6. Walkthrough

Execution starts in `main`. `printStatus(OrderStatus.SHIPPED)` passes the singleton constant `OrderStatus.SHIPPED` into `printStatus`. Inside, the `switch (status)` expression compares `status` against each declared case; it matches `case SHIPPED ->`, evaluates to the string `"Order has shipped"`, assigns it to `message`, and `System.out.println(message)` prints it.

`printStatus(OrderStatus.CANCELLED)` runs the same method again with a different constant: the `switch` matches `case CANCELLED ->`, producing `"Order was cancelled"`, which is printed.

The commented-out `printStatus("Shiped")` line demonstrates what the enum type buys you: it doesn't even compile, because a `String` literal is never assignable to an `OrderStatus` parameter — the class of mistake that silently fell through to `default` in the Level 2 `String` version cannot happen here at all, since it's rejected before the program can even be built.

Expected output:
```
Order has shipped
Order was cancelled
```

## 7. Gotchas & takeaways

> An enum constant like `OrderStatus.PENDING` is a genuine singleton object, not a number or string in disguise — comparing two enum values with `==` is always safe and correct, unlike `==` on boxed numbers or strings, precisely because there is only ever one instance of each constant.

- Declare an enum with `enum Name { CONST1, CONST2, ... }` — each listed name becomes a `public static final` singleton instance of the enum type.
- Enums give you compile-time safety that `int` or `String` constants never can: a method parameter typed as an enum can only ever receive one of its declared constants.
- A `switch` over an enum can be exhaustive — the compiler can verify every constant is handled, catching a missed case before the program ever runs.
- By convention, enum constant names are written in `ALL_CAPS`, matching the style used for other constants in Java.
- Prefer enums over `int`/`String` constants any time a value's legal range is a small, fixed, known set of options — it is one of the cheapest and most effective type-safety upgrades available in Java.
