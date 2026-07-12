---
card: spring-session
gi: 20
slug: spring-security-concurrent-session-control-with-spring-sessi
title: "Spring Security concurrent session control with Spring Session"
---

## 1. What it is

Spring Security has its own built-in concurrent session control (`maximumSessions(...)`, session registry-based) designed originally around a single-instance container session. Combining it with Spring Session requires using `SpringSessionBackedSessionRegistry`, an adapter that lets Spring Security's concurrent-session-limiting logic work correctly against a clustered, external session store instead of assuming everything lives in one JVM's local memory.

## 2. Why & when

Spring Security's default `SessionRegistryImpl` tracks active sessions in a local, in-memory map — which works fine for enforcing "maximum 1 session per user" on a single instance, but breaks down across a cluster: instance A doesn't know about sessions instance B is tracking, so a user could log in once on each of three instances behind a load balancer and end up with three concurrent sessions despite a `maximumSessions(1)` policy that each individual instance believes it's correctly enforcing. `SpringSessionBackedSessionRegistry` fixes this by having Spring Security's concurrent session logic query the *shared* Spring Session store instead of local memory, so the limit is enforced correctly across every instance.

Reach for this integration when:

- Enforcing "maximum N concurrent sessions per user" (a common security control, and this card's card 0003 territory revisited through Spring Security's own specific mechanism) in a clustered deployment — without this adapter, the limit is silently only enforced per-instance, not cluster-wide.
- Migrating an existing single-instance application that already uses Spring Security's `maximumSessions(...)` to a clustered deployment — this is the specific piece that needs updating, since the default `SessionRegistryImpl` won't work correctly once there's more than one instance.
- Debugging "concurrent session limits aren't being enforced correctly" in a load-balanced deployment — a strong signal to check whether `SpringSessionBackedSessionRegistry` is actually wired in, versus the default, cluster-blind registry still being used.

## 3. Core concept

Think of Spring Security's default session registry as each bouncer at a nightclub chain's separate locations keeping their own private guest list, with no way to see who's already checked in at a *different* location — a guest limited to "one visit at a time" could walk into three different branches simultaneously, since none of the bouncers can see what the others know. `SpringSessionBackedSessionRegistry` is like giving every bouncer, at every branch, live access to one single, shared guest list (the same shared session store) — now any bouncer, at any branch, sees the guest's true total concurrent presence across the entire chain, and can correctly enforce a chain-wide limit.

```java
@Bean
public SpringSessionBackedSessionRegistry<?> sessionRegistry(
        FindByIndexNameSessionRepository<? extends Session> sessionRepository) {
    return new SpringSessionBackedSessionRegistry<>(sessionRepository);
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each instance's Spring Security consults the same shared session registry backed by the shared store, correctly enforcing a cluster-wide concurrent session limit">
  <rect x="20" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Instance A: login</text>

  <rect x="20" y="90" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Instance B: login</text>

  <rect x="330" y="55" width="280" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="80" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SpringSessionBackedSessionRegistry</text>
  <text x="470" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">queries shared session store</text>
  <text x="470" y="118" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">correctly sees BOTH logins, enforces limit</text>

  <line x1="160" y1="43" x2="325" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="160" y1="113" x2="325" y2="105" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Without this adapter, each instance's default registry would only see its own login attempt, missing the other entirely.

## 5. Runnable example

The scenario: configuring Spring Security's `maximumSessions(1)` correctly for a clustered deployment, growing to verify the limit is genuinely enforced across two simulated instances, and finally to customize the eviction behavior so the *oldest* session is expired (rather than the default of rejecting the *new* login) when the limit is exceeded.

### Level 1 — Basic

```java
// ClusteredConcurrentSessionConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.session.SessionRegistry;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.session.FindByIndexNameSessionRepository;
import org.springframework.session.Session;
import org.springframework.session.security.SpringSessionBackedSessionRegistry;

@Configuration
public class ClusteredConcurrentSessionConfig {

    @Bean
    public SessionRegistry sessionRegistry(
            FindByIndexNameSessionRepository<? extends Session> sessionRepository) {
        return new SpringSessionBackedSessionRegistry<>(sessionRepository);
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http, SessionRegistry sessionRegistry) throws Exception {
        http.authorizeHttpRequests(authorize -> authorize.anyRequest().authenticated())
                .formLogin(withDefaults -> {})
                .sessionManagement(session -> session
                        .maximumSessions(1) // only one concurrent session per user, cluster-wide
                        .sessionRegistry(sessionRegistry));

        return http.build();
    }
}
```

**How to run:** with a Redis- or JDBC-backed indexed session repository (card 0010, card 0012) and this configuration, log in as the same user from two different browsers. Expected behavior: the second login either rejects with "maximum sessions exceeded" or (depending on `maxSessionsPreventsLogin` configuration) succeeds while silently invalidating the first browser's session — either way, at most one session for that user remains valid, correctly enforced via the shared store rather than any one instance's local memory.

### Level 2 — Intermediate

Verifying this actually works cluster-wide (not just single-instance, where even the *default*, non-Spring-Session-backed registry would have worked) requires genuinely running two separate instances and confirming the limit still holds across both.

```bash
# Run two instances of the same application sharing the same Redis:
java -Dserver.port=8081 -jar app.jar
java -Dserver.port=8082 -jar app.jar
```

```java
public class ClusterConcurrentSessionVerification {
    // Test procedure (executed manually or via an integration test using two
    // separate HTTP clients pointed at different ports):
    //
    // 1. Log in as "alice" against instance A (port 8081).
    // 2. Log in as "alice" AGAIN, this time against instance B (port 8082).
    // 3. Attempt a request using instance A's original session cookie.
    //
    // Expected with SpringSessionBackedSessionRegistry: step 3 fails —
    // instance B's login was correctly recognized (via the SHARED registry) as
    // exceeding alice's limit of 1, and instance A's original session was invalidated,
    // even though the enforcement decision technically happened on instance B.
}
```

**How to run:** perform the three steps above using two separate terminal `curl` sessions (with separate cookie jars) against the two ports. Expected result: the request in step 3 receives an authentication failure or redirect to login, confirming the *second* instance's login attempt correctly saw and acted on the *first* instance's already-active session — proof the registry is genuinely shared, not instance-local.

What changed: this is the actual, concrete test proving the whole point of this integration — without `SpringSessionBackedSessionRegistry`, this exact test would fail (both sessions would remain valid, since each instance's default local registry would be blind to the other's login).

### Level 3 — Advanced

The default behavior when the limit is exceeded rejects the *new* login attempt — but many products prefer the opposite: allow the new login and silently expire the *oldest* existing session instead, a friendlier experience ("logging in here logged you out elsewhere") that's more intuitive for most non-security-critical consumer applications.

```java
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.session.SessionRegistry;
import org.springframework.security.web.SecurityFilterChain;

public class EvictOldestSessionConfig {

    public SecurityFilterChain filterChain(HttpSecurity http, SessionRegistry sessionRegistry) throws Exception {
        http.sessionManagement(session -> session
                .maximumSessions(1)
                .sessionRegistry(sessionRegistry)
                .maxSessionsPreventsLogin(false) // allow the NEW login; expire the OLD session instead
                .expiredUrl("/session-expired")); // where the evicted session's owner is redirected next

        return http.build();
    }
}
```

**How to run:** with this configuration, log in as the same user in two browsers again. Expected behavior: the second (newer) login succeeds normally; the first browser, on its *next* request (not instantly — it only discovers the eviction when it next tries to use the now-invalidated session), is redirected to `/session-expired` with a friendly explanatory message, rather than the second login attempt being blocked outright.

What changed and why it's production-flavored: this matches the UX most consumer applications actually want ("you've been logged in elsewhere") rather than the stricter, more security-conscious default (blocking the new login) that's more appropriate for genuinely high-security applications — the right choice depends entirely on the specific product's security posture and user expectations, and this configuration makes that choice explicit rather than accepting whichever behavior happens to be the library default.

## 6. Walkthrough

Tracing a concurrent-session-limit enforcement across two instances, in execution order:

1. `alice` logs in successfully via instance A (port 8081); Spring Security's session-management filter, using `SpringSessionBackedSessionRegistry`, records this session — but critically, that "recording" is really just alice's session existing in the *shared* Spring Session store with her principal name indexed (card 0003's `findByPrincipalName` mechanism), not anything instance-A-local.
2. `alice` logs in again via instance B (port 8082). Spring Security's concurrent-session-check, before finalizing this new login, calls `sessionRegistry.getAllSessions(alice, false)` (roughly) to see how many sessions she currently has.
3. Because the registry is `SpringSessionBackedSessionRegistry`, this call queries the *shared* store's `findByPrincipalName("alice")` (card 0003) — correctly returning both the instance-A session and this in-progress instance-B login attempt, regardless of which instance is asking.
4. Finding the count exceeds `maximumSessions(1)`, Spring Security applies the configured policy: under `maxSessionsPreventsLogin(false)` (Level 3), the *older* session (instance A's) is marked expired within the shared store, and the new instance-B login is allowed to proceed.
5. The next time a request arrives at instance A carrying alice's original session cookie, that instance's own Spring Security filters find the session marked expired (via the same shared store) and redirect to `/session-expired` — even though the eviction decision was actually made by instance B, moments earlier, in an entirely separate request.
6. This is the essential proof of correctness: an eviction *decided* on one instance is correctly *observed and enforced* by a completely different instance, purely because both are reading and writing the same shared state rather than two disconnected local registries.

```
Instance A: alice logs in -> session recorded in SHARED store (via principal index)
   |
Instance B: alice logs in again
   |
   sessionRegistry.getAllSessions("alice") -> queries SHARED store -> finds 2 (A's + this new one)
   |
   exceeds maximumSessions(1) -> mark A's session expired in SHARED store; allow B's login
   |
(later) Instance A: request with alice's original cookie
   |
   session lookup finds it marked expired (via SHARED store) -> redirect /session-expired
```

## 7. Gotchas & takeaways

> Using Spring Security's `maximumSessions(...)` with the *default* `SessionRegistryImpl` in a multi-instance deployment doesn't produce an error — it simply silently fails to enforce the limit correctly across instances, since each instance's local registry has no visibility into logins happening on other instances. This is a genuinely easy configuration mistake to miss, since single-instance testing (a common local development and even staging setup) would show the feature working perfectly.

- Always explicitly verify concurrent session limits work correctly across *multiple, separately running instances* (Level 2's test) before considering the feature complete in a clustered deployment — single-instance testing alone cannot catch this specific class of misconfiguration.
- `maxSessionsPreventsLogin(true)` (the default) versus `false` (Level 3) is a genuine product decision, not just a technical setting — weigh which behavior better matches the application's actual security posture and user experience expectations before picking one.
- `SpringSessionBackedSessionRegistry` requires a `FindByIndexNameSessionRepository` (card 0003), not just a bare `SessionRepository` — this is another reason to favor the indexed repository variants (`RedisIndexedSessionRepository`, `JdbcIndexedSessionRepository`) over their simpler counterparts (card 0011) whenever concurrent session control is a requirement.
- A session marked "expired" by this eviction mechanism isn't necessarily removed from the store *immediately* — the evicted user only discovers and is redirected away once their next request is processed against that now-invalid session, which is normal, expected behavior, not a bug or delay worth chasing.
- This integration is specifically about *Spring Security's* concurrent session control mechanism — it's a separate, though related, concern from the general-purpose "list/limit sessions per user" patterns covered in card 0003, which can be built independently of whether Spring Security's own `maximumSessions(...)` feature is used at all.
