---
card: java
gi: 439
slug: multi-catch-catch-a-b-e
title: Multi-catch (catch A | B e)
---

## 1. What it is

Multi-catch, added in Java 7, lets one `catch` block handle **several unrelated exception types** at once, separated by `|`: `catch (IOException | SQLException e) { ... }`. Instead of writing near-identical `catch` blocks for each exception type that need the same handling, one block covers all of them. The compiler restricts this to types that aren't related by subclassing (you can't list a type and its own supertype together), and the caught variable's static type becomes the nearest common supertype of all the listed alternatives.

## 2. Why & when

Before Java 7, if two unrelated exception types needed identical handling — logging, wrapping, or a generic error message — you had two options, both unsatisfying: write the same handling code twice, in two separate `catch` blocks (duplication, and a maintenance risk if one copy gets updated and the other doesn't), or catch the broader `Exception` (losing precision, and potentially catching exceptions you didn't intend to handle this way). Multi-catch removes that tradeoff: list every exception type that needs the same treatment, write the handling logic once, and the compiler still enforces that you're catching exactly those specific types — no accidental over-broad catching.

You reach for multi-catch whenever two or more distinct exception types genuinely warrant the same response — parsing code that can fail with either `NumberFormatException` or `ArithmeticException`, I/O code that can fail with several checked exception subtypes needing identical logging, or any case where duplicating a `catch` block would be pure repetition.

## 3. Core concept

```java
try {
    // code that might throw either NumberFormatException or ArithmeticException
} catch (NumberFormatException | ArithmeticException e) {
    // ONE handler for both -- before Java 7, this required two separate catch blocks
    System.out.println("Failed: " + e.getMessage());
}
```

Two important rules: the listed types **cannot** be related by subclassing (you can't write `catch (IOException | FileNotFoundException e)`, since `FileNotFoundException` already *is* an `IOException`), and the caught variable `e` is implicitly **final** — it cannot be reassigned inside the `catch` block, unlike a single-type `catch` variable.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A multi-catch block routes several unrelated exception types into one shared handler, instead of duplicating the same handling code across separate catch blocks">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">NumberFormatException</text>
  <rect x="30" y="70" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="90" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ArithmeticException</text>

  <rect x="330" y="50" width="200" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="430" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ONE catch block</text>

  <line x1="170" y1="45" x2="325" y2="60" stroke="#8b949e" marker-end="url(amc1)"/>
  <line x1="170" y1="85" x2="325" y2="68" stroke="#8b949e" marker-end="url(amc1)"/>
  <text x="430" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">caught variable's static type: nearest common supertype (often Exception)</text>
  <defs><marker id="amc1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Unrelated exception types converge into one handler; the caught variable's usable type is only what all of them have in common.

## 5. Runnable example

Scenario: parsing and processing untrusted input across a couple of failure-prone operations — the same handling logic, evolved from a basic multi-catch covering two exception types, through logging-and-rethrowing with an implicitly-final caught variable, to correctly working with the caught variable's common-supertype static type when the listed exceptions come from entirely unrelated subsystems.

### Level 1 — Basic

```java
public class MultiCatchBasic {
    static int parse(String text) {
        return Integer.parseInt(text) / 0; // deliberately triggers ArithmeticException after a valid parse
    }

    public static void main(String[] args) {
        String[] inputs = {"abc", "42"};
        for (String input : inputs) {
            try {
                int result = parse(input);
                System.out.println("Result: " + result);
            } catch (NumberFormatException | ArithmeticException e) {
                // ONE handler for two unrelated exception types -- before Java 7, this needed two catch blocks
                System.out.println("Failed to process \"" + input + "\": " + e.getClass().getSimpleName());
            }
        }
    }
}
```

**How to run:** `java MultiCatchBasic.java`

`"abc"` fails `Integer.parseInt` with `NumberFormatException`; `"42"` parses fine but then divides by zero, throwing `ArithmeticException` — both are handled by the same `catch` block, since the same "processing failed" response applies to either.

### Level 2 — Intermediate

```java
import java.io.*;

public class MultiCatchLogRethrow {
    static void loadConfig(String path) throws IOException, InterruptedException {
        if (path.equals("missing.conf")) throw new FileNotFoundException(path + " not found");
        if (path.equals("locked.conf")) throw new InterruptedException("interrupted while waiting for lock");
    }

    static void loadWithLogging(String path) throws IOException, InterruptedException {
        try {
            loadConfig(path);
        } catch (IOException | InterruptedException e) {
            // e is implicitly final here -- you cannot reassign it inside the catch block
            System.out.println("Logging failure for " + path + ": " + e.getMessage());
            throw e; // rethrow after logging -- caller still sees the ORIGINAL exception type
        }
    }

    public static void main(String[] args) {
        for (String path : new String[]{"missing.conf", "locked.conf"}) {
            try {
                loadWithLogging(path);
            } catch (IOException e) {
                System.out.println("Caller caught IOException: " + e.getMessage());
            } catch (InterruptedException e) {
                System.out.println("Caller caught InterruptedException: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java MultiCatchLogRethrow.java`

The multi-catch logs both failure types identically, then `throw e;` rethrows — and because `e`'s precise runtime type is preserved (Java 7's "more precise rethrow," covered in the next tutorial, keeps track of this), the caller's separate `catch (IOException e)` and `catch (InterruptedException e)` blocks each correctly receive the exception they expect, rather than both needing to catch some broader common type.

### Level 3 — Advanced

```java
import java.io.*;
import java.sql.*;

public class MultiCatchCommonSupertype {
    static void readFile() throws IOException {
        throw new IOException("disk read failed");
    }
    static void queryDatabase() throws SQLException {
        throw new SQLException("connection refused", "08001", 500);
    }

    static void loadData(boolean fromFile) throws IOException, SQLException {
        if (fromFile) readFile(); else queryDatabase();
    }

    public static void main(String[] args) {
        for (boolean fromFile : new boolean[]{true, false}) {
            try {
                loadData(fromFile);
            } catch (IOException | SQLException e) {
                // e's STATIC type here is Exception (the nearest common supertype of IOException and SQLException) --
                // only methods available on Exception itself can be called directly, without a cast.
                System.out.println("[" + e.getClass().getSimpleName() + "] " + e.getMessage());

                if (e instanceof SQLException sqlEx) {
                    // need an explicit instanceof check to access SQLException-SPECIFIC members like getSQLState()
                    System.out.println("  SQL state: " + sqlEx.getSQLState());
                }
            }
        }
    }
}
```

**How to run:** `java MultiCatchCommonSupertype.java`

`IOException` and `SQLException` share no common supertype closer than `Exception` itself, so `e`'s *static* type inside the block is `Exception` — calling `e.getMessage()` works fine (declared on `Exception`), but accessing `SQLException`-specific members like `getSQLState()` requires an explicit `instanceof` pattern match first, since the compiler can't assume `e` is specifically a `SQLException` just because it *might* be.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The loop runs twice: once with `fromFile = true`, once with `fromFile = false`.

**First iteration (`fromFile = true`):** `loadData(true)` calls `readFile()`, which throws `new IOException("disk read failed")`. This propagates up to the `catch (IOException | SQLException e)` block. `e.getClass().getSimpleName()` is `"IOException"`, and `e.getMessage()` is `"disk read failed"` — printed as `"[IOException] disk read failed"`. The `if (e instanceof SQLException sqlEx)` check is `false` (this `e` is an `IOException`, not a `SQLException`), so the SQL-state-printing branch is skipped entirely.

**Second iteration (`fromFile = false`):** `loadData(false)` calls `queryDatabase()`, which throws `new SQLException("connection refused", "08001", 500)` — the second constructor argument is the SQL state code, the third an error code. This is caught by the same multi-catch block. `e.getClass().getSimpleName()` is now `"SQLException"`, `e.getMessage()` is `"connection refused"` — printed as `"[SQLException] connection refused"`. This time, `e instanceof SQLException sqlEx` is `true`: the pattern match succeeds, binding `sqlEx` as a properly-typed `SQLException` reference, and `sqlEx.getSQLState()` (a method that doesn't exist on the plain `Exception` type) is called, printing `"  SQL state: 08001"`.

Expected output:
```
[IOException] disk read failed
[SQLException] connection refused
  SQL state: 08001
```

## 7. Gotchas & takeaways

> The exception types listed in a multi-catch **cannot be related by subclassing** — `catch (IOException | FileNotFoundException e)` is a compile error (`"Alternative FileNotFoundException is a subclass of alternative IOException"`), since listing both is redundant: catching `IOException` alone already covers every `FileNotFoundException` too. If you get this error, simply remove the more specific subtype from the list (or restructure into a separate `catch` block first, if it genuinely needs different handling).

- Multi-catch (`catch (A | B e)`) lets one handler cover multiple unrelated exception types, avoiding duplicated `catch` blocks for identical handling logic.
- The listed types must not be related by subclassing — the compiler rejects redundant combinations where one type already covers another.
- The caught variable is implicitly **final** inside a multi-catch block — unlike a single-type `catch`, you cannot reassign it.
- The caught variable's *static* type is the nearest common supertype of all the listed alternatives — only members available on that common type can be called directly; accessing a type-specific member requires an `instanceof` pattern match first.
- Rethrowing a caught multi-catch exception (`throw e;`) preserves its precise runtime type for the caller, thanks to Java 7's "more precise rethrow" analysis, covered in the next tutorial.
