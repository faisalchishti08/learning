---
card: java
gi: 622
slug: string-isblank
title: String.isBlank()
---

## 1. What it is

`String.isBlank()` is a Java 11 method that returns `true` if a string is **empty** or contains **only whitespace characters**, and `false` otherwise. It is the Unicode-aware successor to the common `str.trim().isEmpty()` pattern. Unlike `String.isEmpty()` — which returns `true` only for `""` (length zero) — `isBlank()` treats strings like `"   "` (three spaces), `"\t\n"` (tab + newline), and `"\u00A0"` (non-breaking space) as blank. The method uses the same definition of whitespace as `String.strip()`: any character for which `Character.isWhitespace(int)` returns `true`, covering the full Unicode whitespace set, not just ASCII space and tab.

## 2. Why & when

Before Java 11 the standard way to check for "empty or whitespace-only" was `str.trim().isEmpty()`, but this pattern has two problems: (a) `trim()` allocates a new `String` object just to check emptiness, creating avoidable garbage, and (b) `trim()` only strips ASCII space (`' '`) and tab (`'\t'`), missing Unicode whitespace characters like non-breaking space (`\u00A0`), en-space, and various other Unicode separators. `isBlank()` solves both: it performs a zero-allocation check against the full Unicode whitespace definition. Use it whenever you validate user input (checking that a form field isn't just spaces), skip blank lines in text processing, or guard against whitespace-only values in configuration.

## 3. Core concept

```java
"".isBlank();          // true  — empty
"   ".isBlank();       // true  — three spaces
"\t\n".isBlank();     // true  — tab + newline
"\u00A0".isBlank();   // true  — non-breaking space (Unicode)
" hello ".isBlank();   // false — contains non-whitespace
"a".isBlank();         // false — non-blank

// Contrast with isEmpty():
"".isEmpty();          // true
"   ".isEmpty();       // false — isEmpty only checks length == 0
```

The method is a pure query: it allocates no new objects, throws no exceptions (it is null-hostile — calling on `null` throws `NullPointerException`), and returns a simple boolean.

## 4. Diagram

<svg viewBox="0 0 560 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="isBlank vs isEmpty comparison for different input strings">
  <rect x="10" y="10" width="540" height="180" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#8b949e" font-size="10" font-family="monospace">Input</text>
  <text x="190" y="35" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">isEmpty()</text>
  <text x="370" y="35" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">isBlank()</text>

  <text x="30" y="58" fill="#e6edf3" font-size="11" font-family="monospace">""</text>
  <text x="200" y="58" fill="#3fb950" font-size="11" font-family="monospace" text-anchor="middle">true</text>
  <text x="380" y="58" fill="#3fb950" font-size="11" font-family="monospace" text-anchor="middle">true</text>

  <text x="30" y="82" fill="#e6edf3" font-size="11" font-family="monospace">"   "</text>
  <text x="200" y="82" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">false</text>
  <text x="380" y="82" fill="#3fb950" font-size="11" font-family="monospace" text-anchor="middle">true</text>

  <text x="30" y="106" fill="#e6edf3" font-size="11" font-family="monospace">"\t\n"</text>
  <text x="200" y="106" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">false</text>
  <text x="380" y="106" fill="#3fb950" font-size="11" font-family="monospace" text-anchor="middle">true</text>

  <text x="30" y="130" fill="#e6edf3" font-size="11" font-family="monospace">"hello"</text>
  <text x="200" y="130" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">false</text>
  <text x="380" y="130" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">false</text>

  <text x="30" y="154" fill="#e6edf3" font-size="11" font-family="monospace">"  hi  "</text>
  <text x="200" y="154" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">false</text>
  <text x="380" y="154" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">false</text>

  <rect x="30" y="168" width="520" height="1" fill="#30363d"/>
  <text x="30" y="185" fill="#8b949e" font-size="9" font-family="sans-serif">isBlank checks Unicode whitespace (Character.isWhitespace) — covers spaces, tabs, newlines, non-breaking spaces, and more</text>
</svg>

`isBlank()` returns `true` for the first three rows where `isEmpty()` fails — these are the cases where `trim().isEmpty()` would have been needed before Java 11.

## 5. Runnable example

Scenario: validating user-submitted form fields in a registration system — starting with basic blank checks, extending to batch validation, and finally handling Unicode edge cases and null safety.

### Level 1 — Basic

```java
// File: IsBlankDemo.java
public class IsBlankDemo {
    public static void main(String[] args) {
        String[] inputs = {"", "   ", "\t\n", "Alice", "  Bob  "};

        for (String s : inputs) {
            String display = s.replace("\t", "\\t").replace("\n", "\\n");
            System.out.printf("%-10s → isEmpty: %-5s  isBlank: %-5s%n",
                "\"" + display + "\"",
                s.isEmpty(),
                s.isBlank());
        }
    }
}
```

**How to run:** `java IsBlankDemo.java`

Expected output:
```
""         → isEmpty: true   isBlank: true 
"   "      → isEmpty: false  isBlank: true 
"\t\n"    → isEmpty: false  isBlank: true 
"Alice"    → isEmpty: false  isBlank: false
"  Bob  "  → isEmpty: false  isBlank: false
```

The simplest demonstration: `isBlank()` returns `true` for empty and whitespace-only strings, `false` otherwise. The critical difference from `isEmpty()` is visible on rows 2 and 3.

### Level 2 — Intermediate

```java
// File: FormValidator.java
import java.util.*;

public class FormValidator {
    record FieldResult(String field, boolean valid, String reason) {}

    public static void main(String[] args) {
        // Simulate form submission
        Map<String, String> form = new LinkedHashMap<>();
        form.put("username", "  jsmith  ");
        form.put("email", "jsmith@example.com");
        form.put("comment", "   ");          // blank — should be rejected
        form.put("phone", "");               // empty — should be rejected

        List<FieldResult> results = validate(form);

        for (var r : results) {
            String status = r.valid() ? "✓ PASS" : "✗ FAIL";
            System.out.printf("%s  %-10s → %s%n", status, r.field(), r.reason());
        }
    }

    static List<FieldResult> validate(Map<String, String> form) {
        List<FieldResult> results = new ArrayList<>();

        for (var entry : form.entrySet()) {
            String field = entry.getKey();
            String value = entry.getValue();

            if (value == null || value.isBlank()) {
                results.add(new FieldResult(field, false,
                    "must not be blank"));
            } else {
                results.add(new FieldResult(field, true, "ok"));
            }
        }
        return results;
    }
}
```

**How to run:** `java FormValidator.java`

Expected output:
```
✗ FAIL  username   → must not be blank
✓ PASS  email      → ok
✗ FAIL  comment    → must not be blank
✗ FAIL  phone      → must not be blank
```

The real-world concern: form validation. Notice that `"  jsmith  "` (username with surrounding spaces) also fails — `isBlank()` checks the raw value, so you typically want to `strip()` first for fields where surrounding whitespace should be ignored (`value.strip().isBlank()`). This subtlety is a common gotcha.

### Level 3 — Advanced

```java
// File: IsBlankUnicode.java
import java.util.*;

public class IsBlankUnicode {
    public static void main(String[] args) {
        System.out.println("=== Unicode whitespace coverage ===\n");

        // Various Unicode whitespace characters
        Map<String, String> chars = new LinkedHashMap<>();
        chars.put("ASCII space", " ");
        chars.put("ASCII tab", "\t");
        chars.put("Non-breaking space (\\u00A0)", "\u00A0");
        chars.put("En space (\\u2002)", "\u2002");
        chars.put("Em space (\\u2003)", "\u2003");
        chars.put("Thin space (\\u2009)", "\u2009");
        chars.put("Ideographic space (\\u3000)", "\u3000");
        chars.put("Zero-width space (\\u200B)", "\u200B");  // NOT whitespace per Character.isWhitespace

        // Show that trim() fails on Unicode whitespace but isBlank() handles it
        System.out.printf("%-35s %-8s %-8s %-12s%n", "Character", "isEmpty", "isBlank", "trim().isEmpty");
        System.out.println("-".repeat(65));

        for (var entry : chars.entrySet()) {
            String label = entry.getKey();
            String s = entry.getValue();
            System.out.printf("%-35s %-8s %-8s %-12s%n",
                label,
                s.isEmpty(),
                s.isBlank(),
                s.trim().isEmpty());  // trim() only handles ASCII space/tab
        }

        System.out.println("\n=== Null safety ===\n");

        // isBlank() is null-hostile — you must guard against null
        String nullStr = null;
        try {
            nullStr.isBlank();  // throws NullPointerException
        } catch (NullPointerException e) {
            System.out.println("null.isBlank() throws NullPointerException — always null-check first");
        }

        // Safe pattern:
        String safe = null;
        boolean blank = safe == null || safe.isBlank();
        System.out.println("Safe check (null guard): " + blank);
    }
}
```

**How to run:** `java IsBlankUnicode.java`

Expected output:
```
=== Unicode whitespace coverage ===

Character                           isEmpty  isBlank  trim().isEmpty
ASCII space                         false    true     true          
ASCII tab                           false    true     true          
Non-breaking space (\u00A0)         false    true     false         
En space (\u2002)                  false    true     false         
Em space (\u2003)                  false    true     false         
Thin space (\u2009)                false    true     false         
Ideographic space (\u3000)         false    true     false         
Zero-width space (\u200B)          false    false    false         

=== Null safety ===

null.isBlank() throws NullPointerException — always null-check first
Safe check (null guard): true
```

The production-flavoured hard cases: (1) Unicode whitespace — `trim()` only handles ASCII space/tab and silently passes through non-breaking spaces and other Unicode separators, giving a false sense of validation. `isBlank()` catches them all. (2) Zero-width space (`\u200B`) is intentionally NOT considered whitespace by `Character.isWhitespace`, so `isBlank()` returns `false` — it is a formatting character, not a separator. (3) `isBlank()` is null-hostile; always null-guard with `str == null || str.isBlank()`.

## 6. Walkthrough

Tracing `"   ".isBlank()`:

1. The JVM invokes `String.isBlank()` on the instance `"   "` (three space characters, length 3).

2. `isBlank()` iterates over each code point in the string. For each code point (in this case, each `' '` character), it calls `Character.isWhitespace(codepoint)`. Space (`' '`, U+0020) is classified as whitespace.

3. All three characters pass the whitespace check, and the loop completes without finding a non-whitespace character. The method returns `true`.

Now tracing `"  hi  ".isBlank()`:

1. `isBlank()` begins iterating. The first two characters are spaces → whitespace check passes.

2. The third character is `'h'` (U+0068). `Character.isWhitespace('h')` returns `false`. The method immediately returns `false` — short-circuiting, no further characters are examined.

3. No allocation occurs in either case. The method is `O(n)` in the length of the string but stops at the first non-whitespace character.

## 7. Gotchas & takeaways

> `isBlank()` is **null-hostile**: `((String) null).isBlank()` throws `NullPointerException`. Always guard with `str == null || str.isBlank()`. This is consistent with `isEmpty()` but catches developers who are used to `Objects.equals(str, "")`-style null-safe checks.

- `isBlank()` uses `Character.isWhitespace(int)` which covers the full Unicode whitespace set, not just ASCII. This includes non-breaking space (`\u00A0`), various width spaces, line/paragraph separators, and more — making it superior to `trim().isEmpty()` for internationalised applications.
- `isBlank()` does not allocate — it is a simple loop over code points with no object creation. This makes it suitable for performance-sensitive code paths where `trim().isEmpty()` would create unnecessary garbage.
- The method name is intentionally different from `isEmpty()`: "blank" means "empty or whitespace-only," a common concept in form-validation libraries (e.g. Apache Commons Lang's `StringUtils.isBlank()`).
- `isBlank()` returns `false` for strings that contain any non-whitespace character, even if surrounded by whitespace. To check "trimmed value is empty," use `str.strip().isEmpty()` which strips first.
