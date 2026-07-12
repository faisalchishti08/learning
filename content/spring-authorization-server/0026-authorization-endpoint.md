---
card: spring-authorization-server
gi: 26
slug: authorization-endpoint
title: "Authorization endpoint"
---

## 1. What it is

The authorization endpoint (`GET/POST /oauth2/authorize` by default, configurable via `AuthorizationServerSettings`, card 0025) is the front door of the entire OAuth2 authorization code and device code flows — it's where the user's browser is sent to authenticate and consent, and where the server ultimately issues an authorization code by redirecting back to the client. It's implemented internally as `OAuth2AuthorizationEndpointFilter`, one of the filters Spring Authorization Server adds to the security filter chain via `OAuth2AuthorizationServerConfigurer`.

## 2. Why & when

Every piece configured in the previous two sections — `RegisteredClient`, redirect URIs, scopes, consent settings — only actually gets *exercised* the moment a real request hits this endpoint. It's the one place where the client's declared permissions (card 0010), the user's real identity (established by whatever authentication mechanism the server's `SecurityFilterChain` uses), and the specific request's parameters all meet and get validated together.

You interact with this endpoint (directly, as a browser redirect target, or indirectly when debugging) whenever:

- Implementing "login with X" for any client — this is the URL the client redirects the user's browser to first.
- Debugging why a user lands on an error page instead of a login form — the vast majority of authorization endpoint failures (bad redirect URI, invalid scope, missing PKCE parameters) happen before the user is ever shown anything to interact with.
- Understanding exactly what triggers the consent screen versus a silent redirect straight back to the client.

## 3. Core concept

Think of the authorization endpoint as a hotel's front desk during check-in. A guest (the user's browser) arrives with a reservation confirmation (the query parameters: `client_id`, `redirect_uri`, `scope`, `response_type=code`). The desk clerk (the filter) first checks the reservation is valid — is this a real client, is the requested room (redirect URI) actually on file for them — *before* asking the guest for ID (authentication) or a signature (consent). Only once all of that clears does the clerk hand over a room key (the authorization code) and point the guest toward their room (the redirect back to the client).

```
GET /oauth2/authorize
    ?response_type=code
    &client_id=task-tracker
    &redirect_uri=https://task-tracker.example.com/callback
    &scope=tasks.read
    &state=xyz123
    &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
    &code_challenge_method=S256
```

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Authorization endpoint validates the request, authenticates the user, obtains consent, then redirects with a code">
  <rect x="20" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. Validate request</text>

  <rect x="180" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="250" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. Authenticate user</text>

  <rect x="340" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="410" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. Consent (if needed)</text>

  <rect x="500" y="20" width="120" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="560" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">4. Issue code</text>

  <line x1="160" y1="43" x2="175" y2="43" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="320" y1="43" x2="335" y2="43" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="480" y1="43" x2="495" y2="43" stroke="#3fb950" stroke-width="1.5"/>

  <rect x="120" y="130" width="400" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="320" y="155" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Step 1 failure (bad redirect_uri)</text>
  <text x="320" y="175" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">-&gt; error shown directly, NO redirect at all</text>
  <text x="320" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(prevents leaking a code to an unregistered address)</text>
</svg>

Validation happens first and gates everything else — a redirect URI failure never produces any redirect at all.

## 5. Runnable example

The scenario: a minimal `SecurityFilterChain` exposing the authorization endpoint, growing to handle the consent decision and finally to add custom request validation logging for observability.

### Level 1 — Basic

```java
// AuthEndpointConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.Customizer;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
public class AuthEndpointConfig {

    @Bean
    @Order(1)
    public SecurityFilterChain authorizationServerSecurityFilterChain(
            jakarta.servlet.http.HttpServletRequest request,
            org.springframework.security.config.annotation.web.builders.HttpSecurity http) throws Exception {

        OAuth2AuthorizationServerConfigurer authorizationServerConfigurer =
                OAuth2AuthorizationServerConfigurer.authorizationServer();

        http.securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())
                .with(authorizationServerConfigurer, withDefaults());

        return http.build();
    }
}
```

**How to run:** this is a Spring Boot configuration class; add it to a project with `spring-security-oauth2-authorization-server` and run the Boot application, then visit `http://localhost:8080/oauth2/authorize?...` in a browser once a `RegisteredClient` is registered. Expected behavior: a request with valid parameters redirects to the login page if the user isn't authenticated yet.

### Level 2 — Intermediate

A real deployment needs the built-in consent page enabled, since task-tracker requires consent (card 0013) — this is done by enabling OIDC support (which brings the consent page controller) on the same configurer.

```java
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;

public class AuthEndpointConfig {

    static void configureAuthorizationServer(
            org.springframework.security.config.annotation.web.builders.HttpSecurity http,
            OAuth2AuthorizationServerConfigurer authorizationServerConfigurer) throws Exception {

        authorizationServerConfigurer
                .oidc(oidc -> oidc.userInfoEndpoint(userInfo -> {})) // enables OIDC endpoints
                .authorizationEndpoint(authorizationEndpoint ->
                        authorizationEndpoint.consentPage("/oauth2/consent")); // custom consent view

        http.with(authorizationServerConfigurer, org.springframework.security.config.Customizer.withDefaults())
                .exceptionHandling(exceptions -> exceptions
                        .defaultAuthenticationEntryPointFor(
                                new org.springframework.security.web.authentication.LoginUrlAuthenticationEntryPoint("/login"),
                                new org.springframework.security.web.util.matcher.MediaTypeRequestMatcher(
                                        org.springframework.http.MediaType.TEXT_HTML)));
    }
}
```

**How to run:** wire `configureAuthorizationServer` into the filter chain bean from Level 1; requesting the authorization endpoint unauthenticated now redirects to `/login`, and after authentication, a client requiring consent renders `/oauth2/consent` instead of silently issuing a code. Expected behavior: browsing to the authorize URL while logged out redirects to a login form; after logging in as a user who hasn't consented before, a consent page listing the requested scopes appears.

What changed: unauthenticated requests now correctly redirect to a login page instead of failing, and clients requiring consent get a real, custom-styled consent view rather than the library's bare default.

### Level 3 — Advanced

Production adds structured logging around authorization requests — capturing which client, which scopes, and whether the request succeeded or was rejected — since the authorization endpoint is the highest-value place to observe abuse patterns (repeated invalid redirect URIs, scope-scanning attempts) before they reach the token endpoint.

```java
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;

import java.io.IOException;
import java.time.Instant;

public class AuthorizationRequestLoggingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest request = (HttpServletRequest) req;
        if (request.getRequestURI().equals("/oauth2/authorize")) {
            String clientId = request.getParameter("client_id");
            String scope = request.getParameter("scope");
            String redirectUri = request.getParameter("redirect_uri");
            System.out.printf("[%s] authorize request: client_id=%s scope=%s redirect_uri=%s%n",
                    Instant.now(), clientId, scope, redirectUri);
        }
        chain.doFilter(req, res);
    }
}
```

**How to run:** register this as a servlet filter positioned *before* `OAuth2AuthorizationServerConfigurer`'s filters in the chain (e.g. via `http.addFilterBefore(...)`); every hit to the authorization endpoint is logged with its key parameters before validation runs. Expected output when a request comes in:

```
[2026-07-12T10:00:00Z] authorize request: client_id=task-tracker scope=tasks.read redirect_uri=https://task-tracker.example.com/callback
```

What changed and why it's production-flavored: this is the raw material for detecting abuse (a client_id being hammered with mismatched redirect URIs, or scope-enumeration probing) and for basic usage analytics — logging *before* the built-in validation runs captures failed attempts too, which the filter's own error responses wouldn't otherwise leave a durable, centrally-visible trace of.

## 6. Walkthrough

Tracing a complete authorization endpoint request, in execution order, including both the success and failure paths:

1. The browser navigates to `GET /oauth2/authorize?response_type=code&client_id=task-tracker&redirect_uri=https://task-tracker.example.com/callback&scope=tasks.read&state=xyz123&code_challenge=E9Mel...&code_challenge_method=S256`.
2. The logging filter (Level 3) records the attempt, then `OAuth2AuthorizationEndpointFilter` looks up `RegisteredClient` for `task-tracker` and validates `redirect_uri` against its exact allow-list (card 0014) — if this fails, the response is an error page rendered directly, with **no** redirect anywhere (the security property discussed in card 0014).
3. Assuming the redirect URI matches, the filter checks whether `code_challenge` is required (`ClientSettings.isRequireProofKey()`, card 0013) — present here, so validation passes.
4. The filter checks if the current request is authenticated. It isn't (first visit), so Spring Security's standard authentication mechanism intercepts and redirects to `/login`.
5. The user submits valid credentials; Spring Security authenticates them and redirects back to the original `/oauth2/authorize?...` URL, parameters intact.
6. This time the request is authenticated. The filter checks `OAuth2AuthorizationConsentService.findById(...)` (card 0018) — say this user has never consented to `tasks.read` for this client — so it renders the consent page (`/oauth2/consent`, Level 2) listing `tasks.read`.
7. The user approves; the browser submits `POST /oauth2/authorize` (the consent form's action) with the approved scopes.
8. The filter saves an `OAuth2AuthorizationConsent` (card 0018), generates a fresh `OAuth2AuthorizationCode`, attaches it to a new `OAuth2Authorization` (card 0016), saves it via `OAuth2AuthorizationService` (card 0017), and responds `302 Found` with `Location: https://task-tracker.example.com/callback?code=SplxlOBeZQQYbYS6WxSbIA&state=xyz123`.
9. The client's backend receives this redirect, and — critically — checks that the returned `state` (`xyz123`) matches what it originally sent, which is what confirms this redirect is a genuine response to *this* browser's own request and not a cross-site request forgery.

```
GET /oauth2/authorize?...
   |
validate redirect_uri --fail--> error page, NO redirect
   |  pass
validate PKCE params present (if required)
   |
authenticated? --no--> redirect to /login --> authenticate --> redirect back here
   |  yes
consent already on file? --no--> render consent page --> user approves --> POST /oauth2/authorize
   |  yes
issue code, save OAuth2Authorization
   |
302 Found -> Location: <redirect_uri>?code=...&state=xyz123
```

## 7. Gotchas & takeaways

> The `state` parameter is the client's own responsibility to generate and verify — the authorization endpoint faithfully echoes it back unchanged, but does nothing to protect the client if it forgets to check it matches on return. Skipping this check is a real, exploitable CSRF vulnerability in the client, not the server.

- Requests missing `code_challenge` for a client with `requireProofKey(true)` fail validation at step 3, before authentication is even attempted — a `400` error, not a redirect to login.
- The consent page is only shown when there's something new to consent to (card 0018) — repeated logins with already-approved scopes skip straight from authentication to code issuance, which can look like "consent isn't working" if you're testing without clearing prior consent state.
- Never assume the authorization endpoint is only reached via `GET` from a real browser — it also accepts `POST` (used for the consent form submission itself), and testing tools sometimes need to replicate both.
- Logging authorization requests (Level 3) is valuable, but never log the full `code_challenge` or any secret-adjacent parameter indiscriminately in systems with broad log access — treat authorization request logs with the same care as any other security-relevant audit trail.
- If a client reports "I never get redirected back," check the redirect URI match first (card 0014) — a silent, non-redirecting error page is the most common cause and is easy to miss when testing only with a browser that shows the error page without inspecting the URL bar closely.
