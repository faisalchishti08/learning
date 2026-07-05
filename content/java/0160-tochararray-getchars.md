---
card: java
gi: 160
slug: tochararray-getchars
title: toCharArray() & getChars()
---

## 1. What it is

`toCharArray()` returns a brand-new `char[]` containing a copy of every character in the string, in order — it's the standard bridge from `String` (immutable) to a raw, mutable character array you can freely modify. `getChars(int srcBegin, int srcEnd, char[] dst, int dstBegin)` copies a *range* of the string's characters directly into a portion of an existing array you already have, avoiding the allocation of a brand-new array for the whole string when you only need part of it, or when you're filling one array from several sources.

```java
String word = "hello";
char[] letters = word.toCharArray();
// letters = {'h', 'e', 'l', 'l', 'o'} — a genuinely new, independent array

char[] buffer = new char[10];
word.getChars(1, 4, buffer, 2);
// copies characters at indices 1,2,3 of "hello" ('e','l','l') into buffer starting at index 2
// buffer = {'\0','\0','e','l','l','\0','\0','\0','\0','\0'}
```

Both methods copy characters *out of* the string into a separate array — neither can be used to modify the original `String`, which remains immutable regardless.

## 2. Why & when

Converting to a `char[]` is useful whenever code needs to work with individual characters using array-style access and mutation, which `String` itself never allows:

- **In-place character manipulation** — reversing, shuffling, or otherwise rearranging characters, which requires a mutable structure; a `char[]` can be modified freely, then converted back with `new String(charArray)`.
- **Interfacing with APIs that expect `char[]`** — some older or security-sensitive APIs (like password fields) deliberately use `char[]` instead of `String`, specifically so the data can be explicitly overwritten/cleared in memory once no longer needed, something an immutable `String` cannot support.
- **`getChars` for filling one large array from multiple string sources**, avoiding several intermediate small array allocations that `toCharArray` (called once per source string) would otherwise produce.

For read-only character-by-character access, `charAt(int)` (covered earlier) is usually simpler than converting to an array first — reach for `toCharArray`/`getChars` specifically when you need array semantics: indexed mutation, or passing into an API that requires `char[]`.

## 3. Core concept

```java
public class CharArrayDemo {
    public static void main(String[] args) {
        String original = "hello";
        char[] chars = original.toCharArray();

        // Reverse the array in place — impossible to do directly on a String
        int left = 0, right = chars.length - 1;
        while (left < right) {
            char temp = chars[left];
            chars[left] = chars[right];
            chars[right] = temp;
            left++;
            right--;
        }

        String reversed = new String(chars);
        System.out.println("Original: " + original); // "hello" — unchanged
        System.out.println("Reversed: " + reversed);  // "olleh"
    }
}
```

`toCharArray()` produces a mutable working copy, which is then reversed in place using ordinary array-swap logic — something that has no direct equivalent on a `String` itself, precisely because `String` is immutable. `new String(chars)` converts the mutated array back into a genuine `String` once the work is done.

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ToCharArray diagram: the immutable string hello is copied into a mutable char array, which is then reversed in place using index swaps, and finally converted back into a new immutable string olleh, with the original string left completely unchanged throughout." >
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">String (immutable) -&gt; char[] (mutable) -&gt; String (immutable, new)</text>

  <rect x="40" y="45" width="120" height="30" rx="6" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="100" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"hello"</text>

  <path d="M 160 60 L 220 60" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <text x="190" y="50" fill="#79c0ff" font-size="7.5" font-family="sans-serif">toCharArray()</text>

  <rect x="220" y="45" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">char[] mutable, reversed in place</text>

  <path d="M 400 60 L 460 60" stroke="#6db33f" stroke-width="2" marker-end="url(#b)"/>
  <text x="430" y="50" fill="#6db33f" font-size="7.5" font-family="sans-serif">new String(...)</text>

  <rect x="460" y="45" width="120" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="520" y="65" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"olleh"</text>

  <text x="350" y="100" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">The original "hello" String object is never touched — only the intermediate char[] copy is mutated.</text>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`toCharArray()` and `new String(char[])` bracket the one place where genuinely mutable, in-place character work happens.

## 5. Runnable example

Scenario: checking whether a word is a palindrome (reads the same forwards and backwards) — starting with a basic version using `toCharArray()` for a reversal-based check, then extending it to ignore case and spaces, then hardening it into a more memory-efficient two-pointer check that avoids allocating extra arrays altogether, using `charAt` instead once the array-based version has demonstrated the core idea.

### Level 1 — Basic

```java
public class PalindromeBasic {
    public static void main(String[] args) {
        String word = "racecar";
        char[] chars = word.toCharArray();

        int left = 0, right = chars.length - 1;
        boolean isPalindrome = true;
        while (left < right) {
            if (chars[left] != chars[right]) {
                isPalindrome = false;
                break;
            }
            left++;
            right--;
        }

        System.out.println(word + " is a palindrome: " + isPalindrome);
    }
}
```

**How to run:** `java PalindromeBasic.java`

`toCharArray()` produces `{'r','a','c','e','c','a','r'}`, and the two-pointer loop compares `chars[left]` against `chars[right]`, moving inward from both ends — for `"racecar"`, every pair matches all the way to the middle, so `isPalindrome` remains `true`.

### Level 2 — Intermediate

Same palindrome check, now **ignoring case and non-letter characters** (spaces, punctuation) so a phrase like `"A man a plan a canal Panama"` is correctly recognized — building a cleaned `char[]` first using `toCharArray()` combined with filtering.

```java
public class PalindromeIntermediate {

    static char[] cleanChars(String text) {
        String lower = text.toLowerCase();
        StringBuilder cleaned = new StringBuilder();
        for (char c : lower.toCharArray()) {
            if (Character.isLetterOrDigit(c)) {
                cleaned.append(c);
            }
        }
        return cleaned.toString().toCharArray();
    }

    public static void main(String[] args) {
        String phrase = "A man a plan a canal Panama";
        char[] chars = cleanChars(phrase);

        int left = 0, right = chars.length - 1;
        boolean isPalindrome = true;
        while (left < right) {
            if (chars[left] != chars[right]) {
                isPalindrome = false;
                break;
            }
            left++;
            right--;
        }

        System.out.println("\"" + phrase + "\" is a palindrome: " + isPalindrome);
    }
}
```

**How to run:** `java PalindromeIntermediate.java`

`for (char c : lower.toCharArray())` iterates the lowercased phrase's characters (the enhanced `for` loop works directly over the array `toCharArray()` returns), appending only letters/digits into `cleaned` and skipping spaces entirely. The final `cleaned.toString().toCharArray()` converts the filtered `StringBuilder` content into a fresh `char[]` ready for the same two-pointer comparison used in Level 1.

### Level 3 — Advanced

Same cleaned-palindrome check, now avoiding the intermediate `char[]` allocation for the cleaning step by using `getChars` to copy directly into a pre-sized destination array, and adding a defensive check for a `null` or empty input.

```java
public class PalindromeAdvanced {

    static boolean isPalindrome(String text) {
        if (text == null || text.isEmpty()) {
            return false;
        }

        String lower = text.toLowerCase();
        char[] source = new char[lower.length()];
        lower.getChars(0, lower.length(), source, 0); // copy the WHOLE lowercased string into source

        char[] cleaned = new char[source.length];
        int count = 0;
        for (char c : source) {
            if (Character.isLetterOrDigit(c)) {
                cleaned[count] = c;
                count++;
            }
        }

        int left = 0, right = count - 1;
        while (left < right) {
            if (cleaned[left] != cleaned[right]) {
                return false;
            }
            left++;
            right--;
        }
        return true;
    }

    public static void main(String[] args) {
        String[] phrases = { "racecar", "A man a plan a canal Panama", "hello world", "", null };
        for (String phrase : phrases) {
            System.out.println(phrase + " -> " + isPalindrome(phrase));
        }
    }
}
```

**How to run:** `java PalindromeAdvanced.java`

`lower.getChars(0, lower.length(), source, 0)` copies the entire lowercased string directly into the pre-allocated `source` array, starting at destination index `0` — functionally equivalent to `lower.toCharArray()` here, but demonstrating `getChars`'s explicit range/destination parameters, which matter more when copying only part of a string or filling a larger shared array from multiple pieces. The `cleaned` array is sized the same as `source` (an upper bound on how many letter/digit characters could exist) but only the first `count` positions are ever meaningfully filled and compared, since `count` tracks exactly how many characters were actually kept.

## 6. Walkthrough

Trace `isPalindrome("A man a plan a canal Panama")`:

**Guard clause.** Input is neither `null` nor empty, so execution proceeds.

**Lowercasing and copying.** `lower = "a man a plan a canal panama"`. `source = new char[28]` (matching `lower.length()`). `lower.getChars(0, 28, source, 0)` copies every character of `lower` into `source`, positions 0 through 27.

**Filtering.** The loop over `source` copies only letters into `cleaned`, skipping spaces: it builds up `cleaned = {'a','m','a','n','a','p','l','a','n','a','c','a','n','a','l','p','a','n','a','m','a', ...}` (unused trailing slots remain default `'\0'`), with `count` ending at `21` (the number of actual letters).

**Two-pointer comparison.** `left = 0`, `right = count - 1 = 20`. The loop compares `cleaned[0]` (`'a'`) with `cleaned[20]` (`'a'`) — match, `left++`, `right--`. This continues inward; every pair matches all the way to the middle, since the cleaned sequence really does read the same forwards and backwards.

```
lower   = "a man a plan a canal panama"
source  = same characters, copied via getChars (28 chars incl. spaces)
cleaned = "amanaplanacanalpanama" (21 chars, spaces removed), count=21
two-pointer scan: cleaned[0]='a' vs cleaned[20]='a' match... continues to the middle, all match
-> return true
```

**Final output.** `"racecar"` → `true`; the cleaned Panama phrase → `true` (as traced); `"hello world"` → `false` (fails the comparison partway through); `""` → `false` (caught by the guard clause); `null` → `false` (also caught by the guard clause).

## 7. Gotchas & takeaways

> **`toCharArray()` and `getChars()` both copy characters *out of* a string — neither can be used to modify the original `String` in place**, since `String` remains immutable regardless of what you do to a separately-obtained array. Modifying the returned `char[]` never affects the source string at all.

> **`getChars`'s parameters are easy to transpose** — `srcBegin`, `srcEnd` (exclusive, like `substring`), `dst` array, and `dstBegin` (the starting position *in the destination*, not the source). Passing them in the wrong order, or forgetting that `srcEnd` is exclusive, is a common source of off-by-one or `ArrayIndexOutOfBoundsException` bugs.

- `toCharArray()` copies an entire string into a new `char[]`; `getChars(...)` copies a specified range into an existing array at a chosen destination offset.
- Neither method can mutate the original `String` — they exist to give you a separate, genuinely mutable working copy.
- Convert a modified `char[]` back into a `String` with `new String(charArray)` once your in-place work is finished.
- Prefer `charAt` for simple read-only character access; reach for `toCharArray`/`getChars` specifically when you need array-style indexed mutation or must interoperate with a `char[]`-based API.
