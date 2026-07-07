---
card: java
gi: 374
slug: enums-in-switch-statements
title: Enums in switch statements
---

## 1. What it is

Java's `switch` statement (and, since Java 14, `switch` expression) has special support for enums: inside the `switch`, each `case` label is written as just the bare constant name (`case MONDAY:`), without the enum type prefix you'd normally need (`Day.MONDAY`). The compiler already knows the type being switched on, so it resolves the bare name against that enum automatically. Combined with an enum's small, fixed set of constants, the compiler can also check whether a `switch` covers every possible value — an **exhaustiveness** check unavailable for `switch` on `int` or `String`.

## 2. Why & when

Switching on an enum is the most common way to write per-constant logic when you don't want (or can't justify) constant-specific method bodies (see [[constant-specific-method-bodies]]) — for instance, when the logic genuinely belongs outside the enum, in a caller that only cares about this one specific use case, not a general behaviour the enum itself should expose. It's also simply idiomatic: reading a `switch` over an enum's constants at a glance shows every case being handled, in one place, without hunting through separate constant-specific method bodies scattered across the enum declaration.

The traditional `switch` statement (with `case X: ... break;`) does **not** by itself guarantee every constant is handled — a missing `case` just silently falls through to `default` or does nothing. The newer `switch` **expression** (`case X -> ...`, used as a value) is different: when it has no `default` and the compiler can prove every enum constant is covered, it's exhaustive, and forgetting a constant is a compile error. This exhaustiveness check is one of the strongest practical arguments for using switch expressions over classic switch statements when working with enums.

## 3. Core concept

```java
public class SwitchEnumDemo {
    enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

    static String describe(Day d) {
        return switch (d) { // no "Day." prefix needed on case labels
            case MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY -> "Weekday";
            case SATURDAY, SUNDAY -> "Weekend";
            // no default needed -- every Day constant is handled, compiler verifies this
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(Day.WEDNESDAY));
        System.out.println(describe(Day.SUNDAY));
    }
}
```

**How to run:** `java SwitchEnumDemo.java`

Case labels are bare (`MONDAY`, not `Day.MONDAY`) because the compiler already knows `d`'s type from `switch (d)`. Multiple constants can share one arrow-case (`MONDAY, TUESDAY, ... ->`). Because every one of `Day`'s seven constants appears across the two cases, no `default` branch is required — the switch expression is exhaustive, and the compiler would reject this code if a constant were missing.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a switch expression over an enum with every constant covered by some case is exhaustive, needing no default and rejected at compile time if a constant is missing">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">switch (d) { case MON,TUE,WED,THU,FRI -&gt; "Weekday"; case SAT,SUN -&gt; "Weekend"; }</text>

  <rect x="30" y="50" width="280" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="170" y="75" fill="#6db33f" font-size="10" text-anchor="middle">MON TUE WED THU FRI -&gt; "Weekday"</text>

  <rect x="330" y="50" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="405" y="75" fill="#6db33f" font-size="10" text-anchor="middle">SAT SUN -&gt; "Weekend"</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">All 7 Day constants appear across the two cases -- exhaustive, no default needed.</text>
  <text x="20" y="140" fill="#f85149" font-size="10">Remove SUNDAY from either case and this becomes a compile error, not a silent runtime gap.</text>
</svg>

## 5. Runnable example

Scenario: computing a shipping estimate from an order's status, evolved from a classic `switch` statement that silently falls through on a missing case, through an exhaustive switch expression that catches that mistake at compile time, to a version combining exhaustiveness with a guard-clause style default for genuinely open-ended future values.

### Level 1 — Basic

```java
public class ShippingSwitchStatement {
    enum Status { PENDING, SHIPPED, DELIVERED }

    static String estimate(Status status) {
        String result = "unknown";
        switch (status) { // classic switch statement -- NOT exhaustiveness-checked
            case PENDING:
                result = "3-5 days";
                break;
            case SHIPPED:
                result = "1-2 days";
                break;
            // DELIVERED accidentally forgotten -- compiles fine anyway!
        }
        return result;
    }

    public static void main(String[] args) {
        System.out.println(estimate(Status.SHIPPED));
        System.out.println(estimate(Status.DELIVERED)); // silently falls through to "unknown"
    }
}
```

**How to run:** `java ShippingSwitchStatement.java`

This compiles without any warning even though `DELIVERED` was forgotten — the classic `switch` statement provides no exhaustiveness check, so the bug (falling through to the pre-initialised `"unknown"`) only surfaces when `estimate(Status.DELIVERED)` actually runs, and even then, it's easy to misread as a legitimate result rather than a bug.

### Level 2 — Intermediate

```java
public class ShippingSwitchExpression {
    enum Status { PENDING, SHIPPED, DELIVERED }

    static String estimate(Status status) {
        return switch (status) { // switch EXPRESSION -- compiler checks exhaustiveness
            case PENDING -> "3-5 days";
            case SHIPPED -> "1-2 days";
            case DELIVERED -> "Delivered"; // must be present, or this fails to compile
        };
    }

    public static void main(String[] args) {
        System.out.println(estimate(Status.SHIPPED));
        System.out.println(estimate(Status.DELIVERED));
    }
}
```

**How to run:** `java ShippingSwitchExpression.java`

Rewritten as a switch expression with no `default`, the compiler now requires every `Status` constant to appear as a case — omitting `DELIVERED` here (as Level 1 accidentally did) would be a compile error: `the switch expression does not cover all possible input values`, catching the exact class of bug Level 1 let through silently.

### Level 3 — Advanced

```java
public class ShippingCancellable {
    enum Status { PENDING, SHIPPED, DELIVERED, CANCELLED, RETURNED }

    static String estimate(Status status) {
        return switch (status) {
            case PENDING -> "3-5 days";
            case SHIPPED -> "1-2 days";
            case DELIVERED -> "Delivered";
            case CANCELLED, RETURNED -> { // block form: needs a yield, not just an expression
                System.out.println("Note: order will not be shipped (" + status + ")");
                yield "N/A";
            }
        };
    }

    public static void main(String[] args) {
        System.out.println("Result: " + estimate(Status.CANCELLED));
        System.out.println("Result: " + estimate(Status.DELIVERED));
    }
}
```

**How to run:** `java ShippingCancellable.java`

`CANCELLED` and `RETURNED` share a `{ ... }` block body (instead of a single expression), which runs a side-effecting statement (the `println`) before producing its result with `yield` — this shows that switch-expression cases aren't limited to one-liners, and that adding new constants (`CANCELLED`, `RETURNED`) to the enum still forces every case to be accounted for, keeping the exhaustiveness guarantee intact as the enum grows.

## 6. Walkthrough

Execution starts in `main`. `estimate(Status.CANCELLED)` is called first. Inside, `switch (status)` evaluates `status`, which is `Status.CANCELLED`. The compiler-generated dispatch matches it against `case CANCELLED, RETURNED ->` — since `CANCELLED` is one of the two constants listed for that case, this branch's block body runs.

Inside the block: `System.out.println("Note: order will not be shipped (" + status + ")")` runs first, printing `Note: order will not be shipped (CANCELLED)`. Then `yield "N/A"` produces the switch expression's result — `"N/A"` — which becomes the return value of `estimate`.

Back in `main`, `"Result: " + estimate(Status.CANCELLED)` concatenates to `"Result: N/A"`, which is printed.

`estimate(Status.DELIVERED)` runs next: `switch (status)` matches `case DELIVERED ->`, whose body is the plain expression `"Delivered"` — no block, no `yield` keyword needed since it's a single-expression case. This value is returned directly. `main` prints `Result: Delivered`.

Expected output:
```
Note: order will not be shipped (CANCELLED)
Result: N/A
Result: Delivered
```

## 7. Gotchas & takeaways

> A classic `switch` **statement** (`case X: ... break;`) provides no compiler-enforced exhaustiveness check for enums, even though it might seem like it should — a forgotten case simply does nothing (or falls through to whatever code follows), silently. Prefer a `switch` **expression** (`case X -> ...`, used as a value) whenever you want the compiler to guarantee every constant is handled.

- Case labels inside a `switch` over an enum are written bare (`case MONDAY:` or `case MONDAY ->`), never prefixed with the enum type name — the compiler infers the type from the switched value.
- A `switch` expression with no `default`, where every case together covers all of an enum's constants, is exhaustive — the compiler rejects the code at compile time if a constant is missing.
- Classic `switch` statements do not get this exhaustiveness check; a missing case is a silent runtime gap, not a compile error — this is one of the strongest reasons to prefer switch expressions for enum dispatch.
- Multiple constants can share one case (`case CANCELLED, RETURNED -> ...`), and a case body can be a block (`{ ... yield value; }`) when it needs more than a single expression.
- Adding a new constant to an enum later will cause every exhaustive switch expression over it to fail to compile until the new constant is explicitly handled — treat this as a feature: the compiler is finding every place that needs updating for you.
