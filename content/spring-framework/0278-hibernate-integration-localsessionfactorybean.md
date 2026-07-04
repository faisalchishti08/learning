---
card: spring-framework
gi: 278
slug: hibernate-integration-localsessionfactorybean
title: Hibernate integration (LocalSessionFactoryBean)
---

## 1. What it is

`LocalSessionFactoryBean` is Spring's factory bean that builds a Hibernate `SessionFactory` — the root of Hibernate's object graph. It wires Hibernate into a Spring `ApplicationContext`, combining a `DataSource`, entity scanning, and Hibernate properties in one declaration.

```java
@Bean
public LocalSessionFactoryBean sessionFactory(DataSource dataSource) {
    LocalSessionFactoryBean sf = new LocalSessionFactoryBean();
    sf.setDataSource(dataSource);
    sf.setPackagesToScan("com.example.domain");  // finds @Entity classes
    sf.setHibernateProperties(hibernateProps());
    return sf;
}
```

The resulting `SessionFactory` is a thread-safe singleton shared across the application. Individual `Session` instances — not the `SessionFactory` — are obtained per-transaction.

## 2. Why & when

Use `LocalSessionFactoryBean` (Hibernate-native) instead of JPA's `LocalContainerEntityManagerFactoryBean` when:
- You need **Hibernate-specific APIs** (criteria queries, `@Filter`, `@Type`, `@Formula`) not available in JPA.
- You are migrating a legacy Hibernate project to Spring without changing to JPA.
- You prefer Hibernate's `Session` API over JPA's `EntityManager` (they overlap significantly, but Session has more features).

For new projects, prefer the JPA path (`LocalContainerEntityManagerFactoryBean`) — it's the standard, and Spring Data JPA assumes JPA. Use the Hibernate path when Hibernate-specific features are needed.

## 3. Core concept

`LocalSessionFactoryBean` wraps Hibernate's `Configuration` class:

1. Sets the JDBC `DataSource` — Hibernate calls `dataSource.getConnection()` through Spring's `LocalDataSourceConnectionProvider`.
2. Scans `packagesToScan` for `@Entity`, `@Table`, `@MappedSuperclass` classes.
3. Applies `hibernateProperties` (dialect, DDL auto, show SQL, caching).
4. Calls `cfg.buildSessionFactory()` in `afterPropertiesSet()` — validates the schema against entities.

`HibernateTransactionManager` drives `@Transactional` for Hibernate-native (`Session`) code:

```
@Transactional method called:
  → HibernateTransactionManager.getTransaction()
  → sessionFactory.openSession()
  → session.beginTransaction()
  → bind session to thread-local

  → your code calls: session.get(…), session.persist(…), session.createQuery(…)
  → uses thread-bound session

  → TX commits → session.flush() → session.close()
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Spring config -->
  <rect x="10" y="60" width="175" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">LocalSessionFactoryBean</text>
  <line x1="20" y1="88" x2="175" y2="88" stroke="#8b949e" stroke-width="0.5"/>
  <text x="97" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setDataSource()</text>
  <text x="97" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setPackagesToScan()</text>
  <text x="97" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setHibernateProperties()</text>

  <line x1="187" y1="105" x2="230" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- SessionFactory -->
  <rect x="232" y="75" width="140" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="302" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SessionFactory</text>
  <text x="302" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">thread-safe singleton</text>

  <line x1="374" y1="105" x2="417" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Session per TX -->
  <rect x="419" y="65" width="140" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="489" y="88" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Session (per TX)</text>
  <line x1="429" y1="94" x2="549" y2="94" stroke="#8b949e" stroke-width="0.5"/>
  <text x="489" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">session.get/persist</text>
  <text x="489" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">session.createQuery</text>
  <text x="489" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">dirty check + flush</text>

  <line x1="561" y1="105" x2="604" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DB -->
  <rect x="606" y="80" width="85" height="50" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="648" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DB</text>
</svg>

`LocalSessionFactoryBean` produces the `SessionFactory`. `HibernateTransactionManager` opens one `Session` per `@Transactional` method and binds it to the thread.

## 5. Runnable example

Scenario: an **employee directory** — configure `LocalSessionFactoryBean`, use the Hibernate `Session` API, and demonstrate HQL (Hibernate Query Language) queries.

### Level 1 — Basic

`LocalSessionFactoryBean` configuration + `Session.persist()` and `Session.get()`.

```java
// HibernateDemo.java
import jakarta.persistence.*;
import org.hibernate.SessionFactory;
import org.springframework.context.annotation.*;
import org.springframework.orm.hibernate5.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@Entity @Table(name = "employees")
class Employee {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) Long id;
    String name; String dept; int salary;
    public Employee(){}
    public Employee(String n, String d, int s){name=n; dept=d; salary=s;}
    public Long getId(){return id;} public String getName(){return name;}
    public String getDept(){return dept;} public int getSalary(){return salary;}
    public String toString(){return "Employee["+id+","+name+","+dept+","+salary+"]";}
}

@Configuration @EnableTransactionManagement
class HibCfg {
    @Bean DataSource ds(){
        var d = new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:hr;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalSessionFactoryBean sessionFactory(DataSource ds) {
        var sf = new LocalSessionFactoryBean();
        sf.setDataSource(ds);
        sf.setPackagesToScan("");  // scan default package for @Entity
        Properties p = new Properties();
        p.setProperty("hibernate.hbm2ddl.auto", "create-drop");
        p.setProperty("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
        p.setProperty("hibernate.show_sql", "false");
        sf.setHibernateProperties(p);
        return sf;
    }
    @Bean HibernateTransactionManager tx(SessionFactory sf) {
        return new HibernateTransactionManager(sf);
    }
}

public class HibernateDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(HibCfg.class);
        SessionFactory sf = ctx.getBean(SessionFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // Insert employees
        tx.execute(s -> {
            var session = sf.getCurrentSession();
            session.persist(new Employee("Alice","Engineering",95000));
            session.persist(new Employee("Bob","Engineering",88000));
            session.persist(new Employee("Carol","Marketing",72000));
            return null;
        });

        // Load by primary key
        tx.execute(s -> {
            var session = sf.getCurrentSession();
            Employee alice = session.get(Employee.class, 1L);
            System.out.println("Found: " + alice);
            return null;
        });

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-orm.jar:spring-tx.jar:spring-jdbc.jar:hibernate-core.jar:jakarta.persistence-api.jar:h2.jar:. HibernateDemo.java`

`sf.getCurrentSession()` returns the `Session` bound to the current transaction — safe to call from multiple places within the same `@Transactional` method. `session.persist(entity)` queues an INSERT for the commit. `session.get(Class, id)` runs `SELECT * FROM employees WHERE id=?`.

---

### Level 2 — Intermediate

HQL (Hibernate Query Language) — object-oriented queries.

```java
// HibernateDemo.java
import jakarta.persistence.*;
import org.hibernate.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.hibernate5.*;
import org.springframework.transaction.annotation.*;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

// (Entity and @Configuration same as Level 1)

public class HibernateDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(HibCfg.class);
        SessionFactory sf = ctx.getBean(SessionFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        // Seed
        tx.execute(s -> {
            Session session = sf.getCurrentSession();
            for (String[] e : new String[][]{
                {"Alice","Engineering","95000"},{"Bob","Engineering","88000"},
                {"Carol","Marketing","72000"},{"Dave","Design","81000"},
                {"Eve","Engineering","102000"}
            }) session.persist(new Employee(e[0],e[1],Integer.parseInt(e[2])));
            return null;
        });

        // HQL — uses entity class name and property names (NOT table/column names)
        tx.execute(s -> {
            Session session = sf.getCurrentSession();

            // HQL SELECT — FROM Employee (class name, not table name)
            List<Employee> eng = session.createQuery(
                "FROM Employee WHERE dept = :dept ORDER BY salary DESC", Employee.class)
                .setParameter("dept","Engineering")
                .getResultList();
            System.out.println("Engineering team:");
            eng.forEach(e -> System.out.printf("  %-8s $%,d%n", e.getName(), e.getSalary()));

            // HQL aggregate
            Long count = session.createQuery(
                "SELECT COUNT(e) FROM Employee e WHERE e.dept = :d", Long.class)
                .setParameter("d","Engineering").getSingleResult();
            System.out.println("Count: " + count);

            // HQL scalar — projection to Object[]
            List<Object[]> summary = session.createQuery(
                "SELECT e.dept, AVG(e.salary) FROM Employee e GROUP BY e.dept ORDER BY e.dept",
                Object[].class).getResultList();
            summary.forEach(r -> System.out.printf("  %-12s avg=$%.0f%n", r[0], r[1]));
            return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

HQL uses **entity class names** and **property names** — `FROM Employee` (class) not `FROM employees` (table); `e.dept` (field) not `dept` column. Hibernate translates HQL to SQL based on the mapping. Named parameters (`:dept`) work the same as in JPQL.

---

### Level 3 — Advanced

Hibernate-specific features — `@Filter`, native SQL, and `Session.createNativeQuery()`.

```java
// HibernateDemo.java
import jakarta.persistence.*;
import org.hibernate.*;
import org.hibernate.annotations.*;
import org.springframework.context.annotation.*;
import org.springframework.orm.hibernate5.*;
import org.springframework.transaction.support.TransactionTemplate;
import javax.sql.DataSource;
import java.util.*;

@FilterDef(name = "activeFilter", parameters = @ParamDef(name = "active", type = Boolean.class))
@Filter(name = "activeFilter", condition = "active = :active")
@Entity @Table(name = "employees")
class Employee {
    @Id @GeneratedValue(strategy=GenerationType.IDENTITY) Long id;
    String name; String dept; int salary; boolean active = true;
    public Employee(){}
    public Employee(String n, String d, int s, boolean a){name=n;dept=d;salary=s;active=a;}
    public Long getId(){return id;} public String getName(){return name;}
    public String getDept(){return dept;} public int getSalary(){return salary;}
}

@Configuration @EnableTransactionManagement
class HibCfg {
    @Bean DataSource ds(){
        var d=new org.springframework.jdbc.datasource.DriverManagerDataSource();
        d.setDriverClassName("org.h2.Driver"); d.setUrl("jdbc:h2:mem:hr;DB_CLOSE_DELAY=-1");
        d.setUsername("sa"); d.setPassword(""); return d;
    }
    @Bean LocalSessionFactoryBean sessionFactory(DataSource ds) {
        var sf = new LocalSessionFactoryBean(); sf.setDataSource(ds); sf.setPackagesToScan("");
        Properties p = new Properties(); p.setProperty("hibernate.hbm2ddl.auto","create-drop");
        p.setProperty("hibernate.dialect","org.hibernate.dialect.H2Dialect"); sf.setHibernateProperties(p); return sf;
    }
    @Bean HibernateTransactionManager tx(SessionFactory sf){return new HibernateTransactionManager(sf);}
}

public class HibernateDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(HibCfg.class);
        SessionFactory sf = ctx.getBean(SessionFactory.class);
        TransactionTemplate tx = new TransactionTemplate(
            ctx.getBean(org.springframework.transaction.PlatformTransactionManager.class));

        tx.execute(s -> {
            Session session = sf.getCurrentSession();
            session.persist(new Employee("Alice","Engineering",95000,true));
            session.persist(new Employee("Bob","Engineering",88000,false));  // inactive
            session.persist(new Employee("Carol","Marketing",72000,true));
            return null;
        });

        // @Filter — adds WHERE clause automatically when enabled
        tx.execute(s -> {
            Session session = sf.getCurrentSession();
            session.enableFilter("activeFilter").setParameter("active", true);
            List<Employee> active = session.createQuery("FROM Employee", Employee.class).getResultList();
            System.out.println("Active employees: " + active.size());  // 2 (Bob filtered out)
            active.forEach(e -> System.out.printf("  %s (%s)%n", e.getName(), e.getDept()));
            return null;
        });

        // Native SQL via Session
        tx.execute(s -> {
            Session session = sf.getCurrentSession();
            // createNativeQuery — raw SQL, map to entity
            @SuppressWarnings("unchecked")
            List<Employee> highEarners = session.createNativeQuery(
                "SELECT * FROM employees WHERE salary > :min AND active = TRUE", Employee.class)
                .setParameter("min", 90000)
                .getResultList();
            System.out.println("High earners (native SQL): " + highEarners.size());
            highEarners.forEach(e -> System.out.printf("  %s $%,d%n", e.getName(), e.getSalary()));
            return null;
        });

        ctx.close();
    }
}
```

How to run: same classpath

`@FilterDef` / `@Filter` is a Hibernate-specific feature — not available in plain JPA. When the filter is enabled on a `Session`, Hibernate appends the filter's `condition` to every HQL query on that entity automatically. `session.createNativeQuery(sql, Entity.class)` runs raw SQL and maps the result set to entities using Hibernate's column-to-field mapping — useful when HQL lacks the SQL feature you need.

## 6. Walkthrough

**Level 2 — HQL query execution (execution order):**

1. **`tx.execute(s -> { ... })`**: `HibernateTransactionManager.getTransaction()` → `sf.getCurrentSession()` → open a `Session` with a new connection from `DataSource` → `session.beginTransaction()`.
2. **`session.createQuery("FROM Employee WHERE dept = :dept ORDER BY salary DESC", Employee.class)`**: Hibernate parses the HQL, maps `Employee` → `EMPLOYEES` table, `dept` → `DEPT` column, `salary` → `SALARY` column.
3. **`.setParameter("dept","Engineering")`**: binds `:dept` → `?` → `"Engineering"`.
4. **`.getResultList()`**: Hibernate generates and executes: `SELECT e.id, e.name, e.dept, e.salary FROM employees e WHERE e.dept=? ORDER BY e.salary DESC` → params `["Engineering"]`.
5. **H2 returns 3 rows**: Alice (102k), Eve (95k→actually ordering matters here), Bob (88k).
6. **Hibernate maps** each row to `new Employee()` via setter calls → `List<Employee>` returned.
7. **Aggregate query**: `COUNT(e)` → `SELECT COUNT(*) FROM employees WHERE dept=?` → `Long(3)`.
8. **TX commits** (no mutations — only flush of empty dirty set) → session closed.

```
HQL:  FROM Employee WHERE dept = :dept ORDER BY salary DESC
SQL:  SELECT e.id,e.name,e.dept,e.salary FROM employees e WHERE e.dept=? ORDER BY e.salary DESC
Params: ["Engineering"]
Result: [Eve(102000), Alice(95000), Bob(88000)]
```

## 7. Gotchas & takeaways

> **`sf.getCurrentSession()` throws `HibernateException` if there is no active transaction** — it requires a TX-bound session. Always call it inside a `@Transactional` method. Use `sf.openSession()` if you need a session outside a transaction, but remember to close it manually.

> **`hibernate.hbm2ddl.auto=create-drop` drops the schema on `SessionFactory.close()`** — never use this in production. Use `validate` to check the schema against entities at startup; use Flyway/Liquibase for actual migrations.

> **HQL is case-sensitive on entity/property names.** `FROM employee` is wrong if the class is named `Employee`. `FROM Employee` is correct. SQL keywords (`FROM`, `WHERE`, `ORDER BY`) are case-insensitive.

- `LocalSessionFactoryBean` → `SessionFactory` (singleton); configure via `setDataSource` + `setPackagesToScan`.
- `sf.getCurrentSession()` → TX-bound Session; requires active `@Transactional`.
- HQL uses class/property names; Hibernate translates to SQL.
- `@Filter` adds automatic WHERE clauses — Hibernate-specific, not in JPA.
- `hbm2ddl.auto=validate` for production; Flyway/Liquibase for migrations.
