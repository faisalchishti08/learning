---
card: java
gi: 624
slug: string-strip-stripleading-striptrailing
title: String.strip() / stripLeading() / stripTrailing()
---

## 1. What it is

Java 11 introduced three Unicode-aware string-stripping methods: `String.strip()`, `String.stripLeading()`, and `String.stripTrailing()`. These are the modern replacements for the older `String.trim()` method. The critical difference is the definition of "whitespace": `trim()` removes only characters ≤ U+0020 (ASCII space and control characters), while `strip()` removes all characters for which `Character.isWhitespace(int)` returns `true` — the full Unicode whitespace set including non-breaking space (`\u00A0`), various width spaces, and other Unicode separators. `stripLeading()` removes whitespace from the beginning only, and `stripTrailing()` removes from the end only.

## 2. Why & when

`trim()` was defined in Java 1.0 (1995) when Unicode support was minimal. For over two decades, Java developers processing international text — web forms, XML/JSON data, user-generated content — risked non-breaking spaces and other Unicode whitespace characters passing through validation undetected. `strip()` fixes this without breaking backward compatibility: `trim()` is not deprecated and continues to behave exactly as it always did. Use `strip()` as the default whitespace-removal method for all new code; use `trim()` only when you specifically need the legacy ASCII-only behaviour or are working in a codebase that cannot yet adopt Java 11.

## 3. Core concept

```java
String s = "  \u00A0hello\u2003 ";

s.trim();          // "\u00A0hello\u2003 "  — only ASCII space removed; Unicode whitespace stays
s.strip();         // "hello"                  — all Unicode whitespace removed
s.stripLeading();  // "hello\u2003 "          — Unicode whitespace removed from start only
s.stripTrailing(); // "  \u00A0hello"          — Unicode whitespace removed from end only

// strip() vs trim() on a simple ASCII case: identical results
"  hello  ".trim();   // "hello"
"  hello  ".strip();  // "hello"
```

The three methods form a complete toolkit: `strip()` for both ends, `stripLeading()` for the start, `stripTrailing()` for the end.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="trim() vs strip() — Unicode whitespace handling comparison">
  <rect x="10" y="10" width="580" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="30" y="25" width="120" height="35" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="90" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"  \u00A0hi  "</text>

  <text x="165" y="47" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>

  <rect x="185" y="20" width="130" height="45" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="250" y="38" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">trim()</text>
  <text x="250" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"\u00A0hi"</text>

  <text x="330" y="47" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>

  <rect x="350" y="20" width="130" height="45" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="415" y="38" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">strip()</text>
  <text x="415" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">"hi"</text>

  <rect x="30" y="80" width="230" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="145" y="97" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">stripLeading()</text>
  <text x="145" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">whitespace from start only</text>

  <rect x="280" y="80" width="230" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="395" y="97" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">stripTrailing()</text>
  <text x="395" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">whitespace from end only</text>

  <text x="30" y="150" fill="#8b949e" font-size="9" font-family="sans-serif">trim() definition: codepoint &lt;= U+0020  |  strip() definition: Character.isWhitespace(codepoint)</text>
  <text x="30" y="168" fill="#f85149" font-size="9" font-family="sans-serif">trim() is NOT deprecated — it is preserved for backward compatibility</text>
</svg>

`trim()` and `strip()` produce different results on strings containing Unicode whitespace characters; on pure ASCII input they behave identically.

## 5. Runnable example

Scenario: cleaning user-submitted text from a web form where copy-pasting from word processors often introduces non-breaking spaces and other invisible Unicode characters — starting with basic stripping, extending to directional stripping, and finally handling the complete Unicode whitespace spectrum.

### Level 1 — Basic

```java
// File: StripDemo.java
public class StripDemo {
    public static void main(String[] args) {
        String raw = "   hello world   ";

        System.out.println("Original:  '" + raw + "'");
        System.out.println("trim():    '" + raw.trim() + "'");
        System.out.println("strip():   '" + raw.strip() + "'");

        // On ASCII input, trim() and strip() are identical
        System.out.println("\ntrim() == strip(): " + raw.trim().equals(raw.strip()));
    }
}
```

**How to run:** `java StripDemo.java`

Expected output:
```
Original:  '   hello world   '
trim():    'hello world'
strip():   'hello world'

trim() == strip(): true
```

On pure ASCII input, `trim()` and `strip()` produce identical results. The difference emerges with Unicode whitespace.

### Level 2 — Intermediate

```java
// File: StripUnicode.java
public class StripUnicode {
    public static void main(String[] args) {
        // Simulate copy-pasted text with non-breaking spaces (\u00A0)
        // Common in web forms, Word documents, HTML &nbsp;
        String pasted = "\u00A0\u00A0Hello, world!\u00A0\u00A0";
        String mixed  = " \u00A0 hello \u2003 world \u00A0 ";

        System.out.println("=== Non-breaking space (\\u00A0) ===");
        System.out.println("Input:        '" + pasted + "'");
        System.out.println("trim():       '" + pasted.trim() + "'");
        System.out.println("strip():      '" + pasted.strip() + "'");

        System.out.println("\n=== Mixed Unicode whitespace ===");
        System.out.println("Input:        '" + mixed + "'");
        System.out.println("trim():       '" + mixed.trim() + "'");
        System.out.println("strip():      '" + mixed.strip() + "'");

        // Directional stripping
        String leftPadded  = "\u2003\u2003code";
        String rightPadded = "code\u2003\u2003";

        System.out.println("\n=== Directional stripping ===");
        System.out.println("Left-padded:  '" + leftPadded + "'");
        System.out.println("stripLeading: '" + leftPadded.stripLeading() + "'");
        System.out.println("Right-padded: '" + rightPadded + "'");
        System.out.println("stripTrailing:'" + rightPadded.stripTrailing() + "'");
    }
}
```

**How to run:** `java StripUnicode.java`

Expected output:
```
=== Non-breaking space (\u00A0) ===
Input:        '  Hello, world!  '
trim():       '  Hello, world!  '
strip():      'Hello, world!'

=== Mixed Unicode whitespace ===
Input:        '   hello   world   '
trim():       ' hello   world  '
strip():      'hello   world'

=== Directional stripping ===
Left-padded:  '  code'
stripLeading: 'code'
Right-padded: 'code  '
stripTrailing:'code'
```

The real-world concern: `trim()` silently fails on non-breaking spaces (`\u00A0`), which are common in web content (HTML `&nbsp;`), word processor exports, and copy-pasted text. `strip()` removes them correctly. For form validation where leading/trailing whitespace should be ignored but internal whitespace preserved, use `strip()` — or `stripLeading()` / `stripTrailing()` for asymmetric cases.

### Level 3 — Advanced

```java
// File: StripComplete.java
import java.util.*;

public class StripComplete {

    // Whitespace characters to test
    static final Map<String, String> WHITESPACE_CHARS = new LinkedHashMap<>();
    static {
        WHITESPACE_CHARS.put("Space (U+0020)", " ");
        WHITESPACE_CHARS.put("Tab (U+0009)", "\t");
        WHITESPACE_CHARS.put("Line feed (U+000A)", "\n");
        WHITESPACE_CHARS.put("Non-breaking space (U+00A0)", "\u00A0");
        WHITESPACE_CHARS.put("En space (U+2002)", "\u2002");
        WHITESPACE_CHARS.put("Em space (U+2003)", "\u2003");
        WHITESPACE_CHARS.put("Thin space (U+2009)", "\u2009");
        WHITESPACE_CHARS.put("Ideographic space (U+3000)", "\u3000");
        WHITESPACE_CHARS.put("Ogham space mark (U+1680)", "\u1680");
    }

    public static void main(String[] args) {
        System.out.println("=== trim() vs strip() — comprehensive Unicode test ===\n");
        System.out.printf("%-32s %-10s %-10s%n", "Character", "trim()", "strip()");
        System.out.println("-".repeat(54));

        for (var entry : WHITESPACE_CHARS.entrySet()) {
            String name = entry.getKey();
            String ch = entry.getValue();
            String testStr = ch + "X" + ch;  // surround 'X' with the whitespace char

            boolean trimWorked = testStr.trim().equals("X");
            boolean stripWorked = testStr.strip().equals("X");

            System.out.printf("%-32s %-10s %-10s%n",
                name,
                trimWorked ? "removes" : "FAILS",
                stripWorked ? "removes" : "FAILS");
        }

        System.out.println("\n=== Practical: form input sanitation ===\n");

        // Simulate a name field with various Unicode padding
        String[] rawInputs = {
            "  Alice  ",
            "\u00A0Bob\u00A0",
            "\u2003Charlie\u2003",
            "\u3000Diana\u3000",
            "  \u00A0Eve \u2003 ",
        };

        System.out.println("Input              → trim()         → strip()");
        System.out.println("-".repeat(56));
        for (String raw : rawInputs) {
            String t = raw.trim();
            String s = raw.strip();
            System.out.printf("%-18s → %-14s → %s%n",
                "'" + raw + "'",
                "'" + t + "'",
                "'" + s + "'");
        }

        // Performance note: strip() may be marginally slower due to Unicode checks,
        // but the difference is negligible for typical form-input lengths.
        System.out.println("\n=== Performance comparison (1M iterations) ===\n");
        String bench = "  hello  ";
        long start = System.nanoTime();
        for (int i = 0; i < 1_000_000; i++) { bench.trim(); }
        long trimTime = System.nanoTime() - start;

        start = System.nanoTime();
        for (int i = 0; i < 1_000_000; i++) { bench.strip(); }
        long stripTime = System.nanoTime() - start;

        System.out.printf("trim():  %d ns%n", trimTime / 1_000_000);
        System.out.printf("strip(): %d ns%n", stripTime / 1_000_000);
        System.out.println("(strip() may be slightly slower due to full Unicode checks)");
    }
}
```

**How to run:** `java StripComplete.java`

Expected output (times will vary):
```
=== trim() vs strip() — comprehensive Unicode test ===

Character                        trim()     strip()   
------------------------------------------------------
Space (U+0020)                   removes    removes   
Tab (U+0009)                     removes    removes   
Line feed (U+000A)               removes    removes   
Non-breaking space (U+00A0)      FAILS      removes   
En space (U+2002)                FAILS      removes   
Em space (U+2003)                FAILS      removes   
Thin space (U+2009)              FAILS      removes   
Ideographic space (U+3000)       FAILS      removes   
Ogham space mark (U+1680)        FAILS      removes   

=== Practical: form input sanitation ===

Input              → trim()         → strip()
--------------------------------------------------------
'  Alice  '        → 'Alice'        → 'Alice'
' Bob '            → ' Bob '        → 'Bob'
' Charlie '        → ' Charlie '    → 'Charlie'
'　Diana　'         → '　Diana　'     → 'Diana'
'  Eve   '         → '  Eve   '     → 'Eve'

=== Performance comparison (1M iterations) ===

trim():  ... ns
strip(): ... ns
(strip() may be slightly slower due to full Unicode checks)
```

The production-flavoured hard cases: (1) `trim()` fails on all Unicode whitespace beyond ASCII space, tab, and control characters — which covers most "invisible" characters users paste from word processors. (2) `strip()` handles the full Unicode whitespace set correctly, making it the right choice for any application that accepts international text. (3) The performance difference between `trim()` and `strip()` is negligible for typical use; prefer correctness over micro-optimisation.

## 6. Walkthrough

Tracing `" \u00A0hello\u2003 ".strip()`:

1. The JVM invokes `strip()` on the string `" \u00A0hello\u2003 "`. The method delegates to `StringUTF16.strip()` (or `StringLatin1.strip()` for Latin-1 strings).

2. `strip()` works in two phases. **Phase 1 — leading whitespace:** Starting at index 0, the method calls `Character.isWhitespace(codepoint)` for each character from the left. Space (U+0020) → true, keep going. Non-breaking space (U+00A0) → true, keep going. 'h' → false, stop. The leading whitespace count is 2. The new start index is 2.

3. **Phase 2 — trailing whitespace:** Starting from the end (length-1), the method checks each character from the right. Space (U+0020) → true, move left. Em space (U+2003) → true, move left. 'o' → false, stop. The trailing whitespace count is 2. The new end index is (length - 2).

4. The method returns `substring(2, length-2)`, which is `"hello"`. No new character array is allocated if the string is already stripped — `substring` shares the underlying array in modern JDK implementations for single-byte encodings (or copies for compact strings).

5. The caller receives the stripped string. No exceptions, no side effects.

## 7. Gotchas & takeaways

> `trim()` is **not deprecated** and never will be — it is part of Java's core API since 1.0 and its behaviour is specified by the JLS. Do not replace `trim()` with `strip()` in existing code without understanding whether the code relies on the ASCII-only behaviour (e.g. some protocols define whitespace as ASCII space specifically).

- `strip()`, `stripLeading()`, and `stripTrailing()` were added in Java 11 (same JEP as `isBlank()` and `lines()`) to modernise `String`'s whitespace handling for the Unicode era.
- The three methods return the original string unchanged if no whitespace is found at the relevant end(s), avoiding unnecessary allocation. Use `==` to check: `if (s.strip() == s) { /* no change */ }`.
- `Character.isWhitespace(int)` is the definitive Unicode whitespace test. If a character isn't whitespace per this method, `strip()` won't remove it.
- For form validation, the common pattern is `value.strip().isBlank()` — strip first, then check if anything meaningful remains. If blank, reject the input.
