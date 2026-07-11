---
card: spring-data
gi: 102
slug: connecting-mongoclient-settings
title: "Connecting (MongoClient settings)"
---

## 1. What it is

`MongoClientSettings` is the configuration object controlling how the underlying MongoDB driver connects to a database — connection string, connection pool size, timeouts, read preference, and write concern — the MongoDB-specific counterpart to the connection-factory/pooling concepts covered for R2DBC in the relational section.

```java
@Bean
MongoClientSettings mongoClientSettings() {
    return MongoClientSettings.builder()
        .applyConnectionString(new ConnectionString("mongodb://localhost:27017/mydb"))
        .applyToConnectionPoolSettings(builder -> builder.maxSize(50).minSize(5))
        .build();
}
```

## 2. Why & when

Every repository and template card in this section has quietly assumed a working connection to a MongoDB instance already exists. This card is about how that connection is actually configured — the connection string format, pool sizing (conceptually identical to the R2DBC connection-pooling card, just MongoDB-driver-specific in its API), and the write/read concern settings that determine MongoDB's own consistency guarantees for an operation.

Reach for explicit `MongoClientSettings` configuration specifically when:

- Connecting to anything beyond a default local MongoDB instance — a replica set, a sharded cluster, MongoDB Atlas, or any setup needing authentication, TLS, or non-default hosts/ports.
- Tuning connection pool size for production load, mirroring the same considerations as R2DBC connection pooling: too small causes contention, too large risks overwhelming the server.
- Setting a write concern (how many replica-set members must acknowledge a write before it's considered successful) or read preference (which replica-set members reads can be served from) — these directly trade off consistency guarantees against latency/availability.

## 3. Core concept

```
 ConnectionString: mongodb://[user:pass@]host1[:port1][,host2[:port2],...]/database?options

 MongoClientSettings.builder()
     .applyConnectionString(...)                        -- host(s), auth, database
     .applyToConnectionPoolSettings(b -> b.maxSize(50))   -- pooling, same rationale as R2DBC pooling
     .writeConcern(WriteConcern.MAJORITY)                  -- how many replicas must ack a write
     .readPreference(ReadPreference.secondaryPreferred())  -- which members can serve reads
     .build()
```

Connection configuration, pooling, and MongoDB's own consistency knobs (write concern, read preference) are all assembled through the same builder.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="MongoClientSettings assembles connection string, pool sizing, and consistency settings into one configuration object">
  <rect x="20" y="15" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">connection string</text>

  <rect x="230" y="15" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">pool settings</text>

  <rect x="440" y="15" width="180" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="530" y="37" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">write concern /</text>
  <text x="530" y="51" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">read preference</text>

  <rect x="180" y="95" width="280" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="120" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">MongoClientSettings (assembled)</text>

  <line x1="110" y1="60" x2="260" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#mc)"/>
  <line x1="320" y1="60" x2="320" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#mc)"/>
  <line x1="530" y1="60" x2="380" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#mc)"/>
  <defs><marker id="mc" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Three independent configuration concerns — connectivity, pooling, and consistency — assemble into one `MongoClientSettings` object.

## 5. Runnable example

The scenario: configuring a MongoDB connection, evolving from parsing a basic connection string, to adding pool-size configuration, to a write-concern/read-preference tradeoff decision encoded as executable logic.

### Level 1 — Basic

Model parsing a MongoDB connection string into its components, standing in for `ConnectionString`'s parsing behavior.

```java
import java.util.*;

record ParsedConnectionString(String host, int port, String database, Optional<String> username) {}

public class MongoConnectLevel1 {
    // Simplified parser for: mongodb://[user@]host[:port]/database
    static ParsedConnectionString parse(String connectionString) {
        String withoutScheme = connectionString.replace("mongodb://", "");
        String[] atSplit = withoutScheme.split("@", 2);
        String userPart = atSplit.length == 2 ? atSplit[0] : null;
        String rest = atSplit.length == 2 ? atSplit[1] : atSplit[0];

        String[] slashSplit = rest.split("/", 2);
        String hostPort = slashSplit[0];
        String database = slashSplit.length == 2 ? slashSplit[1] : "test";

        String[] hostPortSplit = hostPort.split(":");
        String host = hostPortSplit[0];
        int port = hostPortSplit.length == 2 ? Integer.parseInt(hostPortSplit[1]) : 27017;

        return new ParsedConnectionString(host, port, database, Optional.ofNullable(userPart));
    }

    public static void main(String[] args) {
        ParsedConnectionString parsed = parse("mongodb://appuser@localhost:27017/mydb");
        System.out.println("Host: " + parsed.host() + ", Port: " + parsed.port()
            + ", Database: " + parsed.database() + ", User: " + parsed.username());
    }
}
```

How to run: `java MongoConnectLevel1.java`

`parse` extracts host, port, database, and an optional username from a MongoDB connection string — this mirrors the parsing `ConnectionString` performs internally when passed to `MongoClientSettings.builder().applyConnectionString(...)`, feeding those extracted values into the driver's actual connection setup.

### Level 2 — Intermediate

Add pool-size configuration alongside the parsed connection string, matching `applyToConnectionPoolSettings(...)` — and note how directly this mirrors the R2DBC connection-pooling card's concerns.

```java
import java.util.*;

record ParsedConnectionString(String host, int port, String database) {}
record PoolSettings(int minSize, int maxSize) {}
record MongoClientSettings(ParsedConnectionString connection, PoolSettings pool) {}

public class MongoConnectLevel2 {
    static ParsedConnectionString parse(String connectionString) {
        String withoutScheme = connectionString.replace("mongodb://", "");
        String[] slashSplit = withoutScheme.split("/", 2);
        String[] hostPortSplit = slashSplit[0].split(":");
        return new ParsedConnectionString(hostPortSplit[0],
            hostPortSplit.length == 2 ? Integer.parseInt(hostPortSplit[1]) : 27017,
            slashSplit.length == 2 ? slashSplit[1] : "test");
    }

    // MongoClientSettings.builder().applyConnectionString(...).applyToConnectionPoolSettings(b -> b.maxSize(50).minSize(5)).build()
    static MongoClientSettings buildSettings(String connectionString, int minPoolSize, int maxPoolSize) {
        ParsedConnectionString conn = parse(connectionString);
        PoolSettings pool = new PoolSettings(minPoolSize, maxPoolSize);
        return new MongoClientSettings(conn, pool);
    }

    public static void main(String[] args) {
        MongoClientSettings settings = buildSettings("mongodb://localhost:27017/mydb", 5, 50);
        System.out.println("Connecting to " + settings.connection().host() + ":" + settings.connection().port()
            + "/" + settings.connection().database());
        System.out.println("Pool: min=" + settings.pool().minSize() + ", max=" + settings.pool().maxSize());
    }
}
```

How to run: `java MongoConnectLevel2.java`

`buildSettings` combines connection parsing with pool sizing into one settings object — exactly the same rationale as `ConnectionPoolConfiguration` from the R2DBC pooling card: a small `minSize` keeps idle resource usage low, while `maxSize` caps how many concurrent operations the connection pool can sustain before requests start waiting.

### Level 3 — Advanced

Add write-concern and read-preference decision logic, modeling the consistency-versus-performance tradeoff those settings represent.

```java
import java.util.*;

enum WriteConcern { W1, MAJORITY } // simplified: "acknowledge from 1 node" vs "acknowledge from a majority of replica set members"
enum ReadPreference { PRIMARY, SECONDARY_PREFERRED } // simplified: "always read the primary" vs "prefer secondaries when possible"

record ConsistencyProfile(WriteConcern writeConcern, ReadPreference readPreference, String rationale) {}

public class MongoConnectLevel3 {
    // Encodes the tradeoff: strict consistency (slower, safer) vs. higher throughput (faster, eventually consistent reads).
    static ConsistencyProfile chooseProfile(boolean isFinancialData, boolean readHeavyWorkload) {
        if (isFinancialData) {
            return new ConsistencyProfile(WriteConcern.MAJORITY, ReadPreference.PRIMARY,
                "financial data requires durability and strong consistency -- worth the extra write/read latency");
        }
        if (readHeavyWorkload) {
            return new ConsistencyProfile(WriteConcern.W1, ReadPreference.SECONDARY_PREFERRED,
                "read-heavy, non-critical data benefits from spreading reads to secondaries for higher throughput");
        }
        return new ConsistencyProfile(WriteConcern.W1, ReadPreference.PRIMARY,
            "default: fast writes, always-consistent reads from the primary");
    }

    public static void main(String[] args) {
        ConsistencyProfile financial = chooseProfile(true, false);
        ConsistencyProfile analytics = chooseProfile(false, true);
        ConsistencyProfile general = chooseProfile(false, false);

        System.out.println("Financial data: " + financial.writeConcern() + " / " + financial.readPreference());
        System.out.println("  Rationale: " + financial.rationale());
        System.out.println("Read-heavy analytics: " + analytics.writeConcern() + " / " + analytics.readPreference());
        System.out.println("  Rationale: " + analytics.rationale());
        System.out.println("General purpose: " + general.writeConcern() + " / " + general.readPreference());
        System.out.println("  Rationale: " + general.rationale());
    }
}
```

How to run: `java MongoConnectLevel3.java`

`chooseProfile` mechanically encodes the write-concern/read-preference tradeoff: financial data gets the strictest settings (`MAJORITY` write concern, always read from `PRIMARY`) prioritizing correctness over speed, while read-heavy analytics data gets the loosest settings (`W1` write concern, prefer `SECONDARY_PREFERRED` reads) prioritizing throughput, accepting a small risk of reading slightly stale data from a secondary replica.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `chooseProfile(true, false)` runs for `financial`: since `isFinancialData` is `true`, the first branch executes immediately, returning `ConsistencyProfile(MAJORITY, PRIMARY, "financial data requires...")` — `readHeavyWorkload` is never even consulted, because financial-data correctness requirements take precedence over any throughput consideration.

Next, `chooseProfile(false, true)` runs for `analytics`: `isFinancialData` is `false`, so the first branch is skipped; `readHeavyWorkload` is `true`, so the second branch executes, returning `ConsistencyProfile(W1, SECONDARY_PREFERRED, "read-heavy, non-critical data benefits...")`.

Finally, `chooseProfile(false, false)` runs for `general`: both flags are `false`, so both special-case branches are skipped, falling through to the default return: `ConsistencyProfile(W1, PRIMARY, "default: fast writes, always-consistent reads...")`.

The three printed blocks confirm each profile's chosen write concern, read preference, and the reasoning behind it — financial data trading latency for durability, analytics data trading strict consistency for throughput, and the general case taking a balanced middle ground.

```
chooseProfile(financial=true, readHeavy=false)  -> MAJORITY / PRIMARY           (correctness prioritized)
chooseProfile(financial=false, readHeavy=true)   -> W1 / SECONDARY_PREFERRED     (throughput prioritized)
chooseProfile(financial=false, readHeavy=false)  -> W1 / PRIMARY                (balanced default)
```

In a real Spring Data MongoDB application, these settings are configured once on the `MongoClientSettings` bean (or per-operation, for read preference, via `Query.withReadPreference(...)`) and apply to every subsequent database interaction through that client — a financial-transactions collection might use a `MongoClientSettings` bean configured with `WriteConcern.MAJORITY` (waiting for acknowledgment from a majority of replica set members before considering a write successful) and `ReadPreference.primary()` (always reading the most up-to-date data), while a separate analytics-reporting collection might use a lighter-weight configuration favoring throughput over strict consistency.

## 7. Gotchas & takeaways

> Gotcha: a write concern weaker than `MAJORITY` (e.g., acknowledging from just one node) means a write can be reported as successful to the application, then subsequently lost if that one node fails before the write replicates further — for any data where losing a recently-written value would be a real problem, `MAJORITY` write concern (or stronger) is the correct choice, not a premature optimization to avoid.

- `MongoClientSettings` assembles connection details, pool sizing, and MongoDB's own consistency knobs (write concern, read preference) into one configuration object.
- Connection pool sizing follows the exact same tradeoff logic covered in the R2DBC connection-pooling card — too small causes contention, too large risks overwhelming the server.
- Write concern controls how many replica-set members must acknowledge a write before it's considered successful — weaker settings mean faster writes but a real risk of data loss on node failure.
- Read preference controls which replica-set members can serve reads — preferring secondaries improves read throughput and reduces load on the primary, at the cost of potentially reading slightly stale data.
