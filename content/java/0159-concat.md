---
card: java
gi: 159
slug: concat
title: concat()
---

## 1. What it is

`String.concat(String str)` returns a new string consisting of the calling string's characters followed by the argument string's characters — functionally similar to using `+` for two strings, but as an explicit method call rather than an operator, and restricted specifically to joining two `String`s together (no automatic conversion of non-`String` types, unlike `+`).

```java
String first = "Hello, ";
String second = "world!";
String combined = first.concat(second);

System.out.println(combined); // "Hello, world!"
System.out.println(first);    // "Hello, " — unchanged, per immutability
```

If the argument to `concat` is an empty string, the method returns the original string's content unchanged (though as a technical note, it may or may not be the exact same object, since `String` reserves the right to optimize this case) — there is no error or special behavior, just no visible effect.

## 2. Why & when

`concat` and `+` accomplish the same core task — joining two strings — and the choice between them is largely stylistic:

- **`+` is far more common in everyday code** because it reads naturally, handles automatic conversion of numbers/booleans, and chains cleanly across multiple values (`a + b + c`).
- **`concat` is occasionally preferred when you specifically want to signal "these two are strings being joined" without any implicit type conversion** — since `concat` only accepts a `String` argument, it can't silently absorb a non-string value the way `+` can.
- **`concat` throws a `NullPointerException` if its argument is `null`** — whereas `+` with a `null` operand produces the literal text `"null"` instead of throwing. This is an important, easy-to-miss difference: `str + null` never throws, but `str.concat(null)` always does.

In modern code, `+` (or `StringBuilder` for loops) is used far more often than `concat`; understanding `concat` mainly means understanding this `null`-handling difference and recognizing the method when it appears in existing code.

## 3. Core concept

```java
public class ConcatDemo {
    public static void main(String[] args) {
        String greeting = "Hello";
        String name = "Alice";

        String withPlus = greeting + ", " + name + "!";
        String withConcat = greeting.concat(", ").concat(name).concat("!");

        System.out.println(withPlus);   // "Hello, Alice!"
        System.out.println(withConcat); // "Hello, Alice!" — same result, different mechanism

        String nullName = null;
        System.out.println(greeting + ", " + nullName + "!"); // "Hello, null!" — + never throws
        // greeting.concat(nullName); // would throw NullPointerException immediately
    }
}
```

`withPlus` and `withConcat` produce identical output through two different mechanisms — but the commented-out final line demonstrates the crucial difference: `+` silently converts a `null` operand into the text `"null"`, while `concat` throws immediately if handed a `null` argument.

## 4. Diagram

<svg viewBox="0 0 700 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Concat versus plus diagram: joining Hello with a null value using the plus operator produces the string Hello null without error, while calling concat with a null argument throws a NullPointerException instead." >
  <rect x="8" y="8" width="684" height="124" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Joining "Hello" with a null value — two different outcomes</text>

  <rect x="60" y="45" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="180" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Hello" + null -&gt; "Hellonull"</text>

  <rect x="380" y="45" width="260" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="510" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">"Hello".concat(null) -&gt; throws!</text>

  <text x="350" y="105" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">"+" auto-converts null to the text "null" — concat() has no such conversion and throws immediately.</text>
</svg>

`+` never throws on a `null` operand; `concat` always throws if its argument is `null`.

## 5. Runnable example

Scenario: building a full name from a first and last name field — starting with basic concatenation of two known-good strings, then handling an optional middle name, then hardening the process against a genuinely `null` field, which behaves very differently depending on whether `+` or `concat` is used.

### Level 1 — Basic

```java
public class NameJoinBasic {
    public static void main(String[] args) {
        String firstName = "Alice";
        String lastName = "Smith";

        String fullName = firstName.concat(" ").concat(lastName);
        System.out.println(fullName); // "Alice Smith"
    }
}
```

**How to run:** `java NameJoinBasic.java`

`firstName.concat(" ")` joins `"Alice"` with a literal space, producing `"Alice "`; `.concat(lastName)` then joins that result with `"Smith"`, producing the final `"Alice Smith"` — each `concat` call returns a new string, chained just like the earlier `replace`/`trim` examples.

### Level 2 — Intermediate

Same name-joining, now including an **optional middle name** — using `+` here instead of `concat`, since we need conditional logic (an `if`/`else` choosing what to join) rather than a fixed chain of two-argument calls.

```java
public class NameJoinIntermediate {
    public static void main(String[] args) {
        String firstName = "Alice";
        String middleName = "Jane";
        String lastName = "Smith";

        String fullName;
        if (middleName.isEmpty()) {
            fullName = firstName + " " + lastName;
        } else {
            fullName = firstName + " " + middleName + " " + lastName;
        }

        System.out.println(fullName); // "Alice Jane Smith"
    }
}
```

**How to run:** `java NameJoinIntermediate.java`

`+` is used here rather than `concat` because the logic needs to build the final string across multiple pieces conditionally — `concat`'s fixed two-argument shape (one call joins exactly two strings) becomes awkward for chains built up conditionally, whereas `+` chains naturally across however many pieces a given branch needs.

### Level 3 — Advanced

Same name builder, now defensively handling a genuinely `null` middle name field — demonstrating why `+` is generally the safer default for joining potentially-`null` fields, and how to use `concat` correctly only once you've confirmed a value is non-`null`.

```java
public class NameJoinAdvanced {

    static String buildFullName(String firstName, String middleName, String lastName) {
        if (firstName == null || lastName == null) {
            throw new IllegalArgumentException("First and last name are required");
        }

        // "+" tolerates a null middleName gracefully during the check itself
        boolean hasMiddleName = middleName != null && !middleName.isEmpty();

        if (hasMiddleName) {
            return firstName.concat(" ").concat(middleName).concat(" ").concat(lastName); // safe: middleName confirmed non-null
        } else {
            return firstName.concat(" ").concat(lastName);
        }
    }

    public static void main(String[] args) {
        System.out.println(buildFullName("Alice", "Jane", "Smith"));
        System.out.println(buildFullName("Bob", null, "Jones"));
        System.out.println(buildFullName("Carol", "", "Lee"));
    }
}
```

**How to run:** `java NameJoinAdvanced.java`

`hasMiddleName` is computed with `middleName != null && !middleName.isEmpty()` — this check itself never calls `concat` on `middleName`, so it's safe even if `middleName` is `null` (the `&&` short-circuits before `.isEmpty()` would ever be called on a `null` reference). Only once `hasMiddleName` has confirmed `middleName` is both non-`null` and non-empty does the code call `.concat(middleName)` on it — using `concat` here is safe specifically because the `null` case has already been excluded by that point.

## 6. Walkthrough

Trace `buildFullName("Bob", null, "Jones")`:

**Guard clause.** `firstName` (`"Bob"`) and `lastName` (`"Jones"`) are both non-`null`, so the guard clause doesn't throw.

**Middle name check.** `middleName != null` is `false` (it genuinely is `null`) — because `&&` short-circuits, `middleName.isEmpty()` is never evaluated at all, avoiding what would otherwise be a `NullPointerException`. `hasMiddleName` is `false`.

**Building the name.** Since `hasMiddleName` is `false`, the `else` branch runs: `firstName.concat(" ").concat(lastName)` — `"Bob".concat(" ")` gives `"Bob "`, then `.concat("Jones")` gives `"Bob Jones"`. `middleName` (the actual `null` value) is never passed to `concat` anywhere in this branch, so no exception occurs.

```
buildFullName("Bob", null, "Jones"):
  guard: firstName, lastName non-null -> OK
  hasMiddleName: null != null? false -> short-circuit, isEmpty() never called -> hasMiddleName = false
  else branch: "Bob".concat(" ").concat("Jones") -> "Bob Jones"
```

**Final output.** The three calls print `"Alice Jane Smith"`, `"Bob Jones"` (as traced — the `null` middle name is correctly skipped, never touching `concat`), and `"Carol Lee"` (an empty, non-`null` middle name is also treated as "no middle name" by the `!middleName.isEmpty()` check).

## 7. Gotchas & takeaways

> **`concat(null)` throws a `NullPointerException` immediately — `+` with a `null` operand never throws, and instead produces the literal text `"null"`.** This is the single most important practical difference between the two; if a value might be `null`, either use `+` (accepting that it will print the word `"null"` if that value truly is `null`) or explicitly null-check before calling `concat` on it.

> **`concat` only accepts a `String` argument, with no automatic type conversion** — `str.concat(42)` does not compile, whereas `str + 42` works fine and converts the number to text automatically. This makes `concat` slightly more restrictive but also more explicit about exactly what's being joined.

- `concat` and `+` both join strings and both return a new string, leaving the originals unchanged.
- `+` is more flexible (handles automatic type conversion, chains cleanly, tolerates `null` by printing `"null"`) and is far more common in everyday code.
- `concat` throws immediately on a `null` argument — never call it on a value without first confirming it's non-`null`.
- Prefer `+` (or `StringBuilder` in loops) as the default; reach for `concat` mainly when reading or maintaining existing code that already uses it.
