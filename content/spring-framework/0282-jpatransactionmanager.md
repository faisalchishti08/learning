---
card: spring-framework
gi: 282
slug: jpatransactionmanager
title: JpaTransactionManager
---

## 1. What it is

`JpaTransactionManager` is Spring's `PlatformTransactionManager` implementation for **JPA-backed transactions**. It binds a JPA `EntityManager` to the current thread for the duration of a transaction, making `@Transactional` work with JPA repositories and `EntityManager` injection.

```java
@Bean
JpaTransactionManager transactionManager(EntityManagerFactory emf) {
    return new JpaTransactionManager(emf);
}
```

With this bean in place, `@Transactional` methods get a full JPA context: `EntityManager` creation, flush, and commit/rollback are all managed automatically.

```java
@Service
class OrderService {
    @PersistenceContext EntityManager em;

    @Transactional         // JpaTransactionManager drives this
    public Order placeOrder(Order order) {
        em.persist(order); // flushed + committed by JpaTransactionManager
        return order;
    }
}
```

## 2. Why & when

`DataSourceTransactionManager` manages JDBC connections directly. It knows nothing about JPA flushing, entity state, or the persistence context lifecycle. If you use JPA and configure a `DataSourceTransactionManager` instead, `em.persist()` calls won't be flushed at commit time.

`JpaTransactionManager` bridges JPA and Spring's TX abstraction:
- Creates a real `EntityManager` at the start of each transaction.
- Binds it to the thread-local registry so `@PersistenceContext` proxy calls route to it.
- Flushes the persistence context before commit.
- Rolls back by discarding the `EntityManager` without flushing.
- Interoperates with JDBC (`DataSourceUtils`) via the underlying `DataSource` — JDBC code in the same transaction participates through the same connection.

Use `JpaTransactionManager` whenever you use Spring + JPA without JTA. For multi-database XA transactions, use a JTA `JtaTransactionManager` instead.

## 3. Core concept

`JpaTransactionManager` implements `ResourceTransactionManager`, meaning it both manages transactions AND owns the transactional resource (the `EntityManager`). Here's what happens during a `@Transactional` method call:

```
Transaction begin:
  emf.createEntityManager()           → real EM created
  em.getTransaction().begin()         → JDBC connection obtained, TX started
  TransactionSynchronizationManager
    .bindResource(emf, emHolder)      → EM stored in thread-local

During method:
  em.persist(entity)                  → entity enqueued in persistence context
  em.find(...)                        → SELECT (may go to DB or 1st-level cache)

Transaction commit (no exception):
  em.flush()                          → INSERT/UPDATE/DELETE sent to DB
  em.getTransaction().commit()        → JDBC COMMIT
  em.close()                          → connection released

Transaction rollback (exception):
  em.getTransaction().rollback()      → JDBC ROLLBACK (flush NOT called)
  em.close()
```

JDBC interop: `JpaTransactionManager` can expose the same JDBC `Connection` used by the `EntityManager` so that JDBC templates (`JdbcTemplate`, `NamedParameterJdbcTemplate`) running in the same transaction join the same physical connection and commit together.

```java
@Bean
JpaTransactionManager transactionManager(EntityManagerFactory emf, DataSource ds) {
    JpaTransactionManager jtm = new JpaTransactionManager(emf);
    jtm.setDataSource(ds);  // enables JDBC participation in JPA transaction
    return jtm;
}
```

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- @Transactional -->
  <rect x="10" y="85" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="70" y="107" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional</text>
  <text x="70" y="123" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">AOP proxy</text>

  <line x1="132" y1="110" x2="175" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- JpaTransactionManager -->
  <rect x="177" y="65" width="185" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="269" y="88" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JpaTransactionManager</text>
  <line x1="187" y1="94" x2="352" y2="94" stroke="#8b949e" stroke-width="0.5"/>
  <text x="269" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">emf.createEntityManager()</text>
  <text x="269" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">em.flush() + commit</text>
  <text x="269" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">em.rollback + close</text>

  <line x1="364" y1="95" x2="407" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="364" y1="125" x2="407" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- EntityManager -->
  <rect x="409" y="65" width="145" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="481" y="88" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">EntityManager</text>
  <text x="481" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">thread-local (TxSync)</text>

  <!-- JDBC Connection -->
  <rect x="409" y="130" width="145" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="481" y="148" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JDBC Connection</text>
  <text x="481" y="162" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">DataSource (shared)</text>

  <line x1="481" y1="120" x2="481" y2="128" stroke="#8b949e" stroke-width="1"/>

  <!-- Legend -->
  <text x="10" y="200" fill="#8b949e" font-size="8" font-family="sans-serif">Both EM + Connection bound to same TX thread-local — JDBC code in same TX participates via same connection</text>
</svg>

## 5. Runnable example

Scenario: a **library booking system** — `JpaTransactionManager` drives `@Transactional` on a service with JPA + JDBC interop.

### Level 1 — Basic

`JpaTransactionManager` with a simple service.

```java
// JpaTxManagerDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name="books")
class Book {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String title; boolean available;
    public Book(){} public Book(String t, boolean a){title=t;available=a;}
    public Long getId(){return id;} public String getTitle(){return title;}
    public boolean isAvailable(){return available;} public void setAvailable(boolean a){available=a;}
    public String toString(){return "Book["+id+","+title+","+(available?"avail":"booked")+"]";}
}

@Service
class LibraryService {
    @PersistenceContext EntityManager em;

    @Transactional      // JpaTransactionManager: begin → flush → commit
    public Book addBook(String title) {
        Book b = new Book(title, true);
        em.persist(b);
        return b;
    }

    @Transactional      // separate TX for each checkout
    public void checkout(Long bookId, String borrower) {
        Book b = em.find(Book.class, bookId);
        if (b == null) throw new RuntimeException("Book not found: " + bookId);
        if (!b.isAvailable()) throw new IllegalStateException("Already booked: " + bookId);
        b.setAvailable(false);  // dirty check → UPDATE at flush
        System.out.println(borrower + " checked out: " + b.getTitle());
    }

    @Transactional(readOnly = true)     // flush mode NEVER — no accidental writes
    public List<Book> findAvailable() {
        return em.createQuery("FROM Book WHERE available=true", Book.class).getResultList();
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:lib;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf){ return new JpaTransactionManager(emf); }
}

public class JpaTxManagerDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        LibraryService svc = ctx.getBean(LibraryService.class);

        Book b1 = svc.addBook("Clean Code");
        Book b2 = svc.addBook("Effective Java");
        svc.checkout(b1.getId(), "Alice");

        System.out.println("Available: " + svc.findAvailable());
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. JpaTxManagerDemo.java`

`JpaTransactionManager` creates a new `EntityManager` for each `@Transactional` method, binds it to the thread, flushes and commits on success, rolls back on unchecked exception.

---

### Level 2 — Intermediate

Rollback on business exception + verifying TX isolation.

```java
// JpaTxManagerDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (Book entity and AppCfg same as Level 1)

class BookUnavailableException extends RuntimeException {
    BookUnavailableException(String msg){ super(msg); }
}

@Service
class LibraryService2 {
    @PersistenceContext EntityManager em;

    @Transactional
    public Book addBook(String title) {
        Book b=new Book(title,true); em.persist(b); return b;
    }

    // TRANSACTION A: checkout + mark unavailable — atomic
    @Transactional(rollbackFor = BookUnavailableException.class)
    public void checkout(Long bookId, String borrower) {
        Book b = em.find(Book.class, bookId);
        if (!b.isAvailable()) {
            // exception thrown BEFORE flush → JpaTransactionManager rolls back
            throw new BookUnavailableException(b.getTitle() + " is not available");
        }
        b.setAvailable(false);
        System.out.println(borrower + " checked out: " + b.getTitle());
        // flush + commit happens here
    }

    // TRANSACTION B: return book — own TX
    @Transactional
    public void returnBook(Long bookId) {
        Book b = em.find(Book.class, bookId);
        if (b != null) { b.setAvailable(true); System.out.println("Returned: " + b.getTitle()); }
    }

    @Transactional(readOnly = true)
    public List<Book> findAll() {
        return em.createQuery("FROM Book ORDER BY id", Book.class).getResultList();
    }
}

public class JpaTxManagerDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        LibraryService2 svc = ctx.getBean(LibraryService2.class);

        Book b1 = svc.addBook("Clean Code");
        svc.checkout(b1.getId(), "Alice");
        System.out.println("After checkout: " + svc.findAll());

        // Alice checks out again — should rollback
        try {
            svc.checkout(b1.getId(), "Bob");
        } catch (BookUnavailableException e) {
            System.out.println("Caught (expected rollback): " + e.getMessage());
        }

        // book still unavailable — rollback preserved DB state
        System.out.println("After failed checkout: " + svc.findAll());

        svc.returnBook(b1.getId());
        System.out.println("After return: " + svc.findAll());

        ctx.close();
    }
}
```

How to run: same classpath

Rollback on unchecked exception (`RuntimeException`) is automatic. `rollbackFor` is needed for checked exceptions. When `JpaTransactionManager` rolls back, `em.flush()` is never called — the dirty entity state is simply discarded.

---

### Level 3 — Advanced

JPA + JDBC in the same transaction via `setDataSource()`.

```java
// JpaTxManagerDemo.java
import jakarta.persistence.*;
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.orm.jpa.*;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.*;
import javax.sql.DataSource;
import java.util.*;

// (Book entity same as Level 1)

@Service
class LibraryService3 {
    @PersistenceContext EntityManager em;
    private final JdbcTemplate jdbc;
    LibraryService3(DataSource ds){ this.jdbc = new JdbcTemplate(ds); }

    @Transactional          // JPA + JDBC share the same connection + TX
    public void checkoutWithAudit(Long bookId, String borrower) {
        Book b = em.find(Book.class, bookId);
        if (b == null || !b.isAvailable())
            throw new RuntimeException("Cannot checkout book " + bookId);

        b.setAvailable(false);  // JPA dirty check → UPDATE
        em.flush();             // force flush before JDBC audit insert

        // JDBC participates in the same TX — same Connection from DataSourceUtils
        jdbc.update("INSERT INTO audit_log(book_id, action, borrower) VALUES(?,?,?)",
            bookId, "CHECKOUT", borrower);

        System.out.println(borrower + " checked out: " + b.getTitle());
        // TX commit → both JPA UPDATE + JDBC INSERT committed atomically
    }
}

@Configuration @EnableTransactionManagement @ComponentScan
class AppCfg3 {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver");
        d.setUrl("jdbc:h2:mem:lib3;DB_CLOSE_DELAY=-1;INIT=CREATE TABLE IF NOT EXISTS audit_log(id BIGINT AUTO_INCREMENT,book_id BIGINT,action VARCHAR,borrower VARCHAR)");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalContainerEntityManagerFactoryBean emf(DataSource ds){
        var emf=new LocalContainerEntityManagerFactoryBean(); emf.setDataSource(ds); emf.setPackagesToScan("");
        emf.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties p=new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); emf.setJpaProperties(p); return emf;
    }
    @Bean JpaTransactionManager transactionManager(EntityManagerFactory emf, DataSource ds){
        JpaTransactionManager jtm = new JpaTransactionManager(emf);
        jtm.setDataSource(ds);  // expose same Connection to JDBC code
        return jtm;
    }
}

public class JpaTxManagerDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg3.class);
        var jpa = ctx.getBean(LibraryService3.class);
        var ds = ctx.getBean(DataSource.class);
        var jdbc = new JdbcTemplate(ds);

        // add a book via JPA
        var svc = new org.springframework.orm.jpa.JpaTransactionManager();
        var emfBean = ctx.getBean(EntityManagerFactory.class);
        var em = emfBean.createEntityManager();
        em.getTransaction().begin();
        Book b = new Book("Clean Code", true); em.persist(b);
        em.getTransaction().commit(); Long bookId = b.getId(); em.close();

        // checkout — JPA + JDBC in one TX
        jpa.checkoutWithAudit(bookId, "Alice");

        // verify JDBC audit log
        List<Map<String,Object>> rows = jdbc.queryForList("SELECT * FROM audit_log");
        System.out.println("Audit log: " + rows);
        ctx.close();
    }
}
```

How to run: same classpath

`jtm.setDataSource(ds)` tells `JpaTransactionManager` to expose the underlying `Connection` from the JPA TX to `DataSourceUtils`. When `JdbcTemplate` runs in the same thread and TX, it calls `DataSourceUtils.getConnection(ds)` and gets the SAME connection used by the `EntityManager` — both operations commit atomically.

## 6. Walkthrough

**Level 1 — Full TX lifecycle (method `addBook("Clean Code")`):**

1. **AOP proxy intercepts**: `LibraryService.addBook()` is called through a CGLIB/JDK proxy created by `@EnableTransactionManagement`.
2. **`JpaTransactionManager.getTransaction()`**: no existing TX in thread-local → begin new TX.
   - `emf.createEntityManager()` → new real EM (Hibernate Session).
   - `em.getTransaction().begin()` → acquires JDBC `Connection` from pool, issues `SET autocommit=false`.
   - Binds `EntityManagerHolder` to `TransactionSynchronizationManager` under key `emf`.
3. **Method runs**: `em.persist(b)` enqueues `Book` in the persistence context's first-level cache. No SQL yet.
4. **`JpaTransactionManager.commit()`**:
   - `em.flush()` → generates `INSERT INTO books (title, available) VALUES (?, ?)` → executes via JDBC.
   - `em.getTransaction().commit()` → JDBC COMMIT.
   - `em.close()` → connection released to pool.
   - Thread-local binding removed.
5. **Return**: proxy returns the persisted `Book` with ID assigned.

**Rollback path** (Level 2 — `checkout()` throws `BookUnavailableException`):

```
1. AOP interceptor sees RuntimeException thrown from method body
2. JpaTransactionManager.rollback()
   → em.getTransaction().rollback()    (JDBC ROLLBACK)
   → em.close()
   → thread-local cleared
3. Dirty entity (b.setAvailable(false) call) was NEVER flushed → DB unchanged
4. Exception propagates to caller
```

## 7. Gotchas & takeaways

> **`readOnly = true` sets flush mode to `NEVER`**, not just a hint. Hibernate will throw if you call `em.persist()` inside a read-only TX. It also allows the JDBC driver to use read-only routing (e.g., replica DB).

> **JDBC code without `setDataSource(ds)` does NOT participate in the JPA TX.** If you inject `JdbcTemplate` and do NOT call `jtm.setDataSource(ds)`, `JdbcTemplate` will obtain its own connection and commit independently — you lose atomicity between JPA and JDBC operations.

> **`em.flush()` is NOT called on rollback.** Dirty state set within a rolled-back TX is lost. This is correct behavior — don't try to "save partial state" after an exception.

> **For `@Transactional(propagation = REQUIRES_NEW)`: JpaTransactionManager suspends the current TX**, saves its `EntityManagerHolder`, creates a new EM + connection for the inner TX. After the inner TX commits/rolls back, the outer TX resumes.

- Configure: `@Bean JpaTransactionManager transactionManager(EntityManagerFactory emf)`.
- Add `jtm.setDataSource(ds)` to interop JPA + JDBC in the same TX.
- `readOnly = true` sets flush mode NEVER — prevents accidental writes.
- Rollback discards dirty state without flushing — DB unchanged.
- Use `JtaTransactionManager` for cross-database XA transactions; `JpaTransactionManager` is single-database only.
