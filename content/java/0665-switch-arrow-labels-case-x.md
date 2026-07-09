---
card: java
gi: 665
slug: switch-arrow-labels-case-x
title: Switch arrow labels (case x ->)
---

## 1. What it is

The **arrow label** syntax (`case x ->`), standardized in **Java 14** alongside switch expressions, is actually usable in **two** places: inside switch *expressions* (covered in [Switch expressions — standardized](0664-switch-expressions-standardized.md)) and, less obviously, inside plain switch **statements** too. A `switch` statement written entirely with arrow labels — `switch (x) { case A -> doA(); case B -> doB(); }` — runs a statement per matching case with **no fall-through**, even though the overall `switch` is still a statement (produces no value, no `yield` needed) rather than an expression. This is a distinct, narrower feature from switch expressions themselves: it's specifically the arrow-label *syntax* being usable as a non-fall-through alternative to colon labels, independent of whether the switch as a whole computes a value.

## 2. Why & when

Fall-through is the single most notorious footgun of the classic `switch` statement — forgetting a `break` silently lets execution continue into the next case's code. Arrow-labeled switch *statements* let you keep writing switch statements (multiple statements per case, no value produced, used purely for control flow) while getting the same "no accidental fall-through" safety that switch expressions provide. This is useful when you want each case to run some side-effecting code (logging, mutating external state, calling a void method) but have no interest in switch-as-expression's "produce a value" behavior — you get the safety without needing to restructure your code around a return value. Reach for `case X -> { ... }` as a statement whenever you're writing what would traditionally be a `switch` statement and want each case body's execution to be self-contained, without a stray missing `break` letting one case bleed into the next.

## 3. Core concept

```java
// Arrow-labeled SWITCH STATEMENT: runs code, produces no value, no fall-through.
switch (event) {
    case CLICK -> System.out.println("Handling click");
    case HOVER -> System.out.println("Handling hover");
    case KEY_PRESS -> {
        System.out.println("Handling key press");
        logKeyEvent(); // multiple statements are fine in a { } arm
    }
    default -> System.out.println("Unknown event");
}

// Compare: colon-labeled statement — needs explicit break to avoid fall-through
switch (event) {
    case CLICK:
        System.out.println("Handling click");
        break; // easy to forget!
    default:
        System.out.println("Unknown event");
}
```

Note there's no `yield` anywhere in the arrow-labeled statement above — `yield` is only relevant when the enclosing `switch` is being used as an **expression**; a switch statement's arrow arms simply execute their statements and then the whole `switch` statement ends, whether the arm was a single statement or a `{ }` block of several.

## 4. Diagram

<svg viewBox="0 0 620 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Colon labels in a switch statement fall through without break; arrow labels in a switch statement never fall through, with or without producing a value">
  <rect x="10" y="15" width="290" height="140" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="35" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Colon labels (statement)</text>
  <text x="25" y="60" fill="#e6edf3" font-size="10" font-family="monospace">case CLICK:</text>
  <text x="25" y="75" fill="#f85149" font-size="10" font-family="monospace">  print("click"); // no break!</text>
  <text x="25" y="90" fill="#e6edf3" font-size="10" font-family="monospace">case HOVER:</text>
  <text x="25" y="105" fill="#e6edf3" font-size="10" font-family="monospace">  print("hover"); break;</text>
  <text x="25" y="135" fill="#f85149" font-size="9" font-family="sans-serif">CLICK falls into HOVER's body.</text>

  <rect x="320" y="15" width="290" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="35" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Arrow labels (statement)</text>
  <text x="335" y="60" fill="#e6edf3" font-size="10" font-family="monospace">case CLICK -> print("click");</text>
  <text x="335" y="75" fill="#e6edf3" font-size="10" font-family="monospace">case HOVER -> print("hover");</text>
  <text x="335" y="105" fill="#6db33f" font-size="9" font-family="sans-serif">Still a statement (no value),</text>
  <text x="335" y="120" fill="#6db33f" font-size="9" font-family="sans-serif">but no fall-through either way —</text>
  <text x="335" y="135" fill="#6db33f" font-size="9" font-family="sans-serif">no break needed or possible here.</text>
</svg>

Arrow labels eliminate fall-through in both switch statements and switch expressions — the choice of `->` vs `:` controls fall-through independently of whether the switch produces a value.

## 5. Runnable example

Scenario: handling a set of UI event types by performing different side-effecting actions per event — first the classic colon-label statement showing a realistic fall-through bug, then the fix using arrow labels as a pure statement, then combining multiple case labels per arrow arm to handle related events together.

### Level 1 — Basic

```java
// File: EventHandlerBuggy.java
public class EventHandlerBuggy {
    enum Event { CLICK, HOVER, KEY_PRESS, UNKNOWN }

    static void handle(Event e) {
        switch (e) {
            case CLICK:
                System.out.println("Handling click");
                // missing break! falls through into HOVER's body
            case HOVER:
                System.out.println("Handling hover");
                break;
            case KEY_PRESS:
                System.out.println("Handling key press");
                break;
            default:
                System.out.println("Unknown event");
        }
    }

    public static void main(String[] args) {
        handle(Event.CLICK);
    }
}
```

**How to run:** `java EventHandlerBuggy.java`

Expected (buggy) output:
```
Handling click
Handling hover
```

`CLICK` incorrectly prints both messages because the missing `break` after `case CLICK:` lets execution fall through into `case HOVER:`'s body — exactly the classic fall-through bug.

### Level 2 — Intermediate

```java
// File: EventHandlerFixed.java
public class EventHandlerFixed {
    enum Event { CLICK, HOVER, KEY_PRESS, UNKNOWN }

    static void handle(Event e) {
        switch (e) {
            case CLICK -> System.out.println("Handling click");
            case HOVER -> System.out.println("Handling hover");
            case KEY_PRESS -> System.out.println("Handling key press");
            default -> System.out.println("Unknown event");
        }
    }

    public static void main(String[] args) {
        for (Event e : Event.values()) {
            handle(e);
        }
    }
}
```

**How to run:** `java EventHandlerFixed.java`

Expected output:
```
Handling click
Handling hover
Handling key press
Unknown event
```

Each event now prints exactly one message — the arrow-labeled statement structurally cannot fall through, so there's no `break` to forget and no bug to introduce.

### Level 3 — Advanced

```java
// File: EventHandlerGrouped.java
public class EventHandlerGrouped {
    enum Event { CLICK, DOUBLE_CLICK, HOVER, MOUSE_ENTER, MOUSE_LEAVE, KEY_PRESS }

    static int clickCount = 0;
    static int pointerEventCount = 0;

    static void handle(Event e) {
        switch (e) {
            case CLICK, DOUBLE_CLICK -> {
                clickCount++;
                pointerEventCount++;
                System.out.println("Click-family event: " + e + " (total clicks: " + clickCount + ")");
            }
            case HOVER, MOUSE_ENTER, MOUSE_LEAVE -> {
                pointerEventCount++;
                System.out.println("Pointer-movement event: " + e);
            }
            case KEY_PRESS -> System.out.println("Keyboard event: " + e);
        }
    }

    public static void main(String[] args) {
        Event[] sequence = {
            Event.MOUSE_ENTER, Event.HOVER, Event.CLICK,
            Event.DOUBLE_CLICK, Event.MOUSE_LEAVE, Event.KEY_PRESS
        };
        for (Event e : sequence) {
            handle(e);
        }
        System.out.println("Total pointer events: " + pointerEventCount);
    }
}
```

**How to run:** `java EventHandlerGrouped.java`

Expected output:
```
Pointer-movement event: MOUSE_ENTER
Pointer-movement event: HOVER
Click-family event: CLICK (total clicks: 1)
Click-family event: DOUBLE_CLICK (total clicks: 2)
Pointer-movement event: MOUSE_LEAVE
Keyboard event: KEY_PRESS
Total pointer events: 5
```

Level 3 groups multiple related `Event` constants under single arrow arms (`case CLICK, DOUBLE_CLICK ->` and `case HOVER, MOUSE_ENTER, MOUSE_LEAVE ->`), each running a multi-statement `{ }` block that mutates shared counters — this switch is still a **statement** (nothing is `yield`ed or returned from it), just one built entirely from arrow labels for safety and conciseness.

## 6. Walkthrough

1. `main` iterates `sequence` in order, starting with `Event.MOUSE_ENTER`. `handle(MOUSE_ENTER)` is called, entering `switch (e)`.
2. `MOUSE_ENTER` is checked against each arrow arm's label list in order: it doesn't match `CLICK, DOUBLE_CLICK`, but it does match `HOVER, MOUSE_ENTER, MOUSE_LEAVE` — so control jumps directly into that arm's `{ }` block.
3. Inside, `pointerEventCount++` increments the shared counter from `0` to `1`, and `System.out.println` prints `"Pointer-movement event: MOUSE_ENTER"`. The block ends, and since this is a switch **statement** (no `yield`, nothing being assigned), execution simply falls out of the entire `switch` construct and returns to `main`'s loop — there's no fall-through into the next case's label group, because arrow labels never fall through regardless of statement-vs-expression context.
4. The loop continues with `Event.HOVER`, matching the same arm again; `pointerEventCount` increments to `2`.
5. Next, `Event.CLICK` matches the first arm (`CLICK, DOUBLE_CLICK`): `clickCount` becomes `1`, `pointerEventCount` becomes `3`, and `"Click-family event: CLICK (total clicks: 1)"` prints.
6. `Event.DOUBLE_CLICK` matches the same arm again: `clickCount` becomes `2`, `pointerEventCount` becomes `4`.
7. `Event.MOUSE_LEAVE` matches the pointer-movement arm: `pointerEventCount` becomes `5`.
8. `Event.KEY_PRESS` matches its own single-label arm, a one-line arrow arm with no block braces needed since it's just one statement, printing `"Keyboard event: KEY_PRESS"`.
9. After the loop finishes all six events, `main` prints the final `pointerEventCount`, which accumulated across every `HOVER`/`MOUSE_ENTER`/`MOUSE_LEAVE`/`CLICK`/`DOUBLE_CLICK` event (5 of the 6 total events counted as "pointer" events, since `KEY_PRESS` doesn't touch that counter) — `"Total pointer events: 5"`.

```
sequence: MOUSE_ENTER, HOVER, CLICK, DOUBLE_CLICK, MOUSE_LEAVE, KEY_PRESS
             │            │      │         │            │           │
             ▼            ▼      ▼         ▼            ▼           ▼
        pointer arm   pointer  click arm  click arm  pointer arm  keyboard arm
        (no fall-through anywhere — each event handled by exactly one arm)
```

## 7. Gotchas & takeaways

> Arrow-labeled switch **statements** never use `yield` — `yield` only applies when the whole `switch` construct is being used as an **expression** whose value is consumed (assigned, returned, passed as an argument). Writing `yield` inside an arrow-labeled statement's block is a compile error, since there's no expression context expecting a produced value. Don't conflate "uses arrow labels" with "is a switch expression" — they're independent choices.

- Arrow labels (`case X ->`) are usable in both switch statements and switch expressions; both get the "no fall-through" behavior, but only the expression form requires (or allows) `yield`.
- A single-statement arrow arm needs no braces (`case X -> doSomething();`); a multi-statement arm needs `{ }` (`case X -> { stmt1; stmt2; }`).
- Multiple case labels can share one arrow arm (`case A, B, C ->`), replacing the old pattern of stacking colon-labels to intentionally fall through into shared code.
- You cannot mix colon labels and arrow labels within the same `switch` block — pick one style per switch construct.
- Preferring arrow-labeled statements over colon-labeled ones, even when you don't need a value, is a reasonable default from Java 14 onward purely for the fall-through safety it provides.
