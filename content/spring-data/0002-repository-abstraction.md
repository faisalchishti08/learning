---
card: spring-data
gi: 2
slug: repository-abstraction
title: "Repository abstraction"
---

## 1. What it is

The repository abstraction is Spring Data's central idea: instead of writing a data-access-object class by hand — a class with fields for a connection or session, and methods you implement one statement at a time — you write a plain Java *interface* describing the operations you need, and Spring Data generates a working implementation for you at runtime. `Repository<T, ID>` is the marker interface at the root of this whole hierarchy; everything else in Spring Data (`CrudRepository`, `PagingAndSortingRepository`, `JpaRepository`, and so on) builds on top of it.

```java
public interface CustomerRepository extends Repository<Customer, Long> {
    Optional<Customer> findById(Long id); // you declare it, Spring Data implements it
}
```

## 2. Why & when

Hand-written DAOs repeat the same shape across every entity in an application: obtain a connection or session, build a statement, execute it, map the result, handle exceptions, close resources. None of that boilerplate carries information specific to *this* entity's business meaning — it's pure mechanical repetition. The repository abstraction removes it by inverting the relationship: you describe the *contract* (an interface), and the framework supplies the *implementation*, generated from generic infrastructure that already knows how to talk to the store.

Reach for the repository abstraction specifically when:

- You're building any Spring Data-based data-access layer — this is the foundational pattern every other Spring Data capability in this section (CRUD, paging, query derivation, custom implementations) builds on top of.
- You want a data-access contract that's easy to mock or stub in tests — because it's a plain interface, test doubles are trivial to write without any Spring Data machinery involved at all.
- You need the same conceptual data-access shape across different entities and, if a project uses more than one, different stores — every repository interface in a codebase looks and behaves consistently, regardless of what's actually persisting the data underneath.

## 3. Core concept

```
 Repository<T, ID>              -- the ROOT marker interface: no methods, no behavior
        |                          just declares "T is the entity type, ID is its id type"
        v
 (you can extend Repository directly and declare ONLY the methods you want,
  OR extend a richer interface like CrudRepository that already declares
  save/findById/delete/etc. -- covered in the next cards)
        |
        v
 At application startup, Spring Data's repository infrastructure:
   1. finds every interface extending Repository (via component scanning)
   2. for each one, generates a proxy implementation class at runtime
   3. registers that proxy as a Spring bean, injectable like any other bean
        |
        v
 Calling a method on the injected repository bean invokes the GENERATED
 implementation -- your interface never has a class implementing it in source code
```

`Repository<T, ID>` itself is deliberately empty — it exists purely as a marker so Spring Data's scanning infrastructure knows "this interface should get a generated implementation."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A repository interface extending Repository gets a runtime-generated proxy implementation registered as a Spring bean">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CustomerRepository</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends Repository&lt;Customer,Long&gt;</text>

  <rect x="250" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Repository infrastructure</text>
  <text x="340" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scans + generates proxy at startup</text>

  <rect x="480" y="20" width="150" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">generated proxy</text>
  <text x="555" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a real Spring bean</text>

  <line x1="200" y1="47" x2="245" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="430" y1="47" x2="475" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Nothing in your source code implements `CustomerRepository` — the implementation exists only at runtime, generated by the infrastructure.

## 5. Runnable example

The scenario: a `CustomerRepository` that starts as a bare `Repository<Customer, Long>` extension with hand-picked methods (not the full `CrudRepository` contract), evolves to show what the generated proxy actually is at runtime, then to a custom method added on top of the base contract — building intuition for exactly what "you declare it, Spring Data implements it" means in practice.

### Level 1 — Basic

Extend `Repository<T, ID>` directly (not `CrudRepository`) and declare only two methods — `save` and `findById` — proving Spring Data implements exactly, and only, what you declare.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.Repository;

import java.util.Optional;

@SpringBootApplication
public class RepositoryAbstractionLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
    }

    // Extends the bare Repository marker, not CrudRepository -- only these two methods exist.
    public interface CustomerRepository extends Repository<Customer, Long> {
        Customer save(Customer customer);
        Optional<Customer> findById(Long id);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(RepositoryAbstractionLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:repoabs1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        System.out.println("proxy implementation class = " + repo.getClass().getName());

        Customer saved = repo.save(new Customer("Ada Lovelace"));
        Optional<Customer> found = repo.findById(saved.getId());
        System.out.println("found = " + found.map(Customer::getName).orElse("MISSING"));

        if (found.isEmpty() || !found.get().getName().equals("Ada Lovelace"))
            throw new AssertionError("Expected to find the saved customer");
        System.out.println("Bare Repository<T,ID> with only 2 declared methods worked -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java RepositoryAbstractionLevel1.java` on JDK 17+.

`CustomerRepository extends Repository<Customer, Long>` — the root marker interface, not `CrudRepository` — and declares only `save` and `findById`; no `delete`, `findAll`, or anything else exists on this interface at all. Printing `repo.getClass().getName()` reveals the actual runtime type is a dynamically generated proxy class (typically reported as something like `com.sun.proxy.$ProxyNN` or a CGLIB-generated class name), confirming there is genuinely no hand-written implementation class anywhere — the proxy is manufactured purely from the interface's declared methods and Spring Data JPA's generic query-execution infrastructure.

### Level 2 — Intermediate

Add a custom derived-query method directly on the bare `Repository` extension, showing that query derivation (covered fully in a later card) works the same way regardless of whether the interface extends `Repository` directly or a richer interface like `CrudRepository`.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.Repository;

import java.util.List;
import java.util.Optional;

@SpringBootApplication
public class RepositoryAbstractionLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String tier;
        protected Customer() {}
        public Customer(String name, String tier) { this.name = name; this.tier = tier; }
        public Long getId() { return id; }
        public String getName() { return name; }
        public String getTier() { return tier; }
    }

    public interface CustomerRepository extends Repository<Customer, Long> {
        Customer save(Customer customer);
        Optional<Customer> findById(Long id);
        List<Customer> findByTier(String tier); // derived query, no body needed
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(RepositoryAbstractionLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:repoabs2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada Lovelace", "gold"));
        repo.save(new Customer("Grace Hopper", "gold"));
        repo.save(new Customer("Katherine Johnson", "silver"));

        List<Customer> goldCustomers = repo.findByTier("gold");
        System.out.println("gold-tier customers = " + goldCustomers.size());

        if (goldCustomers.size() != 2)
            throw new AssertionError("Expected 2 gold-tier customers, found " + goldCustomers.size());
        System.out.println("Derived query on a bare Repository<T,ID> extension worked -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java RepositoryAbstractionLevel2.java`.

`findByTier(String tier)` is added to the same bare-`Repository`-extending interface as Level 1 and works identically to how it would on `CrudRepository` or `JpaRepository` — query derivation is a capability of the shared Spring Data infrastructure, independent of which base interface a repository extends. This confirms `Repository<T, ID>` isn't a lesser or restricted starting point; it's the same generation machinery with a deliberately minimal declared surface.

### Level 3 — Advanced

Show the actual difference between two repositories over the *same* entity — one extending bare `Repository` with a hand-picked subset of methods (an intentionally restricted contract), one extending `CrudRepository` (full CRUD) — demonstrating why choosing the base interface is itself a design decision about how much surface area to expose to callers.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.Repository;

import java.util.Optional;

@SpringBootApplication
public class RepositoryAbstractionLevel3 {

    @Entity
    public static class Account {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private double balance;
        protected Account() {}
        public Account(double balance) { this.balance = balance; }
        public Long getId() { return id; }
        public double getBalance() { return balance; }
    }

    // Read-only, intentionally restricted contract -- no delete, no findAll exposed.
    public interface AccountReadOnlyRepository extends Repository<Account, Long> {
        Optional<Account> findById(Long id);
    }

    // Full CRUD contract, used internally by administrative code.
    public interface AccountAdminRepository extends JpaRepository<Account, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(RepositoryAbstractionLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:repoabs3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        AccountAdminRepository adminRepo = ctx.getBean(AccountAdminRepository.class);
        AccountReadOnlyRepository readOnlyRepo = ctx.getBean(AccountReadOnlyRepository.class);

        Account created = adminRepo.save(new Account(1000.0));
        System.out.println("created account id = " + created.getId());

        // The read-only interface can find it...
        Optional<Account> found = readOnlyRepo.findById(created.getId());
        System.out.println("read-only lookup found = " + found.map(Account::getBalance).orElse(null));

        // ...but has NO delete or save method available at compile time -- this is enforced
        // by the Java type system, not a runtime check, because AccountReadOnlyRepository
        // never declared those methods.
        boolean hasDeleteMethod = java.util.Arrays.stream(AccountReadOnlyRepository.class.getMethods())
            .anyMatch(m -> m.getName().equals("deleteById") || m.getName().equals("delete"));
        System.out.println("AccountReadOnlyRepository exposes a delete method? " + hasDeleteMethod);

        if (found.isEmpty()) throw new AssertionError("Expected the read-only repository to find the account");
        if (hasDeleteMethod) throw new AssertionError("The read-only contract should not expose delete methods");

        // The admin repository, backed by the SAME underlying table, can delete.
        adminRepo.deleteById(created.getId());
        boolean stillExists = readOnlyRepo.findById(created.getId()).isPresent();
        System.out.println("still exists after admin delete? " + stillExists);
        if (stillExists) throw new AssertionError("Expected the account to be gone after admin delete");

        System.out.println("Two differently-scoped repository interfaces over one table worked correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java RepositoryAbstractionLevel3.java`.

`AccountReadOnlyRepository` and `AccountAdminRepository` both operate on the exact same `Account` entity and the same underlying database table, but expose completely different method surfaces, because each interface declares (or inherits, via `JpaRepository`) a different set of methods. This isn't a runtime access-control check — a caller holding only an `AccountReadOnlyRepository` reference *cannot even compile* a call to `deleteById`, because that method doesn't exist on the interface at all. This is the practical payoff of the repository abstraction being interface-driven: the contract itself controls what capabilities are exposed, and that control happens at compile time, for free.

## 6. Walkthrough

Trace Level 3's startup and the delete sequence.

1. **Component scanning**: Spring Data JPA's auto-configuration finds both `AccountReadOnlyRepository` (extends `Repository`) and `AccountAdminRepository` (extends `JpaRepository`, which itself extends `PagingAndSortingRepository`, which extends `CrudRepository`, which extends `Repository`) during startup.
2. **Two separate proxies generated**: even though both interfaces ultimately describe operations against the same `Account` entity, Spring Data generates two distinct proxy beans — one implementing only `findById` (because that's all `AccountReadOnlyRepository` declares), one implementing the full CRUD surface inherited through `JpaRepository`.
3. **`adminRepo.save(...)`** creates a new `Account` row via the full-featured proxy, returning the entity with its generated `id` populated.
4. **`readOnlyRepo.findById(...)`** — a completely separate proxy instance — queries the very same table (both proxies ultimately talk to the same `EntityManager`/database) and successfully finds the row `adminRepo` just created, since both interfaces describe the same entity and table, just with different exposed operations.
5. **Reflection check**: `AccountReadOnlyRepository.class.getMethods()` inspects the interface's method list directly — there is no `deleteById` or `delete` method present, because the interface never declared or inherited one. This is checked at runtime here only to make the point visible in output; in real code, the absence would simply be a compile error if you tried to call `readOnlyRepo.deleteById(...)`.
6. **`adminRepo.deleteById(...)`** runs through the admin proxy, which does have this method (inherited from `CrudRepository` via `JpaRepository`), and removes the row.
7. **Final verification**: `readOnlyRepo.findById(...)` is called again — now returning empty, since the row is gone — confirming both repositories really do operate against the same live data, and that the earlier compile-time restriction genuinely reflected the interface's declared capability, not some hidden extra method.

```
 Account table (one underlying table)
        ^                          ^
        |                          |
 AccountReadOnlyRepository   AccountAdminRepository
   only: findById              full: save/findById/deleteById/findAll/...
        |                          |
   caller CANNOT call         caller CAN call
   deleteById -- doesn't      deleteById -- inherited
   exist on the interface     from CrudRepository
```

## 7. Gotchas & takeaways

> **Gotcha:** declaring a method on a `Repository`-extending interface that Spring Data cannot map to either a known base-interface method or a valid derived-query pattern (a misspelled entity field name, an unsupported keyword) fails at *application startup*, not at the call site — Spring Data validates every declared repository method's query derivability when it builds the proxy, so a typo like `findByLastNam` (missing the final `e`) throws a clear startup exception rather than a confusing runtime error the first time the method happens to be called.

- `Repository<T, ID>` is an empty marker interface — all the actual behavior comes from either extending a richer interface (`CrudRepository`, `PagingAndSortingRepository`, a store-specific one like `JpaRepository`) or declaring your own methods that Spring Data can implement via query derivation or `@Query`.
- Every repository interface, regardless of which base interface it extends, gets a runtime-generated proxy implementation — there is never hand-written implementation source code to maintain for standard operations.
- Choosing to extend bare `Repository` (or a narrow custom interface) instead of `CrudRepository`/`JpaRepository` is a legitimate design choice for restricting a contract's exposed surface — useful for read-only views or narrowly-scoped access patterns, enforced by the Java compiler rather than by runtime checks.
- The next few cards in this section build directly on this foundation, covering the specific richer interfaces (`CrudRepository`, `ListCrudRepository`, `PagingAndSortingRepository`) that most real applications extend instead of the bare marker.
