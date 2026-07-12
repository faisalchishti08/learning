---
card: spring-session
gi: 8
slug: session-events-created-deleted-expired
title: "Session events (created/deleted/expired)"
---

## 1. What it is

Spring Session publishes Spring `ApplicationEvent`s for major session lifecycle transitions — `SessionCreatedEvent`, `SessionDeletedEvent`, `SessionExpiredEvent`, and `SessionDestroyedEvent` (a common superclass of the latter two) — that any `@EventListener` in the application can subscribe to, entirely independent of the request that caused them.

## 2. Why & when

Session state changes (a user logging in and creating a session, a session timing out, an explicit logout deleting one) are often meaningful beyond just the request that caused them — auditing when users' sessions end, updating a live "currently online" count, or cleaning up resources tied to a session (temporary files, in-progress upload state) that should be released once that session is truly gone. Polling the session store for these transitions would be wasteful and laggy; events let the application react the moment Spring Session itself detects the change.

Reach for session events when:

- Building a live "active users" indicator or dashboard that needs to update immediately as sessions come and go, not on a polling interval.
- Auditing session lifecycle for security or compliance purposes — recording exactly when each session was created, and whether it ended via explicit logout (`SessionDeletedEvent`) or timeout (`SessionExpiredEvent`), which are meaningfully different for a security audit trail.
- Cleaning up session-associated resources (temp files, WebSocket subscriptions, cached data keyed by session ID) precisely when a session ends, rather than leaking them until some unrelated cleanup pass notices.

## 3. Core concept

Think of session events as a building's key-card system publishing a live feed of every badge-in and badge-out event to a central security office — rather than the security team having to periodically walk the building checking who's still inside (polling), they get notified the instant someone badges in (`SessionCreatedEvent`), badges out at a turnstile (`SessionDeletedEvent`), or their temporary visitor badge simply times out unused (`SessionExpiredEvent`). Anyone in the security office (any `@EventListener`) can subscribe to this feed and react immediately, without needing to be the one checking badges at the door.

```java
@EventListener
public void onSessionCreated(SessionCreatedEvent event) {
    log.info("Session created: {}", event.getSessionId());
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Session lifecycle transitions in the store trigger corresponding Spring application events that any listener can subscribe to">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Session store</text>
  <text x="95" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">create/delete/expire</text>

  <rect x="250" y="80" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring ApplicationEvent</text>
  <text x="340" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Created/Deleted/Expired</text>

  <rect x="510" y="20" width="130" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="575" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Online-count listener</text>

  <rect x="510" y="90" width="130" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="575" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Audit log listener</text>

  <rect x="510" y="160" width="130" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="575" y="185" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Cleanup listener</text>

  <line x1="170" y1="110" x2="245" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="430" y1="110" x2="505" y2="40" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="430" y1="110" x2="505" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="430" y1="110" x2="505" y2="180" stroke="#8b949e" stroke-width="1.5"/>
</svg>

Multiple independent listeners can all react to the same underlying event with no coordination needed between them.

## 5. Runnable example

The scenario: building a live "active sessions" counter driven by session events, growing to distinguish explicit logout from timeout in an audit log, and finally to clean up a session-associated resource (an in-progress upload's temp directory) reliably when its owning session ends.

### Level 1 — Basic

```java
// ActiveSessionCounter.java
import org.springframework.context.event.EventListener;
import org.springframework.session.events.SessionCreatedEvent;
import org.springframework.session.events.SessionDestroyedEvent;
import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicInteger;

@Component
public class ActiveSessionCounter {

    private final AtomicInteger activeCount = new AtomicInteger(0);

    @EventListener
    public void onCreated(SessionCreatedEvent event) {
        int current = activeCount.incrementAndGet();
        System.out.println("Session created: " + event.getSessionId() + " (active: " + current + ")");
    }

    @EventListener
    public void onDestroyed(SessionDestroyedEvent event) {
        int current = activeCount.decrementAndGet();
        System.out.println("Session ended: " + event.getSessionId() + " (active: " + current + ")");
    }

    public int getActiveCount() {
        return activeCount.get();
    }
}
```

**How to run:** with any Spring Session store configured (Redis's session events require additional keyspace notification setup, covered in Level 2 — a JDBC-backed store publishes these more directly), create a few sessions from different browser sessions and let one expire or explicitly log out. Expected console output: `Session created` lines as each session starts, and `Session ended` lines as each ends, with `getActiveCount()` tracking the live total.

### Level 2 — Intermediate

Redis specifically requires keyspace notifications to be enabled for expiration events to be detected and translated into Spring Session events at all — a common gotcha where events silently never fire because this Redis-side configuration was missed.

```java
// RedisKeyspaceNotificationConfig.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.stereotype.Component;

@Component
public class RedisKeyspaceNotificationConfig {

    @Autowired
    private RedisConnectionFactory connectionFactory;

    @EventListener(ContextRefreshedEvent.class)
    public void enableKeyspaceNotifications() {
        connectionFactory.getConnection().setConfig("notify-keyspace-events", "Egx");
        // "Ex" = expired events, "g" = generic commands — required for Spring Session's
        // Redis-backed implementation to detect and translate expiration into SessionExpiredEvent.
    }
}
```

**How to run:** without this configuration, let a Redis-backed session expire and observe that `ActiveSessionCounter`'s `onDestroyed` handler never fires for it — the count silently drifts wrong over time. Add this configuration, restart, and repeat the same expiration test. Expected behavior: `SessionDestroyedEvent` (specifically as a `SessionExpiredEvent`, its subtype) now fires correctly when the Redis key's TTL elapses, and the active count decrements as expected.

What changed: this closes a real, easy-to-miss gap — Redis-backed session *expiration* events specifically depend on Redis server-side configuration that Spring Boot doesn't set automatically, unlike explicit deletion events (from `session.invalidate()`), which work without this extra step.

### Level 3 — Advanced

Distinguishing `SessionDeletedEvent` (explicit logout or invalidation) from `SessionExpiredEvent` (timeout) matters for both audit logging and resource cleanup — an explicit logout might mean "clean up immediately, the user is done," while an expiration might warrant a different handling path (e.g. flagging for review if it happened mid-upload).

```java
import org.springframework.context.event.EventListener;
import org.springframework.session.events.SessionDeletedEvent;
import org.springframework.session.events.SessionExpiredEvent;
import org.springframework.stereotype.Component;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class UploadCleanupListener {

    // Tracks temp directories created for in-progress uploads, keyed by session ID.
    private final Map<String, Path> uploadTempDirsBySession = new ConcurrentHashMap<>();

    public void registerUpload(String sessionId, Path tempDir) {
        uploadTempDirsBySession.put(sessionId, tempDir);
    }

    @EventListener
    public void onExplicitLogout(SessionDeletedEvent event) {
        System.out.printf("[%s] AUDIT: session %s ended via explicit logout%n", Instant.now(), event.getSessionId());
        cleanupUploadDir(event.getSessionId());
    }

    @EventListener
    public void onTimeout(SessionExpiredEvent event) {
        System.out.printf("[%s] AUDIT: session %s ended via timeout (possible abandoned upload)%n",
                Instant.now(), event.getSessionId());
        cleanupUploadDir(event.getSessionId());
    }

    private void cleanupUploadDir(String sessionId) {
        Path tempDir = uploadTempDirsBySession.remove(sessionId);
        if (tempDir != null) {
            try {
                Files.walk(tempDir)
                        .sorted(java.util.Comparator.reverseOrder())
                        .map(Path::toFile)
                        .forEach(File::delete);
                System.out.println("Cleaned up temp upload dir for session " + sessionId);
            } catch (Exception e) {
                System.err.println("Failed to clean up temp dir for session " + sessionId + ": " + e.getMessage());
            }
        }
    }
}
```

**How to run:** register a temp directory for a test session via `registerUpload(...)`, then trigger both an explicit logout (expect `SessionDeletedEvent`, distinct audit message) and, separately, let another session simply time out (expect `SessionExpiredEvent`, a different audit message flagging a possible abandoned upload). Verify the temp directory is deleted from disk in both cases, and that the audit log correctly distinguishes which path caused it.

What changed and why it's production-flavored: resources tied to a session's lifetime (temp files being the classic example) are now reliably released exactly when that session truly ends, regardless of whether it ended cleanly (logout) or was abandoned (timeout) — and the audit trail preserves the distinction, which matters for diagnosing whether abandoned uploads are a UX problem (users walking away mid-upload) worth investigating.

## 6. Walkthrough

Tracing session events for both an explicit logout and a timeout, in execution order:

1. A user uploads a large file; the application calls `uploadCleanupListener.registerUpload(session.getId(), tempDir)` to associate a temp directory with their session for later cleanup.
2. **Explicit logout path:** the user clicks "log out," which calls `session.invalidate()` (or Spring Security's logout handler does so internally). The configured `SessionRepository` deletes the session from the store and, as part of that deletion, Spring Session publishes a `SessionDeletedEvent` carrying the session's ID.
3. Spring's event infrastructure dispatches this event synchronously to every registered `@EventListener` matching its type — `ActiveSessionCounter.onDestroyed` (Level 1, since `SessionDeletedEvent` is a `SessionDestroyedEvent`) and `UploadCleanupListener.onExplicitLogout` (Level 3) both fire.
4. `onExplicitLogout` logs the audit line and calls `cleanupUploadDir`, removing the temp directory from disk immediately.
5. **Timeout path (a different session, abandoned mid-upload):** the user closes their laptop without logging out; 30 minutes pass with no requests. For a Redis-backed store, once keyspace notifications are correctly configured (Level 2), Redis's own key expiration triggers a notification that Spring Session's Redis integration translates into a `SessionExpiredEvent`.
6. The same dispatch mechanism delivers this event to `onTimeout` instead of `onExplicitLogout` — the listener logs a distinctly different audit message ("possible abandoned upload") and performs the identical cleanup, ensuring the temp directory doesn't linger regardless of which path ended the session.

```
Explicit logout:  session.invalidate() -> repository deletes -> SessionDeletedEvent
                                                                        |
                                                     onExplicitLogout: audit "explicit logout" + cleanup

Timeout:          Redis TTL expires -> keyspace notification -> SessionExpiredEvent
                                                                        |
                                                     onTimeout: audit "timeout, possible abandoned upload" + cleanup

Both paths -> UploadCleanupListener.cleanupUploadDir(sessionId) -> temp dir removed
```

## 7. Gotchas & takeaways

> Redis-backed `SessionExpiredEvent`s require `notify-keyspace-events` to be explicitly enabled on the Redis server — without it (the default Redis configuration), expiration still happens correctly (the session is genuinely gone from Redis, card 0007), but Spring Session never learns about it and no event fires, silently breaking any cleanup or audit logic that depends on expiration events specifically.

- `SessionDestroyedEvent` is the common superclass of both `SessionDeletedEvent` and `SessionExpiredEvent` — a listener that only needs to react to "the session is gone, regardless of why" (like the basic counter in Level 1) should listen for the superclass; a listener that needs to distinguish the cause (Level 3's audit logging) should listen for the specific subtypes.
- Event listeners run synchronously by default within the thread that triggered the event — a slow listener (heavy file I/O, a blocking external call) can noticeably delay whatever triggered the event; use `@Async` on the listener method if that latency matters and the ordering guarantee isn't required.
- Session events reflect changes at the *store* level, not necessarily the exact moment a user's browser tab closes — a browser closing doesn't immediately delete or expire a session; the session simply sits idle until its `maxInactiveInterval` elapses (card 0007), and only then does `SessionExpiredEvent` fire.
- Don't rely on session events as the sole mechanism for critical cleanup in a multi-instance deployment without considering event delivery scope — depending on the store implementation, these events are typically published only within the JVM instance that detects the transition, which is usually fine for per-instance concerns (like the local `ActiveSessionCounter`) but matters if a cluster-wide accurate count is needed instead.
- Test both the explicit-deletion and expiration paths independently before relying on session events for anything security- or resource-critical — they're triggered through genuinely different mechanisms under the hood (an application-initiated delete versus a store-detected timeout), and it's easy to verify one path works while never noticing the other is silently broken.
