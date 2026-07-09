---
card: java
gi: 648
slug: string-indent-int
title: String.indent(int)
---

## 1. What it is

`String.indent(int n)`, added in **Java 12**, adjusts the indentation of every line in a string by `n` spaces. Passing a **positive** number prepends `n` spaces to the start of each line; passing a **negative** number removes up to `n` leading whitespace characters from each line (never going past the first non-whitespace character). It also **normalizes line endings** to `\n` and guarantees the result ends with a trailing newline. It works on multi-line strings by splitting on line terminators, adjusting each line, and rejoining — you never have to hand-roll that splitting logic yourself.

## 2. Why & when

Before `indent()`, shifting every line of a block of text — say, to nest a code snippet inside another one, or to visually indent a multi-line report — meant writing a loop that split on `\n`, prepended spaces to each piece, and rejoined with `\n`, carefully handling the trailing-newline edge case yourself. That's a small amount of code, but it's easy to get subtly wrong (missing the last line, double newlines, inconsistent line-ending handling across platforms). `indent()` does this exact, common operation as a single built-in method call. Reach for it whenever you're generating formatted text — pretty-printers, code generators, nested log output, or CLI help text — and need consistent indentation without writing your own line-splitting code.

## 3. Core concept

```java
String text = "line one\nline two\nline three";

String indented = text.indent(4);
// "    line one\n    line two\n    line three\n"
//  ^^^^ 4 spaces added to EVERY line, plus a trailing \n

String already = "   already indented\n   with spaces";
String outdented = already.indent(-2);
// removes up to 2 leading spaces per line (won't go negative / past non-whitespace)
```

Positive `n` = add spaces; negative `n` = remove up to that many spaces; the method always normalizes to `\n` line endings and appends one at the end if missing.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="indent(4) adds 4 spaces to each line; indent(-2) removes up to 2 leading spaces from each line">
  <rect x="10" y="10" width="270" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="145" y="30" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">indent(4) — positive</text>
  <text x="20" y="55" fill="#8b949e" font-size="10" font-family="monospace">"line one</text>
  <text x="20" y="70" fill="#8b949e" font-size="10" font-family="monospace">line two"</text>
  <text x="145" y="95" fill="#79c0ff" font-size="14" text-anchor="middle" font-family="sans-serif">↓ +4 spaces/line</text>
  <text x="20" y="120" fill="#e6edf3" font-size="10" font-family="monospace">"    line one</text>
  <text x="20" y="135" fill="#e6edf3" font-size="10" font-family="monospace">    line two"</text>
  <text x="20" y="160" fill="#8b949e" font-size="9" font-family="sans-serif">+ trailing \n guaranteed</text>

  <rect x="310" y="10" width="280" height="170" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="450" y="30" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">indent(-2) — negative</text>
  <text x="320" y="55" fill="#8b949e" font-size="10" font-family="monospace">"   already indented</text>
  <text x="320" y="70" fill="#8b949e" font-size="10" font-family="monospace">   with spaces"</text>
  <text x="450" y="95" fill="#f85149" font-size="14" text-anchor="middle" font-family="sans-serif">↓ −2 leading spaces</text>
  <text x="320" y="120" fill="#e6edf3" font-size="10" font-family="monospace">" already indented</text>
  <text x="320" y="135" fill="#e6edf3" font-size="10" font-family="monospace"> with spaces"</text>
  <text x="320" y="160" fill="#8b949e" font-size="9" font-family="sans-serif">never strips past non-whitespace</text>
</svg>

`indent()` shifts every line the same amount, in either direction, and always normalizes line endings.

## 5. Runnable example

Scenario: rendering a small block of "generated code" text with progressively more realistic indentation needs — first a flat indent, then nesting inside a wrapper, then a generic pretty-printer that indents arbitrarily nested blocks.

### Level 1 — Basic

```java
// File: IndentBasic.java
public class IndentBasic {
    public static void main(String[] args) {
        String block = "System.out.println(\"hi\");\nSystem.out.println(\"bye\");";

        System.out.println("Original:");
        System.out.println(block);

        System.out.println("\nIndented by 4:");
        System.out.print(block.indent(4));
    }
}
```

**How to run:** `java IndentBasic.java` (JDK 17+; works from Java 12 onward too).

Expected output:
```
Original:
System.out.println("hi");
System.out.println("bye");

Indented by 4:
    System.out.println("hi");
    System.out.println("bye");
```

### Level 2 — Intermediate

```java
// File: IndentNested.java
public class IndentNested {
    static String wrapInMethod(String body) {
        return "void run() {\n" + body.indent(4) + "}\n";
    }

    public static void main(String[] args) {
        String body = "int x = 1;\nint y = 2;\nSystem.out.println(x + y);";
        String method = wrapInMethod(body);
        System.out.print(method);
    }
}
```

**How to run:** `java IndentNested.java`

Expected output:
```
void run() {
    int x = 1;
    int y = 2;
    System.out.println(x + y);
}
```

`wrapInMethod` uses `indent(4)` to push the whole `body` one level in before wrapping it in braces — no manual `\n` splitting required, and the trailing newline from `indent()` lines up the closing `}` on its own line automatically.

### Level 3 — Advanced

```java
// File: IndentGenerator.java
import java.util.List;

public class IndentGenerator {
    // Recursively renders nested blocks, each level indented 2 more spaces than its parent.
    static String render(String name, List<String> lines, List<?> children) {
        StringBuilder sb = new StringBuilder();
        sb.append(name).append(" {\n");
        for (String line : lines) {
            sb.append(line).append("\n");
        }
        for (Object child : children) {
            sb.append(child.toString());
        }
        sb.append("}\n");
        return sb.toString().indent(0); // normalize line endings, keep this level flat
    }

    public static void main(String[] args) {
        String inner = render("inner", List.of("doWork();"), List.of());
        String outer = render("outer", List.of("setup();"), List.of(inner.indent(2)));

        System.out.print(outer);
    }
}
```

**How to run:** `java IndentGenerator.java`

Expected output:
```
outer {
setup();
  inner {
  doWork();
  }
}
```

This builds a small nested pretty-printer: each nested block is indented 2 spaces further than its parent by calling `.indent(2)` on the already-rendered child text before splicing it into the parent, showing that `indent()` composes cleanly across recursive text-generation calls.

## 6. Walkthrough

1. In Level 3, `main` calls `render("inner", List.of("doWork();"), List.of())` first, since Java evaluates arguments left to right and `inner` is needed before `outer` can be built.
2. Inside `render`, a `StringBuilder` accumulates `"inner {\n"`, then the loop appends each line in `lines` (`"doWork();\n"`), then the (empty) children loop does nothing, then `"}\n"` closes the block.
3. `sb.toString().indent(0)` is called — `indent(0)` doesn't shift indentation at all, but it still normalizes line endings and guarantees a trailing `\n`, so `inner` becomes the clean string `"inner {\ndoWork();\n}\n"`.
4. Back in `main`, `render("outer", List.of("setup();"), List.of(inner.indent(2)))` runs next. Before this call, `inner.indent(2)` shifts *every line* of the already-rendered `inner` text two spaces to the right, producing `"  inner {\n  doWork();\n  }\n"`.
5. Inside this second `render` call, the `StringBuilder` builds `"outer {\n"`, then appends `"setup();\n"`, then appends the *already-indented* `inner` block as-is (it's just a child string being spliced in), then closes with `"}\n"`.
6. The final `sb.toString().indent(0)` normalizes the combined text once more before returning.
7. `System.out.print(outer)` writes the final nested structure: the `outer` line and its own direct lines sit at the base indentation, while everything that came from `inner` is shifted 2 spaces in, because that shift was baked in during step 4 — before the two strings were ever concatenated.

```
render("inner", ...) ──► "inner {\ndoWork();\n}\n"
        │
        ▼ .indent(2)
"  inner {\n  doWork();\n  }\n"
        │
        ▼ spliced into
render("outer", ...) ──► "outer {\nsetup();\n  inner {\n  doWork();\n  }\n}\n"
```

## 7. Gotchas & takeaways

> `indent()` always **normalizes line terminators to `\n`** and appends a trailing `\n` if the string doesn't already end with one — even `indent(0)`. If you concatenate an `indent()`-processed string with more text expecting no trailing newline, you may get an unexpected blank line; call `.stripTrailing()` afterward if you need to remove it.

- `indent(n)` with `n > 0` adds `n` spaces to the start of every line.
- `indent(n)` with `n < 0` removes up to `|n|` leading whitespace characters per line, but never strips past the first non-whitespace character (a line with only 1 leading space and `indent(-5)` just loses that 1 space, not more).
- `indent(0)` is a useful idiom purely for normalizing line endings and ensuring a trailing newline, without changing indentation.
- Because each nested string can be indented independently before being spliced together, `indent()` composes well for building small text/code generators.
- It operates on `\n`-split lines internally, so it correctly handles strings originally using `\r\n` or `\r` — the result always uses `\n`.
