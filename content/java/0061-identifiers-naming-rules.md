---
card: java
gi: 61
slug: identifiers-naming-rules
title: Identifiers & naming rules
---

## 1. What it is

An **identifier** is any name you invent in Java: for a class, method, variable, field, parameter, or label. Java's lexer recognises an identifier as a sequence of **Unicode letters, digits, currency symbols, and connecting punctuation**, subject to three hard rules:

1. Must **not start with a digit**.
2. Must **not be a reserved keyword** (`if`, `class`, `return`, …).
3. Must **not be a reserved literal** (`true`, `false`, `null`).

```java
// Valid identifiers
int orderCount;
String _name;
double $rate;
long μsElapsed;          // Unicode letter ✓
class Ω_Handler { }      // Greek + underscore ✓

// Invalid identifiers
// int 2fast;            // starts with digit ✗
// String class;         // reserved keyword ✗
// boolean true;         // reserved literal ✗
// double order-count;   // hyphen not allowed ✗
```

## 2. Why & when

The rule set exists so the compiler can tokenise source code unambiguously. Because Java uses Unicode for source files, identifiers may include letters from any script — Arabic, Chinese, Greek, etc. In practice most teams restrict to ASCII for portability. Understanding the rules matters when:
- A name you chose causes a compile error (starts with digit, clashes with keyword).
- You read foreign-language code or auto-generated identifiers.
- A linter flags a name as non-conventional (vs non-legal — two different issues).

## 3. Core concept

```java
// Character set allowed in identifiers:
// Character.isJavaIdentifierStart(ch) → true for first character
// Character.isJavaIdentifierPart(ch)  → true for subsequent characters

// isJavaIdentifierStart: letters (any Unicode category Lu/Ll/Lt/Lm/Lo/Nl),
//   currency signs ($), connecting punctuation (_)
// isJavaIdentifierPart: above + digits (Nd), combining marks, non-spacing marks

// Length: unlimited (no maximum imposed by spec)

// Case sensitivity: Java is case-sensitive
int order = 1;
int Order = 2;    // different variable — compiles fine
int ORDER = 3;    // yet another — different again

// $ and _ are legal but have conventions:
// _   : prefix for "private-ish" (Python tradition leaking in) — avoid in Java
// $   : generated code (inner classes, lambdas) — avoid in hand-written code

// Checking programmatically:
String candidate = "2fast";
System.out.println(Character.isJavaIdentifierStart(candidate.charAt(0)));  // false

// Unicode identifier (legal, discouraged in practice):
// class 注文Handler { }  — compiles, but most teams disallow non-ASCII

// isKeyword check — no JDK method; compare against the list manually
// (see gi 63 — reserved keywords tutorial)
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java identifier rules: first char must be letter/$/_, rest can also include digits; keywords and literals excluded">
  <rect x="8" y="8" width="684" height="174" rx="8" fill="#0d1117"/>

  <!-- First char box -->
  <rect x="20" y="24" width="200" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">First character</text>
  <text x="120" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Letter (any Unicode)</text>
  <text x="120" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">$ (currency sign)</text>
  <text x="120" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">_ (connecting punct)</text>
  <line x1="40" y1="96" x2="200" y2="96" stroke="#8b949e" stroke-width="0.5"/>
  <text x="120" y="111" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">NOT: digit 0–9</text>
  <text x="120" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">NOT: keyword</text>
  <text x="120" y="139" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">NOT: true/false/null</text>
  <text x="120" y="153" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">NOT: operator/separator</text>

  <!-- Arrow -->
  <text x="234" y="98" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">+</text>

  <!-- Subsequent chars box -->
  <rect x="248" y="24" width="210" height="140" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="353" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Subsequent characters (0..N)</text>
  <text x="353" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Everything above, PLUS:</text>
  <text x="353" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Digit 0–9</text>
  <text x="353" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Combining/non-spacing marks</text>
  <text x="353" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Unlimited length</text>

  <!-- Arrow -->
  <text x="473" y="98" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">→</text>

  <!-- Result box -->
  <rect x="488" y="24" width="196" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="586" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Valid examples</text>
  <text x="586" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">orderCount</text>
  <text x="586" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">MAX_RETRIES</text>
  <text x="586" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">_legacyField</text>
  <text x="586" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">$generated</text>
  <text x="586" y="114" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">μsElapsed</text>
  <text x="586" y="128" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">x1</text>
  <text x="586" y="144" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">case-sensitive</text>
</svg>

First character: letter / $ / _. Subsequent: same plus digits. Keywords and reserved literals never valid regardless.

## 5. Runnable example

Scenario: a token validator for an order system that checks whether candidate field names are valid Java identifiers and explains why each passes or fails.

### Level 1 — Basic

```java
public class IdentifierRulesBasic {
    public static void main(String[] args) {
        System.out.println("=== Identifier rules demo ===\n");

        String[] candidates = {
            "orderCount",    // valid
            "Order_ID",      // valid
            "_legacyField",  // valid (discouraged)
            "$generated",    // valid (discouraged)
            "2fast",         // invalid: starts with digit
            "order-count",   // invalid: hyphen
            "class",         // invalid: keyword
        };

        for (String c : candidates) {
            System.out.printf("  %-20s  %s%n", c, classify(c));
        }
    }

    static String classify(String s) {
        if (s.isEmpty()) return "INVALID: empty";
        if (!Character.isJavaIdentifierStart(s.charAt(0)))
            return "INVALID: bad first char '" + s.charAt(0) + "'";
        for (int i = 1; i < s.length(); i++)
            if (!Character.isJavaIdentifierPart(s.charAt(i)))
                return "INVALID: bad char '" + s.charAt(i) + "' at pos " + i;
        return "valid  ✓";
    }
}
```

**How to run:** `java IdentifierRulesBasic.java`

`Character.isJavaIdentifierStart` and `Character.isJavaIdentifierPart` are the exact methods the Java compiler uses internally to tokenise source code. Calling them lets us replicate the compiler's logic precisely.

### Level 2 — Intermediate

Same validator extended to also catch reserved keywords and reserved literals, and report which rule each candidate breaks.

```java
import java.util.*;

public class IdentifierRulesIntermediate {

    static final Set<String> KEYWORDS = Set.of(
        "abstract","assert","boolean","break","byte","case","catch","char","class",
        "const","continue","default","do","double","else","enum","extends","final",
        "finally","float","for","goto","if","implements","import","instanceof","int",
        "interface","long","native","new","package","private","protected","public",
        "return","short","static","strictfp","super","switch","synchronized","this",
        "throw","throws","transient","try","var","void","volatile","while"
    );
    static final Set<String> RESERVED_LITERALS = Set.of("true","false","null");

    public static void main(String[] args) {
        System.out.println("=== Extended identifier validator ===\n");

        String[] candidates = {
            "orderCount", "Order_ID", "_legacyField", "$generated",
            "2fast", "order-count", "class", "return", "true", "null",
            "μsElapsed", "x", "MAX_RETRIES_5"
        };

        System.out.printf("  %-22s  %-8s  %s%n", "Candidate", "Valid?", "Reason");
        System.out.println("  " + "-".repeat(60));
        for (String c : candidates) {
            String[] result = validate(c);
            System.out.printf("  %-22s  %-8s  %s%n", c, result[0], result[1]);
        }
    }

    static String[] validate(String s) {
        if (s.isEmpty())
            return new String[]{"INVALID", "empty string"};
        if (!Character.isJavaIdentifierStart(s.charAt(0)))
            return new String[]{"INVALID",
                "first char '" + s.charAt(0) + "' not allowed (digit or operator)"};
        for (int i = 1; i < s.length(); i++)
            if (!Character.isJavaIdentifierPart(s.charAt(i)))
                return new String[]{"INVALID",
                    "char '" + s.charAt(i) + "' at pos " + i + " not allowed"};
        if (KEYWORDS.contains(s))
            return new String[]{"INVALID", "reserved keyword"};
        if (RESERVED_LITERALS.contains(s))
            return new String[]{"INVALID", "reserved literal"};
        return new String[]{"valid  ✓", "passes all rules"};
    }
}
```

**How to run:** `java IdentifierRulesIntermediate.java`

The validator now applies all three rules in the correct order: character-set check first (compiler tokenisation), then keyword collision, then literal collision — matching the exact sequence a Java compiler uses.

### Level 3 — Advanced

Same system grown to a full linter: validates candidates, scores them against team naming conventions (camelCase for variables, PascalCase for classes, UPPER_SNAKE for constants), and produces a detailed report.

```java
import java.util.*;
import java.util.regex.*;

public class IdentifierRulesAdvanced {

    static final Set<String> KEYWORDS = Set.of(
        "abstract","assert","boolean","break","byte","case","catch","char","class",
        "const","continue","default","do","double","else","enum","extends","final",
        "finally","float","for","goto","if","implements","import","instanceof","int",
        "interface","long","native","new","package","private","protected","public",
        "return","short","static","strictfp","super","switch","synchronized","this",
        "throw","throws","transient","try","var","void","volatile","while"
    );
    static final Set<String> RESERVED_LITERALS = Set.of("true","false","null");

    enum Kind { VARIABLE, CLASS, CONSTANT }
    record Check(String name, Kind kind) {}

    public static void main(String[] args) {
        System.out.println("=== Full identifier linter ===\n");

        List<Check> checks = List.of(
            new Check("orderCount",      Kind.VARIABLE),
            new Check("OrderService",    Kind.CLASS),
            new Check("MAX_RETRIES",     Kind.CONSTANT),
            new Check("order_count",     Kind.VARIABLE),   // snake_case — bad for variable
            new Check("orderservice",    Kind.CLASS),      // all lower — bad for class
            new Check("maxRetries",      Kind.CONSTANT),   // camel — bad for constant
            new Check("2fast",           Kind.VARIABLE),
            new Check("class",           Kind.VARIABLE),
            new Check("_legacyField",    Kind.VARIABLE),   // legal but discouraged
            new Check("$generated",      Kind.VARIABLE),   // legal but discouraged
            new Check("μsElapsed",       Kind.VARIABLE)    // unicode — legal
        );

        System.out.printf("  %-22s  %-10s  %-8s  %s%n", "Name", "Kind", "Legal?", "Convention");
        System.out.println("  " + "-".repeat(70));
        for (Check c : checks) {
            String legal = isLegal(c.name());
            String conv  = conventionCheck(c.name(), c.kind());
            System.out.printf("  %-22s  %-10s  %-8s  %s%n",
                c.name(), c.kind(), legal.isEmpty() ? "yes ✓" : "NO", legal + conv);
        }

        System.out.println("\n[ Unicode identifier demo ]");
        String unicodeName = "注文Handler";  // 注文Handler
        System.out.println("  '" + unicodeName + "' legal? " + (isLegal(unicodeName).isEmpty() ? "yes" : "no"));
        System.out.println("  (Most teams disallow non-ASCII via Checkstyle illegalIdentifierNames)");
    }

    static String isLegal(String s) {
        if (s.isEmpty()) return "empty; ";
        if (!Character.isJavaIdentifierStart(s.charAt(0)))
            return "bad first char; ";
        for (int i = 1; i < s.length(); i++)
            if (!Character.isJavaIdentifierPart(s.charAt(i)))
                return "bad char at " + i + "; ";
        if (KEYWORDS.contains(s))  return "keyword; ";
        if (RESERVED_LITERALS.contains(s)) return "reserved literal; ";
        return "";
    }

    static String conventionCheck(String s, Kind kind) {
        return switch (kind) {
            case VARIABLE -> Pattern.matches("[a-z][a-zA-Z0-9]*", s) ? "camelCase ✓"
                           : s.startsWith("_") || s.startsWith("$") ? "warn: avoid _ or $ prefix"
                           : "warn: expected camelCase";
            case CLASS    -> Pattern.matches("[A-Z][a-zA-Z0-9]*", s) ? "PascalCase ✓"
                           : "warn: expected PascalCase";
            case CONSTANT -> Pattern.matches("[A-Z][A-Z0-9_]*", s) ? "UPPER_SNAKE ✓"
                           : "warn: expected UPPER_SNAKE";
        };
    }
}
```

**How to run:** `java IdentifierRulesAdvanced.java`

The linter separates two concerns: **legality** (Java spec — compiler enforces) and **convention** (team style — Checkstyle/SonarQube enforce). A name can be legal but conventionally wrong (`order_count` for a variable) or both legal and conventional (`orderCount`).

## 6. Walkthrough

Execution trace in `IdentifierRulesAdvanced.main`:

**Input list.** Eleven `Check` records are built, each pairing a candidate name with an expected naming kind (VARIABLE, CLASS, or CONSTANT).

**`isLegal(s)` — character-set phase.** For each candidate, `isLegal` checks `Character.isJavaIdentifierStart(s.charAt(0))` for the first character. `2fast` fails here immediately: `'2'` has Unicode category Nd (decimal digit), which `isJavaIdentifierStart` rejects. `μ` (Greek lowercase mu) has category Ll (lowercase letter), so it passes. After the first character, each remaining character is checked with `isJavaIdentifierPart`, which additionally allows digits. If the whole string passes character checks, the method checks `KEYWORDS` and `RESERVED_LITERALS`.

**`conventionCheck(s, kind)` — style phase.** Uses `Pattern.matches` with anchored regexes: `[a-z][a-zA-Z0-9]*` for camelCase variables, `[A-Z][a-zA-Z0-9]*` for PascalCase classes, `[A-Z][A-Z0-9_]*` for UPPER_SNAKE constants. `_legacyField` passes character checks but starts with `_`, triggering the "warn: avoid _ or $ prefix" path.

**Unicode demo.** `"注文Handler"` is the string `注文Handler` — `注` and `文` are CJK ideographs (Unicode category Lo = letter other). `Character.isJavaIdentifierStart('注')` returns `true`. The name is legally valid; a Checkstyle `illegalIdentifierNames` rule would block it at CI time.

**Output.** Each row shows the candidate, its expected kind, legal status, and convention verdict — giving a complete picture of both compiler rules and team style rules in one report.

## 7. Gotchas & takeaways

> **`var` is not a reserved keyword — it is a reserved type name.** You cannot use `var` as a type name or in certain positions, but it IS a legal identifier in other positions (`int var = 1;` compiles). This is intentional: adding it as a hard keyword would have broken code that already used `var` as a variable name before JDK 10.

- First char: letter / `$` / `_`. Subsequent: same + digits. Case-sensitive.
- `Character.isJavaIdentifierStart` / `isJavaIdentifierPart` mirror the compiler's exact checks.
- Keywords and reserved literals (`true`, `false`, `null`) are never valid identifiers, regardless of character set.
- `$` and `_` prefixes are legal but conventionally reserved for generated/legacy code.
- Unicode letters are legal; most teams ban non-ASCII via Checkstyle for readability.
- Legality (compiler) and convention (style guide) are separate concerns — both matter in production code.
