---
card: java
gi: 414
slug: scanner-class
title: Scanner class
---

## 1. What it is

`Scanner`, added in Java 5 (`java.util`), is a text-parsing utility that reads tokens (whitespace-separated words, numbers, lines) from an input source — `System.in`, a `String`, a file, or any `Readable`/`InputStream` — and converts them to typed values. Its core methods come in pairs: `hasNextX()` to check whether the next token can be parsed as type `X` without consuming it, and `nextX()` to actually consume and return it — `hasNextInt()`/`nextInt()`, `hasNextLine()`/`nextLine()`, `hasNext()`/`next()`, and so on.

## 2. Why & when

Before `Scanner`, reading and parsing typed input from the console or a file meant manually reading raw text with a `BufferedReader` and hand-parsing it — splitting on whitespace yourself, calling `Integer.parseInt()` and catching `NumberFormatException` for validation, and generally writing a fair amount of boilerplate for what should be a simple task. `Scanner` bundles tokenizing and type-conversion into one object with a clean, chainable-feeling API: ask "is the next token an int?" then "give me the next int."

You reach for `Scanner` for command-line programs that read user input, quick parsing of structured text (a line of space-separated numbers, simple config-like text), and educational/prototype code where simplicity matters more than raw parsing performance. For high-volume or performance-critical parsing (parsing gigabytes of log files, for example), a `BufferedReader` with manual splitting is typically faster, since `Scanner` has more overhead per token.

## 3. Core concept

```java
import java.util.Scanner;

Scanner scanner = new Scanner(System.in); // or new Scanner("some string"), or new Scanner(new File(...))

System.out.print("Enter your age: ");
if (scanner.hasNextInt()) {         // check WITHOUT consuming
    int age = scanner.nextInt();    // consume and parse as an int
    System.out.println("You are " + age);
} else {
    System.out.println("That wasn't a valid number: " + scanner.next()); // consume whatever it was
}
```

The `hasNextX()` / `nextX()` pairing is the whole safety mechanism: calling `nextInt()` directly on non-numeric input throws `InputMismatchException` — checking with `hasNextInt()` first lets you handle bad input gracefully instead of crashing.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scanner splits input into tokens by whitespace; hasNextInt checks the next token's type without consuming it, nextInt consumes and parses it">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">Input: "25 apples 3.5"</text>

  <rect x="30" y="40" width="70" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="65" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">"25"</text>
  <rect x="110" y="40" width="100" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="160" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">"apples"</text>
  <rect x="220" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="260" y="60" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">"3.5"</text>

  <text x="20" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">hasNextInt() on "25" -&gt; true;  nextInt() -&gt; 25 (int), cursor advances past it</text>
  <text x="20" y="125" fill="#8b949e" font-size="10" font-family="sans-serif">hasNextInt() on "apples" -&gt; false;  nextInt() here would throw InputMismatchException</text>
</svg>

Each token is checked and consumed one at a time; the cursor only moves forward when a `nextX()` call succeeds.

## 5. Runnable example

Scenario: reading a simple shopping-list command from user input (item name and quantity) — the same parsing task, evolved from a version that crashes on bad input, through a validating loop that handles malformed entries, to a version parsing a whole multi-line list with a running total.

### Level 1 — Basic

```java
import java.util.Scanner;

public class ShoppingInputCrashes {
    public static void main(String[] args) {
        Scanner scanner = new Scanner("apples 3"); // simulate input as a String instead of System.in

        String item = scanner.next();
        int quantity = scanner.nextInt(); // would throw InputMismatchException if this weren't actually a number

        System.out.println("Item: " + item + ", quantity: " + quantity);
    }
}
```

**How to run:** `java ShoppingInputCrashes.java`

`nextInt()` works here because the second token really is a number, but calling it blindly on untrusted input (e.g. real `System.in` from a user) with no type-check first is fragile — a user typing `"apples three"` would crash the program with an uncaught `InputMismatchException`.

### Level 2 — Intermediate

```java
import java.util.Scanner;

public class ShoppingInputValidated {
    public static void main(String[] args) {
        Scanner scanner = new Scanner("apples three"); // simulate BAD input: "three" isn't a number

        String item = scanner.next();

        if (scanner.hasNextInt()) {
            int quantity = scanner.nextInt();
            System.out.println("Item: " + item + ", quantity: " + quantity);
        } else {
            String badToken = scanner.next(); // consume it so we can report what was actually there
            System.out.println("Invalid quantity for '" + item + "': \"" + badToken + "\" is not a number");
        }
    }
}
```

**How to run:** `java ShoppingInputValidated.java`

`hasNextInt()` checks the type of the next token *before* consuming it, so bad input (`"three"` instead of a number) is detected and handled gracefully — printing a helpful error message — instead of crashing with an uncaught exception.

### Level 3 — Advanced

```java
import java.util.Scanner;

public class ShoppingListMultiLine {
    public static void main(String[] args) {
        String input = "apples 3\nbread 2\nmilk abc\neggs 12"; // "milk abc" is deliberately malformed
        Scanner scanner = new Scanner(input);

        int totalItems = 0;
        int lineNumber = 0;

        while (scanner.hasNextLine()) {
            lineNumber++;
            String line = scanner.nextLine();
            Scanner lineScanner = new Scanner(line); // a nested Scanner just to parse this one line's tokens

            if (!lineScanner.hasNext()) continue; // skip blank lines

            String item = lineScanner.next();
            if (lineScanner.hasNextInt()) {
                int quantity = lineScanner.nextInt();
                totalItems += quantity;
                System.out.println("Line " + lineNumber + ": " + item + " x" + quantity);
            } else {
                System.out.println("Line " + lineNumber + ": SKIPPED (bad quantity for '" + item + "')");
            }
            lineScanner.close();
        }

        System.out.println("Total items: " + totalItems);
        scanner.close();
    }
}
```

**How to run:** `java ShoppingListMultiLine.java`

`hasNextLine()`/`nextLine()` process the input one full line at a time, and a fresh nested `Scanner` per line handles that line's own tokens — malformed lines (like `"milk abc"`) are detected via `hasNextInt()` and skipped without stopping the whole parse, so one bad line doesn't derail the entire list.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `input` is a 4-line string; `scanner` wraps it. `totalItems` and `lineNumber` both start at 0.

**Line 1:** `scanner.hasNextLine()` is `true`. `lineNumber` becomes 1, `scanner.nextLine()` consumes and returns `"apples 3"`. A nested `lineScanner` wraps just this string. `lineScanner.hasNext()` is `true` (not blank), so `item = "apples"`. `lineScanner.hasNextInt()` checks the remaining token `"3"` — `true` — so `quantity = 3`, `totalItems` becomes `0 + 3 = 3`, and `"Line 1: apples x3"` is printed.

**Line 2:** similarly, `"bread 2"` is parsed: `item = "bread"`, `quantity = 2`, `totalItems` becomes `3 + 2 = 5`, printing `"Line 2: bread x2"`.

**Line 3:** `"milk abc"` is read. `item = "milk"`. `lineScanner.hasNextInt()` checks the remaining token `"abc"` — since `"abc"` cannot be parsed as an `int`, this is `false`. The `else` branch runs, printing `"Line 3: SKIPPED (bad quantity for 'milk')"` — critically, `totalItems` is **not** incremented, and the malformed token is never actually consumed via `nextInt()` (which would have thrown), so no exception occurs.

**Line 4:** `"eggs 12"` parses normally: `item = "eggs"`, `quantity = 12`, `totalItems` becomes `5 + 12 = 17`, printing `"Line 4: eggs x12"`.

After the 4th line, `scanner.hasNextLine()` returns `false` (no more input), the `while` loop ends, and the final total is printed.

Expected output:
```
Line 1: apples x3
Line 2: bread x2
Line 3: SKIPPED (bad quantity for 'milk')
Line 4: eggs x12
Total items: 17
```

## 7. Gotchas & takeaways

> Mixing `nextInt()` (or other `nextX()` token methods) with `nextLine()` is a classic `Scanner` trap: `nextInt()` consumes only the numeric token, **leaving the trailing newline character in the buffer** — a subsequent `nextLine()` call then immediately returns an empty string (just that leftover newline) instead of the next real line of input. Always call an extra `scanner.nextLine()` to consume the leftover newline after a `nextInt()`/`nextX()` call, if a `nextLine()` call follows it.

- `hasNextX()` checks the type of the next token without consuming it; `nextX()` consumes and parses it — always pair them when input isn't guaranteed to be well-formed.
- `Scanner` can wrap `System.in`, a `String`, a `File`, or any `Readable`, making it flexible for both interactive input and parsing arbitrary text.
- Calling `nextInt()` (or similar) on a token that doesn't match throws `InputMismatchException` — check with `hasNextInt()` first if the input source isn't trusted.
- `hasNextLine()`/`nextLine()` operate on whole lines, while `hasNext()`/`next()`/`hasNextInt()`/`nextInt()` operate on whitespace-delimited tokens — know which granularity you need.
- For very large inputs or performance-critical parsing, a `BufferedReader` with manual splitting is typically faster than `Scanner`, which carries more overhead per token.
