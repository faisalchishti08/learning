---
card: java
gi: 66
slug: whitespace-line-terminators
title: Whitespace & line terminators
---

## 1. What it is

**Whitespace** in Java source code is any sequence of space characters, tab characters, form feeds, and line terminators that separates tokens but carries no semantic meaning. The compiler discards all whitespace between tokens.

Java recognises three **line terminators**:
- LF (`\n`, U+000A) — Unix/macOS
- CR (`\r`, U+000D) — old Mac (pre-OS X)
- CR+LF (`\r\n`) — Windows

```java
// All of these are identical after whitespace stripping:
int x=1;
int x = 1;
int   x   =   1  ;
int
    x
    =
    1
    ;
```

## 2. Why & when

Whitespace matters for:
- **Readability**: the style guide says how much to use (indent 4 spaces, space after comma, blank line between methods).
- **String literals and text blocks**: whitespace INSIDE a string is preserved and meaningful.
- **`
` / `` escape trap**: Unicode line-terminator escapes in source are expanded in Pass 1 — before tokenisation — which can accidentally split a `//` comment (see gi 65).
- **Text blocks** (JDK 15+): trailing whitespace on each line is stripped by the compiler unless you use `\s` to anchor it.

## 3. Core concept

```java
// ---- Token separation ----
// Whitespace is required between adjacent identifier/keyword tokens:
// intx = 5;        ✗ — 'intx' is parsed as one identifier
// int x = 5;       ✓ — space separates keyword 'int' from identifier 'x'

// Operators and punctuation don't need surrounding whitespace:
int x=1+2;           // legal; style guides require spaces anyway

// ---- Line terminators ----
// LF   = \n   = Unix line ending
// CR   = \r   = old Mac line ending
// CR+LF= \r\n = Windows line ending
// javac normalises all three to LF in Pass 2 (after Unicode escape expansion)

// ---- Inside string literals — whitespace is PRESERVED ----
String table = "Name    Amount\n" +
               "Alice   £100.00\n" +
               "Bob     £ 50.00\n";
System.out.print(table);

// ---- Text block (JDK 15+) — indentation stripping ----
String json = """
        {
          "orderId": "ORD-001",
          "amount":   299.99
        }
        """;
// Common leading whitespace (8 spaces — the indent of the closing """) is stripped.
// Result is a clean 2-space-indented JSON string.

// ---- Trailing whitespace in text blocks ----
String line = """
        value:   \s
        """;
// The \s anchor preserves the trailing space before it;
// without \s, trailing spaces are stripped by the compiler.

// ---- Form feed ----
// '\f' (U+000C) is also whitespace in Java source.
// Rare in modern code; used in old printer-era code to separate logical sections.
```

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Whitespace in Java: source tokens separated by whitespace, line terminators normalised, text block indentation stripped">
  <rect x="8" y="8" width="684" height="164" rx="8" fill="#0d1117"/>

  <!-- Source -->
  <rect x="16" y="22" width="260" height="132" rx="5" fill="#1c2430"/>
  <text x="146" y="36" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Source (whitespace visible)</text>
  <text x="26" y="52" fill="#79c0ff" font-size="8" font-family="monospace">int</text>
  <text x="55" y="52" fill="#e6edf3" font-size="8" font-family="monospace"> · </text>
  <text x="72" y="52" fill="#e6edf3" font-size="8" font-family="monospace">x</text>
  <text x="82" y="52" fill="#e6edf3" font-size="8" font-family="monospace"> · </text>
  <text x="98" y="52" fill="#e6edf3" font-size="8" font-family="monospace">=</text>
  <text x="108" y="52" fill="#e6edf3" font-size="8" font-family="monospace"> · </text>
  <text x="124" y="52" fill="#6db33f" font-size="8" font-family="monospace">5</text>
  <text x="134" y="52" fill="#e6edf3" font-size="8" font-family="monospace"> · </text>
  <text x="148" y="52" fill="#e6edf3" font-size="8" font-family="monospace">;</text>
  <text x="26" y="68" fill="#8b949e" font-size="7" font-family="sans-serif">· = whitespace (spaces)</text>
  <line x1="26" y1="76" x2="266" y2="76" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="90" fill="#8b949e" font-size="7.5" font-family="sans-serif">Line terminators (all normalised → LF):</text>
  <text x="26" y="104" fill="#e6edf3" font-size="7.5" font-family="monospace">\n     = LF   (Unix/macOS)</text>
  <text x="26" y="116" fill="#e6edf3" font-size="7.5" font-family="monospace">\r     = CR   (old Mac)</text>
  <text x="26" y="128" fill="#e6edf3" font-size="7.5" font-family="monospace">\r\n   = CRLF (Windows)</text>
  <text x="26" y="142" fill="#8b949e" font-size="7" font-family="sans-serif">All become LF in Pass 2</text>

  <!-- Arrow -->
  <line x1="278" y1="88" x2="308" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#c)"/>
  <defs><marker id="c" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>
  <text x="293" y="82" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">stripped</text>

  <!-- Tokens -->
  <rect x="310" y="22" width="180" height="132" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="400" y="36" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">After stripping</text>
  <text x="320" y="52" fill="#79c0ff" font-size="8" font-family="monospace">int</text>
  <text x="342" y="52" fill="#e6edf3" font-size="8" font-family="monospace">x = </text>
  <text x="370" y="52" fill="#6db33f" font-size="8" font-family="monospace">5</text>
  <text x="380" y="52" fill="#e6edf3" font-size="8" font-family="monospace">;</text>
  <text x="320" y="70" fill="#8b949e" font-size="7" font-family="sans-serif">Tokens: int, x, =, 5, ;</text>
  <line x1="320" y1="78" x2="480" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="320" y="92" fill="#8b949e" font-size="7" font-family="sans-serif">EXCEPTION: whitespace inside</text>
  <text x="320" y="104" fill="#8b949e" font-size="7" font-family="sans-serif">string literals is PRESERVED.</text>
  <text x="320" y="116" fill="#8b949e" font-size="7" font-family="sans-serif">Text block: common leading</text>
  <text x="320" y="128" fill="#8b949e" font-size="7" font-family="sans-serif">whitespace stripped by compiler.</text>

  <!-- Tip box -->
  <rect x="500" y="22" width="182" height="132" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="591" y="36" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Style conventions</text>
  <text x="510" y="52" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Indent: 4 spaces (not tab)</text>
  <text x="510" y="64" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Space after comma: yes</text>
  <text x="510" y="76" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Space around operators: yes</text>
  <text x="510" y="88" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Blank line between methods</text>
  <text x="510" y="100" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• No trailing whitespace</text>
  <text x="510" y="112" fill="#e6edf3" font-size="7.5" font-family="sans-serif">• Max line length: 100–120</text>
  <text x="510" y="128" fill="#8b949e" font-size="7" font-family="sans-serif">Enforced by: Google Java Format</text>
  <text x="510" y="140" fill="#8b949e" font-size="7" font-family="sans-serif">Spotless, Checkstyle</text>
</svg>

Whitespace separates tokens but carries no semantic weight — except inside string literals, where every space and newline is preserved.

## 5. Runnable example

Scenario: an order report formatter that uses whitespace deliberately — aligned table output, text blocks for JSON payloads, and a whitespace inspector that shows exactly which whitespace characters appear in a string.

### Level 1 — Basic

```java
public class WhitespaceBasic {
    public static void main(String[] args) {
        System.out.println("=== Whitespace & line terminators ===\n");

        // Whitespace between tokens — entirely up to style
        int orderCount=3;            // legal — no spaces
        int itemCount   =   10;      // legal — extra spaces
        System.out.println("orderCount: " + orderCount + "  items: " + itemCount);

        // Whitespace inside string literals — PRESERVED
        String header = "Order ID     Customer       Amount";
        String row1   = "ORD-001      Alice          £299.99";
        String row2   = "ORD-002      Bob            £ 50.00";
        System.out.println("\nFormatted table (whitespace preserved in strings):");
        System.out.println(header);
        System.out.println("-".repeat(header.length()));
        System.out.println(row1);
        System.out.println(row2);

        // Line terminator in string
        String twoLines = "Line 1\nLine 2";   // \n is a newline
        System.out.println("\nTwo-line string:\n" + twoLines);

        // Tab character
        String tabbed = "Name:\tAlice";
        System.out.println("\nTab in string: " + tabbed);
    }
}
```

**How to run:** `java WhitespaceBasic.java`

Spaces inside the string literals `row1` and `row2` are part of the string value — they are not stripped. The `\n` in `twoLines` is an escape sequence representing a line-feed character, embedded in the string constant.

### Level 2 — Intermediate

Same order report: use a text block (JDK 15+) for a JSON payload and demonstrate indentation stripping, trailing-whitespace handling with `\s`, and platform line-ending differences.

```java
public class WhitespaceIntermediate {
    public static void main(String[] args) {
        System.out.println("=== Text blocks & line terminators ===\n");

        // 1. Text block — common leading whitespace is stripped
        String json = """
                {
                  "orderId": "ORD-001",
                  "customer": "Alice",
                  "amount": 299.99
                }
                """;
        System.out.println("Text block JSON:");
        System.out.println(json);

        // 2. Strip amount — how many spaces were removed?
        String raw = """
        indented content""";      // indented 8 spaces in source
        System.out.println("Text block indent stripped: '" + raw + "'");

        // 3. Trailing whitespace with \s anchor
        String padded = """
                value:   \s
                """;
        // Without \s, trailing spaces after "value:" are stripped.
        // With \s, the space before \s is kept.
        System.out.println("Padded line length: " + padded.stripTrailing().length() + " chars");

        // 4. Line terminator normalisation
        System.out.println("\n[ Line terminator normalisation ]");
        String crlf = "line1\r\nline2";      // Windows-style
        String lf   = "line1\nline2";        // Unix-style
        String[] crlfLines = crlf.split("\\r?\\n");  // handles both
        String[] lfLines   = lf.split("\\r?\\n");
        System.out.println("CRLF line count: " + crlfLines.length);  // 2
        System.out.println("LF   line count: " + lfLines.length);    // 2

        // 5. System line separator
        System.out.println("\n[ System.lineSeparator() ]");
        String sep = System.lineSeparator();
        System.out.printf("  Platform line separator: %s (%d bytes)%n",
            sep.equals("\r\n") ? "CRLF" : sep.equals("\n") ? "LF" : "CR",
            sep.length());
        System.out.println("  Use System.lineSeparator() for cross-platform output files.");
    }
}
```

**How to run:** `java WhitespaceIntermediate.java`

The closing `"""` of a text block sets the indentation baseline: the compiler measures the column of `"""` and strips that many spaces from every line. Moving `"""` one column to the left includes one more space in the output.

### Level 3 — Advanced

Same order report: build a whitespace inspector that analyses strings character-by-character, counts line terminators, detects mixed indentation (tabs vs spaces), and formats an aligned table using printf — demonstrating that whitespace control is precise and intentional.

```java
import java.util.*;

public class WhitespaceAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Whitespace inspector + table formatter ===\n");

        // 1. Whitespace character inspector
        System.out.println("[ Whitespace character inventory ]");
        String sample = "Order\tAlice\r\nShipped\nPending\r";
        inspectWhitespace(sample);

        // 2. Mixed indentation detector
        System.out.println("\n[ Mixed indentation detector ]");
        String[] codeLines = {
            "    void process() {",       // 4 spaces — OK
            "\t    int x = 1;",           // tab + spaces — MIXED
            "    }",                       // 4 spaces — OK
            "\tvoid other() {",            // tab only
        };
        for (String line : codeLines) {
            boolean hasTab    = line.contains("\t");
            boolean hasSpace  = !line.stripLeading().equals(line.stripLeading().stripLeading())
                              || line.startsWith(" ");
            String indent = line.isEmpty() ? "" : (hasTab && hasSpace) ? "MIXED !" :
                            hasTab ? "tab" : hasSpace ? "space" : "none";
            System.out.printf("  %-40s → %s%n",
                line.replace("\t", "→").replace(" ", "·"), indent);
        }

        // 3. Aligned order table using printf (whitespace-controlled output)
        System.out.println("\n[ Order report — printf-aligned ]");
        record Order(String id, String customer, double amount, String status) {}
        List<Order> orders = List.of(
            new Order("ORD-001", "Alice Marchetti",  299.99, "SHIPPED"),
            new Order("ORD-002", "Bob",               50.00, "PENDING"),
            new Order("ORD-003", "Carol De Souza",  1200.00, "CONFIRMED"),
            new Order("ORD-004", "D",                  5.50, "CANCELLED")
        );
        String fmt = "  %-10s  %-18s  %8.2f  %-10s%n";
        System.out.printf("  %-10s  %-18s  %8s  %-10s%n",
            "Order ID", "Customer", "Amount(£)", "Status");
        System.out.println("  " + "-".repeat(54));
        for (Order o : orders)
            System.out.printf(fmt, o.id(), o.customer(), o.amount(), o.status());

        // 4. String.isBlank vs String.isEmpty
        System.out.println("\n[ isBlank vs isEmpty ]");
        String[] tests = { "", " ", "\t", "\n", "  x  " };
        for (String t : tests) {
            System.out.printf("  %-8s  isEmpty=%-6b  isBlank=%b%n",
                "'" + t.replace("\t","\\t").replace("\n","\\n") + "'",
                t.isEmpty(), t.isBlank());
        }
    }

    static void inspectWhitespace(String s) {
        int spaces=0, tabs=0, lf=0, cr=0, crlf=0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '\r' && i+1 < s.length() && s.charAt(i+1) == '\n') { crlf++; i++; }
            else if (c == '\r') cr++;
            else if (c == '\n') lf++;
            else if (c == '\t') tabs++;
            else if (c == ' ')  spaces++;
        }
        System.out.printf("  Input: %s%n", s.replace("\r\n","⏎").replace("\n","↵").replace("\r","←").replace("\t","→"));
        System.out.printf("  Spaces=%d  Tabs=%d  LF=%d  CR=%d  CRLF=%d%n",
            spaces, tabs, lf, cr, crlf);
    }
}
```

**How to run:** `java WhitespaceAdvanced.java`

`String.isBlank()` (JDK 11+) returns `true` for any string containing only whitespace characters (space, tab, newline, etc.) — including strings that `isEmpty()` returns `false` for. Use `isBlank()` to validate user input, `isEmpty()` to test for a zero-length string.

## 6. Walkthrough

Execution trace in `WhitespaceAdvanced.main`:

**`inspectWhitespace(sample)`.** The method scans `"Order\tAlice\r\nShipped\nPending\r"` one character at a time. When it sees `\r` at position after `Alice`, it looks ahead one character: the next is `\n` — a CR+LF pair. `crlf` is incremented and `i` is advanced by one extra to skip the `\n`. The bare `\r` at the end of `Pending\r` is a lone carriage return — `cr++`.

**Mixed indentation.** `"\t    int x = 1;"` starts with a tab then four spaces. `hasTab = line.contains("\t")` — true. `hasSpace` checks if `stripLeading()` on the raw line strips anything that `stripLeading()` again would also strip — since the line starts with `\t`, `stripLeading()` removes it, leaving `"    int x = 1;"` which still starts with spaces. `hasTab && hasSpace` → `"MIXED !"`.

**`printf` alignment.** `"%-10s"` left-aligns in a 10-character field. `"%8.2f"` right-aligns a floating-point number in an 8-character field with 2 decimal places. The whitespace is inserted by `printf` to fill the specified width — this is formatting, not source whitespace, but it demonstrates that whitespace in output strings is meaningful and precise.

**`isBlank` vs `isEmpty`.** `""` → both true. `" "` → isEmpty=false, isBlank=true. `"\t"` → isEmpty=false, isBlank=true. This distinction is critical for form validation: `"  "` (spaces only) should be treated the same as empty in most UI contexts — use `isBlank()`.

## 7. Gotchas & takeaways

> **Text block trailing whitespace is silently stripped.** If your text block needs to end a line with spaces (e.g., for a fixed-width protocol), use `\s` to anchor the trailing space: `"value:   \s"`. Without `\s`, the compiler strips the trailing spaces and you will send a shorter line than expected.

> **`System.lineSeparator()` ≠ `"\n"` on Windows.** If you write files with `"\n"` hardcoded on a Windows system, some tools will display the file without line breaks. Use `System.lineSeparator()` or `PrintWriter` (which automatically uses the platform separator) for text output files.

- Whitespace between tokens is ignored by the compiler — style is a human concern.
- Inside string literals and text blocks, whitespace is part of the value.
- Line terminators: LF (`\n`), CR (`\r`), CR+LF (`\r\n`) — all normalised to LF by javac in Pass 2.
- `String.isBlank()` — whitespace-only returns true; `String.isEmpty()` — zero-length only.
- `String.stripLeading()` / `stripTrailing()` / `strip()` use Unicode whitespace definition (broader than `trim()`).
- Text block indentation is stripped based on the column of the closing `"""`.
- Mixed tabs+spaces in indentation causes inconsistent display across editors — pick one and enforce via Checkstyle or `.editorconfig`.
