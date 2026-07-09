---
card: java
gi: 719
slug: code-snippets-in-javadoc-snippet
title: Code snippets in Javadoc (@snippet)
---

## 1. What it is

**Java 18** (JEP 413) adds a new **`{@snippet ...}`** tag to Javadoc, giving documentation authors a dedicated, purpose-built way to embed example source code in generated API documentation. Before this, embedding a code example in Javadoc meant reaching for `{@code ...}` (fine for a single line, awkward for anything longer) or `<pre>{@code ...}</pre>` (works, but forces manual HTML escaping of `<`, `>`, and `&`, and offers no way to highlight specific lines, pull in external files, or validate the snippet actually compiles). `{@snippet}` replaces all of that with a single tag that handles multi-line code cleanly, supports region markup, and — critically — can reference an *external, separately-compiled* source file, so the example shown in the documentation is guaranteed to actually compile.

## 2. Why & when

Documentation examples rot. A code sample pasted into a Javadoc comment as a string is invisible to the compiler — nothing stops the surrounding class from being refactored while the example in the comment quietly goes stale, still referencing a method that was renamed three releases ago. This is a well-known, chronic problem in API documentation generally, and the JDK's own Javadoc had no first-class fix for it. JEP 413 addresses this two ways: first, by making inline snippets far more pleasant to write (no more manually escaping `<T>` as `&lt;T&gt;`), and second — the more important part — by letting a snippet's *content* live in an actual `.java` file under `src/**/snippet-files/`, a file that is a normal part of the source tree and can be compiled and even executed as part of a build or test step. When the source changes in a way that breaks the example, the build breaks too, instead of the documentation silently drifting out of sync. Use `{@snippet}` any time Javadoc needs to show non-trivial example code — and prefer the external-file form specifically when you want that example to be compiler-verified.

## 3. Core concept

```java
/**
 * Reverses the given list in place.
 *
 * Inline snippet (content lives directly in the comment):
 * {@snippet lang=java :
 *     List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
 *     Collections.reverse(nums);
 *     // nums is now [3, 2, 1]
 * }
 *
 * External snippet (content lives in a separate, compilable file):
 * {@snippet file="ReverseDemo.java" region="reverse-example"}
 */
public static <T> void reverse(List<T> list) { ... }
```

An external snippet file marks the region it exposes with `// @start region="reverse-example"` and `// @end` comments; only that marked region is pulled into the generated docs, even though the file itself may contain more surrounding setup code that keeps it compiling.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An external snippet file is a real compilable Java file; only its marked region is extracted into the generated Javadoc HTML">
  <rect x="30" y="30" width="260" height="160" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">ReverseDemo.java (real, compiled)</text>
  <text x="160" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">import java.util.*;</text>
  <text x="160" y="96" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">class ReverseDemo {</text>
  <text x="160" y="114" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">// @start region="reverse-example"</text>
  <text x="160" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">List&lt;Integer&gt; nums = ...</text>
  <text x="160" y="150" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">// @end</text>
  <text x="160" y="168" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">}</text>

  <line x1="295" y1="110" x2="405" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#a2)"/>
  <text x="350" y="100" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">javadoc</text>

  <rect x="410" y="30" width="200" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Generated HTML</text>
  <text x="510" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">only the region</text>
  <text x="510" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">between @start/@end</text>
  <text x="510" y="126" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">is shown, syntax-</text>
  <text x="510" y="144" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">highlighted</text>

  <defs><marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The documentation shows only the marked region, but the whole file compiles — so the example can never silently go stale.

## 5. Runnable example

Scenario: documenting a small `Stack`-like `reverse` utility. The example grows from an inline snippet, to an external, compiler-verified snippet file, to a fully executable snippet file whose output is captured and shown alongside the code in the generated documentation.

### Level 1 — Basic

```java
// File: ListUtils.java
import java.util.*;

public class ListUtils {

    /**
     * Reverses the given list in place.
     *
     * <p>Example:
     * {@snippet lang=java :
     *     List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
     *     ListUtils.reverseInPlace(nums);
     *     // nums is now [3, 2, 1]
     * }
     *
     * @param list the list to reverse, modified in place
     */
    public static <T> void reverseInPlace(List<T> list) {
        Collections.reverse(list);
    }

    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
        reverseInPlace(nums);
        System.out.println("Reversed: " + nums);
    }
}
```

**How to run:**
```
java ListUtils.java
javadoc ListUtils.java -d docs
```

Expected output from running the program:
```
Reversed: [3, 2, 1]
```
The `javadoc` command additionally produces `docs/ListUtils.html`, in which the `{@snippet lang=java : ...}` block renders as a syntax-highlighted code panel showing exactly the three lines between the tag's colon and its closing brace.

### Level 2 — Intermediate

```java
// File: ListUtils.java (updated Javadoc, referencing an external file)
import java.util.*;

public class ListUtils {

    /**
     * Reverses the given list in place.
     *
     * <p>Example:
     * {@snippet file="ReverseDemoSnippet.java" region="reverse-example"}
     *
     * @param list the list to reverse, modified in place
     */
    public static <T> void reverseInPlace(List<T> list) {
        Collections.reverse(list);
    }

    public static void main(String[] args) {
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
        reverseInPlace(nums);
        System.out.println("Reversed: " + nums);
    }
}
```

```java
// File: snippet-files/ReverseDemoSnippet.java
// This file is a REAL, separately compilable Java file — javac must accept
// it, so the example in the docs can never silently drift out of sync.
import java.util.*;

class ReverseDemoSnippet {
    static void run() {
        // @start region="reverse-example"
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
        ListUtils.reverseInPlace(nums);
        // nums is now [3, 2, 1]
        // @end
        System.out.println(nums); // kept outside the region: not shown in docs, but keeps this file meaningful
    }

    public static void main(String[] args) {
        run();
    }
}
```

**How to run:**
```
javac ListUtils.java snippet-files/ReverseDemoSnippet.java -d out
java -cp out ReverseDemoSnippet
javadoc ListUtils.java --snippet-path snippet-files -d docs
```

Expected output from running the snippet file directly (proving it genuinely compiles and runs):
```
[3, 2, 1]
```
`javadoc --snippet-path snippet-files` locates `ReverseDemoSnippet.java`, extracts only the `reverse-example` region, and embeds it in `docs/ListUtils.html` — the `run()` wrapper and the trailing `System.out.println` stay out of the rendered documentation but keep the file compiling as ordinary Java.

### Level 3 — Advanced

```java
// File: snippet-files/ReverseDemoAdvanced.java
// Adds a second region for handling an edge case (empty list), and separates
// "setup" code from the "highlighted" example region using two regions in
// one file — a common pattern for documenting a method plus a gotcha.
import java.util.*;

class ReverseDemoAdvanced {
    static void basicExample() {
        // @start region="reverse-example"
        List<Integer> nums = new ArrayList<>(List.of(1, 2, 3));
        ListUtils.reverseInPlace(nums);
        System.out.println(nums); // [3, 2, 1]
        // @end
    }

    static void emptyListExample() {
        // @start region="reverse-empty-example"
        List<Integer> empty = new ArrayList<>();
        ListUtils.reverseInPlace(empty); // no-op, does not throw
        System.out.println(empty); // []
        // @end
    }

    public static void main(String[] args) {
        System.out.print("Basic: ");
        basicExample();
        System.out.print("Empty: ");
        emptyListExample();
    }
}
```

**How to run:**
```
javac ListUtils.java snippet-files/ReverseDemoAdvanced.java -d out
java -cp out ReverseDemoAdvanced
```

Expected output:
```
Basic: [3, 2, 1]
Empty: []
```
Referencing `region="reverse-example"` in one Javadoc comment and `region="reverse-empty-example"` in another (e.g. inside a `@apiNote` documenting the empty-list edge case) pulls each region into its own place in the generated documentation, from this single compiled, executable file.

## 6. Walkthrough

1. A reader opens the generated `docs/ListUtils.html` page for `reverseInPlace`. The Javadoc tool already ran ahead of time, during the `javadoc` build step — not at page-view time — so what the reader sees is static HTML with the snippet already expanded.
2. During that `javadoc` build step, the tool encountered `{@snippet file="ReverseDemoSnippet.java" region="reverse-example"}` inside the method's doc comment. Because `--snippet-path snippet-files` was passed, it looked for `snippet-files/ReverseDemoSnippet.java` relative to the source root.
3. It opened that file and scanned for the markers `// @start region="reverse-example"` and its matching `// @end`. Everything strictly between those two markers — the three lines building the list, calling `reverseInPlace`, and the comment about the result — is extracted as plain text.
4. That extracted text is HTML-escaped automatically (unlike the old `<pre>{@code}</pre>` approach, no manual `&lt;`/`&gt;` needed) and wrapped in a `<pre class="snippet">` block in the output HTML, ready for CSS syntax highlighting.
5. Crucially, step 2 through 4 only affect what's *shown*. The file `ReverseDemoSnippet.java` as a whole — including the `run()` wrapper method and `main` — is a completely ordinary Java source file. Running `javac` on it (as Level 2's "How to run" does) compiles it for real; running it prints `[3, 2, 1]`. If a future edit to `ListUtils.reverseInPlace` changed its name or signature, `ReverseDemoSnippet.java` would fail to compile, and that build failure — not a silently wrong documentation page — is what the author would see.
6. In Level 3, two independent regions inside one file (`reverse-example` and `reverse-empty-example`) are each referenced by a *different* `{@snippet ... region="..."}` tag elsewhere in the Javadoc — one region per concern, from one shared, compiled, runnable source file.

```
javadoc build time                              Reader's browser (later)
-------------------                             ------------------------
1. parse {@snippet file=... region=...}
2. open snippet-files/Foo.java
3. extract text between @start/@end markers  -> baked into static HTML
4. HTML-escape + wrap in <pre class="snippet">
                                                  5. loads finished HTML,
                                                     sees ready-made code block
```

## 7. Gotchas & takeaways

> External snippet files live under a `snippet-files` directory and must be passed to `javadoc` via `--snippet-path` — forgetting that flag makes every `{@snippet file="..."}` tag fail to resolve, and the documentation build reports the missing file rather than silently omitting the example.
- `{@snippet}` supports three sources: inline (`{@snippet : ... }`), inline with an explicit language (`{@snippet lang=java : ... }`), and external file (`{@snippet file="..." region="..."}`) — pick inline for a one-off two-line example and external whenever the example is worth keeping compiler-honest.
- Region markers (`// @start region="name"` / `// @end`) can nest and repeat within one file, letting a single snippet source file back multiple documentation examples, as in Level 3's advanced example.
- Because external snippet files are ordinary `.java` files, nothing stops a build from also *compiling and running* them as part of CI — turning documentation examples into a lightweight form of executable test that fails loudly the moment it goes stale, rather than the traditional silent doc rot.
- `{@snippet}` also has markup actions beyond regions — `@highlight`, `@replace`, and `@link` — for emphasizing specific lines or turning a token in the snippet into a hyperlink to another Javadoc page, though the region-and-external-file pattern shown here covers the most common real-world need: guaranteeing the example actually compiles.
