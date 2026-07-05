---
card: java
gi: 65
slug: unicode-source-u-escapes
title: Unicode source & \u escapes
---

## 1. What it is

Java source files are Unicode text. The compiler accepts any Unicode character — not just ASCII — in identifiers, string literals, and comments. Additionally, any Unicode character can be written as a `\u` escape sequence: `\uXXXX` where `XXXX` is a four-hex-digit code point.

```java
// \u escape in a string literal
String greeting = "Hello";   // "Hello"

// \u escape in an identifier (legal but impractical)
int bar = 5;    // compiles as: int bar = 5;

// \u escape in a comment — dangerous: processed BEFORE comment stripping
// 
  ← this is a NEWLINE character, processed even inside a comment
```

Unicode escapes are processed in the very first pass of compilation — before tokenisation, before comment stripping. This makes them uniquely powerful and uniquely dangerous.

## 2. Why & when

Java was designed from the start (1995) to be a global language. The Unicode source design means you can write identifiers in Japanese, Arabic, Cyrillic, or any other script. `\u` escapes exist to embed any Unicode character in source code even when the editor or file transfer tool doesn't support that code point. Practical uses today:
- Embedding non-ASCII characters in source that must stay ASCII-safe (e.g., some CI environments).
- Writing a known Unicode control character in a string without copy-pasting an invisible glyph.
- Understanding legacy code that uses `\u` escapes for obfuscation (uncommon but real in security contexts).

## 3. Core concept

```java
// ---- Processing order (Java Language Specification §3.3) ----
// Pass 1: \uXXXX escapes expanded to Unicode characters
// Pass 2: Line terminators normalised
// Pass 3: Source divided into tokens (identifiers, keywords, literals, operators)
// Pass 4: Tokens parsed into the AST

// Because pass 1 happens FIRST, \u escapes affect tokenisation:
int i = 5;      // i = 'i'; compiles as: int i = 5;
System.out.println(i);   // prints: 5

// ---- Dangerous case: \u in comments ----
// The following comment contains a 
 (newline) escape.
// The compiler expands it BEFORE realising the line is a comment,
// so the character after it starts a new logical line — outside the comment!

// 
 int escaped = 42;    ← the int declaration is LIVE CODE, not a comment!
// This compiles and runs.

// ---- \u in string literals ----
// Inside strings, \u is also expanded in pass 1, BEFORE string scanning:
String s1 = ""hello"";   // " = '"'; becomes: = "hello"  (string boundary!)
// This compiles to s1 = "hello" — the " closes/opens the string token.

// ---- Legal \u escape forms ----
// \uXXXX    — exactly 4 hex digits (0–9, a–f, A–F)
// \uuXXXX   — multiple u's are allowed: \uuuXXXX  (historical compatibility)
// \U...      — does NOT exist in Java (that's C syntax)

// ---- Common code points ----
// 	  horizontal tab
// 
  line feed (LF)
//   carriage return (CR)
//    space
// "  "  (double quote)
// '  '  (single quote)
// \  \  (backslash)
// ©  ©  (copyright)
// ♥  ♥  (heart)
// 中  中 (CJK ideograph)

// ---- Source file encoding ----
// Default encoding: UTF-8 (since JDK 18; -encoding flag in earlier versions)
// javac -encoding UTF-8 MyFile.java
// Non-ASCII chars in source → stored as their UTF-8 bytes in .java file;
//   OR escaped as \uXXXX for ASCII-safe source.
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java compilation passes: \u escapes expanded first (pass 1), then line terminators, then tokenisation — so \u in comments is still live">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>

  <!-- Pass 1 -->
  <rect x="16" y="22" width="150" height="148" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="91" y="38" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Pass 1</text>
  <text x="91" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">\u escape expansion</text>
  <line x1="26" y1="58" x2="156" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="72" fill="#e6edf3" font-size="7.5" font-family="monospace">H → H</text>
  <text x="26" y="85" fill="#e6edf3" font-size="7.5" font-family="monospace">
 → LF</text>
  <text x="26" y="98" fill="#e6edf3" font-size="7.5" font-family="monospace">" → "</text>
  <text x="26" y="115" fill="#8b949e" font-size="7" font-family="sans-serif">Before comment strip!</text>
  <text x="26" y="128" fill="#8b949e" font-size="7" font-family="sans-serif">Before string scan!</text>
  <text x="26" y="141" fill="#8b949e" font-size="7" font-family="sans-serif">Affects tokenisation.</text>
  <text x="26" y="158" fill="#6db33f" font-size="7" font-family="monospace">\uuuXXXX legal</text>

  <!-- Arrow -->
  <line x1="166" y1="96" x2="188" y2="96" stroke="#6db33f" stroke-width="1.5" marker-end="url(#b)"/>
  <defs><marker id="b" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>

  <!-- Pass 2 -->
  <rect x="190" y="22" width="145" height="148" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="262" y="38" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">Pass 2</text>
  <text x="262" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Line terminators</text>
  <line x1="200" y1="58" x2="325" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="200" y="72" fill="#e6edf3" font-size="7.5" font-family="monospace">CR LF → LF</text>
  <text x="200" y="85" fill="#e6edf3" font-size="7.5" font-family="monospace">CR     → LF</text>
  <text x="200" y="98" fill="#e6edf3" font-size="7.5" font-family="monospace">LF     → LF</text>

  <!-- Arrow -->
  <line x1="335" y1="96" x2="357" y2="96" stroke="#6db33f" stroke-width="1.5" marker-end="url(#b)"/>

  <!-- Pass 3 -->
  <rect x="359" y="22" width="150" height="148" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="434" y="38" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">Pass 3</text>
  <text x="434" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Tokenisation</text>
  <line x1="369" y1="58" x2="499" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="369" y="72" fill="#e6edf3" font-size="7.5" font-family="monospace">/* comments */</text>
  <text x="369" y="85" fill="#e6edf3" font-size="7.5" font-family="monospace">// stripped</text>
  <text x="369" y="98" fill="#e6edf3" font-size="7.5" font-family="monospace">identifiers</text>
  <text x="369" y="111" fill="#e6edf3" font-size="7.5" font-family="monospace">keywords</text>
  <text x="369" y="124" fill="#e6edf3" font-size="7.5" font-family="monospace">literals</text>

  <!-- Arrow -->
  <line x1="509" y1="96" x2="531" y2="96" stroke="#6db33f" stroke-width="1.5" marker-end="url(#b)"/>

  <!-- AST -->
  <rect x="533" y="22" width="155" height="148" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="38" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">Pass 4</text>
  <text x="610" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Parsing → AST → bytecode</text>
  <line x1="543" y1="58" x2="678" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="543" y="72" fill="#e6edf3" font-size="7.5" font-family="monospace">class OrderService</text>
  <text x="543" y="85" fill="#e6edf3" font-size="7.5" font-family="monospace">{ void pay() {...} }</text>
  <text x="543" y="105" fill="#8b949e" font-size="7" font-family="sans-serif">→ .class bytecode</text>
</svg>

`\u` escapes are expanded in Pass 1 — before comment stripping and string scanning — so a `
` inside a comment creates a real newline that ends the comment.

## 5. Runnable example

Scenario: an order processing system that uses Unicode identifiers and `\u` escapes to store currency symbols and order labels, demonstrating safe vs dangerous uses of Unicode escapes.

### Level 1 — Basic

```java
public class UnicodeSourceBasic {
    public static void main(String[] args) {
        System.out.println("=== Unicode source & \\u escapes ===\n");

        // \u in string literals — most common use
        String pound    = "£";   // £
        String euro     = "€";   // €
        String yen      = "¥";   // ¥
        String heart    = "♥";   // ♥
        String copyright = "©";  // ©

        System.out.println("Currency symbols via \\u escape:");
        System.out.printf("  GBP: %s  EUR: %s  JPY: %s%n", pound, euro, yen);

        // Practical use: format an order amount
        double amount = 299.99;
        System.out.printf("  Order total: %s%.2f%n", pound, amount);
        System.out.printf("  Signature:   %s 2024 ACME Corp%n", copyright);

        // Characters decoded: \u escapes become their character at compile time
        char ch = 'A';   // 'A'
        System.out.println("\nChar literal via \\u: '" + ch + "' (code point " + (int) ch + ")");

        // Verification: \u == direct char
        System.out.println("Hello!");  // Hello!

        // Code point ↔ escape
        System.out.println("\n[ Code point examples ]");
        int[] points = { 0x0048, 0x65, 0x20AC, 0x2665 };
        for (int cp : points) {
            System.out.printf("  \\u%04X = '%s' (decimal %d)%n",
                cp, String.valueOf((char) cp), cp);
        }
    }
}
```

**How to run:** `java UnicodeSourceBasic.java`

`£` becomes the `£` character at compile time — it is not a runtime conversion. The `.class` file contains the UTF-8 bytes for `£` in the string constant pool.

### Level 2 — Intermediate

Same order system: demonstrate the first-pass expansion rule with a safe example, and show the dangerous `
` in source code in a way that illustrates the issue without silently breaking compilation.

```java
public class UnicodeSourceIntermediate {
    public static void main(String[] args) {
        System.out.println("=== Unicode: first-pass expansion ===\n");

        // 1. \u in identifier — expanded in pass 1, before tokenisation
        // o = 'o', n = 'n', e = 'e' → identifier "one"
        int one = 1;    // compiles as: int one = 1;
        System.out.println("\\u escape in identifier 'one' = " + one);

        // 2. \u in a keyword — also expanded (rarely seen, never do this)
        // int = "int" — this is a real int declaration!
        int y = 42;    // compiles as: int y = 42;
        System.out.println("Keyword via \\u escape (int y) = " + y);

        // 3. " = '"' — appears inside string, closes/opens it (pass 1 first)
        // String bad = "";  ← this closes the string at ", then '; is outside!
        // The safe way to embed a double quote in a string:
        String safe = "She said \"hello\"";   // use \" escape (processed in pass 3, not pass 1)
        System.out.println("\nSafe embedded quote: " + safe);

        // 4. 
 = LF — in a comment, creates a real newline (the comment ends)
        // Demonstrate with a printed explanation rather than putting live dangerous code:
        System.out.println("\n[ The \\u000A comment trap ]");
        System.out.println("  Source:    // comment \\u000A int live = 1;");
        System.out.println("  After pass1: // comment");
        System.out.println("               int live = 1;    ← LIVE CODE, not in comment!");
        System.out.println("  This compiles! The \\u000A ended the // comment.");

        // 5. Multiple u's in escape — valid (legacy)
        String s = "\uu0041";   // \uu0041 == A == 'A'
        System.out.println("\nMultiple u's: \\uu0041 = '" + s + "'");

        // 6. \uXXXX range — only BMP (Basic Multilingual Plane, U+0000..U+FFFF)
        // Supplementary characters (U+10000+) need surrogate pairs or text blocks:
        String smile = "😀";   // U+1F600 😀 (surrogate pair)
        System.out.println("Surrogate pair for emoji: " + smile);
    }
}
```

**How to run:** `java UnicodeSourceIntermediate.java`

The `"` trap is the most dangerous: putting `"` inside a string literal looks like an escape but actually terminates the string token in Pass 1 — before the string scanner runs in Pass 3. Use `\"` for a literal double quote instead.

### Level 3 — Advanced

Same order system: write a mini Unicode-escape preprocessor that mimics Java's Pass 1, process sample source strings, and demonstrate encoding detection and safe Unicode identifier use.

```java
import java.util.*;
import java.util.regex.*;
import java.nio.charset.*;

public class UnicodeSourceAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Unicode source: pass-1 preprocessor simulation ===\n");

        // 1. Simulate Java Pass 1: expand \uXXXX escapes in a source string
        String[] sources = {
            "int \\u0078 = 5;",                    // x = 'x'
            "String s = \"\\u00A3100\";",          // £100
            "// \\u000A int hidden = 1;",           // LF in comment — dangerous
            "\\u0063\\u006C\\u0061\\u0073\\u0073 Foo {}", // class Foo {}
            "\"She said \\u0022hello\\u0022\"",    // double-quote trap
        };

        System.out.println("[ Pass 1 simulation: \\u escape expansion ]");
        for (String src : sources) {
            String expanded = expandUnicodeEscapes(src);
            System.out.printf("  IN:  %s%n", src);
            System.out.printf("  OUT: %s%n", printVisible(expanded));
            System.out.println();
        }

        // 2. Unicode identifier demo (legal identifier characters)
        System.out.println("[ Unicode identifiers ]");
        String[] unicodeIds = { "日本語Var", "café", "Ω_factor", "résumé", "αβγ" };
        for (String id : unicodeIds) {
            boolean valid = Character.isJavaIdentifierStart(id.charAt(0))
                && id.chars().skip(1).allMatch(Character::isJavaIdentifierPart);
            System.out.printf("  %-15s  %s%n", id, valid ? "valid identifier" : "invalid");
        }

        // 3. Source encoding check
        System.out.println("\n[ Source file encoding ]");
        System.out.println("  Default (JDK 18+): UTF-8");
        System.out.println("  Earlier:           platform default (risk on non-UTF-8 systems)");
        System.out.println("  Override:          javac -encoding UTF-8 MyFile.java");

        // 4. String.codePoints — handle supplementary chars correctly
        System.out.println("\n[ Supplementary characters (> U+FFFF) ]");
        String text = "Order 📦 packed";   // 📦
        System.out.println("  Text: " + text);
        System.out.println("  char length (UTF-16 units): " + text.length());
        System.out.println("  Code point count:           " + text.codePointCount(0, text.length()));
        System.out.println("  (emoji = 2 chars / 1 code point — surrogate pair)");

        // 5. Safe way to embed arbitrary Unicode in ASCII-safe source
        System.out.println("\n[ ASCII-safe source tips ]");
        System.out.println("  Currency:  \\u00A3 → £   \\u20AC → €");
        System.out.println("  Quote:     \\\"  not \\u0022 (avoid pass-1 string close)");
        System.out.println("  Newline:   \\n   not \\u000A (avoid pass-1 comment break)");
        System.out.println("  Backslash: \\\\  not \\u005C");
    }

    /** Simulate Java's Pass 1: expand \uXXXX (and \uuXXXX) escapes. */
    static String expandUnicodeEscapes(String src) {
        StringBuilder sb = new StringBuilder();
        int i = 0;
        while (i < src.length()) {
            if (i + 1 < src.length() && src.charAt(i) == '\\' && src.charAt(i+1) == 'u') {
                // consume extra u's
                int j = i + 2;
                while (j < src.length() && src.charAt(j) == 'u') j++;
                if (j + 4 <= src.length()) {
                    String hex = src.substring(j, j + 4);
                    if (hex.chars().allMatch(c -> "0123456789abcdefABCDEF".indexOf(c) >= 0)) {
                        sb.append((char) Integer.parseInt(hex, 16));
                        i = j + 4;
                        continue;
                    }
                }
            }
            sb.append(src.charAt(i++));
        }
        return sb.toString();
    }

    /** Make control characters visible in output. */
    static String printVisible(String s) {
        return s.replace("\n", "⏎\n").replace("\t", "→").replace("\r", "CR");
    }
}
```

**How to run:** `java UnicodeSourceAdvanced.java`

The `expandUnicodeEscapes` method mirrors the JLS §3.3 algorithm: scan for `\u` (with any number of extra `u` characters), parse four hex digits, and replace the escape with the corresponding Unicode character. This runs before any other processing — which is why `
` in a comment is deadly.

## 6. Walkthrough

Execution trace in `UnicodeSourceAdvanced.main`:

**`expandUnicodeEscapes("int \\u0078 = 5;")`.** The method scans character by character. When it finds `\u`, it advances past any extra `u` characters, reads the next four characters `0078`, parses them as hex (= 120 decimal = `'x'`), and emits `'x'`. Result: `"int x = 5;"`.

**`"// \\u000A int hidden = 1;"` expansion.** `
` → `'\n'` (line feed). Output: `"// \n int hidden = 1;"`. The `//` comment ends at the `\n`. The string `" int hidden = 1;"` is on a new logical line — it is live code. The Java compiler would parse this as a real `int hidden = 1;` declaration.

**`"\\u0063\\u006C...\\u0073 Foo {}"` expansion.** Produces `"class Foo {}"`. This is valid Java source — the `class` keyword was spelled with `\u` escapes. The compiler accepts it because Pass 1 runs first, then Pass 3 recognises the keyword token `class`.

**Supplementary characters.** `"📢"` (📦) is a surrogate pair: two UTF-16 code units (`char` values) that together encode U+1F4E6. `text.length()` counts `char` values; `text.codePointCount(0, text.length())` counts Unicode code points. For most text processing, you should iterate with `codePoints()` or `codePointAt()` to handle these correctly.

## 7. Gotchas & takeaways

> **Never use `
` or `` inside `//` comments.** The compiler expands them before recognising the comment boundary, creating a real newline that ends the comment. Everything after the newline is parsed as live code. This has been used in obfuscated/malicious Java code.

> **`"` inside a string literal closes the string.** Use `\"` for an embedded double quote — not `"`. Similarly, use `\\` not `\` for backslash inside strings.

- `\uXXXX` expands in **Pass 1** — before comments, before string scanning, before tokenisation.
- Multiple `u` characters are legal: `\uuXXXX` is the same as `\uXXXX` (historical).
- `\u` escapes only cover BMP (U+0000–U+FFFF); supplementary characters need surrogate pairs.
- Source file encoding defaults to UTF-8 since JDK 18; earlier versions use platform default — always compile with `-encoding UTF-8`.
- Unicode identifiers are legal; most teams restrict to ASCII via Checkstyle to avoid editor/diff tool issues.
- For currency/special chars in string literals, `\u` escapes are safe — just avoid `
`, ``, `"`, `'`, `\` where the literal character or a standard escape (`\n`, `\"`, `\\`) would be clearer.
