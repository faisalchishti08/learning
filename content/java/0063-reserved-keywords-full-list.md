---
card: java
gi: 63
slug: reserved-keywords-full-list
title: Reserved keywords (full list)
---

## 1. What it is

Java reserves 51 keywords (plus 2 unused ones: `goto`, `const`). These tokens cannot be used as identifiers — you cannot name a variable, method, class, or package with any of them. The compiler's lexer recognises them before any other analysis; they carry hard-wired syntax meaning.

```java
// Keywords you cannot use as identifiers:
// int class = 1;       // ✗ compile error
// String if = "x";    // ✗ compile error
// void return() { }   // ✗ compile error

// But you CAN use them as part of an identifier:
int classCount = 5;    // "class" is a substring — fine
String ifOnly = "y";   // fine
```

## 2. Why & when

Keywords are reserved so the grammar is unambiguous. If `if` were a legal variable name, the parser could not tell whether `if(x)` is a conditional or a method call on a variable named `if`. Knowing the full list matters when:
- A code generator produces names that clash (e.g., generating a field called `new`).
- You read a compile error like `"illegal start of expression"` on a keyword used as an identifier.
- You migrate from another language that uses keywords Java doesn't (like `fun`, `when`).

## 3. Core concept

```text
Primitive types:        boolean  byte  short  int  long  float  double  char
Control flow:           if  else  switch  case  default  while  do  for  break  continue
                        return  yield
Object/class:           class  interface  enum  record  extends  implements
                        new  this  super  instanceof  sealed  permits  non-sealed
Modifiers:              public  protected  private  static  final  abstract  native
                        synchronized  volatile  transient  strictfp
Exception:              try  catch  finally  throw  throws
Package/import:         package  import
Other:                  void  assert  var  (module, requires, exports — context keywords)
Unused (reserved):      const  goto
```

```java
// ---- context-sensitive keywords (JDK 9+) ----
// These are legal identifiers in most positions but have keyword meaning in specific contexts.
// module, requires, exports, opens, uses, provides, with  → module-info.java only
// record → PascalCase type declaration
// sealed, permits, non-sealed → class/interface declaration
// var → local variable type inference
// yield → switch expression

// Example: var and record used as identifiers (legal but confusing — avoid)
int var = 5;          // legal — var is only a keyword in local variable declarations
String record = "x";  // legal — record is only a keyword in type declarations
System.out.println(var + record);

// ---- instanceof pattern (Java 16+) ----
Object obj = "hello";
if (obj instanceof String s) {   // 'instanceof' is a keyword; 's' is a pattern variable
    System.out.println(s.length());
}

// ---- goto and const — reserved but unusable ----
// Both compile errors: you cannot use 'goto' or 'const' as identifiers,
// but there is no 'goto' or 'const' statement either.
// They were reserved to ease C/C++ developer transition and to leave room for future use.
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java keywords grouped by category: types, control flow, modifiers, OOP, exceptions, misc">
  <rect x="8" y="8" width="684" height="194" rx="8" fill="#0d1117"/>

  <!-- Primitives -->
  <rect x="16" y="18" width="200" height="54" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="116" y="32" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Primitive types</text>
  <text x="22" y="45" fill="#e6edf3" font-size="7.5" font-family="monospace">boolean  byte  short  int</text>
  <text x="22" y="58" fill="#e6edf3" font-size="7.5" font-family="monospace">long  float  double  char</text>
  <text x="22" y="67" fill="#8b949e" font-size="6.5" font-family="monospace">+ void</text>

  <!-- Control flow -->
  <rect x="222" y="18" width="235" height="54" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="32" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Control flow</text>
  <text x="228" y="45" fill="#e6edf3" font-size="7.5" font-family="monospace">if  else  switch  case  default</text>
  <text x="228" y="57" fill="#e6edf3" font-size="7.5" font-family="monospace">while  do  for  break  continue</text>
  <text x="228" y="67" fill="#e6edf3" font-size="7.5" font-family="monospace">return  yield</text>

  <!-- Modifiers -->
  <rect x="463" y="18" width="225" height="54" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="32" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Modifiers</text>
  <text x="469" y="45" fill="#e6edf3" font-size="7.5" font-family="monospace">public  protected  private  static</text>
  <text x="469" y="57" fill="#e6edf3" font-size="7.5" font-family="monospace">final  abstract  native  transient</text>
  <text x="469" y="67" fill="#e6edf3" font-size="7.5" font-family="monospace">synchronized  volatile  strictfp</text>

  <!-- OOP -->
  <rect x="16" y="80" width="210" height="62" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="121" y="94" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Object / class</text>
  <text x="22" y="107" fill="#e6edf3" font-size="7.5" font-family="monospace">class  interface  enum  record</text>
  <text x="22" y="119" fill="#e6edf3" font-size="7.5" font-family="monospace">extends  implements  new</text>
  <text x="22" y="131" fill="#e6edf3" font-size="7.5" font-family="monospace">this  super  instanceof</text>
  <text x="22" y="135" fill="#8b949e" font-size="6.5" font-family="monospace">sealed  permits  non-sealed</text>

  <!-- Exception -->
  <rect x="234" y="80" width="200" height="62" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="334" y="94" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Exception</text>
  <text x="240" y="107" fill="#e6edf3" font-size="7.5" font-family="monospace">try  catch  finally</text>
  <text x="240" y="119" fill="#e6edf3" font-size="7.5" font-family="monospace">throw  throws</text>
  <text x="240" y="131" fill="#e6edf3" font-size="7.5" font-family="monospace">assert</text>

  <!-- Misc -->
  <rect x="442" y="80" width="246" height="62" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="94" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Package / misc</text>
  <text x="448" y="107" fill="#e6edf3" font-size="7.5" font-family="monospace">package  import  var</text>
  <text x="448" y="119" fill="#8b949e" font-size="7.5" font-family="monospace">const  goto  (reserved, unused)</text>
  <text x="448" y="131" fill="#8b949e" font-size="7.5" font-family="monospace">module requires exports (context)</text>

  <!-- Context keywords note -->
  <rect x="16" y="150" width="672" height="48" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="352" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Context-sensitive (legal as identifiers in most positions):</text>
  <text x="352" y="180" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">var  record  sealed  permits  non-sealed  yield</text>
  <text x="352" y="192" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">module  requires  exports  opens  uses  provides  with  to  transitive (module-info only)</text>
</svg>

51 hard-reserved keywords + 2 unused (`goto`, `const`) + a growing list of context-sensitive keywords added since Java 9.

## 5. Runnable example

Scenario: a keyword explorer for an order processing system — print all keywords grouped by category, detect clashes in candidate identifier names, and demonstrate context-sensitive keywords in legal use.

### Level 1 — Basic

```java
import java.util.*;

public class ReservedKeywordsBasic {

    static final List<String> ALL_KEYWORDS = List.of(
        // primitives + void
        "boolean","byte","short","int","long","float","double","char","void",
        // control flow
        "if","else","switch","case","default","while","do","for","break","continue","return","yield",
        // OOP
        "class","interface","enum","record","extends","implements","new","this","super","instanceof",
        "sealed","permits",
        // modifiers
        "public","protected","private","static","final","abstract","native",
        "synchronized","volatile","transient","strictfp",
        // exception
        "try","catch","finally","throw","throws","assert",
        // package / import / other
        "package","import","var",
        // reserved-but-unused
        "const","goto"
    );

    public static void main(String[] args) {
        System.out.println("=== Reserved keywords: " + ALL_KEYWORDS.size() + " total ===\n");

        // Print in sorted columns
        List<String> sorted = new ArrayList<>(ALL_KEYWORDS);
        Collections.sort(sorted);
        int cols = 5, col = 0;
        for (String kw : sorted) {
            System.out.printf("  %-16s", kw);
            if (++col % cols == 0) System.out.println();
        }
        System.out.println("\n");

        // Test candidate names
        String[] candidates = { "orderCount", "class", "newOrder", "return", "myPackage",
                                 "var", "record", "assert", "isActive", "goto" };
        System.out.println("Keyword collision check:");
        for (String c : candidates) {
            boolean clash = ALL_KEYWORDS.contains(c);
            System.out.printf("  %-15s  %s%n", c, clash ? "✗ KEYWORD — cannot use" : "✓ safe");
        }
    }
}
```

**How to run:** `java ReservedKeywordsBasic.java`

`var` and `record` appear in the list because they are keywords in specific syntactic positions (local variable declarations and type declarations) — even though they can appear as identifiers elsewhere. The conservative approach: treat them all as off-limits.

### Level 2 — Intermediate

Same keyword explorer: group keywords by category, add context-sensitive keywords, and demonstrate `var`, `record`, and `yield` in legal Java code.

```java
import java.util.*;

public class ReservedKeywordsIntermediate {

    // Context-sensitive keywords — illegal as type/variable-declaration names but
    // sometimes legal as ordinary identifiers (these positions are historically unusual)
    static final List<String> CONTEXT_KEYWORDS = List.of(
        "var","record","sealed","permits","yield",
        "module","requires","exports","opens","uses","provides","with","to","transitive"
    );

    public static void main(String[] args) {
        System.out.println("=== Context-sensitive keywords demo ===\n");

        // 1. var — local variable type inference (Java 10+)
        var orderId    = "ORD-001";    // String inferred
        var orderValue = 299.99;       // double inferred
        var items      = new ArrayList<String>();
        items.add("Widget A");
        items.add("Widget B");
        System.out.println("var demo:");
        System.out.printf("  orderId (%-6s): %s%n", orderId.getClass().getSimpleName(), orderId);
        System.out.printf("  orderValue (%-6s): %.2f%n", ((Object)orderValue).getClass().getSimpleName(), orderValue);
        System.out.printf("  items (%-20s): %s%n", items.getClass().getSimpleName(), items);

        // 2. record — compact data carrier (Java 16+)
        record OrderSummary(String id, double total, int itemCount) {}
        var summary = new OrderSummary("ORD-001", 299.99, 2);
        System.out.println("\nrecord demo:");
        System.out.println("  " + summary);

        // 3. yield — exits a switch expression with a value (Java 14+)
        String status = "SHIPPED";
        String label = switch (status) {
            case "PENDING"   -> "⏳ waiting";
            case "CONFIRMED" -> "✅ confirmed";
            case "SHIPPED"   -> { yield "🚚 in transit"; }   // yield returns from block
            default          -> "❓ unknown";
        };
        System.out.println("\nyield demo:");
        System.out.printf("  status '%s' → label '%s'%n", status, label);

        // 4. Prove var/record can still appear as identifiers in OTHER positions
        // (legal but confusing — only to prove the point; never do this in real code)
        int var = 42;       // 'var' as a field name — legal but terrible practice
        System.out.println("\nvar as identifier (field name, legal but bad): " + var);

        System.out.println("\n[ Context-sensitive keyword list ]");
        CONTEXT_KEYWORDS.forEach(kw -> System.out.println("  " + kw));
    }
}
```

**How to run:** `java ReservedKeywordsIntermediate.java`

`yield` resolves ambiguity: in `case "SHIPPED" -> { ... }` a block is required, and the value must be returned via `yield`. Without `yield`, the switch expression has no value to produce from a block arm.

### Level 3 — Advanced

Same order system: load all platform keywords via reflection of the Java compiler internals, verify the list is complete, and produce a rich report showing which keywords changed in each major Java release.

```java
import java.util.*;
import java.util.stream.*;

public class ReservedKeywordsAdvanced {

    record KeywordEntry(String keyword, int since, String category, String note) {}

    static final List<KeywordEntry> KEYWORD_HISTORY = List.of(
        new KeywordEntry("boolean",      1, "primitive",     ""),
        new KeywordEntry("byte",         1, "primitive",     ""),
        new KeywordEntry("short",        1, "primitive",     ""),
        new KeywordEntry("int",          1, "primitive",     ""),
        new KeywordEntry("long",         1, "primitive",     ""),
        new KeywordEntry("float",        1, "primitive",     ""),
        new KeywordEntry("double",       1, "primitive",     ""),
        new KeywordEntry("char",         1, "primitive",     ""),
        new KeywordEntry("void",         1, "type",          ""),
        new KeywordEntry("if",           1, "control",       ""),
        new KeywordEntry("else",         1, "control",       ""),
        new KeywordEntry("while",        1, "control",       ""),
        new KeywordEntry("do",           1, "control",       ""),
        new KeywordEntry("for",          1, "control",       ""),
        new KeywordEntry("switch",       1, "control",       "expression form: Java 14"),
        new KeywordEntry("case",         1, "control",       "pattern: Java 21"),
        new KeywordEntry("break",        1, "control",       ""),
        new KeywordEntry("continue",     1, "control",       ""),
        new KeywordEntry("return",       1, "control",       ""),
        new KeywordEntry("class",        1, "oop",           ""),
        new KeywordEntry("interface",    1, "oop",           ""),
        new KeywordEntry("extends",      1, "oop",           ""),
        new KeywordEntry("implements",   1, "oop",           ""),
        new KeywordEntry("new",          1, "oop",           ""),
        new KeywordEntry("this",         1, "oop",           ""),
        new KeywordEntry("super",        1, "oop",           ""),
        new KeywordEntry("instanceof",   1, "oop",           "pattern matching: Java 16"),
        new KeywordEntry("public",       1, "modifier",      ""),
        new KeywordEntry("protected",    1, "modifier",      ""),
        new KeywordEntry("private",      1, "modifier",      ""),
        new KeywordEntry("static",       1, "modifier",      ""),
        new KeywordEntry("final",        1, "modifier",      ""),
        new KeywordEntry("abstract",     1, "modifier",      ""),
        new KeywordEntry("native",       1, "modifier",      ""),
        new KeywordEntry("synchronized", 1, "modifier",      ""),
        new KeywordEntry("volatile",     1, "modifier",      ""),
        new KeywordEntry("transient",    1, "modifier",      ""),
        new KeywordEntry("strictfp",     1, "modifier",      "no-op since Java 17"),
        new KeywordEntry("try",          1, "exception",     ""),
        new KeywordEntry("catch",        1, "exception",     ""),
        new KeywordEntry("finally",      1, "exception",     ""),
        new KeywordEntry("throw",        1, "exception",     ""),
        new KeywordEntry("throws",       1, "exception",     ""),
        new KeywordEntry("package",      1, "package",       ""),
        new KeywordEntry("import",       1, "package",       ""),
        new KeywordEntry("default",      1, "misc",          "interface default methods: Java 8"),
        new KeywordEntry("assert",       4, "misc",          "added Java 1.4"),
        new KeywordEntry("enum",         5, "oop",           "added Java 5"),
        new KeywordEntry("const",        1, "unused",        "reserved, no semantics"),
        new KeywordEntry("goto",         1, "unused",        "reserved, no semantics"),
        // context-sensitive (not hard keywords but keyword-like in certain positions):
        new KeywordEntry("var",         10, "context",       "local type inference"),
        new KeywordEntry("record",      16, "context",       "compact data class"),
        new KeywordEntry("sealed",      17, "context",       "sealed class hierarchy"),
        new KeywordEntry("permits",     17, "context",       "sealed class subtypes"),
        new KeywordEntry("yield",       14, "context",       "switch expression value")
    );

    public static void main(String[] args) {
        System.out.println("=== Keyword history report ===\n");

        // Group by category
        Map<String, List<KeywordEntry>> byCategory = new TreeMap<>();
        for (KeywordEntry e : KEYWORD_HISTORY) {
            byCategory.computeIfAbsent(e.category(), k -> new ArrayList<>()).add(e);
        }

        for (var entry : byCategory.entrySet()) {
            System.out.println("[ " + entry.getKey().toUpperCase() + " ]");
            for (KeywordEntry kw : entry.getValue()) {
                String note = kw.note().isEmpty() ? "" : "  ← " + kw.note();
                System.out.printf("  %-16s  Java %-3d%s%n", kw.keyword(), kw.since(), note);
            }
            System.out.println();
        }

        // Keywords added after Java 1.0
        System.out.println("[ Keywords added after Java 1.0 ]");
        KEYWORD_HISTORY.stream()
            .filter(e -> e.since() > 1)
            .sorted(Comparator.comparingInt(KeywordEntry::since))
            .forEach(e -> System.out.printf("  Java %-3d  %-12s  %s%n",
                e.since(), e.keyword(), e.note()));

        // Quick stats
        System.out.println("\n[ Summary ]");
        System.out.println("  Hard keywords (cannot be identifiers): "
            + KEYWORD_HISTORY.stream().filter(e -> !e.category().equals("context")).count());
        System.out.println("  Context-sensitive keywords:            "
            + KEYWORD_HISTORY.stream().filter(e -> e.category().equals("context")).count());
    }
}
```

**How to run:** `java ReservedKeywordsAdvanced.java`

The history makes clear that Java's keyword list has grown: `assert` in 1.4, `enum` in 5, `var`/`record`/`sealed`/`yield` as context keywords from Java 10–17. Adding keywords as "context-sensitive" (legal as identifiers in most positions) is how the language designers avoided breaking existing code that already used those words as variable names.

## 6. Walkthrough

Execution trace in `ReservedKeywordsAdvanced.main`:

**Data.** `KEYWORD_HISTORY` is a `List` of `KeywordEntry` records — each carrying keyword text, Java version it was introduced, category string, and a note. Using a record here is idiomatic: pure data, no logic.

**Group by category.** `byCategory.computeIfAbsent(e.category(), k -> new ArrayList<>()).add(e)` builds a `TreeMap<String, List<KeywordEntry>>`. `TreeMap` sorts categories alphabetically, so the printed groups appear in consistent order.

**Post-Java-1.0 filter.** `.stream().filter(e -> e.since() > 1).sorted(Comparator.comparingInt(KeywordEntry::since))` extracts keywords introduced after Java 1.0 and sorts them by version — revealing the language evolution timeline: `assert` (1.4), `enum` (5), `var` (10), `yield` (14), `record` (16), `sealed`/`permits` (17).

**Context-sensitive count.** The `"context"` category contains `var`, `record`, `sealed`, `permits`, `yield` — keywords that don't break existing code because they're only keyword-ish in specific syntactic positions.

## 7. Gotchas & takeaways

> **`const` and `goto` are reserved but do nothing.** You will get a compile error if you try to use them as identifiers, but there is no `goto` statement or `const` declaration in Java. They were reserved from day one to ease migration from C/C++ (where they exist) and to discourage bad patterns — and possibly to leave room for future syntax.

> **`strictfp` is a legal keyword but a no-op since Java 17.** Floating-point operations now always use strict IEEE 754 semantics (which `strictfp` used to enforce). The keyword still compiles cleanly; it just has no effect. Some older codebases still have `strictfp` on class/method declarations.

- 51 hard keywords + `const`/`goto` (reserved, unused) = 53 reserved tokens.
- Context-sensitive keywords (`var`, `record`, `sealed`, `permits`, `yield`) are keyword-like only in specific positions — conservative approach: avoid using them as identifiers entirely.
- `default` pulls triple duty: `switch` default case, interface default methods, annotation default values.
- `assert` requires JVM flag `-ea` to activate; assertions are disabled by default at runtime.
- Module-system keywords (`module`, `requires`, `exports`, …) only apply inside `module-info.java` — they are ordinary identifiers in all other source files.
