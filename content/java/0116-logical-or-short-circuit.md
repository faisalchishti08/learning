---
card: java
gi: 116
slug: logical-or-short-circuit
title: Logical OR || (short-circuit)
---

## 1. What it is

`||` evaluates two `boolean` operands and produces `true` if either is `true`. It short-circuits in the mirror-image way to `&&`: if the left operand evaluates to `true`, Java never evaluates the right operand at all, because the overall result is already determined to be `true` regardless of what the right side would produce. As with `&&`, this is distinct from the bitwise `|`, which always evaluates both operands.

```java
boolean result = (5 < 10) || (10 / 0 > 0);   // left is true -> right is NEVER evaluated
System.out.println(result);                   // true, and no ArithmeticException is thrown

boolean r2 = (5 > 10) || (3 < 4);              // left is false -> right IS evaluated
System.out.println(r2);                         // true, determined by the right operand
```

The right operand is only evaluated when the left operand is `false` — this enables the "try the cheap/safe check first, fall back to the expensive/risky one only if needed" idiom, and it is the mirror image of `&&`'s "only proceed if the guard passed" idiom.

## 2. Why & when

Short-circuiting `||` is used whenever a fallback or default only needs to be computed if the primary condition fails:

- Providing a default when a value is missing: `if (userPreference == null || userPreference.isEmpty())` — no exception is a concern here specifically, but the same pattern extends to cases where checking `.isEmpty()` on a `null` would throw.
- Fast-path/slow-path logic: `if (cache.containsKey(key) || computeExpensive(key) != null)` avoids `computeExpensive` whenever the cache already has an answer.
- Early-exit validation: `if (input == null || input.trim().isEmpty())` returns `true` (invalid) immediately for `null` input without ever calling `.trim()` on it, which would otherwise throw `NullPointerException`.

## 3. Core concept

```java
public class LogicalOrDemo {

    static boolean loggedCheck(String label, boolean value) {
        System.out.println("  evaluating: " + label);
        return value;
    }

    public static void main(String[] args) {
        System.out.println("Case 1: left is true");
        boolean r1 = loggedCheck("left", true) || loggedCheck("right", false);
        System.out.println("Result: " + r1);   // true; "right" never printed

        System.out.println("Case 2: left is false");
        boolean r2 = loggedCheck("left", false) || loggedCheck("right", true);
        System.out.println("Result: " + r2);    // true; "right" WAS printed this time

        // The essential null-or-empty guard pattern
        String input = null;
        if (input == null || input.trim().isEmpty()) {
            System.out.println("Input is missing or blank (safely checked)");
        } else {
            System.out.println("Input: " + input);
        }

        // Cache-or-compute pattern
        java.util.Map<String, String> cache = new java.util.HashMap<>();
        String key = "greeting";
        String value = cache.get(key);
        if (value == null || value.isEmpty()) {
            value = "Hello!";   // compute/default only because the cache check failed
            cache.put(key, value);
        }
        System.out.println("Value: " + value);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Short-circuit OR diagram: when the left operand is true, the right operand box is grayed out and never evaluated, skipping straight to a true result. When the left operand is false, the right operand is evaluated and determines the final result.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">left || right — right is only evaluated if left is false</text>

  <text x="170" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">left = true</text>
  <rect x="30" y="56" width="100" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="77" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">left: true</text>
  <text x="150" y="77" fill="#8b949e" font-size="14" text-anchor="middle">→</text>
  <rect x="170" y="56" width="120" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="230" y="77" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">right: SKIPPED</text>
  <text x="170" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Result: true — right never runs.</text>

  <text x="530" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">left = false</text>
  <rect x="410" y="56" width="100" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="77" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">left: false</text>
  <text x="520" y="77" fill="#8b949e" font-size="14" text-anchor="middle">→</text>
  <rect x="540" y="56" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="77" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">right: evaluated</text>
  <text x="530" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Result: whatever right evaluates to.</text>
</svg>

The right operand of `||` is only ever evaluated after the left operand has already proven to be `false`.

## 5. Runnable example

Scenario: a configuration loader that falls back through several sources (explicit override, environment variable, then a hardcoded default) — a textbook chain of `||`-style fallbacks, extended to handle a case where an earlier "cheap" check should prevent an expensive fallback from running at all.

### Level 1 — Basic

```java
public class FallbackBasic {
    public static void main(String[] args) {
        String override = null;      // no explicit override provided
        String envVar = "production"; // simulate an environment variable being set

        // Falls through: use override if present, else envVar, else a hardcoded default
        String resolved = (override != null && !override.isEmpty()) ? override
                         : (envVar != null && !envVar.isEmpty()) ? envVar
                         : "development";

        System.out.println("Resolved environment: " + resolved);

        // A simpler use of || for a single missing-or-blank check
        String username = "";
        if (username == null || username.isEmpty()) {
            System.out.println("No username provided, using 'guest'");
            username = "guest";
        }
        System.out.println("Username: " + username);
    }
}
```

**How to run:** `java FallbackBasic.java`

`username == null || username.isEmpty()` checks `null` first; since `username` is `""` (not `null`), the left operand is `false`, so the right operand *does* run: `"".isEmpty()` is `true`, and the whole expression is `true`, triggering the fallback to `"guest"`. If `username` had been `null` instead, the left operand alone would be `true`, and `.isEmpty()` would never be called — calling it on a genuinely `null` reference would otherwise throw `NullPointerException`.

### Level 2 — Intermediate

Same configuration loader, now written as a clean chain of `||`-based checks feeding into a proper fallback function, demonstrating how each successive check is only attempted if all prior ones failed (returned `false`/empty).

```java
public class FallbackIntermediate {

    static String firstNonBlank(String... candidates) {
        for (String candidate : candidates) {
            if (candidate != null && !candidate.isEmpty()) {
                return candidate;
            }
        }
        return null;
    }

    public static void main(String[] args) {
        String override = null;
        String envVar = "";          // present but blank — should be skipped too
        String configFile = "staging";
        String hardcodedDefault = "development";

        String resolved = firstNonBlank(override, envVar, configFile, hardcodedDefault);
        System.out.println("Resolved: " + resolved);   // "staging" — skips both null and blank sources

        // Demonstrating the || pattern directly for a two-source case
        String primary = null;
        String secondary = null;
        boolean hasAnySource = (primary != null && !primary.isEmpty())
                              || (secondary != null && !secondary.isEmpty());
        System.out.println("Has any source: " + hasAnySource);  // false — neither source available
    }
}
```

**How to run:** `java FallbackIntermediate.java`

`firstNonBlank` generalizes the `||` fallback chain into a loop over any number of candidates, returning the first one that is both non-null and non-empty — functionally equivalent to writing `candidate1 != null && !candidate1.isEmpty() ? candidate1 : (candidate2 ...)` by hand, but far more maintainable as the number of fallback sources grows. The `hasAnySource` line shows the same short-circuit principle directly with `||`: since `primary` is `null`, the left side of the outer `||` is `false` (because `primary != null` is `false`, and `&&` short-circuits *that* sub-expression to `false` without even trying `.isEmpty()`), so the right side is evaluated, checking `secondary` similarly.

### Level 3 — Advanced

Same configuration system, now with a genuinely expensive fallback (simulating a network or file-system call) that must only run if all cheaper sources fail, verified with a call counter to prove the short-circuit actually prevents unnecessary work — plus a subtlety about combining `||` and `&&` correctly with parentheses.

```java
public class FallbackAdvanced {

    static int expensiveCallCount = 0;

    static String expensiveRemoteFetch() {
        expensiveCallCount++;
        System.out.println("  (expensive remote fetch executed)");
        return "remote-value";
    }

    static boolean isUsable(String value) {
        return value != null && !value.isEmpty();
    }

    public static void main(String[] args) {
        String cached = "cached-value";  // cache hit — the common, fast case

        // The expensive fetch must NOT run when the cache already has a usable value
        String resolved = isUsable(cached) ? cached : expensiveRemoteFetch();
        System.out.println("Resolved (cache hit): " + resolved);
        System.out.println("Expensive calls so far: " + expensiveCallCount);  // 0

        // Now simulate a cache MISS, forcing the expensive path
        String missingCache = null;
        String resolved2 = isUsable(missingCache) ? missingCache : expensiveRemoteFetch();
        System.out.println("Resolved (cache miss): " + resolved2);
        System.out.println("Expensive calls so far: " + expensiveCallCount);  // 1

        // Subtlety: && binds tighter than ||, but parentheses make intent explicit and safe
        boolean cond1 = false, cond2 = true, cond3 = false;
        // Without parens, this means: cond1 || (cond2 && cond3) — NOT (cond1 || cond2) && cond3
        boolean result = cond1 || cond2 && cond3;
        boolean resultExplicit = cond1 || (cond2 && cond3);
        System.out.println("cond1 || cond2 && cond3 : " + result);            // false
        System.out.println("Same, parenthesized:      " + resultExplicit);     // false — identical, confirms precedence
    }
}
```

**How to run:** `java FallbackAdvanced.java`

The ternary `isUsable(cached) ? cached : expensiveRemoteFetch()` is not `||` itself, but it demonstrates the identical short-circuit principle: the `expensiveRemoteFetch()` branch is a separate expression that Java only evaluates if `isUsable(cached)` is `false` — exactly like `||`'s right operand. `expensiveCallCount` staying at `0` after the cache-hit case, then becoming `1` after the deliberately-forced cache-miss case, is direct, verifiable proof that the expensive branch only ran once, precisely when needed. The final section addresses operator precedence: `&&` binds more tightly than `||` (just like `*` binds tighter than `+` in arithmetic), so `cond1 || cond2 && cond3` is parsed as `cond1 || (cond2 && cond3)`, not `(cond1 || cond2) && cond3` — the explicit parenthesized version is shown to produce the identical result, confirming the implicit precedence, but relying on implicit precedence in real code is risky for readability and should generally be made explicit with parentheses anyway.

## 6. Walkthrough

Trace the cache-hit case, `isUsable(cached) ? cached : expensiveRemoteFetch()`, where `cached = "cached-value"`:

**Evaluate the condition.** `isUsable(cached)` runs first: `cached != null` is `true`, and (because `&&` requires both to be true and only proceeds past a `true` left operand) `!cached.isEmpty()` is then checked: `"cached-value".isEmpty()` is `false`, so `!false` is `true`. `isUsable` returns `true` overall.

**Ternary short-circuit.** Because the condition is `true`, the ternary operator evaluates and returns the `?`-branch (`cached`) directly. The `:`-branch, `expensiveRemoteFetch()`, is a completely separate expression that the ternary operator never touches in this case — it is not merely "skipped after being computed," it is never invoked at all.

**Result.** `resolved` is assigned `"cached-value"`. `expensiveCallCount` remains at its initial value, `0`, proving the expensive method body (including its `expensiveCallCount++` line) never executed.

```
isUsable(cached)?
  cached != null?        true
  !cached.isEmpty()?      true
  -> isUsable returns true
        |
        v
ternary: condition true -> evaluate "cached" branch ONLY
         expensiveRemoteFetch() branch: never invoked
        |
        v
resolved = "cached-value"; expensiveCallCount stays 0
```

**Contrast with the cache-miss case.** When `missingCache` is `null`, `isUsable(missingCache)` short-circuits its own internal `&&` at `missingCache != null` (which is `false`), returning `false` without even attempting `.isEmpty()` on the `null` reference. The outer ternary then evaluates its `:`-branch, `expensiveRemoteFetch()`, which increments `expensiveCallCount` to `1` and returns `"remote-value"`.

## 7. Gotchas & takeaways

> **`||` only evaluates its right operand if the left operand is `false`.** This lets you check a cheap or safe condition first and only fall back to an expensive or risky one when necessary — the mirror image of `&&`'s guard pattern.

> **`&&` binds tighter than `||`, just like `*` binds tighter than `+`.** `a || b && c` means `a || (b && c)`, not `(a || b) && c` — relying on this implicit precedence is legal but reduces readability; add explicit parentheses in real code to make the intent unambiguous to future readers.

- `||` short-circuits: if the left operand is `true`, the right operand is never evaluated at all.
- This enables "cheap check first, expensive/risky fallback only if needed" and "null-or-empty" guard patterns.
- The ternary operator (`?:`) has the same short-circuit property for its two branches — only the selected branch is ever evaluated.
- Prefer explicit parentheses when mixing `&&` and `||` in the same expression, even though Java's precedence rules make the grouping unambiguous to the compiler.
