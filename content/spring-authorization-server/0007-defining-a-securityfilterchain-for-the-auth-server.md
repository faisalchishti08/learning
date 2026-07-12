---
card: spring-authorization-server
gi: 7
slug: defining-a-securityfilterchain-for-the-auth-server
title: "Defining a SecurityFilterChain for the auth server"
---

## 1. What it is

Card 0006 introduced the minimal default configuration; this card focuses specifically on the `SecurityFilterChain` bean itself — its exact structure, its required `@Order`, its `securityMatcher(...)` scoping, and the specific exception-handling customization (`defaultAuthenticationEntryPointFor(...)`) that redirects an unauthenticated browser request to a login page rather than returning a bare `401`, while still returning a proper OAuth2 error response for non-browser (API) clients hitting the same endpoints without valid credentials.

```java
@Bean
@Order(Ordered.HIGHEST_PRECEDENCE)
public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
    OAuth2AuthorizationServerConfigurer authorizationServerConfigurer =
            OAuth2AuthorizationServerConfigurer.authorizationServer();

    http
        .securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())
        .with(authorizationServerConfigurer, (authorizationServer) -> authorizationServer
                .oidc(Customizer.withDefaults()))  // enables OpenID Connect endpoints too
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .exceptionHandling(exceptions -> exceptions
                .defaultAuthenticationEntryPointFor(
                        new LoginUrlAuthenticationEntryPoint("/login"),
                        new MediaTypeRequestMatcher(MediaType.TEXT_HTML)));

    return http.build();
}
```

## 2. Why & when

Getting each piece of this chain's configuration right matters concretely: `@Order(Ordered.HIGHEST_PRECEDENCE)` ensures this chain is evaluated before any other `SecurityFilterChain` in the application (card 0002's second, ordinary chain must not intercept OAuth2 endpoint traffic first); `securityMatcher(...)` scopes this chain's rules to *only* the OAuth2/OIDC endpoints, leaving every other request path to the application's other chain; and the media-type-conditional `defaultAuthenticationEntryPointFor(...)` produces the right response shape for two genuinely different callers hitting the same unauthenticated endpoint — a browser (which should see a login page) and an API client or OAuth2 flow's own server-to-server call (which should see a proper error response, not an HTML page it can't render).

Reach for understanding this exact bean structure when:

- Setting up a Spring Authorization Server instance for the first time — this is the foundational bean every subsequent customization (custom client repository, custom token customizer, custom consent page) builds on top of.
- Debugging why an unauthenticated request to `/oauth2/authorize` produces the wrong response shape (an unexpected `401` instead of a login redirect, or vice versa) — this almost always traces to the `defaultAuthenticationEntryPointFor(...)` media-type matcher configuration.
- Verifying the chain ordering is correct when adding a second, custom `SecurityFilterChain` for the application's own (non-OAuth2) endpoints — the OAuth2 chain's `@Order` must remain higher precedence.
- Adding OIDC support specifically — the `.oidc(Customizer.withDefaults())` call inside the configurer lambda is what additionally enables OpenID Connect-specific endpoints (`/userinfo`, ID token issuance) beyond plain OAuth2.

## 3. Core concept

```
authorizationServerSecurityFilterChain, piece by piece:

    @Order(Ordered.HIGHEST_PRECEDENCE)
        -- MUST be evaluated before any other SecurityFilterChain bean in the application,
           or a broader chain could intercept OAuth2 endpoint requests first

    .securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())
        -- SCOPES this entire chain to ONLY the OAuth2/OIDC endpoints this configurer registers
           (card 0006's endpoint family) -- everything else falls through to OTHER chains

    .with(authorizationServerConfigurer, customizer)
        -- the ACTUAL registration of every OAuth2/OIDC filter into this chain

    .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        -- every one of THESE endpoints requires SOME authenticated principal
           (the resource owner, authenticated via the OTHER chain's formLogin(), card 0002)

    .exceptionHandling(exceptions -> exceptions.defaultAuthenticationEntryPointFor(
            new LoginUrlAuthenticationEntryPoint("/login"),
            new MediaTypeRequestMatcher(MediaType.TEXT_HTML)))
        -- CONDITIONAL entry point: an unauthenticated BROWSER request (Accept: text/html)
           gets redirected to /login; an unauthenticated API/OAuth2 client request gets
           the STANDARD OAuth2 error response shape instead (no redirect makes sense for it)
```

Every clause in this configuration addresses a specific, concrete requirement — none of it is boilerplate that could be safely omitted without losing real functionality.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing an unauthenticated request to the authorization endpoint being routed by media type a browser request accepting text html is redirected to the login page while an api or oauth2 client request receives the standard oauth2 error response instead">
  <rect x="20" y="20" width="200" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="120" y="42" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">unauthenticated request</text>
  <text x="120" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">to /oauth2/authorize</text>

  <line x1="220" y1="45" x2="270" y2="45" stroke="#8b949e" stroke-width="1.6" marker-end="url(#sfc7)"/>

  <rect x="275" y="15" width="180" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="365" y="35" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">MediaTypeRequestMatcher</text>
  <text x="365" y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">TEXT_HTML ?</text>

  <line x1="365" y1="65" x2="220" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sfc7b)"/>
  <line x1="365" y1="65" x2="510" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sfc7c)"/>

  <rect x="40" y="112" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="130" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">YES (browser)</text>
  <text x="130" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">302 -&gt; redirect to /login</text>

  <rect x="420" y="112" width="180" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="510" y="132" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">NO (API/OAuth2 client)</text>
  <text x="510" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">standard OAuth2 error response</text>

  <defs>
    <marker id="sfc7" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="sfc7b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="sfc7c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The same unauthenticated hit on the same endpoint produces genuinely different responses, routed by what kind of caller it appears to be.

## 5. Runnable example

The scenario: model the media-type-conditional entry point directly, growing from a single browser-vs-API distinction into a full simulated request-handling pipeline mirroring the whole `SecurityFilterChain` bean's structure, then into verifying the `@Order`/`securityMatcher` scoping actually prevents cross-chain interference.

### Level 1 — Basic

Route an unauthenticated request based on its `Accept` header.

```java
import java.util.*;

public class AuthServerChainLevel1 {
    record MockRequest(String path, String acceptHeader) {}
    record MockResponse(int status, String location, String body) {}

    // mirrors defaultAuthenticationEntryPointFor(LoginUrlAuthenticationEntryPoint, MediaTypeRequestMatcher(TEXT_HTML))
    static MockResponse handleUnauthenticated(MockRequest request) {
        if (request.acceptHeader().contains("text/html")) {
            return new MockResponse(302, "/login", null); // browser -> redirect to login
        }
        return new MockResponse(401, null, "{\"error\":\"invalid_token\"}"); // API/OAuth2 client -> standard error
    }

    public static void main(String[] args) {
        MockResponse browserResponse = handleUnauthenticated(new MockRequest("/oauth2/authorize", "text/html"));
        System.out.println("browser request: status=" + browserResponse.status() + " location=" + browserResponse.location());

        MockResponse apiResponse = handleUnauthenticated(new MockRequest("/oauth2/token", "application/json"));
        System.out.println("API request: status=" + apiResponse.status() + " body=" + apiResponse.body());
    }
}
```

**How to run:** save as `AuthServerChainLevel1.java`, run `java AuthServerChainLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
browser request: status=302 location=/login
API request: status=401 body={"error":"invalid_token"}
```

`handleUnauthenticated` mirrors exactly `defaultAuthenticationEntryPointFor`'s conditional behavior: the *same* underlying "you're not authenticated" fact produces a redirect for a browser and a structured error response for anything else, based purely on the request's `Accept` header.

### Level 2 — Intermediate

Model the full chain structure — `securityMatcher` scoping, the authenticated-required rule, and the conditional entry point — as one coherent pipeline.

```java
import java.util.*;
import java.util.function.*;

public class AuthServerChainLevel2 {
    record MockRequest(String path, String acceptHeader, boolean isAuthenticated) {}
    record MockResponse(int status, String location, String body) {}

    static class AuthorizationServerChain {
        private final Predicate<String> endpointsMatcher;

        AuthorizationServerChain(Predicate<String> endpointsMatcher) { this.endpointsMatcher = endpointsMatcher; }

        // returns EMPTY if this chain doesn't even MATCH the request path (securityMatcher scoping)
        Optional<MockResponse> handle(MockRequest request) {
            if (!endpointsMatcher.test(request.path())) return Optional.empty(); // NOT this chain's concern

            if (!request.isAuthenticated()) {
                if (request.acceptHeader().contains("text/html")) {
                    return Optional.of(new MockResponse(302, "/login", null));
                }
                return Optional.of(new MockResponse(401, null, "{\"error\":\"invalid_token\"}"));
            }
            return Optional.of(new MockResponse(200, null, "{\"code\":\"abc123\"}")); // authenticated -> proceed
        }
    }

    public static void main(String[] args) {
        AuthorizationServerChain chain = new AuthorizationServerChain(path -> path.startsWith("/oauth2/"));

        Optional<MockResponse> matchedUnauthenticated = chain.handle(new MockRequest("/oauth2/authorize", "text/html", false));
        System.out.println("oauth2 endpoint, unauthenticated: " + matchedUnauthenticated.map(MockResponse::status));

        Optional<MockResponse> matchedAuthenticated = chain.handle(new MockRequest("/oauth2/authorize", "text/html", true));
        System.out.println("oauth2 endpoint, authenticated: " + matchedAuthenticated.map(MockResponse::status));

        Optional<MockResponse> unmatchedPath = chain.handle(new MockRequest("/dashboard", "text/html", false));
        System.out.println("non-oauth2 path, this chain's response: " + unmatchedPath
                + " (falls through to the OTHER chain entirely)");
    }
}
```

**How to run:** save as `AuthServerChainLevel2.java`, run `java AuthServerChainLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
oauth2 endpoint, unauthenticated: Optional[302]
oauth2 endpoint, authenticated: Optional[200]
non-oauth2 path, this chain's response: Optional.empty (falls through to the OTHER chain entirely)
```

What changed: `AuthorizationServerChain.handle` now checks `securityMatcher`-equivalent scoping first — a request to `/dashboard` isn't even this chain's concern at all, returning `Optional.empty()` so it can fall through to whatever *other* `SecurityFilterChain` bean handles ordinary application paths, exactly mirroring card 0002's two-chain architecture in action.

### Level 3 — Advanced

Verify that ordering (`@Order`) genuinely matters — simulate a misconfigured setup where a broader, lower-precedence-intended chain is mistakenly evaluated first, incorrectly intercepting an OAuth2 endpoint request, then the corrected version.

```java
import java.util.*;
import java.util.function.*;

public class AuthServerChainLevel3 {
    record MockRequest(String path, String acceptHeader, boolean isAuthenticated) {}
    record MockResponse(int status, String location, String body, String handledBy) {}

    interface Chain { Optional<MockResponse> handle(MockRequest request); }

    static Chain authorizationServerChain() {
        return request -> {
            if (!request.path().startsWith("/oauth2/")) return Optional.empty();
            if (!request.isAuthenticated()) {
                return Optional.of(new MockResponse(302, "/login", null, "AUTHORIZATION SERVER chain"));
            }
            return Optional.of(new MockResponse(200, null, "{\"code\":\"abc123\"}", "AUTHORIZATION SERVER chain"));
        };
    }

    static Chain ordinaryApplicationChain() {
        return request -> {
            // a BROADLY-matching chain -- authorizeHttpRequests().anyRequest().authenticated()
            if (!request.isAuthenticated()) {
                return Optional.of(new MockResponse(403, null, "Forbidden (ordinary app rule)", "ORDINARY APP chain"));
            }
            return Optional.of(new MockResponse(200, null, "ordinary page content", "ORDINARY APP chain"));
        };
    }

    static MockResponse dispatch(MockRequest request, List<Chain> chainsInOrder) {
        for (Chain chain : chainsInOrder) {
            Optional<MockResponse> result = chain.handle(request);
            if (result.isPresent()) return result.get(); // FIRST matching chain wins
        }
        throw new IllegalStateException("no chain handled this request");
    }

    public static void main(String[] args) {
        MockRequest oauthRequest = new MockRequest("/oauth2/authorize", "text/html", false);

        System.out.println("--- CORRECT order: authorization server chain FIRST (@Order HIGHEST_PRECEDENCE) ---");
        MockResponse correct = dispatch(oauthRequest, List.of(authorizationServerChain(), ordinaryApplicationChain()));
        System.out.println("handled by: " + correct.handledBy() + ", status=" + correct.status() + ", location=" + correct.location());

        System.out.println("--- MISCONFIGURED order: ordinary chain FIRST (a real ordering bug) ---");
        MockResponse misconfigured = dispatch(oauthRequest, List.of(ordinaryApplicationChain(), authorizationServerChain()));
        System.out.println("handled by: " + misconfigured.handledBy() + ", status=" + misconfigured.status()
                + " (WRONG -- got a generic 403 instead of a proper login redirect)");
    }
}
```

**How to run:** save as `AuthServerChainLevel3.java`, run `java AuthServerChainLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- CORRECT order: authorization server chain FIRST (@Order HIGHEST_PRECEDENCE) ---
handled by: AUTHORIZATION SERVER chain, status=302, location=/login
--- MISCONFIGURED order: ordinary chain FIRST (a real ordering bug) ---
handled by: ORDINARY APP chain, status=403 (WRONG -- got a generic 403 instead of a proper login redirect)
```

What changed: `dispatch` now demonstrates the concrete, observable consequence of getting chain ordering wrong — with the ordinary application chain evaluated first (an `ordinaryApplicationChain()`, deliberately written to naively match everything, mirroring a broad `anyRequest()` rule without proper `securityMatcher` scoping elsewhere), the OAuth2-specific request never even reaches the correctly-configured authorization server chain, producing a generic `403` instead of the proper login redirect a real OIDC/OAuth2 flow depends on.

## 6. Walkthrough

Trace the misconfigured-order failure from Level 3, then the corrected version, mapping both to the real `@Order` annotation's role.

**Step 1 — a browser is redirected by an OAuth2 client to this server's authorization endpoint:**
```
GET /oauth2/authorize?client_id=my-app&response_type=code&... HTTP/1.1
Accept: text/html
```
Neither the browser nor the client has any authenticated session with this authorization server yet.

**Step 2a — CORRECT configuration: the authorization server chain (`@Order(Ordered.HIGHEST_PRECEDENCE)`) is evaluated first.** Its `securityMatcher` (`/oauth2/**` and related paths) matches this request — corresponding to `authorizationServerChain().handle(oauthRequest)` returning a non-empty result. Since the request is unauthenticated and the `Accept` header indicates a browser, `defaultAuthenticationEntryPointFor`'s browser branch fires, correctly redirecting to `/login`.

**Step 2b — MISCONFIGURED (hypothetical): a broader chain, without a correctly scoped `securityMatcher`, is evaluated first instead.** It matches *every* request (having no meaningful path restriction), so it handles this OAuth2 request too — corresponding to `ordinaryApplicationChain().handle(oauthRequest)` in Level 3 returning a result before the authorization server chain is ever consulted. Its own, generic unauthenticated handling (a bare `403`, with no knowledge of OAuth2-specific login redirection) fires instead — the wrong response entirely for this specific endpoint.

**Step 3 — the practical consequence.** In the correct configuration, the user is smoothly redirected to log in, then continues through the OAuth2 flow normally. In the misconfigured one, the user (or the OAuth2 client library handling the redirect) receives a bare `403` with no indication of what to do next — the flow simply breaks, and the root cause (an ordering/scoping mistake in `SecurityFilterChain` bean configuration) is not obvious from the symptom alone.

```
CORRECT:  [AuthServerChain (Order=HIGHEST), OrdinaryChain] -> AuthServerChain matches FIRST -> proper login redirect

WRONG:    [OrdinaryChain (misconfigured, matches everything), AuthServerChain] -> OrdinaryChain matches FIRST
              -> generic 403, AuthServerChain NEVER EVEN CONSULTED for this request
```

## 7. Gotchas & takeaways

> **Gotcha:** omitting `@Order(Ordered.HIGHEST_PRECEDENCE)` (or setting it to a value lower than the application's other `SecurityFilterChain` beans) is one of the most common configuration mistakes when first setting up Spring Authorization Server — Spring Security evaluates multiple `SecurityFilterChain` beans in ascending `@Order` value, and if the authorization server's chain isn't evaluated early enough, a broader chain could match and mishandle its endpoint requests first, exactly as Level 3 demonstrates.

- The authorization server's `SecurityFilterChain` bean needs `@Order(Ordered.HIGHEST_PRECEDENCE)` to guarantee it's evaluated before any other chain in the application, given `securityMatcher(...)`'s scoping only prevents this specific chain from mishandling unrelated paths, not the reverse.
- `securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())` scopes this chain to exactly the OAuth2/OIDC endpoints the configurer registers, letting every other application path fall through to a separate, ordinary chain.
- `defaultAuthenticationEntryPointFor(...)` with a `MediaTypeRequestMatcher` produces genuinely different responses for the same unauthenticated condition, based on whether the caller looks like a browser (redirect to login) or an API/OAuth2 client (a structured error response) — both are correct for their respective caller, and neither would be correct for the other.
- `.oidc(Customizer.withDefaults())` inside the configurer lambda specifically enables OpenID Connect support (the `/userinfo` endpoint, ID token issuance) beyond bare OAuth2 — omitting it limits the server to OAuth2-only behavior.
- Getting this bean's structure right is foundational — every subsequent customization in this project (custom clients, custom token claims, custom consent pages) is layered on top of, not a replacement for, this correctly-configured baseline chain.
