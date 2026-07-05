---
card: java
gi: 152
slug: compareto-comparetoignorecase
title: compareTo() & compareToIgnoreCase()
---

## 1. What it is

`String.compareTo(String other)` compares two strings **lexicographically** (dictionary order, based on Unicode character values) and returns an `int`: negative if the calling string comes before `other`, zero if they're equal in content, and positive if it comes after. `compareToIgnoreCase` does the same comparison while ignoring letter case. Unlike `equals` (which only answers "same or not"), `compareTo` answers "which comes first?" — making it the basis for sorting strings.

```java
System.out.println("apple".compareTo("banana"));  // negative — "apple" comes before "banana"
System.out.println("banana".compareTo("apple"));  // positive — "banana" comes after "apple"
System.out.println("apple".compareTo("apple"));   // 0        — identical content
System.out.println("Apple".compareTo("apple"));   // negative — uppercase 'A' (65) sorts before lowercase 'a' (97)
System.out.println("Apple".compareToIgnoreCase("apple")); // 0 — case ignored
```

The exact magnitude of a nonzero result isn't generally meaningful beyond its sign (for `String`, it happens to often reflect a character-code difference, but code should only ever check whether the result is negative, zero, or positive).

## 2. Why & when

`compareTo` exists specifically to answer "which of these two strings sorts first," and is used whenever ordering — not just equality — matters:

- **Sorting** — `Collections.sort(list)` on a `List<String>` (or `Arrays.sort` on a `String[]`) uses each element's `compareTo` under the hood to decide the correct order.
- **Implementing `Comparable`** — any custom class wanting a natural sort order by some `String` field typically delegates to that field's `compareTo`.
- **Case-insensitive sorting** — `compareToIgnoreCase` (or, more flexibly, `String.CASE_INSENSITIVE_ORDER`) when a strict dictionary order shouldn't be affected by capitalization, such as sorting a list of names where "bob" and "Bob" should be treated as adjacent, not separated by every other uppercase-starting name.

Note that `compareTo == 0` and `.equals(...) == true` agree for `String` (both mean identical content) — but `compareTo` additionally tells you the *direction* of any difference, which `equals` alone never can.

## 3. Core concept

```java
import java.util.Arrays;

public class CompareToDemo {
    public static void main(String[] args) {
        String[] names = { "Charlie", "alice", "Bob", "dave" };

        Arrays.sort(names); // uses each String's compareTo internally
        System.out.println(Arrays.toString(names));
        // [Bob, Charlie, alice, dave] — uppercase letters sort before all lowercase ones

        Arrays.sort(names, String::compareToIgnoreCase); // case-insensitive order instead
        System.out.println(Arrays.toString(names));
        // [alice, Bob, Charlie, dave] — proper alphabetical order regardless of case
    }
}
```

The default `Arrays.sort(names)` uses `compareTo` directly, which sorts by raw character codes — since every uppercase letter has a lower code than every lowercase letter, all uppercase-starting words cluster before all lowercase-starting ones, producing an order that looks "wrong" to a human reader. Supplying `String::compareToIgnoreCase` as the comparator instead produces the alphabetical order most people actually expect.

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CompareTo diagram: comparing apple to banana returns a negative number since apple sorts first, comparing banana to apple returns a positive number since banana sorts second, and comparing apple to apple returns zero for identical content.">
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"apple".compareTo(...) — sign of the result tells you the ORDER</text>

  <rect x="60" y="45" width="150" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="135" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">compareTo("banana")</text>
  <text x="135" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">negative (apple &lt; banana)</text>

  <rect x="270" y="45" width="150" height="28" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="345" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">compareTo("apple")</text>
  <text x="345" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">zero (equal content)</text>

  <rect x="480" y="45" width="150" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="555" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">compareTo("aardvark")</text>
  <text x="555" y="88" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">positive (apple &gt; aardvark)</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Code should only ever check the SIGN (negative / zero / positive), never rely on the exact magnitude.</text>
</svg>

The sign of `compareTo`'s result — not its exact value — tells you whether the calling string sorts before, equal to, or after the argument.

## 5. Runnable example

Scenario: sorting a list of registered usernames for a directory listing — starting with a basic sort using natural `compareTo` order, then switching to case-insensitive sorting for a more human-friendly display, then hardening the comparison into a reusable, tie-breaking sort for a more realistic dataset with mixed case and duplicates differing only by case.

### Level 1 — Basic

```java
import java.util.Arrays;

public class UserSortBasic {
    public static void main(String[] args) {
        String[] usernames = { "zara", "Amir", "bob", "Diana" };

        Arrays.sort(usernames); // natural order: uses compareTo
        System.out.println(Arrays.toString(usernames));
    }
}
```

**How to run:** `java UserSortBasic.java`

`Arrays.sort` with no explicit comparator uses each `String`'s natural `compareTo` ordering — since uppercase letters have lower Unicode values than lowercase ones, this produces `[Amir, Diana, bob, zara]`, which groups both uppercase-starting names before both lowercase-starting ones, rather than true alphabetical order.

### Level 2 — Intermediate

Same username list, now sorted **case-insensitively** so the display order matches what a person would expect from a phone book or directory.

```java
import java.util.Arrays;

public class UserSortIntermediate {
    public static void main(String[] args) {
        String[] usernames = { "zara", "Amir", "bob", "Diana" };

        Arrays.sort(usernames, String::compareToIgnoreCase);
        System.out.println(Arrays.toString(usernames));
    }
}
```

**How to run:** `java UserSortIntermediate.java`

Passing `String::compareToIgnoreCase` as the comparator tells `Arrays.sort` to order elements by comparing them case-insensitively — this now correctly produces `[Amir, bob, Diana, zara]`, true alphabetical order, regardless of each name's original capitalization.

### Level 3 — Advanced

Same directory sort, now with a dataset that includes **two usernames differing only by case** (`"Bob"` and `"bob"`) — `compareToIgnoreCase` alone treats these as equal for sorting purposes, so their relative order becomes unpredictable; a proper tie-breaker uses the case-sensitive `compareTo` as a secondary comparison to make the sort fully deterministic.

```java
import java.util.Arrays;
import java.util.Comparator;

public class UserSortAdvanced {
    public static void main(String[] args) {
        String[] usernames = { "zara", "Bob", "Amir", "bob", "Diana" };

        Comparator<String> byNameThenCase =
            Comparator.<String>comparing(String::toLowerCase) // primary: alphabetical, ignoring case
                      .thenComparing(Comparator.naturalOrder()); // tie-breaker: exact compareTo, decides Bob vs bob

        Arrays.sort(usernames, byNameThenCase);
        System.out.println(Arrays.toString(usernames));
    }
}
```

**How to run:** `java UserSortAdvanced.java`

`Comparator.comparing(String::toLowerCase)` sorts primarily by each name's lowercase form, exactly like `compareToIgnoreCase` did in Level 2 — but two names that become identical once lowercased (`"Bob"` and `"bob"` both become `"bob"`) are then genuinely tied under that primary comparison. `.thenComparing(Comparator.naturalOrder())` supplies a deterministic tie-breaker, falling back to plain `compareTo` (which does distinguish case) only when the primary comparison reports a tie — this guarantees `"Bob"` and `"bob"` always land in the same relative order on every run, rather than depending on the sort algorithm's incidental behavior for equal elements.

## 6. Walkthrough

Trace how `byNameThenCase` orders `{ "Bob", "bob" }` specifically (the interesting pair from this dataset):

**Primary comparison.** `Comparator.comparing(String::toLowerCase)` converts both to `"bob"` and `"bob"` before comparing — `compareTo` between two identical strings returns `0`, a tie.

**Tie-breaker.** Since the primary comparison returned `0`, `.thenComparing(Comparator.naturalOrder())` runs next, comparing `"Bob".compareTo("bob")` directly (no lowercasing this time) — `'B'` (Unicode 66) is less than `'b'` (Unicode 98), so this returns a negative number, meaning `"Bob"` sorts before `"bob"`.

```
compare("Bob", "bob"):
  primary:  "bob".compareTo("bob") -> 0 (tie, both lowercase forms identical)
  tie-break: "Bob".compareTo("bob") -> negative ('B' < 'b') -> "Bob" sorts first
```

**Full sort result.** Applying `byNameThenCase` across the whole array `{ "zara", "Bob", "Amir", "bob", "Diana" }` produces `[Amir, Bob, bob, Diana, zara]` — alphabetically ordered overall (case-insensitively), with the `"Bob"`/`"bob"` tie broken deterministically by exact character comparison, placing the uppercase variant first.

## 7. Gotchas & takeaways

> **`compareTo`'s natural order sorts uppercase letters before all lowercase letters**, because it compares raw Unicode character values (`'A'` = 65 through `'Z'` = 90, then `'a'` = 97 through `'z'` = 122) — a list sorted with plain `compareTo` will look "wrong" to human readers whenever the data mixes cases, which is almost always. Use `compareToIgnoreCase` or a `Comparator` built on it for human-facing alphabetical order.

> **`compareToIgnoreCase` (or any comparator built purely on it) treats case variants of the same word as equal ties** — if your dataset can contain values differing only by case, and you need a fully deterministic, repeatable order, add a secondary tie-breaking comparison (as in Level 3) rather than leaving the relative order of ties up to the sort algorithm's incidental behavior.

- `compareTo` returns negative/zero/positive to indicate sort order, not just true/false equality like `.equals()` does.
- Only check the *sign* of a `compareTo` result, never its exact magnitude — the specific numeric value is not a documented, portable guarantee.
- Plain `compareTo` sorts by raw character codes, meaning all-uppercase-starting words cluster before all-lowercase-starting ones; use `compareToIgnoreCase` for human-friendly alphabetical order.
- When sorting data that might contain case-only duplicates, chain a case-sensitive tie-breaker after a case-insensitive primary comparison for a fully deterministic order.
