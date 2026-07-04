---
card: spring-framework
gi: 247
slug: transaction-proxy-self-invocation-limitation
title: Transaction proxy & self-invocation limitation
---

## 1. What it is

`@Transactional` relies on Spring AOP proxies. When you call a method on a Spring-managed bean from **outside** the bean, the call goes through the proxy — the transaction starts, the method runs, and the transaction commits or rolls back. When a method in the same class calls another method **on `this`**, the call bypasses the proxy entirely. No proxy means no transaction.

```java
@Service
public class InvoiceService {
    public void generateInvoice(Order order) {
        // PROBLEM: calls this.save() directly — bypasses proxy
        this.save(order);             // @Transactional on save() DOES NOTHING
    }

    @Transactional
    public void save(Order order) {  // annotation silently ignored when called via this
        repo.save(order);
    }
}
```

This is the same self-invocation problem as general AOP (tutorial 0233), but it appears most often with `@Transactional` because transaction annotations on public methods are extremely common.

## 2. Why & when

This limitation matters most for:

- **Helper methods** in service classes annotated with `@Transactional` that are called from other methods in the same class.
- **`@Transactional` on `private` methods** — silently ignored; Spring's proxy AOP cannot intercept private methods.
- **Batch operations** where an outer public method calls an inner `@Transactional` method per item — the inner transaction never starts.

The fix is always the same: **route the call through the proxy**, not through `this`.

## 3. Core concept

The proxy wraps the bean. The proxy holds a reference to the raw target. When the target's code runs `this.save(order)`, it calls directly on the raw object — the proxy is not involved.

```
External caller → PROXY → InvoiceService.generateInvoice()
                              │
                              └─► this.save()      ← raw object, no proxy
                                     ↓
                                InvoiceService.save()  ← @Transactional ignored
```

Three solutions, in order of preference:

1. **Refactor** — move `save()` into a separate `@Service` bean and inject it.
2. **Self-inject** — inject the bean's own proxy via `@Lazy @Autowired`.
3. **`AopContext.currentProxy()`** — retrieve the proxy from a ThreadLocal (requires `exposeProxy=true`).

AspectJ LTW (tutorial 0234) avoids this problem because the advice is woven into the bytecode — no proxy is involved and `this.save()` calls the woven version.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="rarr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
    <marker id="garr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Caller -->
  <rect x="10" y="95" width="70" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="45" y="119" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller</text>

  <line x1="82" y1="115" x2="135" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Proxy -->
  <rect x="135" y="70" width="130" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="200" y="91" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">TX Proxy</text>
  <line x1="145" y1="100" x2="255" y2="100" stroke="#8b949e" stroke-width="0.5"/>
  <text x="200" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">begin tx ✓</text>
  <text x="200" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">generateInvoice()</text>
  <text x="200" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">commit/rollback ✓</text>

  <line x1="267" y1="115" x2="320" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Target -->
  <rect x="320" y="40" width="215" height="175" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="428" y="62" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">InvoiceService (raw target)</text>
  <line x1="330" y1="72" x2="525" y2="72" stroke="#8b949e" stroke-width="0.5"/>
  <text x="428" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">generateInvoice(order) {</text>
  <text x="428" y="108" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">  this.save(order)  ← raw this</text>
  <text x="428" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">}</text>

  <line x1="428" y1="130" x2="428" y2="158" stroke="#f85149" stroke-width="1.5" marker-end="url(#rarr)"/>

  <text x="428" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Transactional</text>
  <text x="428" y="192" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">save(order) {}</text>
  <text x="428" y="207" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">no tx! proxy bypassed</text>
</svg>

External call enters the proxy (tx starts). `this.save()` inside the target bypasses the proxy — no transaction.

## 5. Runnable example

Scenario: an **`InvoiceService`** — first showing the bug, then fixing via self-injection, then fixing via `AopContext.currentProxy()`.

### Level 1 — Basic

The bug: `@Transactional` on `save()` is silently ignored when called from `generateInvoice()`.

```java
// TxSelfInvokeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;

@Configuration
@EnableTransactionManagement
@EnableAspectJAutoProxy
@ComponentScan
public class TxSelfInvokeDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("invoices-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxSelfInvokeDemo.class);
        System.out.println("=== BUG: self-invocation ===");
        ctx.getBean(InvoiceService.class).generateInvoice("INV-001");
        ctx.close();
    }
}

@Service
class InvoiceService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    InvoiceService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    public void generateInvoice(String invoiceId) {
        System.out.println("[generateInvoice] calling save via this — @Transactional ignored");
        this.save(invoiceId);   // BUG: no proxy → no transaction
    }

    @Transactional
    public void save(String invoiceId) {
        jdbc.update("INSERT INTO invoices(id,status) VALUES(?,'GENERATED')", invoiceId);
        System.out.println("[save] inserted — but is there a tx? Let's check via aspect...");
    }
}

// Aspect to verify whether a transaction is active
@Aspect @org.springframework.stereotype.Component
class TxCheckAspect {
    @Before("execution(* InvoiceService.save(..))")
    public void check(JoinPoint jp) {
        boolean active = org.springframework.transaction.support
            .TransactionSynchronizationManager.isActualTransactionActive();
        System.out.println("[TxCheck] transaction active when save() called: " + active);
    }
}
```

`invoices-schema.sql`: `CREATE TABLE invoices (id VARCHAR(20) PRIMARY KEY, status VARCHAR(20));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:spring-aop.jar:aspectjweaver.jar:h2.jar:. TxSelfInvokeDemo.java`

`[TxCheck] transaction active … false` — the aspect confirms no transaction is active when `save()` is called via `this`. The `@Transactional` annotation on `save()` was silently ignored.

---

### Level 2 — Intermediate

Fix via **self-injection** — inject the proxy of `InvoiceService` into itself.

```java
// TxSelfInvokeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;

@Configuration
@EnableTransactionManagement
@EnableAspectJAutoProxy
@ComponentScan
public class TxSelfInvokeDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("invoices-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxSelfInvokeDemo.class);
        System.out.println("=== FIX: self-injection ===");
        ctx.getBean(InvoiceService.class).generateInvoice("INV-002");
        ctx.close();
    }
}

@Service
class InvoiceService {
    @Lazy @Autowired
    private InvoiceService self;     // injects the PROXY, not the raw bean

    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    InvoiceService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    public void generateInvoice(String invoiceId) {
        System.out.println("[generateInvoice] calling save via self proxy");
        self.save(invoiceId);        // FIX: goes through the proxy → @Transactional fires
    }

    @Transactional
    public void save(String invoiceId) {
        jdbc.update("INSERT INTO invoices(id,status) VALUES(?,'GENERATED')", invoiceId);
        System.out.println("[save] inserted inside transaction");
    }
}

@Aspect @org.springframework.stereotype.Component
class TxCheckAspect {
    @Before("execution(* InvoiceService.save(..))")
    public void check(JoinPoint jp) {
        boolean active = org.springframework.transaction.support
            .TransactionSynchronizationManager.isActualTransactionActive();
        System.out.println("[TxCheck] transaction active: " + active);
    }
}
```

How to run: same classpath

`[TxCheck] transaction active: true` — the fix works. `@Lazy` is required to break the circular dependency (`InvoiceService` needs itself, but must not be injected before it's fully created). The `@Lazy` proxy is resolved only on first access.

---

### Level 3 — Advanced

Fix via **`AopContext.currentProxy()`** and demonstrate detecting vs debugging the self-invocation problem at runtime.

```java
// TxSelfInvokeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.aop.framework.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;

@Configuration
@EnableTransactionManagement
@EnableAspectJAutoProxy(exposeProxy = true)   // ← required for AopContext
@ComponentScan
public class TxSelfInvokeDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("invoices-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TxSelfInvokeDemo.class);

        // Detect: is the bean a proxy?
        InvoiceService svc = ctx.getBean(InvoiceService.class);
        System.out.println("Is AOP proxy? " + AopUtils.isAopProxy(svc));
        System.out.println("Target class: " + AopUtils.getTargetClass(svc).getSimpleName());

        System.out.println("\n=== FIX: AopContext.currentProxy() ===");
        svc.generateInvoice("INV-003");

        ctx.close();
    }
}

@Service
class InvoiceService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    InvoiceService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    public void generateInvoice(String invoiceId) {
        System.out.println("[generateInvoice] calling save via AopContext proxy");
        ((InvoiceService) AopContext.currentProxy()).save(invoiceId);  // FIX: proxy call
    }

    @Transactional
    public void save(String invoiceId) {
        jdbc.update("INSERT INTO invoices(id,status) VALUES(?,'GENERATED')", invoiceId);
        System.out.println("[save] inserted inside transaction");
    }
}

@Aspect @org.springframework.stereotype.Component
class TxCheckAspect {
    @Before("execution(* InvoiceService.save(..))")
    public void check(JoinPoint jp) {
        boolean active = org.springframework.transaction.support
            .TransactionSynchronizationManager.isActualTransactionActive();
        System.out.println("[TxCheck] transaction active: " + active);
    }
}
```

How to run: same classpath

`AopUtils.isAopProxy(svc)` → `true`. `AopUtils.getTargetClass(svc)` → `InvoiceService`. `AopContext.currentProxy()` retrieves the proxy from the ThreadLocal set by `exposeProxy=true`, casts it, and routes `save()` through the proxy. `[TxCheck] transaction active: true` confirms success.

## 6. Walkthrough

**Level 1 — bug path (step by step):**

```
caller → PROXY.generateInvoice("INV-001")
  → TransactionInterceptor:
      @Transactional on generateInvoice? NO (no annotation) → proceed without tx
  → InvoiceService.generateInvoice("INV-001")
      this.save("INV-001")   ← raw 'this' — not the proxy
        → InvoiceService.save("INV-001")  [directly, no proxy involved]
            jdbc.update("INSERT invoices…")   [runs WITHOUT a transaction!]
            autoCommit=true on the JDBC connection → INSERT auto-committed
  ← returns
```

**Level 2 — self-inject fix path:**

```
caller → PROXY.generateInvoice("INV-002")
  → generateInvoice("INV-002")
      self.save("INV-002")   ← self IS the PROXY
        → PROXY.save("INV-002")
            → TransactionInterceptor:
                @Transactional on save → YES → getTransaction()
                conn acquired; autoCommit=false
            → InvoiceService.save("INV-002")
                jdbc.update("INSERT invoices…")   [inside tx]
            → commit()   conn.commit()
  ← returns
```

**Level 3 — AopContext fix path:**

```
caller → PROXY.generateInvoice("INV-003")
  → generateInvoice("INV-003")
      AopContext.currentProxy()   ← reads ThreadLocal, returns PROXY ref
      cast to InvoiceService
      PROXY.save("INV-003")
        → TransactionInterceptor: begin tx
        → save() body: INSERT invoices
        → commit()
  ← returns
```

## 7. Gotchas & takeaways

> **`private` methods can NEVER participate in `@Transactional` via Spring AOP.** A `@Transactional` annotation on a `private` method is completely ignored — no warning, no error, no transaction. This is a proxy limitation: Spring's CGLIB/JDK proxies cannot intercept private methods.

> **The most dangerous form of this bug is `@Transactional` on a batch-inner method.** A common pattern is `batchImport()` calling `processSingle()` per item. If `processSingle()` is `@Transactional` and called via `this`, each item runs with no transaction. A single database error leaves data partially inserted.

> **`exposeProxy=true` has a small overhead.** Every intercepted method call writes the proxy ref to a ThreadLocal. Acceptable in most applications, but avoid it on hot-path beans in high-TPS systems. Prefer self-injection for those.

- The self-invocation problem is a consequence of proxy-based AOP — the proxy is not the target.
- Cleanest fix: move the called method into a separate `@Service` and inject it.
- `@Lazy @Autowired private MyService self` — self-injection; works for all proxy-based Spring AOP.
- `AopContext.currentProxy()` — works for legacy code where refactoring is costly; requires `exposeProxy=true`.
- AspectJ LTW (tutorial 0234) avoids this problem entirely — use it when the self-invocation pattern is pervasive.
