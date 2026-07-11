---
card: spring-security
gi: 35
slug: session-management-fixation-protection
title: "Session management & fixation protection"
---

## 1. What it is

Session fixation is an attack where an attacker plants a *known* session identifier on a victim (via a crafted link, or a cookie set before login) and waits for the victim to authenticate using that same session ID, at which point the attacker — already knowing that ID — can hijack the now-authenticated session. Spring Security's default protection, configured via `sessionManagement(session -> session.sessionFixation(fixation -> fixation.changeSessionId()))`, defeats this by creating a brand-new session identifier at the moment of successful authentication, invalidating whatever session ID existed beforehand, so any ID an attacker planted pre-login is worthless post-login.

```java
http.sessionManagement(session -> session
        .sessionFixation(fixation -> fixation.changeSessionId()) // the DEFAULT since Servlet 3.1+ containers
        .maximumSessions(1));
```

## 2. Why & when

Without fixation protection, a session ID is the same object before and after login — meaning if an attacker can get a victim's browser to use a session ID the attacker already knows (a surprisingly easy thing to arrange in some setups, such as a session ID accepted from a URL parameter, or a cookie set by a shared or compromised network), the attacker can simply wait for the victim to log in using that ID and then use the identical ID themselves to inherit the now-authenticated session, entirely bypassing the need to guess or steal a password. `changeSessionId()` closes this specific window by making the pre-login and post-login session identifiers *always* different, so an attacker's foreknowledge of the pre-login ID is rendered useless the moment real authentication occurs.

Reach for understanding (or explicitly configuring) session fixation protection when:

- Confirming a Spring Boot application's default posture — `changeSessionId()` is already the default in modern Spring Security, so most applications are protected without any extra configuration, but confirming this explicitly is worthwhile in a security review.
- `migrateSession()` (an older, alternative strategy) creates an entirely new `HttpSession` object (not just a new ID for the same session) and copies its attributes over — relevant when integrating with legacy session-clustering infrastructure that has trouble with in-place session ID changes.
- `none()` disables the protection entirely — reach for this only in narrow, well-understood integration scenarios (some legacy single-sign-on setups genuinely require a stable session ID across the login boundary), never as a general default.

## 3. Core concept

```
 WITHOUT fixation protection:
   pre-login session ID:  ABC123 (possibly ALREADY KNOWN to an attacker who planted it)
   ... user authenticates ...
   post-login session ID: ABC123  (SAME ID -- attacker's foreknowledge is now USEFUL)

 WITH changeSessionId() (the default):
   pre-login session ID:  ABC123 (possibly known to an attacker)
   ... user authenticates ...
   post-login session ID: XYZ789 (a BRAND NEW, freshly generated ID -- ABC123 is now invalidated)
   attacker's foreknowledge of ABC123 is now WORTHLESS
```

The defense is simple and structural: never let a pre-authentication session ID survive into a post-authentication state.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An attacker plants a known session ID on a victim before login the victim authenticates using that session Spring Security generates a brand new session ID at the moment of authentication invalidating the planted one so the attacker's foreknowledge becomes useless">
  <rect x="15" y="20" width="190" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="110" y="38" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">attacker plants session ID</text>
  <text x="110" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ABC123 on victim's browser</text>

  <rect x="15" y="120" width="190" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="110" y="138" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">victim logs in using</text>
  <text x="110" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">session ID ABC123</text>

  <rect x="260" y="70" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="90" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">changeSessionId()</text>
  <text x="360" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">at the moment of login</text>

  <rect x="510" y="70" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="90" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">XYZ789</text>
  <text x="570" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(new, unknown)</text>

  <defs><marker id="a35" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="205" y1="41" x2="260" y2="85" stroke="#8b949e" stroke-width="1" marker-end="url(#a35)"/>
  <line x1="205" y1="141" x2="260" y2="105" stroke="#8b949e" stroke-width="1" marker-end="url(#a35)"/>
  <line x1="460" y1="95" x2="510" y2="95" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a35)"/>
</svg>

The attacker's planted ID (left) reaches authentication, but exits as a completely different, unguessable ID (right).

## 5. Runnable example

The scenario: simulate a fixation attack against an unprotected system, showing the attacker's exploit succeeding, then apply `changeSessionId()`-style protection and show the identical attack failing, then add `migrateSession()`-style protection (a new session object with copied attributes) as an alternative that achieves the same defensive outcome differently.

### Level 1 — Basic

An unprotected system where the session ID never changes across login — the vulnerable baseline.

```java
import java.util.*;

public class FixationLevel1 {
    static Map<String, String> sessionToUser = new HashMap<>(); // sessionId -> authenticated username (or absent)

    static void plantSession(String sessionId) {
        sessionToUser.putIfAbsent(sessionId, null); // session exists, but NOT yet authenticated
    }

    // NO fixation protection: the session ID is left completely unchanged after login
    static void login(String sessionId, String username) {
        sessionToUser.put(sessionId, username); // SAME sessionId, now associated with a real user
    }

    public static void main(String[] args) {
        String attackerPlantedId = "ABC123"; // the attacker CHOSE this value and already knows it

        plantSession(attackerPlantedId); // attacker gets the victim to load a link carrying this session ID
        System.out.println("before login: " + sessionToUser.get(attackerPlantedId));

        login(attackerPlantedId, "victim"); // victim unknowingly logs in using the attacker's planted session

        // the attacker, who already knew "ABC123", can now use it directly:
        System.out.println("attacker uses KNOWN id 'ABC123' -> authenticated as: " + sessionToUser.get(attackerPlantedId));
    }
}
```

How to run: `java FixationLevel1.java`

`login` never changes `sessionId` at all — it simply associates the *same* `"ABC123"` (which the attacker chose and already knew) with `"victim"`, so the attacker's own, independently-held copy of that session ID now grants them the victim's authenticated session.

### Level 2 — Intermediate

Apply `changeSessionId()`-style protection: generate a fresh session ID at the moment of authentication, invalidating the old one.

```java
import java.util.*;

public class FixationLevel2 {
    static Map<String, String> sessionToUser = new HashMap<>();
    static Set<String> invalidatedSessionIds = new HashSet<>();
    static int idCounter = 1000;

    static void plantSession(String sessionId) { sessionToUser.putIfAbsent(sessionId, null); }

    static String freshSessionId() { return "SESSION-" + (idCounter++); }

    // WITH fixation protection: changeSessionId() -- a NEW id is generated at the moment of login
    static String login(String preLoginSessionId, String username) {
        invalidatedSessionIds.add(preLoginSessionId); // the OLD id is explicitly invalidated
        sessionToUser.remove(preLoginSessionId);
        String newSessionId = freshSessionId();
        sessionToUser.put(newSessionId, username);
        return newSessionId; // returned to the LEGITIMATE browser via a Set-Cookie response
    }

    static String useSession(String sessionId) {
        if (invalidatedSessionIds.contains(sessionId)) return "REJECTED: session id has been invalidated";
        String user = sessionToUser.get(sessionId);
        return user != null ? "authenticated as " + user : "not authenticated";
    }

    public static void main(String[] args) {
        String attackerPlantedId = "ABC123";
        plantSession(attackerPlantedId);

        String newSessionId = login(attackerPlantedId, "victim"); // the VICTIM's browser receives newSessionId
        System.out.println("new session id issued to the legitimate browser: " + newSessionId);

        System.out.println("attacker tries the OLD, known id 'ABC123': " + useSession(attackerPlantedId));
        System.out.println("legitimate browser uses its NEW id: " + useSession(newSessionId));
    }
}
```

How to run: `java FixationLevel2.java`

`login` now invalidates `preLoginSessionId` and generates a completely fresh `newSessionId`, which only the legitimate browser receives (via the response's `Set-Cookie` header, not modeled directly here); the attacker's attempt using the old, known `"ABC123"` is rejected outright, while the legitimate browser's new ID works correctly — the attack from Level 1 no longer succeeds.

### Level 3 — Advanced

Add `migrateSession()`-style protection as an alternative: instead of just changing the ID, create an entirely new session object and copy over its attributes, useful for infrastructure where in-place ID changes are problematic.

```java
import java.util.*;

public class FixationLevel3 {
    record SessionData(Map<String, Object> attributes, String user) {}
    static Map<String, SessionData> sessions = new HashMap<>();
    static Set<String> invalidatedSessionIds = new HashSet<>();
    static int idCounter = 1000;

    static void plantSession(String sessionId) {
        Map<String, Object> attrs = new HashMap<>();
        attrs.put("cartItems", List.of("item-42")); // some PRE-LOGIN session state worth preserving
        sessions.put(sessionId, new SessionData(attrs, null));
    }

    static String freshSessionId() { return "SESSION-" + (idCounter++); }

    // migrateSession(): an ENTIRELY NEW session object, with attributes COPIED over (not just a renamed reference)
    static String loginWithMigration(String preLoginSessionId, String username) {
        SessionData old = sessions.get(preLoginSessionId);
        invalidatedSessionIds.add(preLoginSessionId);
        sessions.remove(preLoginSessionId);

        String newSessionId = freshSessionId();
        Map<String, Object> copiedAttributes = new HashMap<>(old.attributes()); // COPY, not the same object
        sessions.put(newSessionId, new SessionData(copiedAttributes, username));
        return newSessionId;
    }

    static String useSession(String sessionId) {
        if (invalidatedSessionIds.contains(sessionId)) return "REJECTED: invalidated";
        SessionData data = sessions.get(sessionId);
        if (data == null) return "no such session";
        return "authenticated as " + data.user() + ", cartItems=" + data.attributes().get("cartItems");
    }

    public static void main(String[] args) {
        String preLoginId = "ABC123";
        plantSession(preLoginId);
        System.out.println("pre-login cart preserved? " + sessions.get(preLoginId).attributes().get("cartItems"));

        String newId = loginWithMigration(preLoginId, "alice");

        System.out.println("attacker's old id: " + useSession(preLoginId));
        System.out.println("legitimate new id: " + useSession(newId));
    }
}
```

How to run: `java FixationLevel3.java`

`loginWithMigration` reads the pre-login session's `attributes` (containing `cartItems`), invalidates the old session entirely, then creates a *new* `SessionData` object under a new ID, with a *copy* of those attributes attached to the now-authenticated user — alice's pre-login shopping cart survives the login boundary (visible under the new ID), while the old ID is fully invalidated exactly as in `changeSessionId()`'s approach, achieving the same fixation defense with a slightly different mechanism (a new object with copied state, rather than simply renaming the existing one).

## 6. Walkthrough

Trace `loginWithMigration("ABC123", "alice")` from Level 3.

1. `sessions.get("ABC123")` retrieves the `SessionData` created by `plantSession`, which holds `attributes = {"cartItems": ["item-42"]}` and `user = null` — this is assigned to `old`.
2. `invalidatedSessionIds.add("ABC123")` marks the old ID as invalidated, and `sessions.remove("ABC123")` deletes its entry from the `sessions` map entirely — from this point on, `"ABC123"` no longer maps to any session data at all.
3. `freshSessionId()` generates `"SESSION-1000"` (assuming this is the first call), assigned to `newSessionId`.
4. `new HashMap<>(old.attributes())` creates a *new*, independent map containing a copy of `old`'s entries — this is `copiedAttributes`, holding its own copy of `{"cartItems": ["item-42"]}`, not a reference to the original map.
5. `sessions.put(newSessionId, new SessionData(copiedAttributes, "alice"))` registers a brand-new `SessionData` object under `"SESSION-1000"`, now correctly associated with `"alice"` and carrying the copied cart attribute — the method returns `"SESSION-1000"` as `newId`.
6. Back in `main`, `useSession("ABC123")` checks `invalidatedSessionIds.contains("ABC123")`, which is `true`, so it returns `"REJECTED: invalidated"` immediately — the attacker's known ID is now useless; `useSession(newId)` finds the new `SessionData`, returning `"authenticated as alice, cartItems=[item-42]"` — the legitimate user's authenticated identity *and* their pre-login cart state both survived, just under a completely new, attacker-unknown ID.

```
plantSession("ABC123")                -> cartItems=[item-42] stored under ABC123 (unauthenticated)
loginWithMigration("ABC123", "alice") -> ABC123 invalidated; NEW id "SESSION-1000" created
                                          with COPIED cartItems, now associated with alice
useSession("ABC123")                  -> REJECTED (invalidated)
useSession("SESSION-1000")            -> authenticated as alice, cartItems=[item-42] (preserved!)
```

## 7. Gotchas & takeaways

> **Gotcha:** explicitly configuring `sessionFixation(fixation -> fixation.none())` disables this protection entirely and should only ever be done for a specific, well-understood integration reason (certain legacy SSO handoffs) — doing so without a clear reason reopens exactly the session fixation vulnerability this default protection exists to close.

- Session fixation exploits an unchanged session ID across the login boundary — an attacker who can plant a known ID on a victim's browser inherits that victim's authenticated session once they log in using it.
- `changeSessionId()` (the default in modern Spring Security) generates a brand-new session ID at the moment of authentication, invalidating whatever ID existed beforehand — the simplest and most common defense.
- `migrateSession()` achieves the same defensive outcome by creating an entirely new session object with copied attributes, useful when infrastructure constraints make in-place session ID changes problematic.
- This protection is on by default in modern Spring Security applications — explicitly disabling it (`none()`) should be a deliberate, narrowly justified choice, not an accidental default.
