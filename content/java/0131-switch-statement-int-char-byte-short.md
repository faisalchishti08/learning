---
card: java
gi: 131
slug: switch-statement-int-char-byte-short
title: switch statement (int/char/byte/short)
---

## 1. What it is

The classic `switch` statement selects one of several code paths based on the exact value of a single expression, comparing it against a list of constant `case` labels. The original (Java 1.0–era) form works with `int` and types that implicitly widen to `int` for this purpose (`byte`, `short`, `char`, and their boxed wrapper equivalents) — `String` and `enum` support were added in later versions. Execution jumps directly to the `case` label matching the switch expression's value, and (in this classic form) continues running from there through subsequent `case` labels until it hits a `break` or the end of the `switch` block — this "fall-through" behavior is covered in depth in the next topic; here we focus on the basic matching mechanism.

```java
int dayNumber = 3;
switch (dayNumber) {
    case 1:
        System.out.println("Monday");
        break;
    case 2:
        System.out.println("Tuesday");
        break;
    case 3:
        System.out.println("Wednesday");
        break;
    default:
        System.out.println("Unknown day");
}
```

Each `case` label must be a **compile-time constant** (a literal, a `final` variable initialized with a constant expression, or an enum constant) — you cannot `case` on a variable or a runtime-computed expression, which is a key difference from an `else if` chain, where each condition can be an arbitrary boolean expression evaluated at runtime.

## 2. Why & when

`switch` is preferable to an `else if` chain when branching on the exact value of a single variable against a set of discrete possibilities, especially once there are more than a handful of cases:

- Mapping a numeric or character code to a named action or label (day numbers, menu choices, simple state machines).
- Dispatching on a small, fixed set of `enum` or `char` values, where the switch's structure makes the full set of handled cases visually clear at a glance.
- Situations where the JVM can potentially optimize a `switch` over small, dense integer ranges into a fast jump table, rather than a sequence of comparisons — though this is a performance detail secondary to the readability benefit for most application code.

`switch` is the wrong tool when conditions involve ranges (`score >= 90`), multiple variables, or arbitrary boolean logic — those scenarios still call for `if`/`else if` chains.

## 3. Core concept

```java
public class SwitchDemo {
    public static void main(String[] args) {
        int dayNumber = 3;

        switch (dayNumber) {
            case 1:
                System.out.println("Monday");
                break;
            case 2:
                System.out.println("Tuesday");
                break;
            case 3:
                System.out.println("Wednesday");
                break;
            case 4:
                System.out.println("Thursday");
                break;
            case 5:
                System.out.println("Friday");
                break;
            default:
                System.out.println("Weekend or invalid day");
                break;
        }

        // char works directly as a switch expression too
        char grade = 'B';
        switch (grade) {
            case 'A':
                System.out.println("Excellent");
                break;
            case 'B':
                System.out.println("Good");
                break;
            case 'C':
                System.out.println("Average");
                break;
            default:
                System.out.println("Needs improvement");
        }

        // byte and short widen implicitly to int for the switch comparison
        byte statusCode = 2;
        switch (statusCode) {
            case 0: System.out.println("Idle"); break;
            case 1: System.out.println("Running"); break;
            case 2: System.out.println("Paused"); break;
            default: System.out.println("Unknown status");
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="switch statement diagram: the switch expression value 3 is compared against each case label, jumping directly to the matching case 3 label and skipping cases 1 and 2 entirely, then executing until the break statement is reached.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">switch (dayNumber) with dayNumber = 3 — jumps directly to the matching case</text>

  <rect x="30" y="40" width="110" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="85" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">case 1: (skip)</text>

  <rect x="150" y="40" width="110" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="205" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">case 2: (skip)</text>

  <rect x="270" y="40" width="130" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="57" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">case 3: MATCH ✓</text>

  <path d="M 335 66 L 335 90" stroke="#6db33f" stroke-width="2" marker-end="url(#a)"/>
  <rect x="240" y="90" width="190" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">print "Wednesday"; break;</text>

  <text x="335" y="146" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Execution jumps directly here — cases 1 and 2 are never even compared sequentially like an if-chain.</text>
</svg>

`switch` jumps directly to the matching label rather than sequentially testing each preceding condition the way an `else if` chain does.

## 5. Runnable example

Scenario: a simple traffic-light controller that maps a light color code to an action — starting with a basic int-based switch, then a char-based menu dispatcher, then a combined validated dispatcher handling an out-of-range input.

### Level 1 — Basic

```java
public class TrafficLightBasic {
    public static void main(String[] args) {
        int lightCode = 1;   // 0=red, 1=yellow, 2=green

        switch (lightCode) {
            case 0:
                System.out.println("STOP");
                break;
            case 1:
                System.out.println("SLOW DOWN");
                break;
            case 2:
                System.out.println("GO");
                break;
            default:
                System.out.println("INVALID SIGNAL");
        }
    }
}
```

**How to run:** `java TrafficLightBasic.java`

`switch (lightCode)` compares `lightCode`'s value (`1`) against each `case` label in turn, jumping directly to `case 1:` once a match is found — the code prints `"SLOW DOWN"` and then hits `break;`, which exits the `switch` block immediately, skipping `case 2:` and `default:` entirely.

### Level 2 — Intermediate

Same controller, now driven by a `char` command input from a simple text-based menu, demonstrating `switch` working directly on `char` values without any explicit conversion.

```java
public class MenuIntermediate {
    public static void main(String[] args) {
        char[] commands = { 'n', 's', 'q', 'x' };

        for (char command : commands) {
            switch (command) {
                case 'n':
                    System.out.println("Moving north.");
                    break;
                case 's':
                    System.out.println("Moving south.");
                    break;
                case 'q':
                    System.out.println("Quitting.");
                    break;
                default:
                    System.out.println("Unrecognized command: '" + command + "'");
            }
        }
    }
}
```

**How to run:** `java MenuIntermediate.java`

`switch (command)` works directly on the `char` value without any manual conversion to `int` — internally, `char` is an integer type and is compared directly against each `case` label's character literal (which is itself just a compact way of writing that character's underlying numeric code point). `'x'` matches none of the explicit cases, so execution falls through to `default:`, printing the "unrecognized" message.

### Level 3 — Advanced

Same traffic-light system, now validating the input is within the expected `byte`-range status codes before switching, and using grouped `case` labels (multiple labels sharing one body — a preview of fall-through mechanics, covered fully in the next topic) to treat several related status codes identically.

```java
public class TrafficLightAdvanced {

    static void handleSignal(byte code) {
        switch (code) {
            case 0:
                System.out.println("STOP (solid red)");
                break;
            case 1:
            case 4:   // both a standard yellow AND a special "flashing yellow" code map to the same action
                System.out.println("SLOW DOWN");
                break;
            case 2:
                System.out.println("GO");
                break;
            case 3:
                System.out.println("PROCEED WITH CAUTION (flashing red, treat as stop-then-go)");
                break;
            default:
                throw new IllegalArgumentException("Unrecognized signal code: " + code);
        }
    }

    public static void main(String[] args) {
        byte[] codes = { 0, 1, 2, 3, 4 };
        for (byte code : codes) {
            handleSignal(code);
        }

        try {
            handleSignal((byte) 99);   // invalid, out-of-range code
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java TrafficLightAdvanced.java`

`case 1: case 4:` stacks two labels with no statements between them, meaning both `1` and `4` jump to the *same* shared body — this is a deliberate, common use of `switch`'s fall-through mechanics to treat multiple distinct input values identically without duplicating the body. `byte code` is implicitly widened to `int` for the comparison against each `case` label, exactly as described in Section 1 — this works transparently and requires no special syntax. The `default:` branch here throws an exception rather than merely printing a message, demonstrating that `switch` is not limited to producing output; any valid Java statement, including a `throw`, is legal inside a `case` body, making `default` a natural place to reject genuinely invalid input.

## 6. Walkthrough

Trace `handleSignal((byte) 4)`:

**Promotion.** `code` is declared `byte` with value `4`. Before the `switch` compares it against any `case` label, `code` is implicitly widened to `int` (unary numeric promotion, the same rule that applies throughout Java's integer operators) — this happens transparently and requires no cast in the source code.

**Matching.** The `switch` compares the promoted value, `4`, against each `case` label in the order they're checked internally (conceptually, though the JVM may implement this as a jump table rather than a literal sequential scan for dense integer ranges). It finds a match at `case 4:`.

**Falling into the shared body.** Because `case 1:` and `case 4:` are stacked with no code between them, `case 4:` has no body of its own to execute — execution falls straight through from the `case 4:` label into the body that follows both labels: `System.out.println("SLOW DOWN"); break;`.

**Break exits.** After printing `"SLOW DOWN"`, the `break;` statement is reached, which exits the `switch` block entirely — `case 2:`, `case 3:`, and `default:` are never reached for this call.

```
handleSignal(code=4):

promote byte 4 -> int 4
switch matches: case 4:   (case 1: and case 4: share one body)
        |
        v
  no code between "case 1:" and "case 4:" -- execution falls through the label
        |
        v
  System.out.println("SLOW DOWN");
  break;   <- exits switch here
```

**Final output.** The loop over `{0, 1, 2, 3, 4}` prints the STOP, SLOW DOWN (from case 1), GO, PROCEED WITH CAUTION, and SLOW DOWN (from case 4, sharing case 1's body) messages in turn, and the final out-of-range call with `99` falls through every explicit `case` to `default:`, where it throws and is caught, printing the rejection message.

## 7. Gotchas & takeaways

> **`case` labels must be compile-time constants — you cannot switch on a variable's current value as a label, or use a range/comparison expression as a label.** `case (x > 5):` and `case someVariable:` (where `someVariable` is not itself a `final` constant) are both illegal; only literals, `final` constant-initialized variables, and (for a `String`/`enum` switch) their respective constant forms are permitted as labels.

> **Stacking `case` labels with no statements between them (`case 1: case 4: ...`) makes both labels share the same body** — this is a deliberate, idiomatic use of fall-through for grouping multiple input values that should be treated identically, distinct from accidentally forgetting a `break` (covered in depth in the next topic).

- `switch` compares a single expression's exact value against a list of constant `case` labels, jumping directly to the matching one rather than sequentially testing conditions like an `else if` chain.
- `byte`, `short`, and `char` all work directly as `switch` expressions; they are implicitly promoted to `int` for the comparison.
- Each `case` label must be a genuine compile-time constant; `switch` cannot branch on ranges or arbitrary runtime boolean expressions — use `if`/`else if` for those.
- `default:` handles any value not matched by an explicit `case`, and (like any `case` body) can contain arbitrary statements, including throwing an exception to reject invalid input.
