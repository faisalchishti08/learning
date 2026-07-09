---
card: java
gi: 608
slug: improved-javadoc-search-html5
title: Improved Javadoc (search, HTML5)
---

## 1. What it is

Java 9 modernised the Javadoc tool with two major output improvements: the generated documentation now uses **HTML5** markup instead of the legacy HTML 4.01 frameset, and a built-in **client-side search** box is included on every page. The search indexes classes, methods, fields, and package names — no external search plugin needed. Additionally, the module system introduced a new "Module" view alongside the existing "Package" and "Class" views, and the overall styling was refreshed with a cleaner, more responsive layout.

## 2. Why & when

The old Javadoc output had been essentially unchanged since the early 2000s: HTML 4.01 with a three-pane frameset (package list, class list, detail pane). Framesets broke deep linking (you couldn't share a direct URL to a specific method), were incompatible with mobile browsers, and prevented search engines from indexing individual pages properly. The search functionality relied on the browser's built-in `find` (Ctrl+F), which only searched the current page. HTML5 output (optional in JDK 9, default in JDK 10+) replaces the frameset with a single-page layout that supports deep linking, responsive design, and an integrated search index. This brings Javadoc in line with modern documentation sites.

## 3. Core concept

```
javadoc -d docs \
        --module-source-path src \
        -html5 \
        -use \
        -author \
        -version \
        com.example.module

# The output now includes:
#   docs/
#     index.html           (single-page layout, no frameset)
#     search.js            (client-side search index)
#     member-search-index.js
#     type-search-index.js
#     ...
```

The `-html5` flag (optional in JDK 9, default from JDK 10 onward) enables HTML5 output. The search box appears at the top of every page and indexes types, members, packages, and modules. The search index is generated as JavaScript files that the browser loads and queries locally — no server-side component required.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JDK 9 Javadoc: HTML5 output, client-side search, module view">
  <rect x="20" y="10" width="560" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#e6edf3" font-size="11" font-family="sans-serif">javadoc -html5 -d docs com.example</text>

  <rect x="40" y="55" width="160" height="40" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="120" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">HTML5 output</text>
  <text x="120" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">single-page, responsive</text>

  <rect x="220" y="55" width="140" height="40" rx="4" fill="#79c0ff" stroke="#79c0ff"/>
  <text x="290" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Search box</text>
  <text x="290" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">client-side index</text>

  <rect x="380" y="55" width="160" height="40" rx="4" fill="#f0883e" stroke="#f0883e"/>
  <text x="460" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Module view</text>
  <text x="460" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">new tab: Module/Package/Class</text>

  <text x="30" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">Old (JDK 8):</text>
  <text x="30" y="138" fill="#f85149" font-size="10" font-family="monospace">  HTML 4.01, frameset, no search — Ctrl+F only, can't deep-link methods</text>

  <text x="30" y="160" fill="#8b949e" font-size="10" font-family="sans-serif">New (JDK 9+):</text>
  <text x="30" y="178" fill="#6db33f" font-size="10" font-family="monospace">  HTML5, no frames, built-in search, deep-linkable, module view, responsive</text>
</svg>

The shift from frameset to single-page HTML5 is the most visible change — deep linking and search work out of the box.

## 5. Runnable example

Scenario: generating API documentation for a small library — starting with basic Javadoc generation, extending to HTML5 output with search, and finally building a complete documentation set with module docs, search, and cross-references.

### Level 1 — Basic

```java
// File: Calculator.java (a documented class for Javadoc generation)

/**
 * A simple calculator with basic arithmetic operations.
 *
 * <p>This class demonstrates Javadoc conventions:
 * {@code @param}, {@code @return}, and {@code @throws} tags.
 *
 * @author JDK Team
 * @version 1.0
 */
public class Calculator {

    /**
     * Adds two integers and returns the result.
     *
     * @param a the first operand
     * @param b the second operand
     * @return the sum of {@code a} and {@code b}
     */
    public int add(int a, int b) {
        return a + b;
    }

    /**
     * Divides two integers.
     *
     * @param a the dividend
     * @param b the divisor (must not be zero)
     * @return the quotient of {@code a} divided by {@code b}
     * @throws ArithmeticException if {@code b} is zero
     */
    public int divide(int a, int b) {
        if (b == 0) throw new ArithmeticException("Division by zero");
        return a / b;
    }

    public static void main(String[] args) {
        System.out.println("=== Javadoc Demo ===\n");

        System.out.println("To generate Javadoc for this class:");
        System.out.println("$ javadoc -d docs Calculator.java");
        System.out.println();
        System.out.println("This generates docs/index.html and related files.");
        System.out.println("Open docs/index.html in a browser to see:");
        System.out.println("  - Class description with @author and @version");
        System.out.println("  - Method summaries with @param and @return");
        System.out.println("  - Cross-references between methods and classes");
    }
}
```

**How to run:** `java Calculator.java`

Expected output:
```
=== Javadoc Demo ===

To generate Javadoc for this class:
$ javadoc -d docs Calculator.java

This generates docs/index.html and related files.
Open docs/index.html in a browser to see:
  - Class description with @author and @version
  - Method summaries with @param and @return
  - Cross-references between methods and classes
```

The simplest Javadoc invocation: run `javadoc` on a Java file to produce HTML documentation. The output is a self-contained documentation site in the `docs/` directory.

### Level 2 — Intermediate

```java
// File: JavadocSearchDemo.java
import java.io.*;

/**
 * Demonstrates JDK 9 Javadoc improvements: HTML5 and search.
 *
 * <p>In JDK 9, add the {@code -html5} flag to generate HTML5 output
 * with a built-in client-side search box.
 */
public class JavadocSearchDemo {

    /**
     * Computes the factorial of a non-negative integer.
     *
     * @param n a non-negative integer
     * @return the factorial of {@code n}
     * @throws IllegalArgumentException if {@code n} is negative
     */
    public static long factorial(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be >= 0");
        long result = 1;
        for (int i = 2; i <= n; i++) result *= i;
        return result;
    }

    /**
     * Checks if a string is a palindrome (reads the same forwards and backwards).
     *
     * @param s the string to check (may be null)
     * @return {@code true} if {@code s} is a palindrome
     */
    public static boolean isPalindrome(String s) {
        if (s == null) return false;
        return s.equals(new StringBuilder(s).reverse().toString());
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Javadoc with HTML5 + Search ===\n");

        System.out.println("Generate Javadoc with JDK 9+ features:");
        System.out.println("$ javadoc -d docs \\");
        System.out.println("    -html5 \\");
        System.out.println("    -use \\");
        System.out.println("    -author \\");
        System.out.println("    -version \\");
        System.out.println("    JavadocSearchDemo.java\n");

        System.out.println("New features visible in the output:");
        System.out.println("  1. Search box at the top of every page");
        System.out.println("     → Type 'factorial' to find the method instantly");
        System.out.println("     → Type 'isPalindrome' to jump to that method\n");

        System.out.println("  2. HTML5 single-page layout (no frameset)");
        System.out.println("     → You can bookmark a specific method's URL");
        System.out.println("     → Works on mobile browsers\n");

        System.out.println("  3. Search index files generated:");
        System.out.println("     docs/member-search-index.js");
        System.out.println("     docs/type-search-index.js");
        System.out.println("     docs/package-search-index.js");
        System.out.println("     docs/module-search-index.js (for modular projects)\n");

        System.out.println("  4. -use flag generates cross-reference pages");
        System.out.println("     showing where each class/method is used");
    }
}
```

**How to run:** `java JavadocSearchDemo.java`

Expected output:
```
=== Javadoc with HTML5 + Search ===

Generate Javadoc with JDK 9+ features:
$ javadoc -d docs \
    -html5 \
    -use \
    -author \
    -version \
    JavadocSearchDemo.java

New features visible in the output:
  1. Search box at the top of every page
     → Type 'factorial' to find the method instantly
     → Type 'isPalindrome' to jump to that method

  2. HTML5 single-page layout (no frameset)
     → You can bookmark a specific method's URL
     → Works on mobile browsers

  3. Search index files generated:
     docs/member-search-index.js
     docs/type-search-index.js
     docs/package-search-index.js
     docs/module-search-index.js (for modular projects)

  4. -use flag generates cross-reference pages
     showing where each class/method is used
```

The real-world concern: generating HTML5 Javadoc with search, usage cross-references, and author/version metadata. The search box on the generated page indexes every class, method, field, and package — users can type part of a name and get instant results without page reload.

### Level 3 — Advanced

```java
// File: CompleteDocDemo.java

/**
 * Demonstrates a complete JDK 9+ Javadoc generation workflow for a
 * modular project, including package descriptions, custom tags,
 * and the module overview page.
 */
public class CompleteDocDemo {

    /** API version. */
    public static final String VERSION = "2.0.0";

    /**
     * Formats a greeting message.
     *
     * @param name the person to greet (not null)
     * @return the greeting string
     * @since 1.0
     */
    public String greet(String name) {
        return "Hello, " + name + "!";
    }

    public static void main(String[] args) {
        System.out.println("=== Complete Javadoc Generation (JDK 9+) ===\n");

        System.out.println("Sample modular project structure:");
        System.out.println("  src/");
        System.out.println("    com.example.lib/");
        System.out.println("      module-info.java");
        System.out.println("      package-info.java");
        System.out.println("      MyClass.java\n");

        System.out.println("Generate full documentation:");
        System.out.println("$ javadoc -d docs \\");
        System.out.println("    --module-source-path src \\");
        System.out.println("    --module com.example.lib \\");
        System.out.println("    -html5 \\");
        System.out.println("    -use \\");
        System.out.println("    -author \\");
        System.out.println("    -version \\");
        System.out.println("    -linksource \\");
        System.out.println("    -link https://docs.oracle.com/en/java/javase/17/docs/api/ \\");
        System.out.println("    -tag 'apiNote:a:API Note:' \\");
        System.out.println("    -tag 'implSpec:a:Implementation Requirements:'\n");

        System.out.println("Output pages include:");
        System.out.println("  • Module page: describes module exports, requires, services");
        System.out.println("  • Package page: shows package description from package-info.java");
        System.out.println("  • Class pages: HTML5, deep-linkable anchors per method");
        System.out.println("  • Search box: indexes modules, packages, types, members");
        System.out.println("  • Use pages: cross-references showing class/method usage");
        System.out.println("  • Source links: -linksource adds links to source code");
        System.out.println("  • External links: -link adds links to JDK API docs\n");

        System.out.println("Comparison — old vs new:");
        System.out.println("  JDK 8:  frameset, no search, HTML 4.01, no module view");
        System.out.println("  JDK 9+: single page, search, HTML5, module view");
        System.out.println("  JDK 10+: HTML5 is default (no -html5 flag needed)");
    }
}
```

**How to run:** `java CompleteDocDemo.java`

Expected output:
```
=== Complete Javadoc Generation (JDK 9+) ===

Sample modular project structure:
  src/
    com.example.lib/
      module-info.java
      package-info.java
      MyClass.java

Generate full documentation:
$ javadoc -d docs \
    --module-source-path src \
    --module com.example.lib \
    -html5 \
    -use \
    -author \
    -version \
    -linksource \
    -link https://docs.oracle.com/en/java/javase/17/docs/api/ \
    -tag 'apiNote:a:API Note:' \
    -tag 'implSpec:a:Implementation Requirements:'

Output pages include:
  • Module page: describes module exports, requires, services
  • Package page: shows package description from package-info.java
  • Class pages: HTML5, deep-linkable anchors per method
  • Search box: indexes modules, packages, types, members
  • Use pages: cross-references showing class/method usage
  • Source links: -linksource adds links to source code
  • External links: -link adds links to JDK API docs

Comparison — old vs new:
  JDK 8:  frameset, no search, HTML 4.01, no module view
  JDK 9+: single page, search, HTML5, module view
  JDK 10+: HTML5 is default (no -html5 flag needed)
```

The production-flavoured documentation build: modular projects get a module overview page; `package-info.java` files provide package-level descriptions; `-linksource` adds hyperlinked source code; `-link` connects to the JDK API docs; custom `-tag` options add project-specific documentation tags (like `@apiNote`). This is the standard configuration used by the JDK itself to produce its own documentation.

## 6. Walkthrough

Tracing `javadoc -html5 -use -d docs Calculator.java`:

1. `javadoc` starts by parsing the command line. It identifies `Calculator.java` as the input source file, `-d docs` as the output directory, `-html5` to enable HTML5 mode, and `-use` to generate cross-reference pages.

2. **Parsing**: `javadoc` parses `Calculator.java` using the compiler's parser. It builds an internal documentation model:
   - Class: `Calculator` (public, version 1.0, author "JDK Team")
   - Methods: `add(int, int)`, `divide(int, int)`
   - Each method has `@param` and `@return` entries in the model.

3. **Resolution**: `javadoc` resolves type references — `ArithmeticException` resolves to `java.lang.ArithmeticException`. The `{@code}` and `{@link}` tags are processed, generating HTML `<code>` and `<a>` elements.

4. **Search index generation**: `javadoc` builds index data structures:
   - Type index: `["Calculator"]`
   - Member index: `["add(int,int)", "divide(int,int)"]`
   - Each entry maps the search term to the URL of its documentation page.
   - The indices are serialised to JavaScript files (`member-search-index.js`, etc.).

5. **HTML5 page generation**: For `Calculator.html`:
   - A single-page layout with a top navigation bar (Module / Package / Class tabs).
   - A search box in the top-right corner.
   - Class description from the class-level Javadoc comment.
   - Method summary table with links to method detail sections.
   - Each method has an anchor ID (e.g. `#add-int-int-`), making it deep-linkable.
   - The `-use` flag produces `class-use/Calculator.html` showing where `Calculator` is referenced.

6. **Output**: Files are written to `docs/`:
   - `Calculator.html` (class page), `index.html` (overview)
   - `member-search-index.js`, `type-search-index.js`
   - `stylesheet.css`, `script.js`
   - `class-use/Calculator.html` (cross-references)

Open `docs/index.html` in a browser, type "divide" in the search box — the client-side JavaScript scans the index and shows `Calculator.divide(int,int)` as a result. Click it to navigate directly to the method's documentation.

## 7. Gotchas & takeaways

> The `-html5` flag was optional in JDK 9 but became the default in JDK 10 — if you're generating Javadoc with JDK 10+, you don't need to specify it. The legacy frameset output is still available with `-html4` if absolutely needed for backward compatibility with old tooling that scrapes frameset-based documentation.

- The search index is **client-side only** — it works by loading pre-built JavaScript index files in the browser. The search is fast (local, no server round-trip) but does not support fuzzy matching or stemming. Typing "divide" finds `divide`; typing "divides" does not.
- The `-linksource` flag embeds formatted source code directly in the documentation, with each identifier hyperlinked to its declaration. This is useful for API documentation but increases output size significantly.
- Custom tags (`-tag 'mytag:a:My Tag:'`) let you define project-specific documentation annotations that `javadoc` will recognise and render. The `a` in the definition means "allowed anywhere" (as opposed to `m` for method-only, `c` for constructor-only, etc.).
- If your project uses modules, `--module-source-path` and `--module` replace the old `-sourcepath` flag. `javadoc` generates a module summary page showing `exports`, `requires`, `uses`, and `provides` declarations.
- The `-link` flag requires an existing `package-list` or `element-list` file at the linked URL to work — if the target documentation site doesn't provide this file (some custom doc sites don't), the link silently fails and external references are not hyperlinked. 