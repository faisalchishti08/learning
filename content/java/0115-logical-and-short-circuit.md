---
card: java
gi: 115
slug: logical-and-short-circuit
title: Logical AND && (short-circuit)
---

## 1. What it is

`&&` evaluates two `boolean` operands and produces `true` only if both are `true`. Its defining feature is **short-circuit evaluation**: if the left operand evaluates to `false`, Java never evaluates the right operand at all, because the overall result is already determined to be `false` regardless of what the right side would produce. This is different from the bitwise `&` operator (covered separately), which always evaluates both operands even when used on `boolean`s.

```java
boolean result = (5 > 10) && (10 / 0 > 0);   // left is false -> right is NEVER evaluated
System.out.println(result);                   // false, and no ArithmeticException is thrown

int callCount = 0;
boolean check(boolean value) { callCount++; return value; }
// (assume check is a static method for this snippet)
boolean r = check(false) && check(true);       // second check() call never happens
```

The right operand is only evaluated when the left operand is `true` — this is precisely what enables the common "guard, then use" idiom, where the left side checks that it is safe to evaluate the right side at all.

## 2. Why & when

Short-circuiting `&&` is essential, not just a performance optimization, whenever the right operand's evaluation depends on the left operand having already been true:

- Null-guard before dereferencing: `if (obj != null && obj.isValid())` — safely checks `isValid()` only when `obj` is known to be non-null; without short-circuiting, this would throw `NullPointerException` whenever `obj` was `null`.
- Bounds-check before indexing: `if (i < array.length && array[i] == target)` — avoids `ArrayIndexOutOfBoundsException` by ensuring `i` is in range before accessing `array[i]`.
- Avoiding expensive computation: `if (cachedResult != null && cachedResult.equals(expected))` avoids recomputing `expected` unnecessarily if it were expensive, though more commonly it avoids a `NullPointerException` from calling `.equals()` on a `null`.

## 3. Core concept

```java
public class LogicalAndDemo {

    static boolean loggedCheck(String label, boolean value) {
        System.out.println("  evaluating: " + label);
        return value;
    }

    public static void main(String[] args) {
        System.out.println("Case 1: left is false");
        boolean r1 = loggedCheck("left", false) && loggedCheck("right", true);
        System.out.println("Result: " + r1);   // false; "right" never printed

        System.out.println("Case 2: left is true");
        boolean r2 = loggedCheck("left", true) && loggedCheck("right", false);
        System.out.println("Result: " + r2);    // false; but "right" WAS printed this time

        // The essential null-guard pattern
        String data = null;
        if (data != null && data.length() > 0) {
            System.out.println("Has data: " + data);
        } else {
            System.out.println("No data (safely checked, no NullPointerException)");
        }

        // Array bounds guard
        int[] arr = { 10, 20, 30 };
        int i = 5;   // out of bounds
        if (i < arr.length && arr[i] == 99) {
            System.out.println("Found");
        } else {
            System.out.println("Safely skipped out-of-bounds access");
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Short-circuit AND diagram: when the left operand is false, the right operand box is grayed out and never evaluated, skipping straight to a false result. When the left operand is true, the right operand is evaluated and determines the final result.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">left && right — right is only evaluated if left is true</text>

  <text x="170" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">left = false</text>
  <rect x="30" y="56" width="100" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="77" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">left: false</text>
  <text x="150" y="77" fill="#8b949e" font-size="14" text-anchor="middle">→</text>
  <rect x="170" y="56" width="120" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="230" y="77" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">right: SKIPPED</text>
  <text x="170" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Result: false — right never runs.</text>

  <text x="530" y="46" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">left = true</text>
  <rect x="410" y="56" width="100" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="77" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">left: true</text>
  <text x="520" y="77" fill="#8b949e" font-size="14" text-anchor="middle">→</text>
  <rect x="540" y="56" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="77" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">right: evaluated</text>
  <text x="530" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Result: whatever right evaluates to.</text>
</svg>

The right operand of `&&` is only ever evaluated after the left operand has already proven to be `true`.

## 5. Runnable example

Scenario: a linked-list-style traversal that safely checks a node and its children before dereferencing them — the canonical use case for short-circuit `&&` guarding against `NullPointerException`.

### Level 1 — Basic

```java
public class GuardBasic {

    static class Node {
        int value;
        Node next;
        Node(int value, Node next) { this.value = value; this.next = next; }
    }

    public static void main(String[] args) {
        Node head = new Node(1, new Node(2, null));  // second node has no "next"

        Node current = head;
        // Safe traversal: check current != null before dereferencing current.next
        while (current != null && current.value != 0) {
            System.out.println("Visiting: " + current.value);
            current = current.next;
        }
        System.out.println("Reached the end safely.");
    }
}
```

**How to run:** `java GuardBasic.java`

`current != null && current.value != 0` relies on short-circuiting: the moment `current` becomes `null` (after visiting the last node), the left operand is `false`, so `current.value` is never evaluated — if `&&` did *not* short-circuit, this would throw `NullPointerException` trying to read `.value` on a `null` reference.

### Level 2 — Intermediate

Same traversal, now searching for a target value while also checking a "skip flag" on each node — showing how multiple `&&`-chained guards compose left to right, each protecting the next.

```java
public class GuardIntermediate {

    static class Node {
        int value;
        boolean skip;
        Node next;
        Node(int value, boolean skip, Node next) { this.value = value; this.skip = skip; this.next = next; }
    }

    static boolean containsActive(Node head, int target) {
        Node current = head;
        while (current != null) {
            // Chain of guards: check not-skipped AND matches target, each short-circuiting the next
            if (!current.skip && current.value == target) {
                return true;
            }
            current = current.next;
        }
        return false;
    }

    public static void main(String[] args) {
        Node list = new Node(1, false,
                     new Node(2, true,     // this one is "skipped" (soft-deleted)
                     new Node(3, false, null)));

        System.out.println("Contains active 2: " + containsActive(list, 2));  // false — skipped
        System.out.println("Contains active 3: " + containsActive(list, 3));  // true
        System.out.println("Contains active 99: " + containsActive(list, 99)); // false — not found, loop ends via current==null guard
    }
}
```

**How to run:** `java GuardIntermediate.java`

`!current.skip && current.value == target` evaluates `!current.skip` first; if the node is marked skipped, the whole expression short-circuits to `false` without even checking `current.value == target` — a minor efficiency gain here, but the pattern generalizes to cases where the second check would be invalid or expensive if the first check fails. The outer `while (current != null)` loop guard is itself the same defensive pattern from Level 1, now composed with the inner business-logic check.

### Level 3 — Advanced

Same list, now performing a deep validation that chains several guards where each one truly depends on the previous one having succeeded — validating a node, then its child, then a property of that child — demonstrating why reordering the conditions would break correctness, not just efficiency.

```java
public class GuardAdvanced {

    static class Config {
        String name;
        Settings settings;
        Config(String name, Settings settings) { this.name = name; this.settings = settings; }
    }

    static class Settings {
        Map<String, String> options;
        Settings(Map<String, String> options) { this.options = options; }
    }

    static java.util.Map<String, String> emptyMap() { return java.util.Map.of(); }

    static boolean isDebugModeEnabled(Config config) {
        // Each && guard is REQUIRED before the next expression is safe to evaluate:
        // 1. config itself might be null
        // 2. config.settings might be null even if config is not
        // 3. config.settings.options might be null (defensive, even though we control Settings' constructor)
        // 4. only if all prior checks pass is it safe to call options.get(...) and compare
        return config != null
            && config.settings != null
            && config.settings.options != null
            && "true".equals(config.settings.options.get("debug"));
    }

    public static void main(String[] args) {
        Config fullyConfigured = new Config("app", new Settings(java.util.Map.of("debug", "true")));
        Config noSettings = new Config("app2", null);
        Config nullConfig = null;

        System.out.println("Fully configured: " + isDebugModeEnabled(fullyConfigured));  // true
        System.out.println("No settings:      " + isDebugModeEnabled(noSettings));        // false, safely
        System.out.println("Null config:      " + isDebugModeEnabled(nullConfig));         // false, safely
    }
}
```

**How to run:** `java GuardAdvanced.java`

Each `&&` link in `isDebugModeEnabled` is not just a style choice — reordering them (say, checking `config.settings.options != null` before `config.settings != null`) would throw `NullPointerException` whenever `config.settings` actually was `null`, because you cannot access a field (`.options`) on a `null` reference. The chain is deliberately ordered from "least specific, most likely to be null" to "most specific, only safe to check once everything before it is confirmed non-null" — this mirrors exactly how a defensive null-check chain must be written in real code, and `"true".equals(...)` (calling `.equals()` on the string literal rather than on the possibly-null map value) additionally avoids a `NullPointerException` if `options.get("debug")` itself returns `null` (i.e., the key was absent).

## 6. Walkthrough

Trace `isDebugModeEnabled(noSettings)` where `noSettings = new Config("app2", null)`:

**First guard: `config != null`.** `config` is `noSettings`, a non-null `Config` object, so this evaluates to `true`. Because `&&` only short-circuits on `false`, evaluation proceeds to the next operand.

**Second guard: `config.settings != null`.** `config.settings` is `null` (as constructed). This evaluates to `false`.

**Short-circuit triggers.** Because the second operand of the `&&` chain evaluated to `false`, Java does not evaluate the *third* guard (`config.settings.options != null`) at all — doing so would have thrown `NullPointerException`, since `config.settings` is `null` and you cannot access `.options` on it. The short-circuit protects exactly this line from ever running.

**Final result.** The entire chained expression evaluates to `false` immediately at the point the first `false` operand was found, without touching the remaining two conditions.

```
config != null?              true  -> continue
config.settings != null?     false -> STOP, short-circuit here
config.settings.options...   never evaluated (would have NPE'd)
"true".equals(...)           never evaluated

overall result: false
```

**Final output.** The program prints `true` for the fully configured object (all four guards pass in sequence, and the final `.equals()` check confirms the `"debug"` option is `"true"`), then `false` for both the incompletely configured and the entirely `null` config — both without ever throwing an exception, thanks to the short-circuiting chain stopping exactly where it is no longer safe to proceed.

## 7. Gotchas & takeaways

> **`&&` only evaluates its right operand if the left operand is `true`.** This is not just a performance detail — code frequently *depends* on this behavior for correctness, using the left operand as a guard that makes the right operand safe to evaluate (e.g., a null check, a bounds check).

> **The order of operands in a `&&` chain matters when later operands depend on earlier ones having passed.** `a.field != null && a.field.method()` is safe; `a.field.method() != null && a.field != null` is not — reordering can reintroduce the exact bug the guard was meant to prevent.

- `&&` short-circuits: if the left operand is `false`, the right operand is never evaluated at all.
- This enables the standard "guard, then use" idiom for avoiding `NullPointerException` and `ArrayIndexOutOfBoundsException`.
- Chain guards from least-specific/most-likely-null to most-specific/dependent, mirroring the actual dependency between the checks.
- Contrast with the non-short-circuiting bitwise `&`, which always evaluates both operands even on `boolean` values — using `&` where a guard is needed reintroduces the exception the guard was meant to prevent.
