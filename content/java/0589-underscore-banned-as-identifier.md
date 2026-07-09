---
card: java
gi: 589
slug: underscore-banned-as-identifier
title: 'Underscore ''_'' banned as identifier'
---

## 1. What it is

Since Java 9, a single underscore (`_`) can no longer be used as a variable, method, class, or any other identifier name — code that compiled fine on Java 8 using `_` as a name now fails with a compile error. The underscore was reserved specifically so a future Java version could give it special meaning (which eventually happened: Java 21 introduced `_` as an unnamed-variable pattern for cases where a variable must be declared but is never used).

## 2. Why & when

Java 8 already deprecated using `_` as an identifier, with a compiler warning: `'_' used as an identifier might not be supported in releases after Java SE 8`. That warning was Oracle signaling a plan, not yet an enforced rule — Java 9 turned it into a hard compile error. The motivation was forward-looking: language designers wanted to reserve `_` for a genuinely useful future purpose (a stand-in for "I have to write a variable here syntactically, but I don't care about its name or value") without that future feature clashing with existing code that happened to use `_` as an ordinary variable name. This matters directly if you're migrating code from Java 8 or earlier that used `_` anywhere as an identifier — it will fail to compile on Java 9+ until renamed, and understanding why explains the seemingly odd restriction.

## 3. Core concept

```java
// Compiles on Java 8 (with a deprecation warning), FAILS to compile on Java 9+:
int _ = 5;
String _ = "hello";

// Always fine, on every Java version — underscore is legal as PART of a longer identifier:
int my_count = 5;
int _internal = 10;
int total_ = 15;
```

The restriction applies only to `_` as the **entire** identifier, standing completely alone — using underscore as part of a multi-character name (`my_count`), or even as the sole character of a name that also includes other characters, remains completely unaffected and always has been legal.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bare underscore as an identifier is banned since Java 9; underscore within a longer identifier remains fine">
  <rect x="20" y="20" width="280" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="45" fill="#f85149" font-size="12" text-anchor="middle" font-family="monospace">int _ = 5;  // compile ERROR (Java 9+)</text>

  <rect x="320" y="20" width="300" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">int my_count = 5;  // always fine</text>

  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">Only a BARE, standalone "_" is banned — underscore as part of a longer name was never restricted.</text>
</svg>

The ban targets exactly one specific token — a lone underscore — not the underscore character in general.

## 5. Runnable example

Scenario: a small statistics accumulator, showing exactly the kind of variable naming that breaks when migrating from a Java 8 codebase — starting with legal Java 8-era code using `_` as a throwaway loop variable name, then the same code updated to compile on Java 9+, then a look at what `_` actually means in modern Java (21+) once it was given real meaning as an unnamed-variable pattern.

### Level 1 — Basic

```java
// Legal on Java 8 (with a deprecation warning); FAILS to compile on Java 9+.
public class LegacyLoop {
    public static void main(String[] args) {
        int sum = 0;
        for (int _ = 0; _ < 5; _++) { // "_" used as an ordinary loop variable name
            sum += 1;
        }
        System.out.println("Sum: " + sum);
    }
}
```

**How to run (on a Java 9+ JDK):** `java LegacyLoop.java`

Expected output (compilation fails — this is the intended demonstration; exact wording varies slightly by JDK version, since later versions like 21+ also recognize `_` as a preview unnamed-variable pattern in declaration position specifically):
```
LegacyLoop.java:4: error: unnamed variables are a preview feature and are disabled by default.
        for (int _ = 0; _ < 5; _++) {
                 ^
  (use --enable-preview to enable unnamed variables)
LegacyLoop.java:4: error: as of release 9, '_' is a keyword, and may not be used as an identifier
        for (int _ = 0; _ < 5; _++) {
                        ^
LegacyLoop.java:4: error: as of release 9, '_' is a keyword, and may not be used as an identifier
        for (int _ = 0; _ < 5; _++) {
                               ^
3 errors
```

On Java 8, this loop compiled successfully (with only a deprecation warning suggesting the practice would eventually be removed). On Java 9 and later, the compiler treats a bare `_` as a reserved word rather than an available identifier — its use in the loop condition and increment (`_ < 5`, `_++`) both fail with the same "as of release 9" error. On a newer JDK such as 21, the *declaration* itself (`int _ = 0`) is instead recognized as an attempt at the unnamed-variable pattern (covered in Level 3) — which is real syntax, just gated behind a preview flag not enabled by default — producing a related but distinctly worded error for that specific position.

### Level 2 — Intermediate

```java
// Migrated for Java 9+: the loop variable is simply renamed to something meaningful.
public class ModernLoop {
    public static void main(String[] args) {
        int sum = 0;
        for (int i = 0; i < 5; i++) { // renamed "_" -> "i", a small, mechanical fix
            sum += 1;
        }
        System.out.println("Sum: " + sum);
    }
}
```

**How to run:** `java ModernLoop.java`

Expected output:
```
Sum: 5
```

The real-world concern this adds: the fix for code broken by this change is almost always this simple — rename `_` to any other legal identifier (`i`, `ignored`, `unused`, whatever fits the codebase's naming conventions). There's no deeper behavioral change to reason about; `_` was never doing anything special before Java 9 beyond being a legal, if unconventional, variable name, so replacing it changes nothing about the program's logic or output.

### Level 3 — Advanced

```java
// Java 21+: "_" is now a genuinely meaningful unnamed-variable pattern, not just a banned identifier.
import java.util.*;

public class UnnamedVariablePattern {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        List<Point> points = List.of(new Point(1, 2), new Point(3, 4), new Point(5, 6));

        int totalX = 0;
        for (Point p : points) {
            totalX += p.x();
        }
        System.out.println("Total x: " + totalX);

        // "_" here means "I must catch this exception type, but I don't need its value" —
        // this is the NEW, intentional meaning "_" was reserved for back in Java 9.
        try {
            Integer.parseInt("not a number");
        } catch (NumberFormatException _) {
            System.out.println("Caught a parse failure (details intentionally ignored)");
        }
    }
}
```

**How to run:** on Java 22+, `java UnnamedVariablePattern.java` runs directly (unnamed variables became a permanent, non-preview feature in Java 22, JEP 456). On Java 21, the same syntax exists only as a **preview** feature (JEP 443) and requires two extra flags: `java --source 21 --enable-preview UnnamedVariablePattern.java`.

Expected output:
```
Total x: 9
```
```
Caught a parse failure (details intentionally ignored)
```

This handles the production-flavoured payoff of the whole Java 9 restriction: `catch (NumberFormatException _)` uses `_` as an **unnamed variable pattern** — previewed in Java 21 (JEP 443) and finalized as a permanent language feature in Java 22 (JEP 456) — that lets code declare "a variable has to go here syntactically, but I'm never going to reference it" without inventing a throwaway name like `e` or `ignored` that static analysis tools might otherwise flag as unused. This exact syntax would have been ambiguous or impossible to introduce cleanly if `_` had still been usable as an arbitrary identifier — Java 9's ban is precisely what made this later feature possible without breaking any existing code that used `_` as a normal name.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `points` is built as an immutable `List<Point>` with three records.

The `for (Point p : points)` loop iterates each `Point`, accumulating `p.x()` into `totalX`: `1 + 3 + 5 = 9`. `main` prints `"Total x: 9"`.

Next, `main` enters a `try` block attempting `Integer.parseInt("not a number")`. Since `"not a number"` isn't a valid integer, `parseInt` throws `NumberFormatException`.

```
try { Integer.parseInt("not a number"); }
catch (NumberFormatException _) { ... }
                         |
                         v
      the exception object IS caught (control transfers to the catch block),
      but the variable normally used to reference it (traditionally named "e")
      is replaced with "_", signaling to any reader: "this exception's specific
      details are never inspected inside this catch block."
```

Control transfers to the `catch (NumberFormatException _)` block. The exception is genuinely caught — the program does not crash, and the catch block's body does run — but `_` is not a usable variable inside that block; unlike a normally-named catch parameter (`catch (NumberFormatException e)`, where `e.getMessage()` or similar would be available), `_` signals that this specific exception instance's details are deliberately never going to be referenced. `System.out.println("Caught a parse failure (details intentionally ignored)")` runs, printing that message, and the program continues normally after the `try`/`catch` block, having handled the exception without ever needing (or being able) to name it.

The deeper point this demonstrates: Java 9's seemingly minor "you can't name a variable `_` anymore" restriction was the necessary first step, twelve years before Java 21 shipped, toward giving `_` this cleaner, purpose-built meaning — reserving the token early meant Java 21 could introduce unnamed variables without any risk of silently changing the behavior of code still using `_` as an ordinary name somewhere.

## 7. Gotchas & takeaways

> The `_` restriction is purely about `_` as a **complete, standalone identifier** — `_count`, `count_`, `my_variable`, and every other identifier that merely *contains* an underscore remain completely legal on every Java version, past and present. Only code using the bare single character `_` by itself as an entire name is affected by this change; a search-and-replace migration fix should target exactly that pattern, not underscores in general.

- This change was announced well in advance: Java 8 already emitted a deprecation warning for `_` as an identifier specifically so codebases would have time to migrate before Java 9 turned it into a hard error.
- Automated migration tooling (or a simple regex-based search) can typically find every affected usage by searching for a lone `_` token used in variable, parameter, or method declarations — since the fix is always a mechanical rename with no behavioral change, this is a safe, low-risk class of migration to automate.
- Unlike most language changes, this one has no partial or gradual enforcement — there is no compiler flag to re-enable `_` as an identifier on Java 9+; the only fix is renaming.
- The unnamed-variable pattern (`_`), finalized in Java 22, extends beyond `catch` blocks — it also works for unused lambda parameters, unused pattern-matching bindings in `switch` expressions, and unused local variables in some contexts, all sharing the same underlying reserved token this Java 9 change made available.
- If a codebase must still compile against both an older JDK version and Java 9+, avoid `_` as an identifier entirely going forward — there's no version-conditional way to keep using it, and the earliest JDK version the code needs to support determines whether the deprecation warning (Java 8) or the hard error (Java 9+) applies.
