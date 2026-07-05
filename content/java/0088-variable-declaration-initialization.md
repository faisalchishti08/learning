---
card: java
gi: 88
slug: variable-declaration-initialization
title: Variable declaration & initialization
---

## 1. What it is

A variable declaration introduces a name with a type into the current scope, optionally binding it to an initial value (initialization). Declaration and initialization can be combined or separated. Java distinguishes the type (what kind of value the variable holds), the name (how you refer to it), and the value (the actual data stored).

```java
// Declaration only
int count;

// Declaration with initializer
int count = 0;

// Multiple declarations on one line (same type)
int x = 1, y = 2, z = 3;

// Type inference with var (Java 10+)
var message = "Hello";   // inferred type: String
var items   = new java.util.ArrayList<String>();  // inferred: ArrayList<String>
```

Java variables are either **primitive** (store the value directly) or **reference** (store a pointer to an object on the heap). The rules differ significantly between local variables, instance fields, static fields, and parameters.

## 2. Why & when

Understanding declaration and initialization matters because:
- **Definite assignment** — the compiler rejects reads of local variables that might not have been assigned. Fields get zero defaults; locals do not.
- **`var` inference** — choosing between `var` and an explicit type trades verbosity for self-documentation. Use `var` when the type is obvious from the right-hand side.
- **Scope** — where you declare a variable determines how long it lives and where it is visible.
- **Final vs mutable** — `final` on a variable prevents reassignment, which is useful for communicating intent and enabling lambda capture.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class VariableDeclaration {

    // ---- Fields: declared at class level ----
    int     instanceField;          // default: 0
    String  name;                   // default: null
    boolean active;                 // default: false
    static int classCounter = 0;    // static with explicit initializer

    public static void main(String[] args) {
        // ---- Local variable: explicit init required before use ----
        int x;
        // System.out.println(x);  // compile error: x not initialized
        x = 5;
        System.out.println(x);     // 5

        // ---- Declaration with initializer ----
        int age      = 30;
        double price = 9.99;
        String label = "sale";
        boolean flag = true;

        // ---- Multiple variables: avoid — one per line is clearer ----
        int a = 1, b = 2, c = 3;   // legal but harder to read
        int d = 1;
        int e = 2;   // preferred style: one per line

        // ---- var: type inference (Java 10+) ----
        var count  = 0;                       // int
        var greet  = "Hello";                 // String
        var names  = new ArrayList<String>(); // ArrayList<String>
        var pi     = 3.14159;                 // double

        names.add("Alice");
        names.add("Bob");

        // var makes the declared type the inferred type — it is not dynamic
        // count = "text";  // compile error: count is int

        // ---- final variables ----
        final int MAX = 100;
        // MAX = 200;  // compile error: cannot assign to final

        // ---- Reference vs primitive ----
        int  prim = 42;          // stores the value 42 directly
        List<String> ref = names; // stores a reference (pointer) to the same list
        ref.add("Carol");
        System.out.println(names.size());  // 3 — both ref and names point to same object

        // ---- Arrays ----
        int[]    scores = {90, 85, 92};   // array literal initializer
        String[] tags   = new String[3];  // elements default to null
        System.out.println(scores[0]);    // 90
        System.out.println(tags[0]);      // null
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Variable declaration anatomy: type, name, initializer; field vs local default rules; primitive stores value, reference stores pointer">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- Anatomy row -->
  <rect x="16" y="18" width="668" height="52" rx="4" fill="#1c2430"/>
  <text x="350" y="33" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Variable declaration anatomy</text>

  <!-- final (optional) -->
  <rect x="36" y="38" width="58" height="26" rx="3" fill="#8b949e" opacity="0.4"/>
  <text x="65" y="55" fill="#e6edf3" font-size="10" font-weight="bold" text-anchor="middle" font-family="monospace">final</text>

  <!-- type -->
  <rect x="100" y="38" width="60" height="26" rx="3" fill="#6db33f" opacity="0.8"/>
  <text x="130" y="55" fill="#0d1117" font-size="10" font-weight="bold" text-anchor="middle" font-family="monospace">int</text>

  <!-- name -->
  <rect x="165" y="38" width="80" height="26" rx="3" fill="#79c0ff" opacity="0.7"/>
  <text x="205" y="55" fill="#0d1117" font-size="10" font-weight="bold" text-anchor="middle" font-family="monospace">count</text>

  <!-- = -->
  <text x="260" y="56" fill="#8b949e" font-size="14" text-anchor="middle" font-family="monospace">=</text>

  <!-- initializer -->
  <rect x="278" y="38" width="46" height="26" rx="3" fill="#8b949e" opacity="0.45"/>
  <text x="301" y="55" fill="#e6edf3" font-size="10" font-weight="bold" text-anchor="middle" font-family="monospace">0</text>

  <!-- ; -->
  <text x="338" y="56" fill="#8b949e" font-size="14" font-family="monospace">;</text>

  <!-- labels -->
  <text x="65"  y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">optional</text>
  <text x="130" y="76" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">type</text>
  <text x="205" y="76" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">name</text>
  <text x="301" y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">initializer</text>

  <!-- var inference -->
  <text x="490" y="54" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">var count = 0;  // inferred: int</text>

  <!-- Field defaults box -->
  <rect x="16" y="90" width="320" height="72" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="176" y="106" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Fields (default values)</text>
  <line x1="26" y1="112" x2="326" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="26" y="126" fill="#e6edf3" font-size="7.5" font-family="monospace">int / long / etc: 0</text>
  <text x="26" y="139" fill="#e6edf3" font-size="7.5" font-family="monospace">float / double  : 0.0</text>
  <text x="26" y="152" fill="#e6edf3" font-size="7.5" font-family="monospace">boolean         : false</text>
  <text x="160" y="126" fill="#e6edf3" font-size="7.5" font-family="monospace">char   : '\0'</text>
  <text x="160" y="139" fill="#e6edf3" font-size="7.5" font-family="monospace">Object : null</text>
  <text x="160" y="152" fill="#8b949e" font-size="7.5" font-family="monospace">local vars: NONE</text>

  <!-- Prim vs ref box -->
  <rect x="348" y="90" width="336" height="72" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="516" y="106" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Primitive vs reference</text>
  <line x1="358" y1="112" x2="674" y2="112" stroke="#8b949e" stroke-width="0.5"/>
  <text x="358" y="126" fill="#e6edf3" font-size="7.5" font-family="monospace">int x = 5;         → stores 5</text>
  <text x="358" y="139" fill="#e6edf3" font-size="7.5" font-family="monospace">List l = list;     → stores pointer</text>
  <text x="358" y="152" fill="#8b949e" font-size="7.5" font-family="monospace">l.add() modifies the shared object</text>
</svg>

A declaration binds a name and type; the initializer is optional for fields (auto-zeroed) but required for local variables before first read; `var` infers the type from the right-hand side.

## 5. Runnable example

Scenario: a shopping cart — tracks items, quantities, and total price, with variable declarations illustrating field defaults, local initializers, `var`, and `final` constants, growing from basic usage to reference aliasing to a full cart summary.

### Level 1 — Basic

```java
import java.util.ArrayList;
import java.util.List;

public class VariableDeclBasic {

    // Instance fields with defaults
    String storeName;   // null
    int    itemCount;   // 0
    double totalPrice;  // 0.0

    public static void main(String[] args) {
        VariableDeclBasic cart = new VariableDeclBasic();
        System.out.println("=== Initial state (defaults) ===");
        System.out.println("storeName  : " + cart.storeName);   // null
        System.out.println("itemCount  : " + cart.itemCount);   // 0
        System.out.println("totalPrice : " + cart.totalPrice);  // 0.0

        // Local variables with explicit initializers
        final double TAX_RATE = 0.08;   // final constant
        var items = new ArrayList<String>();
        items.add("Apple");
        items.add("Bread");
        items.add("Milk");

        cart.storeName = "Fresh Mart";
        cart.itemCount = items.size();
        cart.totalPrice = 3.99 + 2.49 + 1.89;

        System.out.println();
        System.out.println("=== After adding items ===");
        System.out.println("storeName  : " + cart.storeName);
        System.out.println("itemCount  : " + cart.itemCount);
        System.out.printf("subtotal   : $%.2f%n", cart.totalPrice);
        System.out.printf("tax (%.0f%%): $%.2f%n", TAX_RATE * 100,
            cart.totalPrice * TAX_RATE);
        System.out.printf("total      : $%.2f%n",
            cart.totalPrice * (1 + TAX_RATE));
    }
}
```

**How to run:** `java VariableDeclBasic.java`

`storeName`, `itemCount`, and `totalPrice` are instance fields — they are automatically zero-initialised before the constructor body runs. `TAX_RATE` is a `final` local variable — once assigned it cannot be changed. `var items = new ArrayList<String>()` infers type `ArrayList<String>` from the right-hand side; the variable is still strongly typed — attempting `items = 5` would be a compile error.

### Level 2 — Intermediate

Same cart: demonstrate reference aliasing (two variables pointing to the same list), combined vs separate declaration/initialization, and multi-variable declaration.

```java
import java.util.*;

public class VariableDeclIntermediate {

    record CartItem(String name, int qty, double price) {
        double subtotal() { return qty * price; }
    }

    public static void main(String[] args) {
        // Declaration separate from initialization
        List<CartItem> cart;
        double discount;

        // Initialize after some logic
        boolean isVip = true;
        cart     = new ArrayList<>();
        discount = isVip ? 0.10 : 0.0;

        cart.add(new CartItem("Apple",  3, 0.99));
        cart.add(new CartItem("Bread",  1, 2.49));
        cart.add(new CartItem("Cheese", 2, 4.99));

        // Reference aliasing: both point to same list
        List<CartItem> receipt = cart;
        receipt.add(new CartItem("Milk", 2, 1.89));
        System.out.println("cart size   : " + cart.size());     // 4
        System.out.println("receipt size: " + receipt.size());  // 4 (same object)

        // Compute totals
        double subtotal = cart.stream()
            .mapToDouble(CartItem::subtotal)
            .sum();
        double savings  = subtotal * discount;
        double total    = subtotal - savings;

        System.out.println();
        System.out.printf("Subtotal  : $%6.2f%n", subtotal);
        System.out.printf("Discount  : $%6.2f (%.0f%%)%n", savings, discount * 100);
        System.out.printf("Total     : $%6.2f%n", total);

        // var with complex inferred types
        var itemsByName = new TreeMap<String, CartItem>();
        cart.forEach(item -> itemsByName.put(item.name(), item));
        System.out.println();
        itemsByName.forEach((name, item) ->
            System.out.printf("  %-8s qty=%-2d $%.2f%n",
                name, item.qty(), item.price()));
    }
}
```

**How to run:** `java VariableDeclIntermediate.java`

`List<CartItem> receipt = cart;` does not copy the list — it makes `receipt` a second reference to the same `ArrayList`. Adding through `receipt` modifies the object that `cart` also points to, so `cart.size()` reflects the addition. This reference aliasing is fundamental to how Java passes objects: assigning an object to a variable always copies the reference, not the object. `var itemsByName = new TreeMap<String, CartItem>()` is clearer than writing `TreeMap<String, CartItem>` twice.

### Level 3 — Advanced

Same cart: show `final` fields in a record, `var` with lambda inference, array declarations, and multiple initialisation patterns in one realistic example.

```java
import java.util.*;
import java.util.stream.*;

public class VariableDeclAdvanced {

    // Immutable line item — all fields effectively final via record
    record LineItem(String sku, String name, int qty, double unitPrice) {
        double total() { return qty * unitPrice; }
    }

    public static void main(String[] args) {
        // Array declaration and initializer
        String[] skus   = {"SKU001", "SKU002", "SKU003", "SKU004"};
        String[] names  = {"Apple", "Bread", "Cheese", "Milk"};
        int[]    qtys   = {3, 1, 2, 2};
        double[] prices = {0.99, 2.49, 4.99, 1.89};

        // Build cart from parallel arrays
        var cart = new ArrayList<LineItem>();
        for (int i = 0; i < skus.length; i++) {
            cart.add(new LineItem(skus[i], names[i], qtys[i], prices[i]));
        }

        // var with complex generic type
        var byCategory = cart.stream()
            .collect(Collectors.groupingBy(
                item -> item.unitPrice() < 2.0 ? "budget" : "premium",
                Collectors.toList()
            ));

        System.out.println("=== Cart by category ===");
        byCategory.forEach((cat, items) -> {
            double catTotal = items.stream().mapToDouble(LineItem::total).sum();
            System.out.printf("%-8s: %d items  $%.2f%n", cat, items.size(), catTotal);
            items.forEach(item ->
                System.out.printf("  %-8s %-8s x%d @ $%.2f = $%.2f%n",
                    item.sku(), item.name(), item.qty(), item.unitPrice(), item.total()));
        });

        // final local computed once
        final double GRAND_TOTAL = cart.stream().mapToDouble(LineItem::total).sum();
        System.out.printf("%nGrand total: $%.2f%n", GRAND_TOTAL);

        // Array of arrays (2D)
        int[][] grid = {{1, 2}, {3, 4}, {5, 6}};
        System.out.println("grid[1][0] = " + grid[1][0]);   // 3
    }
}
```

**How to run:** `java VariableDeclAdvanced.java`

`var byCategory` infers type `Map<String, List<LineItem>>` — writing this explicitly would be verbose. `final double GRAND_TOTAL` captures the computed sum as an effectively-final constant, communicating that it should not change after assignment. The `int[][]` grid is a 2D array literal: each `{...}` sub-array initialises one row. `record LineItem(...)` gives all fields implicit `final` semantics — records are immutable by design.

## 6. Walkthrough

Execution trace through `VariableDeclAdvanced.main`:

**Array declarations.** `String[] skus = {"SKU001", ...}` allocates a 4-element `String` array and initialises each slot. `int[] qtys = {3, 1, 2, 2}` allocates and initialises four `int` slots. All four arrays share the same length `skus.length = 4`.

**Cart construction.** The loop runs four times. Each iteration creates a `new LineItem(...)` record and adds it to `cart`. After the loop, `cart` holds four `LineItem` objects on the heap.

**`var byCategory`.** The stream groups `LineItem` by whether `unitPrice < 2.0`. `cart` has Apple (`0.99`) and Milk (`1.89`) in `"budget"`, and Bread (`2.49`) and Cheese (`4.99`) in `"premium"`. The inferred type `Map<String, List<LineItem>>` is determined by the compiler from the `collect` call's return type.

**`final double GRAND_TOTAL`.** `mapToDouble(LineItem::total).sum()` traverses the stream once, computing `(3×0.99) + (1×2.49) + (2×4.99) + (2×1.89) = 2.97 + 2.49 + 9.98 + 3.78 = 19.22`. Declaring it `final` communicates that this value is fixed for the rest of the method.

```
Variable kinds in this example:
  String[] skus      → local, reference to String[] on heap
  var cart           → local, inferred ArrayList<LineItem>
  var byCategory     → local, inferred Map<String,List<LineItem>>
  final GRAND_TOTAL  → local final, computed once, prevents reassignment
  LineItem fields    → record fields — implicitly final
```

## 7. Gotchas & takeaways

> **`var` cannot be used for fields, method parameters, or return types.** It is only valid for local variable declarations where the type can be inferred from the initializer. `var x;` without an initializer is also a compile error.

> **Declaring multiple variables of the same type on one line (`int x = 1, y = 2;`) is legal but error-prone.** Only the first gets a type annotation visible to the reader. Declare one variable per line for clarity and diffability.

- Fields (instance and static) are auto-initialised to zero/null; local variables have no default and must be initialised before use.
- `var` (Java 10+) infers the type from the initializer at compile time — it is not dynamic typing.
- `final` prevents reassignment; it does not make the object itself immutable (a `final List` can still be mutated).
- Assigning one reference variable to another copies the reference, not the object — both variables then point to the same heap object.
- Array elements are zero-initialised (primitives) or null-initialised (references) on creation.
- Declare one variable per line; avoid `int x = 1, y = 2, z = 3;`.
