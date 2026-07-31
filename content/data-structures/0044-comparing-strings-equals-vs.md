---
card: data-structures
gi: 44
slug: comparing-strings-equals-vs
title: Comparing strings (equals vs ==)
---

## 1. What it is

`==` on `String` variables compares **references** — whether both variables point at the exact same object in memory. `.equals()` compares **content** — whether both strings contain the same sequence of characters, regardless of whether they are the same object. For strings, these two questions usually have different answers, which is why using `==` for content comparison is one of the most common Java mistakes.

## 2. Why & when

Always use `.equals()` (or `.equalsIgnoreCase()` for case-insensitive comparison) when you want to know if two strings "say the same thing." `==` is only correct when you specifically want to know if two references point at the identical object — a rare, deliberate check, not the default choice for comparing string values.

## 3. Core concept

**Why `==` seems to "work" for literals — the string pool.** As covered in [String pool & interning](0034-string-pool-interning.md), identical string literals are automatically pooled to share one object, so `"hi" == "hi"` happens to be `true`. This creates a false sense that `==` is safe for strings, which breaks the moment a string is built at runtime (concatenation, user input, `substring`, `new String(...)`).

**`.equals()` is defined to compare content, character by character.** `String` overrides `Object.equals()` (following the [equals() & hashCode() contract](0014-equals-hashcode-contract.md)) to check that both objects are `String`s of the same length with identical characters at every position — this is always the correct semantic for "are these two strings the same text?"

**`compareTo()` for ordering, not just equality.** `s1.compareTo(s2)` returns a negative number, zero, or a positive number, based on lexicographic (dictionary) order — useful for sorting strings, not just testing equality. `s1.compareTo(s2) == 0` is equivalent to `s1.equals(s2)` for `String`.

**Null-safety: `.equals()` can throw; helper methods avoid it.** Calling `s.equals(other)` throws `NullPointerException` if `s` itself is `null`. `Objects.equals(s, other)` handles `null` on either side safely, returning `true` only if both are `null` or both are equal by content — this is the safer default in code where either value might legitimately be `null`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two String variables built differently, comparing identically by equals() but differently by ==">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">a = "cat"; b = new String("cat");</text>
    <rect x="80" y="30" width="60" height="26" fill="#161b22" stroke="#79c0ff"/><text x="110" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">a</text>
    <rect x="180" y="30" width="60" height="26" fill="#161b22" stroke="#f0883e"/><text x="210" y="47" fill="#e6edf3" text-anchor="middle" font-size="10">b</text>
    <rect x="60" y="80" width="80" height="26" fill="#0d1117" stroke="#3fb950"/><text x="100" y="97" fill="#e6edf3" text-anchor="middle" font-size="10">"cat" (pooled)</text>
    <rect x="180" y="80" width="80" height="26" fill="none" stroke="#f0883e"/><text x="220" y="97" fill="#e6edf3" text-anchor="middle" font-size="10">"cat" (own copy)</text>
    <text x="320" y="140" fill="#79c0ff" text-anchor="middle">a == b -&gt; false (different objects); a.equals(b) -&gt; true (same content)</text>
  </g>
</svg>

`a` and `b` hold equal content but are different objects — `==` says "no," `.equals()` correctly says "yes."

## 5. Runnable example

```java
// ComparingStringsEqualsVs.java
import java.util.Objects;

public class ComparingStringsEqualsVs {

    // Basic: == compares references, .equals() compares content.
    static void basicLevel() {
        String a = "cat";
        String b = new String("cat");
        System.out.println("basic: a == b -> " + (a == b));           // false: different objects
        System.out.println("basic: a.equals(b) -> " + a.equals(b));    // true: same content
    }

    // Intermediate: a string built at runtime never automatically matches == against a literal.
    static void intermediateLevel() {
        String literal = "dog";
        String built = "d" + "o" + "g"; // compile-time constant folding may pool this -- but a runtime-variable version won't
        String suffix = "og";
        String runtimeBuilt = "d" + suffix; // built using a variable -- NOT folded at compile time, NOT pooled

        System.out.println("intermediate: literal == built (compile-time constant) -> " + (literal == built));
        System.out.println("intermediate: literal == runtimeBuilt (built at runtime) -> " + (literal == runtimeBuilt));
        System.out.println("intermediate: literal.equals(runtimeBuilt) -> " + literal.equals(runtimeBuilt)); // always true
    }

    // Advanced: compareTo() for ordering, and Objects.equals() for null-safe comparison.
    static void advancedLevel() {
        String s1 = "apple", s2 = "banana";
        System.out.println("advanced: \"apple\".compareTo(\"banana\") -> " + s1.compareTo(s2)); // negative: apple < banana

        String maybeNull = null;
        // maybeNull.equals("x") would throw NullPointerException here
        System.out.println("advanced: Objects.equals(null, \"x\") -> " + Objects.equals(maybeNull, "x")); // false, no exception
        System.out.println("advanced: Objects.equals(null, null) -> " + Objects.equals(null, null));       // true
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ComparingStringsEqualsVs.java`, then run `java ComparingStringsEqualsVs.java`.

## 6. Walkthrough

1. `basicLevel()` compares `a` (a pooled literal) and `b` (explicitly `new String("cat")`). `a == b` is `false`, since `b` is a deliberately separate object; `a.equals(b)` is `true`, since both hold the identical character sequence `"cat"`.
2. `intermediateLevel()` shows a subtlety: `built = "d" + "o" + "g"` is entirely made of compile-time constants, so the compiler can fold it into the literal `"dog"` and pool it — `literal == built` may print `true`. But `runtimeBuilt = "d" + suffix`, where `suffix` is a variable, cannot be folded at compile time, so it is built fresh at runtime — `literal == runtimeBuilt` prints `false`.
3. Regardless of how `runtimeBuilt` was constructed, `literal.equals(runtimeBuilt)` reliably prints `true`, because `.equals()` never depends on how or when the string was built — only its actual character content.
4. `advancedLevel()`'s `s1.compareTo(s2)` returns a negative number, since `"apple"` sorts before `"banana"` lexicographically — this is the method to use for sorting strings, not just testing equality.
5. `Objects.equals(maybeNull, "x")` safely returns `false` without throwing, even though `maybeNull` is `null` — calling `maybeNull.equals("x")` directly would have thrown `NullPointerException` instead.

## 7. Gotchas & takeaways

> Gotcha: whether `==` "happens to work" for two string expressions depends on compiler constant-folding and pooling details that are easy to get wrong by eye — the reliable rule is simply: never use `==` to compare string *content*. Use `.equals()` always, and `Objects.equals()` when either side might be `null`.

- `==` on strings compares object identity; `.equals()` compares character content — always prefer `.equals()` for value comparison.
- Compile-time constant expressions can be pooled and make `==` "accidentally" true; anything built from a variable at runtime cannot rely on this.
- `compareTo()` gives lexicographic ordering, useful for sorting; `Objects.equals()` gives null-safe equality checking.
- Related concepts: [String pool & interning](0034-string-pool-interning.md), [equals() & hashCode() contract](0014-equals-hashcode-contract.md).
