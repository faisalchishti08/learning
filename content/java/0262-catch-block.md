---
card: java
gi: 262
slug: catch-block
title: catch block
---

## 1. What it is

A `catch` block follows a `try` block and specifies the exception type it is prepared to handle, along with a variable name bound to the actual thrown exception object. When an exception is thrown inside the `try` block, Java checks each `catch` clause in order (top to bottom) and runs the body of the *first* one whose declared type matches (via "is-a" polymorphism) the thrown exception's actual type — once one matches and runs, no other `catch` clause for that same `try` is even considered.

```java
public class CatchBlockDemo {
    public static void main(String[] args) {
        try {
            String s = null;
            System.out.println(s.length()); // throws NullPointerException
        } catch (NullPointerException e) { // matches: NullPointerException IS-A NullPointerException
            System.out.println("Caught NPE: " + e.getMessage());
        } catch (Exception e) { // would ALSO match, but never runs -- the first match above already handled it
            System.out.println("This line never runs for this particular exception");
        }
    }
}
```

`s.length()` throws `NullPointerException`, and Java checks the `catch` clauses top to bottom: the first one, `catch (NullPointerException e)`, matches exactly, so its body runs and the exception is considered fully handled — the second `catch (Exception e)` clause, even though it *would* also match a `NullPointerException` (since it's a subtype of `Exception`), is never reached, because only one `catch` clause per `try` ever executes for a given thrown exception.

## 2. Why & when

The `catch` block exists to let you respond to a specific failure with recovery logic, and Java's "first match wins, then stop" behaviour is what makes ordering multiple `catch` clauses meaningful.

- **Binding the exception object for inspection** — the variable declared in a `catch` clause (like `e` above) gives you access to the actual thrown exception instance: its message (`getMessage()`), its type (`getClass()`), its stack trace (`printStackTrace()`), and, for custom exceptions, any additional fields it carries.
- **Multiple `catch` clauses for differentiated handling** — a single `try` block can be followed by several `catch` clauses, each handling a different exception type differently, letting you tailor the response precisely to what actually went wrong (as the previous `Throwable` hierarchy topic explored with layered catches).
- **Order matters, and the compiler enforces sensible ordering** — since only the first matching clause runs, placing a broader type (like `Exception`) before a narrower one it would also match (like `NullPointerException`) makes the narrower clause unreachable, and Java's compiler actively rejects this as an error, rather than silently letting you write dead code.

Write a `catch` block for every exception type you have a genuine, distinct recovery strategy for; order multiple `catch` clauses from most specific to least specific, and use the caught exception object's message, type, and any custom fields to build a response tailored to exactly what failed, rather than generic, one-size-fits-all handling.

## 3. Core concept

```java
public class CatchBlockCore {
    public static void main(String[] args) {
        int[] numbers = {1, 2, 3};

        try {
            System.out.println(numbers[10]);
        } catch (ArrayIndexOutOfBoundsException e) {
            System.out.println("Index error — message: " + e.getMessage());
            System.out.println("Exception type: " + e.getClass().getSimpleName());
        }
    }
}
```

The caught exception variable `e` provides `getMessage()` (a description of what went wrong, here something like `"Index 10 out of bounds for length 3"`) and `getClass().getSimpleName()` (confirming the exact runtime type, `"ArrayIndexOutOfBoundsException"`) — both are commonly used together to build informative log messages or user-facing error reports.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java checks catch clauses top to bottom and runs only the first one whose type matches the thrown exception, then skips every remaining catch clause for that same try block">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="200" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="140" y="40" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">exception thrown</text>

  <line x1="140" y1="50" x2="140" y2="70" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="75" width="200" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="140" y="95" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">catch (Specific e) — MATCH, runs</text>

  <line x1="140" y1="105" x2="140" y2="125" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="220" y="120" fill="#8b949e" font-size="8" font-family="sans-serif">never reached</text>

  <rect x="40" y="130" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="3"/>
  <text x="140" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">catch (Broader e) — skipped</text>

  <text x="450" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Only ONE catch clause</text>
  <text x="450" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runs per thrown exception —</text>
  <text x="450" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the first one that matches.</text>
</svg>

Java runs exactly one matching `catch` clause per thrown exception — the first one in source order that matches.

## 5. Runnable example

Scenario: a data-validation routine handling several distinct failure types, evolved from a single catch clause into multiple differentiated ones, then hardened with multi-catch syntax combining related types into one clause.

### Level 1 — Basic

```java
public class CatchBlockBasic {
    public static void main(String[] args) {
        try {
            int result = Integer.parseInt("not-a-number");
            System.out.println("Result: " + result);
        } catch (NumberFormatException e) {
            System.out.println("Number format problem: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CatchBlockBasic.java`

A single `catch` clause handles the one specific exception type that can actually be thrown here, printing a targeted message using the caught exception's `getMessage()`.

### Level 2 — Intermediate

Same idea, now with two distinct operations inside separate `try` blocks, each with its own tailored `catch` clause — demonstrating differentiated handling for genuinely different failure types.

```java
public class CatchBlockIntermediate {
    public static void main(String[] args) {
        String[] values = { "42", "abc" };
        int[] numbers = {10, 20, 30};

        for (String v : values) {
            try {
                System.out.println("Parsed: " + Integer.parseInt(v));
            } catch (NumberFormatException e) {
                System.out.println("Cannot parse '" + v + "': " + e.getMessage());
            }
        }

        int[] indexesToTry = {0, 1, 99};
        for (int idx : indexesToTry) {
            try {
                System.out.println("Value at " + idx + ": " + numbers[idx]);
            } catch (ArrayIndexOutOfBoundsException e) {
                System.out.println("Bad index " + idx + ": " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java CatchBlockIntermediate.java`

Each loop has its own `try`/`catch` pair tailored to the specific exception type that operation can throw — `NumberFormatException` for parsing, `ArrayIndexOutOfBoundsException` for array access — keeping each catch's handling logic focused and specific to its own failure mode.

### Level 3 — Advanced

Same validation system, now combining two related exception types into a single multi-catch clause (using `|`) where the handling logic is genuinely identical for both, alongside a separate, differently-handled clause for a third type — demonstrating when combining catches is appropriate and when it is not.

```java
public class CatchBlockAdvanced {
    static int parseAndLookup(String input, int[] data) {
        int index = Integer.parseInt(input); // can throw NumberFormatException
        return data[index];                    // can throw ArrayIndexOutOfBoundsException
    }

    public static void main(String[] args) {
        int[] data = {100, 200, 300};
        String[] attempts = { "1", "abc", "99", "-1" };

        for (String attempt : attempts) {
            try {
                System.out.println("Result: " + parseAndLookup(attempt, data));
            } catch (NumberFormatException | ArrayIndexOutOfBoundsException e) {
                // Multi-catch: both cases are handled IDENTICALLY here (log and skip),
                // so combining them avoids duplicating the same handling logic twice.
                System.out.println("Input '" + attempt + "' rejected (" + e.getClass().getSimpleName() + "): " + e.getMessage());
            } catch (Exception e) {
                // A genuinely different, broader fallback for anything else unexpected
                System.out.println("Unexpected failure for '" + attempt + "': " + e);
            }
        }
    }
}
```

**How to run:** `java CatchBlockAdvanced.java`

The multi-catch clause `catch (NumberFormatException | ArrayIndexOutOfBoundsException e)` handles both exception types with one shared block of code, since the recovery action (log and move on) is identical for both — this avoids writing the same handling logic twice; note that in a multi-catch clause, `e`'s declared type is effectively the common supertype of the listed exceptions, so only methods available on all of them (like `getMessage()`, inherited from `Throwable`) can be called on it directly.

## 6. Walkthrough

Trace the loop in `CatchBlockAdvanced.main` over all four attempts.

**`attempt = "1"`.** `parseAndLookup("1", data)`: `Integer.parseInt("1")` succeeds, returning `1`. `data[1]` is `200` (valid index). Returns `200` with no exception. Prints `"Result: 200"`.

**`attempt = "abc"`.** `parseAndLookup("abc", data)`: `Integer.parseInt("abc")` throws `NumberFormatException` immediately — `data[index]` is never reached. The multi-catch clause matches (`NumberFormatException` is one of the listed types). Prints `"Input 'abc' rejected (NumberFormatException): For input string: \"abc\""`.

**`attempt = "99"`.** `parseAndLookup("99", data)`: `Integer.parseInt("99")` succeeds, returning `99`. `data[99]` throws `ArrayIndexOutOfBoundsException`, since `data` only has indices `0` through `2`. The multi-catch clause matches (`ArrayIndexOutOfBoundsException` is the other listed type). Prints `"Input '99' rejected (ArrayIndexOutOfBoundsException): Index 99 out of bounds for length 3"`.

**`attempt = "-1"`.** `parseAndLookup("-1", data)`: `Integer.parseInt("-1")` succeeds, returning `-1`. `data[-1]` also throws `ArrayIndexOutOfBoundsException` (negative indices are out of bounds too). The multi-catch clause matches again. Prints `"Input '-1' rejected (ArrayIndexOutOfBoundsException): Index -1 out of bounds for length 3"`.

```
"1"  -> parseInt(1) ok, data[1]=200  -> "Result: 200"
"abc"-> parseInt throws NumberFormatException      -> multi-catch -> "Input 'abc' rejected (NumberFormatException): ..."
"99" -> parseInt(99) ok, data[99] throws AIOOBE     -> multi-catch -> "Input '99' rejected (ArrayIndexOutOfBoundsException): ..."
"-1" -> parseInt(-1) ok, data[-1] throws AIOOBE     -> multi-catch -> "Input '-1' rejected (ArrayIndexOutOfBoundsException): ..."
```

**Final output.**
```
Result: 200
Input 'abc' rejected (NumberFormatException): For input string: "abc"
Input '99' rejected (ArrayIndexOutOfBoundsException): Index 99 out of bounds for length 3
Input '-1' rejected (ArrayIndexOutOfBoundsException): Index -1 out of bounds for length 3
```
The third, broader `catch (Exception e)` clause never runs at all in this program, since every thrown exception was successfully matched by the multi-catch clause above it — a concrete demonstration that only the first matching `catch` clause ever executes.

## 7. Gotchas & takeaways

> **Inside a multi-catch clause (`catch (TypeA | TypeB e)`), the variable `e`'s effective type is the closest common supertype of the listed types, so you can only call methods available on all of them** — typically this means only `Throwable`'s own methods (`getMessage()`, `getClass()`, `printStackTrace()`) are directly usable, unless the listed types share a more specific common supertype with additional methods; if you need type-specific behaviour, use separate `catch` clauses instead of combining them.

> **Only combine exception types in a multi-catch clause when the recovery logic is genuinely identical for both** — if handling `NumberFormatException` and `ArrayIndexOutOfBoundsException` actually required different responses (say, one triggers a retry and the other doesn't), combining them into one multi-catch block would force you to write awkward `instanceof` checks inside the shared block just to differentiate, which defeats the purpose; separate `catch` clauses would be clearer in that case.

- A `catch` block runs only if its declared exception type matches the thrown exception (via "is-a" polymorphism), and only the first matching clause (checked top to bottom) ever executes for a given thrown exception.
- The variable bound in a `catch` clause gives access to the actual exception object: its message, its runtime type, its stack trace, and any custom fields.
- Order multiple `catch` clauses from most specific to least specific; the compiler rejects an unreachable, overly broad clause placed too early.
- Multi-catch syntax (`catch (TypeA | TypeB e)`) combines identical handling logic for multiple exception types into one clause, but restricts `e` to methods common to all the listed types.
