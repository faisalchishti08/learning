---
card: java
gi: 148
slug: charat-int
title: charAt(int)
---

## 1. What it is

`String.charAt(int index)` returns the single `char` located at the given zero-based position in the string. Valid indices range from `0` (the first character) to `length() - 1` (the last character); passing an index outside that range — negative, or equal to/greater than `length()` — throws a `StringIndexOutOfBoundsException` immediately.

```java
String word = "hello";
char first = word.charAt(0); // 'h'
char last = word.charAt(word.length() - 1); // 'o'
// char bad = word.charAt(5); // would throw StringIndexOutOfBoundsException — valid indices are 0..4
```

`charAt` gives direct, constant-time access to any single character, which is the building block for nearly all manual character-by-character string processing.

## 2. Why & when

`charAt` is the tool of choice whenever logic must examine or act on **individual characters** rather than the string as a whole:

- **Character-by-character scanning** — checking each character against some rule (is it a digit? a vowel? uppercase?), typically in a loop from `0` to `length() - 1`.
- **Parsing simple formats** — reading fixed positions in a structured string (a specific column in a fixed-width record, a single-character flag at a known offset).
- **Building new strings character by character** — combined with a `StringBuilder`, `charAt` lets you inspect and selectively include characters one at a time.

For anything beyond single characters — substrings, searching for a pattern — dedicated methods (`substring`, `indexOf`, `split`) are almost always clearer and less error-prone than manually looping with `charAt` and reconstructing the logic yourself.

## 3. Core concept

```java
public class CharAtDemo {
    public static void main(String[] args) {
        String word = "Hello";

        for (int i = 0; i < word.length(); i++) {
            char c = word.charAt(i);
            System.out.println("Index " + i + ": '" + c + "'");
        }

        // Counting vowels using charAt in a loop
        int vowelCount = 0;
        String vowels = "aeiouAEIOU";
        for (int i = 0; i < word.length(); i++) {
            if (vowels.indexOf(word.charAt(i)) >= 0) {
                vowelCount++;
            }
        }
        System.out.println("Vowel count: " + vowelCount);
    }
}
```

The first loop simply prints every character with its index. The second loop reuses the same `charAt`-driven scanning pattern but adds a condition (checking membership in `vowels` via `indexOf`) to count only the characters that match — the loop shape stays the same, only what happens per character changes.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="charAt diagram: the string Hello with indices 0 through 4 shown above each character; charAt(1) points at the character e, and charAt(5) would be out of bounds since the valid range only goes up to index 4.">
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">word.charAt(1) — indexing into "Hello"</text>

  <rect x="220" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="246" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">H</text>
  <rect x="272" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="298" y="67" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">e</text>
  <rect x="324" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">l</text>
  <rect x="376" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="402" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">l</text>
  <rect x="428" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="454" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">o</text>

  <text x="246" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">0</text>
  <text x="298" y="93" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">1 ← charAt(1)</text>
  <text x="350" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2</text>
  <text x="402" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">3</text>
  <text x="454" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">4</text>

  <text x="350" y="120" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">charAt(5) or charAt(-1) would throw StringIndexOutOfBoundsException — only 0..4 are valid.</text>
</svg>

`charAt(index)` returns exactly one character; any index outside `0..length()-1` is an immediate exception, not a silent default.

## 5. Runnable example

Scenario: validating a simple password's character composition (at least one digit, at least one uppercase letter) — starting with a basic per-character scan, then extending it to track multiple conditions at once, then hardening it against an empty-string edge case where the scanning loop must not assume there's at least one character to check.

### Level 1 — Basic

```java
public class PasswordCheckBasic {
    public static void main(String[] args) {
        String password = "Secret1";
        boolean hasDigit = false;

        for (int i = 0; i < password.length(); i++) {
            char c = password.charAt(i);
            if (Character.isDigit(c)) {
                hasDigit = true;
            }
        }

        System.out.println("Has at least one digit: " + hasDigit);
    }
}
```

**How to run:** `java PasswordCheckBasic.java`

The loop visits every character via `password.charAt(i)`, and `Character.isDigit(c)` checks whether that single character is a digit — the moment any character satisfies it, `hasDigit` is set `true` and stays that way for the rest of the scan (there's no early exit here, since we still want to visit every character for other checks added later).

### Level 2 — Intermediate

Same password check, now tracking **two** conditions simultaneously in one pass — at least one digit *and* at least one uppercase letter — reusing the same single-scan loop rather than looping over the string twice.

```java
public class PasswordCheckIntermediate {
    public static void main(String[] args) {
        String password = "secret1";
        boolean hasDigit = false;
        boolean hasUpper = false;

        for (int i = 0; i < password.length(); i++) {
            char c = password.charAt(i);
            if (Character.isDigit(c)) {
                hasDigit = true;
            }
            if (Character.isUpperCase(c)) {
                hasUpper = true;
            }
        }

        boolean strong = hasDigit && hasUpper;
        System.out.println("hasDigit=" + hasDigit + ", hasUpper=" + hasUpper + ", strong=" + strong);
    }
}
```

**How to run:** `java PasswordCheckIntermediate.java`

Both `if` checks run for every character in the same loop iteration — `charAt(i)` is called once per pass and reused for both checks, rather than scanning the string twice (once per condition). For `password = "secret1"`, `hasDigit` becomes `true` (the `'1'`) but `hasUpper` stays `false` (no uppercase letters), so `strong` is `false`.

### Level 3 — Advanced

Same strength check, now defensively handling an **empty password** — the loop naturally handles `length() == 0` correctly (it simply never executes), but the method adds an explicit early check so the "empty password" case is reported clearly rather than silently falling through as "not strong" with no explanation.

```java
public class PasswordCheckAdvanced {

    static String checkStrength(String password) {
        if (password == null || password.length() == 0) {
            return "Password is empty or missing";
        }

        boolean hasDigit = false;
        boolean hasUpper = false;
        boolean hasLower = false;

        for (int i = 0; i < password.length(); i++) {
            char c = password.charAt(i);
            if (Character.isDigit(c)) hasDigit = true;
            else if (Character.isUpperCase(c)) hasUpper = true;
            else if (Character.isLowerCase(c)) hasLower = true;
        }

        if (hasDigit && hasUpper && hasLower) {
            return "Strong";
        } else if (hasDigit || hasUpper || hasLower) {
            return "Weak";
        } else {
            return "Contains no letters or digits";
        }
    }

    public static void main(String[] args) {
        String[] passwords = { "Secret1", "secret", "", "12345", null };
        for (String p : passwords) {
            System.out.println("password=" + p + " -> " + checkStrength(p));
        }
    }
}
```

**How to run:** `java PasswordCheckAdvanced.java`

The guard clause `if (password == null || password.length() == 0)` handles both a missing password and a genuinely empty one *before* the `charAt` loop, since `password.length()` (and, transitively, `charAt`) would throw a `NullPointerException` if called on `null`. Note that even without the guard, an empty (but non-`null`) string would have been handled safely by the loop itself: `for (int i = 0; i < 0; i++)` simply never runs, leaving all three flags `false` — the explicit check exists purely to give a clearer message than "contains no letters or digits" for a password that was never provided at all.

## 6. Walkthrough

Trace `checkStrength("Secret1")`:

**Guard clause.** `password` is neither `null` nor empty (`length() == 7`), so execution proceeds to the scanning loop.

**i = 0.** `c = charAt(0) = 'S'`. Not a digit; `Character.isUpperCase('S')` is `true` → `hasUpper = true`.

**i = 1 through 5.** Characters `'e'`, `'c'`, `'r'`, `'e'`, `'t'` are each lowercase letters, setting `hasLower = true` (repeatedly, harmlessly) on each of these passes.

**i = 6.** `c = charAt(6) = '1'`. `Character.isDigit('1')` is `true` → `hasDigit = true`.

```
i=0: 'S' -> uppercase -> hasUpper=true
i=1..5: 'e','c','r','e','t' -> lowercase -> hasLower=true
i=6: '1' -> digit -> hasDigit=true
```

**Final decision.** After the loop, `hasDigit`, `hasUpper`, and `hasLower` are all `true`, so `hasDigit && hasUpper && hasLower` is `true`, and the method returns `"Strong"`.

**Full output.** For the five passwords in `main`: `"Secret1"` → `Strong`; `"secret"` → `Weak` (only `hasLower` is true); `""` → `Password is empty or missing` (caught by the guard clause); `"12345"` → `Weak` (only `hasDigit` is true); `null` → `Password is empty or missing` (also caught by the guard clause, before any `charAt` call could throw).

## 7. Gotchas & takeaways

> **`charAt` throws `StringIndexOutOfBoundsException` for any index outside `0` to `length() - 1`, including exactly `length()` itself** — a very common off-by-one bug is looping with `i <= word.length()` instead of `i < word.length()`, which attempts `charAt(length())` on the final pass and crashes.

> **A `for` loop bounded by `i < password.length()` handles an empty string safely on its own** (`length()` is `0`, so the loop body never runs) — you don't strictly need a separate empty-string guard just to avoid a crash, though adding one can still be worthwhile for a clearer, more specific message to the caller.

- `charAt(index)` returns one `char` at the given zero-based position; valid indices run from `0` to `length() - 1` inclusive.
- Looping with `i < str.length()` (not `<=`) is the standard, safe way to visit every character exactly once.
- Multiple independent per-character checks can share a single scanning loop, calling `charAt(i)` once and reusing the result for each check.
- Always null-check a string before scanning it with `charAt` in a loop, since `length()` itself throws on a `null` receiver.
