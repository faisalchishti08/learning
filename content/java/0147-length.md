---
card: java
gi: 147
slug: length
title: length()
---

## 1. What it is

`String.length()` returns the number of `char` values in a string, as an `int`. It is a **method call**, not a field access — a common trip-up for anyone coming from arrays, where `array.length` is a field with no parentheses. Strings use `str.length()`, arrays use `array.length`; mixing the two up is a compile error either way, so the confusion surfaces immediately rather than silently.

```java
String word = "hello";
int len = word.length(); // 5

int[] numbers = { 1, 2, 3 };
int arrLen = numbers.length; // 3 — no parentheses; this is a field, not a method
```

An empty string `""` has `length() == 0`; there is no such thing as a "null-length" string distinct from `null` itself — `length()` called on a `null` reference throws a `NullPointerException`, since there's no object to ask.

## 2. Why & when

`length()` is the starting point for almost any character-level string processing:

- **Bounds-checking before indexed access** — `charAt(i)` (covered next) requires `0 <= i < length()`; you nearly always check `length()` first.
- **Loop bounds** — iterating character by character with `for (int i = 0; i < str.length(); i++)`.
- **Validation** — checking a string isn't too short/long for some requirement (a password's minimum length, a fixed-width field's expected size).
- **Emptiness checks** — `str.length() == 0` (equivalent to, but more explicit historically than, the modern `str.isEmpty()`).

## 3. Core concept

```java
public class LengthDemo {
    public static void main(String[] args) {
        String[] samples = { "hello", "", "a", "supercalifragilisticexpialidocious" };

        for (String s : samples) {
            System.out.println("\"" + s + "\" has length " + s.length());
        }
    }
}
```

Each call to `s.length()` simply reports how many characters make up that particular string — `""` reports `0`, and the longest sample reports its full character count, regardless of how the string was constructed or where it came from.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Length diagram: the string hello is shown as five indexed character boxes, 0 through 4, with length() returning 5 — one more than the highest valid index.">
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"hello".length() == 5 — indices run 0 through length()-1</text>

  <rect x="220" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="246" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">h</text>
  <rect x="272" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="298" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">e</text>
  <rect x="324" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">l</text>
  <rect x="376" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="402" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">l</text>
  <rect x="428" y="45" width="52" height="34" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="454" y="67" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">o</text>

  <text x="246" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">idx 0</text>
  <text x="298" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">idx 1</text>
  <text x="350" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">idx 2</text>
  <text x="402" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">idx 3</text>
  <text x="454" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">idx 4</text>

  <text x="350" y="120" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">length() = 5, but the highest valid index is 4 — index 5 would throw an exception.</text>
</svg>

`length()` counts characters (5), while valid indices only ever go up to `length() - 1` (index 4).

## 5. Runnable example

Scenario: validating a fixed-format product code before processing it — starting with a basic length check, then adding a minimum/maximum range check, then hardening it to safely handle a `null` input, which would otherwise crash on `.length()`.

### Level 1 — Basic

```java
public class CodeLengthBasic {
    public static void main(String[] args) {
        String code = "ABC123";
        int expectedLength = 6;

        if (code.length() == expectedLength) {
            System.out.println("Code has the correct length.");
        } else {
            System.out.println("Invalid code length: " + code.length());
        }
    }
}
```

**How to run:** `java CodeLengthBasic.java`

`code.length()` returns `6`, matching `expectedLength`, so the program prints `"Code has the correct length."`. Changing `code` to anything shorter or longer than 6 characters would print the mismatch branch instead.

### Level 2 — Intermediate

Same code validator, now checking a **range** of acceptable lengths (some product codes are 6-8 characters) rather than one exact value.

```java
public class CodeLengthIntermediate {
    public static void main(String[] args) {
        String[] codes = { "ABC123", "AB12", "ABCDEFGH", "ABCD1234567" };
        int minLength = 6;
        int maxLength = 8;

        for (String code : codes) {
            int len = code.length();
            if (len >= minLength && len <= maxLength) {
                System.out.println(code + " (" + len + " chars) is valid.");
            } else {
                System.out.println(code + " (" + len + " chars) is INVALID — must be " + minLength + "-" + maxLength + " chars.");
            }
        }
    }
}
```

**How to run:** `java CodeLengthIntermediate.java`

`len` is stored once per iteration rather than calling `code.length()` repeatedly — a minor efficiency habit, since `length()` in `String` is actually cheap (it just returns a stored value), but storing it also avoids recomputation if it were ever used multiple times in a longer check.

### Level 3 — Advanced

Same validator, now defensively handling a **`null`** code — a real production concern, since calling `.length()` directly on a `null` reference throws a `NullPointerException` rather than returning `0` or `false`.

```java
public class CodeLengthAdvanced {

    static boolean isValidCode(String code, int minLength, int maxLength) {
        if (code == null) {
            return false; // check null FIRST — calling .length() on null would throw
        }
        int len = code.length();
        return len >= minLength && len <= maxLength;
    }

    public static void main(String[] args) {
        String[] codes = { "ABC123", null, "AB", "ABCDEFGH12" };

        for (String code : codes) {
            boolean valid = isValidCode(code, 6, 8);
            System.out.println("code=" + code + " -> valid: " + valid);
        }
    }
}
```

**How to run:** `java CodeLengthAdvanced.java`

The `if (code == null) return false;` guard clause runs *before* `code.length()` is ever called, so a `null` code is safely reported as invalid instead of crashing the program. This is the standard defensive pattern whenever a string's origin (user input, a database column, a parsed field) might legitimately be `null`.

## 6. Walkthrough

Trace `isValidCode(null, 6, 8)`:

**Null check.** `code == null` is `true` (the argument really is `null`), so the guard clause immediately executes `return false;` — `code.length()` is never reached, avoiding what would otherwise be a `NullPointerException`.

Trace `isValidCode("AB", 6, 8)` for comparison:

**Null check.** `code == null` is `false` (a real, non-null empty-ish string), so execution proceeds. `len = code.length()` is `2`. `len >= 6 && len <= 8` evaluates to `false && true` = `false`, so the method returns `false`.

```
isValidCode(null, 6, 8):   code==null? true  -> return false (length() never called)
isValidCode("AB", 6, 8):   code==null? false -> len=2 -> 2>=6? false -> return false
isValidCode("ABC123", 6, 8): code==null? false -> len=6 -> 6>=6 && 6<=8 -> return true
```

**Final output.** For the four codes in `main`, the program prints `code=ABC123 -> valid: true`, `code=null -> valid: false`, `code=AB -> valid: false`, and `code=ABCDEFGH12 -> valid: false` (length `10` exceeds `maxLength` of `8`).

## 7. Gotchas & takeaways

> **`str.length()` (method, with parentheses) and `array.length` (field, no parentheses) are different syntax for different constructs — mixing them up is a compile error.** `str.length` (missing parentheses) and `array.length()` (extra parentheses) both fail to compile; the fix is simply remembering which construct you're working with.

> **Calling `.length()` on a `null` `String` reference throws a `NullPointerException`** — always check for `null` before calling `.length()` (or any method) if the string's origin might legitimately produce `null`.

- `str.length()` returns the character count as an `int`; it requires parentheses because it's a method, unlike an array's `.length` field.
- Valid character indices for a string of length `n` run from `0` to `n - 1` — `length()` itself is always one more than the highest valid index.
- Always null-check before calling `.length()` if the string could be `null`, or the call throws a `NullPointerException`.
- `length() == 0` and the more explicit `isEmpty()` (a later addition) mean the same thing for detecting an empty string.
