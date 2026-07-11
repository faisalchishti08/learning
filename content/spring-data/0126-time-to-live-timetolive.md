---
card: spring-data
gi: 126
slug: time-to-live-timetolive
title: "Time to live (@TimeToLive)"
---

## 1. What it is

`@TimeToLive` marks a field (or method) on a `@RedisHash` entity as the number of seconds Redis should keep that entity alive before automatically deleting it — Spring Data Redis reads the field's value on every save and issues Redis's native `EXPIRE` command, so the entity disappears on its own without any explicit `delete` call.

```java
@RedisHash("sessions")
class Session {
    @Id String id;
    String userId;
    @TimeToLive Long ttlSeconds; // this instance auto-expires this many seconds after being saved
}
```

## 2. Why & when

The earlier `@RedisHash` card noted that saved entities live forever by default, unlike a `RedisTemplate`-based cache entry with an explicit TTL. Many Redis-backed entities genuinely *should* expire — session data, one-time tokens, temporary locks, rate-limit counters — and `@TimeToLive` brings that same automatic-expiry behavior to the repository programming model, instead of requiring a separate scheduled cleanup job.

Reach for `@TimeToLive` when:

- The entity represents something inherently time-bounded — a login session, a password-reset token, a temporary reservation hold — where "still exists" should naturally become false after some period.
- You want Redis itself (not application code, not a cron job) to guarantee cleanup — Redis expires keys reliably and efficiently, even if the application that wrote them is down.
- You need a **per-instance** TTL that varies by entity (a `@RedisHash("sessions")` with different expiry per user tier, say) rather than one fixed keyspace-wide expiry — a field-level `@TimeToLive` supports exactly that, since it's read from each saved instance.

## 3. Core concept

```
 @RedisHash("sessions")
 class Session { @Id String id; @TimeToLive Long ttlSeconds; }

 sessionRepository.save(new Session("abc", 1800L))
        |
        v
 HSET sessions:abc userId ...
 EXPIRE sessions:abc 1800          -- Redis's own clock now owns this key's lifetime

 ... 1800 seconds later, with NO application code running at all ...
 GET sessions:abc  -> (nil)         -- Redis deleted it automatically
```

Once `EXPIRE` is set, the key's disappearance is entirely Redis's responsibility — no poll, no scheduled job, no application code needs to run for the deletion to happen.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A saved session gets an EXPIRE command; after the TTL elapses Redis deletes it automatically with no application involvement">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">save(session, ttl=1800)</text>

  <rect x="250" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">HSET + EXPIRE 1800</text>
  <text x="340" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">key: sessions:abc</text>

  <rect x="480" y="20" width="140" height="45" rx="8" fill="#f8514922" stroke="#f85149" stroke-width="1.5"/>
  <text x="550" y="47" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">auto-deleted</text>

  <line x1="200" y1="42" x2="245" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="430" y1="42" x2="475" y2="42" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3" marker-end="url(#a1)"/>
  <text x="452" y="30" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1800s later</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The gap between "saved" and "auto-deleted" is handled entirely inside Redis, with no application code running during that interval.

## 5. Runnable example

The scenario: session entities that expire automatically, evolving from a basic TTL set at save time, to correctly refreshing the TTL on every access (a sliding-expiration session pattern), to a per-entity variable TTL where different entities get different lifespans based on their own data.

### Level 1 — Basic

Model `@TimeToLive`: an entity's TTL field determines when Redis will consider it expired.

```java
import java.util.*;

public class TtlLevel1 {
    public static void main(String[] args) {
        SessionRepository repo = new SessionRepository();

        repo.save(new Session("abc", "user-1", 1800), 0); // saved at simulated time t=0

        System.out.println("At t=1000s, session exists: " + (repo.findById("abc", 1000) != null));
        System.out.println("At t=2000s, session exists: " + (repo.findById("abc", 2000) != null));
    }
}

class Session { String id; String userId; long ttlSeconds; Session(String id, String userId, long ttlSeconds) { this.id = id; this.userId = userId; this.ttlSeconds = ttlSeconds; } }

class RedisHashEntry { Session session; long expiresAtMillis; RedisHashEntry(Session session, long expiresAtMillis) { this.session = session; this.expiresAtMillis = expiresAtMillis; } }

class SessionRepository {
    private final Map<String, RedisHashEntry> store = new HashMap<>();

    void save(Session session, long nowSeconds) {
        long expiresAt = nowSeconds + session.ttlSeconds; // EXPIRE sessions:<id> <ttlSeconds>, relative to now
        store.put(session.id, new RedisHashEntry(session, expiresAt));
    }

    Session findById(String id, long nowSeconds) {
        RedisHashEntry entry = store.get(id);
        if (entry == null || nowSeconds >= entry.expiresAtMillis) return null; // Redis would have already deleted it
        return entry.session;
    }
}
```

How to run: `java TtlLevel1.java`

`save` records `nowSeconds + ttlSeconds` as the expiry point, mirroring `EXPIRE sessions:abc 1800` executed at save time. `findById` checks whether the current simulated time has passed that point — at `t=1000`, `1800`s hasn't elapsed yet, so the session is found; at `t=2000`, it has, so `findById` behaves as if Redis had already deleted the key, returning `null`.

### Level 2 — Intermediate

Refresh the TTL on every access — a "sliding expiration" session, where activity keeps the session alive and only genuine inactivity lets it expire, matching how a real session store is typically used.

```java
import java.util.*;

public class TtlLevel2 {
    public static void main(String[] args) {
        SessionRepository repo = new SessionRepository();
        repo.save(new Session("abc", "user-1", 1800), 0); // expires at t=1800 if untouched

        repo.findByIdAndRefresh("abc", 1000); // ACCESSED at t=1000 -- TTL resets to expire at t=2800
        System.out.println("At t=2500s (would have expired at t=1800 without the access): "
            + (repo.findByIdAndRefresh("abc", 2500) != null));

        System.out.println("At t=5000s, with no access since t=2500 (expired at t=4300): "
            + (repo.findByIdAndRefresh("abc", 5000) != null));
    }
}

class Session { String id; String userId; long ttlSeconds; Session(String id, String userId, long ttlSeconds) { this.id = id; this.userId = userId; this.ttlSeconds = ttlSeconds; } }

class RedisHashEntry { Session session; long expiresAtMillis; RedisHashEntry(Session session, long expiresAtMillis) { this.session = session; this.expiresAtMillis = expiresAtMillis; } }

class SessionRepository {
    private final Map<String, RedisHashEntry> store = new HashMap<>();

    void save(Session session, long nowSeconds) {
        store.put(session.id, new RedisHashEntry(session, nowSeconds + session.ttlSeconds));
    }

    // Mirrors calling save() again on read -- re-issuing EXPIRE resets the countdown from NOW.
    Session findByIdAndRefresh(String id, long nowSeconds) {
        RedisHashEntry entry = store.get(id);
        if (entry == null || nowSeconds >= entry.expiresAtMillis) return null;
        entry.expiresAtMillis = nowSeconds + entry.session.ttlSeconds; // TTL SLIDES forward on every access
        return entry.session;
    }
}
```

How to run: `java TtlLevel2.java`

`findByIdAndRefresh` not only checks expiry but, on a successful lookup, resets `expiresAtMillis` to `now + ttlSeconds` — sliding the expiration window forward, matching a session store where "still active" is defined by recent activity, not by a fixed clock from creation time. Without the access at `t=1000`, the session would have expired at `t=1800`; because it was accessed, it survives until `t=2500` is checked (still valid, expiring at `t=2800`), but by `t=5000` — with no access since `t=2500` — the `t=2800` expiry has long passed.

### Level 3 — Advanced

Give different sessions different TTLs based on their own data (a "remember me" session gets a longer TTL than a normal one) — the actual value of a **per-instance** `@TimeToLive` field rather than one fixed value for the whole keyspace.

```java
import java.util.*;

public class TtlLevel3 {
    public static void main(String[] args) {
        SessionRepository repo = new SessionRepository();

        Session normal = new Session("normal-session", "user-1", false);
        Session remembered = new Session("remembered-session", "user-2", true);
        repo.save(normal, 0);
        repo.save(remembered, 0);

        long oneHourLater = 3600;
        System.out.println("After 1 hour -- normal session alive:     " + repo.existsAt("normal-session", oneHourLater));
        System.out.println("After 1 hour -- remembered session alive: " + repo.existsAt("remembered-session", oneHourLater));

        long twentyDaysLater = 20L * 24 * 3600;
        System.out.println("After 20 days -- remembered session alive: " + repo.existsAt("remembered-session", twentyDaysLater));
    }
}

class Session {
    String id; String userId; boolean rememberMe;
    long ttlSeconds; // computed per-instance, NOT a fixed constant for the whole "sessions" keyspace
    Session(String id, String userId, boolean rememberMe) {
        this.id = id; this.userId = userId; this.rememberMe = rememberMe;
        this.ttlSeconds = rememberMe ? 30L * 24 * 3600 : 1800L; // 30 days vs 30 minutes
    }
}

class RedisHashEntry { Session session; long expiresAtMillis; RedisHashEntry(Session session, long expiresAtMillis) { this.session = session; this.expiresAtMillis = expiresAtMillis; } }

class SessionRepository {
    private final Map<String, RedisHashEntry> store = new HashMap<>();
    void save(Session session, long nowSeconds) { store.put(session.id, new RedisHashEntry(session, nowSeconds + session.ttlSeconds)); }
    boolean existsAt(String id, long nowSeconds) {
        RedisHashEntry entry = store.get(id);
        return entry != null && nowSeconds < entry.expiresAtMillis;
    }
}
```

How to run: `java TtlLevel3.java`

Each `Session`'s `ttlSeconds` is computed from its own `rememberMe` flag at construction time — `30` minutes for a normal session, `30` days for a "remember me" one — exactly what a `@TimeToLive`-annotated field expresses: the TTL travels with the individual entity instance, not with the keyspace as a whole. After one simulated hour, the normal session has expired but the remembered one is still well within its 30-day window; after twenty simulated days, even the remembered session has finally expired.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two sessions are constructed: `normal` with `rememberMe=false` (so its constructor sets `ttlSeconds = 1800`, i.e. 30 minutes) and `remembered` with `rememberMe=true` (`ttlSeconds = 30 * 24 * 3600 = 2,592,000` seconds, i.e. 30 days). Both are saved at simulated time `t=0`, so `normal` expires at `t=1800` and `remembered` expires at `t=2,592,000`.

`repo.existsAt("normal-session", 3600)` checks whether `3600 < 1800` — it's not, so `existsAt` returns `false`: the normal session has already expired after just one simulated hour. `repo.existsAt("remembered-session", 3600)` checks `3600 < 2,592,000` — true, so it returns `true`: the remembered session is still alive.

`repo.existsAt("remembered-session", 20 * 24 * 3600)` (twenty days, or `1,728,000` seconds) checks `1,728,000 < 2,592,000` — still true, so the session would still be alive at twenty days (the code prints this as `true`, consistent with a 30-day TTL not yet having elapsed).

```
After 1 hour -- normal session alive:     false
After 1 hour -- remembered session alive: true
After 20 days -- remembered session alive: true
```

In real Spring Data Redis, `@TimeToLive Long ttlSeconds` on the `Session` entity is read via reflection on every `save()` call, and the framework issues `EXPIRE sessions:<id> <value>` immediately after writing the hash fields — different saved instances can carry entirely different TTL values, exactly as shown here, letting one repository and one keyspace serve entities with heterogeneous lifespans without any extra application logic.

## 7. Gotchas & takeaways

> Gotcha: `@TimeToLive` is read from the entity **at save time** — changing the field's value on an already-saved, in-memory object does nothing to the entity's actual Redis expiry until `save()` is called again to re-issue the `EXPIRE` command.

> Gotcha: an entity with a secondary index (the previous card) that expires via TTL needs its index entries cleaned up too — Spring Data Redis handles this automatically via Redis keyspace notifications, but it requires keyspace notifications to be enabled on the Redis server (`notify-keyspace-events`); without that configuration, expired entities can leave stale entries behind in index sets.

- `@TimeToLive` on a field (in seconds) makes Spring Data Redis issue Redis's native `EXPIRE` command on every save, so the entity is deleted by Redis itself once the TTL elapses — no polling or scheduled cleanup job needed.
- Calling `save()` again (for example, on every access, for a sliding-expiration pattern) resets the TTL countdown from that moment.
- The TTL is read per-instance, so different saved entities in the same keyspace can have entirely different lifespans based on their own data.
- Combining `@TimeToLive` with `@Indexed` (the previous card) requires Redis keyspace notifications to be enabled for index cleanup to stay in sync with expired entities.
