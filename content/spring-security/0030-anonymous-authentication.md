---
card: spring-security
gi: 30
slug: anonymous-authentication
title: "Anonymous authentication"
---

## 1. What it is

Anonymous authentication is Spring Security's default behavior of populating `SecurityContextHolder` with a special `AnonymousAuthenticationToken` — carrying a configurable principal (`"anonymousUser"` by default) and a configurable authority (`ROLE_ANONYMOUS` by default) — for any request where no *real* authentication was established, rather than leaving `SecurityContextHolder` empty (`null`). `AnonymousAuthenticationFilter` is the filter that does this, positioned late in the chain, right before `AuthorizationFilter`.

```java
// what a genuinely unauthenticated request's SecurityContext actually looks like by DEFAULT:
Authentication auth = SecurityContextHolder.getContext().getAuthentication();
// auth is NEVER null here -- it's an AnonymousAuthenticationToken:
//   auth.getPrincipal()   -> "anonymousUser"
//   auth.getAuthorities() -> [ROLE_ANONYMOUS]
//   auth.isAuthenticated() -> true (!)
```

## 2. Why & when

Without anonymous authentication, code checking "is there a currently authenticated user" would need two different code paths — one for `SecurityContextHolder.getContext().getAuthentication() == null`, and a separate one for "an `Authentication` exists but represents a real, verified identity" — and every authorization expression would need explicit null-checks sprinkled throughout. Anonymous authentication sidesteps this entirely: `Authentication` is *never* `null` in a request that has passed through the standard filter chain, so authorization rules can uniformly express "requires a real login" as `hasRole('USER')` (which `ROLE_ANONYMOUS` never satisfies) and "accessible even to anonymous visitors" as `permitAll()` or an explicit `hasRole('ANONYMOUS')` check, without ever needing a separate `isAuthenticated() == false` branch.

Reach for understanding anonymous authentication when:

- Writing an authorization expression that should distinguish "logged in" from "not logged in" — `authenticated()` in `authorizeHttpRequests`, or `isAuthenticated()` in a `@PreAuthorize` SpEL expression, is specifically designed to evaluate `false` for an `AnonymousAuthenticationToken`, even though `Authentication.isAuthenticated()` itself confusingly returns `true` for it.
- Debugging `SecurityContextHolder.getContext().getAuthentication()` unexpectedly not being `null` on what should be an unauthenticated request — this is expected: it's the anonymous token, not a null reference.
- Building any feature that should behave slightly differently for logged-in versus anonymous visitors (a personalized greeting versus a generic one) — checking `authentication.getPrincipal() instanceof String && authentication.getPrincipal().equals("anonymousUser")`, or more idiomatically, checking for the `ROLE_ANONYMOUS` authority, is how to detect this case.

## 3. Core concept

```
 AnonymousAuthenticationFilter.doFilter(request):
   IF SecurityContextHolder ALREADY has a real Authentication (set by an earlier auth filter)
        -> do nothing, pass through unchanged
   ELSE (nothing else established ANY authentication for this request)
        -> SecurityContextHolder.getContext().setAuthentication(
               new AnonymousAuthenticationToken(key, "anonymousUser", [ROLE_ANONYMOUS]))

 CONSEQUENCE: authentication.isAuthenticated() is confusingly TRUE for anonymous tokens too --
   authorizeHttpRequests()'s .authenticated() rule, and SpEL's isAuthenticated(), are DELIBERATELY
   implemented to treat AnonymousAuthenticationToken as "NOT really authenticated" despite this
```

Every request downstream of this filter has *some* `Authentication` object — the meaningful distinction becomes "is it the anonymous one" rather than "is it null."

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AnonymousAuthenticationFilter checks whether SecurityContextHolder already holds a real Authentication if not it installs an AnonymousAuthenticationToken with principal anonymousUser and ROLE_ANONYMOUS ensuring every downstream filter and controller always sees a non null Authentication object">
  <rect x="15" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="90" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">request with NO</text>
  <text x="90" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">real Authentication</text>

  <rect x="220" y="70" width="200" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="320" y="90" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AnonymousAuthenticationFilter</text>
  <text x="320" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">installs a stand-in token</text>

  <rect x="475" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="90" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">anonymousUser</text>
  <text x="550" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ROLE_ANONYMOUS</text>

  <defs><marker id="a30" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="93" x2="220" y2="93" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a30)"/>
  <line x1="420" y1="93" x2="475" y2="93" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a30)"/>
</svg>

A stand-in identity, not a null reference — every request has *something* in `SecurityContextHolder` by the time it reaches `AuthorizationFilter`.

## 5. Runnable example

The scenario: model the anonymous-token installation and its effect on authorization checks, showing exactly why `authenticated()`-style checks must specifically exclude it. Start with the filter's basic install-if-absent logic, then add the `authenticated()`-vs-raw-`isAuthenticated()` distinction, then add a feature that behaves differently for anonymous versus real users.

### Level 1 — Basic

The core install-if-absent logic: only set an anonymous token if nothing else already populated the context.

```java
import java.util.*;

public class AnonymousAuthLevel1 {
    record Authentication(String principal, Set<String> authorities, boolean isAuthenticated) {}

    static Authentication anonymousAuthenticationFilter(Authentication existing) {
        if (existing != null) return existing; // a REAL auth filter already ran successfully -- leave it alone
        return new Authentication("anonymousUser", Set.of("ROLE_ANONYMOUS"), true); // isAuthenticated() IS true here
    }

    public static void main(String[] args) {
        Authentication realUser = new Authentication("alice", Set.of("ROLE_USER"), true);

        System.out.println("request WITH prior login: " + anonymousAuthenticationFilter(realUser));
        System.out.println("request with NO prior login: " + anonymousAuthenticationFilter(null));
    }
}
```

How to run: `java AnonymousAuthLevel1.java`

When `existing` is already populated (alice's real login), the filter leaves it untouched; when `existing` is `null`, the filter installs the anonymous stand-in token — note that even the anonymous token's `isAuthenticated` field is `true`, which is precisely the confusing detail the next level addresses.

### Level 2 — Intermediate

Add the `authenticated()`-style check that correctly distinguishes "really logged in" from "anonymous," despite `isAuthenticated` being `true` for both.

```java
import java.util.*;

public class AnonymousAuthLevel2 {
    record Authentication(String principal, Set<String> authorities, boolean isAuthenticated) {}

    static Authentication anonymousAuthenticationFilter(Authentication existing) {
        if (existing != null) return existing;
        return new Authentication("anonymousUser", Set.of("ROLE_ANONYMOUS"), true);
    }

    // models authorizeHttpRequests()'s .authenticated() rule -- NOT the same as raw isAuthenticated()
    static boolean isReallyAuthenticated(Authentication auth) {
        return auth.isAuthenticated() && !auth.authorities().contains("ROLE_ANONYMOUS");
    }

    public static void main(String[] args) {
        Authentication realUser = new Authentication("alice", Set.of("ROLE_USER"), true);
        Authentication anonymous = anonymousAuthenticationFilter(null);

        System.out.println("alice: isAuthenticated()=" + realUser.isAuthenticated()
                + ", but really authenticated (per authorizeHttpRequests)? " + isReallyAuthenticated(realUser));
        System.out.println("anonymous: isAuthenticated()=" + anonymous.isAuthenticated()
                + ", but really authenticated (per authorizeHttpRequests)? " + isReallyAuthenticated(anonymous));
    }
}
```

How to run: `java AnonymousAuthLevel2.java`

Both `realUser` and `anonymous` report `isAuthenticated() == true` at the raw field level, but `isReallyAuthenticated` — which additionally excludes anything carrying `ROLE_ANONYMOUS` — correctly returns `true` only for alice and `false` for the anonymous token, exactly matching how `.anyRequest().authenticated()` behaves in a real `SecurityFilterChain`.

### Level 3 — Advanced

Build a feature (a personalized greeting) that behaves correctly for both real and anonymous users, using the anonymous token's principal as the signal, and confirm an authorization rule correctly rejects the anonymous case for a protected action.

```java
import java.util.*;

public class AnonymousAuthLevel3 {
    record Authentication(String principal, Set<String> authorities, boolean isAuthenticated) {}

    static Authentication anonymousAuthenticationFilter(Authentication existing) {
        if (existing != null) return existing;
        return new Authentication("anonymousUser", Set.of("ROLE_ANONYMOUS"), true);
    }

    static boolean isReallyAuthenticated(Authentication auth) {
        return auth.isAuthenticated() && !auth.authorities().contains("ROLE_ANONYMOUS");
    }

    static String greeting(Authentication auth) {
        return isReallyAuthenticated(auth) ? "Welcome back, " + auth.principal() + "!" : "Welcome, guest!";
    }

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }

    // models .authorizeHttpRequests(auth -> auth.requestMatchers("/checkout").authenticated())
    static String checkout(Authentication auth) {
        if (!isReallyAuthenticated(auth)) throw new AccessDeniedException("checkout requires a real login, not anonymous access");
        return "processing checkout for " + auth.principal();
    }

    public static void main(String[] args) {
        Authentication anonymousVisitor = anonymousAuthenticationFilter(null);
        Authentication loggedInUser = anonymousAuthenticationFilter(new Authentication("bob", Set.of("ROLE_USER"), true));

        System.out.println(greeting(anonymousVisitor));
        System.out.println(greeting(loggedInUser));

        System.out.println(checkout(loggedInUser));
        try {
            checkout(anonymousVisitor);
        } catch (AccessDeniedException ex) {
            System.out.println("checkout denied: " + ex.getMessage());
        }
    }
}
```

How to run: `java AnonymousAuthLevel3.java`

`greeting` reads naturally for both cases (a personalized message for bob, a generic one for the anonymous visitor), while `checkout` — a genuinely protected action — correctly throws for the anonymous visitor using the same `isReallyAuthenticated` check, demonstrating both a "works for anyone, personalized when possible" feature and a "requires real authentication" gate built from the identical underlying distinction.

## 6. Walkthrough

Trace `checkout(anonymousVisitor)` from Level 3.

1. `anonymousVisitor` was produced by `anonymousAuthenticationFilter(null)`, so its fields are `principal = "anonymousUser"`, `authorities = {ROLE_ANONYMOUS}`, `isAuthenticated = true`.
2. `checkout(anonymousVisitor)` calls `isReallyAuthenticated(anonymousVisitor)` first: `auth.isAuthenticated()` is `true`, so the first half of the `&&` passes, but `!auth.authorities().contains("ROLE_ANONYMOUS")` evaluates `!true`, which is `false` — the overall expression is `true && false`, i.e. `false`.
3. Because `isReallyAuthenticated` returned `false`, `checkout`'s `if (!isReallyAuthenticated(auth))` condition is `true`, so it throws `AccessDeniedException("checkout requires a real login, not anonymous access")` immediately, before doing any actual checkout processing.
4. Back in `main`, the surrounding try/catch catches this exception and prints the denial message — matching exactly how a real `@PreAuthorize("isAuthenticated()")`-annotated method, or a `.authenticated()` URL rule, would reject an anonymous request reaching a protected checkout endpoint: with an `AccessDeniedException`, routed by `ExceptionTranslationFilter` (from earlier in this section) to whatever `AccessDeniedHandler` is configured.
5. Contrast this with `checkout(loggedInUser)`, called just before: `loggedInUser.authorities()` is `{ROLE_USER}`, which does not contain `"ROLE_ANONYMOUS"`, so `isReallyAuthenticated` returns `true`, the `if` condition is `false`, and the method proceeds to its normal return value, `"processing checkout for bob"`.

```
checkout(loggedInUser=bob, ROLE_USER)        -> isReallyAuthenticated=true  -> proceeds -> "processing checkout for bob"
checkout(anonymousVisitor, ROLE_ANONYMOUS)   -> isReallyAuthenticated=false -> AccessDeniedException thrown
```

## 7. Gotchas & takeaways

> **Gotcha:** calling `authentication.isAuthenticated()` directly (rather than using `authorizeHttpRequests`'s `.authenticated()` rule or SpEL's `isAuthenticated()`) to check "is this a real, logged-in user" is a common and subtle bug — the raw field is `true` for the anonymous token too, so this check would incorrectly treat every anonymous visitor as authenticated.

- Anonymous authentication ensures `SecurityContextHolder.getContext().getAuthentication()` is never `null` for a request that has passed through the standard filter chain, replacing a two-case (`null`-or-real) check with a uniform, always-non-null one.
- The anonymous token's own `isAuthenticated()` field is confusingly `true` — the actually meaningful distinction is checking for the `ROLE_ANONYMOUS` authority (or equivalently, using `authorizeHttpRequests`'s `.authenticated()` rule or SpEL's `isAuthenticated()`, both of which correctly account for this).
- Anonymous authentication's default principal name (`"anonymousUser"`) and authority (`ROLE_ANONYMOUS`) are both configurable, but changing them requires updating any code that checks for these specific default values elsewhere.
- `AnonymousAuthenticationFilter` only installs its stand-in token when nothing else already populated `SecurityContextHolder` for the request — a successful earlier authentication (session-based, Basic, remember-me) always takes precedence and is left untouched.
