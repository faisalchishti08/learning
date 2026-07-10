---
card: spring-data
gi: 30
slug: customizing-the-base-repository
title: "Customizing the base repository"
---

## 1. What it is

Customizing the base repository means replacing the *default* implementation Spring Data uses for every standard method (`save`, `findById`, `delete`, and the rest) across an entire application — not one repository at a time, as the previous card's fragments did, but globally, via a custom base class extending `SimpleJpaRepository` and `@EnableJpaRepositories(repositoryBaseClass = ...)`. This is the mechanism for applying cross-cutting behavior (auditing every save, soft-delete instead of hard-delete, custom exception translation) to *every* repository in an application at once, without touching any individual repository interface.

```java
public class AuditingRepositoryImpl<T, ID> extends SimpleJpaRepository<T, ID> {
    @Override
    public <S extends T> S save(S entity) {
        System.out.println("[audit] saving: " + entity);
        return super.save(entity);
    }
}

@EnableJpaRepositories(repositoryBaseClass = AuditingRepositoryImpl.class)
```

## 2. Why & when

The previous card's fragments customize one repository's *extra* methods; customizing the base repository changes the implementation of the *standard* methods every repository already has, application-wide. This distinction matters: reach for a fragment when one specific repository needs one specific extra capability; reach for a custom base repository when *every* repository in the application needs the same behavioral change applied to its standard save/delete/find operations.

Reach for a custom base repository specifically when:

- You need every `delete`/`deleteById` call across the entire application to actually perform a soft-delete (setting a flag) instead of a hard `DELETE` — changing this once, in a base class, is far more maintainable than modifying every individual repository or every call site.
- You need consistent, automatic behavior on every `save` — auditing, timestamp-stamping (though `@CreatedDate`/`@LastModifiedDate`, covered in the auditing card of this section's Spring Data JPA-specific area, often covers this more directly), or a cross-cutting validation step.
- You want to change what exception type a low-level database failure gets translated into, application-wide, without repeating that translation logic in every custom fragment.

## 3. Core concept

```
 Default:
   SimpleJpaRepository<T, ID>  -- Spring Data JPA's built-in implementation
   of CrudRepository/PagingAndSortingRepository/JpaRepository's standard methods

 Custom base repository:
   1. Extend SimpleJpaRepository<T, ID>, override whichever standard methods
      need different behavior:

      public class SoftDeleteRepositoryImpl<T, ID> extends SimpleJpaRepository<T, ID> {
          @Override
          public void deleteById(ID id) {
              // custom logic: set a "deleted" flag instead of a real DELETE
          }
      }

   2. Register it application-wide via @EnableJpaRepositories:
      @EnableJpaRepositories(repositoryBaseClass = SoftDeleteRepositoryImpl.class)

   3. EVERY repository in the application -- CustomerRepository, OrderRepository,
      ProductRepository, all of them -- now uses THIS class as their base
      implementation for standard methods, with ZERO change to any individual
      repository interface.
```

`repositoryBaseClass` is a single, application-wide setting — one custom base class affects every repository the scanning configuration covers.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A custom repositoryBaseClass replaces the default standard-method implementation for every repository in the application at once">
  <rect x="230" y="15" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SoftDeleteRepositoryImpl</text>

  <rect x="30" y="110" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CustomerRepository</text>
  <text x="120" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deleteById -> soft delete</text>

  <rect x="230" y="110" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderRepository</text>
  <text x="320" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deleteById -> soft delete</text>

  <rect x="430" y="110" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ProductRepository</text>
  <text x="520" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deleteById -> soft delete</text>

  <line x1="290" y1="60" x2="120" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="330" y1="60" x2="320" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="370" y1="60" x2="520" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

One custom base class change ripples out to every repository in the scanned base package(s).

## 5. Runnable example

The scenario: an application-wide soft-delete policy, evolving from a basic custom base repository overriding `deleteById`, to confirming it applies to multiple unrelated repositories simultaneously, to a base repository that also overrides `findById` to respect the soft-delete flag transparently.

### Level 1 — Basic

Override `deleteById` in a custom base repository so it sets a flag instead of performing a real `DELETE`, and confirm one repository picks up this behavior automatically.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.jpa.repository.support.JpaEntityInformation;
import org.springframework.data.jpa.repository.support.SimpleJpaRepository;
import org.springframework.stereotype.Component;

import java.io.Serializable;

@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = CustomBaseLevel1.class, repositoryBaseClass = CustomBaseLevel1.SoftDeleteRepositoryImpl.class)
public class CustomBaseLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean deleted = false;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public Long getId() { return id; }
        public boolean isDeleted() { return deleted; }
        public void setDeleted(boolean deleted) { this.deleted = deleted; }
    }

    // A custom base class replacing SimpleJpaRepository for EVERY repository in this app.
    public static class SoftDeleteRepositoryImpl<T, ID extends Serializable> extends SimpleJpaRepository<T, ID> {
        private final EntityManager entityManager;

        public SoftDeleteRepositoryImpl(JpaEntityInformation<T, ?> entityInformation, EntityManager entityManager) {
            super(entityInformation, entityManager);
            this.entityManager = entityManager;
        }

        @Override
        public void deleteById(ID id) {
            findById(id).ifPresent(entity -> {
                if (entity instanceof Customer c) {
                    c.setDeleted(true); // soft delete instead of a real DELETE
                    entityManager.merge(c);
                }
            });
        }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CustomBaseLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:custombase1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer saved = repo.save(new Customer("Ada"));

        repo.deleteById(saved.getId()); // uses the CUSTOM base class's overridden method

        boolean stillInDatabase = repo.existsById(saved.getId());
        Customer reloaded = repo.findById(saved.getId()).orElseThrow();
        System.out.println("still exists in the table? " + stillInDatabase + ", deleted flag = " + reloaded.isDeleted());

        if (!stillInDatabase) throw new AssertionError("Expected the row to STILL physically exist (soft delete)");
        if (!reloaded.isDeleted()) throw new AssertionError("Expected the deleted flag to be set to true");
        System.out.println("Custom base repository's deleteById override performed a soft delete -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java CustomBaseLevel1.java` on JDK 17+.

`repositoryBaseClass = SoftDeleteRepositoryImpl.class` on `@EnableJpaRepositories` replaces `SimpleJpaRepository` as the base implementation for every repository this configuration scans. `CustomerRepository.deleteById(...)` — a method it never declares itself, inherited from `JpaRepository`/`CrudRepository` — now executes `SoftDeleteRepositoryImpl`'s overridden logic instead of the default hard-delete: the row still physically exists (`existsById` returns `true`), but its `deleted` flag is now `true`.

### Level 2 — Intermediate

Add a second, unrelated entity and repository, confirming the custom base class applies to *both* without any per-repository configuration.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.jpa.repository.support.JpaEntityInformation;
import org.springframework.data.jpa.repository.support.SimpleJpaRepository;

import java.io.Serializable;

@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = CustomBaseLevel2.class, repositoryBaseClass = CustomBaseLevel2.SoftDeleteRepositoryImpl.class)
public class CustomBaseLevel2 {

    public interface SoftDeletable {
        boolean isDeleted();
        void setDeleted(boolean deleted);
    }

    @Entity
    public static class Customer implements SoftDeletable {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean deleted = false;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public Long getId() { return id; }
        public boolean isDeleted() { return deleted; }
        public void setDeleted(boolean deleted) { this.deleted = deleted; }
    }

    @Entity
    public static class Product implements SoftDeletable {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean deleted = false;
        protected Product() {}
        public Product(String name) { this.name = name; }
        public Long getId() { return id; }
        public boolean isDeleted() { return deleted; }
        public void setDeleted(boolean deleted) { this.deleted = deleted; }
    }

    public static class SoftDeleteRepositoryImpl<T, ID extends Serializable> extends SimpleJpaRepository<T, ID> {
        private final EntityManager entityManager;

        public SoftDeleteRepositoryImpl(JpaEntityInformation<T, ?> entityInformation, EntityManager entityManager) {
            super(entityInformation, entityManager);
            this.entityManager = entityManager;
        }

        @Override
        public void deleteById(ID id) {
            findById(id).ifPresent(entity -> {
                if (entity instanceof SoftDeletable sd) {
                    sd.setDeleted(true);
                    entityManager.merge(entity);
                }
            });
        }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}
    public interface ProductRepository extends JpaRepository<Product, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CustomBaseLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:custombase2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository customerRepo = ctx.getBean(CustomerRepository.class);
        ProductRepository productRepo = ctx.getBean(ProductRepository.class);

        Customer customer = customerRepo.save(new Customer("Ada"));
        Product product = productRepo.save(new Product("Widget"));

        customerRepo.deleteById(customer.getId());
        productRepo.deleteById(product.getId());

        Customer reloadedCustomer = customerRepo.findById(customer.getId()).orElseThrow();
        Product reloadedProduct = productRepo.findById(product.getId()).orElseThrow();

        System.out.println("customer soft-deleted? " + reloadedCustomer.isDeleted());
        System.out.println("product soft-deleted? " + reloadedProduct.isDeleted());

        if (!reloadedCustomer.isDeleted() || !reloadedProduct.isDeleted())
            throw new AssertionError("Expected BOTH repositories to apply the soft-delete behavior");
        System.out.println("Custom base class applied identically to two unrelated repositories -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java CustomBaseLevel2.java`.

Neither `CustomerRepository` nor `ProductRepository` mentions `SoftDeleteRepositoryImpl` anywhere in its own declaration — the `repositoryBaseClass` setting on `@EnableJpaRepositories` applies globally to every repository the annotation's scanning covers, which is why both `customerRepo.deleteById(...)` and `productRepo.deleteById(...)` perform a soft delete despite `Customer` and `Product` being entirely unrelated entities.

### Level 3 — Advanced

Additionally override `findById` so that soft-deleted rows are transparently excluded from normal lookups — combining the delete override from Levels 1 and 2 with a matching read-side override, so the soft-delete policy is consistently invisible to ordinary repository callers.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.EntityManager;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.jpa.repository.support.JpaEntityInformation;
import org.springframework.data.jpa.repository.support.SimpleJpaRepository;

import java.io.Serializable;
import java.util.Optional;

@SpringBootApplication
@EnableJpaRepositories(basePackageClasses = CustomBaseLevel3.class, repositoryBaseClass = CustomBaseLevel3.SoftDeleteRepositoryImpl.class)
public class CustomBaseLevel3 {

    public interface SoftDeletable {
        boolean isDeleted();
        void setDeleted(boolean deleted);
    }

    @Entity
    public static class Customer implements SoftDeletable {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private boolean deleted = false;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
        public boolean isDeleted() { return deleted; }
        public void setDeleted(boolean deleted) { this.deleted = deleted; }
    }

    public static class SoftDeleteRepositoryImpl<T, ID extends Serializable> extends SimpleJpaRepository<T, ID> {
        private final EntityManager entityManager;

        public SoftDeleteRepositoryImpl(JpaEntityInformation<T, ?> entityInformation, EntityManager entityManager) {
            super(entityInformation, entityManager);
            this.entityManager = entityManager;
        }

        @Override
        public void deleteById(ID id) {
            findById(id).ifPresent(entity -> {
                if (entity instanceof SoftDeletable sd) {
                    sd.setDeleted(true);
                    entityManager.merge(entity);
                }
            });
        }

        @Override
        public Optional<T> findById(ID id) {
            // Transparently hide soft-deleted rows from normal lookups.
            return super.findById(id).filter(entity ->
                !(entity instanceof SoftDeletable sd) || !sd.isDeleted());
        }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(CustomBaseLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:custombase3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer active = repo.save(new Customer("Ada"));
        Customer toDelete = repo.save(new Customer("Grace"));

        repo.deleteById(toDelete.getId());

        Optional<Customer> foundActive = repo.findById(active.getId());
        Optional<Customer> foundDeleted = repo.findById(toDelete.getId());

        System.out.println("active customer still findable? " + foundActive.isPresent());
        System.out.println("soft-deleted customer findable via findById? " + foundDeleted.isPresent());
        System.out.println("total rows physically in the table (count()) = " + repo.count());

        if (foundActive.isEmpty()) throw new AssertionError("Expected the active customer to still be findable");
        if (foundDeleted.isPresent()) throw new AssertionError("Expected the soft-deleted customer to be hidden from findById");
        if (repo.count() != 2) throw new AssertionError("Expected count() to still see BOTH rows physically (count() wasn't overridden)");

        System.out.println("findById transparently hid the soft-deleted row, while the row still physically exists -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java CustomBaseLevel3.java`.

`findById` is overridden to `.filter(...)` out any entity implementing `SoftDeletable` whose `isDeleted()` is `true` — combined with the `deleteById` override from before, this makes the soft-delete policy consistent and transparent: callers using `findById` genuinely can't tell a soft-deleted row from a truly absent one, exactly matching the semantics of a real `DELETE`. Note `count()` was deliberately *not* overridden here — it still reports `2` (both rows physically present), a reminder that a base-class customization only changes the specific methods you actually override; every other inherited method keeps its default behavior unless deliberately addressed too.

## 6. Walkthrough

Trace Level 3's `repo.findById(toDelete.getId())` call after the soft-delete.

1. **`repo.deleteById(toDelete.getId())`** (from the earlier steps) already ran `SoftDeleteRepositoryImpl`'s overridden `deleteById`, which found the `Grace` customer, set her `deleted` flag to `true`, and merged the change — the row remains physically present in the `customer` table.
2. **`repo.findById(toDelete.getId())`** is called — because `CustomerRepository`'s base implementation is `SoftDeleteRepositoryImpl`, not the default `SimpleJpaRepository`, this invokes the overridden `findById`.
3. **`super.findById(id)`** first calls the *original*, default JPA `findById` logic (via `SimpleJpaRepository`'s own implementation, accessed through `super`), which performs a genuine database lookup and finds the row — Grace's `Customer` entity, with `deleted = true`, is loaded successfully at this point.
4. **`.filter(entity -> ...)`** then applies: the entity is checked — it does implement `SoftDeletable`, and `isDeleted()` returns `true` — so the filter predicate evaluates `false`, and `Optional.filter` converts the previously-present `Optional<Customer>` into an empty one.
5. **Return value**: `findById` returns an empty `Optional<Customer>` to the caller — even though the row genuinely exists in the database and was genuinely loaded a moment ago inside this very method call.
6. **Comparison with `repo.count()`**: since `count()` was never overridden, it uses the original, default `SimpleJpaRepository` counting logic, which has no awareness of the `deleted` flag at all — it reports `2`, both rows, confirming the soft-delete convention is enforced only by the specific methods deliberately customized (`deleteById`, `findById`), not automatically applied everywhere.
7. **Verification**: the program checks the active customer remains findable, the soft-deleted one does not, and the raw physical count still shows both rows — together confirming the base-class customization behaves consistently and only where explicitly implemented.

```
 findById(toDelete.getId())   [overridden in SoftDeleteRepositoryImpl]
        |
        v
 super.findById(id)  -->  Optional[Customer{deleted=true}]   (genuinely found, physically present)
        |
        v
 .filter(entity -> !isDeleted)  -->  predicate FALSE  -->  Optional.empty()
        |
        v
 caller sees: Optional.empty()  -- indistinguishable from "never existed"

 count()   [NOT overridden -- still default SimpleJpaRepository behavior]
        |
        v
 returns 2  -- sees BOTH rows, unaware of the deleted flag
```

## 7. Gotchas & takeaways

> **Gotcha:** overriding one standard method (like `deleteById`) doesn't automatically make *related* standard methods consistent with it — as Level 3's `count()` result shows, every method that should respect the soft-delete convention needs its own explicit override. A common, easy-to-miss gap: overriding `findById` and `findAll()` but forgetting `findAllById(Iterable<ID>)` or `existsById`, leaving those particular inherited methods still seeing soft-deleted rows.

- Customizing the base repository (via `repositoryBaseClass`) changes the *default implementation* of standard methods across every repository in the application at once — distinct from the previous card's fragments, which add *extra* methods to one repository at a time.
- The custom base class extends the store's own default implementation (`SimpleJpaRepository` for JPA) and overrides only the specific methods that need different behavior — every method not explicitly overridden keeps the original default behavior.
- `@EnableJpaRepositories(repositoryBaseClass = ...)` is the single configuration point that applies this custom base class to every repository the annotation's scanning covers — no per-repository opt-in is needed or possible with this mechanism.
- When implementing cross-cutting behavior like soft-delete, be deliberate about exactly which inherited methods need overriding to keep the policy consistent — as demonstrated, overriding `deleteById` alone leaves other read/count methods unaware of the convention unless they're addressed too.
