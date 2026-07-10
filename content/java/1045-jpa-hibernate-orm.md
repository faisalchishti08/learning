---
card: java
gi: 1045
slug: jpa-hibernate-orm
title: JPA / Hibernate ORM
---

## 1. What it is

JPA (Jakarta Persistence API) is a specification for mapping Java objects to relational database tables — an **Object-Relational Mapper (ORM)** — letting you work with plain Java classes annotated with `@Entity`, `@Id`, `@Column`, and query them through an `EntityManager`, rather than hand-writing SQL and manually converting `ResultSet` rows into objects. Hibernate is the most widely-used *implementation* of that specification — JPA defines the annotations and interfaces; Hibernate is the actual engine that translates your annotated classes and queries into real SQL, executes it against the database, and converts the results back into Java objects.

## 2. Why & when

Hand-written JDBC (see [JDBC & connection pooling](1044-jdbc-connection-pooling.md)) requires writing SQL by hand for every query and manually copying each `ResultSet` column into object fields — for an application with dozens of entity types and relationships between them (an `Order` referencing a `Customer`, which has many `Order`s), this becomes a large amount of repetitive, error-prone mapping code. JPA/Hibernate automates that mapping: annotate a class once with how it corresponds to a table, and every subsequent save, load, update, and relationship traversal is handled by the framework — including automatically generating the SQL `JOIN`s needed to follow an `@ManyToOne` or `@OneToMany` relationship, and tracking which loaded entities have been modified so only the actually-changed ones get written back to the database on commit (the "dirty checking" mechanism).

Reach for JPA/Hibernate for applications with a genuinely object-oriented domain model and non-trivial relationships between entities, where hand-writing the mapping and relationship-traversal SQL repeatedly would be substantial, repetitive work. For simple, flat data access with few or no relationships, or for performance-critical queries where you need precise control over the generated SQL, plain JDBC (or a lighter SQL-mapping library) can be a more direct, transparent choice.

## 3. Core concept

```java
import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "customers")
class Customer {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    String name;

    @OneToMany(mappedBy = "customer", cascade = CascadeType.ALL)
    List<Order> orders; // Hibernate generates the JOIN needed to load these automatically
}

@Entity
@Table(name = "orders")
class Order {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    double total;

    @ManyToOne
    @JoinColumn(name = "customer_id")
    Customer customer;
}

// Using it: no hand-written SQL at all for basic operations.
EntityManager em = entityManagerFactory.createEntityManager();
em.getTransaction().begin();
Customer customer = new Customer();
customer.name = "Ana";
em.persist(customer); // generates an INSERT automatically

Customer loaded = em.find(Customer.class, customer.id); // generates a SELECT automatically
loaded.name = "Ana Updated"; // no explicit save call needed --
em.getTransaction().commit(); // Hibernate detects the change and generates an UPDATE
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Customer entity annotated with JPA mappings, translated by Hibernate into generated SQL INSERT, SELECT, and UPDATE statements against the actual customers table">
  <rect x="30" y="50" width="180" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="75" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Entity Customer</text>
  <text x="120" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Java object</text>

  <rect x="250" y="50" width="140" height="70" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Hibernate</text>
  <text x="320" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(the ORM engine)</text>

  <rect x="430" y="50" width="180" height="70" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="520" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">INSERT / SELECT /</text>
  <text x="520" y="93" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">UPDATE customers</text>

  <line x1="210" y1="85" x2="250" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="390" y1="85" x2="430" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Hibernate translates annotated Java entities into the actual SQL executed against the database.

## 5. Runnable example

Scenario: a customer-and-orders domain model, evolving from hand-written JDBC mapping into JPA entities with automatic relationship loading and dirty-checked updates.

### Level 1 — Basic

```java
// File: RawJdbcMapping.java -- manual mapping, no JPA at all
// Requires the H2 driver on the classpath.
import java.sql.*;

public class RawJdbcMapping {
    static final String URL = "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1";

    record Customer(long id, String name) {} // manually mapped from a ResultSet row

    public static void main(String[] args) throws Exception {
        try (Connection conn = DriverManager.getConnection(URL);
             Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE TABLE customers (id BIGINT AUTO_INCREMENT, name VARCHAR(50))");

            // Manual INSERT
            stmt.execute("INSERT INTO customers (name) VALUES ('Ana')");

            // Manual SELECT and manual mapping into a Customer object
            try (ResultSet rs = stmt.executeQuery("SELECT id, name FROM customers WHERE name = 'Ana'")) {
                if (rs.next()) {
                    Customer customer = new Customer(rs.getLong("id"), rs.getString("name"));
                    System.out.println("Loaded: " + customer);
                }
            }
        }
    }
}
```

**How to run:** with the H2 driver JAR on the classpath, `javac -cp h2-2.2.224.jar RawJdbcMapping.java && java -cp .:h2-2.2.224.jar RawJdbcMapping` (JDK 17+).

Expected output:
```
Loaded: Customer[id=1, name=Ana]
```

Every field of `Customer` is manually extracted from the `ResultSet` by column name — for an entity with many fields, or many related entity types, this mapping code multiplies quickly and must be kept manually in sync with the table schema.

### Level 2 — Intermediate

```java
// File: src/main/java/Customer.java
import jakarta.persistence.*;

@Entity
@Table(name = "customers")
public class Customer {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    String name;

    public Customer() {} // JPA requires a no-arg constructor
    public Customer(String name) { this.name = name; }

    @Override public String toString() { return "Customer[id=" + id + ", name=" + name + "]"; }
}
```

```java
// File: src/main/java/JpaBasic.java
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;

public class JpaBasic {
    public static void main(String[] args) {
        EntityManagerFactory emf = Persistence.createEntityManagerFactory("my-persistence-unit");
        EntityManager em = emf.createEntityManager();

        em.getTransaction().begin();
        Customer customer = new Customer("Ana");
        em.persist(customer); // no hand-written SQL -- Hibernate generates the INSERT
        em.getTransaction().commit();

        Customer loaded = em.find(Customer.class, customer.id); // Hibernate generates the SELECT
        System.out.println("Loaded: " + loaded);

        em.close();
        emf.close();
    }
}
```

**How to run:** place in a Maven project with `hibernate-core`, `jakarta.persistence-api`, and the H2 driver as dependencies, plus a `META-INF/persistence.xml` defining `my-persistence-unit` pointing at an H2 in-memory database. Run `mvn compile exec:java -Dexec.mainClass=JpaBasic`.

Expected output:
```
Loaded: Customer[id=1, name=Ana]
```

The real-world concern added: no SQL was written anywhere in `JpaBasic.java` — `em.persist(customer)` and `em.find(Customer.class, customer.id)` generate the equivalent `INSERT` and `SELECT` statements automatically, based purely on `Customer`'s `@Entity` annotations. The mapping between the class and the table lives once, in the entity class itself.

### Level 3 — Advanced

```java
// File: src/main/java/Order.java
import jakarta.persistence.*;

@Entity
@Table(name = "orders")
public class Order {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    double total;

    @ManyToOne
    @JoinColumn(name = "customer_id")
    Customer customer;

    public Order() {}
    public Order(double total, Customer customer) { this.total = total; this.customer = customer; }

    @Override public String toString() { return "Order[id=" + id + ", total=" + total + "]"; }
}
```

```java
// File: src/main/java/Customer.java (updated to add the relationship)
import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "customers")
public class Customer {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;
    String name;

    @OneToMany(mappedBy = "customer", cascade = CascadeType.ALL)
    List<Order> orders = new ArrayList<>(); // the "many" side of the relationship

    public Customer() {}
    public Customer(String name) { this.name = name; }

    @Override public String toString() { return "Customer[id=" + id + ", name=" + name + "]"; }
}
```

```java
// File: src/main/java/JpaAdvanced.java
import jakarta.persistence.EntityManager;
import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;

public class JpaAdvanced {
    public static void main(String[] args) {
        EntityManagerFactory emf = Persistence.createEntityManagerFactory("my-persistence-unit");
        EntityManager em = emf.createEntityManager();

        em.getTransaction().begin();
        Customer customer = new Customer("Ana");
        Order order1 = new Order(19.99, customer);
        Order order2 = new Order(42.50, customer);
        customer.orders.add(order1);
        customer.orders.add(order2);
        em.persist(customer); // cascade=ALL: persisting the customer ALSO persists both orders
        em.getTransaction().commit();

        // Load the customer fresh and follow the relationship -- Hibernate
        // generates the JOIN (or a separate query, depending on fetch strategy)
        // needed to populate `orders` automatically.
        Customer loaded = em.find(Customer.class, customer.id);
        double total = loaded.orders.stream().mapToDouble(o -> o.total).sum();
        System.out.println(loaded + " has " + loaded.orders.size() + " orders totaling " + total);

        // Dirty checking: modify a loaded entity's field with NO explicit save call --
        // Hibernate detects the change and generates the UPDATE automatically on commit.
        em.getTransaction().begin();
        loaded.name = "Ana Updated";
        em.getTransaction().commit();

        Customer reloaded = em.find(Customer.class, customer.id);
        System.out.println("After update: " + reloaded);

        em.close();
        emf.close();
    }
}
```

**How to run:** place in the same Maven project as Level 2 (with `Order.java` added and `Customer.java` updated), then `mvn compile exec:java -Dexec.mainClass=JpaAdvanced`.

Expected output:
```
Customer[id=1, name=Ana] has 2 orders totaling 62.49
After update: Customer[id=1, name=Ana Updated]
```

The production-flavored hard case: `cascade = CascadeType.ALL` means persisting `customer` automatically persists both associated `Order` entities in one call, `em.find` followed by `.orders` transparently loads the related rows via a generated `JOIN` or secondary query, and modifying `loaded.name` with **no explicit save call at all** still results in a generated `UPDATE` — Hibernate's dirty-checking mechanism compares the entity's current state against a snapshot taken when it was loaded, and writes back only what actually changed.

## 6. Walkthrough

Tracing the dirty-checking update in `JpaAdvanced.main`:

1. `Customer loaded = em.find(Customer.class, customer.id)` loads the customer from the database — internally, Hibernate stores a **snapshot** of this entity's field values at the moment it was loaded, associated with the current persistence context (the `EntityManager`'s internal tracking of "managed" entities).
2. `em.getTransaction().begin()` starts a new transaction.
3. `loaded.name = "Ana Updated"` directly reassigns the `name` field on the plain Java object — this is an ordinary field assignment, with no explicit call to any Hibernate method at all; from the code's perspective, it looks exactly like mutating any other object.
4. `em.getTransaction().commit()` triggers Hibernate's **flush** process before actually committing: for every entity currently managed by this persistence context, Hibernate compares its current field values against the snapshot taken when it was loaded (from step 1).
5. Hibernate detects that `loaded.name` now differs from the snapshot's `name` value (`"Ana"` versus `"Ana Updated"`) — this is exactly what "dirty checking" means: identifying which managed entities have actually changed since they were loaded, without requiring the application code to explicitly flag or call a save method for the change.
6. Based on this detected difference, Hibernate generates and executes an `UPDATE customers SET name = 'Ana Updated' WHERE id = ?` statement automatically, then commits the transaction. `em.find(Customer.class, customer.id)` afterward (a fresh load) confirms the change was genuinely persisted to the database, printed as `"After update: Customer[id=1, name=Ana Updated]"`.

## 7. Gotchas & takeaways

> **Gotcha:** the automatic relationship-loading convenience (`loaded.orders`) can silently trigger the notorious "N+1 query problem" — if `orders` is lazily loaded and code iterates over many customers each accessing `.orders`, Hibernate issues one additional query *per customer* to fetch their orders, rather than one efficient batch query for all of them — a performance trap that's invisible in the Java code itself and only shows up as unexpectedly many SQL queries when actually observed.

- JPA is the specification (annotations, interfaces); Hibernate is the most widely-used implementation that actually generates and executes SQL based on annotated entity classes.
- `@OneToMany`/`@ManyToOne` (and `@ManyToMany`) map object relationships to foreign-key relationships, with Hibernate generating the `JOIN`s or secondary queries needed to traverse them.
- Dirty checking means modifying a loaded entity's field directly (no explicit save call) still results in an automatically-generated `UPDATE` on transaction commit — Hibernate detects the change by comparing against a snapshot taken at load time.
- `cascade = CascadeType.ALL` propagates persistence operations (persist, remove) from a parent entity to its related child entities automatically.
- The "N+1 query problem" — one query per related entity instead of one batched query for all of them — is the most common real-world JPA/Hibernate performance trap, and requires deliberate fetch-strategy tuning (eager fetching, batch fetching, or explicit `JOIN FETCH` queries) to avoid.
- Reach for plain JDBC (see [JDBC & connection pooling](1044-jdbc-connection-pooling.md)) instead of JPA/Hibernate specifically when you need precise, transparent control over the exact SQL executed, or when the domain model is simple enough that the ORM's relationship-mapping machinery adds more complexity than it saves.
