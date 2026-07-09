---
card: java
gi: 772
slug: markdown-documentation-comments
title: Markdown documentation comments
---

## 1. What it is

**Java 23** (JEP 467) lets you write **Javadoc comments in Markdown** instead of HTML. A doc comment can now start with `///` (three slashes, one per line) rather than `/** ... */`, and inside it you use ordinary Markdown syntax — `` `code` ``, `**bold**`, `- lists`, fenced code blocks, and `[links](...)` — which the Javadoc tool converts to HTML when it generates documentation pages. The old `/** */` HTML-comment style still works unchanged; Markdown comments are a new, optional alternative.

## 2. Why & when

Traditional Javadoc comments are HTML embedded in a block comment: lists need `<ul><li>`, code needs `<pre>{@code ...}</pre>`, links need `{@link ...}` or raw `<a href>` tags. That's a lot of markup ceremony for what is, in the source file, meant to be read as plain prose by a human working in an editor — and it makes doc comments visually noisy compared to the code around them. Markdown became the de facto standard for exactly this kind of "readable as text, renders as rich content" writing (README files, PR descriptions, chat messages), so JEP 467 brings that same lightweight syntax to doc comments: a bullet list is just `- item`, code is just `` `code` `` or a fenced block, and the comment reads naturally whether you're looking at the raw source or the generated HTML. It's most valuable for new code and for doc comments with lists, code samples, or emphasis — the cases where HTML markup previously added the most visual clutter.

## 3. Core concept

```java
/// Returns the {@code n}th Fibonacci number.
///
/// Uses an iterative approach, so it runs in **O(n)** time and O(1) space:
///
/// - `fib(0)` returns `0`
/// - `fib(1)` returns `1`
/// - `fib(n)` for `n > 1` returns `fib(n-1) + fib(n-2)`
///
/// @param n the index, must be non-negative
/// @return the nth Fibonacci number
public static long fib(int n) {
    if (n < 2) return n;
    long a = 0, b = 1;
    for (int i = 2; i <= n; i++) { long next = a + b; a = b; b = next; }
    return b;
}
```

Every line starts with `///`; the body is plain Markdown, and `@param`/`@return` tags still work exactly as before.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A slash-slash-slash Markdown doc comment is converted by the Javadoc tool into the same HTML output as a traditional HTML doc comment">
  <rect x="20" y="20" width="270" height="90" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="155" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">/// Markdown doc comment</text>
  <text x="155" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">/// - `fib(0)` returns `0`</text>
  <text x="155" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">/// **O(n)** time</text>

  <rect x="350" y="20" width="270" height="90" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="485" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">/** HTML doc comment */</text>
  <text x="485" y="65" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">&lt;li&gt;{@code fib(0)} returns 0&lt;/li&gt;</text>
  <text x="485" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">&lt;b&gt;O(n)&lt;/b&gt; time</text>

  <line x1="155" y1="110" x2="320" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="485" y1="110" x2="320" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <rect x="230" y="150" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="170" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">same generated HTML page</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

*Both comment styles compile to identical documentation output — Markdown is a lighter-weight way to write the same thing.*

## 5. Runnable example

Scenario: documenting a small `Stack` utility class, growing from a single plain-Markdown comment into a fully cross-linked, code-sample-rich set of doc comments, then generating and inspecting the actual HTML output.

### Level 1 — Basic

```java
/// A simple, fixed-capacity stack of integers.
public class TinyStack {
    private final int[] data;
    private int size = 0;

    public TinyStack(int capacity) {
        data = new int[capacity];
    }

    /// Pushes a value onto the top of the stack.
    ///
    /// @param value the value to push
    public void push(int value) {
        data[size++] = value;
    }

    /// Removes and returns the value at the top of the stack.
    ///
    /// @return the value that was on top
    public int pop() {
        return data[--size];
    }

    public static void main(String[] args) {
        TinyStack s = new TinyStack(4);
        s.push(1);
        s.push(2);
        System.out.println("popped: " + s.pop());
    }
}
```

**How to run:** `java --source 23 --enable-preview TinyStack.java` — Markdown doc comments themselves need no preview flag to *compile* as ordinary comments, but Java 23's `javadoc` tool needs the matching release to render them; running the class normally works on any JDK 23 install.

Every `///` line is a doc comment attached to the declaration immediately below it, written as plain sentences — no `<p>` or `<code>` tags needed even though `pop()`'s comment reads naturally as prose.

### Level 2 — Intermediate

```java
/// A simple, fixed-capacity stack of integers.
///
/// Backed by a plain array; pushing past the configured capacity
/// throws `ArrayIndexOutOfBoundsException`. Typical usage:
///
/// ```java
/// TinyStack s = new TinyStack(4);
/// s.push(1);
/// s.push(2);
/// int top = s.pop(); // 2
/// ```
public class TinyStackDocumented {
    private final int[] data;
    private int size = 0;

    /// Creates a stack that can hold up to `capacity` elements.
    ///
    /// @param capacity the maximum number of elements; must be positive
    public TinyStackDocumented(int capacity) {
        data = new int[capacity];
    }

    /// Pushes a value onto the top of the stack.
    ///
    /// @param value the value to push
    /// @throws ArrayIndexOutOfBoundsException if the stack is already full
    public void push(int value) {
        data[size++] = value;
    }

    /// Removes and returns the value at the top of the stack.
    ///
    /// @return the value that was on top
    /// @throws ArrayIndexOutOfBoundsException if the stack is empty
    public int pop() {
        return data[--size];
    }

    public static void main(String[] args) {
        TinyStackDocumented s = new TinyStackDocumented(4);
        s.push(1);
        s.push(2);
        System.out.println("popped: " + s.pop());
    }
}
```

**How to run:** compile and generate docs with `javadoc --source 23 --enable-preview -d out TinyStackDocumented.java`, then run normally with `java --source 23 --enable-preview TinyStackDocumented.java`.

The real-world concern added: a **fenced Markdown code block** (` ```java ... ``` `) showing a usage example directly in the class-level comment, plus `@throws` tags — the fenced block renders as a syntax-highlighted `<pre><code>` block in the generated HTML, exactly like `{@code}`/`{@snippet}` would have produced, but written as plain Markdown.

### Level 3 — Advanced

```java
/// A simple, fixed-capacity stack of integers.
///
/// Backed by a plain array; see [#push(int)] and [#pop()] for the two
/// core operations. This class is **not** thread-safe — concurrent
/// pushes and pops from multiple threads require external synchronization.
///
/// | Method    | Precondition        | Complexity |
/// |-----------|----------------------|------------|
/// | `push`    | stack is not full    | O(1)       |
/// | `pop`     | stack is not empty   | O(1)       |
public class TinyStackAdvanced {
    private final int[] data;
    private int size = 0;

    public TinyStackAdvanced(int capacity) {
        data = new int[capacity];
    }

    /// Pushes a value onto the top of the stack.
    ///
    /// @param value the value to push
    /// @throws ArrayIndexOutOfBoundsException if the stack is already full
    /// @see #pop()
    public void push(int value) {
        data[size++] = value;
    }

    /// Removes and returns the value at the top of the stack.
    ///
    /// @return the value that was on top
    /// @throws ArrayIndexOutOfBoundsException if the stack is empty
    /// @see #push(int)
    public int pop() {
        return data[--size];
    }

    /// Returns `true` if the stack currently holds no elements.
    ///
    /// @return whether the stack is empty
    public boolean isEmpty() {
        return size == 0;
    }

    public static void main(String[] args) {
        TinyStackAdvanced s = new TinyStackAdvanced(2);
        System.out.println("empty at start: " + s.isEmpty());
        s.push(10);
        s.push(20);
        System.out.println("popped: " + s.pop());
        System.out.println("empty now: " + s.isEmpty());
    }
}
```

**How to run:** `javadoc --source 23 --enable-preview -d out TinyStackAdvanced.java` to generate HTML docs into `out/`, then `java --source 23 --enable-preview TinyStackAdvanced.java` to run the class itself.

This adds the production-flavored hard case: a **Markdown table** and **reference links** (`[#push(int)]`, resolved the same way `{@link #push(int)}` would be) inside the class-level comment, alongside `@see` tags on the methods — mixing Markdown's own linking syntax with the doc-comment-specific reference resolution that Javadoc has always provided, so links between members still resolve correctly even though the surrounding prose is plain Markdown.

## 6. Walkthrough

Tracing what happens when you run `javadoc --source 23 --enable-preview -d out TinyStackAdvanced.java`:

1. The Javadoc tool parses the source file and, for each declaration, collects the `///`-prefixed lines immediately preceding it as that declaration's doc comment — stripping the leading `///` and leading whitespace from each line to recover the underlying Markdown text.
2. For the class-level comment, it finds a paragraph, a bold-emphasized sentence (`**not**`), a Markdown table (the `| Method | ... |` block), and two `[#push(int)]`/`[#pop()]`-style reference links.
3. Each Markdown construct is translated to its HTML equivalent: the table becomes an HTML `<table>`, `**not**` becomes `<strong>not</strong>`, and each `[#push(int)]` reference link is resolved exactly like a traditional `{@link #push(int)}` — Javadoc looks up the `push(int)` method on the same class and turns the reference into an `<a href="...">` pointing at that method's generated section.
4. For `push`'s doc comment, the `@param`, `@throws`, and `@see` block tags are parsed exactly as they always have been (block tags are unaffected by comment style) and rendered into the "Parameters," "Throws," and "See Also" sections of the generated page.
5. Javadoc writes the resulting HTML pages into the `out/` directory, including `TinyStackAdvanced.html` with the fully rendered class description (table, bold text, and resolved links) and per-method sections for `push`, `pop`, and `isEmpty`.
6. Separately, running `java --source 23 --enable-preview TinyStackAdvanced.java` executes `main`: it constructs a 2-capacity stack, checks `isEmpty()` (true), pushes `10` and `20`, pops (`20`), and checks `isEmpty()` again (false, one element remains).

Expected program output:
```
empty at start: true
popped: 20
empty now: false
```

Expected `javadoc` output (abridged):
```
Loading source files for package unnamed package...
Constructing Javadoc information...
Generating out/TinyStackAdvanced.html...
```

## 7. Gotchas & takeaways

> **Gotcha:** a `///` line comment and a `/** */` block comment cannot both document the same declaration, and you cannot silently switch styles mid-file expecting them to merge — pick one style per doc comment. Also, because `///` is a *line* comment marker, every line of a multi-line Markdown doc comment needs its own `///` prefix; forgetting it on a continuation line simply ends the doc comment early rather than producing an error.

- Preview in Java 23 (JEP 467) — start each doc-comment line with `///`; the existing `/** */` HTML style keeps working unchanged.
- Inside a `///` comment, use plain Markdown: `` `code` ``, `**bold**`, fenced code blocks, lists, and tables all render to the same HTML a hand-written `/** */` comment would have produced.
- Block tags (`@param`, `@return`, `@throws`, `@see`) work identically in both comment styles — only the *body* text's markup syntax changes.
- Markdown reference links (e.g. `[#method(args)]`) resolve the same way `{@link}` always did, so cross-references between members still work.
- Best suited to new code, or doc comments heavy on lists, tables, or code samples, where HTML markup previously added the most visual noise relative to plain prose.
