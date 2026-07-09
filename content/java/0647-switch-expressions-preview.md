---
card: java
gi: 647
slug: switch-expressions-preview
title: Switch expressions (preview)
---

## 1. What it is

**Switch expressions**, introduced as a **preview feature** (JEP 325) in **Java 12**, let you use `switch` as an *expression* that produces a value, not just a *statement* that runs code. The new form uses an arrow (`->`) instead of `:` and `break`, each case yields its result directly, and there is no fall-through between cases. You can assign the result straight to a variable: `int x = switch (day) { case MONDAY -> 1; default -> 0; };`. Because it was a preview feature, it had to be enabled explicitly with `--enable-preview` when compiling and running, and the syntax was still being refined (it was finalized as a permanent feature two versions later, in Java 14).

## 2. Why & when

The classic `switch` statement is one of Java's oldest sources of bugs: forgetting a `break` lets execution "fall through" into the next case, and using `switch` to *compute* a value required declaring a mutable variable outside the switch and assigning it inside every branch. Switch expressions fix both problems at once — each arm produces exactly one value, there's no accidental fall-through, and the compiler checks that every possible input is covered (exhaustiveness). Reach for a switch expression whenever you're mapping one value to another (an enum to a string, a status code to a message) instead of writing a statement that mutates a variable. Reach for the classic `switch` statement when you genuinely need to run different blocks of side-effecting code with no single "result" to hand back.

## 3. Core concept

```java
// Old style: switch STATEMENT, must declare + mutate a variable
int numLetters;
switch (day) {
    case MONDAY:
    case FRIDAY:
    case SUNDAY:
        numLetters = 6;
        break;
    case TUESDAY:
        numLetters = 7;
        break;
    default:
        numLetters = 9;
}

// New style: switch EXPRESSION, produces a value directly
int numLetters = switch (day) {
    case MONDAY, FRIDAY, SUNDAY -> 6;
    case TUESDAY                -> 7;
    default                     -> 9;
};
```

Notice `case MONDAY, FRIDAY, SUNDAY ->` groups several labels into one arm — no more stacking `case` lines to fall through on purpose. Each arm after `->` is either a single expression (its value is the switch's value) or a `{ ... }` block that ends with a `yield <value>;` statement.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Classic switch statement mutates a variable across branches with possible fall-through; switch expression yields one value with no fall-through">
  <rect x="10" y="10" width="290" height="180" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="32" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">switch STATEMENT</text>
  <text x="25" y="55" fill="#e6edf3" font-size="10" font-family="monospace">case MONDAY:</text>
  <text x="25" y="70" fill="#8b949e" font-size="10" font-family="monospace">  x = 6; // no break!</text>
  <text x="25" y="88" fill="#e6edf3" font-size="10" font-family="monospace">case TUESDAY:</text>
  <text x="25" y="103" fill="#e6edf3" font-size="10" font-family="monospace">  x = 7; break;</text>
  <text x="25" y="130" fill="#f85149" font-size="9" font-family="sans-serif">Falls through MONDAY</text>
  <text x="25" y="145" fill="#f85149" font-size="9" font-family="sans-serif">into TUESDAY's code —</text>
  <text x="25" y="160" fill="#f85149" font-size="9" font-family="sans-serif">a classic bug source.</text>

  <rect x="320" y="10" width="290" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="32" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">switch EXPRESSION</text>
  <text x="335" y="55" fill="#e6edf3" font-size="10" font-family="monospace">int x = switch (day) {</text>
  <text x="335" y="70" fill="#79c0ff" font-size="10" font-family="monospace">  case MONDAY -> 6;</text>
  <text x="335" y="85" fill="#79c0ff" font-size="10" font-family="monospace">  case TUESDAY -> 7;</text>
  <text x="335" y="100" fill="#e6edf3" font-size="10" font-family="monospace">};</text>
  <text x="335" y="130" fill="#6db33f" font-size="9" font-family="sans-serif">Each arm yields exactly</text>
  <text x="335" y="145" fill="#6db33f" font-size="9" font-family="sans-serif">one value. No fall-through,</text>
  <text x="335" y="160" fill="#6db33f" font-size="9" font-family="sans-serif">no mutable helper variable.</text>
</svg>

The arrow form removes fall-through entirely and turns `switch` into something that hands back a value like any other expression.

## 5. Runnable example

Scenario: converting a day of the week into the number of letters in its name — first with the old fall-through-prone statement, then as a preview switch expression, then combining multiple case labels and a `yield` block for a more elaborate computation.

### Level 1 — Basic

```java
// File: SwitchOld.java
public class SwitchOld {
    public static void main(String[] args) {
        for (String day : new String[]{"MONDAY", "TUESDAY", "SATURDAY"}) {
            int numLetters;
            switch (day) {
                case "MONDAY":
                case "FRIDAY":
                case "SUNDAY":
                    numLetters = 6;
                    break;
                case "TUESDAY":
                    numLetters = 7;
                    break;
                default:
                    numLetters = 9;
            }
            System.out.println(day + " -> " + numLetters + " letters");
        }
    }
}
```

**How to run:** `java SwitchOld.java` (works on any JDK; no preview flag needed — this is the old statement form).

Expected output:
```
MONDAY -> 6 letters
TUESDAY -> 7 letters
SATURDAY -> 9 letters
```

### Level 2 — Intermediate

```java
// File: SwitchExpr.java
public class SwitchExpr {
    public static void main(String[] args) {
        for (String day : new String[]{"MONDAY", "TUESDAY", "SATURDAY"}) {
            int numLetters = switch (day) {
                case "MONDAY", "FRIDAY", "SUNDAY" -> 6;
                case "TUESDAY" -> 7;
                default -> 9;
            };
            System.out.println(day + " -> " + numLetters + " letters");
        }
    }
}
```

**How to run:** requires the preview flag on both compile and run since this is a Java 12 preview feature:
```
javac --release 12 --enable-preview SwitchExpr.java
java --enable-preview SwitchExpr
```
(On modern JDKs 14+, switch expressions are permanent and no `--enable-preview` flag is needed at all — the example still compiles and runs unchanged.)

Expected output is identical to Level 1, but the loop body shrank from a 9-line statement to a single expression assigned directly to `numLetters` — no mutable variable declared outside the switch, no `break` to forget.

### Level 3 — Advanced

```java
// File: SwitchAdvanced.java
public class SwitchAdvanced {
    static int workHoursFor(String day) {
        return switch (day) {
            case "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY" -> {
                int base = 8;
                boolean isFriday = day.equals("FRIDAY");
                yield isFriday ? base - 1 : base; // early finish on Friday
            }
            case "SATURDAY", "SUNDAY" -> 0;
            default -> throw new IllegalArgumentException("Not a day: " + day);
        };
    }

    public static void main(String[] args) {
        for (String day : new String[]{"MONDAY", "FRIDAY", "SUNDAY"}) {
            System.out.println(day + " -> " + workHoursFor(day) + " work hours");
        }
        try {
            workHoursFor("FUNDAY");
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac --release 12 --enable-preview SwitchAdvanced.java && java --enable-preview SwitchAdvanced`

Expected output:
```
MONDAY -> 8 work hours
FRIDAY -> 7 work hours
SUNDAY -> 0 work hours
Rejected: Not a day: FUNDAY
```

Level 3 shows a `{ ... }` block arm that runs several statements and finishes with `yield` to produce the switch's value, plus a `default` arm that `throw`s instead of yielding — the compiler accepts this because a thrown exception never needs to produce a value.

## 6. Walkthrough

1. `main` calls `workHoursFor("FRIDAY")`. Control enters the `switch (day)` expression with `day = "FRIDAY"`.
2. The switch evaluates its arms top to bottom looking for a matching label. `"FRIDAY"` matches the first arm's label list (`"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"`), so execution jumps into that arm's `{ ... }` block — no other arm is checked and there is no fall-through risk.
3. Inside the block, `base` is set to `8`, then `isFriday` checks `day.equals("FRIDAY")`, which is `true`.
4. `yield isFriday ? base - 1 : base;` computes `7` and hands it back as the *value of the entire switch expression* — `yield` is to a switch expression what `return` is to a method.
5. Back in `main`, that `7` is what `workHoursFor` returns, and `System.out.println` prints `FRIDAY -> 7 work hours`.
6. For `"SUNDAY"`, the arm `case "SATURDAY", "SUNDAY" -> 0;` matches directly — a single expression arm needs no `yield`; the value after `->` *is* the result.
7. For `"FUNDAY"`, no `case` label matches, so control falls to `default -> throw new IllegalArgumentException(...)`. Throwing is a valid arm body because it never returns a value — control leaves the method entirely via the exception, which `main`'s `catch` block catches and prints.

```
day="FRIDAY" ──► switch matches label group ──► block runs ──► yield 7 ──► workHoursFor returns 7
```

## 7. Gotchas & takeaways

> This is a **preview feature** in Java 12 — it requires `--enable-preview` on both `javac` and `java`, and preview APIs can change or be removed before becoming final. Switch expressions did change slightly (the `yield` keyword itself was refined) before becoming permanent in Java 14; don't rely on Java 12 preview syntax being byte-for-byte identical to the final version in production code.

- Arrow arms (`case X ->`) never fall through; only the matching arm executes.
- Multiple labels can share one arm: `case MONDAY, FRIDAY, SUNDAY ->`.
- Use `yield` inside a `{ }` block arm to produce the expression's value; a single expression after `->` doesn't need `yield`.
- The compiler checks exhaustiveness — for non-enum types you still need a `default` arm, or the code won't compile.
- An arm can `throw` instead of yielding a value, which is useful for rejecting unexpected inputs.
