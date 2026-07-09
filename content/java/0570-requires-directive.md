---
card: java
gi: 570
slug: requires-directive
title: requires directive
---

## 1. What it is

The `requires` directive inside `module-info.java` declares that a module depends on another module's exported packages. It's the module system's explicit dependency edge: `requires other.module` means "give this module access to `other.module`'s exported packages, and refuse to compile or launch if `other.module` isn't available."

## 2. Why & when

On the classpath, a JAR's real dependencies were whatever classes it happened to reference — nothing declared them up front, so the only way to discover a missing dependency was to run the code and see what broke (`NoClassDefFoundError`, `ClassNotFoundException`), sometimes deep into a request handler in production. `requires` moves that discovery to compile time and application startup: if a module references a type from another module without declaring `requires` for it, `javac` refuses to compile; if the required module is absent from the module path at launch, the JVM refuses to start the application at all. Use `requires` for every module (JDK platform module or third-party) whose exported types your module's code actually references directly.

## 3. Core concept

```java
module app {
    requires java.sql;      // needed because app's code imports java.sql.* types
    requires com.example.core;
}
```

```java
package com.myapp;
import java.sql.Connection; // requires java.sql lets this import resolve

public class Repository {
    Connection connection; // uses a type from the required module
}
```

Each `requires` names exactly one module. If `Repository` also used a type from a module `app` hadn't declared `requires` for, `javac` would fail immediately with an error naming the missing dependency — not a vague "class not found" but a specific "module not requires-d" diagnostic.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="requires declares a directed dependency edge from one module to another's exported packages">
  <rect x="20" y="40" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="70" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">module app</text>

  <line x1="200" y1="65" x2="380" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#r1)"/>
  <text x="290" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">requires</text>

  <rect x="380" y="40" width="220" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="70" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">module java.sql</text>

  <text x="20" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">Missing this edge -&gt; compile error the moment app's code imports a java.sql type.</text>

  <defs>
    <marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The edge is one-directional and explicit: `app` can see into `java.sql`'s exports, never the reverse.

## 5. Runnable example

Scenario: a small "billing" module that needs both a JDBC connection type from the JDK's own `java.sql` module and a `Money` type from a hand-written `com.example.core` module — starting with a single `requires`, then adding a second dependency, then observing exactly what happens when a needed `requires` is missing.

### Level 1 — Basic

```java
// File: billing/module-info.java
module billing {
    requires java.sql;
    exports com.billing.api;
}
```

```java
// File: billing/com/billing/api/Invoice.java
package com.billing.api;
import java.sql.Timestamp;

public class Invoice {
    private final String customerId;
    private final Timestamp issuedAt;

    public Invoice(String customerId, Timestamp issuedAt) {
        this.customerId = customerId;
        this.issuedAt = issuedAt;
    }

    @Override public String toString() {
        return "Invoice[" + customerId + " @ " + issuedAt + "]";
    }
}
```

```java
// File: app/module-info.java
module app {
    requires billing;
    requires java.sql; // needed because Main.java itself also constructs a Timestamp directly
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.billing.api.Invoice;
import java.sql.Timestamp;

public class Main {
    public static void main(String[] args) {
        Invoice invoice = new Invoice("cust-42", new Timestamp(0));
        System.out.println(invoice);
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find billing app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output (exact timestamp text may vary by machine timezone, but the pattern is stable):
```
Invoice[cust-42 @ 1970-01-01 00:00:00.0]
```

`requires java.sql` in `billing`'s `module-info.java` grants `billing` access to `java.sql`'s exported packages — without it, `import java.sql.Timestamp` inside `Invoice.java` would fail to compile. `app` needs its own separate `requires java.sql` too, for a different reason: `app`'s own `Main.java` directly `import`s and constructs a `Timestamp`. This is the key rule `requires` enforces — each module must declare `requires` for every module whose types *its own code* references directly, regardless of what its dependencies already require for their own internal use.

### Level 2 — Intermediate

```java
// File: com.example.core/module-info.java
module com.example.core {
    exports com.example.core.money;
}
```

```java
// File: com.example.core/com/example/core/money/Money.java
package com.example.core.money;

public record Money(long cents, String currency) {
    @Override public String toString() {
        return String.format("%d.%02d %s", cents / 100, cents % 100, currency);
    }
}
```

```java
// File: billing/module-info.java — now requires TWO modules
module billing {
    requires java.sql;
    requires com.example.core;
    exports com.billing.api;
}
```

```java
// File: billing/com/billing/api/Invoice.java
package com.billing.api;
import com.example.core.money.Money;
import java.sql.Timestamp;

public class Invoice {
    private final String customerId;
    private final Money amount;
    private final Timestamp issuedAt;

    public Invoice(String customerId, Money amount, Timestamp issuedAt) {
        this.customerId = customerId;
        this.amount = amount;
        this.issuedAt = issuedAt;
    }

    @Override public String toString() {
        return "Invoice[" + customerId + ", " + amount + "]";
    }
}
```

```java
// File: app/module-info.java
module app {
    requires billing;
    requires com.example.core; // Main.java constructs a Money directly, not just through Invoice
    requires java.sql;         // Main.java constructs a Timestamp directly too
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.billing.api.Invoice;
import com.example.core.money.Money;
import java.sql.Timestamp;

public class Main {
    public static void main(String[] args) {
        Invoice invoice = new Invoice("cust-42", new Money(19999, "USD"), new Timestamp(0));
        System.out.println(invoice);
    }
}
```

**How to run:**
```
javac -d out --module-source-path . $(find com.example.core billing app -name "*.java")
java --module-path out -m app/com.myapp.Main
```

Expected output:
```
Invoice[cust-42, 199.99 USD]
```

The real-world concern this adds: `billing` now depends on **two** separate modules, `java.sql` (a JDK platform module) and `com.example.core` (a hand-written one), and needs a `requires` line for each — `requires` is never transitive by default, so `billing` must list both explicitly even though `Invoice` uses types from both simultaneously in its own field declarations. `app` needs its own `requires` for both too, for the same reason as Level 1: it constructs a `Money` and a `Timestamp` directly in `Main.java`, on top of using `Invoice` from `billing` — each module declares `requires` based only on what its own code touches, never inheriting visibility from what a dependency happens to need internally.

### Level 3 — Advanced

```java
// File: billing/module-info.java — the requires java.sql line is REMOVED
module billing {
    requires com.example.core;
    exports com.billing.api;
}
```

```java
// File: billing/com/billing/api/Invoice.java — still imports java.sql.Timestamp
package com.billing.api;
import com.example.core.money.Money;
import java.sql.Timestamp; // this import will now fail to resolve

public class Invoice {
    private final String customerId;
    private final Money amount;
    private final Timestamp issuedAt;

    public Invoice(String customerId, Money amount, Timestamp issuedAt) {
        this.customerId = customerId;
        this.amount = amount;
        this.issuedAt = issuedAt;
    }

    @Override public String toString() {
        return "Invoice[" + customerId + ", " + amount + "]";
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find com.example.core billing -name "*.java")`

Expected output (compilation fails — this is the intended demonstration):
```
billing/com/billing/api/Invoice.java:3: error: package java.sql is not visible
import java.sql.Timestamp;
           ^
  (package java.sql is declared in module java.sql, but module billing does not read it)
```

This handles the production-flavoured case of **forgetting a `requires` line** — an easy mistake when refactoring which types a class uses. The compiler catches it immediately and precisely: rather than a vague "symbol not found," the error names the exact missing module (`java.sql`) and explains why (`billing does not read it`), pointing directly at the fix — add `requires java.sql;` back to `billing/module-info.java`.

## 6. Walkthrough

Execution starts with the compilation command in Level 3, which intentionally omits `requires java.sql` from `billing`'s `module-info.java` to demonstrate the failure path.

`javac` first reads `com.example.core/module-info.java` and `billing/module-info.java`, building its picture of the module graph: `billing` requires `com.example.core` only. It then begins compiling `billing`'s source files, starting with `Invoice.java`.

```
javac processes Invoice.java's imports:

import com.example.core.money.Money  -> billing requires com.example.core, which exports this package -> OK
import java.sql.Timestamp            -> billing does NOT requires java.sql -> ERROR
```

When `javac` reaches `import java.sql.Timestamp`, it checks whether `billing` has declared `requires java.sql` (directly, since `requires` is non-transitive by default — covered in a related topic). It hasn't, so `javac` reports that `java.sql` is "not visible" to `billing`, with the specific explanation "module billing does not read it" — module-system terminology for "no `requires` edge exists from `billing` to `java.sql`." Compilation stops here with a nonzero exit code; no `.class` files are produced for `billing`.

The fix, not shown as a fourth level but implied by the error message itself, is exactly what Level 2 already had: add `requires java.sql;` back to `billing/module-info.java`. Once that line is restored, the same `Invoice.java` source compiles cleanly, because `billing` now has an explicit `requires` edge to the module that exports the `java.sql.Timestamp` type it references.

This demonstrates the core value of `requires`: a dependency that's actually used in code but not declared is caught at the exact point of the missing declaration, during compilation — long before the gap could surface as a runtime failure in a deployed application.

## 7. Gotchas & takeaways

> `requires` is checked against what a module's code **actually imports and uses**, not against what's merely present on the module path. Having `java.sql` available in the runtime environment does not make it usable by a module that never declared `requires java.sql` — presence and permission are two separate things, by design, so that a module's declared dependencies always accurately reflect its real dependencies.

- Every module implicitly `requires java.base` (containing `java.lang`, `java.util`, etc.) — this line is essentially never written explicitly, since every module needs it and the compiler adds it automatically.
- `requires` is **not transitive by default**: if `app` requires `billing`, and `billing` requires `com.example.core`, `app` cannot use `com.example.core`'s types directly unless `app` also declares its own `requires com.example.core` — or `billing` marks its `requires com.example.core` as `requires transitive`, a related, separate directive.
- A missing `requires` produces a specific, actionable compiler error naming the exact module involved — far more diagnostic than the classpath era's `NoClassDefFoundError`, which often surfaced only when the missing class was first touched at runtime, not at compile time.
- `requires` for a module that doesn't exist on the module path at all produces a different error, at `javac` invocation time (or `java` launch time for a fully-compiled application), naming the module that couldn't be resolved — again, caught before any application code runs.
- Circular `requires` between two modules (module A requires module B, and B requires A) is not allowed and is rejected by the compiler — module dependency graphs must be acyclic, a constraint that sometimes forces refactoring shared code out into a third module both can depend on.
