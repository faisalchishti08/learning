---
card: java
gi: 60
slug: javadoc-comments
title: Javadoc comments (/** … */)
---

## 1. What it is

**Javadoc comments** start with `/**` and end with `*/`. They appear immediately before a class, interface, constructor, method, or field declaration. The `javadoc` tool reads them and generates HTML API documentation. IDEs also display them as hover-over tooltips.

```java
/**
 * Processes a payment order and returns a confirmation token.
 *
 * @param orderId unique order identifier (UUID format)
 * @param amount  payment amount in GBP; must be positive and ≤ 10,000
 * @return        a confirmation token on success
 * @throws IllegalArgumentException if {@code amount} is non-positive
 */
public String process(String orderId, double amount) { ... }
```

Javadoc comments use block tags (`@param`, `@return`, `@throws`, `@see`, `@since`, `@deprecated`) and inline tags (`{@code}`, `{@link}`, `{@literal}`) to structure the generated HTML.

## 2. Why & when

| Scope | Recommendation |
|---|---|
| `public` and `protected` members | **Always** document with Javadoc |
| Package-private members | Optional — document if used beyond one class |
| `private` members | Skip Javadoc; use `//` if the implementation is non-obvious |
| Interfaces | Document every method — they define the contract |
| Abstract methods | Document the expected contract and invariants |
| Overriding methods | Add `{@inheritDoc}` if you add nothing new; add Javadoc if you narrow the contract |

Write Javadoc for **API consumers**, not implementers. Explain what the method guarantees, what the parameters must satisfy, and what the return value means — not how it works internally.

## 3. Core concept

```java
/**
 * ---- Structure of a Javadoc comment ----
 *
 * First sentence: the summary — appears in the method listing table.
 *
 * <p>Subsequent paragraphs (after a blank line) give details.
 * Use {@code SomeType} for inline code, {@link ClassName} for cross-links.
 *
 * @param  paramName  what it represents; any constraints (not null, positive, etc.)
 * @param  another    parallel description for each parameter
 * @return            what the value means, not just its type
 * @throws ExceptionType  under what conditions; what state remains after
 * @see    OtherClass#method()
 * @since  1.4
 * @deprecated Use {@link #newMethod()} instead. Removal planned for version 3.0.
 */
```

```bash
# Generate HTML documentation
javadoc -d docs -sourcepath src -subpackages com.example

# With module support (JDK 9+)
javadoc --module-path mods --module com.example.app -d docs

# Output: docs/index.html, class pages, package-summary pages

# Common options
-author           include @author tags in output
-version          include @version tags
-link https://...  link to external Javadoc (e.g., JDK docs)
-nodeprecated     suppress deprecated items

# Check for missing Javadoc
javadoc -Xdoclint:all -d /dev/null src/...
# or use: javac -Xlint:all -proc:none src/...
```

```java
// ---- inline tags ----
// {@code expression}  → renders as monospace code (no HTML escaping needed)
// {@link Class#member} → hyperlink in HTML output, error if target doesn't exist
// {@linkplain ...}    → like @link but renders in normal font
// {@literal text}     → prevents HTML interpretation (for < > & in text)
// {@inheritDoc}       → inserts the supertype's Javadoc for this element
// {@value #CONSTANT}  → inserts the constant's value inline

// ---- @param / @return / @throws alignment (convention) ----
/**
 * @param  orderId  the order UUID; must not be null or blank
 * @param  amount   payment amount in GBP; must be &gt; 0.0 and ≤ 10_000.0
 * @return          confirmation token; never null
 * @throws IllegalArgumentException if {@code orderId} is blank or {@code amount} ≤ 0
 * @throws PaymentException         if the payment gateway rejects the transaction
 */

// ---- common mistakes ----
// Bad: @param amount the amount  ← tautological
// Good: @param amount payment in GBP; must be positive and ≤ the account credit limit

// Bad: @return String  ← just restates the return type
// Good: @return confirmation token in the format "TXN-{uuid}"; never null

// Bad: @throws Exception  ← too broad; document the specific exception
// Good: @throws IllegalArgumentException if amount ≤ 0 or orderId is blank
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Javadoc: /** */ before a declaration; javadoc tool produces HTML; IDE shows hover tooltip; block tags structure the content">
  <rect x="8" y="8" width="684" height="184" rx="8" fill="#0d1117"/>

  <!-- Source -->
  <rect x="18" y="20" width="310" height="155" rx="5" fill="#1c2430"/>
  <text x="173" y="35" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">PaymentService.java</text>
  <text x="28" y="50" fill="#8b949e" font-size="8" font-family="monospace">/**</text>
  <text x="28" y="63" fill="#8b949e" font-size="8" font-family="monospace"> * Processes a payment.</text>
  <text x="28" y="76" fill="#8b949e" font-size="8" font-family="monospace"> *</text>
  <text x="28" y="89" fill="#8b949e" font-size="8" font-family="monospace"> * @param orderId  UUID of the order</text>
  <text x="28" y="102" fill="#8b949e" font-size="8" font-family="monospace"> * @param amount   GBP; must be &gt; 0</text>
  <text x="28" y="115" fill="#8b949e" font-size="8" font-family="monospace"> * @return  confirmation token</text>
  <text x="28" y="128" fill="#8b949e" font-size="8" font-family="monospace"> * @throws IllegalArgumentException</text>
  <text x="28" y="141" fill="#8b949e" font-size="8" font-family="monospace"> */</text>
  <text x="28" y="157" fill="#6db33f" font-size="8" font-family="monospace">public String process(</text>
  <text x="28" y="169" fill="#6db33f" font-size="8" font-family="monospace">    String orderId, double amount)</text>

  <!-- Arrow: javadoc tool -->
  <line x1="330" y1="100" x2="380" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>
  <text x="355" y="93" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">javadoc</text>

  <!-- HTML output -->
  <rect x="382" y="20" width="200" height="90" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="482" y="35" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">docs/PaymentService.html</text>
  <text x="392" y="50" fill="#e6edf3" font-size="7.5" font-family="sans-serif">process(orderId, amount)</text>
  <text x="392" y="63" fill="#8b949e" font-size="7" font-family="sans-serif">Processes a payment.</text>
  <text x="392" y="76" fill="#8b949e" font-size="7" font-family="sans-serif">orderId: UUID of the order</text>
  <text x="392" y="89" fill="#8b949e" font-size="7" font-family="sans-serif">amount: GBP; must be &gt; 0</text>
  <text x="392" y="102" fill="#8b949e" font-size="7" font-family="sans-serif">Returns: confirmation token</text>

  <!-- IDE tooltip -->
  <rect x="382" y="120" width="200" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="482" y="134" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">IDE hover tooltip</text>
  <text x="392" y="148" fill="#8b949e" font-size="7" font-family="sans-serif">process(String orderId, double amount)</text>
  <text x="392" y="161" fill="#8b949e" font-size="7" font-family="sans-serif">Processes a payment.</text>
  <text x="392" y="173" fill="#8b949e" font-size="7" font-family="sans-serif">@param orderId UUID of the order</text>
</svg>

`javadoc` reads `/** */` comments and produces HTML API docs; IDEs surface the same content as hover tooltips during development.

## 5. Runnable example

Scenario: a payment service library — write full Javadoc for its public API, demonstrate all common tags, and verify the docs compile cleanly with `-Xdoclint:all`.

### Level 1 — Basic

```java
/**
 * Manages payment orders for the ACME e-commerce platform.
 *
 * <p>Accepts orders in GBP, validates them against gateway limits,
 * and returns a confirmation token on success.
 *
 * @since 1.0
 */
public class JavadocBasic {

    /** Maximum single-order amount in GBP, per payment gateway SLA (PGW-2023-11). */
    public static final double MAX_AMOUNT = 10_000.00;

    /**
     * Processes a payment order.
     *
     * @param orderId unique order identifier in UUID format; must not be null or blank
     * @param amount  payment amount in GBP; must be positive and at most {@value #MAX_AMOUNT}
     * @return        confirmation token in the format {@code "TXN-<orderId>"}; never null
     * @throws IllegalArgumentException if {@code orderId} is blank or {@code amount} is non-positive
     */
    public static String process(String orderId, double amount) {
        if (orderId == null || orderId.isBlank())
            throw new IllegalArgumentException("orderId must not be blank");
        if (amount <= 0 || amount > MAX_AMOUNT)
            throw new IllegalArgumentException("amount must be > 0 and ≤ " + MAX_AMOUNT);
        return "TXN-" + orderId;
    }

    public static void main(String[] args) {
        System.out.println("=== Javadoc basics demo ===\n");

        // Show the API in action
        try {
            String token = process("550e8400-e29b-41d4-a716-446655440000", 299.99);
            System.out.println("Success: " + token);

            process("", 100.00);   // triggers @throws case
        } catch (IllegalArgumentException e) {
            System.out.println("Expected error: " + e.getMessage());
        }

        // Reflect on our own Javadoc
        System.out.println("\n[ Javadoc structure ]");
        System.out.println("  /** ... */   → Javadoc comment");
        System.out.println("  First sentence → appears in method summary table");
        System.out.println("  @param name desc  → parameter documentation");
        System.out.println("  @return desc       → return value documentation");
        System.out.println("  @throws Type desc  → exception documentation");
        System.out.println("  {@code expr}       → inline monospace code");
        System.out.println("  {@value #FIELD}    → inline constant value");
        System.out.println("  {@link Class#m()}  → hyperlink to another element");

        System.out.println("\n[ Generate docs ]");
        System.out.println("  javadoc -d docs -sourcepath src -subpackages com.example");
        System.out.println("  Check:  javadoc -Xdoclint:all -d /dev/null src/...");
    }
}
```

**How to run:** `java JavadocBasic.java`

`{@value #MAX_AMOUNT}` in the `@param` description will render as the actual value `10000.0` in the generated HTML — eliminating duplication between the constant and its documentation.

### Level 2 — Intermediate

Same payment service: use `@link`, `@see`, `@deprecated`, `{@inheritDoc}`, and interface-level Javadoc — the full set of tags a library author writes.

```java
// JavadocIntermediate.java — full tag set demo
/**
 * Contract for payment processors used across the ACME platform.
 *
 * <p>Implementations must be thread-safe and idempotent:
 * submitting the same {@code orderId} twice must return the same token.
 *
 * @see JavadocIntermediate.DefaultProcessor
 * @since 2.0
 */
interface PaymentProcessor {

    /**
     * Submits a payment order.
     *
     * @param  orderId unique order identifier (UUID); must not be null
     * @param  amount  amount in GBP; must be in range {@code (0, 10_000]}
     * @return         confirmation token; never null; idempotent for same orderId
     * @throws IllegalArgumentException if parameters are out of range
     * @throws PaymentException         if the payment gateway is unavailable
     */
    String submit(String orderId, double amount);

    /**
     * @deprecated Use {@link #submit(String, double)} instead.
     *             This method will be removed in version 3.0.
     */
    @Deprecated(since = "2.0", forRemoval = true)
    default String process(String orderId, double amount) {
        return submit(orderId, amount);
    }
}

/** Thrown when the payment gateway returns an error response. */
class PaymentException extends RuntimeException {
    private final int gatewayCode;

    /**
     * Creates a new {@code PaymentException}.
     *
     * @param message     human-readable error description
     * @param gatewayCode the numeric code returned by the payment gateway
     */
    public PaymentException(String message, int gatewayCode) {
        super(message);
        this.gatewayCode = gatewayCode;
    }

    /**
     * Returns the gateway-specific error code.
     *
     * @return gateway error code; positive integer
     */
    public int getGatewayCode() { return gatewayCode; }
}

/** Default implementation — suitable for production use. */
public class JavadocIntermediate implements PaymentProcessor {

    /** {@inheritDoc} Logs the confirmation token for audit purposes. */
    @Override
    public String submit(String orderId, double amount) {
        if (orderId == null || orderId.isBlank())
            throw new IllegalArgumentException("orderId must not be blank");
        if (amount <= 0 || amount > 10_000)
            throw new IllegalArgumentException("amount out of range");
        String token = "TXN-" + orderId.substring(0, Math.min(8, orderId.length()));
        System.out.println("[AUDIT] " + token + "  amount=" + amount);
        return token;
    }

    public static void main(String[] args) {
        System.out.println("=== Javadoc intermediate: full tag set ===\n");

        JavadocIntermediate svc = new JavadocIntermediate();

        System.out.println("[ @deprecated method ]");
        @SuppressWarnings("deprecation")
        String old = svc.process("ORD-001", 99.99);
        System.out.println("  Old method result: " + old);

        System.out.println("\n[ @throws → PaymentException ]");
        try {
            svc.submit(null, 100.00);
        } catch (IllegalArgumentException e) {
            System.out.println("  Caught: " + e.getMessage());
        }

        System.out.println("\n[ Javadoc tag summary ]");
        System.out.printf("  %-25s %s%n", "@param name desc",    "documents a method parameter");
        System.out.printf("  %-25s %s%n", "@return desc",         "documents the return value");
        System.out.printf("  %-25s %s%n", "@throws Type desc",    "documents a checked/unchecked exception");
        System.out.printf("  %-25s %s%n", "@see Reference",       "adds a 'See Also' cross-reference");
        System.out.printf("  %-25s %s%n", "@since version",       "marks the version that added this element");
        System.out.printf("  %-25s %s%n", "@deprecated reason",   "marks element as deprecated");
        System.out.printf("  %-25s %s%n", "{@code expr}",         "inline monospace code");
        System.out.printf("  %-25s %s%n", "{@link Class#method}", "hyperlink to element");
        System.out.printf("  %-25s %s%n", "{@inheritDoc}",        "copy supertype's Javadoc");
        System.out.printf("  %-25s %s%n", "{@value #CONSTANT}",   "inline constant value");
        System.out.printf("  %-25s %s%n", "{@literal text}",      "prevent HTML interpretation");
    }

    static class DefaultProcessor extends JavadocIntermediate {}
}
```

**How to run:** `java JavadocIntermediate.java`

`{@inheritDoc}` in `submit()`'s Javadoc copies the interface's documentation and appends the "Logs the confirmation token" sentence. Without `{@inheritDoc}`, an overriding method's Javadoc starts from scratch.

### Level 3 — Advanced

Same payment service: programmatically run the `javadoc` tool via `javax.tools`, inspect the generated HTML for required elements, and run `-Xdoclint:all` to catch missing or malformed tags.

```java
// JavadocAdvanced.java — generate, verify, and inspect Javadoc programmatically
import java.io.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;

public class JavadocAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== Javadoc advanced: programmatic generation ===\n");

        // Source file with complete, correct Javadoc
        String goodSource = """
            /**
             * Processes payment orders for the ACME platform.
             *
             * @since 1.0
             */
            public class OrderService {

                /** Maximum single-order amount in GBP. */
                public static final double MAX_AMOUNT = 10_000.00;

                /**
                 * Submits a payment order.
                 *
                 * @param  orderId unique order identifier; must not be blank
                 * @param  amount  amount in GBP; must be in range (0, {@value #MAX_AMOUNT}]
                 * @return         confirmation token in the format {@code "TXN-<orderId>"}
                 * @throws IllegalArgumentException if {@code orderId} is blank or amount ≤ 0
                 */
                public static String submit(String orderId, double amount) {
                    if (orderId == null || orderId.isBlank())
                        throw new IllegalArgumentException("orderId must not be blank");
                    if (amount <= 0 || amount > MAX_AMOUNT)
                        throw new IllegalArgumentException("amount out of range");
                    return "TXN-" + orderId;
                }
            }
            """;

        // Source file with MISSING Javadoc (-Xdoclint:all will flag this)
        String missingDocSource = """
            public class UndocumentedService {
                public static final int RETRY_COUNT = 3;

                public static String send(String message) {
                    return "SENT:" + message;
                }
            }
            """;

        Path tmp = Files.createTempDirectory("javadoc-demo");
        Path src = tmp.resolve("src");
        Files.createDirectories(src);
        Path docs = tmp.resolve("docs");
        Files.createDirectories(docs);
        Path badDocs = tmp.resolve("bad-docs");
        Files.createDirectories(badDocs);

        Path goodFile = src.resolve("OrderService.java");
        Path badFile  = src.resolve("UndocumentedService.java");
        Files.writeString(goodFile, goodSource);
        Files.writeString(badFile,  missingDocSource);

        // Run javadoc via DocumentationTool
        DocumentationTool javadocTool = ToolProvider.getSystemDocumentationTool();
        if (javadocTool == null) {
            System.out.println("javadoc tool not available. Showing concept summary.");
            printSummary();
            return;
        }

        System.out.println("[ 1. Generate docs for well-documented class ]");
        StringWriter errOut = new StringWriter();
        int rc1 = javadocTool.run(null, null, new PrintWriter(errOut),
            "-d", docs.toString(),
            "-quiet",
            goodFile.toString());
        System.out.println("  Exit code: " + rc1 + (rc1 == 0 ? " (SUCCESS)" : " (ERRORS)"));
        if (!errOut.toString().isBlank()) System.out.println("  Warnings: " + errOut.toString().strip());

        // Inspect generated HTML
        Path classPage = docs.resolve("OrderService.html");
        if (Files.exists(classPage)) {
            String html = Files.readString(classPage);
            System.out.println("  Generated: " + classPage.getFileName());
            System.out.println("  Contains '@param orderId': " + html.contains("orderId"));
            System.out.println("  Contains 'MAX_AMOUNT':     " + html.contains("MAX_AMOUNT"));
            System.out.println("  Contains 'TXN-':           " + html.contains("TXN-"));
        }

        System.out.println("\n[ 2. Run -Xdoclint:all on undocumented class ]");
        StringWriter doclintErr = new StringWriter();
        int rc2 = javadocTool.run(null, null, new PrintWriter(doclintErr),
            "-d", badDocs.toString(),
            "-Xdoclint:all",
            "-quiet",
            badFile.toString());
        System.out.println("  Exit code: " + rc2);
        System.out.println("  Doclint output (first 5 lines):");
        doclintErr.toString().lines().limit(5).forEach(l -> System.out.println("    " + l));
        System.out.println("  (expected warnings: missing @param, missing @return, missing class comment)");

        Files.walk(tmp).sorted(Comparator.reverseOrder()).map(Path::toFile).forEach(File::delete);

        printSummary();
    }

    static void printSummary() {
        System.out.println("\n[ Javadoc anti-patterns ]");
        System.out.println("  @param amount  the amount       ← tautological; says nothing");
        System.out.println("  @return String                  ← just restates type; useless");
        System.out.println("  @throws Exception               ← too vague; be specific");
        System.out.println("  Copying param description verbatim from method name ← noise");

        System.out.println("\n[ Good patterns ]");
        System.out.println("  @param amount  payment in GBP; must be > 0 and ≤ 10,000");
        System.out.println("  @return  confirmation token in format TXN-{uuid}; never null");
        System.out.println("  @throws IllegalArgumentException  if amount ≤ 0 or orderId is blank");
        System.out.println("  First sentence = complete thought; appears in summary table");

        System.out.println("\n[ When to write Javadoc ]");
        System.out.println("  public/protected members: always");
        System.out.println("  interface methods:        always (they define the contract)");
        System.out.println("  package-private:          if used across multiple classes");
        System.out.println("  private:                  use // only if non-obvious");

        System.out.println("\n[ Tooling integration ]");
        System.out.println("  javadoc -Xdoclint:all  → enforce completeness at build time");
        System.out.println("  Checkstyle JavadocMethod rule → enforce in CI");
        System.out.println("  Maven: mvn javadoc:javadoc");
        System.out.println("  Gradle: ./gradlew javadoc");
    }
}
```

**How to run:** `java JavadocAdvanced.java`

`ToolProvider.getSystemDocumentationTool()` returns the same `javadoc` tool available on the command line. Running it with `-Xdoclint:all` enforces that every `public` member has complete, structurally valid Javadoc — the same check Maven's `javadoc:verify` goal uses in CI.

## 6. Walkthrough

Execution trace in `JavadocAdvanced.main`:

**`javadocTool.run(..., "-d", docs, "-quiet", goodFile)`** compiles and processes `OrderService.java`. The `-quiet` flag suppresses informational messages. Exit code `0` means success. The output is written to `docs/`.

**HTML inspection.** `docs/OrderService.html` contains the rendered Javadoc. `html.contains("orderId")` verifies the `@param orderId` tag was processed and emitted into the HTML. `html.contains("TXN-")` verifies the `{@code "TXN-<orderId>"}` inline tag was rendered as a code span.

**`-Xdoclint:all` on undocumented source.** `UndocumentedService` has a `public` field (`RETRY_COUNT`), a `public` method (`send`), and no class Javadoc. `-Xdoclint:all` emits one warning per missing element: `missing comment`, `missing @param`, `missing @return`. These are treated as warnings by default; `--Werror` escalates them to errors that fail the build.

**`DocumentationTool` vs `javax.tools.JavaCompiler`.** Both implement `Tool`. `DocumentationTool.run()` accepts standard `javadoc` flags (`-d`, `-sourcepath`, `-Xdoclint`). Wrapping it in a `StringWriter` captures output that would normally go to stderr — useful for parsing warnings in CI scripts.

**`{@value #MAX_AMOUNT}`.** The javadoc tool resolves `{@value #MAX_AMOUNT}` at doc-generation time by reading the constant's value from the compiled class. The rendered HTML shows `10000.0` inline — so if the constant changes, the documentation stays accurate without manual editing.

## 7. Gotchas & takeaways

> **`/** */` is NOT the same as `/* */`.** Javadoc requires exactly two asterisks after the slash: `/**`. A single-asterisk block comment `/* */` is ignored by the `javadoc` tool — it produces no documentation. Always use `/**` before public declarations.

> **The first sentence is the summary.** The `javadoc` tool ends the first sentence at the first `.` followed by whitespace (or the first `<p>` tag). Write the first sentence as a complete, standalone description — it appears in the package/class summary table and in IDE completion popups.

- `/**` ... `*/` — Javadoc comment; must immediately precede a declaration.
- Block tags: `@param`, `@return`, `@throws`, `@see`, `@since`, `@deprecated`, `@author`, `@version`.
- Inline tags: `{@code}`, `{@link}`, `{@linkplain}`, `{@literal}`, `{@inheritDoc}`, `{@value}`.
- `javadoc -d docs -sourcepath src -subpackages com.example` generates HTML.
- `-Xdoclint:all` enforces completeness — use in CI.
- Write for API consumers: what the method guarantees, what params must satisfy, what the return means.
- Don't restate the method name or parameter type — say what they mean and what constraints apply.
- Use `{@inheritDoc}` on overrides that add nothing new; add full Javadoc when you narrow the contract.
