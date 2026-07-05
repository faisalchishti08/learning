---
card: java
gi: 92
slug: variable-scope-lifetime
title: Variable scope & lifetime
---

## 1. What it is

**Scope** is the region of source code in which a variable name is visible and can be referenced. **Lifetime** is the duration during execution for which the variable's storage exists. In Java, scope is determined at compile time by `{ }` blocks; lifetime is a runtime property.

| Variable kind   | Scope                                    | Lifetime                          |
|-----------------|------------------------------------------|-----------------------------------|
| Local           | From declaration to end of enclosing `{}`| From declaration until block exits |
| Loop variable   | Inside the `for`/`while`/`for-each` body | One iteration                     |
| Instance field  | Anywhere the instance is reachable       | As long as the object lives       |
| Static field    | Anywhere the class is reachable          | From class load to JVM exit       |
| Parameter       | Entire method body                       | Duration of the method call       |

## 2. Why & when

Understanding scope and lifetime helps you:
- **Avoid accidental variable reuse** — declaring a variable in the tightest necessary scope prevents it from being misused in unrelated code below.
- **Prevent shadowing surprises** — a local with the same name as a field silently hides the field within its scope.
- **Reason about memory** — once a variable's scope ends, the JVM can reclaim the storage (for locals) or the object becomes eligible for garbage collection (for fields).
- **Capture in lambdas** — only effectively-final variables in scope can be captured by a lambda.

## 3. Core concept

```java
public class ScopeLifetime {
    int x = 10;   // instance field — in scope for all instance methods

    void demo() {
        int x = 20;   // local — shadows the field within this method
        System.out.println(x);       // 20 (local)
        System.out.println(this.x);  // 10 (field, via 'this')

        {
            int y = 30;   // inner block scope
            System.out.println(y);   // 30
            System.out.println(x);   // 20 (outer local still in scope)
        }
        // y is out of scope here
        // System.out.println(y);   // compile error

        // Loop variable scope
        for (int i = 0; i < 3; i++) {
            int doubled = i * 2;     // new variable each iteration
            System.out.println(doubled);
        }
        // i and doubled are out of scope

        // You can reuse the same name in a new, sibling (non-nested) block
        for (int i = 0; i < 2; i++) {   // new 'i' — not a redeclaration of the same scope
            System.out.println("second loop: " + i);
        }
    }

    // Cannot redeclare a variable in an inner scope if it was declared in an outer scope:
    void redeclareIllegal() {
        int z = 1;
        {
            // int z = 2;   // compile error: z already defined in enclosing scope
        }
    }

    // Can use the same name in a completely separate method — no conflict
    void otherMethod() {
        int x = 99;   // different method, different scope — no conflict with field x
        System.out.println(x);
    }

    public static void main(String[] args) {
        new ScopeLifetime().demo();
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scope layers: static field (class lifetime), instance field (object lifetime), method scope, inner block scope, loop variable scope — each nested layer is smaller">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>

  <!-- Static scope (largest) -->
  <rect x="16" y="18" width="668" height="163" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="26" y="33" fill="#6db33f" font-size="7.5" font-family="sans-serif">static field — lives from class load to JVM exit</text>

  <!-- Instance scope -->
  <rect x="26" y="38" width="648" height="137" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="36" y="53" fill="#79c0ff" font-size="7.5" font-family="sans-serif">instance field — lives while object is reachable</text>

  <!-- Method scope -->
  <rect x="36" y="58" width="628" height="111" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="46" y="72" fill="#8b949e" font-size="7.5" font-family="sans-serif">method scope — local variables (call to return)</text>
  <text x="46" y="85" fill="#e6edf3" font-size="8" font-family="monospace">int a = 1;   // visible rest of method</text>

  <!-- Inner block -->
  <rect x="46" y="90" width="390" height="54" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1" stroke-dasharray="3"/>
  <text x="56" y="104" fill="#6db33f" font-size="7" font-family="monospace">{ int b = 2;  // b visible only in this block</text>
  <text x="56" y="116" fill="#e6edf3" font-size="7" font-family="monospace">  a visible (outer scope still in scope)</text>
  <text x="56" y="130" fill="#6db33f" font-size="7" font-family="monospace">}  ← b's lifetime ends</text>

  <!-- for loop -->
  <rect x="450" y="90" width="204" height="54" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1" stroke-dasharray="3"/>
  <text x="460" y="104" fill="#8b949e" font-size="7" font-family="monospace">for (int i=0; ..) {</text>
  <text x="460" y="116" fill="#e6edf3" font-size="7" font-family="monospace">  int step = i*2;</text>
  <text x="460" y="130" fill="#8b949e" font-size="7" font-family="monospace">}  ← i, step dead</text>

  <text x="46" y="158" fill="#8b949e" font-size="7.5" font-family="monospace">// b, i, step not accessible here — only a is</text>
</svg>

Scope layers nest; each inner layer can see all outer variables, but outer layers cannot see inner variables; a variable's lifetime matches its scope layer.

## 5. Runnable example

Scenario: a multi-level product discount calculator — variables are declared at the correct scope level for their purpose, demonstrating how scope prevents cross-contamination between iterations and blocks. The scenario grows from a simple loop, to nested scopes with accumulators, to a method that demonstrates all four variable kinds.

### Level 1 — Basic

```java
public class ScopeBasic {

    static final double DEFAULT_TAX = 0.08;   // static scope — class lifetime

    double baseDiscount = 0.05;               // instance scope — object lifetime

    void calculate(String[] products, double[] prices) {
        // method scope — lives for this call
        double total = 0.0;

        for (int i = 0; i < products.length; i++) {
            // loop-body scope — new each iteration
            double discounted = prices[i] * (1 - baseDiscount);  // sees instance field
            double withTax    = discounted * (1 + DEFAULT_TAX);   // sees static field
            total += withTax;

            System.out.printf("  %-10s $%.2f → $%.2f (after discount+tax)%n",
                products[i], prices[i], withTax);
        }
        // discounted and withTax are out of scope here
        System.out.printf("Total: $%.2f%n", total);
    }

    public static void main(String[] args) {
        ScopeBasic calc = new ScopeBasic();
        calc.calculate(
            new String[]{"Apple", "Bread", "Milk"},
            new double[]{1.20, 2.50, 1.80}
        );
    }
}
```

**How to run:** `java ScopeBasic.java`

`DEFAULT_TAX` is `static` — it lives for the entire program and is visible everywhere the class is in scope. `baseDiscount` is an instance field — it lives as long as the `ScopeBasic` object. `total` is a method-local variable — it lives for one call to `calculate`. `discounted` and `withTax` are loop-body locals — they are created and destroyed on each iteration. Accessing `baseDiscount` from within the loop body works because instance fields are always in scope for instance methods.

### Level 2 — Intermediate

Same calculator: add a nested block that computes bulk discount for large orders, demonstrating that the bulk-discount variable is only visible inside that block, and that the outer `total` is visible everywhere in the method.

```java
public class ScopeIntermediate {

    static final double TAX    = 0.08;
    static final int    BULK_THRESHOLD = 5;

    double baseDiscount = 0.05;

    double process(String category, int qty, double unitPrice) {
        // method scope
        double lineTotal;
        String priceLabel;

        if (qty >= BULK_THRESHOLD) {
            // inner block scope — bulkDiscount only lives here
            double bulkDiscount = 0.10;   // extra 10% for bulk
            double discounted   = unitPrice * (1 - baseDiscount - bulkDiscount);
            lineTotal  = discounted * qty;
            priceLabel = String.format("$%.2f × %d (bulk -%.0f%%)",
                discounted, qty, bulkDiscount * 100);
        } else {
            double discounted = unitPrice * (1 - baseDiscount);
            lineTotal  = discounted * qty;
            priceLabel = String.format("$%.2f × %d", discounted, qty);
        }
        // bulkDiscount is out of scope here — no risk of using wrong discount

        double withTax = lineTotal * (1 + TAX);
        System.out.printf("  %-12s %-30s = $%.2f (+ tax = $%.2f)%n",
            category, priceLabel, lineTotal, withTax);
        return withTax;
    }

    public static void main(String[] args) {
        ScopeIntermediate calc = new ScopeIntermediate();
        double total = 0.0;
        total += calc.process("Apples",  8, 0.99);  // bulk
        total += calc.process("Bread",   2, 2.49);  // normal
        total += calc.process("Cheese", 10, 4.99);  // bulk
        System.out.printf("Grand total: $%.2f%n", total);
    }
}
```

**How to run:** `java ScopeIntermediate.java`

`bulkDiscount` is declared inside the `if (qty >= BULK_THRESHOLD)` block — it is only accessible within that block. If the code were to accidentally use `bulkDiscount` after the `if/else`, the compiler would report it as out of scope. The `else` branch declares its own `double discounted`, which is also scoped to that block. Both branches assign `lineTotal` and `priceLabel`, satisfying the definite-assignment requirement, so they are accessible after the block.

### Level 3 — Advanced

Same system: demonstrate all four variable kinds (static, instance, local, loop) simultaneously in one method, show scope shadowing, and use a lambda that captures effectively-final variables.

```java
import java.util.*;
import java.util.stream.*;

public class ScopeAdvanced {

    // Static field — class lifetime
    static final Map<String, Double> PRICE_LIST = new HashMap<>();
    static { PRICE_LIST.put("apple",0.99); PRICE_LIST.put("bread",2.49);
             PRICE_LIST.put("milk",1.89);  PRICE_LIST.put("cheese",4.99); }

    // Instance field — object lifetime
    double taxRate;
    String storeName;

    ScopeAdvanced(String storeName, double taxRate) {
        this.storeName = storeName;
        this.taxRate   = taxRate;
    }

    List<String> generateReceipt(List<String> order) {
        // Local — method lifetime
        List<String> lines = new ArrayList<>();
        double subtotal = 0.0;

        for (String item : order) {
            // Loop-body locals — one iteration lifetime
            Double price = PRICE_LIST.get(item.toLowerCase());
            if (price == null) {
                lines.add("  UNKNOWN: " + item);
                continue;
            }
            double lineTotal = price;
            subtotal += lineTotal;
            lines.add(String.format("  %-10s $%.2f", item, lineTotal));
        }
        // price and lineTotal are out of scope here

        // Effectively-final capture by lambda
        double finalSubtotal = subtotal;   // new effectively-final local
        double tax = finalSubtotal * taxRate; // captures taxRate (instance field) too

        lines.add("-".repeat(22));
        lines.add(String.format("  Subtotal  $%.2f", finalSubtotal));
        lines.add(String.format("  Tax(%.0f%%) $%.2f", taxRate * 100, tax));
        lines.add(String.format("  Total     $%.2f", finalSubtotal + tax));
        lines.add("Store: " + storeName);   // instance field access
        return lines;
    }

    public static void main(String[] args) {
        ScopeAdvanced store = new ScopeAdvanced("FreshMart", 0.08);
        List<String> receipt = store.generateReceipt(
            List.of("apple", "milk", "bread", "butter", "cheese"));
        receipt.forEach(System.out::println);
    }
}
```

**How to run:** `java ScopeAdvanced.java`

`PRICE_LIST` (static) is visible everywhere the class is in scope — inside the instance method and in the `static {}` initializer. `taxRate` and `storeName` (instance) are visible in all instance methods via `this`. `subtotal` (local) accumulates across loop iterations. `price` and `lineTotal` (loop-body) are created fresh each iteration. `finalSubtotal` is an effectively-final copy of `subtotal` after the loop — necessary because `subtotal` itself might be considered non-final if the compiler cannot prove it was not changed after the loop (in this case the lambda captures `finalSubtotal`, not `subtotal`).

## 6. Walkthrough

Execution trace for `generateReceipt(["apple","milk","bread","butter","cheese"])`:

**Iteration "apple".** `price = PRICE_LIST.get("apple") = 0.99`. `lineTotal = 0.99`. `subtotal = 0.99`. Line added. `price` and `lineTotal` cease to exist as the loop body ends.

**Iteration "butter".** `price = PRICE_LIST.get("butter") = null`. The `if (price == null)` branch appends `"  UNKNOWN: butter"` and `continue` skips to the next iteration. `lineTotal` is never created this iteration.

**After loop.** `subtotal = 0.99 + 1.89 + 2.49 + 4.99 = 10.36`. `price` and `lineTotal` are completely out of scope. `finalSubtotal = 10.36` is a new effectively-final local. `tax = 10.36 * 0.08 = 0.83`.

**Scope resolution.** `taxRate` in `tax = finalSubtotal * taxRate` resolves to the instance field (no local variable of that name is in scope). `storeName` in the last line resolves to the instance field. `PRICE_LIST.get(...)` resolves to the static field directly without a class prefix because we are inside the class.

```
Scope visibility at the lambda capture point:
  PRICE_LIST    → static field (class scope)
  taxRate       → instance field (object scope)
  storeName     → instance field (object scope)
  lines         → method local
  subtotal      → method local (but changes → not captured)
  finalSubtotal → method local, effectively final → capturable
  price         → loop-body local (out of scope here)
  lineTotal     → loop-body local (out of scope here)
```

## 7. Gotchas & takeaways

> **You cannot declare a local variable in an inner block if the same name is already declared in an outer block of the same method.** `int x = 1; { int x = 2; }` is a compile error — the inner `x` would shadow the outer `x` within the same method, which Java forbids. (This differs from field shadowing, which is legal.)

> **A variable's lifetime may be shorter than its lexical scope.** A local variable that is last used early in a method may be garbage-collected before the method returns, even though it is technically in scope until the block closes. The JVM's liveness analysis allows this optimisation.

- Scope is compile-time; lifetime is runtime — but in practice they coincide for simple local variables.
- Declare variables at the smallest scope that satisfies their use to reduce accidental reuse and improve readability.
- Loop variables (`for (int i ...)`) are scoped to the loop body and are not accessible after it.
- An inner block can see outer-scope variables; the outer scope cannot see inner-block variables.
- A local variable cannot shadow another local in an enclosing block of the same method — but it can shadow an instance field (accessed via `this.name`).
- Static fields have the broadest lifetime (class load to JVM exit); loop-body locals have the narrowest (one iteration).
