---
card: spring-session
gi: 11
slug: redis-redisindexedsessionrepository-vs-redissessionrepositor
title: "Redis (RedisIndexedSessionRepository vs RedisSessionRepository)"
---

## 1. What it is

Spring Session offers two distinct Redis-backed repository implementations: `RedisIndexedSessionRepository` (card 0010), which maintains secondary indexes (like principal-name lookup) alongside session data, and the simpler `RedisSessionRepository`, which stores session data alone with no supporting index structures. `@EnableRedisHttpSession`'s `redisSessionRepositoryType` setting (or the specific configuration class chosen) determines which one is active.

## 2. Why & when

Indexing has a real cost — every session save with `RedisIndexedSessionRepository` does extra Redis writes to keep index sets current, and Redis's own expiration-notification mechanism (needed to correctly detect and clean up expired sessions and their index entries together, as opposed to Redis's simple key TTL alone) adds further overhead and configuration complexity (card 0008's keyspace-notification gotcha). For applications that never need `findByPrincipalName` or its dependent features (active-sessions lists, force-logout-everywhere, concurrent session limits), that cost buys nothing — `RedisSessionRepository` is a genuinely simpler, leaner alternative that relies on Redis's native TTL alone, with less write overhead and no keyspace-notification requirement.

Reach for `RedisIndexedSessionRepository` when:

- The application needs any feature that queries sessions by something other than their own ID — active sessions lists, remote logout, concurrent session limits (all covered in card 0003).
- Auditing or security requirements demand visibility into all of a specific user's active sessions.

Reach for `RedisSessionRepository` when:

- None of the above apply, and the priority is minimizing write overhead and operational complexity — a good default for a large class of applications that simply need working clustered sessions, nothing more.
- Avoiding the Redis keyspace-notification configuration requirement (card 0008) entirely — `RedisSessionRepository` relies purely on Redis's native key TTL and doesn't need application-visible expiration events to function correctly.

## 3. Core concept

Think of `RedisIndexedSessionRepository` as a hotel with both room key cards *and* a front-desk guest registry cross-referenced by name — useful when the hotel needs to answer "which rooms is this guest currently checked into" or "check this guest out of every room they hold," but requiring the front desk staff to update the registry every single time a key is issued or a room is vacated. `RedisSessionRepository` is the same hotel with only the key cards and no registry at all — perfectly capable of checking a specific room by its own key, faster and simpler to operate day-to-day, but structurally unable to answer "which rooms does this specific guest hold" without walking every room individually.

```
RedisIndexedSessionRepository:  session hash + principal index set   (richer, more writes)
RedisSessionRepository:         session hash only                    (leaner, fewer writes)
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing write operations and capabilities of the two Redis session repository implementations">
  <rect x="20" y="20" width="290" height="90" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">RedisIndexedSessionRepository</text>
  <text x="165" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">save() -&gt; hash write + index set write</text>
  <text x="165" y="88" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">supports findByPrincipalName</text>

  <rect x="350" y="20" width="290" height="90" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">RedisSessionRepository</text>
  <text x="495" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">save() -&gt; hash write only</text>
  <text x="495" y="88" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">no indexed lookup support</text>
</svg>

The choice is a direct trade between write cost/complexity and query capability — neither option is universally "better."

## 5. Runnable example

The scenario: configuring an application with `RedisSessionRepository` for simplicity, growing to measure the actual write-volume difference against `RedisIndexedSessionRepository` under load, and finally to make an informed decision by adding just enough targeted indexing manually rather than adopting the full indexed repository when only one specific query pattern is needed.

### Level 1 — Basic

```java
// SimpleRedisSessionConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.session.config.annotation.web.http.EnableSpringHttpSession;
import org.springframework.session.data.redis.RedisSessionRepository;

@Configuration
@EnableSpringHttpSession // note: generic annotation, NOT @EnableRedisHttpSession's indexed default
public class SimpleRedisSessionConfig {

    @Bean
    public RedisSessionRepository sessionRepository(RedisConnectionFactory connectionFactory) {
        return new RedisSessionRepository(
                org.springframework.data.redis.core.RedisTemplate.class.cast(
                        buildRedisTemplate(connectionFactory)));
    }

    private Object buildRedisTemplate(RedisConnectionFactory connectionFactory) {
        var template = new org.springframework.data.redis.core.RedisTemplate<String, Object>();
        template.setConnectionFactory(connectionFactory);
        template.afterPropertiesSet();
        return template;
    }
}
```

**How to run:** run this app instead of the `@EnableRedisHttpSession`-based one, make several requests touching the session, then inspect Redis. Expected output: `redis-cli KEYS "spring:session:*"` shows only session hash keys — no `index:*` keys at all, since `RedisSessionRepository` never creates them.

### Level 2 — Intermediate

Measuring the actual difference in write volume between the two repository types under a simple load test makes the trade-off concrete rather than theoretical.

```java
import org.springframework.data.redis.core.StringRedisTemplate;

public class WriteVolumeComparator {

    public void measure(StringRedisTemplate redisTemplate, int sessionCount) {
        redisTemplate.execute((org.springframework.data.redis.connection.RedisConnection connection) -> {
            connection.serverCommands().resetConfigStats(); // reset INFO commandstats counters
            return null;
        });

        // ... create sessionCount sessions via the app under test, then:

        Long totalCommandsIndexed = redisTemplate.execute(connection ->
                (Long) connection.serverCommands().info("commandstats").getProperty("cmdstat_hset"));

        System.out.println("Approximate HSET calls observed for " + sessionCount + " sessions: " + totalCommandsIndexed);
        // Repeat the whole measurement swapping RedisIndexedSessionRepository in for RedisSessionRepository
        // and compare — the indexed variant issues additional SADD/SREM calls the simple variant never does.
    }
}
```

**How to run:** run this measurement (or simply watch `redis-cli MONITOR` output) while creating, say, 1000 sessions under each repository configuration in turn. Expected observation: the indexed variant issues a visibly higher total command count per session created — the concrete, measurable cost of the extra index-maintenance writes that the simpler repository skips entirely.

What changed: the abstract "indexing has overhead" claim from this card's introduction is now a concrete, observed number specific to this application's session usage pattern — the right basis for deciding whether that overhead is actually worth paying, rather than guessing.

### Level 3 — Advanced

If only one narrow indexed capability is genuinely needed — say, just counting active sessions per user, without needing the full `findByPrincipalName` machinery — a lighter, purpose-built solution alongside `RedisSessionRepository` can deliver exactly that one capability without adopting the full indexed repository's broader overhead.

```java
import org.springframework.context.event.EventListener;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.session.events.SessionCreatedEvent;
import org.springframework.session.events.SessionDestroyedEvent;
import org.springframework.stereotype.Component;

@Component
public class LightweightSessionCounter {

    private final StringRedisTemplate redisTemplate;

    public LightweightSessionCounter(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @EventListener
    public void onCreated(SessionCreatedEvent event) {
        String principal = extractPrincipal(event); // resolved from the session's stored SecurityContext
        if (principal != null) {
            redisTemplate.opsForValue().increment("session_count:" + principal);
        }
    }

    @EventListener
    public void onDestroyed(SessionDestroyedEvent event) {
        String principal = extractPrincipal(event);
        if (principal != null) {
            redisTemplate.opsForValue().decrement("session_count:" + principal);
        }
    }

    public long countFor(String principal) {
        String value = redisTemplate.opsForValue().get("session_count:" + principal);
        return value != null ? Long.parseLong(value) : 0;
    }

    private String extractPrincipal(Object event) {
        return "resolved-from-session-attribute"; // real implementation reads it from the session
    }
}
```

**How to run:** use `RedisSessionRepository` (Level 1's leaner setup) as the base, add this counter, and log in as the same user from three devices. Expected behavior: `countFor(username)` returns `3` — the specific capability that was needed (a per-user session count) is now available, built on top of the simple repository via session events (card 0008) instead of requiring the fuller `RedisIndexedSessionRepository`'s always-on indexing overhead.

What changed and why it's production-flavored: this demonstrates that "I need *some* per-user session insight" doesn't automatically mean "I need the full indexed repository" — a targeted, purpose-built addition on top of the simpler repository can deliver exactly the needed capability at a fraction of the always-on cost, which is the kind of deliberate trade-off a production system should make explicitly rather than defaulting to the heavier option out of convenience.

## 6. Walkthrough

Tracing the decision and its consequences across a typical application's evolution, in execution order:

1. At launch, the team reaches for `@EnableRedisHttpSession`'s default (`RedisIndexedSessionRepository`) without much thought, since it's the more commonly documented path and "just works" including features they don't yet need.
2. Months later, a load test or cost review flags Redis write volume as unexpectedly high; `WriteVolumeComparator` (Level 2) reveals a meaningful fraction of it is index-maintenance writes for a `findByPrincipalName` capability the application has never actually called.
3. The team re-evaluates: no feature in the product currently needs "list all sessions for user X" — the switch to `RedisSessionRepository` (Level 1) is made, immediately reducing write volume and removing the keyspace-notification configuration requirement (card 0008) from the deployment checklist.
4. Later still, a new requirement emerges: product wants a simple "you're logged in on 3 devices" indicator, but nothing more elaborate. Rather than reverting to the full indexed repository, the team adds `LightweightSessionCounter` (Level 3) — a small, purpose-built addition using session events, delivering exactly the new requirement without reintroducing the full indexing overhead the team deliberately moved away from.
5. This sequence — start simple or default, measure, then add precisely the capability actually needed — is a reasonable general pattern for this decision, rather than trying to predict every future requirement upfront.

```
Launch: RedisIndexedSessionRepository (default choice, unindexed features unused)
   |
Measure: index-maintenance writes are a real, unnecessary cost
   |
Switch: RedisSessionRepository (leaner, no keyspace-notification requirement)
   |
New requirement: "session count per user" only
   |
Add: LightweightSessionCounter via session events (targeted, not the full indexed repository)
```

## 7. Gotchas & takeaways

> Switching between the two repository types isn't just a configuration change with no other consequences — `RedisIndexedSessionRepository`'s `SessionExpiredEvent` (card 0008) specifically depends on Redis keyspace notifications being enabled, while `RedisSessionRepository` doesn't publish expiration events the same way (relying purely on native TTL); any code depending on expiration events must be re-verified after switching repository types, not assumed to keep working identically.

- Default to `RedisIndexedSessionRepository` only when a genuine need for indexed lookup already exists or is clearly imminent — reaching for it purely because it's the more commonly documented default, without an actual feature need, pays ongoing overhead for nothing.
- The write-volume difference (Level 2) scales with session creation/modification rate, not with total session count at rest — a low-traffic application won't notice the difference regardless of which repository is chosen; a high-throughput application (many logins and session writes per second) is where this decision actually matters materially.
- `RedisSessionRepository` still fully supports everything covered in cards 0001-0008 that doesn't specifically require indexed lookup — expiration (via native TTL), transparent `HttpSession` replacement, and the servlet filter mechanics are identical regardless of which repository type backs them.
- A targeted, event-driven addition (Level 3) is often a better engineering trade-off than adopting a broader, always-on capability for one narrow need — this pattern (build the minimum extra machinery for the specific requirement, rather than the general-purpose superset) applies well beyond just this Redis repository choice.
- When in doubt about which to choose for a new application, `RedisIndexedSessionRepository` remains the safer *default* if there's genuine uncertainty about future feature needs (adding indexed-lookup features later without it requires a repository swap and migration); `RedisSessionRepository` is the right call once that uncertainty is resolved in favor of "we genuinely don't need this."
