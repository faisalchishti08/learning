---
card: java
gi: 261
slug: try-block
title: try block
---

## 1. What it is

A `try` block wraps a section of code that might throw an exception, marking it as the region Java should monitor for failures. On its own, a `try` block must be paired with at least one `catch` block or a `finally` block (covered in the next two topics) — a bare `try` with neither is a compile error. The moment an exception is thrown anywhere inside the `try` block, execution immediately jumps out of it, skipping any remaining statements in the block, to look for a matching `catch`.

```java
public class TryBlockDemo {
    public static void main(String[] args) {
        try {
            System.out.println("Step 1");
            int result = 10 / 0; // throws ArithmeticException here
            System.out.println("Step 2 — never reached"); // skipped entirely
        } catch (ArithmeticException e) {
            System.out.println("Caught: " + e.getMessage());
        }
        System.out.println("Program continues after the try/catch");
    }
}
```

`"Step 2"` never prints, because the moment `10 / 0` throws `ArithmeticException`, control immediately leaves the `try` block — it does not finish executing the remaining statements first — and jumps straight to the matching `catch` block; execution then resumes normally after the whole `try`/`catch` construct.

## 2. Why & when

The `try` block exists to explicitly delineate exactly which code's exceptions you intend to catch, keeping the scope of exception handling precise and intentional.

- **Scoping exception handling precisely** — only exceptions thrown *within* the `try` block (including from methods it calls) are eligible to be caught by the attached `catch` blocks; code outside the `try` block is entirely unaffected by those `catch` clauses, keeping the boundaries of "what this handles" clear and explicit.
- **Immediate exit on the first exception** — as soon as any statement inside a `try` block throws, all subsequent statements in that block are skipped; this "abandon ship immediately" behaviour is important to understand, since code after a risky operation inside the same `try` block will simply never run if that operation fails.
- **Wrapping only the risky code, not everything** — a common good practice is keeping a `try` block as small and focused as possible, containing only the specific operations that can actually fail and that you intend to handle, rather than wrapping large, unrelated stretches of code "just in case."

Use a `try` block around any operation that can throw an exception you intend to catch and handle — keep it scoped tightly to the risky operation itself where practical, since wrapping too much code in one `try` block can make it unclear exactly which statement caused a given caught exception, and can accidentally swallow failures from unrelated code that happened to be nearby.

## 3. Core concept

```java
public class TryBlockCore {
    public static void main(String[] args) {
        int[] numbers = {1, 2, 3};

        try {
            System.out.println("Before risky access");
            System.out.println(numbers[5]); // throws ArrayIndexOutOfBoundsException
            System.out.println("After risky access — never printed");
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Index problem: " + e.getMessage());
        }
    }
}
```

The moment `numbers[5]` throws (since the array only has indices `0` through `2`), execution abandons the rest of the `try` block entirely — `"After risky access"` never prints — and control transfers directly to the matching `catch` block, which handles the failure and lets the program continue normally afterward.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Statements execute in order inside a try block until one throws, at that point all remaining statements in the try block are skipped and control jumps directly to a matching catch block">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="240" height="130" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="38" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">try {</text>
  <rect x="60" y="45" width="200" height="25" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="62" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Step 1 — runs fine</text>
  <rect x="60" y="75" width="200" height="25" rx="4" fill="#0d1117" stroke="#f85149" stroke-width="1.5"/>
  <text x="160" y="92" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">10 / 0 — throws here!</text>
  <rect x="60" y="105" width="200" height="25" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1" stroke-dasharray="3"/>
  <text x="160" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Step 2 — SKIPPED</text>
  <text x="160" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">}</text>

  <line x1="280" y1="90" x2="360" y2="90" stroke="#f85149" stroke-width="1.5"/>

  <rect x="360" y="65" width="200" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">catch block runs</text>

  <text x="300" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Once an exception is thrown, the rest of the try block is skipped entirely.</text>
</svg>

Execution jumps immediately out of the `try` block the instant a statement throws, skipping everything after it.

## 5. Runnable example

Scenario: a small parsing routine reading multiple values, evolved from a single risky operation into a tightly scoped `try` block that demonstrates exactly which statements run and which are skipped when a failure occurs partway through.

### Level 1 — Basic

```java
public class TryBlockBasic {
    public static void main(String[] args) {
        try {
            System.out.println("Parsing input...");
            int value = Integer.parseInt("not a number");
            System.out.println("Parsed value: " + value); // never reached
        } catch (NumberFormatException e) {
            System.out.println("Parsing failed: " + e.getMessage());
        }
        System.out.println("Done");
    }
}
```

**How to run:** `java TryBlockBasic.java`

`Integer.parseInt("not a number")` throws immediately, so `"Parsed value: ..."` never prints — execution jumps straight from the failing line to the `catch` block, then continues normally with `"Done"` after the whole construct.

### Level 2 — Intermediate

Same idea, now with multiple values parsed inside one `try` block, demonstrating that the *entire remaining block* is abandoned the moment any one of them fails — not just the failing statement itself.

```java
public class TryBlockIntermediate {
    public static void main(String[] args) {
        try {
            System.out.println("Parsing first value...");
            int first = Integer.parseInt("42");
            System.out.println("First: " + first);

            System.out.println("Parsing second value...");
            int second = Integer.parseInt("oops"); // fails here
            System.out.println("Second: " + second); // never reached

            System.out.println("Parsing third value...");        // ALSO never reached
            int third = Integer.parseInt("7");                     // never even attempted
            System.out.println("Third: " + third);                 // never reached
        } catch (NumberFormatException e) {
            System.out.println("Parsing stopped due to: " + e.getMessage());
        }
        System.out.println("Program continues after handling the failure");
    }
}
```

**How to run:** `java TryBlockIntermediate.java`

Once `Integer.parseInt("oops")` throws, everything after it in the `try` block — including the entirely unrelated third parsing attempt, which would have succeeded on its own — is skipped completely; this demonstrates why keeping a `try` block scoped to just the operations you genuinely want grouped together as "fail together" matters, since a later, perfectly valid operation never even gets a chance to run.

### Level 3 — Advanced

Same parsing scenario, now restructured with a tightly scoped `try` block per value inside a loop, demonstrating the more robust, production-flavoured pattern: each risky operation gets its own `try`, so one failure doesn't prevent unrelated, independent operations from being attempted.

```java
import java.util.List;

public class TryBlockAdvanced {
    public static void main(String[] args) {
        List<String> inputs = List.of("42", "oops", "7", "also-oops", "100");
        int successCount = 0;
        int failureCount = 0;

        for (String input : inputs) {
            try { // one small, focused try block PER iteration -- failures don't block later iterations
                int value = Integer.parseInt(input);
                System.out.println("Parsed: " + value);
                successCount++;
            } catch (NumberFormatException e) {
                System.out.println("Skipped invalid value '" + input + "': " + e.getMessage());
                failureCount++;
            }
        }

        System.out.println("Total parsed: " + successCount + ", Total skipped: " + failureCount);
    }
}
```

**How to run:** `java TryBlockAdvanced.java`

Because the `try` block is scoped to just one parsing attempt per loop iteration (rather than the whole loop), a failure on `"oops"` only skips the rest of *that one iteration's* `try` block — it does not prevent `"7"` and `"100"` from being successfully parsed in later iterations, which is exactly the kind of resilient, "keep processing what you can" behaviour a tightly scoped `try` block enables.

## 6. Walkthrough

Trace the loop in `TryBlockAdvanced.main` across all five inputs.

**`input = "42"`.** Inside the `try`, `Integer.parseInt("42")` succeeds, returning `42`. Prints `"Parsed: 42"`. `successCount` becomes `1`. No exception, so the `catch` block is skipped entirely for this iteration.

**`input = "oops"`.** Inside the `try`, `Integer.parseInt("oops")` throws `NumberFormatException` immediately — there is no more code after it in this iteration's `try` block anyway, so nothing is skipped that wouldn't have run regardless. Control jumps to the `catch` block: prints `"Skipped invalid value 'oops': For input string: \"oops\""`. `failureCount` becomes `1`.

**`input = "7"`.** A brand-new `try` block execution for this iteration (the loop returns to the top and re-enters `try` fresh). `Integer.parseInt("7")` succeeds, returning `7`. Prints `"Parsed: 7"`. `successCount` becomes `2`.

**`input = "also-oops"`.** `Integer.parseInt("also-oops")` throws. Caught: prints `"Skipped invalid value 'also-oops': For input string: \"also-oops\""`. `failureCount` becomes `2`.

**`input = "100"`.** `Integer.parseInt("100")` succeeds, returning `100`. Prints `"Parsed: 100"`. `successCount` becomes `3`.

**After the loop.** `successCount` is `3`, `failureCount` is `2`. Prints `"Total parsed: 3, Total skipped: 2"`.

```
"42"        -> parses fine -> "Parsed: 42"                      successCount=1
"oops"      -> throws      -> caught -> "Skipped invalid value 'oops': ..."   failureCount=1
"7"         -> parses fine -> "Parsed: 7"                       successCount=2
"also-oops" -> throws      -> caught -> "Skipped invalid value 'also-oops': ..." failureCount=2
"100"       -> parses fine -> "Parsed: 100"                     successCount=3
```

**Final output.**
```
Parsed: 42
Skipped invalid value 'oops': For input string: "oops"
Parsed: 7
Skipped invalid value 'also-oops': For input string: "also-oops"
Parsed: 100
Total parsed: 3, Total skipped: 2
```
Crucially, `"7"` and `"100"` were both successfully parsed *despite* two failures occurring earlier in the loop, because each iteration got its own fresh, independently-scoped `try` block — exactly the resilience the intermediate example's single, broad `try` block lacked.

## 7. Gotchas & takeaways

> **A `try` block abandons all remaining statements the instant any one of them throws — even statements that are completely unrelated to the one that failed and would have succeeded perfectly well on their own.** As `TryBlockIntermediate` demonstrated, a perfectly valid third parsing attempt never even ran, purely because it happened to be textually located after a failing one inside the same `try` block; this is a frequent source of "why didn't this run?" confusion.

> **Keeping `try` blocks small and focused on just the specific risky operation (or a tightly related group of operations that should genuinely succeed or fail together) is a widely recommended practice** — it makes it much easier to reason about exactly what a given `catch` block is actually responding to, and, as `TryBlockAdvanced` showed, allows independent operations (like separate loop iterations) to succeed even when others fail.

- A `try` block marks code Java should monitor for exceptions; it must be paired with at least one `catch` block or a `finally` block.
- The moment an exception is thrown anywhere inside a `try` block, all remaining statements in that block are skipped, and control jumps directly to a matching `catch` block.
- Keep `try` blocks scoped tightly to the specific operations that can fail and that should genuinely be handled together, rather than wrapping large, unrelated stretches of code.
- Structuring risky operations with individually scoped `try` blocks (for example, one per loop iteration) lets independent failures be handled without preventing unrelated, still-valid operations from succeeding.
