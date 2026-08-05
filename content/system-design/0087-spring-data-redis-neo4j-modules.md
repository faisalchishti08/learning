---
card: system-design
gi: 87
slug: spring-data-redis-neo4j-modules
title: "Spring Data Redis / Neo4j modules"
---

## 1. What it is

Beyond using Redis purely as a cache (covered earlier in this section), **Spring Data Redis** also offers a full repository module — `@RedisHash` and `CrudRepository` — for using Redis as a primary key-value data store, not just a cache. **Spring Data Neo4j** brings the same repository pattern to Neo4j, a graph database, with `@Node` and `@Relationship` annotations mapping Java objects directly to graph nodes and edges.

## 2. Why & when

Both modules extend the same Spring Data repository pattern used by JPA, MongoDB, and Cassandra, to two more specialized store types. Reach for the Redis repository module when Redis itself — not a relational database behind a cache — is the actual system of record for fast, simple, key-based data (a leaderboard, a real-time counter, a session store treated as primary data). Reach for Spring Data Neo4j whenever your application's core data is relationship-heavy and you want the graph traversal queries covered earlier in this section, expressed through the same familiar repository interface style.

## 3. Core concept

**Spring Data Redis as a primary store — `@RedisHash`:**

```java
@RedisHash("sessions")
public class UserSession {
    @Id
    private String id;
    private String userId;
    @TimeToLive
    private Long ttlSeconds; // Redis TTL, expressed declaratively
}

public interface SessionRepository extends CrudRepository<UserSession, String> {
    List<UserSession> findByUserId(String userId);
}
```

This is a different usage from `@Cacheable`: here, Redis holds the actual data (with `@TimeToLive` mapping directly to a Redis key expiry), not a cached copy of data whose source of truth is a separate database.

**Spring Data Neo4j — `@Node` and `@Relationship`:**

```java
@Node("Person")
public class Person {
    @Id @GeneratedValue
    private Long id;
    private String name;

    @Relationship(type = "FOLLOWS", direction = Relationship.Direction.OUTGOING)
    private List<Person> follows; // maps directly to graph edges
}

public interface PersonRepository extends Neo4jRepository<Person, Long> {
    List<Person> findByName(String name);

    @Query("MATCH (p:Person {name: $name})-[:FOLLOWS*1..2]->(fof) RETURN DISTINCT fof")
    List<Person> findFriendsOfFriends(String name); // multi-hop traversal, expressed as Cypher
}
```

The `follows` field is not a foreign key column — Spring Data Neo4j maps it directly to `FOLLOWS` relationships in the graph, and a custom `@Query` can use **Cypher**, Neo4j's graph query language, for traversal queries beyond what a derived method name can express.

**The common thread across every Spring Data module:** whether the underlying store is relational, document, wide-column, key-value, or graph, the programming model stays the same — annotate a class, extend a repository interface, and let Spring generate the implementation, with only the annotations and generated query language changing to match the store.

## 4. Diagram

```
Same repository pattern, different stores underneath:

  JpaRepository        -> generates SQL              (relational)
  MongoRepository       -> generates MongoDB queries   (document)
  CassandraRepository   -> generates CQL, key-constrained (wide-column)
  CrudRepository (@RedisHash) -> generates Redis commands (key-value, primary store)
  Neo4jRepository       -> generates Cypher              (graph)

  findByUserId("u42")  -- Redis:  HGETALL / key scan on the userId secondary index
  findByName("Alice")  -- Neo4j:  MATCH (p:Person {name: "Alice"}) RETURN p
```
*Caption: the repository abstraction is shared across every Spring Data module; only the generated query language changes to match the underlying store.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling a Redis-backed primary repository and a Neo4j-backed graph repository, side by side

```java
import java.util.*;

public class SpringDataRedisNeo4jSim {

    // --- Spring Data Redis, as a PRIMARY store (not a cache) ---
    record UserSession(String id, String userId, long ttlSeconds) {}
    static final Map<String, UserSession> redisSessions = new HashMap<>(); // @RedisHash("sessions")

    static void saveSession(UserSession s) { redisSessions.put(s.id(), s); } // CrudRepository.save
    static List<UserSession> findByUserId(String userId) {
        return redisSessions.values().stream().filter(s -> s.userId().equals(userId)).toList();
    }

    // --- Spring Data Neo4j, mapping objects directly to graph nodes/edges ---
    static class Person {
        String name;
        List<Person> follows = new ArrayList<>(); // @Relationship(type = "FOLLOWS")
        Person(String name) { this.name = name; }
    }
    static final Map<String, Person> neo4jGraph = new HashMap<>(); // @Node("Person")

    static void save(Person p) { neo4jGraph.put(p.name, p); } // Neo4jRepository.save

    // Models the custom @Query Cypher traversal: friends of friends, 1-2 hops.
    static List<String> findFriendsOfFriends(String name) {
        Set<String> visited = new LinkedHashSet<>();
        Queue<Person> frontier = new LinkedList<>();
        frontier.add(neo4jGraph.get(name));
        for (int hop = 0; hop < 2; hop++) {
            Queue<Person> next = new LinkedList<>();
            for (Person p : frontier) {
                for (Person f : p.follows) {
                    if (visited.add(f.name)) next.add(f);
                }
            }
            frontier = next;
        }
        return new ArrayList<>(visited);
    }

    public static void main(String[] args) {
        saveSession(new UserSession("sess-1", "user-42", 3600));
        saveSession(new UserSession("sess-2", "user-42", 3600));
        saveSession(new UserSession("sess-3", "user-99", 3600));

        System.out.println("Redis-backed repository, findByUserId(\"user-42\"):");
        for (UserSession s : findByUserId("user-42")) System.out.println("  " + s.id());

        Person alice = new Person("Alice"), bob = new Person("Bob"), cid = new Person("Cid");
        alice.follows.add(bob);
        bob.follows.add(cid);
        save(alice); save(bob); save(cid);

        System.out.println("Neo4j-backed repository, findFriendsOfFriends(\"Alice\") (Cypher-style traversal):");
        System.out.println("  " + findFriendsOfFriends("Alice"));
    }
}
```

**How to run:** save as `SpringDataRedisNeo4jSim.java`, run `java SpringDataRedisNeo4jSim.java` (JDK 17+). A real Spring Boot app needs `spring-boot-starter-data-redis` (with `@RedisHash` classes) or `spring-boot-starter-data-neo4j` (with `@Node` classes), plus a running Redis or Neo4j instance respectively.

## 6. Walkthrough

1. `saveSession` stores each `UserSession` in `redisSessions`, mirroring `CrudRepository.save` against a Redis-backed `@RedisHash`.
2. `findByUserId("user-42")` filters for matching sessions, returning `sess-1` and `sess-2` — mirroring a derived query method against a Redis secondary index on `userId`, distinct from `@Cacheable`'s role of caching another database's data (here, Redis itself is the only place this data lives).
3. `alice.follows.add(bob)` and `bob.follows.add(cid)` build direct object references between `Person` instances, mirroring how `@Relationship` maps Java object references directly to graph edges rather than foreign key columns.
4. `findFriendsOfFriends("Alice")` performs the same two-hop breadth-first traversal shown in the graph databases tutorial, this time framed as what a `@Query` with a Cypher `MATCH ... -[:FOLLOWS*1..2]->` pattern would return: `[Bob, Cid]`.
5. Both repositories — Redis-backed and Neo4j-backed — are used through the exact same `save`/`findBy...` shape as the JPA, MongoDB, and Cassandra repositories from earlier tutorials, even though the underlying stores and their generated query languages are completely different.

## 7. Gotchas & takeaways

> **Gotcha:** using Spring Data Redis as a primary data store (via `@RedisHash`) rather than as a cache means Redis's durability characteristics now matter for real, non-cache data — unlike a cache, where losing data on a crash just means a slower reload from the database, losing a `@RedisHash`-backed session store with no persistence configured means losing that data permanently; enable Redis persistence (RDB or AOF) if it is genuinely your system of record.

- Every Spring Data module — JPA, MongoDB, Cassandra, Redis, Neo4j — shares the same repository programming model, differing only in the store-specific annotations and the query language generated underneath.
- Spring Data Redis has two distinct roles: a `CacheManager` backing `@Cacheable` (a cache, covered earlier), or a `CrudRepository` backing `@RedisHash` (a primary store) — know which one a given piece of code is using.
- Related concepts: [Redis / Memcached as a cache provider](0060-redis-memcached-as-a-cache-provider.md) and [Spring Data Redis for distributed caching](0061-spring-data-redis-for-distributed-caching.md) (Redis's caching role, contrasted with its primary-store role here), [Graph databases](0078-graph-databases.md) (the underlying traversal model Spring Data Neo4j wraps).
