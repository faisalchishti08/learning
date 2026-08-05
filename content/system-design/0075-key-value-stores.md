---
card: system-design
gi: 75
slug: key-value-stores
title: Key-value stores
---

## 1. What it is

A **key-value store** is the simplest kind of NoSQL database: it stores data as pairs of a unique **key** and an opaque **value**, with no fixed schema and no relationships between entries. Lookups are always by exact key — there is no query language for filtering by the contents of the value. Examples include Redis, DynamoDB, and Riak.

## 2. Why & when

A key-value store trades away everything a relational database offers beyond fast key lookup — no joins, no schema enforcement, no complex queries — in exchange for extreme simplicity and speed at massive scale. Use one when your access pattern is fundamentally "fetch this one thing by its ID": a session store, a shopping cart, a user preferences blob, or a cache. It is a poor fit whenever you need to query or filter by anything other than the key itself.

## 3. Core concept

**The value is opaque to the store:** unlike a relational table's typed columns, the value in a key-value store is usually just a blob of bytes (often JSON or a serialized object) that the database itself does not understand. It cannot query "find all values where `age > 30`," because it has no idea what is inside the value — only your application code, after fetching it, can interpret it.

**Why this makes reads and writes extremely fast:** because there is no schema to validate and no secondary index to update, a key-value store's read and write path is close to the theoretical minimum: hash the key, find its location, read or write the bytes. This is the same core mechanism as a hash index, applied as the entire database rather than as one feature of it.

**Partitioning by key:** at scale, a key-value store shards data across many nodes by hashing the key (often with consistent hashing, covered earlier in this section), so lookups route directly to the one node holding that key, without needing to ask every node.

**The cost of simplicity:** if you later need to find "all shopping carts abandoned in the last hour," a pure key-value store cannot answer that without you designing extra keys or a separate index specifically for that access pattern up front — this is the access-pattern-first thinking covered later in this section.

## 4. Diagram

```
KEY-VALUE STORE (opaque values, exact-key lookup only):

  key: "cart:user-42"   -> value: {"items": ["sku1", "sku2"], "total": 39.98}   (opaque bytes)
  key: "cart:user-99"   -> value: {"items": ["sku3"], "total": 12.50}
  key: "session:abc123" -> value: {"userId": 42, "expiresAt": 1234567890}

  GET "cart:user-42"  -> O(1)-ish lookup, direct return of the raw value
  "find carts where total > 30" -> NOT POSSIBLE without reading and checking every value yourself
```
*Caption: a key-value store answers "get me the value for this exact key" extremely fast, and answers nothing else at all.*

## 5. Runnable example

**Level 1 — Basic.** A key-value store as a plain map: `get` and `put` by exact key.

**Level 2 — Opaque values.** Store JSON-like blobs the store itself never inspects, only the application does after fetching.

**Level 3 — Why filtering fails.** Show that answering "find all carts over $30" requires scanning every value manually — the store provides no help.

```java
// KeyValueStores.java
import java.util.*;

public class KeyValueStores {

    // Level 1 & 2: the store itself only knows keys and opaque byte-like blobs (Strings here).
    static final Map<String, String> store = new HashMap<>();

    static void put(String key, String opaqueValue) { store.put(key, opaqueValue); }
    static String get(String key) { return store.get(key); } // the ONLY operation the store optimizes

    public static void main(String[] args) {
        put("cart:user-42", "{\"items\":[\"sku1\",\"sku2\"],\"total\":39.98}");
        put("cart:user-99", "{\"items\":[\"sku3\"],\"total\":12.50}");
        put("session:abc123", "{\"userId\":42,\"expiresAt\":1234567890}");

        System.out.println("GET cart:user-42 -> " + get("cart:user-42")); // fast, exact key
        System.out.println("GET missing:key -> " + get("missing:key")); // null, no match

        // Level 3: "find carts over $30" - the store cannot help; the APPLICATION must scan every value.
        System.out.println("finding carts over $30.00 (manual scan, store provides NO query support):");
        for (Map.Entry<String, String> entry : store.entrySet()) {
            if (!entry.getKey().startsWith("cart:")) continue;
            String value = entry.getValue();
            double total = Double.parseDouble(value.split("\"total\":")[1].replace("}", ""));
            if (total > 30.0) {
                System.out.println("  " + entry.getKey() + " -> total = " + total);
            }
        }
    }
}
```

**How to run:** save as `KeyValueStores.java`, then run `java KeyValueStores.java`.

## 6. Walkthrough

1. `put` and `get` operate purely on `key` and an opaque `String` value — the store (`store`, a `HashMap`) never looks inside that string at all, mirroring how a real key-value store treats a value as an undifferentiated blob of bytes.
2. `get("cart:user-42")` returns the exact stored blob directly — a single, fast operation.
3. `get("missing:key")` returns `null` — a plain miss, with no fallback query capability.
4. Finding carts over `$30` requires the application to iterate every entry, filter by key prefix itself (`"cart:"`), then manually parse each value's `total` field out of the raw string — work a relational database's `WHERE total > 30` would do internally, but a key-value store leaves entirely to the caller.
5. The manual scan finds only `cart:user-42` (total `39.98`), demonstrating both that the answer is reachable, and that reaching it required work the store itself provided zero help with.

## 7. Gotchas & takeaways

> Gotcha: a key-value store's speed comes specifically from *not* supporting queries beyond exact-key lookup; trying to bolt on ad-hoc filtering by scanning every value, as the example above does, does not scale — if you need to query by something other than the key, you need to design that access pattern into your keys up front, or choose a different kind of store.

- Key-value stores are the simplest, fastest NoSQL model, ideal when every access is "fetch by exact ID."
- The value is opaque to the store; all interpretation of its contents is the application's responsibility.
- Related concepts: [Document stores](0076-document-stores.md) (adds the ability to query inside the value), [Access-pattern-first data modeling](0082-access-pattern-first-data-modeling.md) (designing keys around exactly the lookups you will actually need).
