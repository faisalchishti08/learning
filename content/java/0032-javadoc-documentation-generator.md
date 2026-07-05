---
card: java
gi: 32
slug: javadoc-documentation-generator
title: javadoc — documentation generator
---

## 1. What it is

**`javadoc`** is the JDK tool that generates HTML documentation from specially-formatted comments (`/** ... */`) in Java source files. The generated output is the standard Java API documentation — the format used by `docs.oracle.com/en/java/javase/21/docs/api/` and every published Java library's Javadoc site.

`javadoc` is part of `jdk.javadoc` module, JDK-only. The tool processes source files through the compiler's AST, extracts doc comments, resolves cross-references (`{@link}`, `@see`), and produces linked HTML pages with package summaries, class hierarchies, and method signatures.

## 2. Why & when

Javadoc matters for:
- **Library authors** — published JARs should include a `*-javadoc.jar` for IDE integration (Maven Central requires it).
- **IDE tooltip** — when you hover over a method in IntelliJ or VS Code, the popup comes from the Javadoc comment in the attached `*-javadoc.jar`.
- **Generating `package-info.java`** — package-level documentation.
- **Enforcing documentation quality** — `-Xdoclint:all` turns undocumented public APIs into build failures.

As a developer consuming libraries, you care about Javadoc when debugging, because the `@param`, `@return`, `@throws` tags explain contracts that aren't evident from the signature.

As a developer writing libraries, you write Javadoc for every public API surface — anything less makes the library harder to use correctly.

## 3. Core concept

Javadoc comment structure:
```java
/**
 * Short one-sentence summary (used in class/method index).
 *
 * <p>Longer description. Can contain HTML tags.
 * Can reference other types: {@link java.util.List}.
 * Can include code: {@code int x = 42;}.
 *
 * @param name   description of the parameter
 * @param count  must be positive; throws if <= 0
 * @return       the formatted string; never null
 * @throws IllegalArgumentException if count <= 0
 * @since 2.1
 * @see OtherClass#relatedMethod()
 */
public String format(String name, int count) { ... }
```

Key tags:
| Tag | Usage |
|-----|-------|
| `@param name desc` | Method parameter |
| `@return desc` | Return value |
| `@throws Type desc` | Checked and unchecked exceptions |
| `@since N` | Java/library version when added |
| `@deprecated reason` | Marks deprecated API |
| `@see ref` | Cross-reference |
| `{@link Type#method}` | Inline hyperlink in prose |
| `{@code expr}` | Inline code (monospace, no HTML escape needed) |
| `{@inheritDoc}` | Copies Javadoc from overridden method |

`javadoc` command:
```bash
javadoc -d docs/ -sourcepath src/ -subpackages com.example
javadoc -d docs/ src/com/example/*.java
javadoc -d docs/ --module-source-path src/ --module com.example
```

`-Xdoclint:all` enables all lint checks (missing `@param`, missing `@throws`, bad HTML, broken `{@link}` references). Maven's `maven-javadoc-plugin` runs this during `verify`.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="javadoc pipeline: source with doc comments → AST extraction → HTML pages with cross-links">
  <rect x="10" y="10" width="660" height="190" rx="8" fill="#0d1117"/>

  <!-- Source -->
  <rect x="25" y="40" width="130" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Foo.java</text>
  <text x="90" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">/** ... */</text>
  <text x="90" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@param @return</text>

  <line x1="155" y1="70" x2="190" y2="70" stroke="#8b949e" stroke-width="1.5" marker-end="url(#jd1)"/>

  <!-- javadoc tool -->
  <rect x="190" y="40" width="130" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="255" y="62" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">javadoc</text>
  <text x="255" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">AST + doc extract</text>
  <text x="255" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">resolve {@link}</text>

  <line x1="320" y1="70" x2="355" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jd2)"/>

  <!-- Output -->
  <rect x="355" y="28" width="290" height="114" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="46" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">docs/ (HTML output)</text>
  <text x="375" y="64"  fill="#8b949e" font-size="9" font-family="monospace">index.html</text>
  <text x="375" y="79"  fill="#8b949e" font-size="9" font-family="monospace">com/example/Foo.html</text>
  <text x="375" y="94"  fill="#8b949e" font-size="9" font-family="monospace">com/example/package-summary.html</text>
  <text x="375" y="109" fill="#8b949e" font-size="9" font-family="monospace">overview-tree.html</text>
  <text x="375" y="124" fill="#8b949e" font-size="9" font-family="monospace">deprecated-list.html</text>

  <!-- IDE tooltip -->
  <rect x="355" y="155" width="290" height="35" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="500" y="170" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">IDE tooltip: loads from *-javadoc.jar</text>
  <text x="500" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">jar cf library-javadoc.jar -C docs .</text>

  <defs>
    <marker id="jd1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="jd2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

`javadoc` processes source AST + doc comments → HTML site with package/class/method pages and cross-links. Packaged as `*-javadoc.jar` for IDE tooltip support.

## 5. Runnable example

Scenario: generate Javadoc programmatically, inspect what `javadoc` produces, and validate doc comment quality.

### Level 1 — Basic

```java
// JavadocBasic.java
public class JavadocBasic {
    public static void main(String[] args) {
        // Show Javadoc comment examples and what each tag does
        System.out.println("=== Javadoc Tag Reference ===\n");

        String[][] tags = {
            {"@param name desc",    "Documents a method parameter"},
            {"@return desc",        "Documents the return value"},
            {"@throws Type desc",   "Documents a thrown exception"},
            {"@since version",      "When this API was introduced"},
            {"@deprecated reason",  "Marks the API as deprecated"},
            {"@see reference",      "Adds a 'see also' cross-reference"},
            {"{@link Type#method}", "Inline hyperlink in description"},
            {"{@code expression}",  "Inline monospace code, no HTML escaping"},
            {"{@inheritDoc}",       "Copies javadoc from overridden method"},
            {"@author name",        "Author of the class (class-level only)"},
        };

        System.out.printf("%-30s  %s%n", "Tag", "Purpose");
        System.out.println("-".repeat(65));
        for (var t : tags) System.out.printf("%-30s  %s%n", t[0], t[1]);

        System.out.println("\n=== Well-documented method example ===\n");
        System.out.println("/**");
        System.out.println(" * Formats a greeting for the given name.");
        System.out.println(" *");
        System.out.println(" * <p>The greeting is localised to the default locale.");
        System.out.println(" * Use {@link #greetLocale(String, java.util.Locale)} for explicit locale.");
        System.out.println(" *");
        System.out.println(" * @param  name   the recipient's name; must not be null");
        System.out.println(" * @return        a formatted greeting string; never null");
        System.out.println(" * @throws NullPointerException if name is null");
        System.out.println(" * @since 1.0");
        System.out.println(" */");
        System.out.println("public String greet(String name) { ... }");
    }
}
```

**How to run:** `java JavadocBasic.java`

Javadoc comments are `/** ... */` (two asterisks after `/*`). Single-star `/* */` block comments are not processed by `javadoc`.

### Level 2 — Intermediate

Same Javadoc demo extended to generate real Javadoc HTML from a dynamically-compiled class using the `javadoc` tool API.

```java
// JavadocGenerator.java
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JavadocGenerator {

    static final String DOCUMENTED_SOURCE =
        "package example;\n" +
        "\n" +
        "/**\n" +
        " * A simple calculator for demonstration purposes.\n" +
        " *\n" +
        " * <p>Supports basic arithmetic operations.\n" +
        " * Results are {@code double} for precision.\n" +
        " *\n" +
        " * @since 1.0\n" +
        " */\n" +
        "public class Calculator {\n" +
        "\n" +
        "    /**\n" +
        "     * Adds two numbers.\n" +
        "     *\n" +
        "     * @param a  first operand\n" +
        "     * @param b  second operand\n" +
        "     * @return   the sum {@code a + b}\n" +
        "     */\n" +
        "    public double add(double a, double b) { return a + b; }\n" +
        "\n" +
        "    /**\n" +
        "     * Divides two numbers.\n" +
        "     *\n" +
        "     * @param  a       numerator\n" +
        "     * @param  b       denominator; must not be zero\n" +
        "     * @return         {@code a / b}\n" +
        "     * @throws ArithmeticException if {@code b == 0}\n" +
        "     */\n" +
        "    public double divide(double a, double b) {\n" +
        "        if (b == 0) throw new ArithmeticException(\"Division by zero\");\n" +
        "        return a / b;\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("javadoc-gen");
        Path srcDir = Files.createDirectories(tmpDir.resolve("src/example"));
        Path outDir = Files.createDirectories(tmpDir.resolve("docs"));

        // Write source
        Path src = srcDir.resolve("Calculator.java");
        Files.writeString(src, DOCUMENTED_SOURCE);
        System.out.println("Source written: " + src);

        // Run javadoc via DocumentationTool API
        DocumentationTool docTool = ToolProvider.getSystemDocumentationTool();
        if (docTool == null) {
            System.out.println("javadoc tool not available — running on JRE?");
            System.out.println("Equivalent command:");
            System.out.printf("  javadoc -d %s -sourcepath %s example%n", outDir, tmpDir.resolve("src"));
            return;
        }

        StringWriter sw = new StringWriter();
        int rc = docTool.run(null, null, new PrintWriter(sw),
            "-d", outDir.toString(),
            "-sourcepath", tmpDir.resolve("src").toString(),
            "-subpackages", "example");

        System.out.println("javadoc exit code: " + rc + (rc == 0 ? " (success)" : " (FAILED)"));
        if (!sw.toString().isBlank()) {
            System.out.println("Output: " + sw.toString().trim());
        }

        if (rc == 0) {
            System.out.println("\nGenerated files:");
            Files.walk(outDir).filter(p -> p.toString().endsWith(".html"))
                .forEach(p -> System.out.println("  " + outDir.relativize(p)));
        }

        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
    }
}
```

**How to run:** `java JavadocGenerator.java`

`ToolProvider.getSystemDocumentationTool()` returns the `javadoc` tool as a `DocumentationTool` instance — the programmatic equivalent of the `javadoc` CLI.

### Level 3 — Advanced

Same scenario grown to inspect doc comments programmatically using the Compiler Tree API — the way IDE inspectors and lint tools read Javadoc without generating HTML.

```java
// JavadocAnalyzer.java
import com.sun.source.doctree.*;
import com.sun.source.util.*;
import javax.tools.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class JavadocAnalyzer {

    static final String SOURCE =
        "package example;\n" +
        "/**\n" +
        " * Demonstrates Javadoc analysis.\n" +
        " * @since 1.0\n" +
        " */\n" +
        "public class Service {\n" +
        "    /** Creates a service. */\n" +
        "    public Service() {}\n" +
        "\n" +
        "    /**\n" +
        "     * Processes the request.\n" +
        "     * @param input the input data; must not be null\n" +
        "     * @return processed result\n" +
        "     * @throws IllegalArgumentException if input is null\n" +
        "     */\n" +
        "    public String process(String input) { return input; }\n" +
        "\n" +
        "    // No javadoc on this method\n" +
        "    public void undocumented() {}\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        Path tmpDir = Files.createTempDirectory("javadoc-analyze");
        Path srcFile = tmpDir.resolve("Service.java");
        Files.writeString(srcFile, SOURCE);

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        StandardJavaFileManager fm = compiler.getStandardFileManager(null, null, null);
        Iterable<? extends JavaFileObject> units = fm.getJavaFileObjects(srcFile.toFile());

        // Use Trees API to walk doc comments
        JavacTask task = (JavacTask) compiler.getTask(null, fm, null,
            List.of("-d", tmpDir.toString()), null, units);
        Trees trees = Trees.instance(task);

        System.out.println("=== Javadoc Analysis ===\n");

        task.parse();
        task.analyze();

        for (var tree : task.parse()) {
            new TreeScanner<Void, Void>() {
                @Override
                public Void visitMethod(com.sun.source.tree.MethodTree node, Void p) {
                    String name = node.getName().toString();
                    DocCommentTree dct = trees.getDocCommentTree(
                        trees.getPath(tree, node));

                    if (dct == null) {
                        System.out.printf("Method %-20s  WARNING: no Javadoc%n", name + "()");
                    } else {
                        List<String> tags = new ArrayList<>();
                        for (DocTree dt : dct.getBlockTags()) {
                            tags.add("@" + dt.getKind().tagName);
                        }
                        System.out.printf("Method %-20s  tags: %s%n", name + "()", tags);
                    }
                    return super.visitMethod(node, p);
                }
            }.scan(tree, null);
        }

        System.out.println("\nNote: tools like Checkstyle and PMD use the same Trees API");
        System.out.println("to enforce Javadoc requirements in CI pipelines.");

        Files.walk(tmpDir).sorted(Comparator.reverseOrder()).forEach(p -> p.toFile().delete());
    }
}
```

**How to run:** `java JavadocAnalyzer.java`

`Trees.getDocCommentTree(path)` returns the parsed doc comment AST. `DocTree.getBlockTags()` returns the `@param`, `@return`, `@throws` etc. as structured objects. This is how Checkstyle's `JavadocMethodCheck` rule works.

## 6. Walkthrough

Execution in `JavadocAnalyzer.main`:

1. **`JavacTask`** — obtained by casting `compiler.getTask(...)`. It exposes the compiler's internal AST processing pipeline: `task.parse()` produces `CompilationUnitTree` objects (one per source file); `task.analyze()` resolves types and names.

2. **`Trees.instance(task)`** — the `com.sun.source.util.Trees` API gives access to the full compiler AST, including Javadoc tree nodes. This is an internal JDK API (not in a module's exported public API) — it requires `--add-exports` or runs implicitly in JDK-internal mode during annotation processing.

3. **`TreeScanner.visitMethod`** — the visitor pattern on the compiler AST. `MethodTree` represents a method declaration. `trees.getPath(compilationUnit, methodTree)` builds the path needed to retrieve the doc comment.

4. **`DocCommentTree.getBlockTags()`** — returns the Javadoc block tags as a `List<DocTree>`. Each `DocTree` subtype corresponds to a tag kind: `ParamTree` for `@param`, `ReturnTree` for `@return`, `ThrowsTree` for `@throws`.

5. **`null` doc comment** — `trees.getDocCommentTree(path)` returns `null` if the method has no `/** ... */` comment. This is how tools detect undocumented public methods.

## 7. Gotchas & takeaways

> **`{@code}` vs `<code>` in Javadoc**: `{@code text}` is preferred — it does not require HTML escaping (e.g., `{@code List<String>}` works; `<code>List&lt;String&gt;</code>` is the verbose equivalent). `{@code}` also prevents `<` from being interpreted as an HTML tag.

> **`@throws` vs `@exception`**: they are synonyms. Use `@throws`. Document both checked and unchecked exceptions that callers should be aware of — `NullPointerException` on null inputs is worth documenting even though it's unchecked.

- `/** ... */` is a Javadoc comment; `/* ... */` is not.
- `{@link Type#method}` creates a hyperlink; `{@code expr}` creates monospace code.
- `-Xdoclint:all` enforces complete documentation — catches missing `@param`, broken `{@link}`.
- `ToolProvider.getSystemDocumentationTool()` is the programmatic `javadoc` API.
- `Trees` + `DocCommentTree` APIs let you parse and analyse Javadoc in annotation processors and lint tools.
- Maven Central requires a `*-javadoc.jar` alongside the main and sources JARs.
