---
card: spring-security
gi: 117
slug: serverhttpsecurity-dsl
title: "ServerHttpSecurity DSL"
---

## 1. What it is

`ServerHttpSecurity` is the reactive-stack counterpart to `HttpSecurity` — the fluent DSL used inside an `@EnableWebFluxSecurity`-annotated configuration (card 0115) to build a `SecurityWebFilterChain`. Its method names deliberately mirror `HttpSecurity`'s wherever the underlying concept is the same (`.httpBasic()`, `.formLogin()`, `.csrf()`, `.cors()`, `.oauth2Login()`, `.oauth2ResourceServer()` all exist on both), but every configurer underneath is built against reactive contracts (`ServerAuthenticationSuccessHandler` returns `Mono<Void>`, not `void`; matchers are `ServerWebExchangeMatcher`, not `RequestMatcher`), and the request-matching method itself changes name from `authorizeHttpRequests` to `authorizeExchange`, reflecting WebFlux's `ServerWebExchange` abstraction rather than the Servlet API's `HttpServletRequest`.

```java
@Bean
public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
    http
        .authorizeExchange(exchange -> exchange
            .pathMatchers("/public/**").permitAll()
            .pathMatchers(HttpMethod.POST, "/api/orders").hasAuthority("SCOPE_write:orders")
            .anyExchange().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
        .csrf(ServerHttpSecurity.CsrfSpec::disable); // common for a stateless, token-authenticated reactive API
    return http.build();
}
```

## 2. Why & when

Every configuration decision covered across this entire course — which endpoints require authentication, which authentication mechanisms are active, how CSRF and CORS are handled — still needs to be made in a WebFlux application; `ServerHttpSecurity` exists so that decision-making DSL can be expressed against reactive primitives throughout, rather than attempting to reuse `HttpSecurity` (which is fundamentally built around the Servlet API's blocking `Filter` chain and would not compose correctly with a non-blocking server at all). Recognizing the parallel structure — same concepts, same method names in most cases, reactive contracts underneath — is what lets prior knowledge from the Servlet stack transfer efficiently rather than requiring the entire DSL to be relearned from scratch.

Reach for `ServerHttpSecurity` when:

- Configuring security for any Spring WebFlux application — this is the only correct entry point, in the same way `HttpSecurity` is the only correct entry point for a Servlet-stack application.
- Translating a known Servlet-stack security configuration into its reactive equivalent — mapping `authorizeHttpRequests`/`requestMatchers` to `authorizeExchange`/`pathMatchers` is usually a close, direct translation, though every custom component referenced from it (a `UserDetailsService`, an `AuthenticationSuccessHandler`) must be reactive-native (card 0115).
- Building a stateless, bearer-token-authenticated reactive API — a very common WebFlux use case — where `csrf().disable()` (or its reactive equivalent) and `oauth2ResourceServer().jwt(...)` typically appear together, mirroring the Servlet-stack pattern from cards 0099–0106.
- Composing multiple `SecurityWebFilterChain` beans, matched to different path patterns via `securityMatcher(...)` — the reactive equivalent of the Servlet stack's `securityMatcher`-scoped multiple `SecurityFilterChain` beans.

## 3. Core concept

```
Servlet DSL                                Reactive DSL
------------------------------------       ------------------------------------------
HttpSecurity                               ServerHttpSecurity
.authorizeHttpRequests(auth -> ...)        .authorizeExchange(exchange -> ...)
    .requestMatchers("/api/**")                 .pathMatchers("/api/**")
    .hasRole("ADMIN")                           .hasRole("ADMIN")            (SAME method name)
    .anyRequest().authenticated()               .anyExchange().authenticated() (SAME shape)
.formLogin(Customizer.withDefaults())      .formLogin(Customizer.withDefaults())   (SAME)
.httpBasic(Customizer.withDefaults())      .httpBasic(Customizer.withDefaults())   (SAME)
.oauth2Login(...)                          .oauth2Login(...)                       (SAME)
.oauth2ResourceServer(oauth2 -> oauth2.jwt(...))  .oauth2ResourceServer(oauth2 -> oauth2.jwt(...))  (SAME)
.csrf(csrf -> csrf.disable())              .csrf(ServerHttpSecurity.CsrfSpec::disable)   (same idea)
.sessionManagement(...)                    -- reactive apps are typically stateless by DEFAULT design,
                                               so this concern rarely arises the same way

build() -> SecurityFilterChain             build() -> SecurityWebFilterChain
```

The DSL surface is close enough that most of what earlier cards covered about *what* to configure (authorization rules, which authentication mechanisms to enable) transfers directly — only the underlying execution model, and therefore every custom component's contract, genuinely differs.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing HttpSecurity and ServerHttpSecurity as parallel DSL entry points both configuring authorization rules and authentication mechanisms with matching method names but producing SecurityFilterChain versus SecurityWebFilterChain respectively">
  <rect x="20" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="165" y="42" fill="#8b949e" font-size="10.5" text-anchor="middle" font-family="sans-serif">HttpSecurity (Servlet)</text>
  <text x="165" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.authorizeHttpRequests(...)</text>
  <text x="165" y="83" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.formLogin(...) / .httpBasic(...)</text>
  <text x="165" y="101" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.oauth2ResourceServer(...)</text>
  <text x="165" y="130" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">.build() -&gt; SecurityFilterChain</text>

  <rect x="330" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="475" y="42" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">ServerHttpSecurity (WebFlux)</text>
  <text x="475" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.authorizeExchange(...)</text>
  <text x="475" y="83" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.formLogin(...) / .httpBasic(...)</text>
  <text x="475" y="101" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.oauth2ResourceServer(...)</text>
  <text x="475" y="130" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">.build() -&gt; SecurityWebFilterChain</text>

  <text x="330" y="10" fill="#8b949e" font-size="1"> </text>
</svg>

Matching method names throughout — the DSL surface is intentionally familiar; only the execution model and the `build()` result type differ.

## 5. Runnable example

The scenario: model both DSLs' rule-matching logic side by side using a shared, minimal path-matching engine, showing that the same authorization *rules* apply identically in shape to both stacks, then extend into the one area — CSRF defaults — where a stateless reactive API commonly diverges in configuration from a typical browser-facing Servlet application.

### Level 1 — Basic

A minimal `authorizeExchange`-style rule matcher.

```java
import java.util.*;
import java.util.function.*;

public class ServerHttpSecurityLevel1 {
    record Rule(Predicate<String> pathMatcher, String requirement) {}

    static class AuthorizeExchangeSpec {
        private final List<Rule> rules = new ArrayList<>();

        AuthorizeExchangeSpec pathMatchers(String pattern, String requirement) {
            rules.add(new Rule(path -> matchesPattern(path, pattern), requirement));
            return this;
        }
        AuthorizeExchangeSpec anyExchange(String requirement) {
            rules.add(new Rule(path -> true, requirement)); // catch-all, evaluated LAST
            return this;
        }

        String evaluate(String path) {
            for (Rule rule : rules) if (rule.pathMatcher().test(path)) return rule.requirement();
            return "denied (no matching rule)";
        }

        private static boolean matchesPattern(String path, String pattern) {
            String regex = pattern.replace("**", ".*").replace("*", "[^/]*");
            return path.matches(regex);
        }
    }

    public static void main(String[] args) {
        AuthorizeExchangeSpec spec = new AuthorizeExchangeSpec()
                .pathMatchers("/public/**", "permitAll")
                .anyExchange("authenticated");

        System.out.println("/public/info -> " + spec.evaluate("/public/info"));
        System.out.println("/api/orders -> " + spec.evaluate("/api/orders"));
    }
}
```

**How to run:** save as `ServerHttpSecurityLevel1.java`, run `java ServerHttpSecurityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
/public/info -> permitAll
/api/orders -> authenticated
```

`AuthorizeExchangeSpec` mirrors the exact rule-evaluation shape of both `authorizeHttpRequests` and `authorizeExchange` — an ordered list of pattern-to-requirement rules, first match wins — demonstrating that the *authorization logic itself* is identical in shape between the two stacks; only the underlying request type being matched against differs.

### Level 2 — Intermediate

Add method-specific rules and authority requirements, mirroring `pathMatchers(HttpMethod.POST, "/api/orders").hasAuthority(...)`.

```java
import java.util.*;
import java.util.function.*;

public class ServerHttpSecurityLevel2 {
    record Exchange(String method, String path, Set<String> authorities) {}
    record Rule(BiPredicate<String, String> matcher, Function<Exchange, Boolean> requirement, String description) {}

    static class AuthorizeExchangeSpec {
        private final List<Rule> rules = new ArrayList<>();

        AuthorizeExchangeSpec pathMatchers(String method, String pattern, String requiredAuthority) {
            rules.add(new Rule(
                    (m, p) -> method.equals(m) && matchesPattern(p, pattern),
                    ex -> ex.authorities().contains(requiredAuthority),
                    "requires " + requiredAuthority));
            return this;
        }
        AuthorizeExchangeSpec pathMatchers(String pattern, String requirement) {
            rules.add(new Rule((m, p) -> matchesPattern(p, pattern), ex -> true, requirement));
            return this;
        }
        AuthorizeExchangeSpec anyExchange() {
            rules.add(new Rule((m, p) -> true, ex -> !ex.authorities().isEmpty(), "authenticated"));
            return this;
        }

        boolean evaluate(Exchange exchange) {
            for (Rule rule : rules) {
                if (rule.matcher().test(exchange.method(), exchange.path())) {
                    return rule.requirement().apply(exchange);
                }
            }
            return false;
        }

        private static boolean matchesPattern(String path, String pattern) {
            return path.matches(pattern.replace("**", ".*").replace("*", "[^/]*"));
        }
    }

    public static void main(String[] args) {
        AuthorizeExchangeSpec spec = new AuthorizeExchangeSpec()
                .pathMatchers("/public/**", "permitAll")
                .pathMatchers("POST", "/api/orders", "SCOPE_write:orders")
                .anyExchange();

        Exchange readOnlyUser = new Exchange("POST", "/api/orders", Set.of("SCOPE_read:orders"));
        Exchange writeUser = new Exchange("POST", "/api/orders", Set.of("SCOPE_write:orders"));

        System.out.println("read-only user POSTing to /api/orders: allowed=" + spec.evaluate(readOnlyUser));
        System.out.println("write-scoped user POSTing to /api/orders: allowed=" + spec.evaluate(writeUser));
    }
}
```

**How to run:** save as `ServerHttpSecurityLevel2.java`, run `java ServerHttpSecurityLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
read-only user POSTing to /api/orders: allowed=false
write-scoped user POSTing to /api/orders: allowed=true
```

What changed: a method-and-path-specific rule (`POST /api/orders`) now requires a specific authority, mirroring `.pathMatchers(HttpMethod.POST, "/api/orders").hasAuthority("SCOPE_write:orders")` exactly — a user with only read scope is correctly denied write access to the same endpoint a write-scoped user is permitted to reach, with the evaluation logic identical in shape to its Servlet-stack counterpart from card 0104.

### Level 3 — Advanced

Add the CSRF-default divergence: a typical browser-facing Servlet application defaults to CSRF protection enabled, while a stateless, bearer-token-authenticated reactive API commonly disables it deliberately — model both configurations and show why the reactive API's choice is safe in its specific context.

```java
import java.util.*;

public class ServerHttpSecurityLevel3 {
    record Exchange(String method, String path, boolean hasValidCsrfToken, boolean hasValidBearerToken, boolean isSessionBased) {}

    static class SecurityConfig {
        private boolean csrfEnabled;
        private boolean statelessBearerAuth;

        SecurityConfig csrf(boolean enabled) { this.csrfEnabled = enabled; return this; }
        SecurityConfig statelessBearerAuth(boolean enabled) { this.statelessBearerAuth = enabled; return this; }

        boolean isRequestAllowed(Exchange exchange) {
            if (statelessBearerAuth) {
                // a stateless, bearer-token API: the token ITSELF is the CSRF defense --
                // a forged cross-site request can't attach an Authorization header the way it can a cookie
                return exchange.hasValidBearerToken();
            }
            if (csrfEnabled && exchange.isSessionBased() && !"GET".equals(exchange.method())) {
                return exchange.hasValidCsrfToken(); // session-based state-changing request MUST carry a valid CSRF token
            }
            return true;
        }
    }

    public static void main(String[] args) {
        // configuration A: typical browser-facing app, session-based, CSRF protection ON
        SecurityConfig browserApp = new SecurityConfig().csrf(true).statelessBearerAuth(false);

        Exchange sessionRequestNoCsrfToken = new Exchange("POST", "/transfer-funds", false, false, true);
        Exchange sessionRequestWithCsrfToken = new Exchange("POST", "/transfer-funds", true, false, true);

        System.out.println("browser app, session request WITHOUT csrf token: allowed=" + browserApp.isRequestAllowed(sessionRequestNoCsrfToken));
        System.out.println("browser app, session request WITH csrf token: allowed=" + browserApp.isRequestAllowed(sessionRequestWithCsrfToken));

        // configuration B: stateless reactive API, bearer-token authenticated, CSRF explicitly disabled
        SecurityConfig reactiveApi = new SecurityConfig().csrf(false).statelessBearerAuth(true);

        Exchange bearerRequestNoToken = new Exchange("POST", "/api/orders", false, false, false);
        Exchange bearerRequestWithToken = new Exchange("POST", "/api/orders", false, true, false);

        System.out.println("reactive API, request WITHOUT bearer token: allowed=" + reactiveApi.isRequestAllowed(bearerRequestNoToken));
        System.out.println("reactive API, request WITH bearer token: allowed=" + reactiveApi.isRequestAllowed(bearerRequestWithToken));
    }
}
```

**How to run:** save as `ServerHttpSecurityLevel3.java`, run `java ServerHttpSecurityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
browser app, session request WITHOUT csrf token: allowed=false
browser app, session request WITH csrf token: allowed=true
reactive API, request WITHOUT bearer token: allowed=false
reactive API, request WITH bearer token: allowed=true
```

What changed: `isRequestAllowed` now branches on the actual security model in play — a session-cookie-based application genuinely needs CSRF protection (a browser attaches cookies to cross-site requests automatically, card 0075's territory), while a stateless bearer-token API's own authentication mechanism already defends against the same class of attack (a cross-site request can't forge an `Authorization` header the way it can ride along on a cookie), which is exactly why `.csrf(ServerHttpSecurity.CsrfSpec::disable)` is a common and *correct* choice specifically in that configuration, not a security oversight.

## 6. Walkthrough

Trace a real request through a `ServerHttpSecurity`-configured reactive resource server, tying the DSL directly to card 0100's bearer-token authentication flow.

**Step 1 — configuration, at startup:**
```java
@Bean
public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
    http.authorizeExchange(exchange -> exchange
            .pathMatchers("/public/**").permitAll()
            .pathMatchers(HttpMethod.POST, "/api/orders").hasAuthority("SCOPE_write:orders")
            .anyExchange().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
        .csrf(ServerHttpSecurity.CsrfSpec::disable);
    return http.build();
}
```
This corresponds to `Level 2`'s `AuthorizeExchangeSpec` construction combined with `Level 3`'s `statelessBearerAuth(true)` configuration.

**Step 2 — an inbound request:**
```
POST /api/orders HTTP/1.1
Authorization: Bearer eyJhbGci...
```

**Step 3 — rule matching.** The reactive equivalent of `BearerTokenAuthenticationFilter` (card 0100) has already run by this point, resolving the request's authenticated authorities from the JWT's `scope` claim. `authorizeExchange`'s rules are evaluated in order: `/public/**` doesn't match; `POST /api/orders` matches the second rule, requiring `SCOPE_write:orders` — corresponding to `Level 2`'s `pathMatchers("POST", "/api/orders", "SCOPE_write:orders")` rule.

**Step 4 — authority check.** If the decoded JWT's authorities include `SCOPE_write:orders`, the rule's requirement (`ex.authorities().contains("SCOPE_write:orders")`) evaluates `true`, and the request proceeds to the controller.

**Step 5 — CSRF is never evaluated at all.** Because `.csrf(ServerHttpSecurity.CsrfSpec::disable)` was configured, no CSRF token check happens for this (or any) request — this is safe specifically because authentication here rests entirely on the `Authorization` header (which a cross-site request cannot forge), not on an automatically-attached session cookie (which it could).

```
POST /api/orders, Authorization: Bearer <write-scoped JWT>
   -> JWT decoded, authenticated, authorities include SCOPE_write:orders (card 0100, 0104)
   -> authorizeExchange: path+method rule matches -> requires SCOPE_write:orders -> PASSES
   -> csrf() disabled -> no token check needed, safe because auth is header-based, not cookie-based
   -> request reaches the controller
```

## 7. Gotchas & takeaways

> **Gotcha:** disabling CSRF protection is only safe when the application genuinely never relies on cookie-based session authentication for state-changing requests — a WebFlux application that mixes `oauth2Login()` (which does use a session, browser-cookie-based, per card 0088's flow) with CSRF disabled globally reintroduces exactly the vulnerability card 0075 exists to prevent. The `statelessBearerAuth`-implies-`csrf-disable` reasoning in Level 3 applies specifically to APIs with no session-cookie-based authentication path at all.

- `ServerHttpSecurity` is the reactive-stack counterpart to `HttpSecurity`, with deliberately matching method names wherever the underlying concept is shared — `authorizeExchange` replaces `authorizeHttpRequests`, reflecting WebFlux's `ServerWebExchange` in place of `HttpServletRequest`.
- The authorization rule-matching logic (ordered rules, first match wins, path/method/authority-based requirements) is identical in shape between the two stacks — prior knowledge of `authorizeHttpRequests` transfers directly to `authorizeExchange`.
- Every custom component referenced from `ServerHttpSecurity` (a `ReactiveUserDetailsService`, a `ServerAuthenticationSuccessHandler`) must be written against the reactive contract from card 0115 — the DSL's familiar shape does not extend to the components it wires together.
- CSRF defaults commonly diverge in practice: a stateless, bearer-token-authenticated reactive API frequently disables it deliberately, since the bearer token itself already defends against the cross-site-forgery scenario CSRF protection exists for — but this reasoning only holds when no cookie-based session authentication is also in play.
- `.build()` produces a `SecurityWebFilterChain` rather than a `SecurityFilterChain` — the return type is the clearest signal of which stack a given configuration bean belongs to.
