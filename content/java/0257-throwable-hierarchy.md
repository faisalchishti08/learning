---
card: java
gi: 257
slug: throwable-hierarchy
title: Throwable hierarchy
---

## 1. What it is

`Throwable` is the root class of everything that can be thrown and caught in Java — every exception and error, without exception (no pun intended), ultimately extends it. Directly beneath `Throwable` sit two major subclasses: `Error` (serious problems an application generally should not try to catch or recover from) and `Exception` (conditions a program might reasonably want to catch and handle), and `Exception` itself splits further into checked exceptions and the `RuntimeException` subtree (unchecked exceptions) — both explored in the next few topics.

```java
public class ThrowableHierarchyDemo {
    public static void main(String[] args) {
        Throwable t1 = new Exception("a checked exception");
        Throwable t2 = new RuntimeException("an unchecked exception");
        Throwable t3 = new Error("a serious error");

        System.out.println(t1 instanceof Throwable); // true
        System.out.println(t2 instanceof Exception);  // true — RuntimeException IS-A Exception
        System.out.println(t3 instanceof Exception);   // false — Error is a SEPARATE branch
    }
}
```

`RuntimeException` is a subclass of `Exception`, so `t2 instanceof Exception` is `true`, but `Error` is a completely separate branch from `Exception` — both extend `Throwable` directly, but neither is a subtype of the other, which is why `t3 instanceof Exception` is `false`.

## 2. Why & when

Understanding the `Throwable` hierarchy's shape is foundational to writing correct `try`/`catch` code (the next several topics), since it determines exactly what a given `catch` clause will and will not catch.

- **`Throwable` as the universal catchable type** — `catch (Throwable t)` catches literally anything thrown in Java, including `Error`s; this is almost always too broad in practice (discussed in the gotchas), but understanding that `Throwable` sits at the very top explains why it is even possible to write such a catch-all.
- **`Error` versus `Exception` as a deliberate design signal** — the JDK and JVM throw `Error` subclasses (like `OutOfMemoryError` or `StackOverflowError`) specifically to signal "something has gone catastrophically wrong at a level the application usually cannot meaningfully recover from," while `Exception` subclasses signal "something went wrong that your code might reasonably anticipate and handle."
- **The hierarchy determines what a `catch` block actually catches** — because Java's `catch` matching uses `instanceof`-style polymorphism, a `catch (Exception e)` block catches `Exception` itself and every one of its subclasses (including all of `RuntimeException`'s subtree), but never catches an `Error`, since `Error` is not a subtype of `Exception` at all.

Know this hierarchy any time you're deciding what to catch: catch the most specific type that matches the failures you can genuinely handle, rely on the hierarchy to group related failure types together (catching `Exception` catches nearly every "normal" failure in one clause), and avoid catching `Throwable` or `Error` unless you have a very specific, deliberate reason to (some very high-level frameworks do this for logging before rethrowing, for example).

## 3. Core concept

```java
public class HierarchyCore {
    public static void main(String[] args) {
        try {
            throw new IllegalArgumentException("bad input"); // IllegalArgumentException extends RuntimeException
        } catch (RuntimeException e) {          // catches IllegalArgumentException, since it IS-A RuntimeException
            System.out.println("Caught as RuntimeException: " + e.getMessage());
        }

        try {
            throw new IllegalArgumentException("bad input again");
        } catch (Exception e) {                  // ALSO catches it — RuntimeException IS-A Exception too
            System.out.println("Caught as Exception: " + e.getMessage());
        }
    }
}
```

`IllegalArgumentException` extends `RuntimeException`, which extends `Exception`, which extends `Throwable` — so a single thrown `IllegalArgumentException` can be caught by a `catch` clause naming any one of these four types (`IllegalArgumentException`, `RuntimeException`, `Exception`, or `Throwable`), since `catch` matching follows exactly the same "is-a" polymorphism rules as everywhere else in Java.

## 4. Diagram

<svg viewBox="0 0 600 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Throwable is the root, splitting into Error and Exception, Exception splits further into RuntimeException and checked exceptions, IllegalArgumentException is a specific RuntimeException subclass">
  <rect x="8" y="8" width="584" height="204" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="40" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Throwable</text>

  <line x1="260" y1="50" x2="150" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="340" y1="50" x2="450" y2="80" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="80" y="85" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Error</text>

  <rect x="380" y="85" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="105" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Exception</text>

  <line x1="410" y1="115" x2="360" y2="145" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="490" y1="115" x2="530" y2="145" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="280" y="150" width="160" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">checked exceptions</text>

  <rect x="460" y="150" width="130" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">RuntimeException</text>

  <text x="300" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Error and Exception are separate branches; RuntimeException is the unchecked subtree of Exception.</text>
</svg>

`Throwable` splits into `Error` and `Exception`; `Exception` further splits into checked exceptions and the `RuntimeException` subtree.

## 5. Runnable example

Scenario: a small file-processing routine that must react differently to different failure categories, evolved from a single catch of the exact exception type into a layered set of catches exploiting the hierarchy deliberately.

### Level 1 — Basic

```java
public class ThrowableBasic {
    static int parseAge(String input) {
        return Integer.parseInt(input); // throws NumberFormatException if input isn't a valid integer
    }

    public static void main(String[] args) {
        try {
            System.out.println(parseAge("abc"));
        } catch (NumberFormatException e) { // the EXACT thrown type
            System.out.println("Invalid number: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ThrowableBasic.java`

`Integer.parseInt("abc")` throws `NumberFormatException`, and the `catch` clause names that exact type, so it catches it directly — the simplest, most specific level of catching, matching the thrown type one-to-one.

### Level 2 — Intermediate

Same idea, now catching at the `RuntimeException` level instead of the exact type, demonstrating that a broader catch in the hierarchy still catches the same thrown exception, since `NumberFormatException` is a `RuntimeException` subclass.

```java
public class ThrowableIntermediate {
    static int parseAge(String input) {
        if (input == null) throw new NullPointerException("input is null"); // a DIFFERENT RuntimeException subclass
        return Integer.parseInt(input); // NumberFormatException, also a RuntimeException subclass
    }

    public static void main(String[] args) {
        String[] inputs = { "25", "abc", null };

        for (String input : inputs) {
            try {
                System.out.println("Parsed age: " + parseAge(input));
            } catch (RuntimeException e) { // catches BOTH NumberFormatException and NullPointerException
                System.out.println("Failed to parse '" + input + "': " + e.getClass().getSimpleName());
            }
        }
    }
}
```

**How to run:** `java ThrowableIntermediate.java`

A single `catch (RuntimeException e)` clause catches both `NullPointerException` and `NumberFormatException`, since both are subclasses of `RuntimeException` — this is the hierarchy providing real, practical value: one catch clause handles an entire family of related unchecked failures without needing to enumerate every specific exception type.

### Level 3 — Advanced

Same routine, now with layered catches exploiting the hierarchy deliberately: a specific catch for one exception type that needs special handling, a broader `RuntimeException` catch for everything else unchecked, and a final `Exception` catch as a safety net — demonstrating the standard "most specific first" catch ordering the hierarchy demands.

```java
public class ThrowableAdvanced {
    static int parseAge(String input) throws Exception {
        if (input == null) throw new NullPointerException("input is null");
        if (input.isBlank()) throw new IllegalArgumentException("input is blank"); // more specific handling needed
        int age = Integer.parseInt(input); // NumberFormatException if non-numeric
        if (age < 0 || age > 150) throw new Exception("age out of realistic range: " + age); // a CHECKED exception
        return age;
    }

    public static void main(String[] args) {
        String[] inputs = { "25", "abc", null, "", "200" };

        for (String input : inputs) {
            try {
                System.out.println("Parsed age: " + parseAge(input));
            } catch (IllegalArgumentException e) {          // MOST specific: catches blank-input case specially
                System.out.println("Blank input rejected: " + e.getMessage());
            } catch (RuntimeException e) {                    // broader: catches NullPointerException, NumberFormatException
                System.out.println("Unchecked failure (" + e.getClass().getSimpleName() + "): " + e.getMessage());
            } catch (Exception e) {                            // broadest here: catches the checked "out of range" case
                System.out.println("Checked failure: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java ThrowableAdvanced.java`

The three `catch` clauses are ordered from most specific to least specific — `IllegalArgumentException`, then `RuntimeException`, then `Exception` — which Java *requires*, since `IllegalArgumentException` is itself a `RuntimeException`; placing the broader `RuntimeException` catch first would make the `IllegalArgumentException` catch unreachable, a situation the compiler actually detects and rejects.

## 6. Walkthrough

Trace each iteration of the loop in `ThrowableAdvanced.main`.

**`input = "25"`.** `parseAge("25")`: not `null`, not blank, `Integer.parseInt("25")` succeeds returning `25`; `25 < 0 || 25 > 150` is `false`, so `25` is returned normally. No exception is thrown. Prints `"Parsed age: 25"`.

**`input = "abc"`.** `parseAge("abc")`: not `null`, not blank, `Integer.parseInt("abc")` throws `NumberFormatException`. This propagates up to the `catch` clauses: it does not match `IllegalArgumentException` directly... wait — `NumberFormatException` actually *extends* `IllegalArgumentException` in the JDK, so it *is* caught by the first clause. It prints `"Blank input rejected: For input string: \"abc\""` (the message from `NumberFormatException`, caught here specifically because of this real JDK inheritance relationship — a detail worth knowing, and revisited in the gotchas below).

**`input = null`.** `parseAge(null)`: `input == null` is `true`, so `NullPointerException` is thrown immediately. This is a `RuntimeException` but not an `IllegalArgumentException`, so it skips the first `catch` and matches the second: `catch (RuntimeException e)`. Prints `"Unchecked failure (NullPointerException): input is null"`.

**`input = ""`.** `parseAge("")`: not `null`; `input.isBlank()` is `true`, so `IllegalArgumentException("input is blank")` is thrown directly. This matches the first `catch` clause exactly. Prints `"Blank input rejected: input is blank"`.

**`input = "200"`.** `parseAge("200")`: not `null`, not blank, `Integer.parseInt("200")` succeeds, returning `200`; `200 < 0 || 200 > 150` is `true` (since `200 > 150`), so a checked `Exception("age out of realistic range: 200")` is thrown. This is not a `RuntimeException` at all (it's a direct `Exception`), so it skips both the first and second `catch` clauses and matches the third: `catch (Exception e)`. Prints `"Checked failure: age out of realistic range: 200"`.

```
"25"  -> parses fine -> "Parsed age: 25"
"abc" -> NumberFormatException (IS-A IllegalArgumentException in the JDK) -> caught by 1st clause
null  -> NullPointerException (RuntimeException, not IllegalArgumentException) -> caught by 2nd clause
""    -> IllegalArgumentException("input is blank") -> caught by 1st clause
"200" -> checked Exception("out of range") -> not a RuntimeException at all -> caught by 3rd clause
```

**Final output.**
```
Parsed age: 25
Blank input rejected: For input string: "abc"
Unchecked failure (NullPointerException): input is null
Blank input rejected: input is blank
Checked failure: age out of realistic range: 200
```

## 7. Gotchas & takeaways

> **`NumberFormatException` actually extends `IllegalArgumentException` in the real JDK** — a detail many developers don't realize until they see exactly this kind of layered catch block behave unexpectedly. This means a `catch (IllegalArgumentException e)` clause silently catches `NumberFormatException` too, which can be surprising if you intended that clause only for your own, deliberately-thrown `IllegalArgumentException`s — always check the actual JDK class hierarchy (via documentation) rather than assuming based on names alone.

> **Java's compiler enforces "most specific exception type first" ordering in a chain of `catch` clauses** — attempting to place a broader catch (like `RuntimeException`) before a narrower one it would already catch (like `IllegalArgumentException`) is a compile error ("exception X has already been caught"), precisely because the hierarchy makes the narrower clause unreachable in that order.

- Every exception and error extends `Throwable`, which splits into two separate branches: `Error` (serious, generally unrecoverable) and `Exception` (conditions code might reasonably handle).
- `RuntimeException` is a subtree within `Exception`, representing unchecked exceptions (the next couple of topics cover checked versus unchecked in depth).
- `catch` clause matching follows the same "is-a" polymorphism as the rest of Java: a clause catches its named type and every subclass of it.
- Order `catch` clauses from most specific to least specific; the compiler enforces this and will reject an unreachable, overly broad clause placed too early.
