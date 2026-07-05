---
card: java
gi: 52
slug: import-statements
title: import statements
---

## 1. What it is

An **`import` statement** tells the compiler which classes (or packages) you want to use by short name. Without an import, you must write the fully qualified class name everywhere:

```java
// Without import — verbose
java.util.List<String> names = new java.util.ArrayList<>();

// With import — concise
import java.util.List;
import java.util.ArrayList;
List<String> names = new ArrayList<>();
```

`import` statements come after the `package` statement and before the class declaration. They are a compile-time convenience only — they add no runtime overhead and don't copy code.

## 2. Why & when

You need an `import` whenever you use a class from a package other than:
- `java.lang` (automatically imported: `String`, `System`, `Integer`, `Math`, `Thread`, …)
- The current class's own package (same package = visible without import)

Use explicit single-type imports (`import java.util.List`) rather than wildcard imports in production code — they make it immediately clear which classes are used and prevent accidental collisions.

## 3. Core concept

```java
package com.example.orders;

// ────────────────────────────────────────────────────
// import statements (between package and class declaration)
// ────────────────────────────────────────────────────

// Single-type import (preferred)
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.time.LocalDate;
import java.math.BigDecimal;

// Static import (covered in the next tutorial)
import static java.util.Collections.unmodifiableList;

// These are NOT needed (always auto-imported from java.lang):
// import java.lang.String;
// import java.lang.System;
// import java.lang.Math;

// ────────────────────────────────────────────────────
// Class body
// ────────────────────────────────────────────────────
public class OrderService {

    public List<Order> findByDate(LocalDate date) {
        List<Order> results = new ArrayList<>();
        // ...
        return unmodifiableList(results);
    }
}

// Name collision: two classes named 'Date' in different packages
// One must use the fully qualified name:
import java.util.Date;                   // imported
// import java.sql.Date;                 // conflict — cannot import both
// Use fully qualified name for the second:
// java.sql.Date sqlDate = new java.sql.Date(0);
```

`import` is resolved entirely at compile time. The compiler replaces the short name `List` with `java.util.List` in the bytecode. At runtime, the ClassLoader doesn't know about import statements — it sees only FQCNs.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="import statements appear between package and class declaration; compiler replaces short names with FQCNs in bytecode">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Source structure -->
  <rect x="20" y="20" width="310" height="150" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="175" y="38" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService.java (source)</text>

  <text x="35"  y="56" fill="#6db33f" font-size="9" font-family="monospace">package com.example.orders;</text>
  <text x="35"  y="74" fill="#79c0ff" font-size="9" font-family="monospace">import java.util.List;</text>
  <text x="35"  y="87" fill="#79c0ff" font-size="9" font-family="monospace">import java.util.ArrayList;</text>
  <text x="35"  y="100" fill="#79c0ff" font-size="9" font-family="monospace">import java.time.LocalDate;</text>
  <text x="35"  y="118" fill="#6db33f" font-size="9" font-family="monospace">public class OrderService {</text>
  <text x="35"  y="131" fill="#e6edf3" font-size="9" font-family="monospace">  List&lt;Order&gt; find(LocalDate d)</text>
  <text x="35"  y="144" fill="#e6edf3" font-size="9" font-family="monospace">    new ArrayList&lt;&gt;();</text>
  <text x="35"  y="158" fill="#6db33f" font-size="9" font-family="monospace">}</text>

  <!-- javac -->
  <rect x="345" y="80" width="65" height="35" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="377" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">javac</text>
  <line x1="330" y1="97" x2="341" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#im1)"/>
  <line x1="410" y1="97" x2="421" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#im1)"/>

  <!-- Bytecode (FQCNs) -->
  <rect x="424" y="20" width="258" height="150" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="553" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService.class (bytecode)</text>
  <text x="440" y="55" fill="#8b949e" font-size="8" font-family="sans-serif">No import statements in bytecode.</text>
  <text x="440" y="68" fill="#8b949e" font-size="8" font-family="sans-serif">Short names resolved to FQCNs:</text>
  <text x="440" y="86" fill="#e6edf3" font-size="9" font-family="monospace">java.util.List</text>
  <text x="440" y="100" fill="#e6edf3" font-size="9" font-family="monospace">java.util.ArrayList</text>
  <text x="440" y="114" fill="#e6edf3" font-size="9" font-family="monospace">java.time.LocalDate</text>
  <text x="440" y="134" fill="#8b949e" font-size="8" font-family="sans-serif">import = compile-time only</text>
  <text x="440" y="147" fill="#8b949e" font-size="8" font-family="sans-serif">zero runtime overhead</text>

  <defs>
    <marker id="im1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

`import` statements disappear in bytecode. The compiler replaces every short class name with its FQCN in the `.class` output. There is no runtime cost to importing many classes.

## 5. Runnable example

Scenario: an invoice calculation service that imports various `java.util`, `java.time`, and `java.math` classes — showing how imports work, what happens with name conflicts, and alternatives.

### Level 1 — Basic

```java
// ImportsBasic.java — demonstrates standard import usage
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.math.BigDecimal;
import java.math.RoundingMode;

public class ImportsBasic {

    record LineItem(String product, int qty, BigDecimal unitPrice) {
        BigDecimal total() { return unitPrice.multiply(BigDecimal.valueOf(qty)); }
    }

    public static void main(String[] args) {
        System.out.println("=== Import statements demo ===\n");

        // java.time
        LocalDate invoiceDate = LocalDate.of(2025, 7, 15);
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd MMM yyyy");
        System.out.println("Invoice date: " + invoiceDate.format(fmt));

        // java.math — BigDecimal for money (never use double for currency)
        List<LineItem> items = new ArrayList<>();
        items.add(new LineItem("Widget A", 3, new BigDecimal("12.50")));
        items.add(new LineItem("Widget B", 1, new BigDecimal("99.99")));
        items.add(new LineItem("Service", 5, new BigDecimal("25.00")));

        BigDecimal subtotal = items.stream()
            .map(LineItem::total)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        BigDecimal tax = subtotal.multiply(new BigDecimal("0.20"))
                                 .setScale(2, RoundingMode.HALF_UP);
        BigDecimal total = subtotal.add(tax);

        // java.util.Map
        Map<String, BigDecimal> summary = new HashMap<>();
        summary.put("subtotal", subtotal);
        summary.put("tax (20%)", tax);
        summary.put("total", total);

        System.out.println("\nInvoice:");
        items.forEach(item -> System.out.printf("  %-15s x%d @ £%s = £%s%n",
            item.product(), item.qty(), item.unitPrice(), item.total()));
        System.out.println();
        summary.forEach((k, v) -> System.out.printf("  %-15s £%s%n", k, v));

        System.out.println("\n[ java.lang is auto-imported — no import needed for: ]");
        System.out.println("  String, Integer, Long, Double, Math, System, Thread, ...");
        System.out.println("  Also: all classes in the same package as this class.");
    }
}
```

**How to run:** `java ImportsBasic.java`

`java.lang` classes (`String`, `System`, `Math`) need no import. `java.util.List`, `java.time.LocalDate`, and `java.math.BigDecimal` all need explicit imports. Notice `BigDecimal` for currency — floating-point `double` has rounding errors (e.g., `0.1 + 0.2 ≠ 0.3`).

### Level 2 — Intermediate

Same invoice system extended to demonstrate **name collision** (`java.util.Date` vs `java.sql.Date`) and the two resolution strategies: use one import and FQCN for the other, or use FQCNs for both.

```java
// ImportsCollision.java — demonstrate name collision and resolution
import java.util.Date;           // java.util.Date
// cannot also import java.sql.Date — same simple name!
import java.util.List;
import java.util.ArrayList;

public class ImportsCollision {

    public static void main(String[] args) {
        System.out.println("=== Name collision demo ===\n");

        // --- Strategy 1: import one, use FQCN for the other ---
        System.out.println("Strategy 1: import java.util.Date, use FQCN for java.sql.Date\n");

        Date utilDate = new Date();                     // java.util.Date (imported)
        java.sql.Date sqlDate = new java.sql.Date(utilDate.getTime());  // FQCN

        System.out.println("java.util.Date:  " + utilDate);
        System.out.println("java.sql.Date:   " + sqlDate);

        // --- Strategy 2: use FQCNs for both (no import for either) ---
        System.out.println("\nStrategy 2: no imports for either, use both as FQCNs\n");
        java.util.Date u = new java.util.Date();
        java.sql.Date  s = new java.sql.Date(u.getTime());
        System.out.println("java.util.Date:  " + u);
        System.out.println("java.sql.Date:   " + s);

        // --- The modern way: avoid java.util.Date entirely ---
        System.out.println("\nModern alternative: java.time.* (no collision risk)\n");
        java.time.LocalDateTime ldt = java.time.LocalDateTime.now();
        java.time.LocalDate     ld  = ldt.toLocalDate();
        System.out.println("LocalDateTime: " + ldt);
        System.out.println("LocalDate:     " + ld);
        System.out.println("(java.time classes have no ambiguous counterparts in java.sql)");

        // --- Show what class was imported ---
        System.out.println("\n[ Class identity check ]");
        System.out.println("utilDate.getClass().getName(): " + utilDate.getClass().getName());
        System.out.println("sqlDate.getClass().getName():  " + sqlDate.getClass().getName());
    }
}
```

**How to run:** `java ImportsCollision.java`

`java.util.Date` and `java.sql.Date` have the same simple name. The compiler rejects importing both. Resolution: import whichever is used more often and write the FQCN for the rarer one. The modern solution is to avoid `java.util.Date` entirely and use `java.time.LocalDate` / `java.time.Instant` — these never collide.

### Level 3 — Advanced

Same invoice system grown to show a practical import pattern in a large class: single-type imports grouped by origin, what `import *` expands to, and how the compiler resolves ambiguity when both a wildcard and a same-package class match.

```java
// ImportsAdvanced.java — import resolution rules and edge cases
import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Optional;
import java.util.stream.Collectors;   // in java.util.stream sub-package — separate import needed
import java.time.LocalDate;
import java.time.Period;
import java.math.BigDecimal;
import java.math.RoundingMode;

public class ImportsAdvanced {

    record Invoice(String id, LocalDate date, BigDecimal total, String status) {}

    public static void main(String[] args) {
        System.out.println("=== Advanced import patterns ===\n");

        List<Invoice> invoices = new ArrayList<>();
        invoices.add(new Invoice("INV-001", LocalDate.of(2025,1,15), new BigDecimal("1250.00"), "PAID"));
        invoices.add(new Invoice("INV-002", LocalDate.of(2025,3,22), new BigDecimal("375.50"),  "UNPAID"));
        invoices.add(new Invoice("INV-003", LocalDate.of(2025,6,30), new BigDecimal("892.00"),  "PAID"));
        invoices.add(new Invoice("INV-004", LocalDate.of(2025,7,1),  new BigDecimal("100.00"),  "UNPAID"));

        // java.util.stream.Collectors — note: NOT covered by import java.util.*
        // (wildcards don't cover sub-packages)
        BigDecimal paidTotal = invoices.stream()
            .filter(inv -> "PAID".equals(inv.status()))
            .map(Invoice::total)
            .reduce(BigDecimal.ZERO, BigDecimal::add);

        List<Invoice> unpaid = invoices.stream()
            .filter(inv -> "UNPAID".equals(inv.status()))
            .collect(Collectors.toList());

        System.out.println("Paid total: £" + paidTotal);
        System.out.println("Unpaid invoices: " + unpaid.size());
        unpaid.forEach(inv -> System.out.printf("  %s due %s: £%s%n",
            inv.id(), inv.date(), inv.total()));

        // Optional
        Optional<Invoice> oldest = invoices.stream()
            .min(java.util.Comparator.comparing(Invoice::date));
        oldest.ifPresent(inv -> System.out.println("\nOldest: " + inv.id() + " (" + inv.date() + ")"));

        // Period — date arithmetic
        LocalDate today = LocalDate.now();
        Period overduePeriod = Period.between(LocalDate.of(2025, 3, 22), today);
        System.out.println("INV-002 overdue by: " + overduePeriod.getMonths() + " months");

        System.out.println("\n[ Import resolution priority ]");
        System.out.println("  1. Explicit single-type import (highest priority)");
        System.out.println("  2. Same-package classes (no import needed)");
        System.out.println("  3. java.lang.* (auto-imported)");
        System.out.println("  4. Wildcard imports (lowest priority)");
        System.out.println("  If two wildcard imports produce the same name → compile error");
        System.out.println("  If single-type import conflicts with wildcard → single-type wins");
        System.out.println();
        System.out.println("[ Wildcard imports do NOT cover sub-packages ]");
        System.out.println("  import java.util.*  covers java.util.List, java.util.Map");
        System.out.println("  but NOT java.util.stream.Collectors (different package)");
        System.out.println("  need: import java.util.stream.Collectors;  separately");
        System.out.println();
        System.out.println("[ IDE and convention ]");
        System.out.println("  IntelliJ/Eclipse auto-collapse to wildcard at 5+ classes from same package");
        System.out.println("  Google style guide: wildcards allowed");
        System.out.println("  Oracle/Sun style:   single-type imports preferred");
    }
}
```

**How to run:** `java ImportsAdvanced.java`

A wildcard `import java.util.*` does not cover `java.util.stream.Collectors` — sub-packages are entirely separate namespaces. You must import `java.util.stream.Collectors` (or `java.util.stream.*`) explicitly.

## 6. Walkthrough

Execution trace in `ImportsAdvanced.main`:

**Import resolution at compile time.** When `javac` sees `List<Invoice>`, it consults the import list:
1. Is there an explicit `import java.util.List`? Yes → resolve to `java.util.List`.
2. Result: `java.util.List<ImportsAdvanced.Invoice>` in bytecode.

**`Collectors.toList()`.** `import java.util.stream.Collectors` is needed because `import java.util.*` only covers the `java.util` package. `java.util.stream` is a separate package (a sibling, not a child) — wildcards do not descend into sub-packages.

**`BigDecimal.add`.** `BigDecimal.ZERO` is a `static final BigDecimal` field on `java.math.BigDecimal`. `import java.math.BigDecimal` makes `BigDecimal.ZERO` syntactically valid. Without the import, you'd write `java.math.BigDecimal.ZERO`.

**Stream pipeline.** `.filter(inv -> "PAID".equals(inv.status()))` returns a `Stream<Invoice>`. `.map(Invoice::total)` returns a `Stream<BigDecimal>`. `.reduce(BigDecimal.ZERO, BigDecimal::add)` folds the stream into a single sum — no `BigDecimal` multiplication or subtraction needed here.

**Priority rules in action.** If `ImportsAdvanced` were in `com.example.orders` and that package also had a class named `List`, the compiler would choose the same-package `List` over `java.util.List` from the wildcard (if a wildcard were used). The explicit single-type import `import java.util.List` wins over same-package to avoid this ambiguity — which is why explicit imports are recommended in production code.

## 7. Gotchas & takeaways

> **`import` does not make code from another JAR available.** The JAR must be on the classpath (`-cp`) at both compile and runtime. `import` is a name resolver, not a dependency manager. A missing JAR produces `NoClassDefFoundError` at runtime even with a valid `import`.

> **`java.util.stream.*` and `java.util.function.*` are separate packages.** Beginners often assume `import java.util.*` covers everything in the Java ecosystem — it only covers the `java.util` package itself. `Collectors`, `Stream`, `Function`, `Predicate` all need their own imports.

- `java.lang` is auto-imported — `String`, `Integer`, `Math`, `System`, `Thread`, `Object`, etc.
- Same-package classes need no import.
- Explicit single-type imports (`import java.util.List`) are preferred over wildcards in production.
- Name collision (two classes with the same simple name): import one, use FQCN for the other.
- `import` is compile-time only — no performance difference between importing one class or a thousand.
- Sub-packages are NOT covered by wildcard imports: `import java.util.*` ≠ `import java.util.stream.*`.
