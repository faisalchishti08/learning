---
card: java
gi: 965
slug: instanceof-pattern-binding
title: instanceof pattern binding
---

## 1. What it is

Pattern matching for `instanceof`, standardized in Java 16, extends the classic `instanceof` type check with the ability to declare and bind a variable in the same expression: `if (obj instanceof String s)` checks whether `obj` is a `String` *and*, if true, binds `s` as a new local variable of type `String`, already correctly cast — usable directly inside (and, thanks to flow-scoping, sometimes even after) that `if` block, with no separate, manual cast statement needed. Before this feature, the idiomatic pattern was always two steps: `if (obj instanceof String) { String s = (String) obj; ... }` — a type check, followed by a necessarily-redundant explicit cast that could only ever succeed, since the `instanceof` check just confirmed it would.

## 2. Why & when

This feature exists to eliminate an extremely common, purely mechanical piece of redundancy: once you've already confirmed an object's type via `instanceof`, requiring a separate cast to actually use it as that type added no safety (the cast could never fail, having just been checked) and only added boilerplate and an opportunity for the checked type and the cast type to accidentally drift out of sync during a later edit. It's useful anywhere you branch behavior based on an object's runtime type — implementing `equals(Object)` (`if (obj instanceof Point p) { return this.x == p.x && this.y == p.y; }`), handling a heterogeneous collection, or, most powerfully, as the foundation `switch` type patterns and record patterns are built directly on top of (both are, structurally, `instanceof` pattern matching extended to a multi-branch and destructuring context respectively). It's also worth understanding the pattern variable's scoping rules precisely, since Java's flow-sensitive scoping is more permissive than a beginner might expect: the bound variable (`s`, in the example above) is in scope not just inside the `if` block, but in any code path the compiler can prove is only reachable when the pattern matched — including, notably, after an `if` whose *negated* condition returns or throws.

## 3. Core concept

```
Object obj = "hello";

// BEFORE (two steps, redundant cast):
if (obj instanceof String) {
    String s = (String) obj;   // this cast can NEVER actually fail here -- pure redundancy
    System.out.println(s.length());
}

// AFTER (pattern binding -- one step):
if (obj instanceof String s) {   // s is bound HERE, already correctly typed
    System.out.println(s.length());
}

// FLOW-SCOPING: the pattern variable can be usable even AFTER the if block,
// when the compiler can prove the ONLY way past this point is if the match succeeded:
void process(Object obj) {
    if (!(obj instanceof String s)) {
        return;   // if we get past this line, the match MUST have succeeded
    }
    System.out.println(s.length()); // 's' is STILL in scope here -- flow-sensitive
}
```

The compiler's flow analysis, not just simple lexical block nesting, determines exactly where a pattern-bound variable is considered definitely assigned and safe to use — this is a meaningfully more flexible scoping rule than an ordinary local variable declaration gets.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A negated instanceof check that returns early, after which the pattern variable remains in scope because the compiler can prove the match must have succeeded to reach that point" >
  <rect x="20" y="30" width="280" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="50" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">if (!(obj instanceof String s)) return;</text>
  <text x="160" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">if match FAILS -&gt; return early, s never used</text>

  <rect x="340" y="30" width="280" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">println(s.length());</text>
  <text x="480" y="63" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">reachable ONLY if match succeeded -- s is IN SCOPE</text>

  <line x1="300" y1="50" x2="340" y2="50" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="320" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Flow-sensitive scoping: the compiler proves this line is unreachable unless s was bound</text>
</svg>

*Flow-sensitive scoping lets a pattern variable remain usable after a negated check that returns, since reaching that point proves the match succeeded.*

## 5. Runnable example

Scenario: build a small heterogeneous data formatter relying on `instanceof` pattern binding, evolving from a basic single-check version, to a realistic chain of checks across several types, to a more advanced case exploiting flow-sensitive scoping to keep code flat rather than deeply nested.

### Level 1 — Basic

```java
public class InstanceofPatternBasic {
    static String describe(Object obj) {
        if (obj instanceof String s) {
            return "a String of length " + s.length();
        }
        if (obj instanceof Integer i) {
            return "an Integer" + (i % 2 == 0 ? " (even)" : " (odd)");
        }
        return "something else: " + obj;
    }

    public static void main(String[] args) {
        System.out.println(describe("hello"));
        System.out.println(describe(42));
        System.out.println(describe(3.14));
    }
}
```

**How to run:** `java InstanceofPatternBasic.java` (JDK 17+).

Expected output:
```
a String of length 5
an Integer (even)
something else: 3.14
```

Each `instanceof` check both confirms the type and binds a correctly-typed variable (`s`, `i`) directly, with no separate cast statement — `s.length()` and `i % 2` are used immediately, exactly as if `s` and `i` had been declared and cast the old, two-step way, but with less code and no risk of the check and cast types drifting apart.

### Level 2 — Intermediate

```java
import java.util.*;

public class InstanceofPatternChained {
    static double sizeOf(Object obj) {
        if (obj instanceof String s) {
            return s.length();
        } else if (obj instanceof Collection<?> c) {
            return c.size();
        } else if (obj instanceof Map<?, ?> m) {
            return m.size();
        } else if (obj instanceof int[] arr) {
            return arr.length;
        }
        return -1;
    }

    public static void main(String[] args) {
        System.out.println(sizeOf("hello world"));
        System.out.println(sizeOf(List.of(1, 2, 3, 4)));
        System.out.println(sizeOf(Map.of("a", 1, "b", 2)));
        System.out.println(sizeOf(new int[]{1, 2, 3, 4, 5}));
    }
}
```

**How to run:** `java InstanceofPatternChained.java` (JDK 17+).

Expected output:
```
11.0
4.0
2.0
5.0
```

The real-world concern added: chaining several `instanceof` pattern checks across genuinely different, unrelated types (`String`, `Collection`, `Map`, an array) into one `if`/`else if` sequence is a common, practical shape for "figure out what kind of thing this is, and act accordingly" logic — each branch's pattern variable (`s`, `c`, `m`, `arr`) is scoped only to its own branch, with no ambiguity or overlap between them.

### Level 3 — Advanced

```java
public class InstanceofPatternFlowScoping {
    sealed interface Event permits ClickEvent, KeyEvent {}
    record ClickEvent(int x, int y) implements Event {}
    record KeyEvent(char key) implements Event {}

    static String process(Object obj) {
        // Guard clauses using NEGATED instanceof checks -- keeps the method body FLAT
        // rather than deeply nested, while still safely using the bound variable afterward.
        if (!(obj instanceof Event event)) {
            return "not an event: " + obj;
        }
        if (!(event instanceof ClickEvent click)) {
            return "non-click event: " + event;
        }
        // 'click' is STILL in scope here, even though we're past TWO separate
        // negated-and-returned checks -- flow analysis proves it must be bound.
        return "click at (" + click.x() + ", " + click.y() + ")";
    }

    public static void main(String[] args) {
        System.out.println(process("hello"));
        System.out.println(process(new KeyEvent('A')));
        System.out.println(process(new ClickEvent(10, 20)));
    }
}
```

**How to run:** `java InstanceofPatternFlowScoping.java` (JDK 17+).

Expected output:
```
not an event: hello
non-click event: KeyEvent[key=A]
click at (10, 20)
```

The production-flavored hard case: two separate guard-clause-style negated `instanceof` checks, each returning early on failure, keep `process`'s body entirely flat (no nested `if`/`else` blocks) — and the pattern variable `click`, bound by the *second* guard clause, remains correctly in scope for the final `return` statement, because the compiler's flow analysis proves that reaching that line is only possible if both preceding checks succeeded (meaning `obj` genuinely is a `ClickEvent`), letting this idiomatic "guard clauses first, main logic flat at the end" style work naturally with pattern-bound variables.

## 6. Walkthrough

Tracing `process(new ClickEvent(10, 20))` end to end from `InstanceofPatternFlowScoping.main`:

1. `obj` is bound to a `ClickEvent` instance, statically typed as `Object` at the parameter — the first guard clause, `if (!(obj instanceof Event event))`, checks whether `obj` is *not* an `Event`; since a `ClickEvent` does implement the sealed `Event` interface, this negated check evaluates to `false`, so the early `return` inside this `if` block does *not* execute, and the pattern variable `event` — bound because the underlying, non-negated `instanceof` check succeeded — is now in scope for the rest of the method.
2. The second guard clause, `if (!(event instanceof ClickEvent click))`, checks whether `event` (now known, from the first check, to be some kind of `Event`) is *not* specifically a `ClickEvent`; since it genuinely is a `ClickEvent`, this negated check also evaluates to `false`, so its `return` also does not execute, and the pattern variable `click` becomes available.
3. Execution reaches the final `return` statement — at this exact point in the code, the compiler's flow analysis has proven, through the two preceding guard clauses, that the only way to reach this line at all is if `obj instanceof Event event` succeeded *and* `event instanceof ClickEvent click` succeeded, meaning `click` is guaranteed to be definitely assigned and correctly typed as `ClickEvent`, with no explicit cast or re-check needed.
4. `click.x()` and `click.y()` are called, returning `10` and `20` respectively (the record's auto-generated accessors), and the final string `"click at (10, 20)"` is constructed and returned.
5. Contrast this with `process(new KeyEvent('A'))`: the first guard clause's negated check still evaluates to `false` (a `KeyEvent` is an `Event`), so `event` becomes available bound to the `KeyEvent` instance — but the second guard clause's negated check, `!(event instanceof ClickEvent click)`, evaluates to `true` this time (since a `KeyEvent` is not a `ClickEvent`), so its `return "non-click event: " + event;` executes immediately, and the method exits here, with `click` never having been bound or used at all.
6. This demonstrates the complete practical value of flow-sensitive scoping: guard clauses can be stacked one after another, each narrowing what's known about the object's type, with each check's bound pattern variable becoming safely usable in exactly the code that's provably reachable only after that specific check has succeeded — producing flat, linear, easy-to-read code instead of a deeply nested pyramid of `if`/`else` blocks.

## 7. Gotchas & takeaways

> **Gotcha:** a pattern-bound variable from an `instanceof` check inside an `&&` expression is available in the expression's right-hand side (since Java's `&&` short-circuits and only evaluates the right side if the left side was true) — `if (obj instanceof String s && s.length() > 5)` works correctly and is idiomatic — but the same variable is *not* available on the right-hand side of `||`, since `||` only evaluates its right side when the left side is *false*, meaning the pattern match on the left necessarily failed; relying on a pattern variable's scope inside an `||`'s right operand is a compile error, not a subtle runtime bug, but it's worth knowing the rule rather than being surprised by it.

- `instanceof` pattern binding checks an object's type and binds a correctly-typed local variable in one step, eliminating the redundant manual cast the classic two-step `instanceof`-then-cast idiom always required.
- The pattern variable's scope is determined by flow-sensitive analysis, not simple lexical block nesting — it can remain usable after a negated check that returns or throws, since the compiler can prove the only way past that point is if the match succeeded.
- This makes guard-clause-style code (several early-return checks followed by flat main logic) work naturally with pattern-bound variables, avoiding deeply nested `if`/`else` pyramids.
- A pattern variable from the left side of `&&` is available on the right side (since `&&` only evaluates the right side after the left succeeds); the same is not true for `||`, where the left side having failed is precisely what makes the right side evaluate at all.
- This feature is the direct foundation `switch` type patterns and record patterns build on — understanding `instanceof` pattern binding's scoping rules carries over directly to those more advanced forms.
- See [switch type patterns](0966-switch-type-patterns.md) for the multi-branch extension of this same mechanism, and [record patterns / deconstruction](0960-record-patterns-deconstruction.md) for combining pattern binding with automatic record destructuring.
