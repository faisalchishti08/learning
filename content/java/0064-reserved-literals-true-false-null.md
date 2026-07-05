---
card: java
gi: 64
slug: reserved-literals-true-false-null
title: Reserved literals: true, false, null
---

## 1. What it is

Java defines three **reserved literals** — tokens that look like identifiers but have fixed, built-in meaning and cannot be used as names:

| Literal | Type | Meaning |
|---|---|---|
| `true` | `boolean` | logical truth |
| `false` | `boolean` | logical falsehood |
| `null` | null type | absence of any object reference |

```java
boolean active = true;
boolean closed = false;
String name    = null;   // reference holds no object

// Cannot use as identifiers — compile error:
// int true  = 1;         ✗
// String null = "x";     ✗
// boolean false = true;  ✗
```

Unlike keywords (like `if`, `class`), these three are technically called "boolean literals" and the "null literal" in the Java Language Specification — but practically they are reserved: you cannot use them as names.

## 2. Why & when

`true` and `false` give the `boolean` primitive its two and only two values — there is no other way to express a boolean literal in Java (no `1`/`0`, no `yes`/`no`). `null` represents the default state of every reference-type variable before initialisation and is the value you compare with `== null` or pass where no object is appropriate. Understanding these three matters when:
- You receive a `NullPointerException` and need to trace which reference was `null`.
- You return or check `boolean` from conditions without redundant `== true` / `== false`.
- You distinguish `null` (no object) from an empty collection or empty string (real object with no content).

## 3. Core concept

```java
// ---- boolean literals ----
boolean flag = true;
System.out.println(flag);           // true
System.out.println(Boolean.TRUE);   // true  (boxed Boolean, not the primitive literal)
System.out.println(true == Boolean.TRUE);  // true (auto-unboxing)

// Boolean expressions produce boolean — never compare with == true or == false:
if (flag == true) { }    // redundant; just write: if (flag) { }
if (flag == false) { }   // redundant; just write: if (!flag) { }

// ---- null literal ----
String s = null;          // reference type; initialised to null
// int x = null;          // ✗ compile error — primitives cannot be null

// Null checks:
if (s == null) { }        // correct
if (s != null) { }
if (null == s) { }        // Yoda-style — avoids accidental assignment (legacy practice)

// null is type-compatible with any reference type:
Object  o = null;
String  t = null;
int[]   a = null;         // array type — reference

// instanceof with null always returns false:
System.out.println(null instanceof String);   // false (never NPE)

// ---- null in expressions ----
// NPE triggers when you dereference null:
// s.length();   // throws NullPointerException if s is null

// Safe access pattern:
int len = (s != null) ? s.length() : 0;

// Optional as an alternative to null:
java.util.Optional<String> opt = java.util.Optional.ofNullable(s);
System.out.println(opt.isPresent());   // false

// ---- printed representation of null ----
System.out.println(null);          // prints:  null
System.out.println("" + null);     // prints:  null   (String concatenation converts)
System.out.println(String.valueOf(null));  // "null"
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three reserved literals: true and false are the two boolean values; null is the absent-reference value for all reference types">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <!-- true -->
  <rect x="20" y="22" width="190" height="128" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="40" fill="#6db33f" font-size="13" text-anchor="middle" font-family="monospace">true</text>
  <text x="115" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">boolean literal</text>
  <text x="115" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">boolean x = true;</text>
  <text x="115" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Boolean.TRUE  (boxed)</text>
  <line x1="30" y1="96" x2="200" y2="96" stroke="#8b949e" stroke-width="0.5"/>
  <text x="115" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Cannot be used as identifier</text>
  <text x="115" y="124" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Only two boolean values exist</text>
  <text x="115" y="138" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Stored as 1-bit in JVM</text>

  <!-- false -->
  <rect x="222" y="22" width="190" height="128" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="317" y="40" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="monospace">false</text>
  <text x="317" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">boolean literal</text>
  <text x="317" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">boolean x = false;</text>
  <text x="317" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Boolean.FALSE (boxed)</text>
  <line x1="232" y1="96" x2="402" y2="96" stroke="#8b949e" stroke-width="0.5"/>
  <text x="317" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Default value for boolean fields</text>
  <text x="317" y="124" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Avoid: if (x == false)</text>
  <text x="317" y="138" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Prefer: if (!x)</text>

  <!-- null -->
  <rect x="424" y="22" width="260" height="128" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="554" y="40" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="monospace">null</text>
  <text x="554" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">null literal — reference type only</text>
  <text x="434" y="72" fill="#e6edf3" font-size="8" font-family="monospace">String s = null; // no object</text>
  <text x="434" y="86" fill="#e6edf3" font-size="8" font-family="monospace">Object o = null; // any ref type</text>
  <line x1="434" y1="96" x2="674" y2="96" stroke="#8b949e" stroke-width="0.5"/>
  <text x="554" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">s.length() → NullPointerException</text>
  <text x="554" y="124" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">null instanceof X → false</text>
  <text x="554" y="138" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Default for unset reference fields</text>
</svg>

`true` and `false` are the only two `boolean` values. `null` signals "no object" for any reference type — primitive fields cannot hold `null`.

## 5. Runnable example

Scenario: an order state machine that uses `boolean` flags and `null` to track payment and shipping, demonstrating safe null handling and boolean semantics at each stage.

### Level 1 — Basic

```java
public class ReservedLiteralsBasic {

    static String customerId;   // null by default (field not initialised)
    static boolean isPaid = false;
    static boolean isShipped = false;

    public static void main(String[] args) {
        System.out.println("=== Reserved literals: true, false, null ===\n");

        // null default for reference fields
        System.out.println("customerId (unset): " + customerId);     // null
        System.out.println("isPaid (default):   " + isPaid);         // false
        System.out.println("isShipped (default):" + isShipped);      // false

        // Assign a real customer
        customerId = "CUST-001";
        isPaid = true;

        System.out.println("\nAfter payment:");
        System.out.println("  customerId: " + customerId);
        System.out.println("  isPaid:     " + isPaid);

        // Boolean checks — avoid == true / == false
        if (isPaid && !isShipped) {
            System.out.println("  → Ready to ship");
            isShipped = true;
        }

        System.out.println("\nAfter shipping:");
        System.out.println("  isShipped:  " + isShipped);

        // null check
        String promoCode = null;
        if (promoCode == null) {
            System.out.println("\nPromo code: none (null)");
        } else {
            System.out.println("Promo code: " + promoCode);
        }

        // null vs empty string — different things
        String emptyCode = "";
        System.out.println("null == null:          " + (promoCode == null));
        System.out.println("\"\" == null:           " + (emptyCode == null));
        System.out.println("null instanceof String: " + (null instanceof String));
    }
}
```

**How to run:** `java ReservedLiteralsBasic.java`

`customerId` is a `static String` field — its initial value is `null` (Java initialises reference fields to `null`, numeric fields to `0`, `boolean` fields to `false`). An empty string `""` is a real object — it is NOT `null`.

### Level 2 — Intermediate

Same order system: use `Optional<String>` to avoid propagating `null`, show `NullPointerException` source tracing (JDK 14+ helpful NPEs), and use pattern matching with `null` in switch.

```java
import java.util.*;

public class ReservedLiteralsIntermediate {

    record Order(String id, String promoCode, double amount) {}

    static Optional<String> findPromo(String code) {
        if (code == null || code.isBlank()) return Optional.empty();
        return Optional.of(code.toUpperCase());
    }

    static double applyDiscount(Order order) {
        return findPromo(order.promoCode())
            .map(promo -> switch (promo) {
                case "SAVE10" -> order.amount() * 0.90;
                case "SAVE20" -> order.amount() * 0.80;
                default       -> order.amount();
            })
            .orElse(order.amount());
    }

    public static void main(String[] args) {
        System.out.println("=== Intermediate: null, Optional, helpful NPE ===\n");

        var orders = List.of(
            new Order("ORD-001", "SAVE10",  200.00),
            new Order("ORD-002", null,      150.00),
            new Order("ORD-003", "",         80.00),
            new Order("ORD-004", "SAVE20",  500.00)
        );

        for (Order o : orders) {
            double finalPrice = applyDiscount(o);
            String promoDisplay = o.promoCode() == null ? "<none>"
                                : o.promoCode().isEmpty() ? "<blank>"
                                : o.promoCode();
            System.out.printf("  %-8s  promo=%-8s  £%.2f → £%.2f%n",
                o.id(), promoDisplay, o.amount(), finalPrice);
        }

        System.out.println("\n[ null vs Optional ]");
        System.out.println("  null               → absence of value (risk: NPE if dereferenced)");
        System.out.println("  Optional.empty()   → explicit 'no value' (no NPE risk)");
        System.out.println("  Optional.of(x)     → guaranteed non-null value");
        System.out.println("  Optional.ofNullable(x) → wraps potentially-null reference");

        // NullPointerException demo (caught safely)
        System.out.println("\n[ NPE demo — helpful message in JDK 14+ ]");
        try {
            String s = null;
            int len = s.length();   // NPE: Cannot invoke String.length() because s is null
        } catch (NullPointerException e) {
            System.out.println("  NPE: " + e.getMessage());
        }

        // instanceof null-safety
        Object obj = null;
        System.out.println("\n[ instanceof with null ]");
        System.out.println("  null instanceof String: " + (obj instanceof String));
        System.out.println("  null instanceof Object: " + (obj instanceof Object));
        // Both false — instanceof always returns false for null, regardless of type
    }
}
```

**How to run:** `java ReservedLiteralsIntermediate.java`

`Optional.ofNullable(code)` wraps a possibly-`null` reference into a type that forces the caller to handle the absent case explicitly — `orElse`, `map`, `ifPresent` — instead of risking an NPE from silent `null` propagation.

### Level 3 — Advanced

Same order system: demonstrate `null` in switch patterns (Java 21+), ternary chains, `Objects.requireNonNull`, and a custom null-safety analysis that walks an order graph and reports all null-producing paths.

```java
import java.util.*;
import java.util.stream.*;

public class ReservedLiteralsAdvanced {

    record Customer(String id, String email) {}
    record Order(String id, Customer customer, String promoCode, double amount) {}

    static String describePromo(String code) {
        // Java 21: null as a case label in switch
        return switch (code) {
            case null   -> "no promotion";
            case ""     -> "blank code (invalid)";
            case "SAVE10","SAVE20" -> "valid: " + code;
            default     -> "unknown: " + code;
        };
    }

    static void validate(Order o) {
        Objects.requireNonNull(o,            "order must not be null");
        Objects.requireNonNull(o.id(),       "order id must not be null");
        Objects.requireNonNull(o.customer(), "customer must not be null");
        // promoCode is intentionally nullable — Optional is better here but null is fine
        if (o.amount() <= 0) throw new IllegalArgumentException("amount must be positive");
    }

    public static void main(String[] args) {
        System.out.println("=== Advanced: null in switch, requireNonNull, null safety ===\n");

        // 1. null in switch (Java 21+)
        String[] codes = { "SAVE10", null, "", "SAVE20", "UNKNOWN" };
        System.out.println("[ null-aware switch ]");
        for (String c : codes)
            System.out.printf("  %-12s → %s%n",
                c == null ? "null" : "\"" + c + "\"", describePromo(c));

        // 2. requireNonNull
        System.out.println("\n[ Objects.requireNonNull ]");
        var goodCustomer = new Customer("C-001", "alice@example.com");
        var goodOrder    = new Order("ORD-001", goodCustomer, "SAVE10", 299.99);
        try {
            validate(goodOrder);
            System.out.println("  ORD-001: validates OK");
        } catch (NullPointerException | IllegalArgumentException e) {
            System.out.println("  ORD-001 error: " + e.getMessage());
        }

        try {
            var badOrder = new Order(null, goodCustomer, null, 100.0);
            validate(badOrder);
        } catch (NullPointerException e) {
            System.out.println("  null-id order: " + e.getMessage());
        }

        // 3. Null-producing path analysis
        System.out.println("\n[ Null-producing path report ]");
        List<Order> orders = List.of(
            new Order("ORD-001", goodCustomer,             "SAVE10", 299.99),
            new Order("ORD-002", goodCustomer,              null,    150.00),
            new Order("ORD-003", new Customer("C-002", null), "SAVE20", 80.00),
            new Order(null,      goodCustomer,              null,     0.00)
        );

        for (Order o : orders) {
            List<String> nullFields = new ArrayList<>();
            if (o.id()       == null) nullFields.add("order.id");
            if (o.customer() == null) nullFields.add("order.customer");
            else if (o.customer().email() == null) nullFields.add("customer.email");
            if (o.promoCode()== null) nullFields.add("promoCode");

            String orderId = o.id() != null ? o.id() : "<null-id>";
            System.out.printf("  %-10s  null fields: %s%n",
                orderId, nullFields.isEmpty() ? "none" : nullFields);
        }

        // 4. Truthiness: Java has none — only explicit boolean
        System.out.println("\n[ No truthiness in Java — only boolean ]");
        System.out.println("  if (1)       → compile error (not boolean)");
        System.out.println("  if (\"hello\") → compile error (not boolean)");
        System.out.println("  if (null)    → compile error (not boolean)");
        System.out.println("  if (list)    → compile error (not boolean)");
        System.out.println("  Only boolean/Boolean expressions allowed in conditions.");
    }
}
```

**How to run:** `java ReservedLiteralsAdvanced.java`

`case null ->` in a switch expression (Java 21) eliminates a separate null guard before the switch — without it, a `null` value would throw `NullPointerException` when matched against switch cases.

## 6. Walkthrough

Execution trace in `ReservedLiteralsAdvanced.main`:

**`describePromo(null)` — null-aware switch.** The switch expression checks each case label in order. `case null` is evaluated first when the selector is `null`. Without `case null`, a `null` selector in a switch would throw `NullPointerException` before any case is tried (prior to Java 21). With `case null ->`, it cleanly returns `"no promotion"`.

**`Objects.requireNonNull(o.id(), "order id must not be null")`.** This is equivalent to `if (o.id() == null) throw new NullPointerException("order id must not be null")` — but produces a better error message that identifies the exact null field, making the NPE actionable. For `badOrder` with `id=null`, the message "order id must not be null" appears in the catch block output.

**Null-producing path analysis.** Each `Order` in the list is inspected: `o.id() == null`, `o.customer() == null`, `o.customer().email() == null`, `o.promoCode() == null`. Short-circuit evaluation (`o.customer() == null ? ... : o.customer().email() == null`) prevents NPE when dereferencing `o.customer()` before checking it.

**No truthiness.** In Python or JavaScript, `if (1)` or `if ("hello")` is legal (truthy values). In Java, the condition of `if` must be a `boolean` or `Boolean`. This eliminates an entire class of bugs where a non-zero integer is silently treated as `true`.

## 7. Gotchas & takeaways

> **`null == null` is always `true` but `null.equals(anything)` throws `NullPointerException`.** Never call `a.equals(b)` when `a` might be `null` — reverse it: `b.equals(a)` if `b` is a known non-null literal, or use `Objects.equals(a, b)` which handles both sides being null safely.

> **`boolean` fields default to `false`; reference fields default to `null`.** Local variables in methods do NOT get default values — using an uninitialised local is a compile error. Only fields (class and instance) are zero-initialised by the JVM.

- `true` and `false` are the only two `boolean` values — no numeric truthiness in Java.
- `null` is the default value of any unset reference field; it means "no object".
- Primitives (`int`, `double`, `boolean`, etc.) cannot hold `null`.
- `instanceof` on a `null` reference always returns `false` — it never throws.
- `null` in switch expressions (Java 21+) requires an explicit `case null ->` arm; otherwise NPE.
- Prefer `Objects.requireNonNull` for parameter validation and `Optional` for APIs that may return absent values.
- `Objects.equals(a, b)` is null-safe equality; `a.equals(b)` is not when `a` can be `null`.
