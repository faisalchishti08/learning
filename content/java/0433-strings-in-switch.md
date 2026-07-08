---
card: java
gi: 433
slug: strings-in-switch
title: Strings in switch
---

## 1. What it is

Java 7 allowed `switch` statements to operate directly on `String` values, not just `int`, `char`, `byte`, `short`, or `enum` as before. Internally, the compiler still generates efficient bytecode — it computes `hashCode()` to jump to a candidate branch, then confirms with `equals()` — but from the programmer's point of view, it simply reads as `switch (someString) { case "start": ... }`.

## 2. Why & when

Before Java 7, dispatching on a `String` value meant a chain of `if (str.equals("start")) { ... } else if (str.equals("stop")) { ... } else { ... }` — functionally fine, but visually noisier than a `switch`, and easy to fumble (forgetting `.equals` and accidentally using `==`, which compares references rather than content). Allowing `String` directly in `switch` gave a cleaner, more readable way to express "pick one of several known text values and branch accordingly" — a very common pattern for command dispatchers, configuration parsing, and simple state machines keyed by string identifiers.

You reach for this any time you're branching on a fixed, known set of string values — parsing a command-line argument, dispatching on an HTTP method name, or interpreting a configuration key — anywhere the alternative would be an unwieldy `if`/`else if` chain of `.equals()` calls.

## 3. Core concept

```java
String command = "start";

switch (command) {
    case "start":
        System.out.println("Starting...");
        break;
    case "stop":
        System.out.println("Stopping...");
        break;
    default:
        System.out.println("Unknown command: " + command);
}
```

Matching uses `.equals()` under the hood (not `==`), so this behaves exactly as you'd hope — content equality, not reference identity. A `null` value being switched on throws `NullPointerException` immediately, before any case is checked, so guard against `null` beforehand if it's a possibility.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A switch on a String value dispatches to the matching case label using equals-based comparison, falling through to default if nothing matches">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="90" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">command="stop"</text>

  <rect x="220" y="30" width="100" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="270" y="50" fill="#8b949e" font-size="9" text-anchor="middle">"start"?</text>
  <rect x="220" y="70" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="270" y="90" fill="#6db33f" font-size="9" text-anchor="middle">"stop"? YES</text>
  <rect x="220" y="110" width="100" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="270" y="130" fill="#8b949e" font-size="9" text-anchor="middle">default</text>

  <rect x="420" y="70" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="510" y="90" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">"Stopping..." printed</text>
  <line x1="320" y1="85" x2="415" y2="85" stroke="#6db33f" marker-end="url(asw1)"/>
  <defs><marker id="asw1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Each case label is checked with content equality until a match is found, or `default` runs if none match.

## 5. Runnable example

Scenario: a simple text command dispatcher for a toy device controller — the same dispatcher, evolved from a basic three-command `switch`, through grouped case labels sharing behavior, to a modern switch **expression** returning a value directly rather than relying on `break` statements.

### Level 1 — Basic

```java
public class CommandDispatcherBasic {
    static void handle(String command) {
        switch (command) {
            case "start":
                System.out.println("Starting...");
                break;
            case "stop":
                System.out.println("Stopping...");
                break;
            default:
                System.out.println("Unknown command: " + command);
        }
    }

    public static void main(String[] args) {
        handle("start");
        handle("stop");
        handle("reboot");
    }
}
```

**How to run:** `java CommandDispatcherBasic.java`

Each `case` label is a `String` literal, compared to `command` by content — `"start"` and `"stop"` match their respective branches, and `"reboot"` (matching neither) falls through to `default`.

### Level 2 — Intermediate

```java
public class CommandDispatcherGrouped {
    static void handle(String command) {
        switch (command) {
            case "start":
            case "run":       // multiple labels sharing ONE block -- either string triggers this branch
                System.out.println("Starting...");
                break;
            case "stop":
            case "halt":
                System.out.println("Stopping...");
                break;
            default:
                System.out.println("Unknown command: " + command);
        }
    }

    public static void main(String[] args) {
        handle("run");   // synonym for "start"
        handle("halt");  // synonym for "stop"
        handle("pause"); // not recognized
    }
}
```

**How to run:** `java CommandDispatcherGrouped.java`

Stacking case labels with no code between them (`case "start": case "run":`) lets multiple string values share the same branch — `"run"` falls through the empty `case "start":` label straight into the shared block, exactly as if `"start"` had been typed.

### Level 3 — Advanced

```java
public class CommandDispatcherExpression {
    static String handle(String command) {
        // Modern switch EXPRESSION (Java 14+): returns a value directly, arrow syntax, no fall-through risk
        return switch (command) {
            case "start", "run" -> "Starting...";
            case "stop", "halt" -> "Stopping...";
            case "status" -> {
                String status = "All systems normal";
                yield status; // yield produces the expression's value from a block
            }
            default -> "Unknown command: " + command;
        };
    }

    public static void main(String[] args) {
        System.out.println(handle("run"));
        System.out.println(handle("status"));
        System.out.println(handle("upgrade"));
    }
}
```

**How to run:** `java CommandDispatcherExpression.java`

The modern switch **expression** (arrow syntax) directly produces a value for each case — no `break` statements, no fall-through risk, and multiple labels can share an arm with a single comma-separated list (`case "start", "run" ->`). A `{ }` block arm uses `yield` to produce its value, while a single-expression arm (like `"Starting..."`) implicitly yields that expression's result.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `handle("run")` is called first: inside, the switch expression evaluates `command` (`"run"`) against each arm's labels in order. `case "start", "run" ->` matches (since `"run"` is one of its two listed labels), so the expression immediately evaluates to `"Starting..."` — no other arms are checked, and there's no `break` to forget, since arrow-arms never fall through. This value is returned from `handle` and printed.

`handle("status")` is called next: `"status"` doesn't match `"start"`/`"run"` or `"stop"`/`"halt"`, but it does match `case "status" ->`, whose arm is a `{ }` block rather than a single expression. Inside the block, `status` is assigned `"All systems normal"`, and `yield status;` explicitly produces that value as the switch expression's result — this block form is needed whenever an arm requires more than one statement to compute its result.

`handle("upgrade")` is called last: `"upgrade"` matches none of the specific case labels, so the `default ->` arm runs, producing `"Unknown command: upgrade"`.

Expected output:
```
Starting...
All systems normal
Unknown command: upgrade
```

## 7. Gotchas & takeaways

> Switching on a **`null`** `String` throws `NullPointerException` immediately, before any `case` label is even checked — this is true for both the classic `switch` statement and the modern switch expression. If the value being switched on might be `null`, check for it explicitly beforehand (or, in a switch expression, use a `case null ->` arm, supported since Java 21) rather than letting the switch itself throw.

- `String` matching in a classic `switch` uses `.equals()` semantics under the hood (via `hashCode()` plus a confirming `equals()` check), not `==` — content equality, exactly as expected.
- Stacking case labels with no code between them (`case "a": case "b":`) lets multiple values share one branch in the classic `switch` statement — this is fall-through being used deliberately, not a mistake.
- The modern switch **expression** (`->` arrows) returns a value directly, supports comma-separated multiple labels per arm, and has no fall-through at all — each arm is self-contained.
- A block arm (`{ }`) in a switch expression must use `yield` to produce its result; a single-expression arm implicitly yields that expression's value.
- Prefer the switch expression form for new code when you need a resulting value — it eliminates the classic `switch` statement's most common bug, an accidentally-missing `break` causing unintended fall-through.
