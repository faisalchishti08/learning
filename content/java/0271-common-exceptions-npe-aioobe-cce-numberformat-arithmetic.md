---
card: java
gi: 271
slug: common-exceptions-npe-aioobe-cce-numberformat-arithmetic
title: Common exceptions (NPE, AIOOBE, CCE, NumberFormat, Arithmetic)
---

## 1. What it is

Five unchecked exceptions account for the overwhelming majority of everyday Java runtime failures: `NullPointerException` (calling a method or accessing a field on a `null` reference), `ArrayIndexOutOfBoundsException` (accessing an array with an invalid index), `ClassCastException` (an invalid cast between incompatible types), `NumberFormatException` (parsing text that isn't a valid number), and `ArithmeticException` (an invalid arithmetic operation, most commonly integer division by zero). Recognizing exactly what triggers each one is essential for both writing defensive code and quickly diagnosing failures.

```java
public class CommonExceptionsDemo {
    public static void main(String[] args) {
        String s = null;
        try { s.length(); } catch (NullPointerException e) { System.out.println("NPE: " + e.getMessage()); }

        int[] arr = {1, 2, 3};
        try { int x = arr[5]; } catch (ArrayIndexOutOfBoundsException e) { System.out.println("AIOOBE: " + e.getMessage()); }

        Object obj = "a string";
        try { Integer i = (Integer) obj; } catch (ClassCastException e) { System.out.println("CCE: " + e.getMessage()); }

        try { Integer.parseInt("abc"); } catch (NumberFormatException e) { System.out.println("NumberFormat: " + e.getMessage()); }

        try { int r = 10 / 0; } catch (ArithmeticException e) { System.out.println("Arithmetic: " + e.getMessage()); }
    }
}
```

Each block triggers exactly one of the five common exceptions, demonstrating the precise condition that causes it — a `null` method call, an out-of-range array index, an incompatible cast, unparseable text, and integer division by zero, respectively — recognizing these five patterns on sight is one of the fastest ways to diagnose the majority of runtime failures you'll encounter in everyday Java code.

## 2. Why & when

Knowing these five exceptions precisely — not just their names, but exactly what triggers each — is foundational to reading stack traces quickly and writing code that avoids them in the first place.

- **`NullPointerException` (NPE)** — thrown whenever code attempts to use a `null` reference as if it were a real object: calling a method on it, accessing a field, or indexing into it if it were an array. It is by far the single most common runtime exception in Java code, and modern Java (14+) includes "helpful NullPointerExceptions" that name the exact variable that was `null`, making diagnosis considerably easier than in older versions.
- **`ArrayIndexOutOfBoundsException` (AIOOBE)** — thrown when an array index is negative or greater than or equal to the array's length; a very common source is an off-by-one error in a loop condition (using `<=` instead of `<` against an array's length, for instance).
- **`ClassCastException` (CCE)** — thrown when code casts a reference to a type it is not actually compatible with at runtime; this typically surfaces when working with collections of a general type (like raw `Object`) that turn out to contain an unexpected concrete type.
- **`NumberFormatException`** — thrown by parsing methods like `Integer.parseInt` and `Double.parseDouble` when the given string isn't a validly formatted number for that type; a direct subclass of `IllegalArgumentException`, as an earlier topic noted.
- **`ArithmeticException`** — thrown for invalid arithmetic, most commonly integer division (or modulo) by zero; note that *floating-point* division by zero does **not** throw this exception — it instead produces `Infinity`, `-Infinity`, or `NaN`, a frequently surprising distinction covered in the gotchas.

Recognize each of these on sight in a stack trace to immediately narrow down the likely cause of a failure, and understand the specific conditions that trigger each one so you can write validation and defensive checks (`null` checks, bounds checks, `instanceof` checks before casting) that prevent them from occurring in the first place, rather than only reacting to them after the fact.

## 3. Core concept

```java
public class CommonExceptionsCore {
    static void demonstrateEach() {
        // NullPointerException
        String name = null;
        // name.length(); // would throw here

        // ArrayIndexOutOfBoundsException
        int[] scores = {90, 85};
        // scores[2]; // valid indices are only 0 and 1

        // ClassCastException
        Object value = "text";
        // Integer num = (Integer) value; // "text" is not actually an Integer

        // NumberFormatException
        // Integer.parseInt("12.5"); // not a valid integer format (decimal point)

        // ArithmeticException
        int a = 10, b = 0;
        // int result = a / b; // integer division by zero
    }
}
```

Each commented-out line represents a distinct, precise trigger condition — recognizing these patterns in your own code before they run is exactly the defensive mindset that prevents most of these exceptions from ever occurring at runtime in the first place.

## 4. Diagram

<svg viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Five common exceptions each triggered by a distinct condition, null method call, invalid array index, incompatible cast, unparseable number text, integer division by zero">
  <rect x="8" y="8" width="584" height="204" rx="8" fill="#0d1117"/>

  <rect x="20" y="20" width="270" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="155" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">NullPointerException — null.method()</text>

  <rect x="310" y="20" width="270" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">AIOOBE — index &lt; 0 or &gt;= length</text>

  <rect x="20" y="65" width="270" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="87" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ClassCastException — incompatible cast</text>

  <rect x="310" y="65" width="270" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="87" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">NumberFormatException — bad parse text</text>

  <rect x="165" y="110" width="270" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="300" y="132" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">ArithmeticException — int division by zero</text>

  <text x="300" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Recognizing each trigger condition instantly speeds up diagnosing real stack traces.</text>
</svg>

Five distinct trigger conditions account for the vast majority of everyday Java runtime exceptions.

## 5. Runnable example

Scenario: a data-processing routine handling a batch of raw records that can fail in every one of these five ways, evolved from handling one exception type into a comprehensive, correctly-ordered set of guards for all five.

### Level 1 — Basic

```java
public class CommonExceptionsBasic {
    public static void main(String[] args) {
        String input = null;
        try {
            System.out.println(input.length());
        } catch (NullPointerException e) {
            System.out.println("Input was null, cannot process");
        }
    }
}
```

**How to run:** `java CommonExceptionsBasic.java`

`input.length()` on a `null` reference throws `NullPointerException` immediately — the single most common exception in everyday Java code, caught here with a clear, targeted message.

### Level 2 — Intermediate

Same processing idea, now handling records that can fail in three different specific ways — a missing value, a bad index, and an unparseable number — each caught with its own tailored response.

```java
public class CommonExceptionsIntermediate {
    static int[] scores = { 90, 85, 78 };

    static void processRecord(String indexStr) {
        int index = Integer.parseInt(indexStr); // NumberFormatException possible
        int score = scores[index];                 // ArrayIndexOutOfBoundsException possible
        System.out.println("Score: " + score);
    }

    public static void main(String[] args) {
        String[] requests = { "1", "abc", "10" };
        for (String req : requests) {
            try {
                processRecord(req);
            } catch (NumberFormatException e) {
                System.out.println("'" + req + "' is not a valid index format");
            } catch (ArrayIndexOutOfBoundsException e) {
                System.out.println("'" + req + "' is out of range: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java CommonExceptionsIntermediate.java`

Two different exception types are handled, each corresponding precisely to a distinct failure mode inside `processRecord` — a parsing problem versus an out-of-range index — demonstrating that recognizing exactly *why* each exception is thrown lets you write a targeted response for each one.

### Level 3 — Advanced

Same batch processing, now covering all five common exceptions in one realistic scenario: records that might contain `null`, an out-of-range reference, an incompatible stored type, unparseable text, or trigger a division by zero during a calculation — each handled distinctly.

```java
import java.util.List;

public class CommonExceptionsAdvanced {
    static int[] inventory = { 100, 50, 0 }; // index 2 has zero stock, relevant for the division case

    static double processRecord(Object rawRecord) {
        String record = (String) rawRecord; // ClassCastException if rawRecord isn't actually a String
        if (record == null) throw new NullPointerException("record itself was null"); // explicit NPE check, for clarity
        String[] parts = record.split(":");
        int index = Integer.parseInt(parts[0]);     // NumberFormatException possible
        int requested = Integer.parseInt(parts[1]);  // NumberFormatException possible
        int available = inventory[index];              // ArrayIndexOutOfBoundsException possible
        return (double) requested / available;           // ArithmeticException NOT thrown for double division by zero!
    }

    public static void main(String[] args) {
        List<Object> records = List.of("0:20", "abc:5", "1:10", "10:5", 42);
        for (Object rec : records) {
            try {
                System.out.println("Fulfillment ratio: " + processRecord(rec));
            } catch (NullPointerException e) {
                System.out.println("Null record: " + e.getMessage());
            } catch (ClassCastException e) {
                System.out.println("Wrong record type: " + e.getMessage());
            } catch (NumberFormatException e) {
                System.out.println("Bad number format: " + e.getMessage());
            } catch (ArrayIndexOutOfBoundsException e) {
                System.out.println("Bad inventory index: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java CommonExceptionsAdvanced.java`

Four of the five common exceptions are actively demonstrated here (`ClassCastException` via the final `42` entry, `NumberFormatException` via `"abc:5"`, `ArrayIndexOutOfBoundsException` via `"10:5"`, and note that the division at the end uses `double` arithmetic, which — unlike `int` division — does *not* throw `ArithmeticException` for division by zero, a deliberately included gotcha explained fully in the walkthrough).

## 6. Walkthrough

Trace the loop in `CommonExceptionsAdvanced.main` over all five records.

**`rec = "0:20"`.** `processRecord("0:20")`: cast to `String` succeeds (it already is one). Not `null`. `split(":")` gives `["0", "20"]`. `index = Integer.parseInt("0") = 0`. `requested = Integer.parseInt("20") = 20`. `available = inventory[0] = 100`. Returns `(double) 20 / 100 = 0.2`. Prints `"Fulfillment ratio: 0.2"`.

**`rec = "abc:5"`.** `split(":")` gives `["abc", "5"]`. `Integer.parseInt("abc")` throws `NumberFormatException` immediately. Caught by the `NumberFormatException` clause. Prints `"Bad number format: For input string: \"abc\""`.

**`rec = "1:10"`.** `split(":")` gives `["1", "10"]`. `index = 1`, `requested = 10`. `available = inventory[1] = 50`. Returns `(double) 10 / 50 = 0.2`. Prints `"Fulfillment ratio: 0.2"`.

**`rec = "10:5"`.** `split(":")` gives `["10", "5"]`. `index = 10`, `requested = 5`. `inventory[10]` throws `ArrayIndexOutOfBoundsException`, since `inventory` only has indices `0` through `2`. Caught by that clause. Prints `"Bad inventory index: Index 10 out of bounds for length 3"`.

**`rec = 42` (an `Integer`, not a `String`).** `(String) rawRecord` attempts to cast the boxed `Integer` `42` to `String` — these are incompatible types, so `ClassCastException` is thrown immediately, before any of the rest of the method runs. Caught by the `ClassCastException` clause. Prints something like `"Wrong record type: class java.lang.Integer cannot be cast to class java.lang.String"`.

**Note on the third record's division.** If `index` had been `2` (pointing at `inventory[2] = 0`), `(double) requested / available` would compute `(double) requested / 0`, which — since this is `double` division, not `int` division — does **not** throw `ArithmeticException` at all; it produces `Infinity` (or `NaN` if `requested` were also `0`) as a normal, valid `double` value, silently, with no exception raised. This is a deliberately included, commonly surprising distinction: `ArithmeticException` for division by zero applies only to *integer* division, never floating-point division.

```
"0:20"  -> index=0, requested=20, available=100 -> 20/100=0.2   -> "Fulfillment ratio: 0.2"
"abc:5" -> parseInt("abc") throws NumberFormatException          -> "Bad number format: ..."
"1:10"  -> index=1, requested=10, available=50  -> 10/50=0.2    -> "Fulfillment ratio: 0.2"
"10:5"  -> inventory[10] throws ArrayIndexOutOfBoundsException   -> "Bad inventory index: ..."
42      -> (String) 42 throws ClassCastException                 -> "Wrong record type: ..."
```

**Final output.**
```
Fulfillment ratio: 0.2
Bad number format: For input string: "abc"
Fulfillment ratio: 0.2
Bad inventory index: Index 10 out of bounds for length 3
Wrong record type: class java.lang.Integer cannot be cast to class java.lang.String
```

## 7. Gotchas & takeaways

> **`ArithmeticException` for division by zero applies only to integer (and long) division, never floating-point (`double`/`float`) division** — `10 / 0` (both `int`) throws `ArithmeticException: / by zero`, but `10.0 / 0` (a `double` divided by an `int`, promoted to `double` division) evaluates to `Infinity`, a perfectly valid `double` value, with no exception thrown at all. Code that assumes all division-by-zero cases throw an exception can silently propagate `Infinity` or `NaN` through subsequent floating-point calculations undetected — always explicitly check for these special values (`Double.isInfinite()`, `Double.isNaN()`) when working with floating-point division that might involve a zero divisor.

> **Modern Java's "helpful NullPointerExceptions" (enabled by default since Java 15) name the exact variable or method call that was `null`**, turning a previously bare `"NullPointerException"` message into something like `"Cannot invoke \"String.length()\" because \"input\" is null"` — always check your JDK version and this message detail before assuming you need extra logging just to identify which variable was `null` in a given stack trace.

- `NullPointerException`, `ArrayIndexOutOfBoundsException`, `ClassCastException`, `NumberFormatException`, and `ArithmeticException` (integer division by zero) account for the vast majority of everyday Java runtime failures.
- Recognizing each one's precise trigger condition — a `null` method call, an out-of-range index, an incompatible cast, unparseable number text, or integer division by zero — speeds up diagnosing real stack traces significantly.
- `ArithmeticException` for division by zero is specific to integer arithmetic; floating-point division by zero instead silently produces `Infinity` or `NaN`, never an exception.
- Writing defensive checks (`null` checks, bounds checks, `instanceof` before casting, validating parseable text) prevents most of these exceptions from occurring in the first place, rather than only reacting to them after the fact.
