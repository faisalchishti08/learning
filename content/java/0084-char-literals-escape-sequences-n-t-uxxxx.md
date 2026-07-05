---
card: java
gi: 84
slug: char-literals-escape-sequences-n-t-uxxxx
title: char literals & escape sequences (\n \t \\ \' \" \uXXXX)
---

## 1. What it is

A `char` literal is a single character enclosed in single quotes: `'A'`, `'7'`, `'€'`. When the character cannot be typed directly — because it is invisible, conflicts with syntax, or falls outside the basic keyboard set — you use an escape sequence: a backslash followed by one or more characters that together represent the intended value.

Java defines these standard escape sequences:

| Escape | Meaning              | Decimal |
|--------|----------------------|---------|
| `\n`   | newline (LF)         | 10      |
| `\t`   | horizontal tab       | 9       |
| `\r`   | carriage return (CR) | 13      |
| `\b`   | backspace            | 8       |
| `\f`   | form feed            | 12      |
| `\'`   | single quote         | 39      |
| `\"`   | double quote         | 34      |
| `\\`   | backslash            | 92      |
| `\0`   | NUL character        | 0       |
| `\uXXXX` | Unicode code unit (4 hex digits) | 0–65535 |

Escape sequences are also valid inside `String` literals (double quotes), not just `char` literals.

## 2. Why & when

Escape sequences are needed in three situations:
- **Unprintable control characters** — you cannot place a literal newline inside a `char` or `String` literal (it would be a syntax error); you write `'\n'` instead.
- **Syntactic conflicts** — `'\''` is necessary because a bare `'` inside single quotes would end the literal. Likewise `'\\'` for a literal backslash.
- **Unicode characters** — `'€'` embeds the Euro sign regardless of the source file's encoding, which is important for portability and cross-platform builds.

The `\uXXXX` escape is processed by the Java preprocessor before compilation, meaning it can appear even in comments or identifiers (a subtle trap).

## 3. Core concept

```java
// ---- Standard escape sequences ----
char newline   = '\n';    // line feed (LF), code point 10
char tab       = '\t';    // horizontal tab, code point 9
char cr        = '\r';    // carriage return, code point 13
char backslash = '\\';    // literal \
char squote    = '\'';    // literal '
char dquote    = '\"';    // literal " (also valid as just '"' in char literal)

// ---- Unicode escape ----
char euro   = '€';   // €
char sigma  = 'Σ';   // Σ (Greek capital sigma)
char snowman= '☃';   // ☃

// ---- NUL character ----
char nul = '\0';          // code point 0 — default field value
System.out.println((int) nul);   // 0

// ---- Escape sequences in Strings ----
String path    = "C:\\Users\\Alice\\file.txt";
String csv     = "name\tage\tcity\nAlice\t30\tNYC";
String message = "He said, \"Hello!\"";
String hello   = "café";   // café
System.out.println(path);
System.out.println(csv);
System.out.println(message);
System.out.println(hello);   // café

// ---- \uXXXX is preprocessed before parsing ----
// The following is legal — A is 'A' (the letter)
char A = 'A';   // variable named A
System.out.println(A);   // A

// ---- Octal escapes are also legal (rarely used) ----
char octalA = '\101';    // octal 101 = decimal 65 = 'A'
System.out.println(octalA);   // A

// ---- Char literal in arithmetic ----
System.out.println('A' + 1);    // 66 (int)  — NOT 'B'
System.out.println((char)('A' + 1));  // B    — cast back to char
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="char literal anatomy with escape sequences table and Unicode escape processing stages">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <!-- Token anatomy row -->
  <rect x="16" y="18" width="668" height="52" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">char literal anatomy — three forms</text>

  <!-- plain char -->
  <rect x="36" y="38" width="80" height="26" rx="3" fill="#6db33f" opacity="0.75"/>
  <text x="76" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">'A'</text>

  <!-- escape -->
  <rect x="136" y="38" width="90" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="181" y="55" fill="#0d1117" font-size="13" font-weight="bold" text-anchor="middle" font-family="monospace">'\n'</text>

  <!-- unicode escape -->
  <rect x="246" y="38" width="130" height="26" rx="3" fill="#8b949e" opacity="0.5"/>
  <text x="311" y="55" fill="#e6edf3" font-size="11" font-weight="bold" text-anchor="middle" font-family="monospace">'€'</text>

  <!-- labels -->
  <text x="76"  y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">plain char</text>
  <text x="181" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">escape seq</text>
  <text x="311" y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Unicode escape → €</text>

  <!-- Unicode escape stages -->
  <text x="490" y="43" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">\u preprocessing stages:</text>
  <text x="490" y="56" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">source → € → € → char 0x20AC</text>
  <text x="490" y="69" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(runs BEFORE tokenisation)</text>

  <!-- Escape table -->
  <rect x="16" y="90" width="350" height="76" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="191" y="106" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Escape sequences</text>
  <line x1="26" y1="112" x2="356" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26"  y="126" fill="#e6edf3" font-size="7.5" font-family="monospace">\n newline   \t tab    \r CR</text>
  <text x="26"  y="139" fill="#e6edf3" font-size="7.5" font-family="monospace">\\ backslash \' quote  \" dquote</text>
  <text x="26"  y="152" fill="#e6edf3" font-size="7.5" font-family="monospace">\0 NUL      \b backsp  \f formfeed</text>
  <text x="26"  y="165" fill="#8b949e" font-size="7.5" font-family="monospace">\uXXXX Unicode (4 hex digits)</text>

  <!-- gotcha box -->
  <rect x="378" y="90" width="306" height="76" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="531" y="106" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Key gotchas</text>
  <line x1="388" y1="112" x2="674" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="388" y="126" fill="#8b949e" font-size="7.5" font-family="monospace">'\0' ≠ '0'  (NUL vs digit 0)</text>
  <text x="388" y="139" fill="#8b949e" font-size="7.5" font-family="monospace">'\n' in path → newline, not \n</text>
  <text x="388" y="152" fill="#6db33f" font-size="7.5" font-family="monospace">\uXXXX active in comments too</text>
  <text x="388" y="165" fill="#8b949e" font-size="7.5" font-family="monospace">text blocks: """ for multi-line</text>
</svg>

Java has eight single-character escape sequences plus the four-hex-digit `\uXXXX` Unicode escape; `\u` is processed before tokenisation, making it active everywhere — including comments.

## 5. Runnable example

Scenario: a plain-text report formatter that builds structured output using escape sequences — tab-separated columns, newline-separated rows, and quoted string fields. The example grows from basic escape usage, to a CSV encoder that escapes special characters, to a tokeniser that detects and classifies escape sequences within input strings.

### Level 1 — Basic

```java
public class EscapeBasic {
    public static void main(String[] args) {
        // Tab-aligned table using \t and \n in string literals
        String header = "Name\t\tAge\tCity";
        String row1   = "Alice\t\t30\tNew York";
        String row2   = "Bob\t\t25\tLondon";
        String row3   = "Café owner\t42\tParis";   // Unicode in row

        System.out.println(header);
        System.out.println("-".repeat(32));
        System.out.println(row1);
        System.out.println(row2);
        System.out.println(row3);

        // Escaping quotes and backslashes
        System.out.println();
        System.out.println("She said, \"Bonjour!\"");
        System.out.println("Path: C:\\Program Files\\app");
        System.out.println("Newline literal: \\n  Tab literal: \\t");

        // char literals
        char tab       = '\t';
        char newline   = '\n';
        char backslash = '\\';
        System.out.printf("tab=U+%04X  newline=U+%04X  backslash=U+%04X%n",
            (int) tab, (int) newline, (int) backslash);
    }
}
```

**How to run:** `java EscapeBasic.java`

`\t` inside a `String` literal inserts a real tab character, which the terminal renders as whitespace alignment. `é` is the é (e with acute), and `\t\t` inserts two tabs to align the wider name. Printing `\\n` (two characters: `\` then `n`) displays the literal text `\n`, not a newline — the double backslash `\\` is the escape for a single backslash character.

### Level 2 — Intermediate

Same report formatter: write a CSV encoder that correctly escapes double quotes, commas, and newlines within field values.

```java
public class EscapeIntermediate {

    // CSV-encode a single field value per RFC 4180
    static String csvField(String value) {
        // Fields containing quote, comma, or newline must be quoted
        if (value.contains("\"") || value.contains(",") || value.contains("\n")) {
            // Double up any embedded quotes
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }

    static String csvRow(String... fields) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < fields.length; i++) {
            if (i > 0) sb.append(',');
            sb.append(csvField(fields[i]));
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println("=== CSV output ===");

        // Normal row
        System.out.println(csvRow("Alice", "30", "New York"));

        // Field with comma
        System.out.println(csvRow("Bob", "25", "London, UK"));

        // Field with double quote
        System.out.println(csvRow("Carol \"C\" Smith", "28", "Paris"));

        // Field with embedded newline
        System.out.println(csvRow("Dave", "22", "Line1\nLine2"));

        // Field with backslash (no special CSV meaning, but common source of confusion)
        System.out.println(csvRow("Eve", "35", "C:\\Users\\Eve"));

        System.out.println();
        System.out.println("=== Escape code points ===");
        char[] escapes = {'\n', '\t', '\r', '\\', '\'', '\"', '\0'};
        String[] names = {"\\n", "\\t", "\\r", "\\\\", "\\'", "\\\"", "\\0"};
        for (int i = 0; i < escapes.length; i++) {
            System.out.printf("'%s'  → U+%04X  = %3d%n",
                names[i], (int) escapes[i], (int) escapes[i]);
        }
    }
}
```

**How to run:** `java EscapeIntermediate.java`

`value.contains("\n")` tests for a literal newline character inside the string value — `"\n"` in Java source is a `String` containing one character (code point 10), not two characters backslash-n. `value.replace("\"", "\"\"")` doubles up each embedded double-quote character, which is the RFC 4180 CSV escaping rule. The escapes table printed at the end confirms the mapping from escape sequence to code point — `'\0'` is NUL (0), not the digit character `'0'` (48).

### Level 3 — Advanced

Same formatter: build a string escape analyser that scans a string, identifies each character, and classifies it as a printable character, a standard escape, or a Unicode escape — useful for debugging strings containing invisible control characters.

```java
public class EscapeAdvanced {

    // Return the Java source representation of a char
    static String javaEscape(char c) {
        return switch (c) {
            case '\n' -> "\\n";
            case '\t' -> "\\t";
            case '\r' -> "\\r";
            case '\b' -> "\\b";
            case '\f' -> "\\f";
            case '\\' -> "\\\\";
            case '\'' -> "\\'";
            case '"'  -> "\\\"";
            case '\0' -> "\\0";
            default -> {
                if (c < 0x20 || c > 0x7E) {
                    yield String.format("\\u%04X", (int) c);
                }
                yield String.valueOf(c);
            }
        };
    }

    static void analyseString(String label, String s) {
        System.out.printf("%-12s  len=%d%n", label, s.length());
        System.out.printf("  %-6s  %-8s  %-10s  %s%n",
            "Index", "Char", "Decimal", "Java literal");
        System.out.println("  " + "-".repeat(44));
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            System.out.printf("  %-6d  %-8s  %-10d  %s%n",
                i,
                (c < 0x20 || c > 0x7E) ? "(ctrl)" : "'" + c + "'",
                (int) c,
                "'" + javaEscape(c) + "'");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        // String with control chars, Unicode, and quotes
        String s1 = "Hi\tWorld\n";          // tab + newline
        String s2 = "café";            // Unicode é
        String s3 = "She said, \"Hello\"";  // embedded double quotes
        String s4 = "C:\\path\\file.txt";   // Windows path with backslashes

        analyseString("tab+newline", s1);
        analyseString("unicode-e",  s2);
        analyseString("dquotes",    s3);
        analyseString("win-path",   s4);
    }
}
```

**How to run:** `java EscapeAdvanced.java`

`javaEscape(char c)` is the inverse of the Java parser's escape processing — it converts each character back to its source-code literal form. The `switch` expression with a `default` branch handles all remaining characters: code points below `0x20` (control characters) and above `0x7E` (non-ASCII) are formatted as `\uXXXX`. Printable ASCII characters are returned as-is. This kind of analyser is extremely useful when debugging data that arrives from external sources (files, sockets, databases) and may contain invisible or unexpected control characters that cause silent parsing failures.

## 6. Walkthrough

Execution trace through `EscapeAdvanced.main` for `analyseString("tab+newline", "Hi\tWorld\n")`:

**String construction.** `"Hi\tWorld\n"` is parsed at compile time. The Java compiler replaces `\t` with the single character `char(9)` (tab) and `\n` with `char(10)` (newline). The resulting `String` has 10 characters: `H`, `i`, `\t`, `W`, `o`, `r`, `l`, `d`, `\n` — 9 chars. Wait — let's count: H(0), i(1), TAB(2), W(3), o(4), r(5), l(6), d(7), LF(8) — 9 characters. `s.length()` = 9.

**Per-character loop.** For `i=0`: `c = 'H'` (72). `c >= 0x20 && c <= 0x7E` → printable. `javaEscape('H')` hits the `default` branch → `String.valueOf('H')` = `"H"`. For `i=2`: `c = '\t'` (9). `javaEscape('\t')` hits the `case '\t'` branch → `"\\t"` (the two-character string backslash-t, which prints as `\t`). For `i=8`: `c = '\n'` (10). `javaEscape('\n')` → `"\\n"`.

**Unicode path.** For `"café"` (length 4): index 3 holds `char(0xE9)` = 233. `c > 0x7E` → `yield String.format("\\u%04X", 0xE9)` = `"\\u00E9"`. This round-trips: the analyser shows exactly the escape that would reproduce the original character in Java source code.

```
"Hi\tWorld\n"  at compile time:
  Source bytes: H  i  \  t  W  o  r  l  d  \  n
                         ↑                  ↑
                  compiler: → char(9)     char(10)

  Runtime string: [H][i][⇥][W][o][r][l][d][↵]
                                 (length = 9)

javaEscape analysis:
  'H'  → printable   → 'H'
  '\t' → case '\t'   → "\\t"   (displayed as \t)
  '\n' → case '\n'   → "\\n"   (displayed as \n)
```

## 7. Gotchas & takeaways

> **`\uXXXX` is processed by the Java preprocessor before parsing — it is active in comments and identifiers.** A comment containing `/` can inadvertently close a block comment (`/` = `/`). This is a well-known Java quirk with almost no practical use; avoid embedding `\uXXXX` sequences in comments.

> **`'\0'` is NUL (code point 0), not the digit `'0'` (code point 48).** They look similar in code but are completely different characters. `char` arrays and fields default to `'\0'`; testing `c == '0'` against an unset `char` will always be `false`.

- Java escape sequences: `\n` (LF), `\t` (tab), `\r` (CR), `\\` (backslash), `\'` (single quote), `\"` (double quote), `\0` (NUL), `\b` (backspace), `\f` (form feed).
- `\uXXXX` (four hex digits) inserts any Unicode BMP code point; it is processed before tokenisation and is valid everywhere in source code.
- Escape sequences work in both `char` literals (`'\n'`) and `String` literals (`"\n"`).
- To display a literal backslash, write `\\`; to display `\n` as text, write `"\\n"`.
- For multi-line strings with fewer escaping headaches, use Java 15+ text blocks (`"""..."""`).
- `char` arithmetic: `'A' + 1` gives `int` 66; cast back to `char` with `(char)('A' + 1)` to get `'B'`.
