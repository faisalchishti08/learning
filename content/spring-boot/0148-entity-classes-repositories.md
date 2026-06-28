---
card: spring-boot
gi: 148
slug: entity-classes-repositories
title: Entity classes & repositories
---

## 1. What it is

**Entity classes** are Java classes annotated with JPA's `@Entity` — they map to database tables. Each instance represents a row. **Repositories** in Spring Data JPA are interfaces that extend `JpaRepository<T, ID>` (or narrower interfaces like `CrudRepository`, `PagingAndSortingRepository`). Spring Data JPA generates a runtime implementation automatically: save, find, delete, count, and custom derived-query methods all come for free from the interface declaration alone.

## 2. Why & when

Without repositories, every DAO class repeats the same `EntityManager` calls — `em.persist()`, `em.find()`, `em.createQuery()`. Spring Data's repository abstraction eliminates that boilerplate. You describe *what* data you want in a method signature; Spring Data generates *how* to get it.

Use `@Entity` + repository when:

- Your data model maps cleanly to relational tables.
- You need CRUD, pagination, and sorting without hand-writing SQL.
- You want derived queries from method names without writing JPQL.

For complex reporting or bulk operations, complement repositories with `@Query` annotations or `JdbcTemplate`.

## 3. Core concept

**Entity anatomy:**

```java
@Entity                         // marks as JPA entity
@Table(name = "customer")       // explicit table name (optional)
class Customer {
    @Id                         // primary key
    @GeneratedValue(...)        // auto-generate value
    private Long id;

    @Column(nullable = false, length = 100)
    private String email;

    @OneToMany(mappedBy = "customer", cascade = CascadeType.ALL)
    private List<Order> orders;
}
```

**Repository hierarchy:**

```
Repository (marker)
  └─ CrudRepository      → save, findById, findAll, delete, count
       └─ PagingAndSortingRepository  → findAll(Pageable)
            └─ JpaRepository          → flush, saveAll, getById, deleteAllInBatch
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">@Entity class</text>
  <text x="90" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">maps to table</text>
  <rect x="240" y="55" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">JpaRepository</text>
  <text x="327" y="96" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">interface you declare</text>
  <rect x="240" y="125" width="175" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="327" y="147" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">Generated impl</text>
  <text x="327" y="164" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(SimpleJpaRepository)</text>
  <rect x="490" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">EntityManager</text>
  <text x="575" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">→ database</text>
  <line x1="162" y1="110" x2="236" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#er)"/>
  <line x1="327" y1="107" x2="327" y2="123" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#er2)"/>
  <line x1="417" y1="150" x2="486" y2="128" stroke="#8b949e" stroke-width="1.5" marker-end="url(#er3)"/>
  <defs>
    <marker id="er" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="er2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="er3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Entity maps Java class to table; `JpaRepository` interface → Spring Data generates `SimpleJpaRepository` impl → delegates to `EntityManager`.

## 5. Runnable example

```java
// EntityRepoApp.java — Spring Boot project
// pom.xml: spring-boot-starter-data-jpa, com.h2database:h2 (runtime)
// application.properties: spring.jpa.hibernate.ddl-auto=create-drop

import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@SpringBootApplication
public class EntityRepoApp {
    public static void main(String[] args) {
        SpringApplication.run(EntityRepoApp.class, args);
    }
}

@Entity
@Table(name = "employee")
class Employee {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private String department;

    private int salary;

    protected Employee() {}
    Employee(String name, String department, int salary) {
        this.name = name; this.department = department; this.salary = salary;
    }
    public Long getId() { return id; }
    public String getName() { return name; }
    public String getDepartment() { return department; }
    public int getSalary() { return salary; }
}

interface EmployeeRepository extends JpaRepository<Employee, Long> {
    // Derived query: Spring generates the SQL
    List<Employee> findByDepartment(String department);

    // Case-insensitive name search
    List<Employee> findByNameContainingIgnoreCase(String keyword);

    // Custom JPQL query
    @Query("SELECT e FROM Employee e WHERE e.salary > :min ORDER BY e.salary DESC")
    List<Employee> highEarners(@org.springframework.data.repository.query.Param("min") int minSalary);
}

@RestController
@RequestMapping("/employees")
class EmployeeController {

    private final EmployeeRepository repo;

    EmployeeController(EmployeeRepository repo) {
        repo.save(new Employee("Alice", "Engineering", 95000));
        repo.save(new Employee("Bob", "Marketing", 72000));
        repo.save(new Employee("Carol", "Engineering", 110000));
        this.repo = repo;
    }

    @GetMapping
    public Page<Employee> all(@RequestParam(defaultValue = "0") int page) {
        return repo.findAll(PageRequest.of(page, 2, Sort.by("name")));
    }

    @GetMapping("/dept/{dept}")
    public List<Employee> byDept(@PathVariable String dept) {
        return repo.findByDepartment(dept);
    }

    @GetMapping("/high-earners")
    public List<Employee> highEarners(@RequestParam(defaultValue = "80000") int min) {
        return repo.highEarners(min);
    }

    @GetMapping("/{id}")
    public Optional<Employee> byId(@PathVariable Long id) {
        return repo.findById(id);
    }
}
```

**How to run:** start the app, then:
- `curl http://localhost:8080/employees` → first page of employees sorted by name
- `curl http://localhost:8080/employees/dept/Engineering` → Engineering team
- `curl "http://localhost:8080/employees/high-earners?min=90000"` → earners above 90 000

## 6. Walkthrough

- `@Entity` with `@Table(name="employee")` maps the class to the `employee` table. Hibernate creates the table at startup because `ddl-auto=create-drop`.
- `@GeneratedValue(strategy = GenerationType.IDENTITY)` means the database auto-increments the primary key; `@Column(nullable = false)` adds a NOT NULL constraint.
- `EmployeeRepository extends JpaRepository<Employee, Long>` gives 18+ free methods. Spring Data generates `SimpleJpaRepository` at startup that implements them using the `EntityManager`.
- `findByDepartment(String department)` is a derived query: Spring parses the method name, extracts `department`, and generates `SELECT e FROM Employee e WHERE e.department = ?1`.
- `@Query("SELECT e FROM Employee e WHERE e.salary > :min ORDER BY e.salary DESC")` with `@Param("min")` shows explicit JPQL — useful when derived method names become unwieldy.
- `repo.findAll(PageRequest.of(page, 2, Sort.by("name")))` returns a `Page<Employee>` — includes content, total elements, total pages, and navigation metadata.

## 7. Gotchas & takeaways

> Entity classes require a **no-argument constructor** (can be `protected`). Without it, JPA cannot instantiate entities when reading from the database.

> `repo.findById(id)` returns `Optional<Employee>` — never assume it's non-empty. If you know the entity exists and want an exception on absence, use `repo.getReferenceById(id)` (returns a lazy proxy; throws on first field access if not found).

- All JPA annotations live in `jakarta.persistence.*` (Spring Boot 3+) not `javax.persistence.*` (Spring Boot 2).
- Cascade types control what happens when a parent entity is saved/deleted. `CascadeType.ALL` on `@OneToMany` means child entities are also persisted/deleted. Use with care — it can cause unexpected bulk deletes.
- `@Transactional` is not needed on `JpaRepository` calls in a service annotated `@Transactional` — repository methods inherit the transaction.
- Spring Data's `@Modifying` + `@Query` enables `UPDATE`/`DELETE` JPQL in repositories; always pair with `@Transactional`.
- `@DataJpaTest` in tests loads only JPA layer (entity + repository), not the full context — fast and isolated.
