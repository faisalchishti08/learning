---
card: spring-data
gi: 123
slug: opsfor-operations-value-list-set-zset-hash-geo-hyperloglog-s
title: "Opsfor* operations (Value/List/Set/ZSet/Hash/Geo/HyperLogLog/Stream)"
---

## 1. What it is

`RedisTemplate` exposes one `opsFor*()` method per Redis data structure: `opsForValue()` (simple strings, already covered), `opsForList()`, `opsForSet()`, `opsForZSet()` (sorted sets), `opsForHash()`, `opsForGeo()`, `opsForHyperLogLog()`, and `opsForStream()` (the last covered in its own later card). Each returns an operations object with methods matching that data structure's native Redis commands.

```java
redisTemplate.opsForList().rightPush("order:1:events", "CREATED");
redisTemplate.opsForSet().add("order:1:tags", "urgent", "gift-wrap");
redisTemplate.opsForZSet().add("leaderboard", "user-42", 1500.0);
redisTemplate.opsForHash().put("order:1", "status", "PENDING");
```

## 2. Why & when

Redis isn't just a key-value string store — it natively supports several richer data structures, each with its own set of atomic, server-side operations. Modeling "the last 10 events for this order" as a Redis **list**, "which tags apply to this order" as a **set**, or "top scores" as a **sorted set** lets the database do the structural work (ordering, deduplication, ranking) instead of the application fetching a blob and manipulating it in memory.

Reach for the right `opsFor*()` when the shape of your data matches a specific Redis structure:

- `opsForList()` — an ordered sequence with fast push/pop at either end: an event log, a work queue, "recently viewed" history.
- `opsForSet()` — unordered, automatically deduplicated membership: tags, unique visitor IDs, "users who did X."
- `opsForZSet()` — a set where every member has a score, kept sorted automatically: leaderboards, rate-limiting windows, priority queues.
- `opsForHash()` — a single key holding multiple named fields, like a mini-document: storing an object's fields without a full JSON serialization round trip for partial updates.
- `opsForGeo()` — geospatial points with built-in radius/distance queries: "orders being delivered within 5km."
- `opsForHyperLogLog()` — approximate, extremely memory-efficient unique-count estimation: "roughly how many distinct visitors today," when exact counts aren't worth the memory cost.

## 3. Core concept

```
 opsForValue()       "order:1:status" -> "PENDING"                          (one string)
 opsForList()         "order:1:events" -> ["CREATED", "PACKED", "SHIPPED"]   (ordered sequence)
 opsForSet()          "order:1:tags"   -> {"urgent", "gift-wrap"}            (unordered, unique)
 opsForZSet()         "leaderboard"    -> {"user-42": 1500.0, "user-7": 900.0}   (unique, SORTED by score)
 opsForHash()         "order:1"        -> {"status": "PENDING", "total": "50.0"} (named fields under one key)
```

Each Redis key holds exactly one of these structures at a time — the operations object you call must match the structure the key was created with.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Different opsFor methods target different native Redis data structures under different keys">
  <rect x="20" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="90" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">opsForList()</text>

  <rect x="180" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="250" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">opsForSet()</text>

  <rect x="340" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="410" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">opsForZSet()</text>

  <rect x="500" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="560" y="44" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">opsForHash()</text>

  <rect x="20" y="90" width="140" height="55" rx="6" fill="#6db33f22" stroke="#6db33f" stroke-width="1.3"/>
  <text x="90" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">LIST</text>
  <text x="90" y="126" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">[CREATED, PACKED,</text>
  <text x="90" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">SHIPPED]</text>

  <rect x="180" y="90" width="140" height="55" rx="6" fill="#6db33f22" stroke="#6db33f" stroke-width="1.3"/>
  <text x="250" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">SET</text>
  <text x="250" y="126" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">{urgent,</text>
  <text x="250" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">gift-wrap}</text>

  <rect x="340" y="90" width="140" height="55" rx="6" fill="#6db33f22" stroke="#6db33f" stroke-width="1.3"/>
  <text x="410" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ZSET (sorted)</text>
  <text x="410" y="126" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">user-42: 1500</text>
  <text x="410" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">user-7: 900</text>

  <rect x="500" y="90" width="120" height="55" rx="6" fill="#6db33f22" stroke="#6db33f" stroke-width="1.3"/>
  <text x="560" y="112" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">HASH</text>
  <text x="560" y="126" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">status: PENDING</text>
  <text x="560" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">total: 50.0</text>
</svg>

Four different `opsFor*()` calls, four different native Redis storage shapes, each suited to a different access pattern.

## 5. Runnable example

The scenario: tracking an order's lifecycle using several Redis structures at once, evolving from a list-based event log, to a sorted set tracking a "most active customers" leaderboard, to combining a hash (structured order fields) with a set (tags) in one coherent operation.

### Level 1 — Basic

Model `opsForList()`: an append-only, ordered event log per order.

```java
import java.util.*;

public class OpsForLevel1 {
    public static void main(String[] args) {
        RedisTemplate redisTemplate = new RedisTemplate();

        redisTemplate.opsForList().rightPush("order:1:events", "CREATED");
        redisTemplate.opsForList().rightPush("order:1:events", "PACKED");
        redisTemplate.opsForList().rightPush("order:1:events", "SHIPPED");

        List<String> events = redisTemplate.opsForList().range("order:1:events", 0, -1); // 0..-1 = whole list
        System.out.println("Events in order: " + events);

        String mostRecent = redisTemplate.opsForList().index("order:1:events", -1); // last element
        System.out.println("Most recent event: " + mostRecent);
    }
}

class RedisServer { Map<String, List<String>> lists = new HashMap<>(); }

class ListOperations {
    private final RedisServer server;
    ListOperations(RedisServer server) { this.server = server; }
    void rightPush(String key, String value) { server.lists.computeIfAbsent(key, k -> new ArrayList<>()).add(value); }
    List<String> range(String key, int start, int end) {
        List<String> list = server.lists.getOrDefault(key, List.of());
        int actualEnd = end == -1 ? list.size() - 1 : end;
        return list.subList(start, actualEnd + 1);
    }
    String index(String key, int idx) {
        List<String> list = server.lists.getOrDefault(key, List.of());
        return list.get(idx < 0 ? list.size() + idx : idx);
    }
}

class RedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ListOperations listOps = new ListOperations(server);
    ListOperations opsForList() { return listOps; }
}
```

How to run: `java OpsForLevel1.java`

`rightPush` mirrors Redis's `RPUSH`, appending to the end of the list stored under `"order:1:events"`. `range(key, 0, -1)` mirrors `LRANGE key 0 -1`, Redis's idiom for "the whole list" (`-1` means "last element, inclusive"). `index(key, -1)` mirrors `LINDEX key -1`, fetching just the last element without transferring the whole list.

### Level 2 — Intermediate

Model `opsForZSet()`: a sorted set tracking customer activity scores, always kept in rank order by Redis itself.

```java
import java.util.*;
import java.util.stream.*;

public class OpsForLevel2 {
    public static void main(String[] args) {
        RedisTemplate redisTemplate = new RedisTemplate();

        redisTemplate.opsForZSet().add("customer:activity", "alice", 15.0);
        redisTemplate.opsForZSet().add("customer:activity", "bob", 42.0);
        redisTemplate.opsForZSet().add("customer:activity", "carol", 8.0);

        redisTemplate.opsForZSet().incrementScore("customer:activity", "alice", 30.0); // alice: 15 -> 45

        List<String> topThree = redisTemplate.opsForZSet().reverseRange("customer:activity", 0, 2); // highest score first
        System.out.println("Top 3 most active customers: " + topThree);

        Double bobScore = redisTemplate.opsForZSet().score("customer:activity", "bob");
        System.out.println("Bob's score: " + bobScore);
    }
}

class RedisServer { Map<String, TreeMap<Double, List<String>>> zsets = new HashMap<>(); Map<String, Map<String, Double>> zsetScores = new HashMap<>(); }

class ZSetOperations {
    private final RedisServer server;
    ZSetOperations(RedisServer server) { this.server = server; }

    void add(String key, String member, double score) {
        server.zsetScores.computeIfAbsent(key, k -> new HashMap<>()).put(member, score);
    }
    double incrementScore(String key, String member, double delta) {
        Map<String, Double> scores = server.zsetScores.computeIfAbsent(key, k -> new HashMap<>());
        double updated = scores.getOrDefault(member, 0.0) + delta;
        scores.put(member, updated);
        return updated;
    }
    List<String> reverseRange(String key, int start, int end) { // ZREVRANGE -- highest score first
        Map<String, Double> scores = server.zsetScores.getOrDefault(key, Map.of());
        List<String> sorted = scores.entrySet().stream()
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .map(Map.Entry::getKey).collect(Collectors.toList());
        return sorted.subList(start, Math.min(end + 1, sorted.size()));
    }
    Double score(String key, String member) { return server.zsetScores.getOrDefault(key, Map.of()).get(member); }
}

class RedisTemplate {
    private final RedisServer server = new RedisServer();
    private final ZSetOperations zsetOps = new ZSetOperations(server);
    ZSetOperations opsForZSet() { return zsetOps; }
}
```

How to run: `java OpsForLevel2.java`

`add` mirrors `ZADD`, `incrementScore` mirrors `ZINCRBY` (an atomic score bump, avoiding a read-modify-write race exactly like `opsForValue().increment` did in the previous card), and `reverseRange` mirrors `ZREVRANGE`, which returns members ordered by score, highest first — Redis maintains this order natively, so no application-side sorting is ever needed to answer "who's in the top 3 right now."

### Level 3 — Advanced

Combine `opsForHash()` (structured order fields) with `opsForSet()` (tags) in one coherent operation, matching how a real service composes multiple Redis structures to represent one logical entity.

```java
import java.util.*;

public class OpsForLevel3 {
    static void createOrder(RedisTemplate redisTemplate, String orderId, String status, double total, String... tags) {
        String hashKey = "order:" + orderId;
        redisTemplate.opsForHash().put(hashKey, "status", status); // HSET order:1 status PENDING
        redisTemplate.opsForHash().put(hashKey, "total", String.valueOf(total));

        String setKey = "order:" + orderId + ":tags";
        for (String tag : tags) redisTemplate.opsForSet().add(setKey, tag); // SADD order:1:tags urgent gift-wrap
    }

    static void printOrderSummary(RedisTemplate redisTemplate, String orderId) {
        Map<String, String> fields = redisTemplate.opsForHash().entries("order:" + orderId); // HGETALL
        Set<String> tags = redisTemplate.opsForSet().members("order:" + orderId + ":tags");   // SMEMBERS
        System.out.println("Order " + orderId + ": " + fields + ", tags=" + tags);
    }

    public static void main(String[] args) {
        RedisTemplate redisTemplate = new RedisTemplate();

        createOrder(redisTemplate, "1", "PENDING", 150.0, "urgent", "gift-wrap");
        createOrder(redisTemplate, "2", "SHIPPED", 45.5); // no tags

        printOrderSummary(redisTemplate, "1");
        printOrderSummary(redisTemplate, "2");

        redisTemplate.opsForHash().put("order:2", "status", "DELIVERED"); // partial update -- ONLY this field changes
        printOrderSummary(redisTemplate, "2");
    }
}

class RedisServer {
    Map<String, Map<String, String>> hashes = new HashMap<>();
    Map<String, Set<String>> sets = new HashMap<>();
}

class HashOperations {
    private final RedisServer server;
    HashOperations(RedisServer server) { this.server = server; }
    void put(String key, String field, String value) { server.hashes.computeIfAbsent(key, k -> new LinkedHashMap<>()).put(field, value); }
    Map<String, String> entries(String key) { return server.hashes.getOrDefault(key, Map.of()); }
}

class SetOperations {
    private final RedisServer server;
    SetOperations(RedisServer server) { this.server = server; }
    void add(String key, String member) { server.sets.computeIfAbsent(key, k -> new LinkedHashSet<>()).add(member); }
    Set<String> members(String key) { return server.sets.getOrDefault(key, Set.of()); }
}

class RedisTemplate {
    private final RedisServer server = new RedisServer();
    private final HashOperations hashOps = new HashOperations(server);
    private final SetOperations setOps = new SetOperations(server);
    HashOperations opsForHash() { return hashOps; }
    SetOperations opsForSet() { return setOps; }
}
```

How to run: `java OpsForLevel3.java`

`createOrder` writes structured fields via `opsForHash().put` (mirroring `HSET`) and tags via `opsForSet().add` (mirroring `SADD`) — two different Redis structures under two related keys, representing one logical order. The later partial update, `redisTemplate.opsForHash().put("order:2", "status", "DELIVERED")`, changes only the `status` field of order `2`'s hash without touching `total` or needing to rewrite the whole record — a key advantage a hash has over storing the whole order as one serialized JSON string, where any change requires reading, modifying, and rewriting the entire value.

## 6. Walkthrough

Execution starts in `main` for Level 3. `createOrder(redisTemplate, "1", "PENDING", 150.0, "urgent", "gift-wrap")` writes `status` and `total` into the hash at key `"order:1"`, then adds `"urgent"` and `"gift-wrap"` to the set at key `"order:1:tags"`. `createOrder(redisTemplate, "2", "SHIPPED", 45.5)` does the same for order `2` but with no tags, so `"order:2:tags"` is never created.

`printOrderSummary(redisTemplate, "1")` reads back `entries("order:1")` (all hash fields) and `members("order:1:tags")` (the whole tag set) and prints both together. `printOrderSummary(redisTemplate, "2")` does the same, showing an empty tag set for order `2` since nothing was ever added to that key.

`redisTemplate.opsForHash().put("order:2", "status", "DELIVERED")` then overwrites *only* the `status` field within order `2`'s existing hash — `total` remains `45.5`, untouched, because a hash field update targets that one field specifically rather than replacing the whole value. `printOrderSummary(redisTemplate, "2")` is called again and shows `status` updated to `DELIVERED` while `total` is unchanged.

```
Order 1: {status=PENDING, total=150.0}, tags=[urgent, gift-wrap]
Order 2: {status=SHIPPED, total=45.5}, tags=[]
Order 2: {status=DELIVERED, total=45.5}, tags=[]
```

In real Redis, this partial-field update sends `HSET order:2 status DELIVERED` — a single, tiny command that only touches the one field in the hash, in contrast to updating a JSON-serialized string value (as `opsForValue()` would require), which needs the *entire* value read, modified, and rewritten even to change one field.

## 7. Gotchas & takeaways

> Gotcha: calling the wrong `opsFor*()` method against a key created with a different structure throws an error from Redis (`WRONGTYPE Operation against a key holding the wrong kind of value`) — a key is either a list, a set, a sorted set, a hash, or a plain string; it can't be more than one at once.

> Gotcha: `opsForList().range(key, 0, -1)` (or the equivalent `LRANGE`) loads the *entire* list into memory — for a list that can grow unbounded (an ever-appended event log with no trimming), this can become a real memory and latency problem; consider `LTRIM` to cap list length, or paginated ranges instead of always fetching everything.

- Each `opsFor*()` method targets a distinct native Redis data structure, matching the specific atomic commands that structure supports (`RPUSH`/`LRANGE` for lists, `SADD`/`SMEMBERS` for sets, `ZADD`/`ZREVRANGE` for sorted sets, `HSET`/`HGETALL` for hashes).
- Choosing the right structure lets Redis do structural work (ordering, deduplication, ranking) server-side, instead of the application fetching a blob and re-deriving that structure in memory every time.
- `opsForHash()` supports true partial updates — changing one field without touching the rest of the record — which a single serialized string value (via `opsForValue()`) cannot do as efficiently.
- `opsForZSet()`'s score-based ordering is maintained by Redis automatically, making "top N" and "current rank" queries fast without any application-side sorting.
