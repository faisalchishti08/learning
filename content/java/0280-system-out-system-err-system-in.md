---
card: java
gi: 280
slug: system-out-system-err-system-in
title: System.out / System.err / System.in
---

## 1. What it is

`System.out`, `System.err`, and `System.in` are three `public static final` fields on `java.lang.System`, representing the standard output, standard error, and standard input streams every running program has access to. `System.out` and `System.err` are both `PrintStream` objects (supporting `println`, `print`, `printf`); `System.in` is a raw `InputStream`, typically wrapped in something more convenient like a `Scanner` or `BufferedReader` for actually reading text from it.

```java
import java.util.Scanner;

public class StandardStreamsDemo {
    public static void main(String[] args) {
        System.out.println("This goes to standard output"); // normal program output
        System.err.println("This goes to standard error");     // errors/diagnostics, separate stream

        Scanner scanner = new Scanner(System.in); // wraps System.in for convenient reading
        System.out.println("Enter your name:");
        String name = scanner.nextLine();
        System.out.println("Hello, " + name + "!");
    }
}
```

`System.out.println` and `System.err.println` write to two genuinely separate streams — both typically appear together in a terminal, but they can be redirected independently (for example, sending normal output to a file while errors still appear on screen); `System.in`, wrapped in a `Scanner`, lets the program read a line of text the user types at the console.

## 2. Why & when

Understanding these three streams matters for controlling exactly where a program's output goes, reading interactive input, and correctly separating normal output from diagnostic or error information.

- **Separating normal output from error/diagnostic output** — `System.out` is meant for the program's actual intended output (results, data, expected messages); `System.err` is meant for error messages, warnings, and diagnostics — keeping these separate lets users and scripts redirect each independently (for instance, `java MyProgram > results.txt 2> errors.txt` captures each stream to its own file).
- **Reading interactive input from the console** — `System.in` is the raw stream of bytes typed at the console (or piped in from a file or another program); wrapping it in a `Scanner` (as shown) or a `BufferedReader` provides convenient methods for reading lines, numbers, or tokens without manually parsing raw bytes yourself.
- **Understanding why `printStackTrace()` uses `System.err`** — as an earlier topic noted, `Throwable.printStackTrace()` writes to `System.err` by default, precisely because a stack trace is diagnostic information about a failure, not part of the program's normal intended output — recognizing this distinction clarifies why redirecting `System.out` alone doesn't capture stack traces.

Use `System.out` for a program's normal, expected output; use `System.err` for error messages, warnings, and diagnostic information that should be conceptually and practically separable from normal output; use `System.in` (typically wrapped in `Scanner` or similar) whenever a program needs to read interactive input from the console.

## 3. Core concept

```java
public class StandardStreamsCore {
    static void processValue(int value) {
        if (value < 0) {
            System.err.println("Warning: negative value encountered: " + value); // diagnostic, goes to error stream
            return;
        }
        System.out.println("Processed: " + value); // normal output
    }

    public static void main(String[] args) {
        int[] values = { 5, -3, 10 };
        for (int v : values) processValue(v);
    }
}
```

Normal, successfully processed values print via `System.out`, while the warning about the invalid negative value prints via `System.err` — if this program's output were redirected with `java StandardStreamsCore > output.txt`, only the two `"Processed: ..."` lines would land in `output.txt`; the warning would still appear directly in the terminal (or wherever standard error is separately directed).

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System.out carries normal program output, System.err carries error and diagnostic output, System.in carries input typed at the console, all three are independent streams that can be redirected separately">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">System.out</text>

  <rect x="220" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="300" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">System.err</text>

  <rect x="400" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">System.in</text>

  <text x="120" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">normal output</text>
  <text x="300" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">errors/diagnostics</text>
  <text x="480" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">console input</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Three independent streams, each separately redirectable at the shell level.</text>
</svg>

`System.out`, `System.err`, and `System.in` are three independent streams for output, errors, and input.

## 5. Runnable example

Scenario: a small interactive calculator reading numbers from the console, evolved from basic output into distinguishing errors on `System.err`, then hardened with an input-validation loop reading repeatedly from `System.in` until valid data is entered.

### Level 1 — Basic

```java
public class StreamsBasic {
    public static void main(String[] args) {
        System.out.println("Result: " + (10 + 5));
    }
}
```

**How to run:** `java StreamsBasic.java`

A single `System.out.println` call prints normal program output — the simplest starting point before introducing errors or input.

### Level 2 — Intermediate

Same idea, now with a calculation that can fail, printing the error to `System.err` distinctly from normal results on `System.out`.

```java
public class StreamsIntermediate {
    static void divideAndReport(int a, int b) {
        if (b == 0) {
            System.err.println("Error: cannot divide " + a + " by zero");
            return;
        }
        System.out.println(a + " / " + b + " = " + (a / b));
    }

    public static void main(String[] args) {
        divideAndReport(10, 2);
        divideAndReport(10, 0);
        divideAndReport(20, 4);
    }
}
```

**How to run:** `java StreamsIntermediate.java`

Two successful calculations print to `System.out`, while the division-by-zero case prints its error message to `System.err` — running `java StreamsIntermediate 2>/dev/null` (redirecting standard error away) would show only the two successful results, demonstrating the streams' independence in practice.

### Level 3 — Advanced

Same calculator, now reading numbers interactively from `System.in` via a `Scanner`, validating input in a loop and reporting invalid entries to `System.err` while successful calculations go to `System.out`.

```java
import java.util.InputMismatchException;
import java.util.Scanner;

public class StreamsAdvanced {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int validCount = 0;

        System.out.println("Enter up to 3 integers (one per line):");
        while (validCount < 3 && scanner.hasNextLine()) {
            String line = scanner.nextLine();
            try {
                int value = Integer.parseInt(line.trim());
                System.out.println("Accepted: " + value);
                validCount++;
            } catch (NumberFormatException e) {
                System.err.println("Rejected invalid input: '" + line + "'");
            }
        }
        System.out.println("Finished after " + validCount + " valid entries");
    }
}
```

**How to run:** `printf "5\nabc\n10\n\n" | java StreamsAdvanced.java` (feeding input via a pipe, since this program reads from standard input)

Each line read from `System.in` (via the `Scanner` wrapping it) is either accepted (printed to `System.out` and counted) or rejected (printed to `System.err`) — piping input directly (rather than typing interactively) lets this be run and verified non-interactively, exactly the technique used for automated testing of console programs.

## 6. Walkthrough

Trace `main` in `StreamsAdvanced` when run with the piped input `"5\nabc\n10\n\n"` (four lines: `"5"`, `"abc"`, `"10"`, and an empty line).

**`System.out.println("Enter up to 3 integers...")`.** Prints the prompt immediately to standard output.

**Loop iteration 1.** `validCount` is `0`, `scanner.hasNextLine()` is `true`. `line = scanner.nextLine()` reads `"5"`. `Integer.parseInt("5".trim())` succeeds, returning `5`. Prints `"Accepted: 5"` (to `System.out`). `validCount` becomes `1`.

**Loop iteration 2.** `validCount` is `1` (`< 3`), `hasNextLine()` is `true`. `line = "abc"`. `Integer.parseInt("abc")` throws `NumberFormatException`. Caught: prints `"Rejected invalid input: 'abc'"` (to `System.err`). `validCount` remains `1`.

**Loop iteration 3.** `validCount` is `1`, `hasNextLine()` is `true`. `line = "10"`. `Integer.parseInt("10")` succeeds, returning `10`. Prints `"Accepted: 10"`. `validCount` becomes `2`.

**Loop iteration 4.** `validCount` is `2` (`< 3`), `hasNextLine()` is `true` (one more line remains, the empty one). `line = ""`. `Integer.parseInt("".trim())` throws `NumberFormatException` (an empty string is not a valid number). Caught: prints `"Rejected invalid input: ''"`. `validCount` remains `2`.

**Loop check.** `validCount` is `2` (`< 3`), but `scanner.hasNextLine()` is now `false` (no more input remains in the piped stream), so the `while` condition is `false` and the loop ends.

**Final print.** `"Finished after 2 valid entries"` (to `System.out`).

```
input piped: "5", "abc", "10", "" (4 lines)

iter1: "5"   -> parses -> Accepted: 5     (validCount=1)
iter2: "abc" -> NumberFormatException -> Rejected invalid input: 'abc'  (validCount stays 1)
iter3: "10"  -> parses -> Accepted: 10    (validCount=2)
iter4: ""    -> NumberFormatException (empty string) -> Rejected invalid input: ''  (validCount stays 2)
loop check: validCount=2 (<3) but hasNextLine() false -> loop ends
```

**Standard output (System.out) contents.**
```
Enter up to 3 integers (one per line):
Accepted: 5
Accepted: 10
Finished after 2 valid entries
```

**Standard error (System.err) contents.**
```
Rejected invalid input: 'abc'
Rejected invalid input: ''
```
In a typical terminal, both streams appear interleaved together in roughly this order, but they are genuinely separate streams — redirecting `System.out` to a file (`... > out.txt`) would capture only the first block, while the rejected-input warnings would still print directly to the terminal.

## 7. Gotchas & takeaways

> **Forgetting to close or properly manage a `Scanner` wrapping `System.in` is a minor but common oversight** — while `System.in` itself is typically left open for the program's entire lifetime (since it's a shared system resource, not something your program uniquely owns), closing a `Scanner` wrapping it can, on some systems, close the underlying stream too, which would break any subsequent attempt to read further input — generally, don't call `.close()` on a `Scanner` wrapping `System.in` unless you're certain no further input will ever be needed.

> **`System.out` and `System.err` are buffered somewhat differently, and their relative ordering in a terminal is not strictly guaranteed under all conditions** — although in most simple, single-threaded console programs they appear to interleave in the order the code executes, genuinely concurrent or heavily buffered scenarios can occasionally show output from the two streams in a different relative order than the source code's execution order might suggest; this is rarely an issue for simple programs but worth being aware of in more complex, concurrent logging scenarios.

- `System.out` and `System.err` are both `PrintStream` objects for normal output and error/diagnostic output respectively; `System.in` is a raw `InputStream` for reading console input, typically wrapped in a `Scanner` or `BufferedReader`.
- Keeping normal output and error output on separate streams allows each to be redirected independently at the shell level, a standard convention respected by command-line tools generally.
- `Throwable.printStackTrace()` writes to `System.err` by default, consistent with stack traces being diagnostic information, not normal program output.
- Piping input into a program's `System.in` (rather than typing interactively) is a standard technique for testing console-based programs non-interactively and reproducibly.
