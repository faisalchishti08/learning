---
card: spring-framework
gi: 241
slug: declarative-transaction-management-transactional
title: Declarative transaction management (@Transactional)
---

## 1. What it is

**Declarative transaction management** means you declare *that* a method should run in a transaction — using `@Transactional` — without writing any transaction management code yourself. Spring's AOP infrastructure detects the annotation and wraps the bean in a proxy that calls `PlatformTransactionManager.getTransaction()` before the method and `commit()` or `rollback()` after.

```java
@Service
public class OrderService {
    @Transactional                           // declare intent
    public void placeOrder(Order order) {
        orderRepo.save(order);               // no tx code — Spring handles it
        inventoryRepo.deduct(order.items()); // same transaction, auto-committed
    }
}
```

The alternative, **programmatic transaction management**, requires explicit `getTransaction()`/`commit()`/`rollback()` calls and is only used when fine-grained control is needed.

## 2. Why & when

Declarative management separates business logic from transaction plumbing. The developer expresses the *what* (this method must be transactional) not the *how* (open connection, begin, commit, close). Benefits:

- No boilerplate try/catch/rollback.
- Consistent rollback rules across all methods.
- Transaction attributes (propagation, isolation, timeout) are visible at the method signature.
- Easy to change (add `timeout=10` in one place vs. changing a try/catch block).

Use `@Transactional` by default. Switch to programmatic only when you need mid-method control or conditional rollback logic that cannot be expressed through annotation attributes.

## 3. Core concept

`@Transactional` is processed by `TransactionInterceptor`, a Spring AOP `MethodInterceptor`. When `@EnableTransactionManagement` (or `<tx:annotation-driven/>`) is declared, Spring registers `BeanFactoryTransactionAttributeSourceAdvisor` which matches all beans with `@Transactional` methods and wraps them in proxies.

Call path:

```
caller → TransactionProxy.placeOrder()
  → TransactionInterceptor.invoke()
    → tm.getTransaction(txAttribute)
    → OrderService.placeOrder()   (real method)
    → exception? → tm.rollback()
    → normal?    → tm.commit()
```

Key rules:
- `@Transactional` on a **class** applies to all public methods.
- `@Transactional` on a **method** overrides the class-level setting.
- Method-level annotation is **not inherited** by overriding methods in subclasses — each override must carry its own `@Transactional`.
- Only **public** methods are intercepted by the default Spring proxy (CGLIB/JDK).

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="rarr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
  </defs>

  <!-- Caller -->
  <rect x="10" y="80" width="80" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="50" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <line x1="92" y1="100" x2="145" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- TransactionProxy -->
  <rect x="145" y="30" width="200" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="245" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">TransactionProxy</text>
  <line x1="155" y1="60" x2="335" y2="60" stroke="#8b949e" stroke-width="0.5"/>
  <text x="245" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">1. getTransaction()</text>
  <text x="245" y="93" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">→ target method →</text>
  <text x="245" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">2a. commit()     ← normal</text>
  <text x="245" y="128" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">2b. rollback()   ← exception</text>
  <text x="245" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TransactionInterceptor</text>
  <text x="245" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">+BeanFactoryTxAttributeSourceAdvisor</text>

  <line x1="347" y1="100" x2="400" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Service -->
  <rect x="400" y="55" width="180" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="78" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">@Service OrderService</text>
  <text x="490" y="96" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Transactional</text>
  <text x="490" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">placeOrder(order) {</text>
  <text x="490" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">  repo.save(order);</text>
  <text x="490" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">}</text>
</svg>

Spring wraps the `@Service` in a proxy. The proxy handles begin/commit/rollback around the real method.

## 5. Runnable example

Scenario: an **`AccountService`** that opens accounts and makes transfers — first with basic `@Transactional`, then with class-level defaults overridden per-method, then integrating rollback rules.

### Level 1 — Basic

`@Transactional` on a service method — automatic commit on success, rollback on unchecked exception.

```java
// DeclarativeTxDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class DeclarativeTxDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("accounts-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclarativeTxDemo.class);
        AccountService svc = ctx.getBean(AccountService.class);
        svc.openAccount("ACC-100", 1000.0);

        try {
            svc.transfer("ACC-100", "ACC-MISSING", 200.0);   // fails — ACC-MISSING not found
        } catch (Exception e) {
            System.out.println("Transfer rolled back: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class AccountService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AccountService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    @Transactional                                     // begin, commit on return
    public void openAccount(String id, double balance) {
        jdbc.update("INSERT INTO accounts(id,balance) VALUES(?,?)", id, balance);
        System.out.println("Account opened: " + id);
    }

    @Transactional                                     // begin, rollback on RuntimeException
    public void transfer(String fromId, String toId, double amount) {
        Integer from = jdbc.queryForObject("SELECT id FROM accounts WHERE id=?",
                                            Integer.class, fromId);
        Integer to   = jdbc.queryForObject("SELECT id FROM accounts WHERE id=?",
                                            Integer.class, toId);   // throws EmptyResultDataAccessException
        jdbc.update("UPDATE accounts SET balance=balance-? WHERE id=?", amount, fromId);
        jdbc.update("UPDATE accounts SET balance=balance+? WHERE id=?", amount, toId);
    }
}
```

`accounts-schema.sql`: `CREATE TABLE accounts (id VARCHAR(20) PRIMARY KEY, balance DECIMAL(10,2));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. DeclarativeTxDemo.java`

`transfer()` throws `EmptyResultDataAccessException` (unchecked). Spring's proxy catches it and calls `rollback()`. The debit UPDATE was never reached. `openAccount()` is in its own prior transaction that already committed.

---

### Level 2 — Intermediate

Class-level `@Transactional` with method-level overrides — read-only reporting method in the same class.

```java
// DeclarativeTxDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class DeclarativeTxDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("accounts-schema.sql").build();
    }
    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) { return new DataSourceTransactionManager(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclarativeTxDemo.class);
        AccountService svc = ctx.getBean(AccountService.class);
        svc.openAccount("ACC-200", 5000.0);
        svc.openAccount("ACC-201", 3000.0);
        svc.transfer("ACC-200", "ACC-201", 1000.0);

        List<String> report = svc.listAccounts();
        System.out.println("Accounts: " + report);
        ctx.close();
    }
}

@Transactional               // default for all methods: REQUIRED, READ_COMMITTED
@Service
class AccountService {
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;
    AccountService(javax.sql.DataSource ds) { this.jdbc = new org.springframework.jdbc.core.JdbcTemplate(ds); }

    public void openAccount(String id, double balance) {
        jdbc.update("INSERT INTO accounts(id,balance) VALUES(?,?)", id, balance);
        System.out.println("Account opened: " + id + " balance=" + balance);
    }

    public void transfer(String fromId, String toId, double amount) {
        jdbc.update("UPDATE accounts SET balance=balance-? WHERE id=?", amount, fromId);
        jdbc.update("UPDATE accounts SET balance=balance+? WHERE id=?", amount, toId);
        System.out.printf("Transferred $%.2f from %s to %s%n", amount, fromId, toId);
    }

    @Transactional(readOnly = true)   // overrides class default for this method
    public List<String> listAccounts() {
        return jdbc.queryForList("SELECT id||': $'||balance FROM accounts", String.class);
    }
}
```

How to run: same classpath

`@Transactional` on the class applies `REQUIRED` + read-write to all public methods. `listAccounts()` overrides with `readOnly=true`. The proxy picks up the most specific annotation (method wins over class).

---

### Level 3 — Advanced

Integrating `@Transactional` with Spring Data JPA — showing how the proxy chain composes with JPA's own session management.

```java
// DeclarativeTxDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.orm.jpa.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import jakarta.persistence.*;
import java.util.*;

@Configuration
@EnableTransactionManagement
@ComponentScan
public class DeclarativeTxDemo {
    @Bean public javax.sql.DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2).build();
    }

    @Bean public LocalContainerEntityManagerFactoryBean emf(javax.sql.DataSource ds) {
        var emf = new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(ds);
        emf.setPackagesToScan("com.example");
        var adapter = new org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter();
        adapter.setGenerateDdl(true);
        emf.setJpaVendorAdapter(adapter);
        var p = new java.util.Properties();
        p.put("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
        emf.setJpaProperties(p);
        return emf;
    }

    @Bean public org.springframework.transaction.PlatformTransactionManager transactionManager(
            EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclarativeTxDemo.class);
        var svc = ctx.getBean(AccountService.class);
        svc.openAccount("JPA-300", 2000.0);
        svc.transfer("JPA-300", "JPA-301", 500.0);   // JPA-301 does not exist — rollback
        ctx.close();
    }
}

@Entity @Table(name="accounts")
class Account {
    @Id String id;
    double balance;
    Account() {} Account(String id, double balance) { this.id=id; this.balance=balance; }
    @Override public String toString() { return id+"=$"+balance; }
}

@Service
@Transactional
class AccountService {
    @PersistenceContext EntityManager em;

    public void openAccount(String id, double balance) {
        em.persist(new Account(id, balance));
        System.out.println("JPA: opened " + id);
    }

    public void transfer(String fromId, String toId, double amount) {
        Account from = em.find(Account.class, fromId);
        Account to   = em.find(Account.class, toId);
        if (to == null) throw new IllegalArgumentException("Account not found: " + toId);
        from.balance -= amount;
        to.balance   += amount;
        System.out.printf("JPA: transferred $%.2f from %s to %s%n", amount, fromId, toId);
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. DeclarativeTxDemo.java`

`JpaTransactionManager` binds an `EntityManager` to the thread. `@PersistenceContext EntityManager em` receives the thread-bound EM. Dirty-checking: changes to `from.balance` are automatically flushed at commit. The `throw` causes the proxy to call `rollback()` — neither account balance change is persisted.

## 6. Walkthrough

**Level 1 — `openAccount` success path:**

```
caller → proxy.openAccount("ACC-100", 1000.0)
  → TransactionInterceptor.invoke()
    → txManager.getTransaction(REQUIRED)
       conn acquired; autoCommit=false
    → AccountService.openAccount("ACC-100", 1000.0)
       INSERT accounts ('ACC-100', 1000.0)   [on thread-bound conn]
       System.out "Account opened: ACC-100"
    → no exception
    → txManager.commit()
       conn.commit()
       conn returned to pool
```

**Level 1 — `transfer` rollback path:**

```
caller → proxy.transfer("ACC-100","ACC-MISSING",200.0)
  → TransactionInterceptor.invoke()
    → txManager.getTransaction(REQUIRED)   conn acquired; autoCommit=false
    → AccountService.transfer(...)
       SELECT id ... where id='ACC-100' → 1 row (OK)
       SELECT id ... where id='ACC-MISSING' → 0 rows → throws EmptyResultDataAccessException
    → TransactionInterceptor catches RuntimeException
    → txManager.rollback()   conn.rollback(); conn released
  → exception re-thrown to caller
```

**State at each layer:**

```
Request:   transfer("ACC-100","ACC-MISSING",200.0)
  ↓ tx opened (autoCommit=false)
  ↓ SELECT ACC-100 → found
  ↓ SELECT ACC-MISSING → EmptyResultDataAccessException
  ↓ proxy catches → rollback()   (no UPDATEs were executed)
Response:  EmptyResultDataAccessException propagates to caller
```

## 7. Gotchas & takeaways

> **`@Transactional` only works on Spring-managed beans.** Calling a `@Transactional` method on an object you created with `new` bypasses the proxy — no transaction is created. Always get the bean from the Spring context.

> **Checked exceptions do NOT trigger rollback by default.** Only `RuntimeException` and `Error` trigger rollback. If your method throws `IOException`, the transaction commits even if you want a rollback. Use `@Transactional(rollbackFor = IOException.class)` to override this.

> **`@Transactional` on non-public methods is silently ignored by Spring's proxy AOP.** No warning, no error — the method runs without a transaction. Use AspectJ LTW if you need transaction support on package-private or protected methods.

- Declare `@Transactional` at the service layer, not on JPA repositories (repositories already manage their own transactions).
- Class-level `@Transactional` sets the default; method-level overrides for specific methods (e.g., `readOnly=true` on query methods).
- `@Transactional` annotations are NOT inherited by overriding methods in subclasses — each subclass override must re-declare `@Transactional`.
- The proxy can only intercept calls coming from outside the bean (self-invocation problem applies — see tutorial 0233).
