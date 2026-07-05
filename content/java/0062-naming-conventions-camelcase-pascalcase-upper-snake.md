---
card: java
gi: 62
slug: naming-conventions-camelcase-pascalcase-upper-snake
title: Naming conventions (camelCase, PascalCase, UPPER_SNAKE)
---

## 1. What it is

Java has community-standard naming conventions that every Java programmer follows. They are not enforced by the compiler — they are enforced by code review, Checkstyle, and SonarQube. The three main forms:

| Form | Pattern | Used for |
|---|---|---|
| `camelCase` | first word lowercase, rest capitalised | variables, method names, parameters |
| `PascalCase` | every word capitalised | class, interface, enum, record, annotation names |
| `UPPER_SNAKE_CASE` | all uppercase, words separated by `_` | constants (`static final` fields) |

```java
// camelCase → variables, methods, parameters
int orderCount = 0;
String customerName = "Alice";
void processOrder(String orderId, double amount) { }

// PascalCase → types
class OrderService { }
interface PaymentProcessor { }
enum HttpStatus { OK, NOT_FOUND }
record UserEvent(String id, long timestamp) { }

// UPPER_SNAKE_CASE → constants
static final int MAX_RETRY_COUNT = 3;
static final String DEFAULT_CURRENCY = "GBP";
```

## 2. Why & when

Conventions exist so that any Java programmer can read any Java codebase and immediately know what kind of thing each identifier refers to. `OrderService` — a type. `orderService` — a variable holding an instance. `ORDER_SERVICE_TIMEOUT_MS` — a constant. The conventions carry type-role information without needing to look up declarations. They apply everywhere: your own code, library code you read, Spring beans, JDK source.

## 3. Core concept

```java
// ---- package names: all lowercase, dot-separated, no underscores ----
package com.example.orders;
package org.apache.commons.lang3;
// NOT: com.Example.Orders  or  com.example.myOrders

// ---- class / interface / enum / record / annotation: PascalCase ----
class OrderService { }
interface PaymentGateway { }
enum OrderStatus { PENDING, CONFIRMED, SHIPPED }
record OrderEvent(String orderId, long epochMs) { }
@interface Transactional { }  // annotation

// ---- method names: camelCase, verb or verb-phrase ----
void processOrder() { }
String getOrderId() { }
boolean isComplete() { }
List<Order> findAllByStatus(OrderStatus status) { }

// ---- variable / parameter names: camelCase, noun or noun-phrase ----
int retryCount;
String orderId;
List<Order> pendingOrders;

// ---- constants: UPPER_SNAKE_CASE, adjective or noun ----
static final int MAX_RETRY_COUNT = 3;
static final long PAYMENT_TIMEOUT_MS = 30_000L;
static final String BASE_URL = "https://api.example.com";

// ---- type parameters: single uppercase letter or short PascalCase ----
class Box<T> { }
class Pair<K, V> { }
class Repository<ID, T extends Entity> { }

// ---- acronyms in names: treat as words, capitalise only first letter ----
// Good:
class HttpClient { }    // Http, not HTTP
String userId;          // user + Id, not userID
class JsonParser { }    // Json, not JSON

// Acceptable alternative (Google style):
class HTTPClient { }    // some teams keep acronyms all-caps — be consistent

// ---- booleans: is/has/can prefix ----
boolean isActive;
boolean hasChildren;
boolean canRetry;
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java naming conventions: camelCase for variables/methods, PascalCase for types, UPPER_SNAKE for constants">
  <rect x="8" y="8" width="684" height="169" rx="8" fill="#0d1117"/>

  <!-- camelCase -->
  <rect x="20" y="22" width="200" height="138" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">camelCase</text>
  <text x="120" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">variables · methods · params</text>
  <line x1="30" y1="62" x2="210" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="32" y="76" fill="#e6edf3" font-size="8" font-family="monospace">orderCount</text>
  <text x="32" y="89" fill="#e6edf3" font-size="8" font-family="monospace">processOrder()</text>
  <text x="32" y="102" fill="#e6edf3" font-size="8" font-family="monospace">customerId</text>
  <text x="32" y="115" fill="#e6edf3" font-size="8" font-family="monospace">isActive</text>
  <text x="32" y="128" fill="#e6edf3" font-size="8" font-family="monospace">findAllByStatus()</text>
  <text x="32" y="141" fill="#8b949e" font-size="7" font-family="sans-serif">first word lowercase</text>
  <text x="32" y="152" fill="#8b949e" font-size="7" font-family="sans-serif">rest: capitalised words</text>

  <!-- PascalCase -->
  <rect x="240" y="22" width="200" height="138" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">PascalCase</text>
  <text x="340" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">class · interface · enum · record</text>
  <line x1="250" y1="62" x2="430" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="252" y="76" fill="#e6edf3" font-size="8" font-family="monospace">OrderService</text>
  <text x="252" y="89" fill="#e6edf3" font-size="8" font-family="monospace">PaymentProcessor</text>
  <text x="252" y="102" fill="#e6edf3" font-size="8" font-family="monospace">HttpStatus</text>
  <text x="252" y="115" fill="#e6edf3" font-size="8" font-family="monospace">UserEvent</text>
  <text x="252" y="128" fill="#e6edf3" font-size="8" font-family="monospace">IllegalArgumentException</text>
  <text x="252" y="141" fill="#8b949e" font-size="7" font-family="sans-serif">every word capitalised</text>
  <text x="252" y="152" fill="#8b949e" font-size="7" font-family="sans-serif">no separators</text>

  <!-- UPPER_SNAKE -->
  <rect x="460" y="22" width="220" height="138" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">UPPER_SNAKE</text>
  <text x="570" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">static final constants only</text>
  <line x1="470" y1="62" x2="670" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="472" y="76" fill="#e6edf3" font-size="8" font-family="monospace">MAX_RETRY_COUNT</text>
  <text x="472" y="89" fill="#e6edf3" font-size="8" font-family="monospace">DEFAULT_CURRENCY</text>
  <text x="472" y="102" fill="#e6edf3" font-size="8" font-family="monospace">PAYMENT_TIMEOUT_MS</text>
  <text x="472" y="115" fill="#e6edf3" font-size="8" font-family="monospace">BASE_URL</text>
  <text x="472" y="128" fill="#e6edf3" font-size="8" font-family="monospace">HTTP_STATUS_OK</text>
  <text x="472" y="141" fill="#8b949e" font-size="7" font-family="sans-serif">ALL CAPS + underscores</text>
  <text x="472" y="152" fill="#8b949e" font-size="7" font-family="sans-serif">signals immutable value</text>
</svg>

Convention tells you what role a name plays before you look at its declaration — camelCase = instance/method, PascalCase = type, UPPER_SNAKE = constant.

## 5. Runnable example

Scenario: an order processing system that demonstrates all three naming forms in realistic code, then verifies each name against its expected convention programmatically.

### Level 1 — Basic

```java
import java.util.*;

public class NamingConventionsBasic {

    // UPPER_SNAKE_CASE: constants
    static final int    MAX_ITEMS_PER_ORDER = 50;
    static final double DEFAULT_TAX_RATE    = 0.20;
    static final String CURRENCY_CODE       = "GBP";

    // camelCase: fields
    private String orderId;
    private double totalAmount;
    private boolean isPaid;

    // PascalCase: constructor matches class name
    public NamingConventionsBasic(String orderId, double totalAmount) {
        this.orderId     = orderId;
        this.totalAmount = totalAmount;
        this.isPaid      = false;
    }

    // camelCase: methods
    public void markAsPaid()        { isPaid = true; }
    public boolean isPaid()         { return isPaid; }
    public double getTotalAmount()  { return totalAmount; }
    public String getOrderId()      { return orderId; }

    public static void main(String[] args) {
        System.out.println("=== Naming conventions demo ===\n");

        // camelCase: local variable
        NamingConventionsBasic currentOrder = new NamingConventionsBasic("ORD-001", 149.99);
        System.out.println("Order:    " + currentOrder.getOrderId());
        System.out.println("Amount:   " + CURRENCY_CODE + " " + currentOrder.getTotalAmount());
        System.out.println("Paid?     " + currentOrder.isPaid());
        System.out.println("Max items: " + MAX_ITEMS_PER_ORDER);
        System.out.println("Tax rate:  " + (DEFAULT_TAX_RATE * 100) + "%");

        currentOrder.markAsPaid();
        System.out.println("After markAsPaid(): " + currentOrder.isPaid());
    }
}
```

**How to run:** `java NamingConventionsBasic.java`

Reading `isPaid` vs `IsPaid` vs `IS_PAID` instantly signals: method/variable, not a type, not a constant. The convention replaces a type annotation with a visual cue.

### Level 2 — Intermediate

Same order system: add an enum (`OrderStatus` in PascalCase), a record (`OrderEvent`), and a convention validator that checks each field against its expected naming form.

```java
import java.util.*;
import java.util.regex.*;

public class NamingConventionsIntermediate {

    // PascalCase: enum type; UPPER_SNAKE: enum constants
    enum OrderStatus { PENDING, CONFIRMED, SHIPPED, CANCELLED }

    // PascalCase: record type; camelCase: components
    record OrderEvent(String orderId, OrderStatus status, long epochMs) {}

    // UPPER_SNAKE: constants
    static final long   SESSION_TIMEOUT_MS = 30_000L;
    static final int    MAX_RETRY_COUNT    = 3;
    static final String BASE_API_URL       = "https://api.example.com";

    // camelCase: instance fields
    private final String     orderId;
    private       OrderStatus currentStatus;
    private final List<OrderEvent> eventLog = new ArrayList<>();

    public NamingConventionsIntermediate(String orderId) {
        this.orderId       = orderId;
        this.currentStatus = OrderStatus.PENDING;
        log(OrderStatus.PENDING);
    }

    // camelCase: methods — verb phrases
    public void confirmOrder() { transition(OrderStatus.CONFIRMED); }
    public void shipOrder()    { transition(OrderStatus.SHIPPED); }

    private void transition(OrderStatus next) {
        currentStatus = next;
        log(next);
    }

    private void log(OrderStatus s) {
        eventLog.add(new OrderEvent(orderId, s, System.currentTimeMillis()));
    }

    public static void main(String[] args) {
        System.out.println("=== Intermediate naming conventions ===\n");

        NamingConventionsIntermediate order = new NamingConventionsIntermediate("ORD-002");
        order.confirmOrder();
        order.shipOrder();

        System.out.println("Event log for " + order.orderId + ":");
        for (OrderEvent e : order.eventLog)
            System.out.printf("  %s → %s%n", e.orderId(), e.status());

        System.out.println("\n[ Convention checker ]");
        checkConvention("orderId",           "camelCase",   "[a-z][a-zA-Z0-9]*");
        checkConvention("OrderStatus",        "PascalCase",  "[A-Z][a-zA-Z0-9]*");
        checkConvention("MAX_RETRY_COUNT",    "UPPER_SNAKE", "[A-Z][A-Z0-9_]*");
        checkConvention("session_timeout_ms", "camelCase",   "[a-z][a-zA-Z0-9]*");  // wrong form
        checkConvention("orderservice",       "PascalCase",  "[A-Z][a-zA-Z0-9]*");  // wrong form
    }

    static void checkConvention(String name, String expected, String regex) {
        boolean ok = Pattern.matches(regex, name);
        System.out.printf("  %-28s  expected %-12s  %s%n",
            name, expected, ok ? "✓ OK" : "✗ WARN — expected " + expected);
    }
}
```

**How to run:** `java NamingConventionsIntermediate.java`

`PENDING`, `CONFIRMED`, `SHIPPED` are enum constants — they follow UPPER_SNAKE even though they live inside a PascalCase type. Enum constants are effectively `public static final` fields, hence the convention.

### Level 3 — Advanced

Same order system: reflection-based convention auditor that scans all fields, methods, and nested types of a class at runtime and reports any naming violations — the same logic Checkstyle uses internally.

```java
import java.lang.reflect.*;
import java.util.*;
import java.util.regex.*;

public class NamingConventionsAdvanced {

    // --- demo domain classes to audit ---
    static final int    MAX_ORDER_VALUE_GBP = 10_000;
    static final String DEFAULT_REGION      = "EU";

    private String orderId;
    private double totalGbp;
    private boolean isPaid;

    // Intentionally badly-named members for the auditor to catch:
    private int BadField;          // PascalCase on a field — wrong
    private static final int wrongConstant = 5;  // camelCase on constant — wrong

    void ProcessOrder() { }        // PascalCase on method — wrong
    void processOrder() { }        // correct

    enum OrderStatus { PENDING, CONFIRMED }       // correct
    static class order_helper { }                  // snake_case class — wrong

    public static void main(String[] args) {
        System.out.println("=== Convention auditor (reflection-based) ===\n");
        audit(NamingConventionsAdvanced.class);
    }

    static void audit(Class<?> cls) {
        List<String> violations = new ArrayList<>();

        // Check fields
        for (Field f : cls.getDeclaredFields()) {
            String name = f.getName();
            boolean isConstant = Modifier.isStatic(f.getModifiers())
                              && Modifier.isFinal(f.getModifiers());
            if (isConstant) {
                if (!Pattern.matches("[A-Z][A-Z0-9_]*", name))
                    violations.add("FIELD constant '" + name + "' → expected UPPER_SNAKE");
            } else {
                if (!Pattern.matches("[a-z][a-zA-Z0-9]*", name))
                    violations.add("FIELD '" + name + "' → expected camelCase");
            }
        }

        // Check methods
        for (Method m : cls.getDeclaredMethods()) {
            String name = m.getName();
            // Skip synthetic/bridge/compiler-generated
            if (m.isSynthetic() || name.contains("$")) continue;
            if (!Pattern.matches("[a-z][a-zA-Z0-9]*", name))
                violations.add("METHOD '" + name + "' → expected camelCase");
        }

        // Check nested types
        for (Class<?> nested : cls.getDeclaredClasses()) {
            String name = nested.getSimpleName();
            if (!Pattern.matches("[A-Z][a-zA-Z0-9]*", name))
                violations.add("TYPE '" + name + "' → expected PascalCase");
        }

        // Report
        System.out.println("Auditing: " + cls.getSimpleName());
        System.out.println("Violations found: " + violations.size());
        if (violations.isEmpty()) {
            System.out.println("  ✓ All names conform.");
        } else {
            for (String v : violations) System.out.println("  ✗ " + v);
        }

        System.out.println("\n[ Convention reference ]");
        System.out.printf("  %-12s  %s%n", "camelCase",   "variables, methods, params, non-constant fields");
        System.out.printf("  %-12s  %s%n", "PascalCase",  "class, interface, enum, record, annotation");
        System.out.printf("  %-12s  %s%n", "UPPER_SNAKE", "static final fields (constants)");
        System.out.printf("  %-12s  %s%n", "lowercase",   "package names (com.example.orders)");
        System.out.printf("  %-12s  %s%n", "T / K,V",     "generic type parameters");
    }
}
```

**How to run:** `java NamingConventionsAdvanced.java`

The auditor uses `Modifier.isStatic(f.getModifiers()) && Modifier.isFinal(f.getModifiers())` to distinguish constants from mutable fields — the same test Checkstyle's `ConstantName` rule applies. `m.isSynthetic()` filters out compiler-generated bridge methods which do not follow human naming conventions.

## 6. Walkthrough

Execution trace in `NamingConventionsAdvanced.main`:

**`audit(NamingConventionsAdvanced.class)`.** Reflection visits all declared members of the class. `getDeclaredFields()` returns all fields regardless of visibility — including `BadField`, `wrongConstant`, `orderId`, `totalGbp`, `isPaid`.

**Field loop.** For each field, `Modifier.isStatic && Modifier.isFinal` detects constants. `MAX_ORDER_VALUE_GBP` and `DEFAULT_REGION` are constants — checked against `[A-Z][A-Z0-9_]*`. `wrongConstant` is also static+final but matches `[a-z]...` — violation logged. `BadField` is a non-constant but starts with uppercase — violation logged.

**Method loop.** `ProcessOrder` starts with uppercase — violation. `processOrder` matches `[a-z][a-zA-Z0-9]*` — clean. `m.isSynthetic()` skips the `$deserializeLambda$` and similar compiler-generated methods that the JVM inserts for lambdas/method references.

**Nested type loop.** `OrderStatus` is PascalCase — clean. `order_helper` contains underscores and starts lowercase — violation.

**Final report.** Violations are printed in declaration order. Checkstyle produces an identical category of findings during `mvn verify`, except it operates on source text rather than bytecode/reflection.

## 7. Gotchas & takeaways

> **Enum constants use UPPER_SNAKE, not PascalCase.** `enum Day { Monday }` is wrong; `enum Day { MONDAY }` is correct. Enum constants are `public static final` values — so they follow the constant convention. Exception: some teams use PascalCase for rich enums with many fields (this is minority practice; stick with UPPER_SNAKE unless your team explicitly decides otherwise).

> **`boolean` accessor convention: `isX()` not `getX()`.** JavaBeans spec defines that `boolean` getters use the `is` prefix. Frameworks (Spring, Jackson, Hibernate) rely on this to detect boolean properties via reflection. Using `getIsPaid()` instead of `isPaid()` breaks property detection.

- camelCase: variables, methods, parameters, non-constant fields.
- PascalCase: class, interface, enum type, record, annotation type.
- UPPER_SNAKE: `static final` constants — enum constants too.
- Package names: all lowercase, no underscores (`com.example.orders`).
- Type parameters: single uppercase letter (`T`, `K`, `V`, `E`) or short PascalCase (`ID`, `RESULT`).
- Acronyms: treat as a word — `HttpClient` not `HTTPClient` (unless team style says otherwise — be consistent).
- Boolean fields/methods: `isX` / `hasX` / `canX` prefix signals boolean semantics.
- These are conventions — the compiler doesn't enforce them; Checkstyle and SonarQube do.
