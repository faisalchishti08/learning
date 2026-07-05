---
card: java
gi: 85
slug: boolean-literals
title: boolean literals
---

## 1. What it is

Java has exactly two boolean literals: `true` and `false`. They are reserved words (keywords), not values of an enumeration or integers — `true` cannot be cast from `1` and `false` cannot be cast from `0`. A boolean literal has type `boolean` and is the only way to express a boolean constant directly in source code.

```java
boolean isOpen   = true;
boolean isClosed = false;
boolean result   = (5 > 3);   // not a literal, but evaluates to true
```

`true` and `false` are lowercase only. `True`, `TRUE`, and `False` are all compile errors if used as boolean values.

## 2. Why & when

Boolean literals appear as:
- Direct flag assignments (`boolean debug = true;`).
- Default return values in short-circuit guard methods (`return false;`).
- Unit-test assertions (`assertEquals(true, actual)` or simply `assertTrue(actual)`).
- Comparisons — though comparing to `true` is almost always redundant: `if (flag == true)` should be `if (flag)`.

The main design insight is that Java deliberately keeps `boolean` isolated from integers. You cannot pass `1` where `boolean` is expected, and you cannot compare `boolean` with `==` to an integer. This eliminates a whole class of bugs that plague C and C++ code.

## 3. Core concept

```java
// ---- Two and only two values ----
boolean t = true;
boolean f = false;

// ---- No conversion from int ----
// boolean bad = 1;   // compile error — not implicit
// boolean bad = (boolean) 1;   // compile error — no cast
boolean explicit = (1 != 0);   // OK — expression yields boolean

// ---- Comparison ----
System.out.println(t == true);    // true  — but redundant
System.out.println(t == false);   // false — also redundant
System.out.println(!t);           // false — prefer this style
System.out.println(t);            // true  — direct, idiomatic

// ---- Anti-patterns ----
// Anti-pattern: returning a conditional via if/else
boolean isEven1(int n) {
    if (n % 2 == 0) return true;
    else return false;
}
// Better: return the expression directly
boolean isEven2(int n) { return n % 2 == 0; }

// ---- Boolean literals as method arguments ----
// Literal boolean args are often a "flag argument" smell:
doWork(true, false);            // what do these mean?
doWork(/* async= */ true, /* retry= */ false);  // comment helps but still bad
// Better API: separate methods or record/enum config

// ---- Boolean wrapper: Boolean ----
Boolean boxed = Boolean.TRUE;     // cached singleton — same as true but boxed
Boolean boxed2 = true;            // autoboxing
System.out.println(boxed == Boolean.TRUE);   // true — same instance (cached)
System.out.println(boxed.equals(true));      // true
Boolean nullBool = null;
// if (nullBool) { }   // NPE: unboxing null Boolean

// ---- Boolean.toString ----
System.out.println(Boolean.toString(true));   // "true"
System.out.println(Boolean.parseBoolean("TRUE"));  // true (case-insensitive)
System.out.println(Boolean.parseBoolean("yes"));   // false (only "true" parses as true)

static void doWork(boolean async, boolean retry) {}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="boolean literal: true and false as the only two values, no integer coercion, Boolean wrapper with null risk, and anti-pattern vs idiomatic return">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <!-- Two values -->
  <rect x="16" y="18" width="200" height="133" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="116" y="36" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">boolean</text>
  <text x="116" y="50" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">exactly two values</text>
  <line x1="26" y1="56" x2="206" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <text x="116" y="80" fill="#6db33f" font-size="20" text-anchor="middle" font-family="monospace">true</text>
  <text x="116" y="105" fill="#e6edf3" font-size="20" text-anchor="middle" font-family="monospace">false</text>
  <text x="116" y="125" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">no coercion from int</text>
  <text x="116" y="141" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">keywords — lowercase only</text>

  <!-- Anti-pattern vs idiom -->
  <rect x="228" y="18" width="240" height="133" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="348" y="36" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Return style</text>
  <line x1="238" y1="42" x2="458" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="238" y="56" fill="#8b949e" font-size="7.5" font-family="sans-serif">Anti-pattern:</text>
  <rect x="238" y="60" width="210" height="32" rx="3" fill="#0d1117"/>
  <text x="243" y="73" fill="#8b949e" font-size="7" font-family="monospace">if (n%2==0) return true;</text>
  <text x="243" y="84" fill="#8b949e" font-size="7" font-family="monospace">else return false;</text>
  <text x="238" y="105" fill="#6db33f" font-size="7.5" font-family="sans-serif">Idiom:</text>
  <rect x="238" y="109" width="210" height="18" rx="3" fill="#0d1117"/>
  <text x="243" y="121" fill="#6db33f" font-size="7" font-family="monospace">return n % 2 == 0;</text>
  <text x="238" y="142" fill="#8b949e" font-size="7" font-family="sans-serif">expression yields boolean directly</text>

  <!-- Boolean wrapper -->
  <rect x="480" y="18" width="204" height="133" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="582" y="36" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Boolean</text>
  <text x="582" y="50" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">wrapper class</text>
  <line x1="490" y1="56" x2="674" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <text x="490" y="70" fill="#e6edf3" font-size="7.5" font-family="monospace">Boolean.TRUE  (cached)</text>
  <text x="490" y="83" fill="#e6edf3" font-size="7.5" font-family="monospace">Boolean.FALSE (cached)</text>
  <text x="490" y="96" fill="#e6edf3" font-size="7.5" font-family="monospace">null — third state</text>
  <line x1="490" y1="103" x2="674" y2="103" stroke="#8b949e" stroke-width="0.5"/>
  <text x="490" y="117" fill="#8b949e" font-size="7.5" font-family="monospace">unboxing null → NPE</text>
  <text x="490" y="130" fill="#8b949e" font-size="7.5" font-family="monospace">parseBoolean("true") → true</text>
  <text x="490" y="143" fill="#8b949e" font-size="7.5" font-family="monospace">parseBoolean("yes") → false</text>
</svg>

`true` and `false` are reserved keywords; Java has no implicit coercion from integers, and the only values that satisfy a boolean expression are `true` and `false`.

## 5. Runnable example

Scenario: a feature-flag registry for a configuration system — boolean flags control feature activation, logging, and maintenance mode, with the scenario growing from simple flag storage to tri-state Boolean handling (null = "not configured") to parsing config file boolean strings.

### Level 1 — Basic

```java
public class BooleanLiteralsBasic {

    static boolean FEATURE_SEARCH  = true;
    static boolean FEATURE_PAYMENT = false;
    static boolean DEBUG_MODE      = false;

    public static void main(String[] args) {
        System.out.println("=== Feature flags ===");
        System.out.println("search  enabled: " + FEATURE_SEARCH);
        System.out.println("payment enabled: " + FEATURE_PAYMENT);
        System.out.println("debug mode     : " + DEBUG_MODE);

        // Idiomatic conditions
        if (FEATURE_SEARCH) {
            System.out.println("\nSearch feature is ON");
        }
        if (!FEATURE_PAYMENT) {
            System.out.println("Payment feature is OFF");
        }

        // Return a boolean expression directly
        System.out.println("\nAll features enabled: " + allEnabled());
        System.out.println("Any feature enabled : " + anyEnabled());
    }

    static boolean allEnabled() {
        return FEATURE_SEARCH && FEATURE_PAYMENT;   // direct boolean expression
    }

    static boolean anyEnabled() {
        return FEATURE_SEARCH || FEATURE_PAYMENT;
    }
}
```

**How to run:** `java BooleanLiteralsBasic.java`

`FEATURE_SEARCH = true` and `FEATURE_PAYMENT = false` are boolean literals assigned to static fields. `if (FEATURE_SEARCH)` is the idiomatic form — never write `if (FEATURE_SEARCH == true)`, which is redundant. `allEnabled()` and `anyEnabled()` return boolean expressions directly without wrapping them in `if/else return true; else return false;`.

### Level 2 — Intermediate

Same registry: use `Boolean` (boxed) to represent "not yet configured" as `null`, distinguish it from explicitly `false`, and avoid the unboxing NPE.

```java
import java.util.HashMap;
import java.util.Map;

public class BooleanLiteralsIntermediate {

    // null = not configured; true/false = explicit setting
    static final Map<String, Boolean> FLAGS = new HashMap<>();

    static {
        FLAGS.put("search",  true);
        FLAGS.put("payment", false);
        // "reports" is absent — not configured
    }

    static boolean isEnabled(String feature) {
        Boolean val = FLAGS.get(feature);
        // Safe: Boolean.TRUE.equals handles null without NPE
        return Boolean.TRUE.equals(val);
    }

    static String describe(String feature) {
        Boolean val = FLAGS.get(feature);
        if (val == null)    return feature + ": NOT CONFIGURED";
        if (val)            return feature + ": ENABLED";
        return                     feature + ": DISABLED";
    }

    public static void main(String[] args) {
        for (String f : new String[]{"search", "payment", "reports"}) {
            System.out.println(describe(f));
            System.out.println("  isEnabled: " + isEnabled(f));
        }

        // NPE trap demonstration
        System.out.println();
        Boolean notSet = null;
        System.out.println("Boolean.TRUE.equals(null) : " + Boolean.TRUE.equals(notSet));  // false, safe
        try {
            boolean unboxed = notSet;   // NPE!
        } catch (NullPointerException e) {
            System.out.println("Unboxing null Boolean throws NPE — caught: " + e.getClass().getSimpleName());
        }
    }
}
```

**How to run:** `java BooleanLiteralsIntermediate.java`

`Boolean` (boxed) can hold `null`, representing a "not configured" state that is distinct from explicitly disabled (`false`). `Boolean.TRUE.equals(val)` returns `false` when `val` is `null` instead of throwing — the key safe idiom for null-tolerant boolean checks. Directly unboxing `null` with `boolean unboxed = notSet` throws `NullPointerException` at runtime.

### Level 3 — Advanced

Same registry: parse boolean values from a properties file (represented as strings), handle all recognised string forms, and build a typed registry with change tracking.

```java
import java.util.*;

public class BooleanLiteralsAdvanced {

    record FlagChange(String feature, Boolean before, boolean after) {}

    static final Map<String, Boolean> REGISTRY = new LinkedHashMap<>();
    static final List<FlagChange>     CHANGELOG = new ArrayList<>();

    // Recognise "true", "yes", "1", "on" as true (case-insensitive)
    static boolean parseFlag(String value) {
        if (value == null) return false;
        return switch (value.trim().toLowerCase()) {
            case "true", "yes", "1", "on", "enabled"  -> true;
            case "false", "no", "0", "off", "disabled" -> false;
            default -> throw new IllegalArgumentException("Unrecognised boolean value: " + value);
        };
    }

    static void setFlag(String feature, String rawValue) {
        boolean newVal = parseFlag(rawValue);
        Boolean oldVal = REGISTRY.put(feature, newVal);
        if (!Boolean.valueOf(newVal).equals(oldVal)) {
            CHANGELOG.add(new FlagChange(feature, oldVal, newVal));
        }
    }

    public static void main(String[] args) {
        // Simulate loading from a config file
        String[][] config = {
            {"search",       "true"},
            {"payment",      "no"},
            {"dark_mode",    "1"},
            {"maintenance",  "off"},
            {"beta",         "enabled"},
        };

        for (String[] entry : config) {
            setFlag(entry[0], entry[1]);
        }

        System.out.println("=== Feature registry ===");
        REGISTRY.forEach((k, v) -> System.out.printf("  %-14s = %b%n", k, v));

        // Apply a change
        setFlag("payment", "on");
        setFlag("maintenance", "true");

        System.out.println("\n=== Change log ===");
        CHANGELOG.forEach(c -> System.out.printf("  %-14s  %s → %b%n",
            c.feature(), c.before() == null ? "null" : c.before(), c.after()));

        // Demonstrate all truthy and falsy strings
        System.out.println("\n=== parseFlag truthy/falsy ===");
        for (String s : new String[]{"true","yes","1","on","enabled","false","no","0","off","disabled"}) {
            System.out.printf("  %-10s → %b%n", s, parseFlag(s));
        }
    }
}
```

**How to run:** `java BooleanLiteralsAdvanced.java`

`Boolean.parseBoolean` only recognises `"true"` (case-insensitive) — everything else becomes `false`, including `"yes"` and `"1"`. The custom `parseFlag` extends this to all common truthy/falsy conventions. `Boolean.valueOf(newVal).equals(oldVal)` safely compares the new `boolean` (boxed) to the old `Boolean` (which may be `null`). `LinkedHashMap` preserves insertion order for consistent printout.

## 6. Walkthrough

Execution trace through `BooleanLiteralsAdvanced.main`:

**Config loading.** `setFlag("search", "true")` calls `parseFlag("true")`. The `switch` matches `"true"` → `true`. `REGISTRY.put("search", true)` returns `null` (no prior value). `Boolean.valueOf(true).equals(null)` = `false`, so a `FlagChange("search", null, true)` is added.

**`setFlag("payment", "no")`.** `parseFlag("no")` → `false`. `REGISTRY.put("payment", false)` returns `null`. Change logged: `("payment", null, false)`.

**`setFlag("payment", "on")`.** `parseFlag("on")` → `true`. `REGISTRY.put("payment", true)` returns the old value `Boolean.FALSE`. `Boolean.valueOf(true).equals(Boolean.FALSE)` = `false` (they differ), so a change is logged: `("payment", false, true)`.

**Change log output.** For each `FlagChange`, `c.before()` returns the old `Boolean` (possibly `null`). The `null` display is handled by the ternary `c.before() == null ? "null" : c.before()`. The log shows the full audit trail of flag mutations.

```
setFlag("search", "true"):
  parseFlag → true
  old value → null  (first insert)
  change logged: search  null → true

setFlag("payment", "on"):
  parseFlag → true
  old value → false (was set earlier)
  change logged: payment  false → true
```

## 7. Gotchas & takeaways

> **`Boolean.parseBoolean("yes")` returns `false`, not `true`.** The standard library only treats the exact string `"true"` (case-insensitive) as `true`. Every other string — including `"yes"`, `"1"`, `"on"` — returns `false` without error. If your config format uses those values, write a custom parser.

> **Never compare to boolean literals with `==`: `if (flag == true)` should be `if (flag)`.** The `== true` adds no information and makes the condition look like it might mean something else. Return boolean expressions directly rather than wrapping them in `if (cond) return true; else return false;`.

- `true` and `false` are the only two boolean literals — they are lowercase keywords.
- There is no conversion between `int` and `boolean` in either direction.
- Return boolean expressions directly rather than wrapping in `if/else return true/false`.
- Use `if (flag)` and `if (!flag)` — never `if (flag == true)` or `if (flag == false)`.
- `Boolean` (boxed) can be `null`; use `Boolean.TRUE.equals(b)` for null-safe testing.
- `Boolean.parseBoolean` only treats `"true"` (case-insensitive) as `true` — everything else is `false`.
