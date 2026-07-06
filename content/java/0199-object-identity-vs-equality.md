---
card: java
gi: 199
slug: object-identity-vs-equality
title: Object identity vs equality
---

## 1. What it is

**Identity** (checked with `==` for objects) asks "are these two references pointing at the exact same object in memory?" **Equality** (checked with `.equals()`) asks "do these two objects represent the same logical value?" — a question each class defines for itself by overriding `Object`'s default `equals()`, which otherwise just falls back to identity comparison. Two genuinely different objects can be "equal" in the meaningful sense while still failing an identity check, and this distinction is one of the most important in all of Java.

```java
String a = new String("hello");
String b = new String("hello");

System.out.println(a == b);        // false — two DIFFERENT String objects in memory
System.out.println(a.equals(b));   // true — but they represent the SAME text value
```

`a` and `b` are deliberately created as two separate `String` objects here (via `new String(...)`) — `==` correctly reports they are different objects, while `.equals()` correctly reports they hold the same sequence of characters, which is usually the comparison you actually want.

## 2. Why & when

This distinction exists because "sameness" genuinely means different things depending on context, and conflating the two is one of the most common bugs for programmers new to Java:

- **Identity (`==`) is appropriate for**: checking if a variable refers to a specific singleton or cached instance, checking `null`, or comparing enum constants (which are guaranteed to be singletons, so `==` is actually the idiomatic, correct way to compare them).
- **Equality (`.equals()`) is appropriate for**: comparing almost everything else — two `String`s, two custom objects representing the same logical entity (like two separate `Point` objects both meaning "the coordinate (3, 4)"), two boxed numbers, and so on.
- **The default `.equals()` (inherited from `Object`, if a class doesn't override it) is identical to `==`** — it only returns `true` for the exact same object, which is almost never the comparison you actually want for a custom class representing meaningful data, unless the class deliberately overrides `equals()` to compare field values instead (a later topic covers writing a correct `equals()` override).

You reach for `.equals()` by default whenever comparing objects for "do these represent the same value" — reserving `==` specifically for identity checks, `null` checks, and enum comparisons, where it is genuinely the right and idiomatic tool.

## 3. Core concept

```java
class Point {
    int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
    // no equals() override — inherits Object's default, which is identity-based
}

public class IdentityDemo {
    public static void main(String[] args) {
        Point p1 = new Point(3, 4);
        Point p2 = new Point(3, 4); // same coordinates, but a DIFFERENT object
        Point p3 = p1;               // p3 refers to the SAME object as p1

        System.out.println(p1 == p2);       // false — different objects
        System.out.println(p1.equals(p2));  // false too! Point never overrode equals(), so it falls back to ==
        System.out.println(p1 == p3);       // true — same object
        System.out.println(p1.equals(p3));  // true — same object, so identity-based equals() also returns true
    }
}
```

`p1.equals(p2)` returns `false` here specifically because `Point` never overrode `equals()` — without an override, `.equals()` behaves *identically* to `==`, which is why two `Point` objects representing the exact same logical coordinate (3, 4) still compare as "not equal," a common surprise until a proper `equals()` override is written.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two separate Point objects both holding coordinates 3 4 shown as distinct boxes in memory, with double equals comparing their addresses as false, and equals method without an override also falling back to false since no custom equals was written">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Point p1 = new Point(3,4);  Point p2 = new Point(3,4);</text>

  <rect x="80" y="45" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">p1 -&gt; Point(3,4)</text>
  <text x="150" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">object A</text>

  <rect x="380" y="45" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">p2 -&gt; Point(3,4)</text>
  <text x="450" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">object B (different!)</text>

  <text x="300" y="130" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">p1 == p2 -&gt; false        p1.equals(p2) -&gt; false (no override written)</text>
  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same logical coordinates, but two distinct objects — and no custom equals() to recognize that.</text>
</svg>

Without an `equals()` override, two objects representing the "same" logical value still compare as unequal.

## 5. Runnable example

Scenario: managing a small collection of user session tokens — starting with basic identity-vs-equality confusion using `String`, then extending to a custom class demonstrating the same pitfall, then hardening into a class with a correct `equals()` override making value-based comparison work as expected.

### Level 1 — Basic

```java
public class TokenBasic {
    public static void main(String[] args) {
        String token1 = new String("abc123");
        String token2 = new String("abc123");

        System.out.println("Same object? " + (token1 == token2));
        System.out.println("Same value? " + token1.equals(token2));
    }
}
```

**How to run:** `java TokenBasic.java`

`token1 == token2` is `false` (two distinct `String` objects, deliberately constructed with `new` to avoid Java's string pooling), while `token1.equals(token2)` is `true` — `String` *does* override `equals()` to compare character sequences, which is why this specific case correctly reports equality despite being different objects.

### Level 2 — Intermediate

Same idea, now with a custom `Session` class that, like the earlier `Point` example, has **not** overridden `equals()` — demonstrating the pitfall directly with user-defined data.

```java
public class TokenIntermediate {
    static class Session {
        String userId;
        Session(String userId) { this.userId = userId; }
        // no equals() override
    }

    public static void main(String[] args) {
        Session s1 = new Session("user-42");
        Session s2 = new Session("user-42"); // same logical user, different object

        System.out.println("Same object? " + (s1 == s2));
        System.out.println("Same value (equals)? " + s1.equals(s2)); // false! no override means identity-based
    }
}
```

**How to run:** `java TokenIntermediate.java`

`s1.equals(s2)` prints `false` even though both sessions represent the same `userId` — `Session` inherits `Object`'s default `equals()`, which is purely identity-based, so two logically-identical sessions are reported as "not equal" until an explicit `equals()` override is added.

### Level 3 — Advanced

Same `Session`, now with a correct `equals()` override (and the accompanying `hashCode()`, required to keep the two methods consistent, a rule enforced by convention and essential for correct behaviour in hash-based collections) comparing sessions by their logical `userId` value.

```java
import java.util.Objects;

public class TokenAdvanced {
    static class Session {
        String userId;
        Session(String userId) { this.userId = userId; }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;            // identity shortcut: definitely equal
            if (!(obj instanceof Session other)) return false; // different type, or null: not equal
            return Objects.equals(this.userId, other.userId); // compare the meaningful field
        }

        @Override
        public int hashCode() {
            return Objects.hash(userId); // MUST stay consistent with equals()
        }
    }

    public static void main(String[] args) {
        Session s1 = new Session("user-42");
        Session s2 = new Session("user-42");
        Session s3 = new Session("user-99");

        System.out.println("s1 == s2: " + (s1 == s2));           // false — still different objects
        System.out.println("s1.equals(s2): " + s1.equals(s2));   // true — now compares logical value
        System.out.println("s1.equals(s3): " + s1.equals(s3));   // false — genuinely different userId
    }
}
```

**How to run:** `java TokenAdvanced.java`

The overridden `equals()` first checks `this == obj` as a fast shortcut (if it's literally the same object, they're trivially equal), then checks the type with pattern-matching `instanceof`, then compares the actual `userId` fields using `Objects.equals` (which also safely handles either value being `null`) — this is the standard, idiomatic shape of a correct `equals()` override in Java.

## 6. Walkthrough

Trace `s1.equals(s2)` from `TokenAdvanced.main`, where `s1 = new Session("user-42")` and `s2 = new Session("user-42")`:

**Identity shortcut.** `this == obj` compares `s1`'s reference to `s2`'s reference — they're different objects, so this is `false`; execution continues to the next check rather than returning early.

**Type check.** `obj instanceof Session other` checks whether `obj` (which is `s2`, declared as `Object` inside the method signature) is actually a `Session` — it is, so this succeeds, and `other` is bound to `s2`, now typed as `Session`.

**Field comparison.** `Objects.equals(this.userId, other.userId)` compares `s1.userId` (`"user-42"`) against `s2.userId` (`"user-42"`) — `Objects.equals` internally calls `.equals()` on the first argument (here, delegating to `String.equals()`, which does character-by-character comparison), returning `true` since both strings hold identical text.

**Result.** The method returns `true` — `s1.equals(s2)` reports the two sessions as equal, correctly reflecting that they represent the same logical user, despite being two entirely separate objects in memory.

```
s1.equals(s2):
  this == obj?              s1 == s2 -> false (different objects)
  obj instanceof Session?   yes -> other = s2 (as Session)
  Objects.equals(userId, userId)?  "user-42".equals("user-42") -> true
  -> overall result: true
```

**Contrast with `s1.equals(s3)`.** Same process, but `Objects.equals("user-42", "user-99")` returns `false` (different text), so the overall result is `false` — correctly reflecting that `s1` and `s3` represent genuinely different users.

## 7. Gotchas & takeaways

> **The default `equals()`, inherited from `Object` when a class writes no override, is identical to `==` — purely identity-based.** This means every custom class you write starts out with "equals means same object," which is almost never what you actually want for classes meant to represent comparable values; forgetting to override `equals()` is one of the most common sources of "why does my collection say these two things aren't equal" bugs.

> **Whenever you override `equals()`, you must also override `hashCode()` consistently** (objects that are `.equals()` to each other must return the *same* `hashCode()`) — violating this contract causes subtle, hard-to-diagnose bugs in hash-based collections like `HashMap` and `HashSet`, where objects that are logically equal might end up treated as different entries.

- `==` compares object identity (same object in memory); `.equals()` compares logical equality, as defined by each class.
- Without an `equals()` override, a class's `.equals()` behaves exactly like `==` — purely identity-based.
- `String` and many standard library classes already override `equals()` to compare their actual content/value.
- Always override `hashCode()` alongside `equals()`, keeping both consistent, whenever you write a value-based `equals()` for a custom class.
