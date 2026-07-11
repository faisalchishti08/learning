---
card: spring-security
gi: 9
slug: authentication-object-principal
title: "Authentication object & Principal"
---

## 1. What it is

`Authentication` is the interface representing one established (or in-progress) identity, holding three key pieces — a `principal` (the authenticated identity itself, commonly a `UserDetails` object or a username string), `credentials` (typically the password, usually cleared/nulled-out immediately after successful authentication for security), and `authorities` (the granted permissions, covered fully in the next card) — plus a boolean `isAuthenticated()` flag distinguishing a fully-verified `Authentication` from one still mid-process, and it's exactly this object that `SecurityContextHolder` stores and that controller methods receive when they declare an `Authentication` parameter.

```java
public interface Authentication extends Principal {
    Object getPrincipal();       // WHO -- typically a UserDetails object
    Object getCredentials();     // password, etc. -- usually NULLED after successful auth
    Collection<? extends GrantedAuthority> getAuthorities(); // WHAT they can do
    boolean isAuthenticated();
}
```

```java
@GetMapping("/me")
String whoAmI(Authentication authentication) {
    Object principal = authentication.getPrincipal();
    return "Hello, " + authentication.getName(); // getName() typically delegates to principal's username
}
```

## 2. Why & when

Authentication as a *process* (validating credentials, the topic of earlier cards) needs to produce some concrete *result* that the rest of the system can work with — a single, well-defined object representing "this is who we've determined the caller to be, and here's what we know about them." `Authentication` is that result object: a uniform representation regardless of *how* the caller was actually authenticated (username/password form login, an OAuth2 token, a client certificate) — application code working with an `Authentication` object doesn't need to know or care which specific authentication mechanism produced it, since the interface's shape (`principal`, `credentials`, `authorities`, `isAuthenticated()`) stays consistent across every mechanism.

Reach for working directly with the `Authentication` object when:

- Writing code that needs to work generically across multiple possible authentication mechanisms — a piece of auditing or logging code that just needs "who is this," regardless of whether they logged in via a form or an OAuth2 provider, can rely on the uniform `Authentication` interface rather than mechanism-specific types.
- Distinguishing a genuinely established identity from an in-progress or anonymous one — checking `authentication.isAuthenticated()` (and, in practice, checking it's not an `AnonymousAuthenticationToken`, since Spring Security represents "not logged in" as a specific, always-present anonymous `Authentication` rather than a `null`) is the correct way to determine whether a real, verified identity exists.
- Accessing custom application-specific user data attached during authentication — a `principal` object is commonly cast to a custom `UserDetails` implementation (or an entirely custom principal type) carrying application-specific fields (a user ID, a tenant ID) beyond just a username.

## 3. Core concept

```
 Authentication (the interface, uniform regardless of HOW authentication happened):
   principal    -- WHO: typically a UserDetails object (or just a username String, pre-authentication)
   credentials  -- the SECRET used to prove identity (password) -- typically NULLED after success
   authorities  -- WHAT they can do (a set of GrantedAuthority values -- next card)
   isAuthenticated() -- has this identity actually been VERIFIED, or is it still just a claim?

 BEFORE authentication succeeds:
   Authentication(principal="alice", credentials="secret123", authorities=[], isAuthenticated=false)
        |
        v  AuthenticationProvider verifies credentials
 AFTER authentication succeeds:
   Authentication(principal=UserDetails{alice}, credentials=null, authorities=[ROLE_USER], isAuthenticated=true)
```

The same `Authentication` interface represents both an unverified claim (submitted credentials, not yet checked) and a fully verified result — `isAuthenticated()` and whether `credentials` has been cleared are what distinguish the two states.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unauthenticated token carrying a username and password is transformed by an authentication provider into a fully authenticated Authentication object carrying a UserDetails principal cleared credentials and a set of granted authorities">
  <rect x="20" y="20" width="270" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">BEFORE: principal="alice"</text>
  <text x="155" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">credentials="secret123"</text>
  <text x="155" y="68" fill="#f85149" font-size="7.5" text-anchor="middle" font-family="sans-serif">isAuthenticated=false</text>

  <rect x="350" y="20" width="270" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">AFTER: principal=UserDetails</text>
  <text x="485" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">credentials=null (cleared)</text>
  <text x="485" y="68" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">isAuthenticated=true</text>

  <defs><marker id="a9" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="290" y1="50" x2="350" y2="50" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a9)"/>
  <text x="320" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationProvider verifies credentials, transforms one into the other</text>
</svg>

Two states of the same interface — an unverified claim on the left, a verified result on the right.

## 5. Runnable example

The scenario: model both states of an `Authentication`-shaped object — before and after verification — and demonstrate how application code correctly distinguishes them, plus a custom principal carrying application-specific fields beyond just a username. Start with the two-state model, then add checking `isAuthenticated()` correctly, then add a custom principal type with extra fields accessed by application code.

### Level 1 — Basic

The two-state `Authentication` model: an unverified claim, transformed into a verified result.

```java
import java.util.*;

public class AuthenticationObjectLevel1 {
    static class Authentication {
        Object principal;
        String credentials;
        boolean authenticated;
        Authentication(Object principal, String credentials, boolean authenticated) {
            this.principal = principal; this.credentials = credentials; this.authenticated = authenticated;
        }
    }

    public static void main(String[] args) {
        // BEFORE verification -- an unverified claim
        Authentication before = new Authentication("alice", "secret123", false);
        System.out.println("before: principal=" + before.principal + " authenticated=" + before.authenticated);

        // AFTER an AuthenticationProvider verifies the credentials
        Authentication after = new Authentication("alice", null, true); // credentials CLEARED
        System.out.println("after: principal=" + after.principal + " credentials=" + after.credentials + " authenticated=" + after.authenticated);
    }
}
```

How to run: `java AuthenticationObjectLevel1.java`

`before` and `after` model the two distinct states of an `Authentication` object — critically, `after.credentials` is `null`, mirroring how Spring Security clears the raw password from a successfully-authenticated `Authentication` object, so it's never held in memory longer than necessary.

### Level 2 — Intermediate

Add correctly checking `isAuthenticated()` before trusting an `Authentication` object represents a genuinely verified identity.

```java
import java.util.*;

public class AuthenticationObjectLevel2 {
    static class Authentication {
        Object principal;
        boolean authenticated;
        Authentication(Object principal, boolean authenticated) { this.principal = principal; this.authenticated = authenticated; }
    }

    static String handleRequest(Authentication auth) {
        if (auth == null || !auth.authenticated) {
            return "401 Unauthorized -- no VERIFIED identity present"; // correctly checks isAuthenticated, not just null
        }
        return "200 OK -- serving request for " + auth.principal;
    }

    public static void main(String[] args) {
        Authentication verified = new Authentication("alice", true);
        Authentication unverified = new Authentication("alice", false); // principal CLAIMED, but NOT yet verified

        System.out.println(handleRequest(verified));
        System.out.println(handleRequest(unverified)); // correctly rejected, despite having a non-null principal
    }
}
```

How to run: `java AuthenticationObjectLevel2.java`

`handleRequest(unverified)` correctly returns `401`, even though `unverified.principal` is non-null (it's `"alice"`) — checking `auth.authenticated` specifically, rather than merely `auth != null` or `auth.principal != null`, is what correctly distinguishes a genuinely verified identity from a mere unverified claim, exactly the check application code (and Spring Security's own internal logic) must perform.

### Level 3 — Advanced

Add a custom principal type carrying application-specific fields (a user ID, a tenant ID) beyond just a username, demonstrating how real applications commonly extend the plain-username-principal model.

```java
import java.util.*;

public class AuthenticationObjectLevel3 {
    // a CUSTOM principal type -- richer than just a username, carries application-specific data
    record CustomUserPrincipal(String username, int userId, String tenantId) {}

    static class Authentication {
        Object principal;
        boolean authenticated;
        Authentication(Object principal, boolean authenticated) { this.principal = principal; this.authenticated = authenticated; }
        String getName() {
            // mirrors how a real Authentication.getName() commonly delegates to the principal's own username field
            if (principal instanceof CustomUserPrincipal p) return p.username();
            return principal.toString();
        }
    }

    static String handleRequest(Authentication auth) {
        if (auth == null || !auth.authenticated) return "401 Unauthorized";

        // application code accesses the RICHER principal type for data beyond just the username
        if (auth.principal instanceof CustomUserPrincipal p) {
            return "200 OK -- serving tenant '" + p.tenantId() + "', user #" + p.userId() + " (" + p.username() + ")";
        }
        return "200 OK -- serving " + auth.getName(); // fallback for a plain, non-custom principal
    }

    public static void main(String[] args) {
        Authentication customPrincipalAuth = new Authentication(
                new CustomUserPrincipal("alice", 42, "acme-corp"), true);
        Authentication plainPrincipalAuth = new Authentication("bob", true); // just a plain String principal

        System.out.println(handleRequest(customPrincipalAuth));
        System.out.println(handleRequest(plainPrincipalAuth));
        System.out.println("getName() for custom principal: " + customPrincipalAuth.getName());
    }
}
```

How to run: `java AuthenticationObjectLevel3.java`

`handleRequest(customPrincipalAuth)` successfully pattern-matches `auth.principal` as a `CustomUserPrincipal`, extracting `tenantId` and `userId` — application-specific fields entirely unavailable on a plain-username principal — while `handleRequest(plainPrincipalAuth)` falls back to the simpler `getName()`-based path, since `bob`'s principal is just a `String`; `customPrincipalAuth.getName()` still correctly returns `"alice"` via the `instanceof` check inside `getName()`, demonstrating that even a richly-typed custom principal still needs to support the basic `getName()`/username access pattern the rest of Spring Security (and application code expecting a simple username) relies on.

## 6. Walkthrough

Trace `handleRequest(customPrincipalAuth)` in Level 3.

1. `handleRequest` first checks `auth == null || !auth.authenticated` — `customPrincipalAuth.authenticated` is `true`, so `!true` is `false`, and combined with `auth == null` being `false`, the whole condition is `false` — the unauthenticated-rejection branch is skipped.
2. `auth.principal instanceof CustomUserPrincipal p` is evaluated — `auth.principal` is genuinely a `CustomUserPrincipal` instance (constructed with `"alice"`, `42`, `"acme-corp"`), so this pattern match succeeds, binding the local variable `p` to that same `CustomUserPrincipal` object.
3. Because the pattern match succeeded, the method returns a string built from `p.tenantId()` (`"acme-corp"`) and `p.userId()` (`42`) and `p.username()` (`"alice"`) — accessing exactly these application-specific fields is only possible because the principal was constructed as the richer `CustomUserPrincipal` type rather than a plain `String`.
4. Compare this to `handleRequest(plainPrincipalAuth)` — there, `auth.principal instanceof CustomUserPrincipal p` evaluates `false` (`plainPrincipalAuth.principal` is just the `String` `"bob"`, not a `CustomUserPrincipal`), so the method falls through to the `return "200 OK -- serving " + auth.getName();` fallback line, which calls `getName()`, itself checking `principal instanceof CustomUserPrincipal p` (again `false` here) and falling back to `principal.toString()`, which for a `String` is simply `"bob"` itself.
5. This demonstrates the practical value of a custom principal type: application code that specifically needs richer identity data (a tenant ID, a numeric user ID) can reliably access it once it knows to expect a specific custom principal type, while code that only needs the basic username can still work correctly and uniformly across both plain and custom principal types via the shared `getName()`-style access pattern.

```
handleRequest(customPrincipalAuth):
  authenticated=true -> proceed
  principal instanceof CustomUserPrincipal? YES -> extract tenantId, userId, username directly
  -> "200 OK -- serving tenant 'acme-corp', user #42 (alice)"

handleRequest(plainPrincipalAuth):
  authenticated=true -> proceed
  principal instanceof CustomUserPrincipal? NO (it's just a String "bob")
  -> falls back to getName() -> "bob"
  -> "200 OK -- serving bob"
```

## 7. Gotchas & takeaways

> **Gotcha:** casting `Authentication.getPrincipal()` to a specific expected type without first checking (via `instanceof` or a similar guard) risks a `ClassCastException` at runtime if that particular request happened to be authenticated by a different mechanism than expected — an anonymous request's principal, for instance, is commonly the literal string `"anonymousUser"`, not a `UserDetails` or custom principal object at all, and code that blindly casts without checking will fail unpredictably for exactly the requests that are least "normal" (anonymous access, a differently-configured authentication mechanism).

- `Authentication` provides a uniform representation of an identity — established or in-progress — regardless of which specific authentication mechanism produced it, letting generic application code (auditing, logging) work consistently across different auth schemes.
- `isAuthenticated()` (combined, in practice, with checking the concrete type isn't an anonymous token) is the correct way to distinguish a genuinely verified identity from a mere unverified claim or an anonymous stand-in — checking only for a non-null principal is insufficient and can be actively misleading.
- Credentials are typically cleared (nulled) from the `Authentication` object immediately after successful verification, minimizing how long sensitive raw credential material is held in memory — application code should never rely on `getCredentials()` still being populated after authentication has succeeded.
- Custom principal types (extending beyond a plain username) are a common and useful pattern for carrying application-specific identity data, but code accessing them should guard with `instanceof` rather than assuming every `Authentication`'s principal is always the expected custom type.
