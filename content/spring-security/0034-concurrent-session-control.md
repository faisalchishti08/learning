---
card: spring-security
gi: 34
slug: concurrent-session-control
title: "Concurrent session control"
---

## 1. What it is

Concurrent session control limits how many simultaneous sessions a single principal may hold, tracked by `SessionRegistry` (which maps each principal to its list of currently registered sessions) and enforced by `ConcurrentSessionFilter`, configured via `sessionManagement(session -> session.maximumSessions(1))`. When a new login would exceed the configured maximum, one of two policies applies: either the new login is rejected outright, or (the default) the *oldest* existing session is expired to make room for the new one.

```java
http.sessionManagement(session -> session
        .maximumSessions(1)
        .maxSessionsPreventsLogin(false) // default: expire the OLDEST session to make room
        .expiredUrl("/login?expired"));
```

## 2. Why & when

Some applications have a genuine business requirement that a given account only ever be active from one place at a time — a banking application not wanting a session to remain silently active on a shared or previously-used device after logging in elsewhere, or a licensing model that ties a subscription to one concurrent session. `maximumSessions(1)` (or a higher number) plus `SessionRegistry` gives Spring Security the bookkeeping needed to enforce this: every new login is checked against how many sessions the same principal already holds, and the configured policy (block the new login, or expire the oldest existing one) is applied consistently.

Reach for concurrent session control when:

- The application has a genuine "only one active session per user" (or "at most N") business requirement — commonly seen in security-sensitive applications (banking, healthcare) or licensing-constrained ones.
- `maxSessionsPreventsLogin(true)` when a *new* login attempt should itself be rejected while an existing session remains active (forcing the user to explicitly end the old session first); `maxSessionsPreventsLogin(false)` (the default) when the *newest* login should always win, silently expiring whichever session is oldest.
- Debugging why a user reports being unexpectedly logged out on one device after logging in on another — checking `maximumSessions` and `maxSessionsPreventsLogin`'s configured values is the first place to look.

## 3. Core concept

```
 SessionRegistry tracks: principal -> [list of currently registered sessionIds]

 on a NEW successful login:
   currentSessionCount = sessionRegistry.getAllSessions(principal).size()
   IF currentSessionCount >= maximumSessions:
       IF maxSessionsPreventsLogin == true:
           REJECT the new login outright (an AUTHENTICATION FAILURE)
       ELSE (default):
           expire the OLDEST registered session for this principal
           the NEW login proceeds and succeeds

 ConcurrentSessionFilter, on EVERY subsequent request:
   checks whether THIS request's session has been marked expired (by the block above)
   IF expired: redirect to expiredUrl ("/login?expired"), forcing re-authentication
```

The check happens at login time; the *enforcement* against an already-expired session happens on its very next request, via `ConcurrentSessionFilter`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A new login checks SessionRegistry for the principal's existing session count if at the configured maximum either the new login is rejected or the oldest existing session is marked expired ConcurrentSessionFilter later redirects any request using an expired session to a login page with an expired indicator">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">new login attempt</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">for principal alice</text>

  <rect x="215" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="305" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">SessionRegistry check</text>
  <text x="305" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">count &gt;= maximumSessions?</text>

  <rect x="450" y="15" width="170" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="535" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">expire OLDEST session</text>

  <rect x="450" y="120" width="170" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="535" y="145" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">reject new login</text>

  <defs><marker id="a34" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="85" x2="215" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a34)"/>
  <line x1="395" y1="78" x2="450" y2="40" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a34)"/>
  <text x="420" y="55" fill="#8b949e" font-size="6.5" font-family="sans-serif">preventsLogin=false</text>
  <line x1="395" y1="98" x2="450" y2="135" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a34)"/>
  <text x="420" y="120" fill="#8b949e" font-size="6.5" font-family="sans-serif">preventsLogin=true</text>
</svg>

The same "count exceeded" condition produces two entirely different outcomes depending purely on `maxSessionsPreventsLogin`.

## 5. Runnable example

The scenario: model `SessionRegistry` and both concurrent-session policies, then show `ConcurrentSessionFilter`'s later enforcement against a session already marked expired.

### Level 1 — Basic

A minimal session registry tracking sessions per principal, with the default (expire-oldest) policy.

```java
import java.util.*;

public class ConcurrentSessionLevel1 {
    static Map<String, List<String>> sessionRegistry = new HashMap<>(); // principal -> ordered list of sessionIds
    static Set<String> expiredSessions = new HashSet<>();
    static final int MAXIMUM_SESSIONS = 1;

    static String login(String principal, String sessionId) {
        List<String> existing = sessionRegistry.computeIfAbsent(principal, k -> new ArrayList<>());
        if (existing.size() >= MAXIMUM_SESSIONS) {
            String oldest = existing.remove(0); // expire-oldest policy (the DEFAULT)
            expiredSessions.add(oldest);
        }
        existing.add(sessionId);
        return "logged in, session=" + sessionId;
    }

    public static void main(String[] args) {
        System.out.println(login("alice", "session-A"));
        System.out.println(login("alice", "session-B")); // second concurrent login for alice
        System.out.println("session-A expired? " + expiredSessions.contains("session-A"));
        System.out.println("current sessions for alice: " + sessionRegistry.get("alice"));
    }
}
```

How to run: `java ConcurrentSessionLevel1.java`

The second login for `"alice"` finds `existing.size() >= 1`, so it expires `"session-A"` (the oldest) before registering `"session-B"` — `sessionRegistry.get("alice")` ends up holding only `["session-B"]`, and `"session-A"` is now marked expired.

### Level 2 — Intermediate

Add the alternative policy, `maxSessionsPreventsLogin(true)`, rejecting the new login instead of expiring the old one.

```java
import java.util.*;

public class ConcurrentSessionLevel2 {
    static Map<String, List<String>> sessionRegistry = new HashMap<>();
    static Set<String> expiredSessions = new HashSet<>();
    static final int MAXIMUM_SESSIONS = 1;

    static String login(String principal, String sessionId, boolean maxSessionsPreventsLogin) {
        List<String> existing = sessionRegistry.computeIfAbsent(principal, k -> new ArrayList<>());
        if (existing.size() >= MAXIMUM_SESSIONS) {
            if (maxSessionsPreventsLogin) {
                return "401 Unauthorized: maximum sessions (" + MAXIMUM_SESSIONS + ") already reached for " + principal;
            }
            String oldest = existing.remove(0);
            expiredSessions.add(oldest);
        }
        existing.add(sessionId);
        return "logged in, session=" + sessionId;
    }

    public static void main(String[] args) {
        System.out.println("-- policy: maxSessionsPreventsLogin = true --");
        System.out.println(login("alice", "session-A", true));
        System.out.println(login("alice", "session-B", true)); // BLOCKED, session-A is still active
        System.out.println("sessions for alice: " + sessionRegistry.get("alice"));

        sessionRegistry.clear();
        System.out.println();
        System.out.println("-- policy: maxSessionsPreventsLogin = false (default) --");
        System.out.println(login("bob", "session-C", false));
        System.out.println(login("bob", "session-D", false)); // ALLOWED, session-C is expired instead
        System.out.println("sessions for bob: " + sessionRegistry.get("bob"));
    }
}
```

How to run: `java ConcurrentSessionLevel2.java`

With `maxSessionsPreventsLogin = true`, alice's second login attempt is rejected outright and `session-A` remains the only registered session; with the flag `false`, bob's second login succeeds and `session-C` is silently expired instead — the identical "at the limit" condition produces opposite outcomes purely based on this one configuration flag.

### Level 3 — Advanced

Add `ConcurrentSessionFilter`-style enforcement: a request using an already-expired session is redirected, regardless of how much time has passed since the expiry was recorded.

```java
import java.util.*;

public class ConcurrentSessionLevel3 {
    static Map<String, List<String>> sessionRegistry = new HashMap<>();
    static Set<String> expiredSessions = new HashSet<>();
    static final int MAXIMUM_SESSIONS = 1;

    static String login(String principal, String sessionId) {
        List<String> existing = sessionRegistry.computeIfAbsent(principal, k -> new ArrayList<>());
        if (existing.size() >= MAXIMUM_SESSIONS) {
            String oldest = existing.remove(0);
            expiredSessions.add(oldest);
        }
        existing.add(sessionId);
        return "logged in, session=" + sessionId;
    }

    // models ConcurrentSessionFilter checking EVERY subsequent request against the expired set
    static String handleRequest(String sessionId, String path) {
        if (expiredSessions.contains(sessionId)) {
            return "302 Found -> Location: /login?expired (session " + sessionId + " was superseded by a newer login)";
        }
        return "200 OK, request to " + path + " served normally";
    }

    public static void main(String[] args) {
        System.out.println(login("alice", "session-A"));
        System.out.println("alice, session-A, requesting /account BEFORE any second login: " + handleRequest("session-A", "/account"));

        System.out.println(login("alice", "session-B")); // logs in again -- session-A now expired
        System.out.println("alice, session-A, requesting /account AFTER second login: " + handleRequest("session-A", "/account"));
        System.out.println("alice, session-B, requesting /account: " + handleRequest("session-B", "/account"));
    }
}
```

How to run: `java ConcurrentSessionLevel3.java`

Before the second login, `session-A` serves requests normally; the moment `login("alice", "session-B")` runs and expires `session-A`, the *very next* request using `session-A` is redirected to `/login?expired`, while requests using the newer `session-B` continue to succeed — demonstrating that expiry takes effect immediately, enforced on the first request that follows it, not merely reflected as some passive flag.

## 6. Walkthrough

Trace the full sequence of calls in Level 3's `main`.

1. `login("alice", "session-A")` runs first: `sessionRegistry.computeIfAbsent("alice", ...)` creates a new empty list for alice, `existing.size()` is `0`, which is not `>= 1`, so no expiry happens; `"session-A"` is added, and `sessionRegistry.get("alice")` now holds `["session-A"]`.
2. `handleRequest("session-A", "/account")` runs next: `expiredSessions.contains("session-A")` is `false`, so it returns the normal `"200 OK"` message.
3. `login("alice", "session-B")` runs: `existing.size()` is now `1`, which is `>= MAXIMUM_SESSIONS (1)`, so the method removes and expires `"session-A"` (`existing.remove(0)` and `expiredSessions.add("session-A")`), then adds `"session-B"` — `sessionRegistry.get("alice")` now holds only `["session-B"]`.
4. `handleRequest("session-A", "/account")` runs again, with the *same* session ID as step 2's call: this time `expiredSessions.contains("session-A")` is `true` (set in step 3), so the method returns the `/login?expired` redirect message instead — the exact same session ID that worked in step 2 now fails, purely because of the intervening login in step 3.
5. `handleRequest("session-B", "/account")` runs last: `expiredSessions.contains("session-B")` is `false` (it's the newly registered, active session), so it returns the normal `"200 OK"` message — the new session works exactly as the old one did before being superseded.

```
login(alice, session-A)                    -> registered, sessionRegistry["alice"] = [session-A]
handleRequest(session-A, /account)          -> 200 OK (not yet expired)
login(alice, session-B)                    -> session-A EXPIRED, sessionRegistry["alice"] = [session-B]
handleRequest(session-A, /account) AGAIN    -> 302 -> /login?expired (now expired)
handleRequest(session-B, /account)          -> 200 OK (the new, active session)
```

## 7. Gotchas & takeaways

> **Gotcha:** `SessionRegistry`'s default in-memory implementation does not work correctly across multiple application server instances in a load-balanced deployment without a shared, distributed backing store — each instance would maintain its own independent view of "how many sessions does this principal have," allowing a user to exceed the configured maximum by hitting different instances. A distributed session store (or a `SessionRegistry` implementation backed by one) is required for concurrent session control to work correctly at scale.

- Concurrent session control enforces a maximum number of simultaneous sessions per principal, using `SessionRegistry` to track active sessions and `ConcurrentSessionFilter` to reject requests from sessions that have since been superseded.
- `maxSessionsPreventsLogin(true)` rejects a *new* login while the limit is reached; `maxSessionsPreventsLogin(false)` (the default) instead expires the *oldest* existing session, letting the new login succeed.
- Expiry takes effect on login (or session-count-check) but is only *enforced* the next time the now-expired session is actually used, at which point `ConcurrentSessionFilter` redirects it.
- A distributed deployment requires a shared `SessionRegistry` backing store, or the concurrent-session limit can be silently bypassed by spreading logins across different application instances.
