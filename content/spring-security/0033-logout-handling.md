---
card: spring-security
gi: 33
slug: logout-handling
title: "Logout handling"
---

## 1. What it is

`LogoutFilter` handles logout as a coordinated sequence of independent `LogoutHandler` implementations (invalidate the `HttpSession`, clear the `SecurityContextHolder`, delete the remember-me cookie, delete the CSRF token cookie) followed by exactly one `LogoutSuccessHandler` that decides the final response (typically a redirect to a login page with a logged-out indicator). `http.logout(Customizer.withDefaults())` enables it with sensible defaults, matching `POST /logout` by default.

```java
http.logout(logout -> logout
        .logoutUrl("/logout")
        .logoutSuccessUrl("/login?logout")
        .invalidateHttpSession(true)
        .deleteCookies("JSESSIONID", "remember-me")
        .addLogoutHandler((request, response, auth) -> auditLog.record("logout", auth.getName())));
```

## 2. Why & when

A correct logout needs to undo *everything* a successful login and its subsequent session established — the server-side session, the `SecurityContext`, any remember-me cookie, any CSRF token tied to the now-ending session — and missing even one of these can leave a way for the "logged out" session to still be partially usable (a stale remember-me cookie silently re-authenticating the user on the very next request, for instance). `LogoutFilter`'s design, running an ordered list of independent `LogoutHandler`s, makes each of these cleanup concerns explicit and independently composable, so a custom cleanup step (writing an audit log entry, invalidating a server-side token in an external store) can be added alongside the built-in ones without needing to reimplement any of them.

Reach for customizing logout when:

- Remember-me is enabled — logout must delete the remember-me cookie too, or a user who logs out will find themselves silently re-authenticated by the leftover cookie on their very next request, exactly the scenario the earlier remember-me card's persistent-token theft detection was designed to guard against for a *different* case, but which a forgotten logout handler can reintroduce here.
- A custom action needs to run on logout — recording an audit event, invalidating a token in an external system (a distributed session store, a revoked-token list for stateless APIs) — via `addLogoutHandler`.
- Building a stateless API where there's no session to invalidate at all — logout instead typically means instructing the client to discard its token, and/or adding the token to a server-side revocation list if tokens aren't naturally short-lived enough to expire safely on their own.

## 3. Core concept

```
 POST /logout
        |
        v
 LogoutFilter runs an ORDERED list of LogoutHandlers, each independently cleaning up ONE concern:
   1. SecurityContextLogoutHandler   -- SecurityContextHolder.clearContext(), session.invalidate()
   2. CookieClearingLogoutHandler    -- deletes named cookies (JSESSIONID, remember-me, ...)
   3. (any custom LogoutHandler added via addLogoutHandler) -- e.g. an audit log entry
        |
        v
 exactly ONE LogoutSuccessHandler runs LAST, deciding the final response
   (typically: redirect to /login?logout)
```

Every handler in the list runs, in order, regardless of what the others did — logout cleanup is deliberately exhaustive, not short-circuited.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A POST to slash logout runs through an ordered chain of logout handlers clearing the security context invalidating the session and deleting cookies followed by a single logout success handler that produces the final redirect response">
  <rect x="15" y="70" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="93" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">POST /logout</text>

  <rect x="200" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="290" y="41" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">clear SecurityContext</text>

  <rect x="200" y="63" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="290" y="84" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">invalidate HttpSession</text>

  <rect x="200" y="106" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="290" y="127" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">delete cookies</text>

  <rect x="440" y="63" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="83" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">LogoutSuccessHandler</text>
  <text x="530" y="96" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">redirect to /login?logout</text>

  <defs><marker id="a33" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="85" x2="200" y2="37" stroke="#8b949e" stroke-width="1" marker-end="url(#a33)"/>
  <line x1="155" y1="90" x2="200" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a33)"/>
  <line x1="155" y1="95" x2="200" y2="123" stroke="#8b949e" stroke-width="1" marker-end="url(#a33)"/>
  <line x1="380" y1="86" x2="440" y2="86" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a33)"/>
</svg>

Every handler runs in sequence for every logout request, regardless of the others' outcomes.

## 5. Runnable example

The scenario: model the ordered logout-handler chain, demonstrate why forgetting the remember-me cookie handler leaves a silent re-authentication hole, then add a custom audit-logging handler alongside the built-in ones.

### Level 1 — Basic

A minimal logout chain: clear the security context and invalidate the session.

```java
import java.util.*;

public class LogoutLevel1 {
    static Map<String, String> activeSessions = new HashMap<>(Map.of("JSESSIONID-abc", "alice"));
    static String currentSecurityContext = "alice"; // models SecurityContextHolder's current Authentication

    interface LogoutHandler { void handle(String sessionId); }

    static LogoutHandler securityContextLogoutHandler = sessionId -> {
        currentSecurityContext = null;
        activeSessions.remove(sessionId);
        System.out.println("  cleared SecurityContext, invalidated session " + sessionId);
    };

    static void logout(String sessionId, List<LogoutHandler> handlers) {
        for (LogoutHandler handler : handlers) handler.handle(sessionId);
        System.out.println("logout complete -> redirecting to /login?logout");
    }

    public static void main(String[] args) {
        System.out.println("before logout: session active? " + activeSessions.containsKey("JSESSIONID-abc")
                + ", SecurityContext=" + currentSecurityContext);
        logout("JSESSIONID-abc", List.of(securityContextLogoutHandler));
        System.out.println("after logout: session active? " + activeSessions.containsKey("JSESSIONID-abc")
                + ", SecurityContext=" + currentSecurityContext);
    }
}
```

How to run: `java LogoutLevel1.java`

`logout` runs the single handler in its list, which clears both `currentSecurityContext` and the entry in `activeSessions` — after this call, the session is gone and no `Authentication` remains, matching a minimal, correctly cleaned-up logout.

### Level 2 — Intermediate

Add remember-me cookie handling and demonstrate the consequence of omitting it: a "logged out" user silently re-authenticated by the leftover cookie.

```java
import java.util.*;

public class LogoutLevel2 {
    static Map<String, String> activeSessions = new HashMap<>(Map.of("JSESSIONID-abc", "alice"));
    static String currentSecurityContext = "alice";
    static Set<String> browserCookies = new HashSet<>(Set.of("JSESSIONID-abc", "remember-me-token-xyz"));

    interface LogoutHandler { void handle(String sessionId); }

    static LogoutHandler securityContextLogoutHandler = sessionId -> {
        currentSecurityContext = null;
        activeSessions.remove(sessionId);
    };

    static void logout(String sessionId, List<LogoutHandler> handlers) {
        for (LogoutHandler handler : handlers) handler.handle(sessionId);
    }

    // models what happens on the NEXT request after logout, given whatever cookies remain
    static String nextRequestAfterLogout() {
        if (currentSecurityContext != null) return "already authenticated (should not happen right after logout)";
        if (browserCookies.contains("remember-me-token-xyz")) {
            currentSecurityContext = "alice"; // RememberMeAuthenticationFilter silently re-authenticates!
            return "SILENTLY RE-AUTHENTICATED as alice via leftover remember-me cookie";
        }
        return "302 Found -> /login (correctly logged out)";
    }

    public static void main(String[] args) {
        System.out.println("INCOMPLETE logout (forgot to delete remember-me cookie):");
        logout("JSESSIONID-abc", List.of(securityContextLogoutHandler)); // missing cookie-clearing handler!
        System.out.println("  " + nextRequestAfterLogout());
    }
}
```

How to run: `java LogoutLevel2.java`

Because `logout`'s handler list omits any cookie-clearing step, `browserCookies` still contains `"remember-me-token-xyz"` after logout; `nextRequestAfterLogout` then finds `currentSecurityContext` cleared (so the user does appear logged out momentarily) but the leftover remember-me cookie causes silent re-authentication on the very next request — precisely the security gap a complete logout configuration must close.

### Level 3 — Advanced

Add the cookie-clearing handler (fixing Level 2's gap) plus a custom audit-logging handler, running the complete, correctly-ordered chain.

```java
import java.util.*;

public class LogoutLevel3 {
    static Map<String, String> activeSessions = new HashMap<>(Map.of("JSESSIONID-abc", "alice"));
    static String currentSecurityContext = "alice";
    static Set<String> browserCookies = new HashSet<>(Set.of("JSESSIONID-abc", "remember-me-token-xyz"));
    static List<String> auditLog = new ArrayList<>();

    interface LogoutHandler { void handle(String sessionId, String username); }

    static LogoutHandler securityContextLogoutHandler = (sessionId, username) -> {
        currentSecurityContext = null;
        activeSessions.remove(sessionId);
    };

    static LogoutHandler cookieClearingLogoutHandler = (sessionId, username) -> {
        browserCookies.remove(sessionId);
        browserCookies.remove("remember-me-token-xyz");
    };

    static LogoutHandler auditLogoutHandler = (sessionId, username) ->
            auditLog.add("user '" + username + "' logged out (session " + sessionId + ")");

    static void logout(String sessionId, String username, List<LogoutHandler> handlers) {
        for (LogoutHandler handler : handlers) handler.handle(sessionId, username); // ALL run, in order
    }

    static String nextRequestAfterLogout() {
        if (currentSecurityContext != null) return "already authenticated";
        if (browserCookies.contains("remember-me-token-xyz")) return "SILENTLY RE-AUTHENTICATED (should not happen now)";
        return "302 Found -> /login?logout (correctly logged out, no leftover cookies)";
    }

    public static void main(String[] args) {
        List<LogoutHandler> completeChain = List.of(
                securityContextLogoutHandler, cookieClearingLogoutHandler, auditLogoutHandler
        );

        logout("JSESSIONID-abc", "alice", completeChain);

        System.out.println("remaining cookies: " + browserCookies);
        System.out.println("audit log: " + auditLog);
        System.out.println("next request: " + nextRequestAfterLogout());
    }
}
```

How to run: `java LogoutLevel3.java`

With all three handlers registered, `browserCookies` ends up empty, `auditLog` records the logout event, and `nextRequestAfterLogout` correctly reports a clean logout with no leftover remember-me cookie to silently re-authenticate the user — the complete, correctly-ordered chain closes exactly the gap Level 2 demonstrated.

## 6. Walkthrough

Trace `logout("JSESSIONID-abc", "alice", completeChain)` from Level 3.

1. The `for` loop begins iterating `completeChain` in order: `securityContextLogoutHandler.handle("JSESSIONID-abc", "alice")` runs first, setting `currentSecurityContext = null` and removing `"JSESSIONID-abc"` from `activeSessions`.
2. `cookieClearingLogoutHandler.handle(...)` runs next, calling `browserCookies.remove("JSESSIONID-abc")` and `browserCookies.remove("remember-me-token-xyz")` — both entries are deleted from the set, leaving it empty.
3. `auditLogoutHandler.handle(...)` runs last, appending `"user 'alice' logged out (session JSESSIONID-abc)"` to `auditLog` — this is the custom handler added alongside the two built-in-style ones, and it runs regardless of what the earlier handlers did, since nothing in the loop short-circuits.
4. After `logout` returns, `nextRequestAfterLogout()` is called: `currentSecurityContext` is `null`, so the first guard is skipped; `browserCookies.contains("remember-me-token-xyz")` is now `false` (removed in step 2), so the second guard is also skipped, and the method returns the correct "cleanly logged out" message.
5. Compare this with Level 2's trace: there, step 2 (cookie clearing) never happened at all, so `browserCookies` still held the remember-me token, and `nextRequestAfterLogout` took the silent-re-authentication branch instead — the *only* difference between the two runs is whether the cookie-clearing handler was present in the chain.

```
handler 1 (securityContext):  clears currentSecurityContext, removes session
handler 2 (cookieClearing):   removes JSESSIONID AND remember-me cookies
handler 3 (audit):            records the logout event
-> next request: no session, no remember-me cookie -> correctly redirected to /login?logout
```

## 7. Gotchas & takeaways

> **Gotcha:** enabling remember-me without also configuring `deleteCookies(...)` (or otherwise ensuring the remember-me cookie is cleared) on logout is a common, easy-to-miss security gap — the user appears logged out, but the leftover cookie silently re-authenticates them on their very next request, exactly as Level 2 demonstrated.

- `LogoutFilter` runs an ordered, exhaustive list of independent `LogoutHandler`s — every handler runs regardless of the others, ensuring every relevant piece of state (session, security context, cookies) is cleaned up.
- Custom cleanup logic (an audit log entry, invalidating a token in an external store) is added via `addLogoutHandler`, composing alongside the built-in handlers rather than replacing them.
- Any feature that leaves persistent client-side state (remember-me cookies most notably) must have a corresponding logout cleanup step, or that state can silently undo the logout on the very next request.
- Exactly one `LogoutSuccessHandler` runs at the end of the chain, deciding the final response — this is a distinct, separate concern from the (potentially many) `LogoutHandler`s that perform the actual cleanup work before it.
