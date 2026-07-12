---
card: spring-session
gi: 14
slug: spring-session-mongodb
title: "Spring Session MongoDB"
---

## 1. What it is

`spring-session-data-mongodb` is the MongoDB-backed implementation of Spring Session, wired via `@EnableMongoHttpSession`. It stores each session as a document in a configurable MongoDB collection (default name `sessions`), relying on a MongoDB TTL index on the session's expiration field for automatic expiration — closer in spirit to Redis's native-TTL approach (card 0009) than to JDBC's need for an explicit scheduled cleanup task (card 0012).

## 2. Why & when

Teams already operating MongoDB as their primary datastore face the same "should sessions live in existing infrastructure or a new dedicated one" decision covered for JDBC (card 0012) — but MongoDB happens to have a genuinely useful built-in capability neither a plain relational database nor a hand-rolled solution gets for free: TTL indexes, which let MongoDB itself automatically remove documents past a specified expiration time, without any application-side scheduled task required. This makes MongoDB an appealing middle ground: no new infrastructure (like JDBC), but with native expiration handling (like Redis).

Reach for Spring Session MongoDB when:

- MongoDB is already the application's primary or a well-operated secondary datastore, and adding Redis purely for sessions isn't desired.
- Session data's document-oriented shape (attributes as a flexible, schema-less structure) fits naturally with how the rest of the application already models data in MongoDB.
- Deciding between MongoDB, Redis (card 0009), and JDBC (card 0012) — MongoDB's TTL index gives it a genuine edge over JDBC's requirement for a separate scheduled cleanup task, while still avoiding introducing Redis as an entirely new infrastructure dependency.

## 3. Core concept

Think of MongoDB's TTL index as a smart storage unit with an expiration date printed directly on each stored item, where the facility itself automatically clears out anything past its printed date on its own schedule — no need for staff (an application-level scheduled task) to walk the aisles checking labels, unlike JDBC's plain-shelf warehouse from card 0012, which needed exactly that kind of active human intervention. It's not quite as instantaneous as Redis's native key-level TTL (MongoDB's TTL monitor runs on its own periodic background cycle, typically every 60 seconds, rather than expiring at the precise millisecond), but it's a meaningful step up from JDBC's fully manual cleanup requirement.

```javascript
// The TTL index Spring Session MongoDB relies on:
db.sessions.createIndex(
    { "expireAt": 1 },
    { expireAfterSeconds: 0 }  // MongoDB removes documents once expireAt is in the past
)
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MongoDB stores each session as a document and its own TTL monitor background process automatically removes expired documents">
  <rect x="30" y="30" width="260" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">sessions collection</text>
  <text x="160" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{ _id, principal, attrs, expireAt }</text>
  <text x="160" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TTL index on expireAt</text>

  <rect x="380" y="30" width="240" height="80" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MongoDB TTL monitor</text>
  <text x="500" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">background thread, runs</text>
  <text x="500" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">~every 60 seconds internally</text>

  <line x1="290" y1="70" x2="375" y2="70" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no application-level scheduled task needed — MongoDB itself does this</text>
</svg>

Application code never explicitly deletes expired sessions — MongoDB's own background process handles it based purely on the TTL index.

## 5. Runnable example

The scenario: setting up MongoDB-backed sessions and confirming the TTL index handles expiration automatically, growing to verify the roughly-60-second TTL sweep cadence directly, and finally to model session attributes as structured sub-documents rather than opaque serialized blobs, taking advantage of MongoDB's native document flexibility.

### Level 1 — Basic

```java
// MongoSessionConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.mongo.config.annotation.web.http.EnableMongoHttpSession;

@Configuration
@EnableMongoHttpSession
public class MongoSessionConfig {
}
```

```properties
# application.properties
spring.data.mongodb.uri=mongodb://localhost:27017/appdb
```

**How to run:** with `spring-session-data-mongodb`, a `MongoTemplate`/`MongoDatabaseFactory` bean available (Spring Boot's MongoDB starter provides one automatically from `spring.data.mongodb.uri`), start the app and make a request touching the session. Expected result: `db.sessions.findOne()` in a Mongo shell shows the session document, including an `expireAt` field, and `db.sessions.getIndexes()` shows a TTL index was created automatically on that field.

### Level 2 — Intermediate

Confirming the TTL sweep actually runs — and understanding its roughly-60-second granularity, unlike Redis's essentially-instant key expiration — matters for correctly reasoning about exactly when an expired session's document physically disappears versus when the application logically treats it as gone.

```java
import com.mongodb.client.MongoCollection;
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Component;

import java.time.Instant;

@Component
public class MongoTtlObserver {

    private final MongoTemplate mongoTemplate;

    public MongoTtlObserver(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }

    public void observeExpiry(String sessionId) {
        MongoCollection<Document> collection = mongoTemplate.getCollection("sessions");
        Document doc = collection.find(new Document("_id", sessionId)).first();

        if (doc == null) {
            System.out.println("Session document already removed by TTL sweep.");
        } else {
            Instant expireAt = doc.getDate("expireAt").toInstant();
            boolean pastExpiry = Instant.now().isAfter(expireAt);
            System.out.println("Document still present. Past expiry: " + pastExpiry
                    + " (MongoDB's TTL monitor hasn't swept it yet if true)");
        }
    }
}
```

**How to run:** create a session with a short `maxInactiveInterval` (e.g. 10 seconds) for testing, let it pass its expiry, then call `observeExpiry(sessionId)` repeatedly over the following couple of minutes. Expected observation: for some period after the session's logical expiry time (`pastExpiry: true`), the document is still physically present — only once MongoDB's internal TTL monitor next runs (up to ~60 seconds later) does the document actually disappear, at which point subsequent calls report it removed.

What changed: this makes MongoDB's specific expiration timing model concrete and observable — a meaningful, worth-knowing difference from Redis's near-instant expiration, even though both are "automatic" in the sense that neither requires an application-level scheduled task.

### Level 3 — Advanced

MongoDB's document model allows session attributes to be stored as genuinely structured, queryable sub-documents rather than opaque serialized byte blobs — useful for applications that want to run analytical queries directly against session data (e.g. "how many active sessions currently have `cartValue > $100`") without deserializing every session in application code first.

```java
import org.bson.Document;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class SessionAnalyticsQuery {

    private final MongoTemplate mongoTemplate;

    public SessionAnalyticsQuery(MongoTemplate mongoTemplate) {
        this.mongoTemplate = mongoTemplate;
    }

    public long countHighValueActiveCarts(double threshold) {
        // Assumes session attributes are stored in a way that permits querying into them directly —
        // requires a custom attribute serialization strategy beyond the library's default
        // (which stores attributes as opaque serialized bytes by default, not natively queryable).
        Document query = new Document("attrs.cartValue", new Document("$gt", threshold));
        return mongoTemplate.getCollection("sessions").countDocuments(query);
    }
}
```

**How to run:** configure a custom `MongoSessionConverter` (Spring Session MongoDB's extension point for controlling how session attributes are serialized into the document) that stores specific, known attributes as native, directly-queryable MongoDB fields rather than opaque bytes. Populate several test sessions with varying `cartValue` attributes, then call `countHighValueActiveCarts(100.0)`. Expected output: an accurate count reflecting only currently active (non-expired) sessions whose `cartValue` attribute exceeds the threshold — a direct MongoDB query, not an application-level scan requiring every session to be deserialized first.

What changed and why it's production-flavored: this is a capability genuinely unique to MongoDB among the stores covered so far — running structured queries against live session data directly at the database layer, useful for lightweight real-time analytics or operational dashboards without building separate application-level aggregation logic.

## 6. Walkthrough

Tracing a session write and its eventual TTL-driven cleanup, in execution order:

1. `SessionRepositoryFilter` (card 0004) triggers `save(...)` on the Mongo-backed repository at the end of a request.
2. The repository writes (inserts or updates) a document in the `sessions` collection, including an `expireAt` field computed from the current time plus `maxInactiveInterval` — this is the field the TTL index (created automatically at startup by the library) watches.
3. As long as the session is actively used, each subsequent `save(...)` updates `expireAt` to a new, later value — keeping the session alive in MongoDB's eyes exactly as a fresh Redis TTL refresh would.
4. Once the user stops interacting and `maxInactiveInterval` elapses, `expireAt` is now in the past, but the document remains physically present — MongoDB doesn't delete it the instant expiry passes.
5. Independently, MongoDB's own internal TTL background monitor thread wakes up on its regular (roughly 60-second) cycle, scans TTL-indexed collections for documents whose indexed field is in the past, and removes them — this is a MongoDB server-level mechanism, entirely outside Spring Session's or the application's own code.
6. Any `findById(...)` call for a session whose document has already been removed correctly returns nothing, and `SessionRepositoryFilter` treats the request as unauthenticated — same observable behavior as Redis or JDBC, even though the underlying removal mechanism and its timing granularity differ.

```
save(session) -> write document {_id, attrs, expireAt: now + maxInactiveInterval}
   |
(user active) -> repeated save() calls refresh expireAt
   |
(user inactive past maxInactiveInterval) -> expireAt now in the past, document still present
   |
(MongoDB internal TTL monitor cycle, ~60s) -> scans TTL-indexed collections -> removes expired documents
   |
findById(expiredId) -> null (once the sweep has actually run)
```

## 7. Gotchas & takeaways

> MongoDB's TTL monitor runs on its own internal cadence (roughly every 60 seconds by default, and this is a server-level setting, not something Spring Session controls) — a session's document can remain physically present in the collection for up to about a minute past its logical expiration time. Application logic relying on `findById` correctly returns nothing once truly expired, but anything querying the raw collection directly (Level 3's analytics queries, for instance) must account for this lag or explicitly filter on `expireAt` itself rather than assuming absence.

- Spring Session MongoDB requires the TTL index to exist and be correctly maintained — it's created automatically by the library's own startup configuration under normal use, but a hand-managed schema or migration process that doesn't preserve this index silently disables automatic expiration entirely, leaving expired sessions accumulating indefinitely.
- By default, session attributes are serialized as opaque bytes within the document, not as natively queryable MongoDB fields — Level 3's structured querying capability requires deliberately configuring a custom converter; it isn't the out-of-the-box behavior.
- MongoDB-backed sessions share the same general trade-off as JDBC (card 0012) around network round-trip latency compared to Redis's in-memory speed — though MongoDB's native TTL index is a meaningful advantage over JDBC's fully manual cleanup requirement specifically.
- As with JDBC, adding MongoDB purely for session storage when it isn't already part of the stack introduces a new infrastructure dependency — the natural fit is for teams that already operate MongoDB reliably for other application data.
- When debugging "sessions aren't expiring," check first whether the TTL index actually exists on the `sessions` collection (`db.sessions.getIndexes()`) — a missing or dropped index is functionally equivalent to disabling expiration entirely, since nothing else in this setup removes documents on its own.
