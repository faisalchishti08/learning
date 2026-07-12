---
card: spring-authorization-server
gi: 2
slug: relationship-to-spring-security
title: "Relationship to Spring Security"
---

## 1. What it is

Spring Authorization Server is not a standalone product with its own security model — it is a Spring Security **extension**, built entirely on top of the same `SecurityFilterChain`/`HttpSecurity` DSL every earlier card in this course has used, adding a specialized configurer (`OAuth2AuthorizationServerConfigurer`, card 0008's territory) that registers a family of filters (`OAuth2AuthorizationEndpointFilter`, `OAuth2TokenEndpointFilter`, `OAuth2TokenIntrospectionEndpointFilter`, and others) into that same chain, positioned alongside — not instead of — whatever other Spring Security configuration an application already has.

```java
@Bean
@Order(Ordered.HIGHEST_PRECEDENCE)  // this chain must be evaluated FIRST
public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
    OAuth2AuthorizationServerConfigurer authorizationServer = OAuth2AuthorizationServerConfigurer.authorizationServer();
    http.securityMatcher(authorizationServer.getEndpointsMatcher())
        .with(authorizationServer, Customizer.withDefaults());
    return http.build();
}

@Bean
@Order(2)  // this chain handles EVERYTHING ELSE -- ordinary application endpoints
public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .formLogin(Customizer.withDefaults());
    return http.build();
}
```

## 2. Why & when

Every mechanism this course has covered — `authorizeHttpRequests`, `formLogin()`, custom `AuthenticationProvider`s, method security — is genuinely available and applicable within an authorization server application, because the authorization server *is* a Spring Security application, not a separate framework requiring separate skills. This matters practically: the authorization server needs its own login page for resource owners to authenticate against (typically `formLogin()`, exactly as covered in early cards), its own user store (a `UserDetailsService`, cards from this course's earlier sections), and potentially its own method-security-protected admin endpoints for managing registered clients — all built with the *same* tools, not a parallel, OAuth2-specific security stack.

Reach for understanding this relationship specifically when:

- Deciding how the authorization server's *own* login page should authenticate resource owners — this is ordinary `formLogin()`/`UserDetailsService` configuration, no different from any application in this course, layered underneath the OAuth2-specific endpoints.
- Securing administrative endpoints for managing `RegisteredClient`s (adding, revoking client registrations) — this is exactly method security (card 0062) or `authorizeHttpRequests` protecting ordinary application endpoints, composed alongside the authorization server's own configurer.
- Debugging why an authorization server's endpoint behaves unexpectedly — since it's built on the same filter chain machinery, techniques from earlier cards (inspecting filter order, checking `SecurityContextHolder`) apply directly.
- Running the authorization server and a resource server (or even a client) in the same application — since all three roles are just different Spring Security configurations, they can coexist as multiple `SecurityFilterChain` beans, each scoped via `securityMatcher(...)` to its own set of paths.

## 3. Core concept

```
Spring Authorization Server's role in the SecurityFilterChain ecosystem:

    OAuth2AuthorizationServerConfigurer  -- ADDS OAuth2/OIDC-specific filters to a chain,
                                            via the SAME .with(configurer, customizer) mechanism
                                            every other Spring Security configurer uses

Typical multi-chain setup (card 0027's "multiple SecurityFilterChain beans" pattern, applied here):
    Chain 1 (HIGHEST precedence): securityMatcher matches ONLY /oauth2/**, /.well-known/**
        -- configured with OAuth2AuthorizationServerConfigurer
        -- handles authorization requests, token issuance, JWKS, OIDC discovery
    Chain 2 (lower precedence): matches EVERYTHING ELSE
        -- configured with ORDINARY formLogin()/authorizeHttpRequests()
        -- this is where the resource owner actually LOGS IN to the auth server itself

The resource owner's login (via Chain 2's formLogin()) happens BEFORE the OAuth2
authorization flow can complete -- exactly mirroring card 0090's step 2 ("user
authenticates AT the provider"), except here, "the provider" IS this same
application, using the SAME formLogin() mechanism every earlier card covered.
```

Nothing about OAuth2/OIDC protocol logic replaces ordinary Spring Security authentication — it sits on top of it, needing a real, working login mechanism underneath to authenticate the resource owner in the first place.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing two SecurityFilterChain beans in one application the first matching oauth2 specific paths and configured with the authorization server configurer the second matching everything else and configured with ordinary formLogin both coexisting in the same Spring Security application">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="45" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ONE Spring Security application</text>

  <rect x="40" y="75" width="280" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Chain 1 (HIGHEST precedence)</text>
  <text x="180" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">securityMatcher: /oauth2/**, /.well-known/**</text>
  <text x="180" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizationServerConfigurer</text>

  <rect x="340" y="75" width="280" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="480" y="97" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Chain 2 (lower precedence)</text>
  <text x="480" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">securityMatcher: everything else</text>
  <text x="480" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ordinary formLogin() -- resource owner login</text>

  <text x="320" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">both chains are ordinary Spring Security configuration, composed via the SAME mechanism (card 0027)</text>

  <defs></defs>
</svg>

Two `SecurityFilterChain` beans, both built with familiar tools — one OAuth2-specific, one an ordinary application login.

## 5. Runnable example

The scenario: model the two-chain structure directly — a path-matching router deciding which "chain" handles a given request, one chain simulating the OAuth2-specific endpoints, the other simulating an ordinary login form — growing from a bare routing decision into the full picture of a resource owner logging in through the ordinary chain before an OAuth2 flow on the other chain can complete.

### Level 1 — Basic

Two chains, routed by path pattern.

```java
import java.util.*;
import java.util.function.*;

public class RelationshipLevel1 {
    interface Chain { String handle(String path); }

    static class Router {
        private final List<Map.Entry<Predicate<String>, Chain>> chains = new ArrayList<>();
        void addChain(Predicate<String> matcher, Chain chain) { chains.add(Map.entry(matcher, chain)); }

        String route(String path) {
            for (var entry : chains) {
                if (entry.getKey().test(path)) return entry.getValue().handle(path);
            }
            throw new IllegalStateException("no chain matched: " + path);
        }
    }

    public static void main(String[] args) {
        Router router = new Router();
        router.addChain(path -> path.startsWith("/oauth2/"), path -> "OAuth2AuthorizationServerConfigurer handled: " + path);
        router.addChain(path -> true, path -> "ordinary formLogin()/authorizeHttpRequests handled: " + path); // catch-all

        System.out.println(router.route("/oauth2/authorize"));
        System.out.println(router.route("/dashboard"));
    }
}
```

**How to run:** save as `RelationshipLevel1.java`, run `java RelationshipLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
OAuth2AuthorizationServerConfigurer handled: /oauth2/authorize
ordinary formLogin()/authorizeHttpRequests handled: /dashboard
```

`Router` mirrors the `securityMatcher`-based routing between multiple `SecurityFilterChain` beans — a request's path determines which chain (and therefore which configurer) processes it, exactly the mechanism a real Spring Boot application uses to let OAuth2-specific and ordinary application security coexist.

### Level 2 — Intermediate

Add the ordinary login flow on the second chain, requiring an actual authenticated session before the OAuth2 chain's authorization endpoint will proceed — mirroring card 0090's "user authenticates AT the provider" step, here happening against this same application.

```java
import java.util.*;

public class RelationshipLevel2 {
    static class Session {
        String authenticatedUsername;
        boolean isAuthenticated() { return authenticatedUsername != null; }
    }

    static class OrdinaryLoginChain {
        private final Map<String, String> validCredentials;
        OrdinaryLoginChain(Map<String, String> validCredentials) { this.validCredentials = validCredentials; }

        // mirrors formLogin() -- ordinary username/password authentication
        void login(Session session, String username, String password) {
            if (!password.equals(validCredentials.get(username))) throw new IllegalStateException("Bad credentials");
            session.authenticatedUsername = username;
        }
    }

    static class OAuth2AuthorizationChain {
        // mirrors OAuth2AuthorizationEndpointFilter -- requires an ALREADY-authenticated session
        String authorize(Session session, String clientId) {
            if (!session.isAuthenticated()) {
                throw new IllegalStateException("must authenticate first -- redirecting to login page");
            }
            return "code-for-" + session.authenticatedUsername + "-and-" + clientId;
        }
    }

    public static void main(String[] args) {
        OrdinaryLoginChain loginChain = new OrdinaryLoginChain(Map.of("alice", "secret123"));
        OAuth2AuthorizationChain oauth2Chain = new OAuth2AuthorizationChain();

        Session session = new Session();

        // attempt 1: hit the OAuth2 endpoint BEFORE logging in
        try {
            oauth2Chain.authorize(session, "my-app");
        } catch (IllegalStateException e) {
            System.out.println("before login: " + e.getMessage());
        }

        // step: log in via the ORDINARY chain (formLogin(), not anything OAuth2-specific)
        loginChain.login(session, "alice", "secret123");
        System.out.println("logged in as: " + session.authenticatedUsername);

        // attempt 2: NOW the OAuth2 endpoint succeeds
        String code = oauth2Chain.authorize(session, "my-app");
        System.out.println("authorization code issued: " + code);
    }
}
```

**How to run:** save as `RelationshipLevel2.java`, run `java RelationshipLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
before login: must authenticate first -- redirecting to login page
logged in as: alice
authorization code issued: code-for-alice-and-my-app
```

What changed: the OAuth2-specific chain now genuinely *requires* the ordinary login chain to have already authenticated the session — this precisely models why "user authenticates AT the provider" (card 0090's step 2) means logging in via ordinary Spring Security mechanisms *when the provider is your own application*, not some separate OAuth2-specific authentication process.

### Level 3 — Advanced

Add an administrative endpoint protected by method security (mirroring card 0062), demonstrating that every ordinary Spring Security tool — not just `formLogin()` — applies equally well within an authorization server application, alongside the OAuth2-specific machinery.

```java
import java.util.*;

public class RelationshipLevel3 {
    static class Session {
        String authenticatedUsername;
        Set<String> authorities = Set.of();
        boolean isAuthenticated() { return authenticatedUsername != null; }
    }

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    static class OrdinaryLoginChain {
        private final Map<String, String> validCredentials;
        private final Map<String, Set<String>> authoritiesByUsername;
        OrdinaryLoginChain(Map<String, String> validCredentials, Map<String, Set<String>> authoritiesByUsername) {
            this.validCredentials = validCredentials; this.authoritiesByUsername = authoritiesByUsername;
        }
        void login(Session session, String username, String password) {
            if (!password.equals(validCredentials.get(username))) throw new IllegalStateException("Bad credentials");
            session.authenticatedUsername = username;
            session.authorities = authoritiesByUsername.getOrDefault(username, Set.of("ROLE_USER"));
        }
    }

    static class OAuth2AuthorizationChain {
        String authorize(Session session, String clientId) {
            if (!session.isAuthenticated()) throw new IllegalStateException("must authenticate first");
            return "code-for-" + session.authenticatedUsername + "-and-" + clientId;
        }
    }

    // mirrors a @PreAuthorize("hasRole('ADMIN')")-protected client-management endpoint
    static class ClientAdministrationService {
        void registerNewClient(Session session, String newClientId) {
            if (!session.authorities.contains("ROLE_ADMIN")) throw new AccessDeniedException("Access Denied");
            System.out.println("client registered: " + newClientId);
        }
    }

    public static void main(String[] args) {
        OrdinaryLoginChain loginChain = new OrdinaryLoginChain(
                Map.of("alice", "secret123", "bob", "hunter2"),
                Map.of("alice", Set.of("ROLE_USER", "ROLE_ADMIN"), "bob", Set.of("ROLE_USER")));
        OAuth2AuthorizationChain oauth2Chain = new OAuth2AuthorizationChain();
        ClientAdministrationService adminService = new ClientAdministrationService();

        // alice: an admin, can both log in for OAuth2 AND manage client registrations
        Session aliceSession = new Session();
        loginChain.login(aliceSession, "alice", "secret123");
        String aliceCode = oauth2Chain.authorize(aliceSession, "my-app");
        System.out.println("alice's authorization code: " + aliceCode);
        adminService.registerNewClient(aliceSession, "new-partner-app");

        // bob: a regular user, can log in for OAuth2 but CANNOT manage client registrations
        Session bobSession = new Session();
        loginChain.login(bobSession, "bob", "hunter2");
        String bobCode = oauth2Chain.authorize(bobSession, "my-app");
        System.out.println("bob's authorization code: " + bobCode);
        try {
            adminService.registerNewClient(bobSession, "another-app");
        } catch (AccessDeniedException e) {
            System.out.println("bob attempting client admin: DENIED -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `RelationshipLevel3.java`, run `java RelationshipLevel3.java` (JDK 17+ runs single files directly).

Expected output (code values vary by username/client only, deterministic here):
```
alice's authorization code: code-for-alice-and-my-app
client registered: new-partner-app
bob's authorization code: code-for-bob-and-my-app
bob attempting client admin: DENIED -- Access Denied
```

What changed: both alice and bob can complete the OAuth2 authorization flow (both are ordinary, logged-in users as far as the OAuth2 chain cares), but only alice — carrying `ROLE_ADMIN` from the *same* ordinary authentication mechanism — passes the method-security check protecting client administration. This demonstrates that authentication (via ordinary Spring Security) and authorization (via ordinary method security or `authorizeHttpRequests`) both apply uniformly across every part of an authorization server application, OAuth2-specific or not.

## 6. Walkthrough

Trace alice's full sequence from Level 3, showing exactly where ordinary Spring Security and OAuth2-specific machinery each apply.

**Step 1 — alice's browser hits the authorization server's login page**, an entirely ordinary `formLogin()`-rendered page, no different from any application in this course:
```
GET /login HTTP/1.1
```

**Step 2 — she submits her credentials**, processed by the *ordinary* second `SecurityFilterChain` (Level 3's `loginChain.login(...)`):
```
POST /login HTTP/1.1

username=alice&password=secret123
```
Her session is now authenticated, with authorities `{"ROLE_USER", "ROLE_ADMIN"}` — nothing about this step is OAuth2-specific at all.

**Step 3 — an OAuth2 client redirects her browser to this same server's authorization endpoint** (the *first*, OAuth2-specific `SecurityFilterChain`):
```
GET /oauth2/authorize?client_id=my-app&response_type=code&... HTTP/1.1
```
Because her session is already authenticated (step 2), `OAuth2AuthorizationEndpointFilter` (corresponding to `oauth2Chain.authorize(aliceSession, "my-app")`) proceeds directly to issuing an authorization code, rather than redirecting her to log in again.

**Step 4 — separately, alice (an administrator) manages client registrations** through an entirely ordinary, method-security-protected service endpoint:
```
POST /admin/clients HTTP/1.1

clientId=new-partner-app
```
This corresponds to `adminService.registerNewClient(aliceSession, "new-partner-app")` — protected by a check reading the exact same `authorities` her ordinary login (step 2) established, with no OAuth2-specific logic involved at all.

**Step 5 — contrast: bob's attempt at the same admin endpoint.** Bob's session, established through the identical ordinary login mechanism, carries only `{"ROLE_USER"}` — the method-security check denies him, exactly as any `@PreAuthorize("hasRole('ADMIN')")` check would deny any insufficiently-privileged user anywhere in this course.

```
alice: ordinary login (step 2) -> authorities include ROLE_ADMIN
   -> OAuth2 authorization endpoint (step 3): PROCEEDS (already authenticated)
   -> admin endpoint (step 4): PROCEEDS (has ROLE_ADMIN)

bob: ordinary login -> authorities do NOT include ROLE_ADMIN
   -> OAuth2 authorization endpoint: PROCEEDS (already authenticated -- OAuth2 doesn't care about ROLE_ADMIN)
   -> admin endpoint: DENIED (lacks ROLE_ADMIN)
```

## 7. Gotchas & takeaways

> **Gotcha:** the two `SecurityFilterChain` beans' relative order (`@Order`) matters — the OAuth2-specific chain, scoped via `securityMatcher(...)` to only its own endpoints, must be evaluated *before* a broader, catch-all chain, or the more general chain (matching `anyRequest()`) could intercept OAuth2 endpoint requests first and apply the wrong authentication/authorization rules to them entirely. This is exactly card 0027's multiple-`SecurityFilterChain` ordering concern, applying here with real consequences if gotten wrong.

- Spring Authorization Server is a Spring Security extension, not a separate framework — it adds OAuth2/OIDC-specific filters to an ordinary `SecurityFilterChain` via `OAuth2AuthorizationServerConfigurer`, the same configurer mechanism every other Spring Security feature uses.
- A typical setup uses two `SecurityFilterChain` beans: one, at higher precedence, scoped to OAuth2-specific endpoints; another, at lower precedence, handling the authorization server's *own* ordinary application concerns (login pages, admin endpoints).
- The resource owner's login at "the provider" (card 0090's step 2), when the provider is your own Spring Authorization Server instance, is ordinary `formLogin()`/`UserDetailsService` authentication — nothing OAuth2-specific about it at all.
- Every Spring Security tool this course has covered (method security, custom `AuthenticationProvider`s, multiple filter chains) applies directly within an authorization server application, for concerns beyond the OAuth2 protocol itself (admin endpoints, custom login flows).
- Getting the chain ordering right (OAuth2-specific chain evaluated first, scoped narrowly via `securityMatcher`) is essential — a misconfigured order can let a broader chain intercept OAuth2 endpoint traffic before the correct, specialized configuration ever applies.
