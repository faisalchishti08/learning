---
card: spring-boot
gi: 217
slug: datamongotest-dataredistest-dataneo4jtest-etc
title: "@DataMongoTest / @DataRedisTest / @DataNeo4jTest / etc."
---

## 1. What it is

Spring Boot provides data-store-specific test slices for NoSQL and graph databases. Each slice loads only the relevant infrastructure: `@DataMongoTest` for MongoDB repositories (with Flapdoodle embedded MongoDB), `@DataRedisTest` for Redis repositories, `@DataNeo4jTest` for Neo4j (with embedded Neo4j), `@DataCassandraTest` for Cassandra, and `@DataLdapTest` for LDAP. All exclude the web layer, services, and JPA.

## 2. Why & when

| Slice | Use when |
|---|---|
| `@DataMongoTest` | Testing MongoDB repositories, document mapping, queries |
| `@DataRedisTest` | Testing `@RedisHash` repositories, `RedisTemplate` operations |
| `@DataNeo4jTest` | Testing Cypher queries, node/relationship mapping |
| `@DataCassandraTest` | Testing Cassandra repositories, CQL queries |
| `@DataLdapTest` | Testing LDAP repositories and `LdapTemplate` |
| `@DataElasticsearchTest` | Testing Elasticsearch repositories |

The same philosophy as all other slices: test one data layer in isolation, mock everything else.

## 3. Core concept

**`@DataMongoTest`:**
```java
@DataMongoTest
class ProductRepositoryTest {

    @Autowired ProductRepository repo;
    @Autowired MongoTemplate mongoTemplate;

    @Test
    void findByCategory_returnsDocuments() {
        mongoTemplate.insert(new Product("Laptop", "electronics", 999.00));
        mongoTemplate.insert(new Product("Mouse",  "electronics", 29.99));
        mongoTemplate.insert(new Product("Desk",   "furniture",   249.00));

        List<Product> electronics = repo.findByCategory("electronics");
        assertThat(electronics).hasSize(2);
    }
}
```

**`@DataRedisTest`:**
```java
@DataRedisTest
class SessionRepositoryTest {

    @Autowired SessionRepository repo;

    @Test
    void findById_returnsSession() {
        Session s = repo.save(new Session("u1", Instant.now()));
        Optional<Session> found = repo.findById(s.getId());
        assertThat(found).isPresent();
    }
}
```

**Embedded stores:** `@DataMongoTest` uses Flapdoodle embedded MongoDB (auto-configured). `@DataNeo4jTest` uses Neo4j's embedded driver (test jar). Neither requires a running Docker container for basic tests.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four NoSQL test slices side by side: DataMongoTest with Flapdoodle, DataRedisTest with embedded Redis, DataNeo4jTest with embedded Neo4j, DataCassandraTest requiring a real server or Testcontainers">
  <!-- DataMongoTest -->
  <rect x="10" y="25" width="155" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="87" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataMongoTest</text>
  <rect x="20" y="58" width="135" height="32" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="73" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">MongoRepository</text>
  <text x="87" y="85" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">MongoTemplate</text>
  <rect x="20" y="98" width="135" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="87" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Flapdoodle Embedded</text>
  <text x="87" y="125" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">MongoDB (auto)</text>
  <text x="87" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">de.flapdoodle.embed</text>
  <text x="87" y="163" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">.mongo dependency</text>
  <text x="87" y="175" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">no external server</text>

  <!-- DataRedisTest -->
  <rect x="177" y="25" width="155" height="155" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="254" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataRedisTest</text>
  <rect x="187" y="58" width="135" height="32" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="254" y="73" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">RedisRepository</text>
  <text x="254" y="85" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">RedisTemplate</text>
  <rect x="187" y="98" width="135" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="254" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No embedded Redis —</text>
  <text x="254" y="125" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">use Testcontainers or</text>
  <text x="254" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">com.redis.testcontainers</text>
  <text x="254" y="163" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">:redis-stack-server</text>
  <text x="254" y="175" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">for real Redis</text>

  <!-- DataNeo4jTest -->
  <rect x="344" y="25" width="155" height="155" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="421" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataNeo4jTest</text>
  <rect x="354" y="58" width="135" height="32" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="421" y="73" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Neo4jRepository</text>
  <text x="421" y="85" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">Neo4jClient, Neo4jTemplate</text>
  <rect x="354" y="98" width="135" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="421" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Embedded Neo4j (test jar)</text>
  <text x="421" y="125" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">neo4j-harness dependency</text>
  <text x="421" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">or Testcontainers</text>
  <text x="421" y="163" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">for Neo4j Docker</text>
  <text x="421" y="175" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">Cypher query testing</text>

  <!-- DataCassandraTest -->
  <rect x="511" y="25" width="160" height="155" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="591" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataCassandraTest</text>
  <rect x="521" y="58" width="140" height="32" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="591" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">CassandraRepository</text>
  <text x="591" y="85" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CassandraTemplate</text>
  <rect x="521" y="98" width="140" height="30" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="591" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No embedded Cassandra</text>
  <text x="591" y="125" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Testcontainers required</text>
  <text x="591" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">org.testcontainers</text>
  <text x="591" y="163" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">:cassandra</text>
  <text x="591" y="175" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CQL testing</text>
</svg>

MongoDB and Neo4j have embedded options for zero-setup tests; Redis and Cassandra require Testcontainers for a real server.

## 5. Runnable example

```java
// NoSqlTestSlicesDemo.java — simulates @DataMongoTest, @DataRedisTest, @DataNeo4jTest patterns
// How to run: java NoSqlTestSlicesDemo.java  (JDK 17+, no dependencies)
// Real use: each @DataXxxTest slice + appropriate embedded or Testcontainers backing store

import java.util.*;
import java.util.stream.Collectors;

public class NoSqlTestSlicesDemo {

    // ====== Shared types ======
    record Product(String id, String name, String category, double price) {
        Product(String name, String category, double price) {
            this(UUID.randomUUID().toString().substring(0,8), name, category, price);
        }
    }

    record Session(String id, String userId, long createdAt) {
        Session(String userId) { this(UUID.randomUUID().toString().substring(0,8), userId, System.currentTimeMillis()); }
    }

    record Person(String id, String name, int age) {
        Person(String name, int age) { this(UUID.randomUUID().toString().substring(0,8), name, age); }
    }

    // ====== @DataMongoTest: in-memory MongoDB simulation ======
    static class FakeMongoTemplate {
        final List<Product> products = new ArrayList<>();
        void insert(Product p) { products.add(p); System.out.println("  [Mongo INSERT] " + p.name()); }
    }

    static class ProductMongoRepository {
        private final FakeMongoTemplate tmpl;
        ProductMongoRepository(FakeMongoTemplate t) { this.tmpl = t; }
        List<Product> findByCategory(String cat) {
            return tmpl.products.stream().filter(p -> cat.equals(p.category())).collect(Collectors.toList());
        }
        List<Product> findByPriceLessThan(double max) {
            return tmpl.products.stream().filter(p -> p.price() < max).collect(Collectors.toList());
        }
    }

    // ====== @DataRedisTest: in-memory Redis simulation ======
    static class RedisSessionRepository {
        private final Map<String, Session> store = new LinkedHashMap<>();
        Session save(Session s) { store.put(s.id(), s); System.out.println("  [Redis HSET] session:" + s.id()); return s; }
        Optional<Session> findById(String id) { return Optional.ofNullable(store.get(id)); }
        void deleteById(String id) { store.remove(id); }
    }

    // ====== @DataNeo4jTest: in-memory graph simulation ======
    static class PersonNeo4jRepository {
        private final Map<String, Person> nodes = new LinkedHashMap<>();
        private final Map<String, Set<String>> friends = new LinkedHashMap<>(); // personId → friendIds

        Person save(Person p) { nodes.put(p.id(), p); return p; }
        Optional<Person> findByName(String name) { return nodes.values().stream().filter(p -> name.equals(p.name())).findFirst(); }
        void addFriendship(String id1, String id2) {
            friends.computeIfAbsent(id1, k -> new HashSet<>()).add(id2);
            friends.computeIfAbsent(id2, k -> new HashSet<>()).add(id1);
            System.out.println("  [Cypher] MERGE (a)-[:FRIENDS_WITH]-(b) a=" + id1 + " b=" + id2);
        }
        List<Person> findFriendsOf(String id) {
            return friends.getOrDefault(id, Set.of()).stream().map(nodes::get).collect(Collectors.toList());
        }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    public static void main(String[] args) {
        System.out.println("=== NoSQL Test Slices Demo ===\n");

        // --- @DataMongoTest ---
        System.out.println("=== @DataMongoTest (Flapdoodle Embedded MongoDB) ===");
        FakeMongoTemplate mongo = new FakeMongoTemplate();
        ProductMongoRepository productRepo = new ProductMongoRepository(mongo);

        mongo.insert(new Product("Laptop", "electronics", 999.00));
        mongo.insert(new Product("Mouse",  "electronics",  29.99));
        mongo.insert(new Product("Desk",   "furniture",   249.00));

        List<Product> electronics = productRepo.findByCategory("electronics");
        expect(electronics.size() == 2,                "2 electronics products");
        expect(electronics.stream().allMatch(p -> "electronics".equals(p.category())),
               "all are electronics");

        List<Product> cheap = productRepo.findByPriceLessThan(100.0);
        expect(cheap.size() == 1,                      "1 product under $100");
        expect("Mouse".equals(cheap.get(0).name()),    "cheap product is Mouse");

        // --- @DataRedisTest ---
        System.out.println("\n=== @DataRedisTest (Testcontainers / embedded) ===");
        RedisSessionRepository sessionRepo = new RedisSessionRepository();

        Session s1 = sessionRepo.save(new Session("user-alice"));
        Session s2 = sessionRepo.save(new Session("user-bob"));

        Optional<Session> found = sessionRepo.findById(s1.id());
        expect(found.isPresent(),                       "session found by id");
        expect("user-alice".equals(found.get().userId()), "correct user");

        sessionRepo.deleteById(s2.id());
        expect(sessionRepo.findById(s2.id()).isEmpty(), "session deleted");

        // --- @DataNeo4jTest ---
        System.out.println("\n=== @DataNeo4jTest (Embedded Neo4j / Testcontainers) ===");
        PersonNeo4jRepository personRepo = new PersonNeo4jRepository();

        Person alice = personRepo.save(new Person("Alice", 30));
        Person bob   = personRepo.save(new Person("Bob",   25));
        Person carol = personRepo.save(new Person("Carol", 35));

        personRepo.addFriendship(alice.id(), bob.id());
        personRepo.addFriendship(alice.id(), carol.id());

        List<Person> aliceFriends = personRepo.findFriendsOf(alice.id());
        expect(aliceFriends.size() == 2,               "Alice has 2 friends");
        expect(aliceFriends.stream().anyMatch(p -> "Bob".equals(p.name())),   "Bob is a friend");
        expect(aliceFriends.stream().anyMatch(p -> "Carol".equals(p.name())), "Carol is a friend");

        Optional<Person> byName = personRepo.findByName("Alice");
        expect(byName.isPresent() && byName.get().age() == 30, "find Alice by name");

        System.out.println("\n--- Setup requirements ---");
        System.out.println("@DataMongoTest: add de.flapdoodle.embed:de.flapdoodle.embed.mongo.spring30x");
        System.out.println("@DataRedisTest: use Testcontainers: @Container RedisContainer redis = new RedisContainer(...)");
        System.out.println("@DataNeo4jTest: add org.neo4j.test:neo4j-harness (embedded) OR Testcontainers");
        System.out.println("@DataCassandraTest: Testcontainers: @Container CassandraContainer cas = ...");
    }
}
```

**How to run:** `java NoSqlTestSlicesDemo.java`

## 6. Walkthrough

- **`@DataMongoTest`**: `MongoTemplate.insert` seeds documents. `findByCategory` queries by field — equivalent to `db.products.find({category:"electronics"})` in MongoDB. No MongoDB server required — Flapdoodle starts an embedded MongoDB process automatically.
- **`@DataRedisTest`**: `save` calls `RedisTemplate` to `HSET` the session hash. `findById` calls `HGETALL`. `deleteById` calls `DEL`. Unlike MongoDB, there's no embedded Redis — use Testcontainers or an in-process Redis mock.
- **`@DataNeo4jTest`**: `save` creates a `Person` node. `addFriendship` creates a `FRIENDS_WITH` relationship (Cypher `MERGE`). `findFriendsOf` traverses the relationship — this is the key advantage of a graph database that standard SQL can't express cleanly.
- The setup requirements at the end list exactly which Maven/Gradle dependencies are needed for each embedded option.

## 7. Gotchas & takeaways

> Flapdoodle embedded MongoDB downloads a MongoDB binary on first run — CI environments need outbound internet access, or you must pre-cache the binary. Use `de.flapdoodle.embed.mongo.defaultVersion` to pin the MongoDB version and avoid non-deterministic downloads.

> `@DataRedisTest` does NOT include an embedded Redis. It configures the Redis auto-configuration but needs a real Redis connection. Add `@ServiceConnection` with a Testcontainers `RedisContainer` or use `spring.data.redis.host=localhost` pointing to a locally running Redis.

- Each slice excludes other data stores: `@DataMongoTest` excludes JPA; `@DataNeo4jTest` excludes MongoDB.
- `@DataMongoTest` includes both `MongoTemplate` and reactive `ReactiveMongoTemplate` — both are available in the test context.
- `@DataNeo4jTest` wraps each test in a transaction that is rolled back — similar to `@DataJpaTest`.
- For multi-store tests (both MongoDB and Redis in the same test), use `@SpringBootTest` instead of a slice.
