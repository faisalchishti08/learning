---
card: java
gi: 1040
slug: static-analysis-spotbugs-pmd-checkstyle-sonarqube
title: "Static analysis (SpotBugs, PMD, Checkstyle, SonarQube)"
---

## 1. What it is

Static analysis tools scan your source code (or compiled bytecode) **without running it**, looking for patterns known to indicate bugs, style violations, or design smells. **SpotBugs** analyzes compiled bytecode for likely bugs (a `null` that can reach a dereference, a resource that's never closed, an `equals`/`hashCode` inconsistency). **PMD** analyzes source code for both bugs and code-smell patterns (an empty `catch` block, unused variables, overly complex methods). **Checkstyle** enforces formatting and style conventions (naming, brace placement, import order) against a configurable rule set. **SonarQube** is a broader platform that aggregates results from analyses like these (plus its own rules) into dashboards tracking code quality, bugs, and "technical debt" over time across a whole codebase.

## 2. Why & when

A human code reviewer is good at judging design and intent, but tedious, mechanical checks — every resource stream closed, every `equals` override paired correctly with `hashCode`, every method under some complexity threshold — are exactly the kind of thing a reviewer can miss on any given pass, especially in a large diff. Static analysis catches these mechanical categories of mistakes automatically, every time, on every commit, without depending on a human happening to notice — the same class of bug the [equals/hashCode contract](1015-equals-hashcode-contract-implementation.md) tutorial described (a `hashCode` based on different fields than `equals`) is exactly the kind of thing SpotBugs is specifically built to flag automatically.

Run static analysis as part of your build (a Maven/Gradle plugin) or CI pipeline so violations are caught before a change merges, not discovered later by a human or, worse, in production. Reach for SpotBugs and PMD for genuine bug-pattern and code-smell detection; reach for Checkstyle when a team needs consistent formatting/style enforcement (often paired with an auto-formatter — see [code formatting](1041-code-formatting-google-java-format-spotless.md) — so the tool fixes the issue rather than just flagging it); reach for SonarQube when you want aggregated, trend-over-time visibility across an entire codebase or organization, not just a single build's pass/fail result.

## 3. Core concept

```xml
<!-- Minimal SpotBugs setup in pom.xml -->
<build>
  <plugins>
    <plugin>
      <groupId>com.github.spotbugs</groupId>
      <artifactId>spotbugs-maven-plugin</artifactId>
      <version>4.8.5.0</version>
      <executions>
        <execution>
          <goals><goal>check</goal></goals> <!-- fails the build on detected bugs -->
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

```java
class OrderService {
    // SpotBugs flags this: 'name' is compared with == instead of .equals() --
    // a classic pattern that works "by accident" for interned string literals
    // but breaks for equal-but-distinct String objects.
    boolean isDefaultOrder(String name) {
        return name == "default"; // BUG PATTERN: reference comparison on String
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Source code flowing through a static analysis step in the build pipeline before tests run, catching bug patterns like reference comparison on Strings before the build succeeds">
  <rect x="20" y="70" width="130" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Source code</text>

  <rect x="200" y="70" width="160" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="280" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Static analysis</text>

  <rect x="420" y="30" width="200" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="520" y="51" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">violations found -&gt; build FAILS</text>

  <rect x="420" y="110" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="131" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">clean -&gt; build continues</text>

  <line x1="150" y1="90" x2="200" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="360" y1="85" x2="420" y2="47" stroke="#f0883e" marker-end="url(#a)"/>
  <line x1="360" y1="95" x2="420" y2="127" stroke="#6db33f" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Static analysis runs as a build step, catching known bug patterns before the code ever executes.

## 5. Runnable example

Scenario: an order-checking method with a classic string-comparison bug, evolving from an undetected mistake into code that's actually correct — demonstrating exactly the kind of pattern SpotBugs is built to catch automatically.

### Level 1 — Basic

```java
// File: OrderCheckBasic.java
public class OrderCheckBasic {
    static boolean isDefaultOrder(String name) {
        return name == "default"; // reference comparison -- a classic SpotBugs finding
    }

    public static void main(String[] args) {
        String literalName = "default";
        String constructedName = new String("default"); // deliberately NOT interned

        System.out.println("literal: " + isDefaultOrder(literalName));
        System.out.println("constructed: " + isDefaultOrder(constructedName));
    }
}
```

**How to run:** save as `OrderCheckBasic.java`, then `javac OrderCheckBasic.java && java OrderCheckBasic` (JDK 17+).

Expected output:
```
literal: true
constructed: false
```

Both `literalName` and `constructedName` hold logically identical string content (`"default"`), but `==` compares object references, not content — `constructedName` is a genuinely separate `String` object (thanks to `new String(...)`), so the reference comparison fails even though the two values are, by any reasonable definition, "the same." A static analysis tool would flag `name == "default"` immediately, without ever needing to run this program to discover the bug.

### Level 2 — Intermediate

```java
// File: OrderCheckIntermediate.java
public class OrderCheckIntermediate {
    static boolean isDefaultOrder(String name) {
        return "default".equals(name); // content comparison -- also null-safe
    }

    public static void main(String[] args) {
        String literalName = "default";
        String constructedName = new String("default");

        System.out.println("literal: " + isDefaultOrder(literalName));
        System.out.println("constructed: " + isDefaultOrder(constructedName));
        System.out.println("null: " + isDefaultOrder(null));
    }
}
```

**How to run:** save as `OrderCheckIntermediate.java`, then `javac OrderCheckIntermediate.java && java OrderCheckIntermediate` (JDK 17+).

Expected output:
```
literal: true
constructed: true
null: false
```

The real-world concern added: `"default".equals(name)` compares actual string *content*, correctly treating `literalName` and `constructedName` as equal despite being different objects. Writing the literal `"default"` first (rather than `name.equals("default")`) is also a deliberate, common defensive habit — it avoids a `NullPointerException` if `name` itself is `null`, since `null.equals(...)` would throw, but `"default".equals(null)` safely returns `false`.

### Level 3 — Advanced

```java
// File: OrderCheckAdvanced.java
import java.util.Objects;

public class OrderCheckAdvanced {
    static boolean isDefaultOrder(String name) {
        return Objects.equals(name, "default"); // null-safe in BOTH directions
    }

    // A method with high cyclomatic complexity -- exactly the kind of pattern
    // PMD flags for readability/maintainability, independent of correctness.
    static String classifyOrder(int priority, boolean isRush, boolean isInternational, double weight) {
        if (isRush) {
            if (isInternational) {
                return weight > 50 ? "RUSH_INTL_HEAVY" : "RUSH_INTL_LIGHT";
            } else {
                return priority > 5 ? "RUSH_HIGH_PRIORITY" : "RUSH_STANDARD";
            }
        } else {
            if (isInternational) {
                return weight > 50 ? "STANDARD_INTL_HEAVY" : "STANDARD_INTL_LIGHT";
            } else {
                return priority > 5 ? "STANDARD_HIGH_PRIORITY" : "STANDARD_LOW_PRIORITY";
            }
        }
        // A static analysis tool like PMD would flag this method's cyclomatic
        // complexity as high -- worth refactoring into smaller, named pieces
        // even though it is not, strictly speaking, a BUG.
    }

    public static void main(String[] args) {
        System.out.println("null-safe check: " + isDefaultOrder(null));
        System.out.println("classification: " + classifyOrder(8, true, false, 10.0));
        System.out.println("classification: " + classifyOrder(3, false, true, 75.0));
    }
}
```

**How to run:** save as `OrderCheckAdvanced.java`, then `javac OrderCheckAdvanced.java && java OrderCheckAdvanced` (JDK 17+).

Expected output:
```
null-safe check: false
classification: RUSH_HIGH_PRIORITY
classification: STANDARD_INTL_HEAVY
```

The production-flavored hard case: `Objects.equals(name, "default")` is null-safe regardless of which argument might be `null`, fixing even the small remaining asymmetry of Level 2's approach (`"default".equals(name)` only guards against `name` being `null`, not both sides). `classifyOrder` is a working, correct method — but its nested conditionals are exactly the kind of *complexity* smell PMD or SonarQube would flag as worth refactoring for maintainability, distinct entirely from a "bug."

## 6. Walkthrough

Tracing `classifyOrder(3, false, true, 75.0)` in `OrderCheckAdvanced.main`:

1. `isRush` is `false`, so the outer `if (isRush)` branch is skipped and control goes to the `else` block.
2. `isInternational` is `true`, so the inner `if (isInternational)` branch is entered.
3. `weight > 50` evaluates `75.0 > 50`, which is `true`, so `"STANDARD_INTL_HEAVY"` is returned.
4. This result is printed as `"classification: STANDARD_INTL_HEAVY"`.
5. Notice that reaching this single return statement required navigating through two levels of nested `if`/`else` — and there are eight total distinct return statements reachable through different combinations of `isRush`, `isInternational`, and the two numeric comparisons. This is exactly the shape a cyclomatic-complexity metric measures: the number of independent paths through a method's control flow.
6. A tool like PMD or SonarQube would compute this method's complexity score and flag it if it exceeds a configured threshold — not because the logic is wrong (it correctly classifies every combination, as demonstrated by both `println` calls producing correct results), but because a method with many nested branches is harder for a human to verify by inspection and more likely to develop a subtle bug the next time someone adds a ninth case without fully tracing every existing path first.

## 7. Gotchas & takeaways

> **Gotcha:** static analysis findings are not all equally trustworthy — a tool flagging `name == "default"` as a bug is almost always correct (string reference comparison is a well-established anti-pattern), but a complexity or style warning is often a judgment call requiring human context; blindly "fixing" every flagged item without considering whether the fix genuinely improves the code can make things worse, not better.

- SpotBugs analyzes compiled bytecode for likely bug patterns (like `==` comparison on `String`, unclosed resources, `equals`/`hashCode` inconsistencies).
- PMD analyzes source code for both bugs and code-smell patterns (unused variables, high complexity, empty `catch` blocks).
- Checkstyle enforces formatting and naming conventions against a configurable rule set, often paired with an auto-formatter that fixes issues rather than just flagging them.
- SonarQube aggregates results across a codebase into dashboards tracking quality trends over time, rather than just pass/fail results for a single build.
- Running these tools as part of the build (failing the build on genuine violations) catches mechanical categories of bugs and style issues before a human reviewer even sees the change.
- Not every flagged item deserves an unquestioning fix — complexity and style warnings often require human judgment about whether the suggested change genuinely improves the code, unlike well-established, high-confidence bug patterns (like `String` reference comparison).
