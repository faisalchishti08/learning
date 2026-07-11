---
card: spring-data
gi: 149
slug: auditing
title: "Auditing"
---

## 1. What it is

`@EnableElasticsearchAuditing` brings the same auditing model already seen for MongoDB in this course — `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy` — to Elasticsearch documents: fields automatically stamped on every save, without any repository method needing to set them by hand.

```java
@Document(indexName = "orders")
class Order {
    @Id String id;
    @CreatedDate Instant createdAt;
    @LastModifiedDate Instant updatedAt;
    @CreatedBy String createdBy;
    @LastModifiedBy String updatedBy;
}

@Configuration
@EnableElasticsearchAuditing
class ElasticsearchConfig { }
```

## 2. Why & when

Just as the MongoDB auditing card established, every document that matters usually needs a reliable answer to "when was this created, and by whom, and when/by whom was it last changed" — and hand-setting these fields at every save call site is repetitive and easy to forget in exactly one code path. `@EnableElasticsearchAuditing` centralizes this, applying to every save through `ElasticsearchOperations` or a generated `ElasticsearchRepository`, consistently.

Reach for `@EnableElasticsearchAuditing` when:

- Every document in an index needs consistent `createdAt`/`updatedAt` timestamps, and you want that guaranteed centrally rather than dependent on every service method remembering to set them.
- You need to know *who* made a change — `@CreatedBy`/`@LastModifiedBy`, resolved through an `AuditorAware` bean (typically backed by Spring Security's context), for accountability or an audit trail.
- You're combining Elasticsearch as a search-optimized read layer alongside a primary datastore (a common architecture — Elasticsearch as a secondary, search-focused index of data whose source of truth lives elsewhere), and want the search index's own metadata (when was this indexed/reindexed, by which sync process) tracked consistently.

## 3. Core concept

```
 elasticsearchOperations.save(order)  (or orderRepository.save(order))
        |
        v
  Auditing logic runs automatically BEFORE the document is indexed
        |
        +-- if new document: set createdAt = now, createdBy = currentAuditor
        +-- always:          set updatedAt = now, updatedBy = currentAuditor
        |
        v
  document is indexed into Elasticsearch with the audit fields already populated
```

The mechanism mirrors MongoDB's `@EnableMongoAuditing` exactly — same annotations, same "runs automatically before every save" behavior — just applied to Elasticsearch's indexing pipeline instead.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A save call passes through automatic auditing logic that stamps createdAt/updatedAt/createdBy/updatedBy before the document is indexed">
  <rect x="20" y="55" width="150" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">repository.save(order)</text>

  <rect x="240" y="55" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="78" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">auditing logic</text>
  <text x="330" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stamps createdAt/updatedAt/...</text>

  <rect x="490" y="55" width="130" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="555" y="82" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">indexed</text>

  <line x1="170" y1="77" x2="235" y2="77" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="420" y1="77" x2="485" y2="77" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Auditing sits transparently between every save call and the actual indexing operation — no caller has to invoke it explicitly.

## 5. Runnable example

The scenario: stamping audit metadata on order documents automatically, evolving from basic `createdAt`/`updatedAt` timestamping, to also tracking who made each change via an `AuditorAware`-style resolver, to combining auditing with the earlier index-management card's reindex migration — showing audit fields survive a reindex correctly.

### Level 1 — Basic

Model automatic `createdAt`/`updatedAt` stamping on every save.

```java
import java.time.*;
import java.util.*;

public class ElasticAuditingLevel1 {
    public static void main(String[] args) throws InterruptedException {
        OrderRepository repo = new OrderRepository();
        Order order = new Order("1", "PENDING");

        repo.save(order);
        System.out.println("Created at: " + order.createdAt);

        Thread.sleep(10);
        order.status = "SHIPPED";
        repo.save(order);
        System.out.println("Created at (unchanged): " + order.createdAt);
        System.out.println("Updated at (changed):   " + order.updatedAt);
    }
}

class Order { String id; String status; Instant createdAt; Instant updatedAt; Order(String id, String status) { this.id = id; this.status = status; } }

// Stands in for a repository configured with @EnableElasticsearchAuditing.
class OrderRepository {
    Map<String, Order> index = new HashMap<>();

    void save(Order order) {
        if (order.createdAt == null) order.createdAt = Instant.now(); // only stamped ONCE, on first save
        order.updatedAt = Instant.now();                              // stamped on EVERY save
        index.put(order.id, order);
    }
}
```

How to run: `java ElasticAuditingLevel1.java`

`save` checks whether `createdAt` is already set before stamping it (so it's only assigned once), while `updatedAt` is refreshed unconditionally on every save — mirroring exactly how `@EnableElasticsearchAuditing` handles `@CreatedDate`/`@LastModifiedDate` automatically, without any of this logic living in application service code.

### Level 2 — Intermediate

Add `createdBy`/`updatedBy`, resolved through an `AuditorAware`-style current-user supplier — matching how a real deployment ties auditing to the currently authenticated user.

```java
import java.time.*;
import java.util.*;

public class ElasticAuditingLevel2 {
    public static void main(String[] args) {
        List<String> loggedInAs = new ArrayList<>(List.of("alice", "bob"));
        AuditorAware auditorAware = () -> loggedInAs.remove(0);

        OrderRepository repo = new OrderRepository(auditorAware);
        Order order = new Order("1", "PENDING");

        repo.save(order); // "alice" creates it
        System.out.println("Created by: " + order.createdBy + ", updated by: " + order.updatedBy);

        order.status = "SHIPPED";
        repo.save(order); // "bob" updates it
        System.out.println("Created by (unchanged): " + order.createdBy);
        System.out.println("Updated by (changed):   " + order.updatedBy);
    }
}

class Order { String id; String status; Instant createdAt; Instant updatedAt; String createdBy; String updatedBy; Order(String id, String status) { this.id = id; this.status = status; } }

// stands in for org.springframework.data.domain.AuditorAware<String>
interface AuditorAware { String getCurrentAuditor(); }

class OrderRepository {
    Map<String, Order> index = new HashMap<>();
    private final AuditorAware auditorAware;
    OrderRepository(AuditorAware auditorAware) { this.auditorAware = auditorAware; }

    void save(Order order) {
        String currentUser = auditorAware.getCurrentAuditor();
        if (order.createdAt == null) { order.createdAt = Instant.now(); order.createdBy = currentUser; }
        order.updatedAt = Instant.now();
        order.updatedBy = currentUser;
        index.put(order.id, order);
    }
}
```

How to run: `java ElasticAuditingLevel2.java`

`auditorAware.getCurrentAuditor()` stands in for resolving the currently authenticated user (typically from Spring Security's context) — returning `"alice"` on the first call and `"bob"` on the second, simulating two saves performed by different users. `createdBy` is stamped once and never changes; `updatedBy` reflects whoever performed the most recent save, exactly mirroring `@CreatedBy`/`@LastModifiedBy`'s behavior.

### Level 3 — Advanced

Combine auditing with the earlier index-management card's reindex pattern: confirm audit fields survive a reindex into a corrected-mapping index unchanged, since a reindex copies existing document data (including its audit metadata) rather than treating documents as newly created.

```java
import java.time.*;
import java.util.*;

public class ElasticAuditingLevel3 {
    public static void main(String[] args) {
        AuditorAware auditorAware = () -> "migration-service"; // fixed auditor for THIS demo's simplicity

        OrderRepository oldIndex = new OrderRepository(auditorAware);
        Order order = new Order("1", "PENDING");
        oldIndex.save(order); // original creation -- audit fields stamped ONCE, here

        Instant originalCreatedAt = order.createdAt;
        String originalCreatedBy = order.createdBy;

        System.out.println("Original: createdAt=" + originalCreatedAt + ", createdBy=" + originalCreatedBy);

        // Reindex: copy the EXISTING document (with its EXISTING audit fields) into a new index -- NOT a fresh save().
        OrderRepository newIndex = new OrderRepository(auditorAware);
        newIndex.index.put(order.id, order); // direct copy -- bypasses save()'s "stamp if new" logic entirely

        Order reindexed = newIndex.index.get("1");
        System.out.println("After reindex: createdAt=" + reindexed.createdAt + ", createdBy=" + reindexed.createdBy);
        System.out.println("Audit fields preserved: "
            + (reindexed.createdAt.equals(originalCreatedAt) && reindexed.createdBy.equals(originalCreatedBy)));
    }
}

class Order { String id; String status; Instant createdAt; Instant updatedAt; String createdBy; Order(String id, String status) { this.id = id; this.status = status; } }

interface AuditorAware { String getCurrentAuditor(); }

class OrderRepository {
    Map<String, Order> index = new HashMap<>();
    private final AuditorAware auditorAware;
    OrderRepository(AuditorAware auditorAware) { this.auditorAware = auditorAware; }

    void save(Order order) {
        String currentUser = auditorAware.getCurrentAuditor();
        if (order.createdAt == null) { order.createdAt = Instant.now(); order.createdBy = currentUser; }
        index.put(order.id, order);
    }
}
```

How to run: `java ElasticAuditingLevel3.java`

`oldIndex.save(order)` stamps `createdAt`/`createdBy` once, as a genuine new document. The reindex step deliberately does **not** call `newIndex.save(order)` — it copies the already-audited document object directly into `newIndex.index`, exactly mirroring how Elasticsearch's real `_reindex` API copies existing `_source` documents (audit fields and all) into a new index, rather than treating each copied document as newly created. The final check confirms the audit metadata is identical before and after the reindex — a genuine reindex should never reset a document's original creation audit trail.

## 6. Walkthrough

Execution starts in `main` for Level 3. `oldIndex.save(order)` stamps `order.createdAt` to the current time and `order.createdBy` to `"migration-service"`, since `order.createdAt` was `null` beforehand — this is the one and only time this document goes through `save`'s "is this new?" check. `originalCreatedAt`/`originalCreatedBy` capture these values for later comparison.

The reindex step constructs a `newIndex` `OrderRepository`, then directly calls `newIndex.index.put(order.id, order)` — bypassing `save()` entirely. This models the real distinction between "saving a document through the application" (which triggers auditing logic) and "reindexing a document's existing `_source`" (which is a low-level copy operation that Elasticsearch's `_reindex` API performs without invoking any application-level save logic or auditing hooks at all).

`reindexed = newIndex.index.get("1")` retrieves the copied document, and the final check compares its `createdAt`/`createdBy` against the values captured before the reindex — since the same object reference was copied directly, they're identical by construction, confirming that the audit trail survived the reindex unchanged.

```
Original: createdAt=2026-07-11T..., createdBy=migration-service
After reindex: createdAt=2026-07-11T..., createdBy=migration-service
Audit fields preserved: true
```

In a real Elasticsearch migration, using the native `_reindex` API (rather than reading each document into the application and calling `save()` again) is precisely what preserves original audit metadata correctly — if a migration script instead fetched every document and passed it through a normal `save()` call, and that `save()`'s auditing logic incorrectly treated the document as "new" (for instance, if the migration script cleared `createdAt` first), the original creation history would be lost. This is a real, easy-to-make mistake when combining auditing with any bulk reindex or data-migration process.

## 7. Gotchas & takeaways

> Gotcha: a data migration or reindex script that constructs documents from scratch (rather than genuinely copying existing `_source` data) and then calls `save()` will have its auditing logic treat every migrated document as brand new — silently overwriting original `createdAt`/`createdBy` history with the migration's own timestamp and identity. Use Elasticsearch's native `_reindex` API for genuine reindexing, not a save-every-document-again application-level loop.

> Gotcha: exactly as with the earlier MongoDB auditing card, `@CreatedBy`/`@LastModifiedBy` require an `AuditorAware` bean to be registered — without one, those two fields are silently left `null` even though `@CreatedDate`/`@LastModifiedDate` continue to work correctly on their own.

- `@EnableElasticsearchAuditing` brings the same `@CreatedDate`/`@LastModifiedDate`/`@CreatedBy`/`@LastModifiedBy` model already established for MongoDB to Elasticsearch documents, applied automatically on every save.
- `@CreatedBy`/`@LastModifiedBy` require an `AuditorAware` bean resolving the current user, typically from the security context.
- A genuine reindex (via Elasticsearch's `_reindex` API) preserves existing audit metadata by copying `_source` directly; routing migrated documents back through application-level `save()` calls risks resetting that history.
- Centralizing audit logic through the framework, rather than per-service-method, guarantees consistency across every save path — exactly the same benefit this pattern provided for MongoDB.
