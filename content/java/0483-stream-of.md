---
card: java
gi: 483
slug: stream-of
title: Stream.of()
---

## 1. What it is

`Stream.of(...)`, a `static` factory method, creates a stream directly from a fixed set of values you write out inline — no existing collection or array required first. `Stream.of("a", "b", "c")` produces a three-element `Stream<String>` on the spot. There's also a single-value overload and, for arrays, an overload that treats the array's elements as the stream's elements (equivalent to `Arrays.stream` for reference types) via varargs.

## 2. Why & when

Sometimes the data you want to process as a stream doesn't already exist as a collection or array — it's just a handful of literal values you want to run through a pipeline right where you're writing the code: a small set of test inputs, a fixed list of configuration options, a few known constants to validate or transform together. Building a `List.of(...)` first just to immediately call `.stream()` on it works, but `Stream.of(...)` skips that intermediate step entirely when you don't actually need the `List` for anything else.

You reach for `Stream.of(...)` whenever you want to start a stream pipeline from a small number of values known at the point you're writing the code, rather than from an existing collection or array variable. It's especially handy in quick demonstrations, tests, or small fixed-option validations. For anything already living in a collection or array, `Collection.stream()` or `Arrays.stream(array)` remain the right starting point — `Stream.of` is specifically for values you're writing out directly.

## 3. Core concept

```java
import java.util.stream.*;

Stream<String> names = Stream.of("Alice", "Bob", "Carol"); // three literal values, right here

Stream<Integer> singleValue = Stream.of(42); // the single-value overload

String[] existingArray = {"x", "y", "z"};
Stream<String> fromArray = Stream.of(existingArray); // varargs overload treats it like Arrays.stream

long count = Stream.of("a", "b", "c").filter(s -> !s.equals("b")).count(); // 2
```

`Stream.of` is a varargs method (`static <T> Stream<T> of(T... values)`), so it accepts any number of arguments directly, or a single existing array passed as those varargs.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.of builds a stream directly from literal values written inline, with no collection or array needed first">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="65" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"Alice"</text>
  <rect x="130" y="30" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="175" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"Bob"</text>
  <rect x="240" y="30" width="90" height="34" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="285" y="52" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"Carol"</text>

  <text x="380" y="52" fill="#8b949e" font-size="14" font-family="sans-serif">-&gt;</text>

  <rect x="420" y="30" width="180" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="510" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Stream&lt;String&gt;</text>

  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">No List or array needed first -- the values become the stream directly.</text>
</svg>

Literal values, written right where the pipeline starts, become the stream's elements directly.

## 5. Runnable example

Scenario: validating a small, fixed set of configuration flags — evolved from `Stream.of` with a handful of literal strings, through combining several `Stream.of` calls with `flatMap`-style concatenation for grouped validation, to using `Stream.of` to quickly build a small test harness checking multiple known inputs against one function.

### Level 1 — Basic

```java
import java.util.stream.*;

public class StreamOfBasic {
    public static void main(String[] args) {
        long validCount = Stream.of("enabled", "disabled", "unknown", "enabled")
                .filter(flag -> flag.equals("enabled") || flag.equals("disabled"))
                .count();

        System.out.println("Valid flags: " + validCount);
    }
}
```

**How to run:** `java StreamOfBasic.java`

Expected output:
```
Valid flags: 3
```

`Stream.of("enabled", "disabled", "unknown", "enabled")` creates a four-element stream directly from the four literal strings — no `List` was built as an intermediate step. `.filter(...)` keeps only `"enabled"`/`"disabled"` values (three of the four match), and `.count()` returns that final count.

### Level 2 — Intermediate

```java
import java.util.stream.*;

public class StreamOfConcat {
    public static void main(String[] args) {
        Stream<String> requiredFlags = Stream.of("timeout", "retries");
        Stream<String> optionalFlags = Stream.of("debug", "verbose", "trace");

        // Stream.concat joins two streams end to end -- both were built directly with Stream.of.
        long totalFlags = Stream.concat(requiredFlags, optionalFlags).count();

        System.out.println("Total configured flags: " + totalFlags);

        // Separately: validate each REQUIRED flag is non-blank, using a fresh Stream.of each time
        // (a stream can only be consumed once, so requiredFlags above can't be reused here).
        boolean allRequiredPresent = Stream.of("timeout", "retries")
                .allMatch(flag -> !flag.isBlank());
        System.out.println("All required flags present: " + allRequiredPresent);
    }
}
```

**How to run:** `java StreamOfConcat.java`

Expected output:
```
Total configured flags: 5
All required flags present: true
```

The real-world concern this adds: `Stream.concat` joins two independently-built `Stream.of` results into one combined stream — and, since a stream can only ever be traversed once, a fresh `Stream.of("timeout", "retries")` call is needed for the second check, rather than trying to reuse `requiredFlags`, which was already fully consumed by the earlier `Stream.concat`/`count()` call.

### Level 3 — Advanced

```java
import java.util.function.*;
import java.util.stream.*;

public class StreamOfTestHarness {
    static boolean isValidPort(int port) {
        return port >= 1 && port <= 65535;
    }

    public static void main(String[] args) {
        // A quick, inline "test harness" over a fixed set of known inputs -- exactly the
        // kind of small, literal data set Stream.of is built for.
        record Case(int input, boolean expected) {}

        Stream.of(
                new Case(80, true),
                new Case(0, false),
                new Case(65535, true),
                new Case(65536, false),
                new Case(-1, false)
        ).forEach(testCase -> {
            boolean actual = isValidPort(testCase.input());
            String status = (actual == testCase.expected()) ? "PASS" : "FAIL";
            System.out.println(status + ": isValidPort(" + testCase.input() + ") = " + actual);
        });
    }
}
```

**How to run:** `java StreamOfTestHarness.java`

Expected output:
```
PASS: isValidPort(80) = true
PASS: isValidPort(0) = false
PASS: isValidPort(65535) = true
PASS: isValidPort(65536) = false
PASS: isValidPort(-1) = false
```

`Stream.of(...)` here builds a stream of five `Case` records directly, inline, with no separate `List` variable ever declared — a natural fit for a small, fixed, literal set of test inputs known entirely at the point of writing the code. `.forEach(...)` then runs each case through `isValidPort` and reports whether the actual result matched the expected one.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `Stream.of(...)` is called with five `Case` records constructed inline, directly as arguments — this creates a five-element `Stream<Case>` with no intermediate collection.

`.forEach(testCase -> {...})` processes each `Case` in the order given. For the first case, `Case(80, true)`: `isValidPort(80)` evaluates `80 >= 1 && 80 <= 65535`, both `true`, so `isValidPort` returns `true`. Since `actual` (`true`) equals `testCase.expected()` (`true`), `status` is `"PASS"`, and the line `"PASS: isValidPort(80) = true"` is printed.

For the second case, `Case(0, false)`: `isValidPort(0)` evaluates `0 >= 1`, which is `false`, so the `&&` short-circuits and `isValidPort` returns `false`. `actual` (`false`) matches `expected` (`false`), so `"PASS: isValidPort(0) = false"` prints.

For the third case, `Case(65535, true)`: `65535 >= 1 && 65535 <= 65535`, both `true`, `isValidPort` returns `true`, matching the expected `true` — `"PASS"`.

For the fourth case, `Case(65536, false)`: `65536 >= 1` is `true`, but `65536 <= 65535` is `false`, so `isValidPort` returns `false`, matching the expected `false` — `"PASS"`.

For the fifth case, `Case(-1, false)`: `-1 >= 1` is `false`, short-circuiting to `isValidPort` returning `false`, matching the expected `false` — `"PASS"`.

```
Case(80, true)     --> isValidPort(80)    = true  --> matches expected --> PASS
Case(0, false)     --> isValidPort(0)     = false --> matches expected --> PASS
Case(65535, true)  --> isValidPort(65535) = true  --> matches expected --> PASS
Case(65536, false) --> isValidPort(65536) = false --> matches expected --> PASS
Case(-1, false)    --> isValidPort(-1)    = false --> matches expected --> PASS
```

Since `isValidPort`'s implementation correctly handles every boundary case tested (the valid range's edges at `1` and `65535`, and values just outside it), all five cases print `PASS` — if `isValidPort`'s bounds check had an off-by-one error, at least one of these cases would instead print `FAIL`, immediately flagging exactly which boundary was wrong.

## 7. Gotchas & takeaways

> Every stream, including one built with `Stream.of`, can only be traversed **once** — calling a terminal operation (`count()`, `forEach()`, `collect()`, and similar) consumes it, and any further attempt to use that same stream reference throws `IllegalStateException: stream has already been operated upon or closed`. This is exactly why `StreamOfConcat` above builds a fresh `Stream.of(...)` for its second check rather than reusing `requiredFlags` a second time.

- `Stream.of(values...)` builds a stream directly from literal values written inline, with no `List` or array required as an intermediate step.
- It also accepts a single existing array via its varargs form, behaving equivalently to `Arrays.stream(array)` for reference-type arrays in that case.
- `Stream.concat(streamA, streamB)` joins two streams end to end into one — useful for combining multiple `Stream.of` calls or other stream sources.
- Reach for `Stream.of` specifically when your starting data is a handful of values you're writing directly in the code — for data already living in a collection or array, `Collection.stream()`/`Arrays.stream(array)` are the more direct starting points.
- Remember every stream is single-use: once a terminal operation runs, that stream instance is spent, and a fresh one (a new `Stream.of(...)` call, or re-streaming the original source) is needed for any further processing.
