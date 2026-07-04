---
card: spring-framework
gi: 284
slug: jpadialect
title: JpaDialect
---

## 1. What it is

`JpaDialect` is a Spring SPI that abstracts **JPA provider-specific transaction and exception behavior** so that `JpaTransactionManager` and `AbstractEntityManagerFactoryBean` can work uniformly across Hibernate, EclipseLink, and other providers.

```java
public interface JpaDialect extends PersistenceExceptionTranslator {
    Object beginTransaction(EntityManager em, TransactionDefinition def)
        throws PersistenceException, SQLException, TransactionException;
    void cleanupTransaction(@Nullable Object transactionData);
    @Nullable ConnectionHandle getJdbcConnection(EntityManager em, boolean readOnly)
        throws PersistenceException, SQLException;
    void releaseJdbcConnection(ConnectionHandle con, EntityManager em)
        throws PersistenceException, SQLException;
    DataAccessException translateExceptionIfPossible(RuntimeException ex);
}
```

Spring ships two concrete implementations:
- **`DefaultJpaDialect`** — uses standard JPA APIs only; limited TX customisation.
- **`HibernateJpaDialect`** — contributed automatically by `HibernateJpaVendorAdapter`; unlocks Hibernate-specific transaction options (isolation level, flush mode, timeout).

## 2. Why & when

Standard JPA has no API for setting the transaction isolation level — it delegates that to the underlying JDBC connection. Without a dialect, `JpaTransactionManager` cannot honor `@Transactional(isolation = READ_COMMITTED)` — it would silently ignore the isolation attribute.

`HibernateJpaDialect` solves this by:
1. Calling `Session.connection()` (Hibernate API) to get the underlying JDBC `Connection`.
2. Setting `connection.setTransactionIsolation(...)` before the transaction begins.
3. Resetting it afterwards (`cleanupTransaction`).

In practice you rarely configure `JpaDialect` directly — `HibernateJpaVendorAdapter` installs `HibernateJpaDialect` automatically. You only interact with it when:
- You need custom exception translation.
- You must control flush-mode per-TX.
- You implement a custom JPA provider bridge.

## 3. Core concept

`JpaTransactionManager` delegates provider-specific behaviour to the dialect:

```
@Transactional(isolation=REPEATABLE_READ) method call
  ↓
JpaTransactionManager.doBegin()
  ↓
jpaDialect.beginTransaction(em, txDef)
  HibernateJpaDialect:
    connection = em.unwrap(Session.class).connection()
    connection.setTransactionIsolation(TRANSACTION_REPEATABLE_READ)
    em.getTransaction().begin()
    return TransactionData(previousIsolation, connection)
  ↓
method body runs …
  ↓
JpaTransactionManager.doCommit()
  em.flush() + em.getTransaction().commit()
  ↓
jpaDialect.cleanupTransaction(transactionData)
  HibernateJpaDialect:
    connection.setTransactionIsolation(previousIsolation)  // restore
```

Exception translation chain:
```
HibernateJpaDialect.translateExceptionIfPossible(ex)
  → tries Hibernate-specific mapping (ConstraintViolationException → DataIntegrityViolationException)
  → falls back to standard JPA mapping
  → returns DataAccessException subclass (or null if not translatable)
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- JpaTransactionManager -->
  <rect x="10" y="70" width="190" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JpaTransactionManager</text>
  <line x1="20" y1="98" x2="190" y2="98" stroke="#8b949e" stroke-width="0.5"/>
  <text x="105" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">delegates to JpaDialect</text>

  <line x1="202" y1="100" x2="245" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- JpaDialect (interface) -->
  <rect x="247" y="55" width="175" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="334" y="78" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">«interface» JpaDialect</text>
  <line x1="257" y1="84" x2="412" y2="84" stroke="#8b949e" stroke-width="0.5"/>
  <text x="334" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">beginTransaction()</text>
  <text x="334" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">cleanupTransaction()</text>
  <text x="334" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">getJdbcConnection()</text>

  <!-- HibernateJpaDialect -->
  <line x1="424" y1="80" x2="469" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="424" y1="120" x2="469" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="471" y="40" width="205" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="573" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">HibernateJpaDialect</text>
  <text x="573" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">sets isolation, flush mode, timeout</text>

  <rect x="471" y="110" width="205" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="573" y="130" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">DefaultJpaDialect</text>
  <text x="573" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">standard JPA only (no isolation)</text>
</svg>

## 5. Runnable example

Scenario: a **bank account service** — observe how `JpaDialect` enables isolation-level honoring and exception translation.

### Level 1 — Basic

Default `HibernateJpaDialect` auto-installed; observe exception translation.

```java
// JpaDialectDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name="accounts", uniqueConstraints=@UniqueConstraint(columnNames="acct_num"))
class Account {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    @Column(name="acct_num") String acctNum; double balance;
    public Account(){} public Account(String n, double b){acctNum=n;balance=b;}
    public Long getId(){return id;} public String getAcctNum(){return acctNum;}
    public double getBalance(){return balance;}
    public String toString(){return "Account["+acctNum+","+balance+"]";}
}

@Repository
class AccountRepo {
    @PersistenceContext EntityManager em;

    @Transactional
    public void save(Account a){ em.persist(a); }

    @Transactional(readOnly=true)
    public Optional<Account> findByAcctNum(String num){
        List<Account> r = em.createQuery("FROM Account WHERE acctNum=:n", Account.class)
            .setParameter("n",num).getResultList();
        return r.isEmpty() ? Optional.empty() : Optional.of(r.get(0));
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:bank;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        var adapter=new HibernateJpaVendorAdapter(); adapter.setGenerateDdl(true);
        emf.setJpaVendorAdapter(adapter); return emf;
        // HibernateJpaVendorAdapter installs HibernateJpaDialect automatically
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){ return new JpaTransactionManager(emf); }
}

public class JpaDialectDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        AccountRepo repo = ctx.getBean(AccountRepo.class);

        repo.save(new Account("ACC-001", 1000.00));

        // HibernateJpaDialect translates ConstraintViolationException → DataIntegrityViolationException
        try {
            repo.save(new Account("ACC-001", 500.00));  // duplicate acct_num
        } catch (DataIntegrityViolationException e) {
            System.out.println("Caught Spring exception (translated by HibernateJpaDialect): "
                + e.getClass().getSimpleName());
        }

        System.out.println("Found: " + repo.findByAcctNum("ACC-001"));
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. JpaDialectDemo.java`

`HibernateJpaVendorAdapter` automatically sets `jpaTransactionManager.setJpaDialect(new HibernateJpaDialect())`. The dialect's `translateExceptionIfPossible()` converts Hibernate's `ConstraintViolationException` to Spring's `DataIntegrityViolationException`.

---

### Level 2 — Intermediate

`@Transactional(isolation=...)` honored by `HibernateJpaDialect`.

```java
// JpaDialectDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Service;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (Account entity and AppCfg same as Level 1)

@Service
class TransferService {
    @PersistenceContext EntityManager em;

    @Transactional(isolation = Isolation.READ_COMMITTED)
    // HibernateJpaDialect calls connection.setTransactionIsolation(READ_COMMITTED)
    public void transfer(String fromAcct, String toAcct, double amount) {
        Account from = em.createQuery("FROM Account WHERE acctNum=:n", Account.class)
            .setParameter("n", fromAcct).getSingleResult();
        Account to = em.createQuery("FROM Account WHERE acctNum=:n", Account.class)
            .setParameter("n", toAcct).getSingleResult();

        if (from.getBalance() < amount)
            throw new IllegalArgumentException("Insufficient funds");

        // direct field update — JPA dirty check picks it up
        // (normally use setters; inline for demo clarity)
        em.createQuery("UPDATE Account SET balance=balance-:amt WHERE acctNum=:n")
            .setParameter("amt", amount).setParameter("n", fromAcct).executeUpdate();
        em.createQuery("UPDATE Account SET balance=balance+:amt WHERE acctNum=:n")
            .setParameter("amt", amount).setParameter("n", toAcct).executeUpdate();

        System.out.printf("Transferred %.2f from %s to %s%n", amount, fromAcct, toAcct);
    }

    @Transactional(readOnly = true)
    public double getBalance(String acctNum) {
        return em.createQuery("SELECT a.balance FROM Account a WHERE a.acctNum=:n", Double.class)
            .setParameter("n", acctNum).getSingleResult();
    }
}

public class JpaDialectDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        var repo = ctx.getBean(AccountRepo.class);
        var svc = ctx.getBean(TransferService.class);

        repo.save(new Account("ACC-001", 1000.00));
        repo.save(new Account("ACC-002",  500.00));

        svc.transfer("ACC-001", "ACC-002", 200.00);
        System.out.printf("ACC-001 balance: %.2f%n", svc.getBalance("ACC-001"));
        System.out.printf("ACC-002 balance: %.2f%n", svc.getBalance("ACC-002"));

        // rollback case
        try {
            svc.transfer("ACC-001", "ACC-002", 99999.00);  // throws → rolled back
        } catch (IllegalArgumentException e) {
            System.out.println("Transfer failed (rolled back): " + e.getMessage());
        }
        System.out.printf("ACC-001 after failed transfer: %.2f%n", svc.getBalance("ACC-001"));
        ctx.close();
    }
}
```

How to run: same classpath

`HibernateJpaDialect.beginTransaction()` calls `Session.doWork(conn -> conn.setTransactionIsolation(READ_COMMITTED))` then `em.getTransaction().begin()`. Without `HibernateJpaDialect`, `JpaTransactionManager` would ignore the isolation attribute — `DefaultJpaDialect` has no JDBC access.

---

### Level 3 — Advanced

Custom `JpaDialect` that adds request-level savepoint support.

```java
// JpaDialectDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.hibernate5.HibernateJpaDialect;  // use hibernate dialect as base
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.sql.Connection;

// (Account entity same as Level 1)

// Custom dialect — logs every begin/cleanup for auditing
class AuditingJpaDialect extends HibernateJpaDialect {
    @Override
    public Object beginTransaction(EntityManager em, TransactionDefinition def)
            throws Exception {
        System.out.println("[AUDIT] TX begin — isolation=" + def.getIsolationLevel()
            + " readOnly=" + def.isReadOnly());
        Object data = super.beginTransaction(em, def);
        System.out.println("[AUDIT] TX started successfully");
        return data;
    }

    @Override
    public void cleanupTransaction(Object txData) {
        System.out.println("[AUDIT] TX cleanup");
        super.cleanupTransaction(txData);
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfgCustom {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:bankadv;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        var adapter=new HibernateJpaVendorAdapter(); adapter.setGenerateDdl(true);
        emf.setJpaVendorAdapter(adapter); return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){
        var jtm = new JpaTransactionManager(emf);
        jtm.setJpaDialect(new AuditingJpaDialect());  // install custom dialect
        return jtm;
    }
}

public class JpaDialectDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfgCustom.class);
        var repo = ctx.getBean(AccountRepo.class);

        repo.save(new Account("ACC-001", 1000.00));
        System.out.println("Done. Custom dialect logged each TX lifecycle event.");
        ctx.close();
    }
}
```

How to run: same classpath

`JpaTransactionManager.setJpaDialect(new AuditingJpaDialect())` installs the custom dialect. Every `@Transactional` method now triggers `AuditingJpaDialect.beginTransaction()` and `cleanupTransaction()`. Extending `HibernateJpaDialect` rather than `DefaultJpaDialect` preserves the isolation-level and exception-translation logic from Hibernate.

## 6. Walkthrough

**Level 2 — `transfer()` with `isolation=READ_COMMITTED`:**

1. AOP proxy intercepts `transfer()` → `JpaTransactionManager.doBegin(txDef)`.
2. `txDef.getIsolationLevel()` → `READ_COMMITTED (2)`.
3. `HibernateJpaDialect.beginTransaction(em, txDef)`:
   - `em.unwrap(Session.class).doWork(conn -> { prev = conn.getTransactionIsolation(); conn.setTransactionIsolation(TRANSACTION_READ_COMMITTED); })`.
   - `em.getTransaction().begin()` → JDBC TX begins with correct isolation.
   - Returns `TransactionData(prevIsolation, conn)`.
4. `TransactionSynchronizationManager.bindResource(emf, EntityManagerHolder)`.
5. Method body: JPQL UPDATE × 2 → routed to JDBC via Hibernate.
6. Normal return: `JpaTransactionManager.doCommit()` → `em.flush()` → `em.getTransaction().commit()`.
7. `HibernateJpaDialect.cleanupTransaction(txData)` → `conn.setTransactionIsolation(prevIsolation)` → isolation restored.

## 7. Gotchas & takeaways

> **`@Transactional(isolation=...)` is silently ignored with `DefaultJpaDialect`.** If `HibernateJpaVendorAdapter` is NOT used (e.g., you manually construct `LocalContainerEntityManagerFactoryBean` without setting a vendor adapter), `DefaultJpaDialect` is active and cannot set JDBC isolation — the annotation attribute is ignored with no warning.

> **Don't subclass `DefaultJpaDialect` for isolation support** — it has no JDBC connection access. Extend `HibernateJpaDialect` (or the equivalent for your provider) as the base.

> **`HibernateJpaDialect` is wired automatically** by `HibernateJpaVendorAdapter` — you do not need to set it explicitly unless you're customising it (as in Level 3).

- `JpaDialect` = SPI for provider-specific TX + exception behaviour.
- `HibernateJpaDialect` enables isolation-level honoring via JDBC connection access.
- `DefaultJpaDialect` is standard-JPA only — cannot honor `@Transactional(isolation=...)`.
- Exception translation flows through `JpaDialect.translateExceptionIfPossible()`.
- Customise by subclassing `HibernateJpaDialect` and overriding `beginTransaction` + `cleanupTransaction`.
