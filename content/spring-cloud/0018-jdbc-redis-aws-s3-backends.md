---
card: spring-cloud
gi: 18
slug: jdbc-redis-aws-s3-backends
title: "JDBC / Redis / AWS S3 backends"
---

## 1. What it is

Beyond Git, native, and Vault, Spring Cloud Config Server supports several additional backends for less common but still valid scenarios: JDBC (reading key-value configuration rows from a relational database table), Redis (configuration stored as Redis hash entries), and AWS S3 (configuration files stored as objects in an S3 bucket, similar in spirit to the Git backend but backed by object storage instead of version control).

```yaml
# JDBC backend
spring:
  cloud:
    config:
      server:
        jdbc:
          sql: SELECT "key", "value" FROM properties WHERE application=? AND profile=? AND label=?

# S3 backend
spring:
  cloud:
    config:
      server:
        awss3:
          bucket: my-config-bucket
```

## 2. Why & when

Every backend covered so far assumes configuration lives in files (Git, filesystem) or a secrets engine (Vault) with its own tooling. Some organizations already have configuration living somewhere else entirely — an existing database table used by legacy tooling, a Redis instance already used for other shared state, or an S3 bucket that's the standard artifact store in an AWS-centric infrastructure. These backends let the Config Server integrate with that existing infrastructure rather than requiring a migration to Git just to use Spring Cloud Config.

Reach for these alternative backends when:

- JDBC: configuration already lives in (or needs to be queried from) a relational database, often because of existing tooling or a requirement to manage config through the same database-backed admin UI already used for other data.
- Redis: configuration needs extremely fast reads and the organization already operates Redis infrastructure, and Git-level versioning/audit isn't a hard requirement for this particular configuration.
- AWS S3: the organization is AWS-centric and prefers object storage (with S3 versioning, IAM-based access control, and cross-region replication) over running or depending on a separate Git hosting service.

## 3. Core concept

```
 JDBC backend:
   properties table: (application, profile, label, key, value)
   SELECT value FROM properties WHERE application='payment-service' AND profile='production' AND key='db.pool.size'

 Redis backend:
   HGET config:payment-service:production db.pool.size

 S3 backend:
   s3://my-config-bucket/payment-service-production.yml

 All THREE ultimately answer the SAME question the Config Server always asks --
 "what's the config for {application}/{profile}/{label}" -- just sourced differently.
```

Every backend, regardless of the underlying storage technology, answers the same `{application}/{profile}/{label}` question the Config Server's HTTP API exposes uniformly to clients.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three different storage technologies each plug into the same Config Server abstraction, answering the same application profile label query">
  <rect x="20" y="20" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">JDBC (RDBMS)</text>

  <rect x="20" y="70" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="95" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Redis</text>

  <rect x="20" y="120" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="145" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">AWS S3</text>

  <line x1="170" y1="40" x2="260" y2="80" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a38)"/>
  <line x1="170" y1="90" x2="260" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a38)"/>
  <line x1="170" y1="140" x2="260" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a38)"/>

  <rect x="270" y="65" width="180" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>

  <defs><marker id="a38" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each backend technology plugs into the same Config Server abstraction, answering the identical application/profile/label query.

## 5. Runnable example

The scenario: resolving `payment-service`'s production configuration, evolving from a JDBC-style query against a table stand-in, to a Redis-style hash lookup, to a unified resolver that can be pointed at either backend interchangeably — demonstrating that from the Config Server's perspective, the actual storage technology is an implementation detail behind one consistent lookup contract.

### Level 1 — Basic

Model a JDBC-style backend: a flat table of rows, queried by application/profile/key.

```java
import java.util.*;

public class AltBackendsLevel1 {
    public static void main(String[] args) {
        JdbcConfigTable table = new JdbcConfigTable();
        table.insert("payment-service", "production", "db.pool.size", "50");
        table.insert("payment-service", "production", "payment.gateway", "stripe-live");

        Map<String, String> resolved = table.selectWhere("payment-service", "production");
        System.out.println("JDBC-resolved config: " + resolved);
    }
}

class JdbcConfigTable {
    // Simulates rows in a "properties" table: (application, profile, key, value)
    private final List<String[]> rows = new ArrayList<>();
    void insert(String application, String profile, String key, String value) {
        rows.add(new String[]{application, profile, key, value});
    }
    Map<String, String> selectWhere(String application, String profile) {
        Map<String, String> result = new HashMap<>();
        for (String[] row : rows) {
            if (row[0].equals(application) && row[1].equals(profile)) result.put(row[2], row[3]);
        }
        return result;
    }
}
```

How to run: `java AltBackendsLevel1.java`

`selectWhere` mirrors the SQL query the JDBC backend actually runs against a real database table — filtering rows by `application` and `profile`, and assembling matching `key`/`value` pairs into the resolved configuration map.

### Level 2 — Intermediate

Add a Redis-style hash-based backend alongside it, showing the same logical query answered by a structurally different storage mechanism.

```java
import java.util.*;

public class AltBackendsLevel2 {
    public static void main(String[] args) {
        RedisConfigStore redis = new RedisConfigStore();
        redis.hset("config:payment-service:production", "db.pool.size", "50");
        redis.hset("config:payment-service:production", "payment.gateway", "stripe-live");

        Map<String, String> resolved = redis.hgetall("config:payment-service:production");
        System.out.println("Redis-resolved config: " + resolved);
    }
}

// Stands in for a Redis HASH keyed by "config:{application}:{profile}".
class RedisConfigStore {
    private final Map<String, Map<String, String>> hashes = new HashMap<>();
    void hset(String hashKey, String field, String value) {
        hashes.computeIfAbsent(hashKey, k -> new HashMap<>()).put(field, value);
    }
    Map<String, String> hgetall(String hashKey) { return hashes.getOrDefault(hashKey, Map.of()); }
}
```

How to run: `java AltBackendsLevel2.java`

`hgetall` mirrors Redis's own `HGETALL` command against a hash keyed by `config:{application}:{profile}` — a completely different underlying data structure and access pattern from the JDBC table scan in Level 1, but resolving to the same shape of result.

### Level 3 — Advanced

Build a unified resolver behind a common interface, pointed interchangeably at either backend — demonstrating the Config Server's own backend-agnostic contract in action.

```java
import java.util.*;

public class AltBackendsLevel3 {
    public static void main(String[] args) {
        ConfigBackend jdbcBackend = new JdbcBackend();
        jdbcBackend.store("payment-service", "production", Map.of("db.pool.size", "50"));

        ConfigBackend redisBackend = new RedisBackend();
        redisBackend.store("payment-service", "production", Map.of("db.pool.size", "50"));

        // The SAME resolver function works against EITHER backend.
        System.out.println("Via JDBC backend:  " + resolve(jdbcBackend, "payment-service", "production"));
        System.out.println("Via Redis backend: " + resolve(redisBackend, "payment-service", "production"));
    }

    static Map<String, String> resolve(ConfigBackend backend, String application, String profile) {
        return backend.fetch(application, profile);
    }
}

interface ConfigBackend {
    void store(String application, String profile, Map<String, String> values);
    Map<String, String> fetch(String application, String profile);
}

class JdbcBackend implements ConfigBackend {
    private final List<String[]> rows = new ArrayList<>();
    public void store(String application, String profile, Map<String, String> values) {
        values.forEach((k, v) -> rows.add(new String[]{application, profile, k, v}));
    }
    public Map<String, String> fetch(String application, String profile) {
        Map<String, String> result = new HashMap<>();
        for (String[] row : rows) if (row[0].equals(application) && row[1].equals(profile)) result.put(row[2], row[3]);
        return result;
    }
}

class RedisBackend implements ConfigBackend {
    private final Map<String, Map<String, String>> hashes = new HashMap<>();
    public void store(String application, String profile, Map<String, String> values) {
        hashes.computeIfAbsent("config:" + application + ":" + profile, k -> new HashMap<>()).putAll(values);
    }
    public Map<String, String> fetch(String application, String profile) {
        return hashes.getOrDefault("config:" + application + ":" + profile, Map.of());
    }
}
```

How to run: `java AltBackendsLevel3.java`

`resolve` is written once, against the `ConfigBackend` interface, and produces identical output regardless of whether it's handed `JdbcBackend` (internally a list of rows scanned linearly) or `RedisBackend` (internally a hash keyed by a composed string) — exactly mirroring how a real Config Server exposes the same `{application}/{profile}/{label}` HTTP contract to clients no matter which of its supported backends is actually configured underneath.

## 6. Walkthrough

Execution starts in `main` for Level 3. Both backends are populated with identical `payment-service`/`production` data through their own `store` implementations — `JdbcBackend` appends rows to a flat list, `RedisBackend` populates a nested hash map keyed by a composed string.

`resolve(jdbcBackend, "payment-service", "production")` calls `jdbcBackend.fetch`, which scans `rows` looking for matches:

```
Via JDBC backend:  {db.pool.size=50}
```

`resolve(redisBackend, "payment-service", "production")` calls `redisBackend.fetch`, which does a direct hash lookup by the composed key `"config:payment-service:production"`:

```
Via Redis backend: {db.pool.size=50}
```

Both produce the same result despite completely different internal storage and lookup strategies — this is exactly the point of the Config Server's backend abstraction: application code, and even the Config Server's own request-handling logic, never needs to know or care which of JDBC, Redis, S3, Git, native, or Vault is actually answering the `{application}/{profile}` question underneath.

## 7. Gotchas & takeaways

> Gotcha: unlike Git, none of JDBC, Redis, or S3 (used plainly, without S3's own object versioning enabled) provide built-in change history or diff review out of the box — choosing one of these backends for convenience or existing-infrastructure-reuse reasons means separately deciding how configuration changes will be audited and reviewed, since that discipline doesn't come for free the way it does with Git.

> Gotcha: the JDBC backend's default SQL query expects a specific table/column shape (`application`, `profile`, `label`, `key`, `value`) — adapting it to an existing, differently-shaped configuration table requires overriding the SQL query explicitly, and a mismatch between the expected and actual schema surfaces as a runtime query failure, not a startup-time validation error.

- Beyond Git, native, and Vault, Spring Cloud Config Server supports JDBC, Redis, and AWS S3 backends for integrating with existing infrastructure rather than requiring a migration to Git.
- Every backend answers the identical `{application}/{profile}/{label}` question through the same Config Server HTTP contract — the storage technology is an implementation detail invisible to requesting clients.
- These alternative backends generally lack Git's built-in change history and review workflow — that discipline needs a separate, deliberate solution if it's required.
- Choosing a backend is about matching existing infrastructure and operational requirements (speed, existing tooling, audit needs) rather than any difference in what clients actually receive.
