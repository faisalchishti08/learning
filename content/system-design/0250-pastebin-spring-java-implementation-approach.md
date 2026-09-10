---
card: system-design
gi: 250
slug: pastebin-spring-java-implementation-approach
title: Pastebin — Spring/Java implementation approach
---

## 1. What it is

This page covers the **Spring/Java implementation approach** facet of the **Pastebin** case study — how the [API design](0245-pastebin-api-design.md)'s preview-then-reveal endpoints, the [data model](0247-pastebin-data-model-schema.md)'s metadata/blob split, and the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md)'s idempotent cleanup become a real Spring Boot service.

## 2. Why & when

This is the natural closing point of the Pastebin case study, turning every earlier facet's design decisions into working code — with particular attention to correctly implementing the burn-after-reading preview/reveal split, since that is the one place this system's API design differs most sharply from a typical CRUD service.

## 3. Core concept

- **`PasteController` — a `@RestController`** exposing `POST /api/pastes`, `GET /api/pastes/{id}` (preview-only for burn-after-reading), and `POST /api/pastes/{id}/reveal`, mirroring [API design](0245-pastebin-api-design.md) directly.
- **`PasteService` — a `@Service`** coordinating both stores: writes to blob storage, then metadata (on creation, per [high-level architecture](0246-pastebin-high-level-architecture.md)'s ordering); on reveal, reads content, then deletes blob, then updates metadata (per the same ordering discipline).
- **`BlobStorageClient` — a thin wrapper interface** around the actual object storage SDK, kept as an interface (following [hexagonal architecture](0198-hexagonal-ports-and-adapters.md) principles) so `PasteService`'s logic can be tested without a real object store.
- **`PasteRepository` — Spring Data over the `paste` metadata table**, providing `findById`, `save`, and a query for expired/burned rows.
- **`@Scheduled` expiration sweeper**, implementing the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md)'s idempotent, state-machine-based cleanup as a periodically-triggered Spring bean method.

## 4. Diagram

```
   Client
     |
     v
  +--------------------------+
  |     PasteController        |   @RestController
  |  POST /api/pastes           |
  |  GET  /api/pastes/{id}        |
  |  POST /api/pastes/{id}/reveal   |
  +-------------+--------------+
                |
                v
  +--------------------------+
  |      PasteService           |   @Service
  |  - create(): blob, then meta  |
  |  - preview(): meta only         |
  |  - reveal(): read, delete blob,  |
  |    update meta (in that order)     |
  +------+----------+-----------+
         |            |
         v            v
  +------------+  +----------------+
  | PasteRepo   |  | BlobStorageClient|
  | (Spring Data)|  | (interface,       |
  |             |  |  hexagonal-style)   |
  +------------+  +----------------+
                            |
                            v
                       Object Storage

  +--------------------------+
  |   ExpirationSweeper         |   @Scheduled
  |  - claims batches            |
  |  - runs the state machine     |
  |    from the deep-dive facet    |
  +--------------------------+
```
*Caption: `PasteService` is where the two-store coordination and ordering discipline from earlier facets actually live in code; the sweeper reuses the exact state-machine logic from the deep-dive facet as a periodic job.*

## 5. Runnable example

**Level 1 — Basic.** `PasteController` and `PasteService` wired together for creation, coordinating blob and metadata writes in the correct order.

**Level 2 — Intermediate.** Preview (`GET`) vs. reveal (`POST .../reveal`) for a burn-after-reading paste, implementing the safe/non-idempotent split from API design.

**Level 3 — Advanced.** A `@Scheduled`-style expiration sweep using the idempotent state machine from the deep-dive facet, run as part of the service.

```java
// PastebinSpringDemo.java
// A focused, runnable stand-in for the real Spring Boot classes.
import java.util.*;
import java.time.*;

public class PastebinSpringDemo {

    enum DeletionStatus { NONE, PENDING, BLOB_DELETED, DONE }

    static class Paste {
        String pasteId, blobKey, language;
        Instant expiresAt;
        boolean burnAfterReading;
        Instant burnedAt;
        DeletionStatus deletionStatus = DeletionStatus.NONE;
        Paste(String pasteId, String blobKey, String language, Instant expiresAt, boolean burnAfterReading) {
            this.pasteId = pasteId; this.blobKey = blobKey; this.language = language;
            this.expiresAt = expiresAt; this.burnAfterReading = burnAfterReading;
        }
    }

    // ---------- BlobStorageClient (interface, hexagonal-style) ----------
    interface BlobStorageClient {
        void put(String key, String content);
        String get(String key);
        void delete(String key);
        boolean exists(String key);
    }
    static class InMemoryBlobStorageClient implements BlobStorageClient {
        Map<String, String> store = new HashMap<>();
        public void put(String key, String content) { store.put(key, content); }
        public String get(String key) { return store.get(key); }
        public void delete(String key) { store.remove(key); }
        public boolean exists(String key) { return store.containsKey(key); }
    }

    // ---------- PasteRepository (Spring Data JpaRepository in real Spring) ----------
    static class PasteRepository {
        Map<String, Paste> table = new HashMap<>();
        Optional<Paste> findById(String id) { return Optional.ofNullable(table.get(id)); }
        Paste save(Paste paste) { table.put(paste.pasteId, paste); return paste; }
        void delete(String id) { table.remove(id); }
        List<Paste> findExpiredNotDone(Instant now) {
            return table.values().stream()
                .filter(p -> p.expiresAt != null && p.expiresAt.isBefore(now) && p.deletionStatus != DeletionStatus.DONE)
                .toList();
        }
    }

    // ---------- PasteService (@Service) ----------
    static class PasteService {
        PasteRepository repository;
        BlobStorageClient blobStorage;
        int idCounter = 1000;

        PasteService(PasteRepository repository, BlobStorageClient blobStorage) {
            this.repository = repository; this.blobStorage = blobStorage;
        }

        Paste create(String content, String language, Instant expiresAt, boolean burnAfterReading) {
            String pasteId = "p" + (idCounter++);
            String blobKey = "pastes/" + pasteId;
            blobStorage.put(blobKey, content); // blob written FIRST, per high-level architecture
            Paste paste = new Paste(pasteId, blobKey, language, expiresAt, burnAfterReading);
            return repository.save(paste); // metadata written second
        }

        // Level 2: preview - safe, idempotent, never reveals content for a burn paste.
        Object preview(String pasteId) {
            Paste paste = repository.findById(pasteId).orElse(null);
            if (paste == null) return "404 Not Found";
            if (paste.expiresAt != null && Instant.now().isAfter(paste.expiresAt)) return "410 Gone (expired)";
            if (paste.burnAfterReading && paste.burnedAt != null) return "410 Gone (already burned)";
            if (paste.burnAfterReading) return "200 OK - preview only, burnAfterReading=true, revealed=false";
            return "200 OK - content: " + blobStorage.get(paste.blobKey);
        }

        // Level 2: reveal - the ONE non-idempotent operation, only for burn-after-reading pastes.
        Object reveal(String pasteId) {
            Paste paste = repository.findById(pasteId).orElse(null);
            if (paste == null) return "404 Not Found";
            if (!paste.burnAfterReading) return "400 Bad Request - this paste is not burn-after-reading";
            if (paste.burnedAt != null) return "410 Gone (already burned)";
            String content = blobStorage.get(paste.blobKey); // read FIRST
            blobStorage.delete(paste.blobKey);                 // then delete blob
            paste.burnedAt = Instant.now();                     // then mark metadata
            repository.save(paste);
            return "200 OK - content (one time only): " + content;
        }

        // Level 3: idempotent expiration sweep, reusing the deep-dive facet's state machine.
        void sweepExpired(Instant now) {
            for (Paste paste : repository.findExpiredNotDone(now)) {
                if (paste.deletionStatus == DeletionStatus.NONE) paste.deletionStatus = DeletionStatus.PENDING;
                if (paste.deletionStatus == DeletionStatus.PENDING) {
                    blobStorage.delete(paste.blobKey);
                    paste.deletionStatus = DeletionStatus.BLOB_DELETED;
                    System.out.println("    swept " + paste.pasteId + ": blob deleted");
                }
                if (paste.deletionStatus == DeletionStatus.BLOB_DELETED) {
                    repository.delete(paste.pasteId);
                    System.out.println("    swept " + paste.pasteId + ": metadata removed");
                }
            }
        }
    }

    public static void main(String[] args) {
        PasteRepository repository = new PasteRepository();
        BlobStorageClient blobStorage = new InMemoryBlobStorageClient();
        PasteService service = new PasteService(repository, blobStorage);

        System.out.println("Level 1 - create a normal paste:");
        Paste normal = service.create("System.out.println(\"hi\");", "java", null, false);
        System.out.println("  created: " + normal.pasteId + ", blob exists: " + blobStorage.exists(normal.blobKey));
        System.out.println("  preview: " + service.preview(normal.pasteId));

        System.out.println("\nLevel 2 - burn-after-reading paste: preview does not consume it:");
        Paste burn = service.create("the secret", "text", null, true);
        System.out.println("  " + service.preview(burn.pasteId));
        System.out.println("  " + service.preview(burn.pasteId) + "  (still not revealed, repeated preview is safe)");
        System.out.println("  now revealing:");
        System.out.println("  " + service.reveal(burn.pasteId));
        System.out.println("  second reveal attempt: " + service.reveal(burn.pasteId));
        System.out.println("  preview after burn: " + service.preview(burn.pasteId));

        System.out.println("\nLevel 3 - expiration sweep:");
        Paste expiring = service.create("old content", "text", Instant.now().minusSeconds(10), false);
        System.out.println("  before sweep - blob exists: " + blobStorage.exists(expiring.blobKey) +
            ", metadata exists: " + repository.findById(expiring.pasteId).isPresent());
        service.sweepExpired(Instant.now());
        System.out.println("  after sweep - blob exists: " + blobStorage.exists(expiring.blobKey) +
            ", metadata exists: " + repository.findById(expiring.pasteId).isPresent());
    }
}
```

**How to run:** `java PastebinSpringDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `service.create(...)` calls `blobStorage.put(blobKey, content)` **before** `repository.save(paste)` — this exact ordering, called out explicitly in [high-level architecture](0246-pastebin-high-level-architecture.md)'s walkthrough, means a crash between the two calls leaves an orphaned but harmless blob, never a metadata row pointing at content that was never actually saved. The printed check confirms the blob exists immediately after creation.
2. **Level 2:** `service.preview(burn.pasteId)` is called twice in a row for the burn-after-reading paste. Both calls take the `if (paste.burnAfterReading) return "... revealed=false"` branch — neither call touches `blobStorage` at all, confirming preview is genuinely safe and repeatable, exactly matching the [API design](0245-pastebin-api-design.md)'s intent.
3. **`service.reveal(burn.pasteId)` is called once and succeeds**: it reads the content from `blobStorage` first, then calls `blobStorage.delete(...)`, then sets `paste.burnedAt` and saves — this ordering (read, then delete blob, then mark metadata) directly implements the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md)'s discipline of never losing content before successfully returning it to the caller.
4. **The second call to `service.reveal(burn.pasteId)` finds `paste.burnedAt != null`** (set by the first call) and returns `"410 Gone (already burned)"` without touching blob storage again — this is the non-idempotent operation correctly refusing to run twice, and the subsequent `service.preview(...)` call for the same paste also now returns `410 Gone`, confirming both endpoints agree on the paste's now-permanently-gone status.
5. **Level 3:** `service.create(...)` is called with an `expiresAt` already 10 seconds in the past, simulating an already-expired paste. The "before sweep" check confirms both the blob and metadata row exist normally at creation. `service.sweepExpired(Instant.now())` finds this paste via `repository.findExpiredNotDone(now)`, walks it through `NONE → PENDING → BLOB_DELETED → (metadata removed)` in one pass (since no crash is simulated here), and the "after sweep" check confirms both the blob and the metadata row are now gone — the exact same state-machine logic from the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md), here wired up as a method a real `@Scheduled` Spring bean would call periodically.

## 7. Gotchas & takeaways

> **Gotcha:** `BlobStorageClient` is defined as an interface specifically so `PasteService`'s logic (the create-ordering, the reveal-ordering, the sweep state machine) can be unit-tested with `InMemoryBlobStorageClient`, exactly as shown here, without needing a real object storage connection in every test run — this is the same [hexagonal architecture](0198-hexagonal-ports-and-adapters.md) principle the URL Shortener case study's own implementation facet used for its repository, applied here to a second, independent external dependency (blob storage) alongside the database.

- Keep the create/reveal/sweep ordering discipline (blob-then-metadata on write, content-then-blob-delete-then-metadata on reveal/sweep) exactly as specified in earlier facets — this is not an implementation detail to improvise, it is a correctness property established deliberately in [high-level architecture](0246-pastebin-high-level-architecture.md) and the [deep-dive facet](0248-pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup.md).
- The preview/reveal split lives entirely in `PasteService`'s two distinct methods, mirroring the API design's two distinct endpoints — resist any temptation to collapse them back into one method "for simplicity," since that collapse is exactly the bug this whole facet chain was designed to avoid.
- This closes the Pastebin case study — the same nine-facet structure applied to the [URL Shortener](0224-url-shortener-functional-requirements.md) and [Rate Limiter](0233-rate-limiter-functional-requirements.md) case studies applies equally well here, and to the [Web Crawler](0251-web-crawler-functional-requirements.md) case study that follows.
