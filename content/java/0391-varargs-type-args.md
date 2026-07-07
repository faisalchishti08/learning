---
card: java
gi: 391
slug: varargs-type-args
title: 'Varargs (Type... args)'
---

## 1. What it is

**Varargs** (variable-length arguments), introduced in Java 5, let a method accept any number of arguments of a given type — zero, one, or many — using the `Type... name` syntax in the parameter list (`static int sum(int... numbers)`). Inside the method body, the parameter behaves exactly like an ordinary array of that type (`numbers[0]`, `numbers.length`, or a for-each loop over it). At the call site, you simply pass however many individual values you want, separated by commas — no need to manually wrap them in an array yourself.

## 2. Why & when

Before varargs, a method wanting to accept "any number of arguments" had only two options: force every caller to explicitly build an array (`sum(new int[]{1, 2, 3})`, noisy and easy to get wrong), or declare a fixed set of overloads (`sum(int a)`, `sum(int a, int b)`, `sum(int a, int b, int c)`, ...), which caps the maximum count and duplicates logic. Varargs solve both problems: callers write `sum(1, 2, 3)` as naturally as if `sum` had three fixed parameters, while the method itself only needs to be written once, working correctly for any count of arguments, including zero.

You reach for varargs whenever a method's logical purpose is "combine or process an unbounded number of values of the same type" — `String.format(String, Object...)`, `List.of(T...)`, and a custom `sum(int...)` are all classic examples. A method can have at most one varargs parameter, and it must be the *last* parameter in the list, since the compiler needs to know unambiguously where the fixed parameters end and the variable-length ones begin.

## 3. Core concept

```java
public class VarargsDemo {
    static int sum(int... numbers) { // accepts zero or more int arguments
        int total = 0;
        for (int n : numbers) { // numbers behaves like an ordinary int[] inside the method
            total += n;
        }
        return total;
    }

    public static void main(String[] args) {
        System.out.println(sum());        // zero arguments -- perfectly legal
        System.out.println(sum(5));       // one argument
        System.out.println(sum(1, 2, 3)); // three arguments -- no array-building needed at the call site
    }
}
```

**How to run:** `java VarargsDemo.java`

`sum(int... numbers)` accepts any count of `int` arguments. `sum()` passes zero (a valid call, `numbers` becomes an empty array of length 0), `sum(5)` passes one, and `sum(1, 2, 3)` passes three — the same method handles all three call shapes identically, with `numbers` behaving as an ordinary `int[]` inside the method body regardless of how many arguments were actually passed.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="varargs lets callers pass any number of comma-separated arguments, which the compiler collects into an ordinary array visible inside the method body">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">static int sum(int... numbers) { ... }</text>

  <rect x="30" y="50" width="130" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="95" y="72" fill="#6db33f" font-size="10" text-anchor="middle">sum()</text>

  <rect x="180" y="50" width="130" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="245" y="72" fill="#6db33f" font-size="10" text-anchor="middle">sum(5)</text>

  <rect x="330" y="50" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="430" y="72" fill="#6db33f" font-size="10" text-anchor="middle">sum(1, 2, 3)</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">All three compile to: sum(int[]) receiving arrays of length 0, 1, and 3 respectively -- same method body.</text>
</svg>

## 5. Runnable example

Scenario: a logging helper that formats a message with placeholders, evolved from a version limited to a fixed small number of arguments, through varargs removing that limit entirely, to a version combining varargs with a required first parameter to model "at least one, but any number of, extra values."

### Level 1 — Basic

```java
public class LoggerFixedArity {
    static void log(String message, Object arg1, Object arg2, Object arg3) { // capped at exactly 3 extra args
        String formatted = message
                .replaceFirst("\\{\\}", String.valueOf(arg1))
                .replaceFirst("\\{\\}", String.valueOf(arg2))
                .replaceFirst("\\{\\}", String.valueOf(arg3));
        System.out.println(formatted);
    }

    public static void main(String[] args) {
        log("User {} logged in from {} at {}", "alice", "10.0.0.5", "14:32", null); // forced to pass a 4th, unused arg!
    }
}
```

**How to run:** `java LoggerFixedArity.java`

Fixing the parameter count at exactly three forces every call to supply exactly three values, even when a message happens to need fewer or more placeholders — here, an extra dummy `null` argument had to be added just to satisfy the method's rigid signature, which is both awkward and error-prone.

### Level 2 — Intermediate

```java
public class LoggerVarargs {
    static void log(String message, Object... args) { // any number of extra values, including zero
        String formatted = message;
        for (Object arg : args) {
            formatted = formatted.replaceFirst("\\{\\}", String.valueOf(arg));
        }
        System.out.println(formatted);
    }

    public static void main(String[] args) {
        log("Server started"); // zero extra arguments
        log("User {} logged in", "alice"); // one
        log("User {} logged in from {} at {}", "alice", "10.0.0.5", "14:32"); // three, no dummy padding needed
    }
}
```

**How to run:** `java LoggerVarargs.java`

`Object... args` removes the fixed-count limitation entirely: `log` is called with zero, one, and three extra arguments across the three calls, each matching exactly how many placeholders that particular message actually needs — no wasted dummy arguments, no separate overloads to maintain.

### Level 3 — Advanced

```java
public class LoggerRequiredPlusVarargs {
    enum Level { INFO, WARN, ERROR }

    static void log(Level level, String message, Object... args) { // level required, message required, args variable
        String formatted = message;
        for (Object arg : args) {
            formatted = formatted.replaceFirst("\\{\\}", String.valueOf(arg));
        }
        System.out.println("[" + level + "] " + formatted);
    }

    public static void main(String[] args) {
        log(Level.INFO, "Server started");
        log(Level.WARN, "Disk usage at {}%", 87);
        log(Level.ERROR, "Failed to connect to {} after {} retries", "db-primary", 3);
    }
}
```

**How to run:** `java LoggerRequiredPlusVarargs.java`

This demonstrates the common real-world pattern: fixed, required parameters (`level`, `message`) come first, and the varargs parameter (`args`) — necessarily last — captures however many extra values the specific call needs. This mirrors exactly how methods like `String.format(String, Object...)` are shaped: a required format string, followed by an unbounded number of substitution values.

## 6. Walkthrough

Execution starts in `main`. `log(Level.WARN, "Disk usage at {}%", 87)` is called. The compiler matches `Level.WARN` to the `level` parameter and `"Disk usage at {}%"` to the `message` parameter; the single remaining argument, `87` (an `int`, autoboxed to `Integer` since `args` is `Object...`), is collected into a new one-element `Object[]` array and bound to `args`.

Inside `log`, `formatted` starts as `"Disk usage at {}%"`. The `for (Object arg : args)` loop runs once, since `args.length` is `1`. `arg` is the boxed `Integer` `87`. `formatted.replaceFirst("\\{\\}", String.valueOf(arg))` finds the first `{}` in `formatted` and replaces it with `String.valueOf(87)`, which is `"87"` — producing `"Disk usage at 87%"`, reassigned to `formatted`.

After the loop (which only ran once, since there was only one vararg), `System.out.println("[" + level + "] " + formatted)` concatenates `level` (which, since `Level` is an enum, uses its `toString()`, defaulting to its `name()`, `"WARN"`) with `formatted`, producing `[WARN] Disk usage at 87%`, which is printed.

The third call, `log(Level.ERROR, "Failed to connect to {} after {} retries", "db-primary", 3)`, works the same way but collects *two* trailing arguments into a two-element `args` array: `["db-primary", 3]`. The loop runs twice, replacing the first `{}` with `"db-primary"` and the second `{}` with `"3"`, producing `"Failed to connect to db-primary after 3 retries"`, printed as `[ERROR] Failed to connect to db-primary after 3 retries`.

Expected output:
```
[INFO] Server started
[WARN] Disk usage at 87%
[ERROR] Failed to connect to db-primary after 3 retries
```

## 7. Gotchas & takeaways

> A method can have at most one varargs parameter, and it must be the last parameter in the parameter list — `void log(Object... args, String message)` is illegal, since the compiler would have no unambiguous way to know where the variable-length portion ends and the fixed parameter begins.

- `Type... name` lets a method accept any number (including zero) of arguments of that type, collected into an ordinary array visible as `name` inside the method body.
- At the call site, arguments are passed as a plain comma-separated list — the compiler builds the backing array automatically; you can also pass an already-built array directly if you have one.
- Varargs eliminates both the need for callers to manually construct arrays and the need for the method author to write a family of fixed-arity overloads for every supported argument count.
- Combine required fixed parameters with a trailing varargs parameter (as in `log(Level level, String message, Object... args)`) to express "these specific things are mandatory, and then any number of additional values."
- Be aware that varargs interacts with array covariance and generics in subtle ways — see [[varargs-ambiguity-array-passing]] for the specific pitfalls this combination introduces.
