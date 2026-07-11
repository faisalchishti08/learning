---
card: spring-security
gi: 1
slug: what-spring-security-is-its-goals
title: "What Spring Security is & its goals"
---

## 1. What it is

Spring Security is the Spring ecosystem's framework for authentication (confirming who a caller is) and authorization (deciding what that caller is allowed to do), providing a consistent set of abstractions — filters, an `AuthenticationManager`, a `SecurityContext` — that plug into a Spring application's request-handling pipeline to intercept every incoming request, establish or validate an identity, and enforce access rules, before that request ever reaches application-level code like a `@RestController` method.

```java
@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .requestMatchers("/public/**").permitAll()
            .anyRequest().authenticated());
    return http.build();
}
```

```java
@GetMapping("/orders/{id}")
Order getOrder(@PathVariable String id) {
    // this method runs ONLY if Spring Security's filters already confirmed the caller is authenticated & authorized
    return orderService.find(id);
}
```

## 2. Why & when

Every non-trivial application needs to answer two related but distinct questions for every incoming request: "who is making this request" and "is this specific caller allowed to do this specific thing." Handling both correctly and consistently — validating credentials, checking permissions, protecting against common attack vectors (CSRF, session fixation, and others) — is substantial, security-critical work that's easy to get subtly wrong if reimplemented from scratch in every application, or inconsistently across different parts of the same application. Spring Security exists to centralize this: a small, declarative configuration (as shown above) establishes consistent rules enforced uniformly across an entire application, backed by a framework that has already solved the hard, easy-to-get-wrong parts of authentication and authorization correctly, letting application code focus on business logic while trusting that requests reaching it have already been properly vetted.

Reach for Spring Security when:

- Building any Spring Boot application that needs to restrict access — even a simple "only logged-in users can see this page" requirement benefits from Spring Security's tested, consistent enforcement rather than ad hoc, hand-rolled checks scattered through controller methods.
- The application needs to support more than the simplest possible authentication scheme — form login, OAuth2/OIDC, JWT-based stateless authentication, and multi-factor authentication are all supported through the same underlying framework, rather than requiring entirely separate tooling per scheme.
- Consistent, centrally-configured protection against common web vulnerabilities (CSRF, session fixation, clickjacking) matters — Spring Security provides sensible, battle-tested defaults for these concerns out of the box, rather than requiring every application team to independently research and implement each protection correctly.

## 3. Core concept

```
 incoming HTTP request
        |
        v
 Spring Security's filter chain intercepts it FIRST, before any @RestController method runs
        |
        v
 AUTHENTICATION: who is this?  (validate credentials, extract identity)
        |
        v
 AUTHORIZATION: is this identity allowed to do THIS specific thing?
        |
        v
 if BOTH pass -> request proceeds to the actual @RestController method
 if EITHER fails -> request is rejected (401 Unauthorized / 403 Forbidden), the controller method NEVER runs
```

The two questions are answered in strict order, and both must be satisfied before application code ever executes — this ordering (authentication before authorization, both before business logic) is foundational to how every later card in this series builds on Spring Security's model.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming request passes through authentication then authorization checks performed by Spring Security before reaching the controller method with a rejected request never reaching application code at all">
  <rect x="20" y="60" width="120" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">HTTP request</text>

  <rect x="190" y="60" width="130" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="255" y="82" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Authentication</text>
  <text x="255" y="96" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">who is this?</text>

  <rect x="360" y="60" width="130" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="425" y="82" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Authorization</text>
  <text x="425" y="96" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">allowed to do this?</text>

  <rect x="530" y="60" width="90" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="575" y="88" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">controller</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="140" y1="83" x2="190" y2="83" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="320" y1="83" x2="360" y2="83" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <line x1="490" y1="83" x2="530" y2="83" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>
  <text x="425" y="140" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">a rejection at EITHER stage stops the request here -- the controller method NEVER runs</text>
</svg>

Two sequential gates, both must pass, before the request reaches any application-level business logic at all.

## 5. Runnable example

The scenario: model the two-stage authentication-then-authorization pipeline directly, applied to a small set of requests with different credentials and different target resources — proving both gates must independently pass, and that a controller method genuinely never runs when either gate rejects the request. Start with authentication alone, then add authorization on top, then add role-based authorization distinguishing which authenticated users can access which resources.

### Level 1 — Basic

Authentication alone: confirming a request carries valid credentials before doing anything else.

```java
import java.util.*;

public class SpringSecurityIntroLevel1 {
    record Request(String username, String password) {}

    static Map<String, String> validCredentials = Map.of("alice", "secret123", "bob", "hunter2");

    static boolean authenticate(Request request) {
        String storedPassword = validCredentials.get(request.username());
        return storedPassword != null && storedPassword.equals(request.password());
    }

    public static void main(String[] args) {
        Request validRequest = new Request("alice", "secret123");
        Request invalidRequest = new Request("alice", "wrongpassword");

        System.out.println("valid credentials authenticate? " + authenticate(validRequest));
        System.out.println("invalid credentials authenticate? " + authenticate(invalidRequest));
    }
}
```

How to run: `java SpringSecurityIntroLevel1.java`

`authenticate` answers only the first question — "is this really alice" — with no consideration yet of what alice (once confirmed) is actually allowed to do; this mirrors Spring Security's own authentication stage in isolation, before any authorization logic is layered on top.

### Level 2 — Intermediate

Add authorization on top: even a successfully authenticated request must separately pass a permission check before reaching the "controller."

```java
import java.util.*;

public class SpringSecurityIntroLevel2 {
    record Request(String username, String password, String targetResource) {}

    static Map<String, String> validCredentials = Map.of("alice", "secret123", "bob", "hunter2");
    static Set<String> adminOnlyResources = Set.of("/admin/dashboard");
    static Set<String> admins = Set.of("alice"); // only alice is an admin

    static boolean authenticate(Request request) {
        String storedPassword = validCredentials.get(request.username());
        return storedPassword != null && storedPassword.equals(request.password());
    }

    static boolean authorize(Request request) {
        if (adminOnlyResources.contains(request.targetResource())) {
            return admins.contains(request.username()); // only an admin may access an admin-only resource
        }
        return true; // non-admin resources are open to any authenticated user
    }

    static String handleRequest(Request request) {
        if (!authenticate(request)) return "401 Unauthorized";
        if (!authorize(request)) return "403 Forbidden";
        return "200 OK -- controller method runs, serving: " + request.targetResource();
    }

    public static void main(String[] args) {
        System.out.println(handleRequest(new Request("alice", "secret123", "/admin/dashboard")));
        System.out.println(handleRequest(new Request("bob", "hunter2", "/admin/dashboard"))); // authenticated, NOT authorized
        System.out.println(handleRequest(new Request("bob", "wrongpassword", "/admin/dashboard"))); // not even authenticated
    }
}
```

How to run: `java SpringSecurityIntroLevel2.java`

Bob's second request fails authentication outright (`401`, never even reaches the authorization check); Bob's first request passes authentication but fails authorization (`403`, since he's not in `admins`) — two structurally different rejections, both correctly preventing the simulated "controller method" from ever running, exactly mirroring Spring Security's own two-gate model.

### Level 3 — Advanced

Add role-based authorization with multiple roles and resources, plus explicit logging showing exactly which gate a request passed or failed at — making the two-stage pipeline's decision process fully traceable.

```java
import java.util.*;

public class SpringSecurityIntroLevel3 {
    record Request(String username, String password, String targetResource) {}
    record User(String password, Set<String> roles) {}

    static Map<String, User> users = Map.of(
            "alice", new User("secret123", Set.of("ADMIN", "USER")),
            "bob", new User("hunter2", Set.of("USER")),
            "carol", new User("pass789", Set.of("AUDITOR"))
    );

    static Map<String, Set<String>> requiredRolesByResource = Map.of(
            "/admin/dashboard", Set.of("ADMIN"),
            "/audit/logs", Set.of("ADMIN", "AUDITOR"), // EITHER role suffices
            "/orders", Set.of("USER", "ADMIN")
    );

    static User authenticate(Request request) {
        User user = users.get(request.username());
        if (user == null || !user.password().equals(request.password())) return null;
        return user;
    }

    static boolean authorize(User user, String resource) {
        Set<String> required = requiredRolesByResource.getOrDefault(resource, Set.of());
        return required.isEmpty() || !Collections.disjoint(user.roles(), required); // at least ONE overlapping role
    }

    static String handleRequest(Request request) {
        User user = authenticate(request);
        if (user == null) {
            System.out.println("  [AUTHENTICATION] FAILED for '" + request.username() + "'");
            return "401 Unauthorized";
        }
        System.out.println("  [AUTHENTICATION] OK: '" + request.username() + "' has roles " + user.roles());

        if (!authorize(user, request.targetResource())) {
            System.out.println("  [AUTHORIZATION] FAILED: roles " + user.roles() + " insufficient for " + request.targetResource());
            return "403 Forbidden";
        }
        System.out.println("  [AUTHORIZATION] OK for " + request.targetResource());
        return "200 OK";
    }

    public static void main(String[] args) {
        System.out.println("-- carol requests /audit/logs --");
        System.out.println("result: " + handleRequest(new Request("carol", "pass789", "/audit/logs")));

        System.out.println("-- carol requests /admin/dashboard --");
        System.out.println("result: " + handleRequest(new Request("carol", "pass789", "/admin/dashboard")));
    }
}
```

How to run: `java SpringSecurityIntroLevel3.java`

Carol's first request succeeds — `/audit/logs` requires `ADMIN` OR `AUDITOR`, and Carol has `AUDITOR` — while her second request fails authorization specifically (not authentication; her credentials are perfectly valid) because `/admin/dashboard` requires `ADMIN`, which Carol lacks — the explicit per-gate logging makes visible exactly which of the two stages made each decision, mirroring how Spring Security's own filter chain can be configured to log authentication and authorization decisions separately for auditing and debugging.

## 6. Walkthrough

Trace Carol's second request (`/admin/dashboard`) in Level 3.

1. `handleRequest(new Request("carol", "pass789", "/admin/dashboard"))` calls `authenticate(request)` first.
2. Inside `authenticate`, `users.get("carol")` finds Carol's `User` record, and `user.password().equals("pass789")` checks `"pass789".equals("pass789")`, which is `true` — `authenticate` returns Carol's `User` object (non-null).
3. Back in `handleRequest`, `user == null` is `false`, so the authentication-failure branch is skipped, and the `println` confirms authentication succeeded, reporting Carol's roles as `{AUDITOR}`.
4. `authorize(user, "/admin/dashboard")` is called next — `requiredRolesByResource.getOrDefault("/admin/dashboard", ...)` returns `Set.of("ADMIN")`, and `Collections.disjoint(user.roles(), required)` checks whether `{AUDITOR}` and `{ADMIN}` share zero elements — they do share zero elements (disjoint), so `disjoint` returns `true`, and `!true` is `false` — `authorize` returns `false`.
5. Back in `handleRequest`, `!authorize(...)` is `true`, so the authorization-failure branch runs, printing the specific failure reason (`"roles [AUDITOR] insufficient for /admin/dashboard"`) and returning `"403 Forbidden"` — critically, this is a *different* failure than an authentication failure would have been; Carol's identity was never in question, only her permission for this specific resource.

```
handleRequest(carol, pass789, /admin/dashboard):
  authenticate: users.get("carol") found, password matches -> returns User(roles={AUDITOR})
    [AUTHENTICATION] OK
  authorize(user, "/admin/dashboard"): required={ADMIN}, user.roles()={AUDITOR} -> disjoint -> NOT authorized
    [AUTHORIZATION] FAILED
  result: 403 Forbidden   (NOT 401 -- her identity was fine, her PERMISSION was the problem)
```

## 7. Gotchas & takeaways

> **Gotcha:** conflating authentication failures (401) with authorization failures (403) — returning the same generic rejection for both — hides useful diagnostic information from legitimate callers and can even be a minor information-disclosure concern in the other direction (confirming a resource exists to an unauthorized-but-authenticated caller via a 403, versus a 401 that reveals nothing) if not deliberately considered. Spring Security's own default behavior distinguishes these two outcomes precisely because they represent genuinely different problems requiring different responses from a caller (re-authenticate, versus request different permissions).

- Spring Security's foundational job is answering two distinct, sequentially-ordered questions — who is this (authentication) and what can they do (authorization) — before any application business logic executes at all.
- Centralizing this logic in a dedicated, well-tested framework rather than reimplementing it per-application or per-endpoint is the core value proposition: consistent enforcement, and protection against a class of security mistakes that's easy to introduce when security logic is scattered and hand-rolled.
- The strict ordering (authenticate first, then authorize) matters — authorization decisions are meaningless without first establishing a reliable identity to authorize, which is why Spring Security's filter chain (covered in the next several cards) enforces this sequence structurally.
- Every subsequent card in this series builds on this two-question foundation — the filter chain, `SecurityContext`, `Authentication` objects, and `GrantedAuthority` are all mechanisms for implementing authentication and authorization concretely within Spring's request-handling pipeline.
