---
card: system-design
gi: 65
slug: b-tree-hash-composite-indexes
title: "B-tree, hash & composite indexes"
---

## 1. What it is

A database **index** is a separate, ordered structure built on top of a table's columns that lets the database find matching rows without scanning the entire table. A **B-tree index** keeps entries sorted, supporting fast lookups and range queries. A **hash index** maps each value to a location via a hash function, supporting only fast exact-match lookups. A **composite index** is built on multiple columns together, in a specific order.

## 2. Why & when

Without an index, finding a row by a column's value means scanning every row in the table — a **full table scan** — which gets slower as the table grows. An index turns that into a fast, logarithmic-time lookup. Use a B-tree index (the default in most databases) for anything queried by equality or by range (`WHERE age > 30`, `ORDER BY created_at`). Use a hash index only for pure equality lookups where range queries are never needed. Use a composite index when queries commonly filter on more than one column together.

## 3. Core concept

**Why a B-tree supports both equality and range queries:** a B-tree keeps keys sorted in a tree structure where each node holds several keys and pointers to child nodes covering the ranges between them. Finding a value means descending the tree, at each level choosing the child whose range contains the target — O(log n) comparisons. Because keys stay sorted, a range query (`age BETWEEN 20 AND 30`) can find the starting point with one descent, then walk sequentially from there.

**Why a hash index cannot support range queries:** a hash index computes `hash(value)` and jumps directly to that bucket — O(1) for an exact match, but the hash function scrambles ordering, so there is no way to ask "give me everything between X and Y" without checking every single entry.

**Composite index column order matters:** an index on `(last_name, first_name)` can efficiently answer `WHERE last_name = 'Smith'` and `WHERE last_name = 'Smith' AND first_name = 'Jane'`, because both queries can use the index's sorted-by-`last_name`-first structure. But it cannot efficiently answer `WHERE first_name = 'Jane'` alone — the index is not sorted by `first_name` at the top level, so the database would have to scan every entry, just as if there were no index at all.

## 4. Diagram

```
B-TREE index on age (sorted, supports range queries):

              [30]
            /       \
       [10, 20]     [40, 50]
       /  |  \        /  |  \
     ...values sorted, so "age BETWEEN 20 AND 40" walks a contiguous range

HASH index on user_id (exact match only, no ordering):

  hash(42) -> bucket 7 -> row pointer   (O(1) for "user_id = 42")
  hash(43) -> bucket 2 -> row pointer   (bucket for 43 has NO relation to bucket for 42)
  "user_id BETWEEN 42 AND 43" -> hash index cannot help; buckets are scattered, not ordered

COMPOSITE index on (last_name, first_name) - sorted by last_name FIRST:
  [Adams, Amy] [Adams, Bob] [Smith, Jane] [Smith, John] [Zhao, Li]
  WHERE last_name='Smith'                -> fast: contiguous range
  WHERE last_name='Smith' AND first_name='Jane' -> fast: narrows within that range
  WHERE first_name='Jane'                -> index USELESS: matches scattered throughout
```
*Caption: a B-tree's sort order enables range queries; a hash index trades that away for O(1) equality lookups; a composite index only helps queries that use its leading column(s).*

## 5. Runnable example

**Level 1 — Basic.** A sorted structure (`TreeMap`, modeling a B-tree index) supporting both exact and range lookups.

**Level 2 — Hash comparison.** The same data in a `HashMap` (modeling a hash index), showing range queries are not directly supported.

**Level 3 — Composite index ordering.** A composite key built as `(lastName, firstName)`, showing a query on the leading column is fast while a query on only the trailing column is not.

```java
// IndexTypes.java
import java.util.*;

public class IndexTypes {

    public static void main(String[] args) {
        // Level 1: B-tree-like index - TreeMap keeps keys sorted, supports range queries directly.
        TreeMap<Integer, String> ageIndex = new TreeMap<>();
        ageIndex.put(22, "user:Amy");
        ageIndex.put(31, "user:Bob");
        ageIndex.put(45, "user:Cid");
        ageIndex.put(28, "user:Dee");

        System.out.println("B-tree equality (age=31): " + ageIndex.get(31));
        System.out.println("B-tree range (20 <= age <= 30): " + ageIndex.subMap(20, true, 30, true));

        // Level 2: hash-like index - HashMap gives O(1) equality, but no ordered range view.
        HashMap<Integer, String> hashAgeIndex = new HashMap<>(ageIndex);
        System.out.println("hash equality (age=31): " + hashAgeIndex.get(31));
        System.out.println("hash range query: NOT directly supported - would require scanning every entry");

        // Level 3: composite index on (lastName, firstName), sorted by lastName first.
        TreeMap<String, String> compositeIndex = new TreeMap<>();
        compositeIndex.put("Adams|Amy", "row1");
        compositeIndex.put("Adams|Bob", "row2");
        compositeIndex.put("Smith|Jane", "row3");
        compositeIndex.put("Smith|John", "row4");
        compositeIndex.put("Zhao|Li", "row5");

        System.out.println("composite, WHERE last_name='Smith' (uses leading column, FAST):");
        System.out.println("  " + compositeIndex.subMap("Smith|", "Smith}"));

        System.out.println("composite, WHERE first_name='Jane' (trailing column only, index CANNOT help):");
        List<String> matches = new ArrayList<>();
        for (Map.Entry<String, String> e : compositeIndex.entrySet()) { // must scan every entry
            if (e.getKey().endsWith("|Jane")) matches.add(e.getValue());
        }
        System.out.println("  " + matches + "  (found only by scanning all " + compositeIndex.size() + " entries)");
    }
}
```

**How to run:** save as `IndexTypes.java`, then run `java IndexTypes.java`.

## 6. Walkthrough

1. `ageIndex.get(31)` is an O(log n) lookup thanks to `TreeMap`'s sorted internal structure, mirroring a B-tree equality lookup.
2. `ageIndex.subMap(20, true, 30, true)` returns exactly `{22=user:Amy, 28=user:Dee}` — every key between 20 and 30 inclusive — because `TreeMap` keeps entries ordered, so this range is contiguous, mirroring a B-tree range scan.
3. `hashAgeIndex.get(31)` is also fast (O(1) on average), matching a hash index's strength, but `HashMap` has no ordered range view at all — there is no equivalent one-line call for "everything between 20 and 30."
4. `compositeIndex.subMap("Smith|", "Smith}")` finds both Smith rows in one contiguous range, because the composite key's leading segment (`lastName`) sorts them together — this mirrors how a real composite index serves a query filtering on its leading column.
5. Searching for `first_name='Jane'` requires checking every single entry's suffix, because nothing in the composite key's sort order groups entries by `firstName` alone — this mirrors a real composite index being unable to help a query that skips its leading column.

## 7. Gotchas & takeaways

> Gotcha: adding a composite index on `(last_name, first_name)` does **not** also give you a useful index for queries filtering only on `first_name`; if you need both query patterns fast, you need two separate indexes (or, sometimes, a single index built in the other column order, depending on which pattern is more common).

- B-tree is the right general-purpose default: it handles both equality and range queries well, which covers most real query patterns.
- Hash indexes only pay off for pure equality lookups on very hot columns, and even then, many databases' B-tree implementations are fast enough that the extra complexity of a hash index is rarely worth it.
- Composite index column order should match your most common query's filter order, with the most selective or most-frequently-filtered column usually placed first.
- Related concepts: [Covering indexes & index-only scans](0066-covering-indexes-index-only-scans.md) (an extra optimization on top of these index types), [Query planning & the N+1 problem](0067-query-planning-the-n-1-problem.md) (how the database decides whether to actually use an available index).
