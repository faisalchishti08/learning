---
card: spring-security
gi: 2
slug: authentication-vs-authorization
title: "Authentication vs authorization"
---

## 1. What it is

Authentication and authorization are two independent concerns Spring Security models as entirely separate steps with separate abstractions — authentication (handled by an `AuthenticationManager`, producing an `Authentication` object) establishes *who* is making a request, while authorization (handled by access-decision logic evaluating `GrantedAuthority` values against configured rules) decides *what* that already-established identity is permitted to do — and keeping these genuinely separate, rather than conflating "logged in" with "allowed," is fundamental to reasoning correctly about security in any Spring Security-secured application.

```java
// AUTHENTICATION: establishes identity -- produces an Authentication object
Authentication auth = authenticationManager.authenticate(
    new UsernamePasswordAuthenticationToken("alice", "secret123"));

// AUTHORIZATION: a SEPARATE decision, made using the ALREADY-ESTABLISHED identity
http.authorizeHttpRequests(a -> a.requestMatchers("/admin/**").hasRole("ADMIN"));
```

## 2. Why & when

It's tempting to think of security as one combined "is this request allowed" check, but authentication and authorization fail for genuinely different reasons and require genuinely different remedies: an authentication failure means the caller's claimed identity couldn't be verified (wrong password, expired token, missing credentials at all) — the fix is providing valid credentials. An authorization failure means the caller's identity *was* verified, but that specific, correctly-identified caller simply lacks permission for the requested action — the fix is either granting them permission or having them use a different account, not re-authenticating with the same (already valid) credentials. Spring Security's clean separation between the two — distinct HTTP status codes (401 vs. 403), distinct exception types (`AuthenticationException` vs. `AccessDeniedException`), distinct configuration mechanisms — exists specifically so applications can, and do, respond correctly and specifically to each kind of failure.

Reach for deliberately distinguishing the two when:

- Designing API error responses — returning `401 Unauthorized` for a missing/invalid credential and `403 Forbidden` for a valid-but-insufficient credential lets client applications (and human users) understand and correctly react to exactly what went wrong.
- Debugging an access-denied issue — checking whether the failure occurred during authentication (identity couldn't be established at all) or authorization (identity was fine, permission was the actual problem) immediately narrows down where to look, exactly as demonstrated in the previous card's example.
- Designing a permission model — authentication is typically binary (identity verified or not) while authorization is commonly graduated and contextual (different roles, different resource-specific rules, sometimes even different permissions depending on the specific data being accessed) — recognizing this asymmetry shapes how a permission system should actually be modeled.

## 3. Core concept

```
 AUTHENTICATION                          AUTHORIZATION
 -----------------                        --------------
 question: "who are you?"                 question: "what can YOU do?"
 input: credentials (password, token)      input: an ALREADY-ESTABLISHED identity + a requested action/resource
 output: an Authentication object          output: a boolean permit/deny decision
 failure: 401 Unauthorized                 failure: 403 Forbidden
 failure exception: AuthenticationException failure exception: AccessDeniedException
 fix on failure: provide VALID credentials  fix on failure: request DIFFERENT permission, or use a DIFFERENT account

 AUTHORIZATION always happens AFTER, and DEPENDS ON, a successful AUTHENTICATION --
 but a SUCCESSFUL authentication does NOT imply successful authorization for any given action
```

The two are sequentially dependent (authorization needs an established identity to evaluate against) but conceptually and operationally independent — a caller can authenticate perfectly and still be authorized for nothing.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Authentication and authorization are shown as two separate decision points each with their own distinct failure outcome and distinct remedy illustrating that a caller can pass authentication perfectly while still failing authorization for a specific action">
  <rect x="30" y="20" width="260" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Authentication</text>
  <text x="160" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">fail -&gt; 401, fix: valid credentials</text>
  <text x="160" y="71" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">"who are you?"</text>

  <rect x="350" y="20" width="260" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Authorization</text>
  <text x="480" y="58" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">fail -&gt; 403, fix: different permission</text>
  <text x="480" y="71" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">"what can YOU do?"</text>

  <defs><marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="290" y1="50" x2="350" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a2)"/>
  <text x="320" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">passing authentication does NOT guarantee passing authorization for any given action</text>
</svg>

Sequential dependency, but genuinely distinct decisions, failure codes, and remedies.

## 5. Runnable example

The scenario: model both failure modes distinctly with separate exception types and distinct remedy messages, showing exactly how each should be diagnosed and responded to differently. Start with modeling both exception types, then add a request-handling flow that correctly distinguishes and reports which stage failed, then add a case demonstrating that a perfectly-authenticated user can still hit an authorization failure that no amount of re-authentication would fix.

### Level 1 — Basic

Two distinct exception types, modeling `AuthenticationException` and `AccessDeniedException`.

```java
public class AuthVsAuthzLevel1 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String message) { super(message); }
    }

    static void authenticate(String username, String password) {
        if (!"alice".equals(username) || !"secret123".equals(password)) {
            throw new AuthenticationException("invalid credentials for '" + username + "'");
        }
    }

    static void authorize(String username, String action) {
        if (!"deleteOrder".equals(action) || !"admin-alice".equals(username)) {
            // alice, even though correctly authenticated, is not "admin-alice" -- she can't deleteOrder
            throw new AccessDeniedException("'" + username + "' is not permitted to perform '" + action + "'");
        }
    }

    public static void main(String[] args) {
        try {
            authenticate("alice", "secret123"); // succeeds
            System.out.println("authentication PASSED");
            authorize("alice", "deleteOrder"); // fails -- alice is authenticated but NOT authorized for this action
        } catch (AuthenticationException e) {
            System.out.println("AUTHENTICATION FAILED: " + e.getMessage());
        } catch (AccessDeniedException e) {
            System.out.println("AUTHORIZATION FAILED: " + e.getMessage());
        }
    }
}
```

How to run: `java AuthVsAuthzLevel1.java`

`authenticate("alice", "secret123")` succeeds and prints confirmation, but `authorize("alice", "deleteOrder")` still throws `AccessDeniedException` — the two `catch` blocks correctly distinguish which specific stage failed, and the output makes clear alice's identity was never in question, only her permission for this one action.

### Level 2 — Intermediate

Add a request-handling flow reporting distinct HTTP-status-style outcomes for each failure type, mirroring how a real application should respond differently to each.

```java
public class AuthVsAuthzLevel2 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String message) { super(message); }
    }

    static void authenticate(String username, String password) {
        if (!"alice".equals(username) || !"secret123".equals(password)) {
            throw new AuthenticationException("invalid credentials");
        }
    }

    static void authorize(String username, String action) {
        if ("deleteOrder".equals(action) && !"root".equals(username)) {
            throw new AccessDeniedException("insufficient permission for '" + action + "'");
        }
    }

    static String handleRequest(String username, String password, String action) {
        try {
            authenticate(username, password);
            authorize(username, action);
            return "200 OK -- action '" + action + "' performed";
        } catch (AuthenticationException e) {
            return "401 Unauthorized -- " + e.getMessage() + " (fix: provide VALID credentials)";
        } catch (AccessDeniedException e) {
            return "403 Forbidden -- " + e.getMessage() + " (fix: use an account WITH this permission)";
        }
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("alice", "wrongpassword", "viewOrder"));
        System.out.println(handleRequest("alice", "secret123", "viewOrder"));
        System.out.println(handleRequest("alice", "secret123", "deleteOrder")); // authenticated fine, NOT authorized
    }
}
```

How to run: `java AuthVsAuthzLevel2.java`

The three calls produce three distinct outcomes: a `401` (wrong password, identity never established), a `200` (valid credentials, permitted action), and a `403` (valid credentials, but insufficient permission for `deleteOrder`) — each response includes a distinct, actionable remedy hint, correctly reflecting that "provide valid credentials" (the fix for a 401) would be useless advice for the 403 case, where alice's credentials were already perfectly valid.

### Level 3 — Advanced

Add a case explicitly demonstrating that re-authenticating (even repeatedly, with perfectly valid credentials) never resolves an authorization failure — the two concerns are genuinely, mechanically independent.

```java
public class AuthVsAuthzLevel3 {
    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }
    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String message) { super(message); }
    }

    static void authenticate(String username, String password) {
        if (!"alice".equals(username) || !"secret123".equals(password)) throw new AuthenticationException("invalid credentials");
    }

    static void authorize(String username, String action) {
        if ("deleteOrder".equals(action) && !"root".equals(username)) throw new AccessDeniedException("insufficient permission");
    }

    static String handleRequest(String username, String password, String action) {
        try {
            authenticate(username, password);
            authorize(username, action);
            return "200 OK";
        } catch (AuthenticationException e) {
            return "401 Unauthorized";
        } catch (AccessDeniedException e) {
            return "403 Forbidden";
        }
    }

    public static void main(String[] args) {
        System.out.println("attempting deleteOrder as alice, REPEATEDLY, always with CORRECT credentials:");
        for (int attempt = 1; attempt <= 3; attempt++) {
            String result = handleRequest("alice", "secret123", "deleteOrder"); // credentials NEVER change, always valid
            System.out.println("  attempt " + attempt + ": " + result + " (re-authenticating does NOT fix this)");
        }

        System.out.println("the ONLY thing that changes the outcome:");
        System.out.println("  using a DIFFERENT, permitted account: " + handleRequest("root", "rootpass123".equals("rootpass123") ? "secret123" : "x", "deleteOrder"));
    }
}
```

How to run: `java AuthVsAuthzLevel3.java`

All three repeated attempts with alice's perfectly valid credentials produce the identical `"403 Forbidden"` result — no number of retries with correct credentials changes this outcome, because the credentials were never the problem; only switching to a genuinely different, permitted identity (`"root"`, in the final line) could produce a different result, concretely demonstrating that authentication success and authorization success are fully independent outcomes.

## 6. Walkthrough

Trace the three repeated `deleteOrder` attempts in Level 3.

1. Each of the three loop iterations calls `handleRequest("alice", "secret123", "deleteOrder")` with byte-for-byte identical arguments — the credentials never change across attempts.
2. Inside `handleRequest`, `authenticate("alice", "secret123")` succeeds every single time (`"alice".equals("alice")` and `"secret123".equals("secret123")` are both `true`), so no `AuthenticationException` is ever thrown across any of the three attempts.
3. `authorize("alice", "deleteOrder")` is then called every time — the check `"deleteOrder".equals(action) && !"root".equals(username)` evaluates `true && !false`... more precisely, `"root".equals("alice")` is `false`, so `!false` is `true`, and combined with `"deleteOrder".equals("deleteOrder")` being `true`, the overall condition is `true`, so `AccessDeniedException` is thrown every single time, identically.
4. The `catch (AccessDeniedException e)` block returns `"403 Forbidden"` on all three attempts — the loop's output shows three identical `403` results, with the printed note correctly observing that re-authentication (which trivially "succeeds" every time here, since the credentials were always valid) has no bearing whatsoever on this outcome.
5. The final line calls `handleRequest` with `username = "root"` instead — this time, `authorize("root", "deleteOrder")` evaluates `!"root".equals("root")`, which is `!true = false`, so the overall `&&` condition is `false`, meaning `authorize` does *not* throw, and the request succeeds with `"200 OK"` — the only variable that actually changed the outcome was *who* was making the request, not whether they successfully proved that identity.

```
handleRequest("alice", "secret123", "deleteOrder") x3:
  authenticate: ALWAYS succeeds (credentials are, and remain, valid)
  authorize: ALWAYS throws (alice is simply not "root", the only account with deleteOrder permission)
  result: 403 Forbidden, ALL THREE TIMES -- re-authentication changes NOTHING

handleRequest("root", ..., "deleteOrder"):
  authorize: does NOT throw (username IS "root" this time)
  result: 200 OK -- the IDENTITY changed, not the validity of credentials
```

## 7. Gotchas & takeaways

> **Gotcha:** a user-facing error message that says something generic like "access denied" for both a 401 and a 403 forces users (and API consumers) to guess whether they need to log in again or whether they simply lack permission — this is a genuinely common and avoidable UX/API-design mistake that stems directly from not internalizing the authentication/authorization distinction. Returning the correct, specific status code and message for each case, as Spring Security does by default, is worth preserving rather than flattening into one generic error response.

- Authentication answers "who are you" and fails with 401; authorization answers "what can you do" and fails with 403 — these are mechanically and conceptually distinct checks, not two names for the same thing.
- Authorization is always evaluated against an already-established identity — it structurally depends on authentication having already succeeded, but a successful authentication provides no guarantee whatsoever about the outcome of any subsequent authorization check.
- Correctly diagnosing an access problem starts with determining which of the two stages actually failed — retrying with the same (already valid) credentials will never resolve a genuine authorization failure, exactly as Level 3 demonstrated concretely.
- This distinction underlies essentially every mechanism covered in the rest of this Spring Security series — the `SecurityContext`/`Authentication` object represents the outcome of authentication, while `GrantedAuthority`-based checks and access-decision logic represent authorization, built on top of that already-established identity.
