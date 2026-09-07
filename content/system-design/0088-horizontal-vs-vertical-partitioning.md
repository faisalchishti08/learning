---
card: system-design
gi: 88
slug: horizontal-vs-vertical-partitioning
title: Horizontal vs vertical partitioning
---

## 1. What it is

**Partitioning** splits one large dataset into smaller, more manageable pieces. **Horizontal partitioning** (also called sharding) splits a table by rows: each partition holds a subset of the rows, but every partition has the same columns. **Vertical partitioning** splits a table by columns: each partition holds a subset of the columns, but every partition has the same rows. Think of a spreadsheet: horizontal partitioning tears it into row-ranges; vertical partitioning tears it into column-groups.

## 2. Why & when

A single database server has limits on storage, memory, and CPU. Once a table grows past what one machine can hold or serve fast, you must split it. Horizontal partitioning helps when the table has too many rows for one machine — for example, a `users` table with a billion rows. Vertical partitioning helps when a table has some columns that are large or rarely read together with the rest — for example, splitting a `user_profile` blob (bio, photo) from frequently-queried login fields (email, password hash). Use horizontal partitioning to scale write and storage volume; use vertical partitioning to reduce the amount of unrelated data an query has to scan.

## 3. Core concept

**Horizontal partitioning (sharding):**
- Rows are distributed across partitions using a **partition key** (e.g. `user_id`).
- Each shard is a full copy of the schema, holding only its slice of rows.
- A query for one row only needs to hit the shard that owns its key.
- Scaling out means adding more shards, each holding fewer rows.

**Vertical partitioning:**
- Columns are grouped by how they are accessed together.
- "Hot" columns (read on every request) live in one partition; "cold" or large columns (rarely read, or large in size) live in another.
- A query that only needs hot columns avoids loading the cold ones, so it reads less data per row.
- This does not reduce the row count anywhere, so it does not help once row count itself is the bottleneck.

**The key difference:** horizontal partitioning scales the number of rows a system can hold; vertical partitioning scales how efficiently you read a *single* row's data. Large systems often use both together.

## 4. Diagram

```
Original table: users(id, email, password_hash, bio, photo_blob)

HORIZONTAL (by row, split on id range):
  Shard A: rows id 1-500        Shard B: rows id 501-1000
  +----+-------+-----------+    +-----+-------+-----------+
  | id | email | ...       |    | id  | email | ...       |
  +----+-------+-----------+    +-----+-------+-----------+
  (same columns, different rows)

VERTICAL (by column, split on access pattern):
  Partition 1 (hot, small):     Partition 2 (cold, large):
  +----+-------+---------------+   +----+-----+------------+
  | id | email | password_hash |   | id | bio | photo_blob |
  +----+-------+---------------+   +----+-----+------------+
  (same rows, different columns, joined back by id)
```
*Caption: horizontal partitioning cuts by rows across machines; vertical partitioning cuts by columns, usually within reach of a join.*

## 5. Runnable example

**Level 1 — Basic.** Model a table as a list of records, then split it horizontally by an id range.

**Level 2 — Vertical split.** Split the same records into a "hot" and a "cold" column group.

**Level 3 — Routing a query.** Pick the right shard for a horizontal read, and reassemble a row from both vertical partitions.

```java
// PartitioningDemo.java
import java.util.*;

public class PartitioningDemo {

    record User(int id, String email, String passwordHash, String bio) {}
    record HotUser(int id, String email, String passwordHash) {}
    record ColdUser(int id, String bio) {}

    public static void main(String[] args) {
        List<User> table = new ArrayList<>();
        for (int i = 1; i <= 10; i++) {
            table.add(new User(i, "user" + i + "@mail.com", "hash" + i, "bio text ".repeat(50)));
        }

        // Level 1: horizontal partitioning - split rows into two shards by id range.
        List<User> shardA = new ArrayList<>(); // ids 1-5
        List<User> shardB = new ArrayList<>(); // ids 6-10
        for (User u : table) {
            (u.id() <= 5 ? shardA : shardB).add(u);
        }
        System.out.println("shard A row count: " + shardA.size());
        System.out.println("shard B row count: " + shardB.size());

        // Level 2: vertical partitioning - split columns into hot and cold groups.
        List<HotUser> hot = new ArrayList<>();
        List<ColdUser> cold = new ArrayList<>();
        for (User u : table) {
            hot.add(new HotUser(u.id(), u.email(), u.passwordHash()));
            cold.add(new ColdUser(u.id(), u.bio()));
        }
        System.out.println("hot partition columns per row: id, email, passwordHash (small, read on every login)");
        System.out.println("cold partition columns per row: id, bio (large, read only on profile view)");

        // Level 3: routing - find shard for a login (horizontal), then read only hot columns.
        int targetId = 7;
        List<User> targetShard = (targetId <= 5) ? shardA : shardB;
        System.out.println("login lookup for id=" + targetId + " routed to shard " + (targetShard == shardA ? "A" : "B"));

        HotUser loginRow = hot.stream().filter(h -> h.id() == targetId).findFirst().orElseThrow();
        System.out.println("login only reads hot row: " + loginRow + " (bio not loaded)");
    }
}
```

**How to run:** save as `PartitioningDemo.java`, then run `java PartitioningDemo.java`.

## 6. Walkthrough

1. The program builds one logical `table` of 10 users, each carrying a large `bio` field to represent a "cold" column.
2. Level 1 splits the table horizontally: every row goes to `shardA` or `shardB` based on its `id`, so each shard has the same columns but only half the rows.
3. Level 2 splits the same 10 rows vertically: `hot` keeps only `id`, `email`, `passwordHash`; `cold` keeps only `id` and `bio`. Every row appears in both partitions, joined by `id`.
4. Level 3 simulates a real login: the code first decides which **shard** owns `id=7` (horizontal routing), then reads only the **hot** partition for that id, never touching the large `bio` column.
5. The printed output shows the shard boundary (5 rows in A, 5 in B) and confirms the login path loads a small `HotUser` record, not the full row — this is the payoff of combining both techniques.

## 7. Gotchas & takeaways

> Gotcha: vertical partitioning does not reduce the number of rows a query might scan, so it does not fix a "too many rows" problem; horizontal partitioning does not reduce how much unrelated data one row carries, so it does not fix a "rows are too fat" problem. Picking the wrong one for your bottleneck wastes the migration effort.

- Horizontal partitioning (sharding) scales row count across machines; it needs a partition key and a routing rule.
- Vertical partitioning scales per-row read efficiency by separating hot and cold columns; it usually still lives on one machine, or is rejoined via a key.
- Real systems often combine both: shard the hot columns across machines for scale, and keep cold columns in a separate, less frequently accessed store.
- Related concepts: [Range-based sharding](0090-range-based-sharding.md) and [Hash-based sharding](0091-hash-based-sharding.md) (specific horizontal strategies), [Denormalization & data duplication](0081-denormalization-data-duplication.md) (another way to speed up reads by shaping data around access patterns).
