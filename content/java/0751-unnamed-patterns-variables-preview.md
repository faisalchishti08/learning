---
card: java
gi: 751
slug: unnamed-patterns-variables-preview
title: Unnamed patterns & variables (preview)
---

## 1. What it is

**Java 21** (JEP 443) previews the **underscore (`_`)** as an "unnamed" stand-in: it can be written in place of a local variable, a lambda or `catch` parameter, or one component inside a [record pattern](0740-record-patterns-standardized.md), whenever the value itself is required (by the language's syntax or a method signature) but never actually used. `_` isn't a real identifier — you can write `_` multiple times in the same scope without a "variable already defined" error, because each `_` is unnamed and unrelated to any other `_`. Being a preview feature, it requires `--enable-preview` to compile and run.

## 2. Why & when

Java's syntax sometimes forces you to name something you don't care about. A `catch (IOException e)` block that doesn't use `e` still needs a name for it; a record pattern like `Point(int x, int y)` used purely to check "is this a `Point`" still has to name both `x` and `y` even if neither is read; a `for (var ignored : list)` loop that just needs to iterate a certain number of times still needs a loop variable name. Every one of these unused names is a small tax: a name the reader has to notice, register as "not actually used," and then discount — and an unused-variable warning some tools flag, cluttering signal with noise. `_` removes that tax by making "I don't need this value" an explicit, first-class thing to write, rather than an implicitly-unused name the reader has to infer. This becomes especially valuable combined with record patterns, where a nested pattern might destructure five fields but the calling code only actually needs two of them — `_` marks the other three as deliberately discarded, right at the point where the reader would otherwise wonder why they're unused.

## 3. Core concept

```java
record Point(int x, int y) {}
record Rectangle(Point topLeft, Point bottomRight) {}

static boolean isAtOrigin(Object shape) {
    // only topLeft's coordinates matter here; bottomRight is irrelevant to this check
    if (shape instanceof Rectangle(Point(int x, int y), _)) {
        return x == 0 && y == 0;
    }
    return false;
}
```

The second `Point` component of `Rectangle` is matched but never bound to a name — `_` signals "this component must be here structurally, but this code has no use for its value."

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unnamed variable marks a value the language requires syntactically but the code never reads, distinguishing deliberate discard from an unused name">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">catch (NumberFormatException _) { return -1; }</text>

  <rect x="20" y="90" width="280" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="160" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">named but unused: reader must verify</text>

  <rect x="340" y="90" width="280" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="480" y="115" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">_ : explicitly, structurally unused</text>

  <text x="320" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">_ can appear more than once in the same scope with no conflict</text>
</svg>

*`_` turns "this name happens to be unused" into "this value is deliberately discarded."*

## 5. Runnable example

Scenario: validating a batch of coordinate pairs, growing from named-but-unused variables into full use of `_` across catch clauses, record patterns, and a loop.

### Level 1 — Basic

```java
public class UnnamedBasic {
    public static void main(String[] args) {
        String[] inputs = {"42", "oops", "17"};
        int validCount = 0;
        for (String input : inputs) {
            try {
                Integer.parseInt(input);
                validCount++;
            } catch (NumberFormatException e) { // `e` is never used
                System.out.println("skipping invalid input: " + input);
            }
        }
        System.out.println("valid count: " + validCount);
    }
}
```

**How to run:** `java UnnamedBasic.java` (JDK 21+, no preview flag needed for this version).

`e` is a name the reader has to check off as "not used" — the code only cares *that* parsing failed, never *why*, but the `catch` clause still forces a name onto the exception.

### Level 2 — Intermediate

```java
public class UnnamedCatch {
    public static void main(String[] args) {
        String[] inputs = {"42", "oops", "17"};
        int validCount = 0;
        for (String input : inputs) {
            try {
                Integer.parseInt(input);
                validCount++;
            } catch (NumberFormatException _) { // explicitly unused
                System.out.println("skipping invalid input: " + input);
            }
        }
        System.out.println("valid count: " + validCount);
    }
}
```

**How to run:** `java --enable-preview --source 21 UnnamedCatch.java`.

The real-world concern added: `_` replaces the unused `e`, making it immediately visible — without inspecting the block's body — that this `catch` clause never inspects the exception object itself, only the fact that one was thrown.

### Level 3 — Advanced

```java
public class UnnamedAdvanced {
    record Point(int x, int y) {}
    record Rectangle(Point topLeft, Point bottomRight) {}

    static boolean touchesOrigin(Object shape) {
        // only need topLeft's coordinates; bottomRight and its own
        // inner Point components are irrelevant to this specific check
        if (shape instanceof Rectangle(Point(var x, var y), _)) {
            return x == 0 || y == 0;
        }
        return false;
    }

    public static void main(String[] args) {
        Rectangle[] rects = {
            new Rectangle(new Point(0, 5), new Point(10, 15)),
            new Rectangle(new Point(3, 4), new Point(10, 15)),
        };

        int atEdgeCount = 0;
        for (Rectangle r : rects) {
            if (touchesOrigin(r)) {
                atEdgeCount++;
            }
        }

        // `_` as a loop variable: only the repeat count matters, not each element
        for (var _ : rects) {
            // (in real code this might trigger some fixed per-rectangle side effect
            // that doesn't depend on the rectangle's own fields)
        }

        System.out.println("rectangles touching an axis: " + atEdgeCount);
    }
}
```

**How to run:** `java --enable-preview --source 21 UnnamedAdvanced.java`.

This adds the production-flavored hard case: `_` used in **three different positions** — inside a nested record pattern (`Rectangle(Point(var x, var y), _)`, discarding the whole `bottomRight` component), and as an enhanced-`for` loop variable (`for (var _ : rects)`), demonstrating that unnamed variables work anywhere Java requires a bound name syntactically, not just in `catch` clauses.

## 6. Walkthrough

Tracing `UnnamedAdvanced.main`:

1. `main` builds an array of two `Rectangle`s: the first has `topLeft = Point(0, 5)` (x is 0, touching the origin's vertical axis), the second has `topLeft = Point(3, 4)` (neither coordinate is 0).
2. The loop calls `touchesOrigin(r)` for each. Inside, `shape instanceof Rectangle(Point(var x, var y), _)` is evaluated: this confirms `shape` is a `Rectangle`, destructures its `topLeft` component into `x` and `y`, and matches its `bottomRight` component against `_` — meaning "this component must exist for the pattern to match, but bind it to nothing."
3. For the first rectangle: `x = 0`, `y = 5`. The check `x == 0 || y == 0` is `true` (x is 0), so `touchesOrigin` returns `true`, and `atEdgeCount` increments to `1`.
4. For the second rectangle: `x = 3`, `y = 4`. Neither is `0`, so `touchesOrigin` returns `false`, and `atEdgeCount` stays at `1`.
5. The second loop, `for (var _ : rects)`, iterates twice (once per rectangle) purely for its side effects (none, in this simplified example) — the loop variable is never bound to a name, signaling to any reader that the loop body genuinely doesn't depend on each rectangle's own data, only on iterating the right number of times.
6. `main` prints the final count.

Expected output:
```
rectangles touching an axis: 1
```

## 7. Gotchas & takeaways

> **Gotcha:** `_` is **not** a normal identifier — you cannot read its value afterward (`_` used more than once in the same scope doesn't refer to "the last thing bound to `_`"; each occurrence is independent and none of them can be referenced later). Reaching for `_` when you might need the value later, even conditionally, means you'll need to go back and give it a real name — don't use `_` speculatively "just in case."

- Preview feature in Java 21 — requires `--enable-preview` at compile and run time.
- Legal wherever Java's syntax forces a name you don't need: `catch` clauses, lambda parameters, record pattern components, and loop variables.
- Multiple `_` in the same scope don't conflict with each other, because none of them is actually a named binding.
- Use `_` to make "this value is deliberately unused" visible at the point of declaration, rather than leaving a reader to infer it from an unused-variable warning or by reading the whole block.
- Pairs naturally with [record deconstruction patterns](0741-record-deconstruction-patterns.md), where a nested pattern may need to name only some of several destructured components.
