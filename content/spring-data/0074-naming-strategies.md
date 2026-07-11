---
card: spring-data
gi: 74
slug: naming-strategies
title: "Naming strategies"
---

## 1. What it is

A Hibernate **naming strategy** is the algorithm that converts Java-side names (entity class names, field names) into database-side names (table names, column names) when no explicit `@Table`/`@Column` override is given. Hibernate splits this into two cooperating strategies: an **implicit** naming strategy (invents a name when none is specified at all) and a **physical** naming strategy (transforms whatever name — implicit or explicit — into its final physical form, most commonly converting `camelCase` to `snake_case`).

```java
@Entity
class OrderLineItem {         // implicit: "OrderLineItem" -> physical (snake_case): "order_line_item"
    String customerName;      // implicit: "customerName" -> physical: "customer_name"
}
```

## 2. Why & when

Every JPA card in this section has assumed table and column names "just work" without explicit `@Table`/`@Column` annotations — naming strategies are the reason why, and understanding the two-stage process (implicit, then physical) explains exactly what name to expect for any entity or field, and where to intervene if the default doesn't match an existing schema.

Reach for an explicit understanding — or a custom strategy — specifically when:

- You're mapping entities onto an *existing* database schema whose naming convention doesn't match Hibernate's default (e.g., all-caps column names, a legacy schema using abbreviations) — a custom physical naming strategy can bulk-correct the mismatch without annotating every single field.
- You're debugging a "table/column not found" startup error — it's often the implicit or physical strategy producing a name that doesn't match what's actually in the schema, rather than an actual JPA mapping mistake.
- You want consistent naming across a large codebase without relying on every developer remembering to add `@Table`/`@Column` on every entity — configuring the strategy once at the application level is more reliable.

## 3. Core concept

```
 Java: class OrderLineItem { String customerName; }

 Stage 1 -- IMPLICIT strategy (only runs if no @Table/@Column given):
   no @Table  -> implicit name = "OrderLineItem"
   no @Column -> implicit name = "customerName"

 Stage 2 -- PHYSICAL strategy (ALWAYS runs, on implicit OR explicit names):
   "OrderLineItem"  -> physical name = "order_line_item"   (Spring Boot default: CamelCaseToUnderscoresNamingStrategy)
   "customerName"   -> physical name = "customer_name"

 Explicit override skips stage 1, but stage 2 STILL applies:
   @Column(name = "custName") -> implicit stage skipped -> physical stage still runs -> "cust_name"
```

The implicit strategy only fires when you didn't specify a name; the physical strategy always runs afterward, even on names you gave explicitly.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Java names pass through an implicit naming stage, then always through a physical naming stage, to produce the final database name">
  <rect x="20" y="20" width="160" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">customerName (Java)</text>

  <rect x="230" y="20" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Implicit strategy</text>
  <text x="320" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(skipped if @Column given)</text>
  <text x="320" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; "customerName"</text>

  <rect x="460" y="20" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Physical strategy</text>
  <text x="540" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(ALWAYS runs)</text>
  <text x="540" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; "customer_name"</text>

  <line x1="180" y1="45" x2="225" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ns)"/>
  <line x1="410" y1="45" x2="455" y2="45" stroke="#8b949e" stroke-width="1.3" marker-end="url(#ns)"/>
  <defs><marker id="ns" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every Java-side name funnels through the physical strategy on its way to a final database name — regardless of whether it started implicit or explicit.

## 5. Runnable example

The scenario: mapping a `CustomerOrder` entity's fields, evolving from a manual implementation of the default two-stage pipeline, to a version showing that explicit overrides still pass through the physical stage, to a custom physical strategy fixing a legacy schema's naming convention.

### Level 1 — Basic

Model the default two-stage pipeline directly: implicit naming (Java name as-is) followed by physical naming (camelCase to snake_case).

```java
import java.util.*;

public class NamingLevel1 {
    // Stage 1: implicit naming strategy -- when nothing is specified, use the Java name as-is.
    static String implicitName(String javaName) {
        return javaName; // Hibernate's ImplicitNamingStrategy default: no transformation
    }

    // Stage 2: physical naming strategy -- Spring Boot's default converts camelCase to snake_case.
    static String physicalName(String implicit) {
        StringBuilder sb = new StringBuilder();
        for (char c : implicit.toCharArray()) {
            if (Character.isUpperCase(c)) { sb.append('_').append(Character.toLowerCase(c)); }
            else sb.append(c);
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        String[] javaNames = { "CustomerOrder", "customerName", "orderTotal" };
        for (String name : javaNames) {
            String implicit = implicitName(name);
            String physical = physicalName(implicit);
            System.out.println(name + " -> implicit: " + implicit + " -> physical: " + physical);
        }
    }
}
```

How to run: `java NamingLevel1.java`

`CustomerOrder` becomes `_customer_order` — close, but real Hibernate strategies also lowercase and strip a leading underscore; this simplified model shows the *shape* of the two-stage pipeline (implicit, then physical) that real Hibernate naming strategies implement more carefully.

### Level 2 — Intermediate

Show that an explicit `@Column`-style override skips the implicit stage, but the physical stage still applies to whatever name was given.

```java
import java.util.*;

public class NamingLevel2 {
    static String physicalName(String name) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (Character.isUpperCase(c)) {
                if (i > 0) sb.append('_');
                sb.append(Character.toLowerCase(c));
            } else sb.append(c);
        }
        return sb.toString();
    }

    // Simulates a field mapping: either implicit (no override) or explicit (@Column(name=...)).
    record FieldMapping(String javaName, String explicitOverride) {
        String resolvedName() {
            String beforePhysical = explicitOverride != null ? explicitOverride : javaName; // stage 1 (or skip)
            return physicalName(beforePhysical); // stage 2 -- ALWAYS runs
        }
    }

    public static void main(String[] args) {
        FieldMapping noOverride = new FieldMapping("customerName", null);
        FieldMapping withOverride = new FieldMapping("customerName", "custName"); // @Column(name = "custName")

        System.out.println("No @Column override:      " + noOverride.resolvedName());
        System.out.println("@Column(name=\"custName\"): " + withOverride.resolvedName());
    }
}
```

How to run: `java NamingLevel2.java`

`noOverride` resolves through both stages: `customerName` (implicit, unchanged) → `customer_name` (physical). `withOverride` skips the implicit stage (the override `"custName"` is used directly) but *still* passes through the physical stage, becoming `cust_name` — proving the physical strategy applies universally, even to names you specified explicitly, which is a common point of confusion.

### Level 3 — Advanced

Implement a custom physical naming strategy matching an existing legacy schema's convention (all-uppercase, no separators) instead of the default snake_case, and apply it across several entity/field names at once.

```java
import java.util.*;
import java.util.function.*;

public class NamingLevel3 {
    static String defaultPhysical(String name) { // Spring Boot's default: snake_case
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < name.length(); i++) {
            char c = name.charAt(i);
            if (Character.isUpperCase(c)) { if (i > 0) sb.append('_'); sb.append(Character.toLowerCase(c)); }
            else sb.append(c);
        }
        return sb.toString();
    }

    // A custom PhysicalNamingStrategy matching a legacy schema: ALL_CAPS, no separators.
    static String legacyPhysical(String name) {
        return name.toUpperCase();
    }

    record Entity(String javaName, List<String> fields) {}

    static void printMapping(String label, Entity e, Function<String, String> physicalStrategy) {
        System.out.println(label + ": table " + e.javaName() + " -> " + physicalStrategy.apply(e.javaName()));
        for (String f : e.fields()) {
            System.out.println("  column " + f + " -> " + physicalStrategy.apply(f));
        }
    }

    public static void main(String[] args) {
        Entity customerOrder = new Entity("CustomerOrder", List.of("customerName", "orderTotal", "shippingAddress"));

        printMapping("Default (snake_case)", customerOrder, NamingLevel3::defaultPhysical);
        System.out.println();
        printMapping("Legacy (ALL_CAPS)", customerOrder, NamingLevel3::legacyPhysical);
    }
}
```

How to run: `java NamingLevel3.java`

The exact same `Entity` metadata (`CustomerOrder` with fields `customerName`, `orderTotal`, `shippingAddress`) produces two entirely different sets of table/column names depending on which physical strategy is applied — `customer_order`/`customer_name`/... under the default, or `CUSTOMERORDER`/`CUSTOMERNAME`/... under the legacy strategy — demonstrating how swapping the physical naming strategy bulk-corrects every entity's mapping at once, without touching individual `@Table`/`@Column` annotations.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `customerOrder` is constructed once, holding the Java-side names `"CustomerOrder"` and its three field names — this single piece of metadata is reused for both strategy demonstrations, exactly as one `@Entity` class definition is reused regardless of which naming strategy the application configures.

`printMapping("Default (snake_case)", customerOrder, NamingLevel3::defaultPhysical)` runs first: it prints the table mapping (`CustomerOrder -> customer_order`), then loops over each field, applying `defaultPhysical` to produce `customer_name`, `order_total`, and `shipping_address` in turn.

`printMapping("Legacy (ALL_CAPS)", customerOrder, NamingLevel3::legacyPhysical)` runs second, over the *same* `customerOrder` metadata, but passing `legacyPhysical` instead — producing `CUSTOMERORDER` for the table and `CUSTOMERNAME`, `ORDERTOTAL`, `SHIPPINGADDRESS` for the fields. Nothing about `customerOrder` itself changed between the two calls; only the strategy function passed in differs.

```
customerOrder = Entity("CustomerOrder", [customerName, orderTotal, shippingAddress])

defaultPhysical applied  -> customer_order / customer_name, order_total, shipping_address
legacyPhysical applied   -> CUSTOMERORDER  / CUSTOMERNAME, ORDERTOTAL, SHIPPINGADDRESS
```

In a real Spring Boot application, configuring `spring.jpa.hibernate.naming.physical-strategy` to point at a custom class implementing `PhysicalNamingStrategy` has exactly this effect application-wide: every `@Entity` and `@Column` in the codebase, without any change to the entity classes themselves, gets its table/column names recomputed through the new strategy the next time the `EntityManagerFactory` bootstraps and Hibernate builds its mapping metadata — which is why matching an existing legacy database's naming convention is usually a one-time configuration change, not a per-entity annotation exercise.

## 7. Gotchas & takeaways

> Gotcha: the implicit and physical strategies are configured *independently* (`spring.jpa.hibernate.naming.implicit-strategy` and `.physical-strategy`) — overriding only one while assuming it controls the whole pipeline is a common source of confusion when a name doesn't come out as expected.

- The implicit strategy invents a name only when none is given (no `@Table`/`@Column`); the physical strategy runs on *every* name, implicit or explicit.
- Spring Boot's default physical strategy converts `camelCase` to `snake_case` — this is why entities typically don't need explicit `@Column(name = ...)` annotations to get conventional-looking database names.
- A custom `PhysicalNamingStrategy` is the right tool for bulk-matching an existing schema's naming convention across every entity at once, rather than annotating each field individually.
- "Table/column not found" startup errors are often a naming-strategy mismatch, not a mapping mistake — check what name the configured strategy actually produces before assuming the annotation itself is wrong.
