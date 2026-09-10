---
card: system-design
gi: 248
slug: pastebin-deep-dive-blob-storage-ttl-based-expiration-cleanup
title: "Pastebin — deep-dive: blob storage & TTL-based expiration cleanup"
---

## 1. What it is

This page covers the **deep-dive** facet of the **Pastebin** case study, focused on the one genuinely hard sub-problem: reliably cleaning up expired pastes' blob storage and metadata (FR-4), at the scale established in [capacity estimation](0244-pastebin-capacity-estimation.md) (~7.3 TB accumulated over 2 years), without the two-step delete (blob, then metadata, per [high-level architecture](0246-pastebin-high-level-architecture.md)) ever leaving the system in an inconsistent state under real-world crashes and retries.

## 2. Why & when

"Delete expired pastes" sounds like a simple scheduled job until you consider what happens when that job crashes mid-batch, or runs concurrently with itself (two sweeper instances processing the same expired paste simultaneously), or when a paste expires exactly while someone is retrieving it. This is the one part of the Pastebin case study that is a genuine correctness problem under failure, worth its own deep-dive, the same way the URL Shortener and Rate Limiter case studies each had one hard algorithmic sub-problem.

## 3. Core concept

- **Naive approach: a scheduled job deletes rows past `expires_at`, one at a time, synchronously.** Simple to reason about in the happy path, but if the job crashes after deleting the blob but before deleting the metadata row, the metadata row becomes a "dangling reference" — pointing at a blob that no longer exists.
- **Idempotent deletion, using state transitions.** Rather than deleting the metadata row directly, mark it (`deletion_status: PENDING → BLOB_DELETED → DONE`) and only fully remove it once every step is confirmed — a crash at any point leaves a resumable, well-defined state rather than an ambiguous one, the same idempotency principle from [idempotency & safe methods](0210-idempotency-safe-methods.md) applied to a batch cleanup process instead of an API call.
- **Batching with a claim mechanism, to avoid two sweeper instances double-processing the same paste.** A sweeper instance atomically claims a batch of expired rows (e.g. `UPDATE ... SET claimed_by = 'sweeper-A', claimed_at = now() WHERE expires_at < now() AND claimed_by IS NULL LIMIT 1000`), so a second concurrently-running sweeper instance's identical query does not see rows the first has already claimed.
- **Native TTL support, where the storage layer offers it.** Many blob storage services and some databases support native, storage-layer TTL/lifecycle policies (automatically deleting an object after a configured time) — where available, this removes the need for a custom sweeper for the blob-deletion half of the work entirely, though the metadata row still needs its own cleanup since the metadata store's TTL and the blob store's TTL are two independent mechanisms that must be kept in sync (or the metadata row's own expiration check, from [data model & schema](0247-pastebin-data-model-schema.md), is used to treat an already-blob-deleted paste as `410 Gone` even before its metadata row is swept).
- **A retrieval racing an in-progress expiration is handled by checking `expires_at` at read time regardless of sweeper state** — the [high-level architecture](0246-pastebin-high-level-architecture.md)'s retrieval path already checks `expires_at` on every read, so even if the sweeper has not yet run for a paste that expired one second ago, the retrieval path itself correctly refuses to serve it, independent of the sweeper's own progress.

## 4. Diagram

```
   NAIVE (single delete, no state tracking)      IDEMPOTENT (state machine, crash-resumable)

   1. delete blob                                 1. UPDATE paste SET deletion_status='PENDING'
   2. delete metadata row                              WHERE expires_at < now()
   [CRASH between 1 and 2]                         2. for each PENDING row:
        |                                               delete blob
        v                                               UPDATE deletion_status='BLOB_DELETED'
   metadata row survives,                          [CRASH after this point is SAFE - blob is
   pointing at a DELETED blob -                      already gone, row correctly shows it]
   a dangling reference, silently                  3. for each BLOB_DELETED row:
   broken for any retrieval                              DELETE the metadata row itself
   that reaches it                                  [CRASH before this point is SAFE - a resumed
                                                       sweep finds BLOB_DELETED rows and just
                                                       finishes step 3 for them]
```
*Caption: the naive approach has exactly one crash window that leaves an inconsistent, undetectable state. The state-machine approach has no such window — every possible crash point leaves the row in a state the next sweeper run can correctly resume from.*

## 5. Runnable example

**Level 1 — Basic.** The naive single-pass delete, showing the crash window that leaves a dangling metadata reference.

**Level 2 — Intermediate.** The idempotent, state-machine-based delete, resuming correctly after a simulated crash.

**Level 3 — Advanced.** Two concurrent sweeper instances using an atomic claim mechanism, proving neither double-processes the same expired paste.

```java
// PastebinExpirationDemo.java
import java.util.*;
import java.util.concurrent.*;

public class PastebinExpirationDemo {

    enum DeletionStatus { NONE, PENDING, BLOB_DELETED, DONE }

    static class PasteRow {
        String pasteId;
        boolean blobExists = true;
        DeletionStatus status = DeletionStatus.NONE;
        String claimedBy = null;
        PasteRow(String pasteId) { this.pasteId = pasteId; }
    }

    static class MetadataStore {
        Map<String, PasteRow> rows = new ConcurrentHashMap<>();
        void addExpired(String pasteId) { rows.put(pasteId, new PasteRow(pasteId)); }
    }

    // ---------- Level 1: naive delete, no crash safety ----------
    static void naiveDelete(PasteRow row, boolean simulateCrashAfterBlobDelete) {
        row.blobExists = false; // step 1: delete blob
        System.out.println("    blob for " + row.pasteId + " deleted");
        if (simulateCrashAfterBlobDelete) {
            System.out.println("    CRASH before metadata row was deleted!");
            return; // metadata row survives, still pointing at a now-deleted blob
        }
        // step 2 would delete the metadata row here, but we never reach it on crash
    }

    // ---------- Level 2: idempotent, state-machine-based delete ----------
    static void idempotentSweep(MetadataStore store, boolean simulateCrashMidway) {
        for (PasteRow row : store.rows.values()) {
            if (row.status == DeletionStatus.DONE) continue;

            if (row.status == DeletionStatus.NONE) {
                row.status = DeletionStatus.PENDING;
            }
            if (row.status == DeletionStatus.PENDING) {
                row.blobExists = false;
                row.status = DeletionStatus.BLOB_DELETED;
                System.out.println("    " + row.pasteId + ": blob deleted, status -> BLOB_DELETED");
                if (simulateCrashMidway) {
                    System.out.println("    CRASH after blob delete, before final cleanup - SAFE, row is resumable");
                    return;
                }
            }
            if (row.status == DeletionStatus.BLOB_DELETED) {
                store.rows.remove(row.pasteId); // final metadata cleanup
                System.out.println("    " + row.pasteId + ": metadata row removed, status -> DONE");
            }
        }
    }

    // ---------- Level 3: concurrent sweepers with atomic claim ----------
    static synchronized boolean tryClaim(PasteRow row, String sweeperName) {
        if (row.claimedBy != null) return false; // already claimed by another sweeper
        row.claimedBy = sweeperName;
        return true;
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Level 1 - naive delete, crash leaves a dangling metadata reference:");
        PasteRow naiveRow = new PasteRow("p-naive-1");
        naiveDelete(naiveRow, true);
        System.out.println("  result: blobExists=" + naiveRow.blobExists +
            ", but metadata row STILL EXISTS - a dangling reference, silently broken");

        System.out.println("\nLevel 2 - idempotent sweep, crash mid-way, then resumed:");
        MetadataStore store = new MetadataStore();
        store.addExpired("p-idempotent-1");
        System.out.println("  first sweep run (simulated crash after blob delete):");
        idempotentSweep(store, true);
        PasteRow afterCrash = store.rows.get("p-idempotent-1");
        System.out.println("  row state after crash: status=" + afterCrash.status + ", blobExists=" + afterCrash.blobExists);
        System.out.println("  second sweep run (resumes from BLOB_DELETED, no crash this time):");
        idempotentSweep(store, false);
        System.out.println("  row still in store? " + store.rows.containsKey("p-idempotent-1"));

        System.out.println("\nLevel 3 - two concurrent sweepers, atomic claim prevents double-processing:");
        PasteRow sharedRow = new PasteRow("p-concurrent-1");
        AtomicClaimResult[] results = new AtomicClaimResult[2];
        Thread sweeperA = new Thread(() -> results[0] = new AtomicClaimResult("sweeper-A", tryClaim(sharedRow, "sweeper-A")));
        Thread sweeperB = new Thread(() -> results[1] = new AtomicClaimResult("sweeper-B", tryClaim(sharedRow, "sweeper-B")));
        sweeperA.start(); sweeperB.start();
        sweeperA.join(); sweeperB.join();
        for (AtomicClaimResult r : results) System.out.println("  " + r.sweeperName + " claimed: " + r.claimed);
        System.out.println("  final claimedBy: " + sharedRow.claimedBy + "  <- exactly ONE sweeper processes this row");
    }

    record AtomicClaimResult(String sweeperName, boolean claimed) {}
}
```

**How to run:** `java PastebinExpirationDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `naiveDelete(naiveRow, true)` deletes the blob (`row.blobExists = false`) and then, because `simulateCrashAfterBlobDelete` is `true`, returns immediately without ever removing the metadata row. The printed result confirms the exact failure mode from Part 3: the blob is gone, but the metadata row survives, now pointing at nothing — any retrieval reaching this row (before the [data model](0247-pastebin-data-model-schema.md)'s own `expires_at` check would catch it, in a real system, or in an edge case that check misses) would encounter a broken reference.
2. **Level 2:** the first call to `idempotentSweep(store, true)` processes `"p-idempotent-1"` starting from `DeletionStatus.NONE`, transitions it to `PENDING`, then immediately to `BLOB_DELETED` (deleting the blob), and because `simulateCrashMidway` is `true`, returns right after — but critically, **the row's status was already updated to `BLOB_DELETED` before the simulated crash**, not left at `PENDING` or `NONE`.
3. **Printing the row's state after the crash confirms `status=BLOB_DELETED, blobExists=false`** — a well-defined, resumable state, in sharp contrast to Level 1's dangling reference. The **second** call to `idempotentSweep(store, false)` iterates again, finds this same row, sees its status is `BLOB_DELETED` (skipping the already-completed blob deletion step entirely), and proceeds directly to removing the metadata row — completing the cleanup that the "crashed" first run left unfinished, with no risk of re-deleting an already-deleted blob or losing track of the row.
4. **The final check, `store.rows.containsKey("p-idempotent-1")`, prints `false`**, confirming the two-run sequence (crash, then resume) correctly reached the same end state a single, uninterrupted run would have — this is exactly what "idempotent, crash-resumable" means in practice: any number of partial runs, interrupted at any point, eventually converge on the correct final state.
5. **Level 3:** `sweeperA` and `sweeperB` are separate threads, both calling `tryClaim(sharedRow, ...)` on the exact same `PasteRow` at nearly the same instant. Because `tryClaim` is `synchronized`, only one thread's call can execute the check-and-set (`if (row.claimedBy != null) return false; row.claimedBy = sweeperName;`) at a time — whichever thread's call runs first claims the row and returns `true`; the other finds `row.claimedBy` already set and returns `false`. The final printed `claimedBy` value confirms exactly one of the two sweepers won the claim, preventing the double-processing that would occur if both sweepers proceeded to delete the same blob concurrently, unaware of each other's work.

## 7. Gotchas & takeaways

> **Gotcha:** a claim mechanism without an expiry on the claim itself creates a new failure mode — if `sweeper-A` claims a row and then crashes before finishing, that row is permanently stuck, claimed forever by a sweeper instance that no longer exists, and no other sweeper will ever pick it up. A real claim mechanism needs its own timeout (e.g. "a claim older than 5 minutes is considered abandoned and can be re-claimed"), turning this into the same kind of idempotent, resumable design as Level 2, layered on top of Level 3's atomicity.

- Design cleanup and deletion processes around explicit, resumable states (as Level 2 does), not a single "just delete it" step — this is the general fix for the entire category of "crashed halfway through a multi-step operation" bugs, applicable well beyond Pastebin specifically.
- A claim mechanism (Level 3) is necessary the moment more than one instance of a background job might run concurrently — which is the normal case for any horizontally scaled, fault-tolerant deployment, not an edge case to defer.
- Combine claim atomicity (Level 3) with claim expiry (the gotcha above) for a genuinely production-ready cleanup process — either one alone leaves a real gap.
- See [Pastebin — scaling & tradeoffs](0249-pastebin-scaling-tradeoffs.md) next for how this cleanup process and the rest of the architecture hold up as total storage volume grows well past the original ~7.3 TB estimate.
