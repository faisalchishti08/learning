---
card: system-design
gi: 66
slug: covering-indexes-index-only-scans
title: "Covering indexes & index-only scans"
---

## 1. What it is

A **covering index** is an index that includes every column a specific query needs, not just the column(s) used to filter or sort. When a query's needs are fully met by the index itself, the database can perform an **index-only scan** — answering the query directly from the index, without ever reading the underlying table rows.

## 2. Why & when

A normal index lookup is a two-step process: find the matching entries in the index, then follow a pointer back to the full row in the table to read any other requested column — that second step is an extra disk or memory read per row. A covering index removes that second step entirely for queries whose needed columns are all present in the index. Use it for frequent, narrow, performance-critical queries (a dashboard query run thousands of times a minute) where that second lookup is measurably costly.

## 3. Core concept

**The normal (non-covering) path:** an index on `email` speeds up `WHERE email = ?`, but if the query also selects `name`, the database still has to follow a pointer from the matching index entry back to the full table row, just to read `name` — this extra step is called a **heap fetch** (or "bookmark lookup").

**The covering path:** if the index is instead built on `(email, name)` — or the database's index supports an "included columns" feature to attach `name` without making it part of the sort key — then a query selecting only `email` and `name` finds everything it needs directly in the index entry itself, with no heap fetch required.

**Why this matters at scale:** the heap fetch is often the more expensive part of the whole operation, especially when the matching rows are scattered across many different physical table pages. Removing it via a covering index can turn a query that touches many random disk pages into one that only reads a compact, sequential index structure.

**The trade-off:** a covering index is wider (more columns) than a minimal index, so it costs more storage and more work to keep updated on every write. It only pays off for queries that are frequent and performance-sensitive enough to justify that cost.

## 4. Diagram

```
NON-COVERING index on (email) only:
  Index: email='b@x.com' -> row pointer #482
                                  |
                                  v  HEAP FETCH: follow pointer, read the full row
  Table: row #482 -> {id, email, name, address, created_at, ...}
  Query needs "name" -> must do the heap fetch to get it

COVERING index on (email, name):
  Index: email='b@x.com', name='Bob' -> (row pointer, unused)
  Query needs only email + name -> answered directly from the index entry
                                    NO heap fetch, NO table row read at all
```
*Caption: a covering index stores every column the query needs, so the database can skip the extra trip back to the full table row.*

## 5. Runnable example

**Level 1 — Basic.** A non-covering index: matching entries require a follow-up "heap fetch" to another map to get extra columns, counted explicitly.

**Level 2 — Covering index.** The same query answered by an index that already stores every needed column, with zero heap fetches.

**Level 3 — Cost comparison.** Run the same query pattern many times under each approach and compare heap-fetch counts.

```java
// CoveringIndex.java
import java.util.*;

public class CoveringIndex {

    record UserRow(int id, String email, String name, String address) {}

    static final Map<Integer, UserRow> table = new HashMap<>();
    static int heapFetches = 0;

    static UserRow heapFetch(int rowPointer) {
        heapFetches++; // models an extra disk/memory read back to the full row
        return table.get(rowPointer);
    }

    public static void main(String[] args) {
        table.put(1, new UserRow(1, "amy@x.com", "Amy", "1 Main St"));
        table.put(2, new UserRow(2, "bob@x.com", "Bob", "2 Oak Ave"));
        table.put(3, new UserRow(3, "cid@x.com", "Cid", "3 Elm Rd"));

        // Level 1: NON-COVERING index - only maps email -> row pointer.
        Map<String, Integer> nonCoveringIndex = new HashMap<>();
        for (UserRow r : table.values()) nonCoveringIndex.put(r.email(), r.id());

        System.out.println("--- non-covering: query needs email + name ---");
        for (String email : List.of("amy@x.com", "bob@x.com", "cid@x.com")) {
            Integer pointer = nonCoveringIndex.get(email); // index-only step: fast
            UserRow row = heapFetch(pointer); // extra step: follow pointer to get "name"
            System.out.println("  " + email + " -> " + row.name());
        }
        System.out.println("heap fetches with non-covering index: " + heapFetches);

        heapFetches = 0; // reset for the covering-index comparison

        // Level 2: COVERING index - stores (email, name) directly, no pointer-follow needed.
        record CoveringEntry(String email, String name) {}
        List<CoveringEntry> coveringIndex = new ArrayList<>();
        for (UserRow r : table.values()) coveringIndex.add(new CoveringEntry(r.email(), r.name()));

        System.out.println("--- covering: query needs email + name ---");
        for (String email : List.of("amy@x.com", "bob@x.com", "cid@x.com")) {
            for (CoveringEntry e : coveringIndex) {
                if (e.email().equals(email)) {
                    System.out.println("  " + email + " -> " + e.name()); // answered from the index alone
                    break;
                }
            }
        }
        System.out.println("heap fetches with covering index: " + heapFetches); // stays 0
    }
}
```

**How to run:** save as `CoveringIndex.java`, then run `java CoveringIndex.java`.

## 6. Walkthrough

1. `nonCoveringIndex` maps only `email` to a row pointer (`id`) — it does not store `name`.
2. For each email, `nonCoveringIndex.get(email)` is a fast index lookup, but getting `name` requires calling `heapFetch(pointer)`, which reads the full row from `table` — incrementing `heapFetches` once per query.
3. After three queries, `heapFetches` is `3` — one extra read per query, on top of the index lookup itself.
4. `coveringIndex` instead stores `email` and `name` together, directly, with nothing pointing back to `table`.
5. The same three queries now find both `email` and `name` directly within `coveringIndex`'s own entries — `heapFetch` is never called, so `heapFetches` stays at `0` for the entire second run.

## 7. Gotchas & takeaways

> Gotcha: adding a column to a covering index to serve one query makes that index wider and more expensive to update on every write to that column; a covering index is a targeted optimization for a specific, known, frequent query — not something to apply to every index by default.

- A covering index eliminates the heap fetch entirely for queries whose needed columns are all present in the index, which can be a major cost saving under heavy read load.
- The trade-off is storage and write cost: every additional column in the index must be kept up to date on every insert, update, and delete that touches it.
- Related concepts: [B-tree, hash & composite indexes](0065-b-tree-hash-composite-indexes.md) (the underlying index structures a covering index builds on), [Query planning & the N+1 problem](0067-query-planning-the-n-1-problem.md) (how the query planner decides whether an index-only scan is even possible).
