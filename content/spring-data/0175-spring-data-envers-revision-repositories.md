---
card: spring-data
gi: 175
slug: spring-data-envers-revision-repositories
title: "Spring Data Envers (revision repositories)"
---

## 1. What it is

Spring Data Envers integrates Hibernate Envers — a JPA auditing library that records every historical revision of an entity — with Spring Data's repository abstraction, via `RevisionRepository`. Where `@Version` (an earlier card) only detects that a concurrent change happened, Envers keeps the *entire history* of every change, queryable as a sequence of revisions.

```java
interface CustomerRepository extends JpaRepository<Customer, String>,
        RevisionRepository<Customer, String, Integer> {
}

Revisions<Integer, Customer> history = customerRepository.findRevisions("c1");
```

## 2. Why & when

Optimistic locking answers "did someone else change this since I last read it?" Envers answers a different question entirely: "what did this record look like at every point in its history, and who changed what, when?" That's a genuinely different capability — full audit trail and point-in-time reconstruction, not just conflict detection.

Reach for Spring Data Envers when:

- Regulatory or compliance requirements demand a full audit trail of every change to certain entities, not just the current state.
- You need to answer "what was this record's value at revision N" or "show me every change ever made to this entity" — not achievable by keeping just a `version` counter.
- The entity is JPA-backed (Envers is a Hibernate/JPA feature), and the audit requirement is significant enough to justify the extra revision tables Envers creates.

## 3. Core concept

```
 @Entity
 @Audited
 class Customer {
     @Id String id;
     String name, email;
 }

 Every INSERT/UPDATE/DELETE on Customer
   -> also writes a row to Customer_AUD (the revision table)
   -> tagged with a revision number and a REVTYPE (ADD / MOD / DEL)

 customerRepository.findRevisions("c1")
   -> Revisions<Integer, Customer>: every historical version of customer c1, in order
```

Every write to an `@Audited` entity is mirrored into a parallel revision table, building up a full timeline that the repository can query back out.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each write to the main Customer table also appends a row to a parallel Customer_AUD revision table">
  <rect x="30" y="20" width="220" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Customer (current state)</text>
  <text x="140" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">id=c1</text>
  <text x="140" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">name=Amara Okafor</text>

  <line x1="250" y1="70" x2="330" y2="70" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a10)"/>
  <text x="290" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">mirrored</text>

  <rect x="340" y="20" width="270" height="110" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Customer_AUD (revision history)</text>
  <text x="475" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">rev=1, ADD, name=Amara</text>
  <text x="475" y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">rev=2, MOD, name=Amara Okafor</text>

  <defs><marker id="a10" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The main table always shows current state; the revision table accumulates every historical version.

## 5. Runnable example

The scenario: tracking a customer's full change history, evolving from unaudited saves that lose all history, to `@Audited` entities with revisions recorded automatically, to querying that history back out through `findRevisions` and reconstructing the entity as it looked at a specific past revision.

### Level 1 — Basic

Show the unaudited baseline: every save overwrites the previous state, with no history retained.

```java
import java.util.*;

public class EnversLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("c1", "Amara", "amara@old.example"));
        repo.save(new Customer("c1", "Amara", "amara@new.example")); // overwrites -- old email is GONE
        repo.save(new Customer("c1", "Amara Okafor", "amara@new.example")); // overwrites again

        Customer current = repo.findById("c1");
        System.out.println("Current: " + current.name + " <" + current.email + ">");
        // No way to answer "what was her email before this last change?" -- history was never kept.
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

interface CustomerRepository {
    Customer save(Customer c);
    Customer findById(String id);
}

class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> table = new HashMap<>();
    public Customer save(Customer c) { table.put(c.id, c); return c; } // plain overwrite, no history
    public Customer findById(String id) { return table.get(id); }
}
```

How to run: `java EnversLevel1.java`

Every save simply replaces the row — after three saves, only the final state is visible; the two earlier states are unrecoverable, which is exactly the gap Envers closes.

### Level 2 — Intermediate

Add revision tracking: every save also appends a snapshot to a parallel revision list, tagged with a revision number and change type.

```java
import java.util.*;

public class EnversLevel2 {
    public static void main(String[] args) {
        AuditedCustomerRepository repo = new AuditedCustomerRepository();
        repo.save(new Customer("c1", "Amara", "amara@old.example"));                 // rev 1, ADD
        repo.save(new Customer("c1", "Amara", "amara@new.example"));                 // rev 2, MOD
        repo.save(new Customer("c1", "Amara Okafor", "amara@new.example"));          // rev 3, MOD

        List<Revision> history = repo.findRevisions("c1"); // now the FULL history is recoverable
        for (Revision r : history) {
            System.out.println("rev=" + r.revisionNumber + " " + r.type + " name=" + r.snapshot.name + " email=" + r.snapshot.email);
        }
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

class Revision {
    int revisionNumber; String type; Customer snapshot;
    Revision(int revisionNumber, String type, Customer snapshot) { this.revisionNumber = revisionNumber; this.type = type; this.snapshot = snapshot; }
}

// Stands in for a Spring Data Envers RevisionRepository over an @Audited JPA entity.
class AuditedCustomerRepository {
    private final Map<String, Customer> current = new HashMap<>();
    private final Map<String, List<Revision>> revisionsById = new HashMap<>();
    private int nextRevision = 1;

    Customer save(Customer c) {
        boolean isNew = !current.containsKey(c.id);
        current.put(c.id, c);
        revisionsById.computeIfAbsent(c.id, k -> new ArrayList<>())
            .add(new Revision(nextRevision++, isNew ? "ADD" : "MOD", copyOf(c)));
        return c;
    }
    Customer findById(String id) { return current.get(id); }
    List<Revision> findRevisions(String id) { return revisionsById.getOrDefault(id, List.of()); }
    private Customer copyOf(Customer c) { return new Customer(c.id, c.name, c.email); }
}
```

How to run: `java EnversLevel2.java`

Each `save` call, in addition to updating `current`, appends an immutable snapshot to that entity's revision list — `findRevisions("c1")` now returns all three historical states, in order, each tagged with its revision number and whether it was an `ADD` or a `MOD`.

### Level 3 — Advanced

Add "as of revision N" reconstruction and a `DEL` revision type — the full capability set: full history, point-in-time lookup, and tombstoning a deletion into the history rather than erasing it.

```java
import java.util.*;

public class EnversLevel3 {
    public static void main(String[] args) {
        AuditedCustomerRepository repo = new AuditedCustomerRepository();
        repo.save(new Customer("c1", "Amara", "amara@old.example"));         // rev 1, ADD
        repo.save(new Customer("c1", "Amara", "amara@new.example"));         // rev 2, MOD
        repo.save(new Customer("c1", "Amara Okafor", "amara@new.example"));  // rev 3, MOD
        repo.delete("c1");                                                    // rev 4, DEL

        Customer asOfRev2 = repo.findRevision("c1", 2);
        System.out.println("As of revision 2: name=" + asOfRev2.name + " email=" + asOfRev2.email);

        System.out.println("Current state: " + repo.findById("c1")); // null -- entity was deleted
        System.out.println("Full history:");
        for (Revision r : repo.findRevisions("c1")) {
            System.out.println("  rev=" + r.revisionNumber + " " + r.type
                + (r.snapshot != null ? " name=" + r.snapshot.name : ""));
        }
    }
}

class Customer {
    String id, name, email;
    Customer(String id, String name, String email) { this.id = id; this.name = name; this.email = email; }
}

class Revision {
    int revisionNumber; String type; Customer snapshot; // snapshot is null for DEL revisions
    Revision(int revisionNumber, String type, Customer snapshot) { this.revisionNumber = revisionNumber; this.type = type; this.snapshot = snapshot; }
}

class AuditedCustomerRepository {
    private final Map<String, Customer> current = new HashMap<>();
    private final Map<String, List<Revision>> revisionsById = new HashMap<>();
    private int nextRevision = 1;

    Customer save(Customer c) {
        boolean isNew = !current.containsKey(c.id);
        current.put(c.id, c);
        revisionsById.computeIfAbsent(c.id, k -> new ArrayList<>())
            .add(new Revision(nextRevision++, isNew ? "ADD" : "MOD", copyOf(c)));
        return c;
    }
    void delete(String id) {
        current.remove(id);
        revisionsById.computeIfAbsent(id, k -> new ArrayList<>())
            .add(new Revision(nextRevision++, "DEL", null)); // tombstone: history preserved, current state gone
    }
    Customer findById(String id) { return current.get(id); }
    List<Revision> findRevisions(String id) { return revisionsById.getOrDefault(id, List.of()); }
    Customer findRevision(String id, int revisionNumber) {
        for (Revision r : revisionsById.getOrDefault(id, List.of())) {
            if (r.revisionNumber == revisionNumber) return r.snapshot;
        }
        return null;
    }
    private Customer copyOf(Customer c) { return new Customer(c.id, c.name, c.email); }
}
```

How to run: `java EnversLevel3.java`

`findRevision("c1", 2)` reconstructs exactly what the entity looked like at revision 2 — after the email changed but before the name did — even though the entity has since been deleted entirely. `delete` appends a `DEL` revision with a `null` snapshot instead of erasing the history, so the full timeline (`ADD` -> `MOD` -> `MOD` -> `DEL`) remains queryable forever.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three saves build up revisions 1 through 3, then `repo.delete("c1")` removes the entity from `current` but appends a fourth, `DEL`-typed revision rather than removing anything from `revisionsById`.

`repo.findRevision("c1", 2)` scans the revision list for the entry tagged `revisionNumber == 2` and returns its snapshot — the state after the email change but before the name change:

```
As of revision 2: name=Amara email=amara@new.example
Current state: null
Full history:
  rev=1 ADD name=Amara
  rev=2 MOD name=Amara
  rev=3 MOD name=Amara Okafor
  rev=4 DEL
```

In a real Spring Data Envers setup, `findRevisions` returns a `Revisions<Integer, Customer>` object, and `Revision` metadata additionally carries a timestamp and, if `@RevisionEntity` is customized, the authenticated user who made the change — giving a "who changed what, when" trail that's queryable per-entity, entirely independent of the entity's current row, which may no longer even exist.

## 7. Gotchas & takeaways

> Gotcha: `@Audited` only tracks entities explicitly annotated with it — forgetting the annotation on an entity that compliance requirements say must be audited is a silent gap that only surfaces when someone actually needs the history and finds none was ever recorded.

> Gotcha: Envers' revision tables grow without bound by default — every single change to every audited entity adds a permanent row, and there's no built-in pruning; a high-write-volume audited entity can accumulate a revision table many times larger than its current-state table over time.

- Spring Data Envers answers "what was this entity's full history" — a fundamentally different question from optimistic locking's "did someone else change this since I read it."
- Every write to an `@Audited` entity mirrors into a parallel revision table, tagged with a revision number and change type (`ADD`/`MOD`/`DEL`).
- `findRevisions` returns the full timeline; a specific past revision can be reconstructed even after the entity's current row has been deleted.
- Revision tables grow unbounded and need their own retention/archival strategy for high-write entities — Envers itself doesn't prune history automatically.
