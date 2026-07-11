---
card: spring-data
gi: 169
slug: auditing
title: "Auditing"
---

## 1. What it is

Auditing in Spring Data Neo4j automatically populates "who created/modified this node and when" fields — `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy` — every time a node is saved, without the application writing that bookkeeping code itself. The same annotations and behavior seen for MongoDB and JPA earlier in this course apply here, unchanged.

```java
@Node
class Customer {
    @Id String id;
    String name;

    @CreatedDate Instant createdAt;
    @LastModifiedDate Instant updatedAt;
}
```

## 2. Why & when

Almost every persisted entity ends up needing "when was this created" and "when was it last touched" fields somewhere — for debugging, for compliance, for cache invalidation. Writing `entity.setUpdatedAt(Instant.now())` before every save is easy to forget in exactly the one code path where it matters; auditing support makes it automatic and consistent.

Reach for auditing when:

- Every (or most) `@Node` entities need creation/modification timestamps, and manual timestamp-setting risks being missed on some code path.
- You also need to record *who* made the change (`@CreatedBy`/`@LastModifiedBy`), tying persistence into the application's security/authentication context.
- You want this to work uniformly whether the save happened through a repository method, a template call, or a custom fragment.

## 3. Core concept

```
 @EnableNeo4jAuditing                          -- turns auditing on for the whole application

 @Node
 class Customer {
     @CreatedDate Instant createdAt;             -- set once, on first save
     @LastModifiedDate Instant updatedAt;         -- set on every save
     @CreatedBy String createdBy;                  -- from an AuditorAware<String> bean
     @LastModifiedBy String lastModifiedBy;
 }

 repository.save(customer)
   -> auditing listener intercepts BEFORE the write
   -> populates createdAt/updatedAt/createdBy/lastModifiedBy
   -> THEN the node is written to the graph
```

Auditing runs as a listener hooked into the save lifecycle — it fills in the annotated fields just before the actual Cypher write happens.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A save call passes through an auditing listener that stamps timestamps and author fields before the write reaches the graph">
  <rect x="20" y="45" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">repo.save(customer)</text>

  <line x1="170" y1="70" x2="220" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a6)"/>

  <rect x="230" y="45" width="180" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="68" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Auditing listener</text>
  <text x="320" y="83" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">stamps createdAt/By etc.</text>

  <line x1="410" y1="70" x2="460" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a6)"/>

  <rect x="470" y="45" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="545" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Cypher write</text>

  <defs><marker id="a6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The auditing listener stamps the annotated fields before the save reaches the graph, on every call.

## 5. Runnable example

The scenario: tracking creation and modification metadata on a `Customer` node, evolving from manually-set timestamps, to automatic `@CreatedDate`/`@LastModifiedDate` auditing, to full auditing including `@CreatedBy`/`@LastModifiedBy` sourced from a security-context-backed `AuditorAware`.

### Level 1 — Basic

Show the manual, error-prone baseline: setting timestamps by hand before every save.

```java
import java.time.*;
import java.util.*;

public class AuditingLevel1 {
    public static void main(String[] args) throws InterruptedException {
        CustomerRepository repo = new CustomerRepositoryImpl();

        Customer amara = new Customer("c1", "Amara");
        amara.createdAt = Instant.now(); // manual -- easy to forget on some code path
        amara.updatedAt = amara.createdAt;
        repo.save(amara);

        Thread.sleep(10);
        amara.name = "Amara Okafor";
        amara.updatedAt = Instant.now(); // manual again -- and this line is easy to miss
        repo.save(amara);

        Customer found = repo.findById("c1");
        System.out.println("createdAt=" + found.createdAt + " updatedAt=" + found.updatedAt);
    }
}

class Customer {
    String id, name;
    Instant createdAt, updatedAt;
    Customer(String id, String name) { this.id = id; this.name = name; }
}

interface CustomerRepository {
    Customer save(Customer c);
    Customer findById(String id);
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public Customer save(Customer c) { nodes.put(c.id, c); return c; }
    public Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java AuditingLevel1.java`

Every call site that saves a `Customer` must remember to set `updatedAt` correctly — miss it once, on one rarely-exercised code path, and that entity's audit trail silently goes stale.

### Level 2 — Intermediate

Add an auditing listener that automatically stamps `createdAt`/`updatedAt` on every save, removing the manual bookkeeping.

```java
import java.time.*;
import java.util.*;

public class AuditingLevel2 {
    public static void main(String[] args) throws InterruptedException {
        CustomerRepository repo = new CustomerRepositoryImpl();

        Customer amara = new Customer("c1", "Amara"); // no manual timestamps at all
        repo.save(amara);

        Thread.sleep(10);
        amara.name = "Amara Okafor";
        repo.save(amara); // updatedAt refreshed automatically, createdAt untouched

        Customer found = repo.findById("c1");
        System.out.println("createdAt=" + found.createdAt + " updatedAt=" + found.updatedAt);
    }
}

class Customer {
    String id, name;
    // @CreatedDate
    Instant createdAt;
    // @LastModifiedDate
    Instant updatedAt;
    Customer(String id, String name) { this.id = id; this.name = name; }
}

interface CustomerRepository {
    Customer save(Customer c);
    Customer findById(String id);
}

// @EnableNeo4jAuditing wires a listener that runs this stamping logic before every write.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> nodes = new HashMap<>();
    public Customer save(Customer c) {
        Instant now = Instant.now();
        if (c.createdAt == null) c.createdAt = now; // only stamped once, on first save
        c.updatedAt = now;                             // stamped on every save
        nodes.put(c.id, c);
        return c;
    }
    public Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java AuditingLevel2.java`

`createdAt` is only set when it's still `null` (first save), while `updatedAt` is set unconditionally on every save — exactly the semantics `@CreatedDate` and `@LastModifiedDate` provide automatically once `@EnableNeo4jAuditing` is turned on, with zero manual timestamp code left in application logic.

### Level 3 — Advanced

Add `@CreatedBy`/`@LastModifiedBy`, sourced from an `AuditorAware<String>` standing in for the currently authenticated user — the piece that ties persistence auditing into the application's security context.

```java
import java.time.*;
import java.util.*;

public class AuditingLevel3 {
    public static void main(String[] args) throws InterruptedException {
        AuditorAware currentUser = new ThreadLocalAuditorAware();
        CustomerRepositoryImpl repo = new CustomerRepositoryImpl(currentUser);

        currentUser.setCurrentAuditor("amara@example.com");
        Customer amara = new Customer("c1", "Amara");
        repo.save(amara);

        Thread.sleep(10);
        currentUser.setCurrentAuditor("admin@example.com"); // a different user modifies the record
        amara.name = "Amara Okafor";
        repo.save(amara);

        Customer found = repo.findById("c1");
        System.out.println("createdBy=" + found.createdBy + " lastModifiedBy=" + found.lastModifiedBy);
        System.out.println("createdAt=" + found.createdAt + " updatedAt=" + found.updatedAt);
    }
}

class Customer {
    String id, name;
    Instant createdAt, updatedAt;   // @CreatedDate / @LastModifiedDate
    String createdBy, lastModifiedBy; // @CreatedBy / @LastModifiedBy
    Customer(String id, String name) { this.id = id; this.name = name; }
}

// Stands in for org.springframework.data.domain.AuditorAware<String>.
interface AuditorAware {
    String getCurrentAuditor();
    void setCurrentAuditor(String auditor);
}

class ThreadLocalAuditorAware implements AuditorAware {
    private String current;
    public String getCurrentAuditor() { return current; }
    public void setCurrentAuditor(String auditor) { this.current = auditor; }
}

class CustomerRepositoryImpl {
    private final Map<String, Customer> nodes = new HashMap<>();
    private final AuditorAware auditorAware;
    CustomerRepositoryImpl(AuditorAware auditorAware) { this.auditorAware = auditorAware; }

    public Customer save(Customer c) {
        Instant now = Instant.now();
        String auditor = auditorAware.getCurrentAuditor();
        if (c.createdAt == null) { c.createdAt = now; c.createdBy = auditor; } // stamped once
        c.updatedAt = now;
        c.lastModifiedBy = auditor; // stamped every save, reflecting whoever is currently authenticated
        nodes.put(c.id, c);
        return c;
    }
    public Customer findById(String id) { return nodes.get(id); }
}
```

How to run: `java AuditingLevel3.java`

`createdBy` is stamped once, from whoever was the current auditor at creation time (`amara@example.com`), and never changes again. `lastModifiedBy` is re-stamped on every save with whoever is currently authenticated at that moment — here, `admin@example.com` on the second save — giving a full "who created it, who touched it last" trail with no manual code in the business logic.

## 6. Walkthrough

Execution starts in `main` for Level 3. `currentUser.setCurrentAuditor("amara@example.com")` simulates Amara being the authenticated user, then `repo.save(amara)` runs: `createdAt`/`createdBy` are both null-checked and stamped for the first time, `updatedAt`/`lastModifiedBy` are stamped unconditionally to the same values.

After a short delay, the auditor changes to `admin@example.com` and `amara.name` is edited before a second `repo.save(amara)`. This time `createdAt`/`createdBy` are already non-null, so they're left untouched; `updatedAt` gets a new, later `Instant`, and `lastModifiedBy` flips to `admin@example.com`:

```
createdBy=amara@example.com lastModifiedBy=admin@example.com
createdAt=2026-... updatedAt=2026-...   (updatedAt strictly later than createdAt)
```

In a real Spring Data Neo4j application, `AuditorAware<String>` would typically read `SecurityContextHolder.getContext().getAuthentication().getName()` instead of a hand-set field, so `@CreatedBy`/`@LastModifiedBy` reflect whichever user's request triggered the save — the listener runs identically whether the save came from a repository `save()` call, a `Neo4jTemplate` call, or a custom fragment, because it hooks into the shared save lifecycle, not any one API surface.

## 7. Gotchas & takeaways

> Gotcha: auditing only fires through Spring Data's managed save lifecycle — a raw `@Query` `CREATE`/`MERGE` statement that writes a node directly bypasses the auditing listener entirely, leaving `createdAt`/`updatedAt` unset unless the Cypher itself sets them.

> Gotcha: forgetting `@EnableNeo4jAuditing` on a configuration class is a common silent failure — the `@CreatedDate`/`@LastModifiedDate` annotations are simply ignored with no error, and every timestamp field stays `null` until someone notices in production.

- `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy` work identically here to how they work for MongoDB and JPA earlier in this course — Spring Data's auditing abstraction is shared across modules.
- Auditing runs as a listener in the save lifecycle, so it applies uniformly across repository saves, template saves, and custom fragments — but only for calls that actually go through that lifecycle.
- `@CreatedBy`/`@LastModifiedBy` need an `AuditorAware` bean, typically backed by the security context, to know "who" is making the change.
- Hand-written `@Query` writes bypass auditing — timestamps and author fields must be set explicitly in the Cypher, or handled another way, if a save path uses raw queries.
