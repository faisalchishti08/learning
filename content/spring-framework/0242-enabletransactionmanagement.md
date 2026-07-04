---
card: spring-framework
gi: 242
slug: enabletransactionmanagement
title: "@EnableTransactionManagement"
---

## 1. What it is

`@EnableTransactionManagement` is a `@Configuration` annotation that activates Spring's annotation-driven transaction infrastructure. It registers three key beans:

1. `AnnotationTransactionAttributeSource` — parses `@Transactional` annotations on beans.
2. `TransactionInterceptor` — the AOP `MethodInterceptor` that calls `getTransaction`/`commit`/`rollback`.
3. `BeanFactoryTransactionAttributeSourceAdvisor` — the AOP advisor that matches beans with `@Transactional` methods and attaches the interceptor.

```java
@Configuration
@EnableTransactionManagement
public class AppConfig {
    @Bean
    public PlatformTransactionManager transactionManager(DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }
}
```

Without `@EnableTransactionManagement`, `@Transactional` annotations are parsed but no proxy is created — the annotation does nothing.

## 2. Why & when

`@EnableTransactionManagement` is required in any Java-config Spring application that uses `@Transactional`. Spring Boot auto-configures it via `TransactionAutoConfiguration` when a `PlatformTransactionManager` bean is present — you rarely add it manually in Boot apps.

Add it explicitly when:
- Writing a non-Boot Spring Framework app.
- Writing a library or test configuration class that needs transaction support without Boot auto-configuration.
- Customizing the proxy mode, order, or transaction manager bean name resolution.

The XML equivalent is `<tx:annotation-driven/>`.

## 3. Core concept

`@EnableTransactionManagement` imports `TransactionManagementConfigurationSelector`, which registers one of two configurations:

- `ProxyTransactionManagementConfiguration` (default, `mode = AdviceMode.PROXY`) — registers the three beans listed above, using Spring AOP proxies.
- `AspectJTransactionManagementConfiguration` (`mode = AdviceMode.ASPECTJ`) — configures the AspectJ `AnnotationTransactionAspect` for load-time or compile-time weaving instead of proxies.

Key attributes:

| Attribute | Default | Meaning |
|-----------|---------|---------|
| `mode` | `PROXY` | AOP mechanism: `PROXY` (Spring AOP) or `ASPECTJ` |
| `proxyTargetClass` | `false` | `true` forces CGLIB; `false` uses JDK when interface available |
| `order` | `Ordered.LOWEST_PRECEDENCE` | Advisor order when multiple AOP advisors are present |

The advisor's order matters: if a security aspect and a transaction aspect both apply, the lower `order` value fires first (outermost wrapper). The default `LOWEST_PRECEDENCE` means transaction advice wraps inside all other advice.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- @EnableTM -->
  <rect x="10" y="70" width="210" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="94" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@EnableTransactionManagement</text>
  <text x="115" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mode=PROXY | proxyTargetClass=false | order=MAX</text>

  <line x1="222" y1="100" x2="280" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="251" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">imports</text>

  <!-- Registered beans -->
  <rect x="280" y="25" width="220" height="150" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="390" y="48" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Registered Infrastructure</text>
  <line x1="290" y1="56" x2="490" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <text x="390" y="74" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">AnnotationTransactionAttributeSource</text>
  <text x="390" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(parses @Transactional)</text>
  <text x="390" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">TransactionInterceptor</text>
  <text x="390" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(begin/commit/rollback)</text>
  <text x="390" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">BeanFactoryTxAttributeSourceAdvisor</text>
  <text x="390" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(matches @Transactional beans)</text>

  <line x1="502" y1="100" x2="555" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Result -->
  <rect x="555" y="65" width="135" height="70" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="623" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional beans</text>
  <text x="623" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wrapped in proxy</text>
  <text x="623" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">tx applied on call</text>
</svg>

`@EnableTransactionManagement` registers three infrastructure beans that make `@Transactional` work.

## 5. Runnable example

Scenario: a **`NotificationService`** — first with `@EnableTransactionManagement` defaults, then with `proxyTargetClass=true` and `order` customization, then with `mode=ASPECTJ`.

### Level 1 — Basic

Standard `@EnableTransactionManagement` — enabling `@Transactional` in a non-Boot app.

```java
// EnableTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement      // activates @Transactional processing
@ComponentScan
public class EnableTMDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("notif-schema.sql").build();
    }

    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EnableTMDemo.class);
        ctx.getBean(NotificationService.class).send("user@example.com", "Welcome!");
        ctx.close();
    }
}

@Service
class NotificationService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    NotificationService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional
    public void send(String to, String msg) {
        jdbc.update("INSERT INTO notifications(to_addr, msg) VALUES(?,?)", to, msg);
        System.out.println("Notification sent to " + to);
    }
}
```

`notif-schema.sql`: `CREATE TABLE notifications (id BIGINT AUTO_INCREMENT PRIMARY KEY, to_addr VARCHAR(100), msg VARCHAR(255));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. EnableTMDemo.java`

Without `@EnableTransactionManagement` the `INSERT` runs but NOT in a transaction (no proxy). With it, the proxy intercepts `send()` and wraps it in a `DataSourceTransactionManager` transaction.

---

### Level 2 — Intermediate

`proxyTargetClass=true` (CGLIB) and `order` — controlling advisor ordering when security and transaction aspects overlap.

```java
// EnableTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.aop.framework.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;

@Configuration
@EnableTransactionManagement(
    proxyTargetClass = true,   // force CGLIB — inject by concrete type
    order = 5                  // tx advisor fires BEFORE security (order=10)
)
@EnableAspectJAutoProxy(proxyTargetClass = true)
@ComponentScan
public class EnableTMDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("notif-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EnableTMDemo.class);
        NotificationService svc = ctx.getBean(NotificationService.class);  // concrete type — works with CGLIB
        System.out.println("Proxy class: " + svc.getClass().getSimpleName());
        svc.send("cglib@example.com", "CGLIB works");
        ctx.close();
    }
}

@Service
class NotificationService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    NotificationService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional
    public void send(String to, String msg) {
        jdbc.update("INSERT INTO notifications(to_addr,msg) VALUES(?,?)", to, msg);
        System.out.println("Sent to " + to);
    }
}

@Aspect @org.springframework.stereotype.Component
@org.springframework.core.annotation.Order(10)    // fires after tx (order=5)
class SecurityAspect {
    @Before("execution(* NotificationService.send(..))")
    public void check(JoinPoint jp) {
        System.out.println("[SECURITY order=10] checking " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath + `spring-aop.jar:aspectjweaver.jar`

`order=5` on the transaction advisor means it fires at lower order number than the security aspect (`order=10`). Outer-to-inner: TX (5) wraps SECURITY (10) wraps target. The security check runs INSIDE the transaction. Print shows the order explicitly.

---

### Level 3 — Advanced

**TransactionManagementConfigurer** — implement it in `@Configuration` to programmatically select the `PlatformTransactionManager` instead of relying on bean name auto-detection.

```java
// EnableTMDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class EnableTMDemo implements TransactionManagementConfigurer {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("notif-schema.sql").build();
    }

    @Bean(name = "myCustomTM")          // NOT named "transactionManager"
    public PlatformTransactionManager myCustomTM(javax.sql.DataSource ds) {
        System.out.println("[CONFIG] creating custom TM");
        return new DataSourceTransactionManager(ds);
    }

    @Override
    public PlatformTransactionManager annotationDrivenTransactionManager() {
        // Spring calls this to resolve which TM to use for @Transactional
        return myCustomTM(dataSource());
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EnableTMDemo.class);
        ctx.getBean(NotificationService.class).send("custom-tm@example.com", "works");
        ctx.close();
    }
}

@Service
class NotificationService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    NotificationService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional       // uses the TM from annotationDrivenTransactionManager()
    public void send(String to, String msg) {
        jdbc.update("INSERT INTO notifications(to_addr,msg) VALUES(?,?)", to, msg);
        System.out.println("Sent (custom TM): " + to);
    }
}
```

How to run: same classpath

`TransactionManagementConfigurer.annotationDrivenTransactionManager()` is called once by `@EnableTransactionManagement`. The returned TM is used for all `@Transactional` annotations in the context. This avoids naming the bean `transactionManager` and is useful when you have multiple TMs and want explicit control over which one is the default.

## 6. Walkthrough

**Context startup with `@EnableTransactionManagement`:**

1. `@Configuration` class is processed.
2. `@EnableTransactionManagement` triggers import of `TransactionManagementConfigurationSelector`.
3. Selector returns `ProxyTransactionManagementConfiguration` (mode=PROXY default).
4. `ProxyTransactionManagementConfiguration` `@Bean` methods fire:
   - `AnnotationTransactionAttributeSource` bean created.
   - `TransactionInterceptor` bean created (references TM bean lazily).
   - `BeanFactoryTransactionAttributeSourceAdvisor` bean created (holds interceptor + pointcut).
5. The advisor has order `Ordered.LOWEST_PRECEDENCE` by default (overridden via `order=5` in Level 2).

**Bean post-processing:**

```
NotificationService raw bean created
  → BeanPostProcessor (InfrastructureAdvisorAutoProxyCreator) fires
    → finds BeanFactoryTxAttributeSourceAdvisor
    → checks: does NotificationService have @Transactional methods? YES
    → wraps NotificationService in CGLIB proxy (or JDK if interface + proxyTargetClass=false)
  → proxy registered in context as "notificationService"
```

**Per-call (Level 2 — order matters):**

```
svc.send("cglib@example.com","CGLIB works")
  → CGLIB proxy.send()
    → advisor chain (by order):
        order=5  TX advisor:  getTransaction() → conn acquired
        order=10 Security:   [SECURITY] checking send()
    → NotificationService.send() executes
    → TX advisor:  commit()
```

Lower order number = outer wrapper (runs first on entry, last on exit).

## 7. Gotchas & takeaways

> **Spring Boot applies `@EnableTransactionManagement` automatically** via `TransactionAutoConfiguration` when a `PlatformTransactionManager` bean exists. Adding it again in your `@SpringBootApplication` class is harmless but redundant.

> **`order` on `@EnableTransactionManagement` sets the transaction advisor's position, not individual `@Transactional` methods.** If you want the transaction to wrap inside an outer security check, set `order` on `@EnableTransactionManagement` to a higher number than the security aspect.

> **`mode=ASPECTJ` requires AspectJ weaving configuration.** Setting `mode=ASPECTJ` without `-javaagent:aspectjweaver.jar` or compile-time weaving results in no transaction interception (no error, silent failure).

- `@EnableTransactionManagement` must appear in exactly one `@Configuration` class per application context.
- `proxyTargetClass=true` on `@EnableTransactionManagement` does the same thing as `@EnableAspectJAutoProxy(proxyTargetClass=true)` — forces CGLIB globally.
- Implement `TransactionManagementConfigurer` on your `@Configuration` class for explicit TM selection when the default bean-name detection (`"transactionManager"`) is insufficient.
- `order=Ordered.LOWEST_PRECEDENCE` (default) means the transaction aspect is the innermost wrapper — it fires LAST going in and FIRST coming out. Set a lower number to make it outermost.
